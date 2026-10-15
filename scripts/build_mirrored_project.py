"""Migrate the approved mirrored frame into the existing finished Bambu project.

The baseline is immutable. Stage and native slicing never overwrite production.
Hammered faces, M poses, covers, backers, wall blocks and coupons are retained.
"""
import argparse,copy,hashlib,json,math,re,shutil,subprocess,time,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from build_jointed_bambu_project import ROOT,P,tag,xml,model,mesh_object,meta,uid,cylinder,IDENTITY
from colorize_print_project import read_mesh,setmeta,weave_modifier,projection
from validate_print_project import props,transform,scan_gcode
from add_blue_ribbon_edge import artwork,section,as_mesh,in_print_coordinates
from add_weave_test_coupon import read_zip,write_zip
from mesh_sections import mesh_slice
from repartition_mirrored_frame import WORK,BASE,CAD,STLS,PLAN,REVIEW,sha
import numpy as np
import trimesh
import manifold3d as mf
from scipy.spatial import cKDTree
from shapely import union_all,constrained_delaunay_triangles
from shapely import affinity
from shapely.geometry import Point,shape,Polygon,MultiPolygon,box

PACKAGE=ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed'
CHANGED=list(range(1,21))+[21,23,26]

def solid(mesh):
    result=mf.Manifold(mf.Mesh64(mesh.vertices,mesh.faces.astype(np.uint64)))
    assert result.status()==mf.Error.NoError,result.status()
    return result

def affine(mesh,t):
    result=mesh.copy();result.apply_transform(t);return result

def surface_distance(points,triangles):
    tree=cKDTree(triangles.mean(axis=1));worst=0.
    for start in range(0,len(points),3000):
        q=points[start:start+3000];_,near=tree.query(q,k=16)
        repeated=np.repeat(q,16,axis=0)
        close=trimesh.triangles.closest_point(triangles[near].reshape(-1,3,3),repeated)
        dist=np.linalg.norm(close-repeated,axis=1).reshape(-1,16).min(axis=1)
        for i in np.where(dist>1e-5)[0]:
            repeated=np.broadcast_to(q[i],(len(triangles),3))
            dist[i]=np.linalg.norm(trimesh.triangles.closest_point(triangles,repeated)-repeated,axis=1).min()
        worst=max(worst,float(dist.max()))
    return worst

def cylinder3(xy,r,z,h,r2=-1):
    return mf.Manifold.cylinder(h,r,r2,circular_segments=64).translate([*xy,z])

def locator(row,extra=0):
    # Exact blind locator and insertion chamfer from the production CAD.
    _,_,xy,secondary,angle=row
    pair=[-.4,.4] if secondary else [0]
    bore=sum((cylinder3([x,0],2.1+extra,-.02,3.32) for x in pair),mf.Manifold()).hull()
    mouth=sum((cylinder3([x,0],2.4+extra,-.01,.46,2.1+extra) for x in pair),mf.Manifold()).hull()
    return (bore+mouth).rotate([0,0,angle]).translate([*xy,0])

