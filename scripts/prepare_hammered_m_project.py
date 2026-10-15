"""Full-size, separately staged hammered M candidate; never overwrite Dara.3mf.

Use the successful coupon's surface field, the close-seam test's end relief,
and a common tilt direction for all six assembled parts. Native Studio slicing
and actual support/toolpath validation are separate steps from mesh generation.
"""
import argparse
import ast
import collections
import json
import math
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from prepare_tilted_hammered_joint import (
    ROOT, P, R, IDENTITY, np, trimesh, read_array, model, mesh_object, meta, tag,
    uid, read_zip, write_zip, sha, xml, props, setmeta, transform, read_mesh,
    artwork, section, as_mesh, mesh_slice, boolean, rotation, texture_field,
    scan_gcode,
)
from build_jointed_bambu_project import cylinder
from shapely.geometry import Polygon, LineString
from shapely import union_all, affinity
from scipy.spatial import cKDTree
from validate_print_project import TOKEN
import shapely

WORK = ROOT / '.work/hammered-m-production'
REVIEW = ROOT / 'working/review/hammered-m-production'
SOURCE = ROOT / 'Dara-Hammered-Close-Seam-Test.3mf'
TARGET = ROOT / 'Dara-Hammered-M-Candidate.3mf'
YAW = [34.5, 2., 61.5, 79.5, 85.75, 13.5]
TIP = .003 * 25.4
TITLE = 'Dara full-size hammered M - conditional joint-fit candidate'


def cad_polygon(text, name):
    body = text.split('module ' + name + '() {', 1)[1].split('\n}', 1)[0]
    polys = []
    for points, paths in re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity', body, re.S):
        pts, rings = ast.literal_eval(points), ast.literal_eval(paths)
        polys.append(Polygon([pts[j] for j in rings[0]], [[pts[j] for j in r] for r in rings[1:]]))
    return union_all(polys)


def joint_matrix(j):
    t = rotation(j[3]); t[:2, 3] = j[2]
    return t


def box(low, high):
    low, high = np.array(low), np.array(high)
    m = trimesh.creation.box(high-low); m.apply_translation((high+low)/2)
    return m


def height_envelope(evaluate, bounds):
    """Globally aligned half-mm grid, closed underneath at Z=6.7."""
    lo = np.floor(np.array(bounds[:2])*2)/2-1
    hi = np.ceil(np.array(bounds[2:])*2)/2+1
    xs, ys = [np.arange(a,b+.25,.5) for a,b in zip(lo,hi)]
    xx, yy = np.meshgrid(xs,ys)
    xy = np.column_stack([xx.ravel(),yy.ravel()]); nx,ny=len(xs),len(ys)
    v = np.column_stack([xy,10.5+evaluate(xy)])
    aa=(np.arange(ny-1)[:,None]*nx+np.arange(nx-1)[None,:]).ravel()
    faces=np.concatenate([np.column_stack([aa,aa+1,aa+nx+1]),np.column_stack([aa,aa+nx+1,aa+nx])])
    boundary=np.array(list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+[(ny-1)*nx+i for i in range(nx-2,-1,-1)]+[j*nx for j in range(ny-2,0,-1)])
    bot=np.arange(len(v),len(v)+len(boundary)); nxt=np.roll(np.arange(len(bot)),-1)
    center=len(v)+len(bot)
    vertices=np.concatenate([v,np.column_stack([v[boundary,:2],np.full(len(bot),6.7)]),[[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,6.7]]])
    faces=np.concatenate([faces,np.column_stack([bot,bot[nxt],boundary[nxt]]),np.column_stack([bot,boundary[nxt],boundary]),np.column_stack([np.full(len(bot),center),bot[nxt],bot])])
    out=trimesh.Trimesh(vertices,faces,process=False)
    assert out.is_volume
    return out