def hammered():
    """Move only three rear attachments; the removed/added volume is bounded."""
    out=WORK/'hammered';out.mkdir(exist_ok=True)
    files=read_zip(BASE/'Dara.3mf');cfg=ET.fromstring(files['Metadata/model_settings.config'])
    root=ET.fromstring(files['3D/3dmodel.model']);objects={o.get('id'):o for o in root.find(tag('resources'))}
    d=json.loads(PLAN.read_text());rows=[];meshes={};poses={}
    pose_path=ROOT/'working/geometry/hammered-M-assembly-poses.json'
    if pose_path.exists():poses=json.loads(pose_path.read_text())
    else:
        # Capture the verified production poses once, then retain them as source
        # data independently of the historical orientation experiment.
        stage=json.loads((ROOT/'.work/y-stable-dara/normal-stage.json').read_text())
        for co in cfg.findall('object'):
            name=props(co)['name'].split(' - ')[0]
            if name not in [f'M{i}' for i in range(1,7)]:continue
            part=co.find("part[@subtype='normal_part']");oid=co.get('id')
            comp=next(c for c in objects[oid].find(tag('components')) if c.get('objectid')==part.get('id'))
            b=next(b for b in root.find(tag('build')) if b.get('objectid')==oid)
            r=next(r for r in stage['objects'] if r['name']==name)
            t=np.array(r['build_transform']);pi=20+int(name[1:])-1
            t[:3,3]+=[pi%6*307.2,-(pi//6)*307.2,0]
            poses[name]=dict(assembly_from_mesh=(np.linalg.inv(t)@transform(b.get('transform'))@transform(comp.get('transform'))).tolist(),assembly_to_world=t.tolist(),object_id=oid,part_id=part.get('id'),path=comp.get('{'+P+'}path').lstrip('/'))
        pose_path.write_text(json.dumps(poses,indent=2)+'\n')
    for name,p in poses.items():
        child=ET.fromstring(files[p['path']]);obj=child.find(tag('resources')).find(f"{tag('object')}[@id='{p['part_id']}']")
        meshes[name]=affine(read_mesh(obj),np.array(p['assembly_from_mesh']))
    owners={}
    for move in d['hardware_moves']:
        if move['kind']=='photo_tab':continue
        ids=[n for n,m in meshes.items() if mesh_slice(m,9).contains(Point(move['old_xy'])) and mesh_slice(m,9).contains(Point(move['new_xy']))]
        assert len(ids)==1,(move,ids)
        owners.setdefault(ids[0],[]).append(move)
    assert set(owners)=={'M1','M3','M6'},owners
    for name,moves in owners.items():
        original=meshes[name];changed=original.copy()
        for move in moves:
            i=move['index']-1;xy=move['old_xy'];newxy=move['new_xy']
            screw=move['kind']=='screw';radius=1.61 if screw else 2.85;ceiling=8.71 if screw else 3.31
            select=(np.linalg.norm(original.vertices[:,:2]-xy,axis=1)<radius)&(original.vertices[:,2]<ceiling)
            assert int(select.sum())==(128 if screw else 262),(name,int(select.sum()))
            points=original.vertices[select,:2]-xy
            if not screw:
                angle=math.radians(d['dowel_mounts'][i][4]-d['old_dowel_mounts'][i][4])
                points=points@np.array([[math.cos(angle),math.sin(angle)],[-math.sin(angle),math.cos(angle)]])
            changed.vertices[select,:2]=points+newxy
        # Move the existing bore vertices exactly. Re-triangulate only the
        # flat rear if the move inverted a rear triangle. A whole-mesh boolean
        # needlessly simplifies tiny native hammered facets near the M edges.
        touched=np.any(np.linalg.norm(original.triangles-changed.triangles,axis=2)>1e-7,axis=1)
        inverted=touched&(np.einsum('ij,ij->i',original.face_normals,changed.face_normals)<.99)
        if inverted.any():
            bottom=np.all(np.abs(original.triangles[:,:,2])<1e-5,axis=1)
            assert np.all(bottom[inverted]),name
            indices=np.unique(original.faces[bottom]);tree=cKDTree(original.vertices[indices,:2])
            region=union_all([Polygon(t[:,:2]) for t in original.triangles[bottom] if Polygon(t[:,:2]).area>1e-12])
            def loop(ring):
                distances,ids=tree.query(np.array(ring.coords));assert distances.max()<1e-6
                return changed.vertices[indices[ids],:2]
            polygons=[region] if region.geom_type=='Polygon' else region.geoms
            revised=MultiPolygon([Polygon(loop(p.exterior),[loop(r) for r in p.interiors]) for p in polygons]);assert revised.is_valid
            ts=constrained_delaunay_triangles(revised)
            xy=np.array([list(t.exterior.coords)[:3] for t in ts.geoms]).reshape(-1,2)
            dist,ids=cKDTree(changed.vertices[indices,:2]).query(xy);assert dist.max()<1e-6
            faces=indices[ids].reshape(-1,3);vv=changed.vertices[faces]
            upwards=np.cross(vv[:,1]-vv[:,0],vv[:,2]-vv[:,0])[:,2]>0;faces[upwards]=faces[upwards,::-1]
            changed.faces=np.concatenate([changed.faces[~bottom],faces])
            # Native meshes contain exact duplicate vertices and zero-length
            # boundary edges. Merge exact duplicates only, without rounding.
            if not changed.is_watertight:
                vs,inv=np.unique(changed.vertices,axis=0,return_inverse=True);fs=inv[changed.faces]
                valid=(fs[:,0]!=fs[:,1])&(fs[:,1]!=fs[:,2])&(fs[:,0]!=fs[:,2])
                changed=trimesh.Trimesh(vs,fs[valid],process=False)
        assert changed.is_volume and len(changed.split())==1,name
        assert abs(changed.volume-original.volume)<.0001,(name,changed.volume-original.volume)
        # Every nonzero-area triangle above the rear attachment ceilings is
        # retained exactly, including the hammered face and all band seats.
        front_old=original.triangles[original.triangles[:,:,2].min(axis=1)>8.8]
        front_new=changed.triangles[changed.triangles[:,:,2].min(axis=1)>8.8]
        a=np.concatenate([front_old.reshape(-1,3),front_old.mean(axis=1)])
        b=np.concatenate([front_new.reshape(-1,3),front_new.mean(axis=1)])
        front_error=max(cKDTree(a).query(b)[0].max(),cKDTree(b).query(a)[0].max())
        assert front_error<.00002,(name,front_error)
        p=poses[name];p['moves']=moves
        np.savez_compressed(out/(name+'-changed.npz'),vertices=changed.vertices,faces=changed.faces)
        rows.append(dict(name=name,object_id=p['object_id'],path=p['path'],moves=moves,faces=len(changed.faces),volume_before_mm3=original.volume,volume_after_mm3=changed.volume,method='Existing rear bore vertices moved; flat rear retriangulated where necessary; all front triangles retained.',front_geometry_error_mm=float(front_error)))
        print(name,'rear attachments updated; face deviation',front_error,flush=True)
    (WORK/'hammered-stage.json').write_text(json.dumps(dict(poses=poses,checks=rows),indent=2)+'\n')

def stage():
    files=read_zip(BASE/'Dara.3mf');cfg=ET.fromstring(files['Metadata/model_settings.config'])
    root=ET.fromstring(files['3D/3dmodel.model']);res=root.find(tag('resources'));build=root.find(tag('build'))
    objects={o.get('id'):o for o in res};d=json.loads(PLAN.read_text());cad=CAD.read_text()
    knot=artwork(cad,'knot_outline');fabric=artwork(cad,'fabric_outline').buffer(.1125,join_style=2)
    blue=fabric.buffer(2.75).difference(fabric.buffer(1.25)).intersection(knot).simplify(.001,preserve_topology=True)
    pivots=np.array(d['photo_anchors']).reshape(-1,2)*.75+np.array(d['photo_normals']).reshape(-1,2)*9.5
    next_id=10000;records=[];changed_ids=set();changed_paths=[]
    for co in cfg.findall('object'):
        name=props(co)['name'].split(' - ')[0]
        if not re.fullmatch(r'F(?:[1-9]|1[0-9]|20)',name):continue
        i=int(name[1:])-1;mesh=trimesh.load_mesh(STLS/(name+'.stl'));assert mesh.is_volume and len(mesh.split())==1
        p=d['frame_placements'][i];angle=math.radians(p[0]);rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
        local=lambda xy:rot@np.array(xy)-p[1]
        mods=[]
        for k,row in enumerate(d['screw_mounts']):
            if row[1]==i:mods.append((f'100% M screw {k+1} seat - D16',cylinder(local(row[2]),16,mesh.bounds[1,2]),0))
        for k in d['frame_retainers'][i]:mods.append((f'100% photo screw {k+1} - D14',cylinder(local(pivots[k]),14,mesh.bounds[1,2]),0))
        for k,w in enumerate(d['wall_mounts']):
            if w[0]==i:
                for j,x in enumerate(w[5]):mods.append((f'100% B{k+1} screw {j+1} pilot - D14',cylinder(local(np.array(w[1])+[x,w[4]]),14,mesh.bounds[1,2]),0))
        for title,modifier,_ in mods:assert (solid(mesh)^solid(modifier)).volume()>1,(name,title)
        wood=weave_modifier(mesh)
        if wood:mods.append((name+' - Wood weave',wood[0],2))
        # This is a material modifier only; clipping happens against the real
        # printable body, including its lap and weave surfaces.
        blue_local=in_print_coordinates(blue,p)
        blue_local=blue_local.intersection(mesh_slice(mesh,13.2))
        if blue_local.area>1e-5:mods.append((name+' - Blue ribbon',as_mesh(section(blue_local).extrude(.6).translate([0,0,12.9])),4))
        oid=co.get('id');top=objects[oid];components=top.find(tag('components'))
        path=next(iter(components)).get('{'+P+'}path').lstrip('/')
        for c in list(components):components.remove(c)
        for part in co.findall('part'):co.remove(part)
        child=model();cr=ET.SubElement(child,tag('resources'))
        for k,(title,m,col) in enumerate([(name,mesh,1),*mods]):
            mid=next_id;next_id+=1;mesh_object(cr,mid,m)
            ET.SubElement(components,tag('component'),objectid=str(mid),transform=IDENTITY,attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
            part=ET.SubElement(co,'part',id=str(mid),subtype='normal_part' if k==0 else 'modifier_part');meta(part,'name',title)
            if col:meta(part,'extruder',col)
            else:meta(part,'sparse_infill_density','100%');meta(part,'sparse_infill_pattern','cubic')
            if k==0:meta(part,'source_file',name+'.stl')
            ET.SubElement(part,'mesh_stat',face_count=str(len(m.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        files[path]=xml(child);changed_paths.append(path);changed_ids.add(oid)
        b=next(b for b in build if b.get('objectid')==oid)
        tx,ty=128+i%6*307.2,128-(i//6)*307.2
        b.set('transform',f'1 0 0 0 1 0 0 0 1 {tx:.9f} {ty:.9f} 0')
        setmeta(co,'brim_width',1);setmeta(co,'raft_first_layer_expansion',0)
        setmeta(co,'name',name+' - mirrored short seams')
        bounds=mesh.bounds+np.array([128,128,0]);margin=min(*bounds[0,:2],*(256-bounds[1,:2]));assert margin>=1.499,(name,margin)
        records.append(dict(name=name,plate=i+1,object_id=oid,path=path,faces=len(mesh.faces),bounds_mm=bounds.tolist(),minimum_bed_edge_clearance_mm=float(margin),modifiers=[m[0] for m in mods]))
        print(name,'staged',len(mesh.faces),'faces; edge clearance',round(margin,3),flush=True)
    h=json.loads((WORK/'hammered-stage.json').read_text())
    for row in h['checks']:
        name=row['name'];p=h['poses'][name];oid=p['object_id'];co=cfg.find(f"object[@id='{oid}']");changed_ids.add(oid)
        path=p['path'];child=ET.fromstring(files[path]);cr=child.find(tag('resources'));changed_paths.append(path)
        data=np.load(WORK/'hammered'/(name+'-changed.npz'));body=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        raw=affine(body,np.linalg.inv(p['assembly_from_mesh']))
        original=cr.find(f"{tag('object')}[@id='{p['part_id']}']");at=list(cr).index(original);cr.remove(original)
        mesh_object(cr,p['part_id'],raw);replacement=list(cr)[-1];cr.remove(replacement);cr.insert(at,replacement)
        centers=body.triangles_center;placed_normals=body.face_normals@np.array(p['assembly_to_world'])[:3,:3].T
        front=body.triangles[:,:,2].max(axis=1)>9.89;hole_mask=np.zeros(len(body.faces),dtype=bool)
        for rr in d['screw_mounts']:hole_mask|=(np.linalg.norm(centers[:,:2]-rr[2],axis=1)<1.75)&(centers[:,2]<8.71)
        for rr in d['dowel_mounts']:hole_mask|=(np.linalg.norm(centers[:,:2]-rr[2],axis=1)<3.05)&(centers[:,2]<3.4)
        enforce=(placed_normals[:,2]<-.1)&~front&~hole_mask;block=front|hole_mask
        for k,tri in enumerate(replacement.find(tag('mesh')).find(tag('triangles'))):
            if block[k] or enforce[k]:tri.set('paint_supports','8' if block[k] else '4')
        co.find(f"part[@id='{p['part_id']}']/mesh_stat").set('face_count',str(len(body.faces)))
        b=next(b for b in build if b.get('objectid')==oid);components=objects[oid].find(tag('components'))
        # Move matching reinforcement volumes in their own mesh coordinates.
        for move in row['moves']:
            if move['kind']!='screw':continue
            matches=[part for part in co.findall('part') if props(part).get('name','')==f"Screw reinforcement {move['index']}"]
            assert len(matches)==1,(name,move,matches)
            part=matches[0];comp=next(c for c in components if c.get('objectid')==part.get('id'))
            cp=comp.get('{'+P+'}path').lstrip('/');assert cp==path
            obj=cr.find(f"{tag('object')}[@id='{part.get('id')}']")
            a=np.linalg.inv(p['assembly_to_world'])@transform(b.get('transform'))@transform(comp.get('transform'))
            mod=affine(read_mesh(obj),a);mod.apply_translation([*(np.array(move['new_xy'])-move['old_xy']),0]);mod=affine(mod,np.linalg.inv(a))
            cr.remove(obj);mesh_object(cr,part.get('id'),mod)
        if not any(k.startswith('{'+P+'}') for el in child.iter() for k in el.attrib):child.set('xmlns:p',P)
        files[path]=xml(child)
        row['support_paint']=dict(blocked_faces=int(block.sum()),enforced_faces=int(enforce.sum()),front_faces_blocked=int(front.sum()))
    # Bambu's saved assembly view must not retain the old centered frame volumes.
    asm=cfg.find('assemble')
    if asm is not None:
        for item in list(asm):
            if item.get('object_id') in {r['object_id'] for r in records}:asm.remove(item)
    for plate in cfg.findall('plate'):
        n=int(props(plate)['plater_id'])
        if n<=20:setmeta(plate,'plater_name',f'{n:02d} - F{n} mirrored short seams')
    for md in root.findall(tag('metadata')):
        if md.get('name')=='Description':md.text='Mirrored short-seam frame: 20 sections, 32 keyed laps; matching hammered M rear attachments; 32 plates.'
    files['3D/3dmodel.model']=xml(root);files['Metadata/model_settings.config']=xml(cfg)
    # Save only reviewed edits; all global settings and unrelated meshes remain.
    for path,data in files.items():
        if path.endswith('.model'):ET.fromstring(data)
    write_zip(WORK/'staged.3mf',files)
    report=dict(baseline_sha256=sha(BASE/'Dara.3mf'),staged_sha256=sha(WORK/'staged.3mf'),changed_plates=CHANGED,frame_records=records,hammered_checks=h['checks'],changed_mesh_paths=changed_paths,changed_object_ids=sorted(changed_ids),cad_sha256=sha(CAD))
    (WORK/'project-stage.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Staged complete project; production has not been replaced.',flush=True)

def native_slice():
    out=WORK/'slice';out.mkdir(exist_ok=True);exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'cli.log').open('w') as log:
        p=subprocess.run([str(exe),'--slice','0','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/'native-input.3mf')],cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print('Native slice exit:',p.returncode,flush=True);p.check_returncode()

def prepare_native():
    files=read_zip(WORK/'staged.3mf');cfg=ET.fromstring(files['Metadata/model_settings.config']);root=ET.fromstring(files['3D/3dmodel.model'])
    asm=cfg.find('assemble');settings=json.loads(files['Metadata/project_settings.config']);towers=[]
    for co in cfg.findall('object'):
        name=props(co)['name'].split(' - ')[0]
        if name.startswith('F') or name in ['M1','M3','M6']:
            count=co.find("part[@subtype='normal_part']/mesh_stat").get('face_count')
            for md in co.findall('metadata'):
                if md.get('face_count') is not None:md.set('face_count',count)
        if not re.fullmatch(r'F\d+',name):continue
        for item in list(asm):
            if item.get('object_id')==co.get('id'):asm.remove(item)
        bi=next(b for b in root.find(tag('build')) if b.get('objectid')==co.get('id'))
        ET.SubElement(asm,'assemble_item',object_id=co.get('id'),instance_id='0',transform=bi.get('transform'),offset='0 0 0')
        ET.SubElement(asm,'assemble_item',object_id=co.get('id'),volume_id='0',transform=IDENTITY)
        mesh=trimesh.load_mesh(STLS/(name+'.stl'));footprint=projection(mesh);footprint=affinity.translate(footprint,128,128)
        best=None
        for x in range(10,211,5):
            for y in range(10,211,5):
                # Allow for a 35 mm tower, purge depth, brim and rib wall.
                reserved=box(x-5,y-5,x+40,y+40);gap=footprint.distance(reserved)
                score=(gap,-math.hypot(x-210,y-210))
                if best is None or score>best[0]:best=(score,x,y)
        score,x,y=best;assert score[0]>5,(name,best)
        i=int(name[1:])-1;settings['wipe_tower_x'][i]=str(x);settings['wipe_tower_y'][i]=str(y)
        towers.append(dict(plate=i+1,xy=[x,y],reserved_bounds_mm=[x-5,y-5,x+40,y+40],minimum_reserved_gap_mm=score[0]))
    files['Metadata/model_settings.config']=xml(cfg);files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
    write_zip(WORK/'staged.3mf',files)
    # Do not let old native preview/slice caches load with a changed component
    # graph. The completed release receives matching fresh caches afterwards.
    native={k:v for k,v in files.items() if not k.startswith('Metadata/') or k in ['Metadata/project_settings.config','Metadata/model_settings.config']}
    for plate in cfg.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key','').endswith('_file'):plate.remove(md)
    native['Metadata/model_settings.config']=xml(cfg);write_zip(WORK/'native-input.3mf',native)
    p=WORK/'project-stage.json';d=json.loads(p.read_text());d['staged_sha256']=sha(WORK/'staged.3mf');d['towers']=towers
    p.write_text(json.dumps(d,indent=2)+'\n');print('Fresh native input and clear tower placements prepared.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['hammered','stage','prepare-native','slice']);args=p.parse_args()
    {'hammered':hammered,'stage':stage,'prepare-native':prepare_native,'slice':native_slice}[args.action]()