def wedge(j, domain, outline, envelope, male):
    inv=np.linalg.inv(joint_matrix(j))
    local=affinity.affine_transform(domain,[inv[0,0],inv[0,1],inv[1,0],inv[1,1],inv[0,3],inv[1,3]])
    ymin,ymax=local.bounds[1]-.1,local.bounds[3]+.1
    profile=np.array([[-.065,6.7],[-.0375,6.7],[-.0125,10.5],[-.0125,13.],[-.065,13.]])
    if not male: profile[:,0]*=-1
    m=as_mesh(section(Polygon(profile)).extrude(ymax-ymin))
    swap=np.array([[1,0,0,0],[0,0,1,ymin],[0,1,0,0],[0,0,0,1.]])
    m.apply_transform(joint_matrix(j)@swap)
    limit=as_mesh(section(domain.intersection(outline)).extrude(14))
    return boolean([m,limit,envelope],'intersection')


def geometry(numbers):
    WORK.mkdir(parents=True,exist_ok=True); REVIEW.mkdir(parents=True,exist_ok=True)
    cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    placements=read_array(cad,'M_placements'); joints=read_array(cad,'M_joints')
    outline=artwork(cad,'letter_outline'); field=texture_field(outline)
    domains=[cad_polygon(cad,f'M_joint_domain_{i}') for i in range(len(joints))]
    for number in numbers:
        i=number-1; name=f'M{number}'; p=placements[i]
        base=trimesh.load_mesh(ROOT/f'working/stl/Dara-Photo-Frame-A1-Jointed/{name}.stl')
        base.apply_translation([*p[1],-p[3]]); base.apply_transform(rotation(-p[0]))
        original=base.copy(); original.export(WORK/f'{name}-original.ply')
        cuts=[]
        for j,domain in zip(joints,domains):
            if j[0]!=i: continue
            t=joint_matrix(j)
            shelf=box([18-TIP,-150,-1],[20,150,6.3]);shelf.apply_transform(t)
            keys=box([15.75-TIP,-150,4.8],[16,150,6.3]);keys.apply_transform(t)
            limit=as_mesh(section(domain).extrude(8))
            for cut in [shelf,keys]:
                cuts.append(boolean([cut,limit],'intersection'))
        if cuts: base=boolean([base,*cuts],'difference')
        print(name,'trimmed',len(base.faces),'faces',flush=True)
        top=mesh_slice(base,10.49)
        envelope=height_envelope(field,top.bounds)
        prism=as_mesh(section(top).extrude(3).translate([0,0,10.4]))
        cap=boolean([envelope,prism],'intersection')
        additions=[cap]
        for j,domain in zip(joints,domains):
            if i in j[:2]: additions.append(wedge(j,domain,outline,envelope,i==j[0]))
        result=boolean([base,*additions],'union')
        assert result.is_volume and result.body_count==1,(name,result.is_watertight,result.body_count)
        removed=boolean([original,result],'difference')
        unauthorized=boolean([removed,*cuts],'difference') if cuts else removed
        assert abs(unauthorized.volume)<.001,(name,unauthorized.volume)
        added=boolean([result,base],'difference')
        lower=box([-400,-250,-1],[400,250,6.6999])
        lower_added=boolean([added,lower],'intersection')
        assert abs(lower_added.volume)<1e-5,(name,lower_added.volume)
        diff={str(z):mesh_slice(base,z).symmetric_difference(mesh_slice(result,z)).area for z in [.1,3.25,4.7,4.95,6.05,6.65]}
        assert max(diff.values())<1e-5,(name,diff)
        t=rotation(YAW[i])@rotation(55,(1,0,0))@rotation(1.5)
        placed=result.copy();placed.apply_transform(t)
        t[:2,3]=128-placed.bounds.mean(axis=0)[:2];t[2,3]=-placed.bounds[0,2]
        front=(result.triangles[:,:,2].min(axis=1)>=10.4999)&(result.face_normals[:,2]>.2)
        front_normals=result.face_normals[front]@t[:3,:3].T
        assert front_normals[:,2].min()>0,(name,front_normals[:,2].min())
        result.export(WORK/f'{name}-assembled.ply')
        np.savez_compressed(WORK/f'{name}.npz',vertices=result.vertices,faces=result.faces)
        report=dict(part=name,watertight=True,components=1,triangles=len(result.faces),volume_mm3=float(result.volume),
            bounds_assembled_mm=result.bounds.tolist(),build_transform=t.tolist(),print_extents_mm=placed.extents.tolist(),
            removed_tip_volume_mm3=float(removed.volume),unauthorized_removal_mm3=float(unauthorized.volume),
            added_below_6_7_mm3=float(lower_added.volume),hidden_sections_unchanged_mm2=diff,
            minimum_decorative_face_up_normal=float(front_normals[:,2].min()),source_stl_sha256=sha(ROOT/f'working/stl/Dara-Photo-Frame-A1-Jointed/{name}.stl'))
        (WORK/f'{name}-geometry.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report),flush=True)


def load_part(number):
    arr=np.load(WORK/f'M{number}.npz')
    return trimesh.Trimesh(arr['vertices'],arr['faces'],process=False)


def stage(numbers):
    source=read_zip(SOURCE)
    settings=json.loads(source['Metadata/project_settings.config'])
    settings.update(print_settings_id=TITLE,print_sequence='by layer',enable_prime_tower='0')
    assert settings['enable_support']=='1' and settings['support_type']=='tree(auto)'
    cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    screws=read_array(cad,'screw_mounts'); dowels=read_array(cad,'dowel_mounts')
    for n in numbers:
        name=f'M{n}'; body=load_part(n)
        report=json.loads((WORK/f'{name}-geometry.json').read_text()); t=np.array(report['build_transform'])
        files={k:source[k] for k in ['[Content_Types].xml','_rels/.rels']}
        root=model();del root.attrib['xmlns:p']
        for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title',TITLE+' - '+name)]:
            ET.SubElement(root,tag('metadata'),name=k).text=v
        res=ET.SubElement(root,tag('resources'));build=ET.SubElement(root,tag('build'),attrib={'{'+P+'}UUID':uid()})
        config=ET.Element('config');relations=ET.Element('Relationships',xmlns=R)
        oid=n*1000;path=f'3D/Objects/{name}.model';child=model();cr=ET.SubElement(child,tag('resources'))
        mesh_object(cr,oid+1,body)
        tri=cr.find(tag('object')).find(tag('mesh')).find(tag('triangles'))
        centers=body.triangles_center;normals=body.face_normals@t[:3,:3].T
        holes=np.zeros(len(body.faces),bool)
        for s in screws:
            if s[0]==n-1: holes|=(np.linalg.norm(centers[:,:2]-s[2],axis=1)<1.75)&(centers[:,2]<8.71)
        for d in dowels:
            if d[0]==n-1: holes|=(np.linalg.norm(centers[:,:2]-d[2],axis=1)<3.05)&(centers[:,2]<3.4)
        front=(body.triangles[:,:,2].min(axis=1)>=10.4999)&(body.face_normals[:,2]>.2)
        enforce=(normals[:,2]<-.1)&~holes&~front
        block=holes|front
        for idx in np.where(enforce|block)[0]: tri[idx].set('paint_supports','8' if block[idx] else '4')
        report['support_enforced_area_mm2']=float(body.area_faces[enforce].sum())
        report['support_blocked_hole_facets']=int(holes.sum())
        report['support_blocked_decorative_area_mm2']=float(body.area_faces[front].sum())
        obj=ET.SubElement(res,tag('object'),id=str(oid),type='model',attrib={'{'+P+'}UUID':uid()})
        comps=ET.SubElement(obj,tag('components'));cfg=ET.SubElement(config,'object',id=str(oid))
        meta(cfg,'name',name+' - full size hammered');meta(cfg,'extruder',1)
        mods=[(f'100% screw pilot {idx+1} - D14',cylinder(s[2],14,10.5)) for idx,s in enumerate(screws) if s[0]==n-1]
        for k,(label,mesh) in enumerate([(name,body)]+mods,1):
            if k>1:mesh_object(cr,oid+k,mesh)
            ET.SubElement(comps,tag('component'),objectid=str(oid+k),transform=IDENTITY,attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
            part=ET.SubElement(cfg,'part',id=str(oid+k),subtype='normal_part' if k==1 else 'modifier_part');meta(part,'name',label)
            if k==1:ET.SubElement(part,'mesh_stat',face_count=str(len(mesh.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
            else:
                meta(part,'sparse_infill_density','100%');meta(part,'sparse_infill_pattern','cubic')
                assert boolean([body,mesh],'intersection').volume>1
        ET.SubElement(build,tag('item'),objectid=str(oid),printable='1',transform=' '.join(f'{x:.12g}' for x in t[:3,:].T.ravel()),attrib={'{'+P+'}UUID':uid()})
        ET.SubElement(relations,'Relationship',Target='/'+path,Id=f'rel-{n}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        plate=ET.SubElement(config,'plate')
        for k,v in [('plater_id',1),('plater_name',name+' - full size hammered'),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 1 1 1'),('filament_volume_maps','0 0 0 0')]:meta(plate,k,v)
        inst=ET.SubElement(plate,'model_instance')
        for k,v in [('object_id',oid),('instance_id',0),('identify_id',n)]:meta(inst,k,v)
        files.update({path:xml(child),'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(relations),
            'Metadata/model_settings.config':xml(config),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
        write_zip(WORK/f'{name}-staged.3mf',files)
        report['reinforcement_modifiers']=[s[0] for s in mods]
        (WORK/f'{name}-geometry.json').write_text(json.dumps(report,indent=2))
        print(name,'staged',len(body.faces),'triangles;',len(mods),'screw modifiers',flush=True)


def combine_staged():
    source=read_zip(WORK/'M1-staged.3mf')
    files={k:source[k] for k in ['[Content_Types].xml','_rels/.rels','Metadata/project_settings.config']}
    root=ET.fromstring(source['3D/3dmodel.model'])
    resources=root.find(tag('resources'));resources.clear()
    build=root.find(tag('build'));build.clear()
    config=ET.Element('config');rels=ET.Element('Relationships',xmlns=R)
    for md in root.findall(tag('metadata')):
        if md.get('name')=='Title':md.text=TITLE
    for n in range(1,7):
        f=read_zip(WORK/f'M{n}-staged.3mf');r=ET.fromstring(f['3D/3dmodel.model']);c=ET.fromstring(f['Metadata/model_settings.config'])
        resources.extend(r.find(tag('resources')))
        for item in r.find(tag('build')):
            t=transform(item.get('transform'));t[:2,3]+=[((n-1)%3)*307.2,-((n-1)//3)*307.2]
            item.set('transform',' '.join(f'{x:.12g}' for x in t[:3,:].T.ravel()));build.append(item)
        config.extend(c.findall('object'))
        plate=c.find('plate');setmeta(plate,'plater_id',n);config.append(plate)
        path=f'3D/Objects/M{n}.model';files[path]=f[path]
        ET.SubElement(rels,'Relationship',Target='/'+path,Id=f'rel-{n}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    config[:]=config.findall('object')+config.findall('plate')
    files.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(rels),'Metadata/model_settings.config':xml(config)})
    write_zip(WORK/'all-staged.3mf',files)
    print('All six plates combined for native Studio slicing',flush=True)


def slice_parts(numbers):
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for n in numbers:
        out=WORK/(f'M{n}-slice' if n else 'all-slice');out.mkdir(exist_ok=True)
        staged=WORK/(f'M{n}-staged.3mf' if n else 'all-staged.3mf')
        with (out/'console.log').open('w') as log:
            completed=subprocess.run([str(exe),'--slice','1' if n else '0','--export-3mf','sliced.3mf','--outputdir',str(out),str(staged)],cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        print(f'M{n} slice exit {completed.returncode}',flush=True)
        assert completed.returncode==0,(out/'console.log').read_text()[-6000:]


def assembly_audit():
    bodies=[load_part(n) for n in range(1,7)]
    cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    joints=read_array(cad,'M_joints'); rows=[]
    sections=[mesh_slice(b,10.499) for b in bodies]
    for index,j in enumerate(joints):
        a,b=[bodies[k] for k in j[:2]]
        overlap=boolean([a,b],'intersection')
        assert abs(overlap.volume)<.001,(index,overlap.volume)
        inv=np.linalg.inv(joint_matrix(j))
        af=[inv[0,0],inv[0,1],inv[1,0],inv[1,1],inv[0,3],inv[1,3]]
        sa,sb=[affinity.affine_transform(sections[k],af) for k in j[:2]]
        gaps=[]
        for y in np.linspace(-j[4]/2+.5,j[4]/2-.5,31):
            line=LineString([[-.3,y],[.3,y]])
            left,right=sa.intersection(line),sb.intersection(line)
            if left.is_empty or right.is_empty:continue
            gaps.append(right.bounds[0]-left.bounds[2])
        assert len(gaps)>=10 and min(gaps)>.024 and max(gaps)<.026,(index,gaps)
        rows.append(dict(joint=index+1,male=f'M{j[0]+1}',female=f'M{j[1]+1}',
            overlap_volume_mm3=float(overlap.volume),samples=len(gaps),face_gap_min_mm=min(gaps),face_gap_max_mm=max(gaps),
            lower_shelf_end_mm=18-TIP,key_end_mm=15.75-TIP,tip_shortening_mm=TIP))
    # Check all remaining pairs too, including nearby non-joint arms.
    for i in range(6):
        for k in range(i+1,6):
            if np.any(bodies[i].bounds[1,:2]<bodies[k].bounds[0,:2]) or np.any(bodies[k].bounds[1,:2]<bodies[i].bounds[0,:2]):continue
            overlap=boolean([bodies[i],bodies[k]],'intersection')
            assert abs(overlap.volume)<.001,(i,k,overlap.volume)
    mounts=[];placements=read_array(cad,'M_placements')
    for i,body in enumerate(bodies):
        original=trimesh.load_mesh(ROOT/f'working/stl/Dara-Photo-Frame-A1-Jointed/M{i+1}.stl')
        p=placements[i];original.apply_translation([*p[1],-p[3]]);original.apply_transform(rotation(-p[0]))
        for kind,key,diameter,height in [('screw','screw_mounts',5,8.8),('locator','dowel_mounts',7,3.5)]:
            for hole in read_array(cad,key):
                if hole[0]!=i:continue
                region=cylinder(hole[2],diameter,height)
                old,new=boolean([original,region],'intersection'),boolean([body,region],'intersection')
                removed,added=boolean([old,new],'difference'),boolean([new,old],'difference')
                error=abs(removed.volume)+abs(added.volume)
                assert error<.001,(i,kind,hole,error)
                mounts.append(dict(part=f'M{i+1}',type=kind,xy_mm=hole[2],region_diameter_mm=diameter,
                    region_height_mm=height,geometry_difference_mm3=float(error)))
    assert len(mounts)==22
    report=dict(overall_bounds_mm=np.stack([np.min([b.bounds[0] for b in bodies],axis=0),np.max([b.bounds[1] for b in bodies],axis=0)]).tolist(),
        unchanged_mount_regions=mounts,
        joints=rows,texture=dict(pitch_mm=9,depth_mm=.55,maximum_added_crown_mm=2.2,edge_blend_distance_mm=17.5,grid_spacing_mm=.5,seed=73),
        common_tilt_deg=55,common_assembled_in_plane_rotation_deg=1.5,physical_joint_fit_pending=True,
        preserved_projects={p:sha(ROOT/p) for p in ['Dara.3mf','working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']},
        reference_close_seam_test_sha256=sha(SOURCE))
    assert all(v=='f0a0fe7ee2d3c2b64e8d5819b2c471785f8dbce4d115c9093cffcec646a7de94' for v in report['preserved_projects'].values())
    (REVIEW/'assembly-validation.json').write_text(json.dumps(report,indent=2))
    render_assembly(bodies)
    print(json.dumps(report,indent=2))


def render_assembly(bodies):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig,ax=plt.subplots(figsize=(15,10),facecolor='#f3efe7');ax.set_facecolor('#f3efe7')
    light=np.array([-.45,-.65,.65]);light/=np.linalg.norm(light)
    for n,m in enumerate(bodies,1):
        mask=(m.face_normals[:,2]>.15)&(m.triangles[:,:,2].min(axis=1)>=10.499)
        shade=.35+.65*np.maximum(m.face_normals[mask]@light,0)
        color=np.array([.89,.49,.23])[None,:]*shade[:,None]
        ax.add_collection(PolyCollection(m.triangles[mask,:,:2],facecolors=color,edgecolors='none',antialiaseds=False))
        point=mesh_slice(m,10.49).representative_point()
        ax.text(point.x,point.y,f'M{n}',ha='center',va='center',weight='bold',fontsize=15,color='white',bbox=dict(facecolor='#3e3025',alpha=.8,edgecolor='none',pad=4))
    ax.set(xlim=(-320,320),ylim=(-200,200),aspect='equal');ax.axis('off')
    fig.suptitle('Full-size hammered M — actual candidate geometry',fontsize=20)
    fig.text(.5,.04,'599.88 × 358.74 mm assembled | 10.5 mm structural body + up to 2.2 mm relief\nContinuous dimples across five joints; crown blends to the true outline. Shading shows geometry, not predicted silk sheen.',ha='center',fontsize=12)
    fig.tight_layout(rect=(0,.09,1,.93));fig.savefig(REVIEW/'assembled-M.png',dpi=150);plt.close(fig)


def model_entries(files):
    root=ET.fromstring(files['3D/3dmodel.model']);config=ET.fromstring(files['Metadata/model_settings.config'])
    cfg={c.get('id'):c for c in config.findall('object')};result={}
    for item in root.find(tag('build')):
        obj=root.find(tag('resources')).find(f"{tag('object')}[@id='{item.get('objectid')}']")
        co=cfg[item.get('objectid')];name=props(co)['name'].split(' - ')[0]
        parts=[]
        for comp in obj.find(tag('components')):
            child=ET.fromstring(files[comp.get('{'+P+'}path').lstrip('/')])
            meshobj=child.find(tag('resources')).find(f"{tag('object')}[@id='{comp.get('objectid')}']")
            m=read_mesh(meshobj);m.apply_transform(transform(item.get('transform'))@transform(comp.get('transform')))
            pc=co.find(f"part[@id='{comp.get('objectid')}']")
            paint=np.array([int(t.get('paint_supports','0'),16) for t in meshobj.find(tag('mesh')).find(tag('triangles'))])
            parts.append(dict(mesh=m,config=pc,paint=paint))
        result[name]=parts
    return result


def support_paths(text):
    """Actual extruding moves; sample lines for pictures, keep all interfaces."""
    groups={'Support':[],'Support interface':[],'Outer wall':[]}
    volume=collections.defaultdict(float);x=y=z=e=0.;feature='Custom';relative=False;relative_xyz=False
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '):feature=raw[11:].strip()
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ('G90','G91'):relative_xyz=cmd=='G91'
        elif cmd=='G92':
            v={k:float(n) for k,n in TOKEN.findall(code)};x,y,z,e=[v.get(k,old) for k,old in zip('XYZE',(x,y,z,e))]
        elif cmd in ('G0','G1','G2','G3'):
            v={k:float(n) for k,n in TOKEN.findall(code)}
            nx,ny,nz=[old+v.get(k,0) if relative_xyz else v.get(k,old) for k,old in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e
            if de>0 and feature!='Custom' and any(k in v for k in ('X','Y','I','J')):
                volume[feature]+=de*math.pi*(1.75/2)**2
                if feature in groups:groups[feature].append([[x,y,z],[nx,ny,nz]])
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    return {k:np.array(v).reshape(-1,2,3) for k,v in groups.items()},dict(volume)


def publish():
    files=read_zip(WORK/'all-slice/sliced.3mf');staged=read_zip(WORK/'all-staged.3mf')
    result=json.loads((WORK/'all-slice/result.json').read_text())
    assert result['return_code']==0 and len(result['sliced_plates'])==6,result
    settings=json.loads(files['Metadata/project_settings.config'])
    assert settings==json.loads(staged['Metadata/project_settings.config'])
    before,after=model_entries(staged),model_entries(files)
    assert set(before)==set(after)=={f'M{n}' for n in range(1,7)}
    geometry=[]
    for n in range(1,7):
        name=f'M{n}';a,b=before[name],after[name]
        assert len(a)==len(b)
        errors=[]
        for pa,pb in zip(a,b):
            ma,mb=pa['mesh'],pb['mesh']
            err=max(cKDTree(ma.vertices).query(mb.vertices)[0].max(),cKDTree(mb.vertices).query(ma.vertices)[0].max())
            assert err<.0001,(name,err);errors.append(float(err))
            for state in [4,8]:
                assert (pa['paint']==state).sum()==(pb['paint']==state).sum()
                aa=ma.area_faces[pa['paint']==state].sum();bb=mb.area_faces[pb['paint']==state].sum()
                assert abs(aa-bb)<max(.001,aa*1e-6),(name,state,aa,bb)
            assert pa['config'].get('subtype')==pb['config'].get('subtype')
            if pa['config'].get('subtype')=='modifier_part':
                for k in ['sparse_infill_density','sparse_infill_pattern']:assert props(pa['config'])[k]==props(pb['config'])[k]
        row=json.loads((WORK/f'{name}-geometry.json').read_text());row['native_round_trip_error_mm']=errors;geometry.append(row)
    info=ET.fromstring(files['Metadata/slice_info.config']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    assert len(info.findall('plate'))==len(cfg.findall('plate'))==6
    audits=[];plots=[]
    for n,plate in enumerate(info.findall('plate'),1):
        assert int(props(plate)['index'])==n
        setmeta(plate,'printer_model_id','N2S')
        for md in list(plate.findall('metadata')):
            if md.get('key')=='first_layer_time':
                v=float(md.get('value'))
                if not math.isfinite(v) or not 0<=v<=float(props(plate)['prediction']):plate.remove(md)
        warnings=[dict(w.attrib) for w in plate.findall('warning')]
        assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
        assert props(plate)['outside']=='false'
        gcode=files[f'Metadata/plate_{n}.gcode'].decode();audit=scan_gcode(gcode)
        assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',gcode,re.M)
        assert audit['conservative_bed_edge_clearance_mm']>=1.5,(n,audit)
        assert set(audit['model_extrusion_z_by_filament_mm'])=={'1'}
        zs=audit.pop('model_extrusion_z_by_filament_mm')['1']
        assert max(zs)<250 and min(zs)>=.1999
        audit['model_z_range_mm']=[min(zs),max(zs)]
        for feature in ['Sparse infill','Support','Support interface']:assert audit['features'].get(feature,0)>0,(n,feature)
        assert not audit['features'].get('Ironing',0)
        paths,vol=support_paths(gcode)
        inv=np.linalg.inv(np.array(geometry[n-1]['build_transform']))
        centers=paths['Support interface'].mean(axis=1)
        local=trimesh.transform_points(centers,inv)
        # Side-edge supports can extend past the face's plane outside the
        # silhouette. Check the decorative interior separately from that rim.
        top=mesh_slice(load_part(n),10.49);points=shapely.points(local[:,:2])
        interior=shapely.contains(top,points)&(shapely.distance(points,top.boundary)>.5)
        maximum=float(local[interior,2].max())
        assert maximum<6.7,(n,maximum)
        audit['support_interface_interior_max_assembled_z_mm']=maximum
        audit['support_interface_face_interior_margin_mm']=.5
        audit['support_interface_checks_use_segment_midpoints']=True
        cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
        holes=[]
        for kind,key,radius in [('screw','screw_mounts',1.5875),('locator','dowel_mounts',2.1)]:
            for hole in read_array(cad,key):
                if hole[0]!=n-1:continue
                near=np.linalg.norm(local[:,:2]-hole[2],axis=1)<radius
                penetration=float(local[near,2].max()) if near.any() else 0.
                assert penetration<1.2,(n,kind,penetration)
                holes.append(dict(type=kind,xy_mm=hole[2],interface_center_max_z_from_back_mm=penetration))
        audit['hole_entrance_support_check']=holes
        audit['feature_extrusion_volume_mm3']=vol
        audit['slice_metadata']=props(plate);audit['warnings']=warnings
        audits.append(audit)
        plots.append({k:v[::max(1,len(v)//16000)] for k,v in paths.items()})
        print(f'M{n}: {props(plate)["weight"]} g; {props(plate)["prediction"]} s; bed clearance {audit["conservative_bed_edge_clearance_mm"]:.2f} mm; interior support interface max local Z {maximum:.3f}',flush=True)
    files['Metadata/slice_info.config']=xml(info)
    write_zip(TARGET,files)
    assembly=json.loads((REVIEW/'assembly-validation.json').read_text())
    for p,h in assembly['preserved_projects'].items():assert sha(ROOT/p)==h
    report=dict(project=TARGET.name,sha256=sha(TARGET),parts=geometry,plates=audits,
        total_weight_g=sum(float(a['slice_metadata']['weight']) for a in audits),
        total_time_s=sum(int(a['slice_metadata']['prediction']) for a in audits),
        all_native_round_trips_passed=True,profile_unchanged_from_staged=True,
        source_profile_sha256=sha(SOURCE),physical_joint_fit_pending=True,
        slicer_result=result)
    (REVIEW/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    render_supports(plots,audits)
    render_assembly([load_part(n) for n in range(1,7)])
    print(json.dumps({k:report[k] for k in ['project','sha256','total_weight_g','total_time_s']},indent=2))


def render_supports(plots,audits):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    fig=plt.figure(figsize=(16,11),facecolor='#f3efe7')
    for n,(paths,audit) in enumerate(zip(plots,audits),1):
        ax=fig.add_subplot(2,3,n,projection='3d',facecolor='#f3efe7')
        for key,color,lw in [('Outer wall','#b9692e',.35),('Support','#969ca3',.25),('Support interface','#2c7788',.45)]:
            ax.add_collection3d(Line3DCollection(paths[key],colors=color,linewidths=lw))
        ax.set(xlim=(0,256),ylim=(0,256),zlim=(0,230));ax.set_box_aspect((256,256,230));ax.view_init(22,-65)
        ax.set_xlabel('X');ax.set_ylabel('Y');ax.set_zlabel('Z');ax.tick_params(labelsize=7)
        meta=audit['slice_metadata'];hours=int(meta['prediction'])/3600
        ax.set_title(f'M{n} | {hours:.1f} h | {float(meta["weight"]):.1f} g',fontsize=13)
    fig.suptitle('Native Bambu toolpaths — all six full-size plates',fontsize=20)
    fig.text(.5,.035,'Copper: outer walls | Gray: tree supports | Teal: support interfaces\nActual exported paths, sampled for legibility; heights and axes are in millimeters.',ha='center',fontsize=12)
    fig.subplots_adjust(left=.01,right=.99,top=.91,bottom=.11,wspace=.04,hspace=.18)
    fig.savefig(REVIEW/'supports-all-plates.png',dpi=150);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['geometry','stage','slice','assembly','combine','publish']);parser.add_argument('--parts',nargs='+',type=int,default=list(range(1,7)))
    args=parser.parse_args()
    if args.action=='assembly':assembly_audit()
    elif args.action=='combine':combine_staged()
    elif args.action=='publish':publish()
    else:{'geometry':geometry,'stage':stage,'slice':slice_parts}[args.action](args.parts)
