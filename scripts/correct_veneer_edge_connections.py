"""Repair saved production/sample edge pockets without regenerating artwork.

Only connections whose 2.6 mm cleanup pocket crosses the perimeter move.
The old pocket is filled from a translated intact section of the SAME mesh.
The new pocket has at least 1.7 mm of continuous perimeter stock around it.
"""
import copy,json,sys,shutil,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import manifold3d as mf
import trimesh
from shapely.geometry import shape,Point,box
from shapely.ops import nearest_points
from add_blue_ribbon_edge import section
from development_3mf import solid,mesh,tag,xml,sha,mesh_xml,transform
from promote_veneer_wall_cradle import read,write
from validate_production_split import Project
import build_a2l_project as builder

WORK=ROOT/'.work/veneer-edge-r7'
REPORT=ROOT/'release/veneer-edge-r7'
SAMPLE=Path(r'C:\Users\Zach\Desktop\Dara-A2L-Hammered-Finish-ERYONE-r3.3mf')
SAMPLE_OUT=ROOT/'output/Dara-A2L-Hammered-Finish-ERYONE-r4'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'

def block(x,y,z,at):return mf.Manifold.cube([x,y,z]).translate(at)
def slab(lo,hi):return block(2000,2000,hi-lo,[-1000,-1000,lo])
def saved(path):
    return Project(path)

def repair(body,region,contacts):
    safe=region.buffer(-3.6)
    changes=[];result=body;oldcuts=[];fills=[];newcuts=[];newteeth=[]
    # The intact rear-adjacent layer has the exact saved perimeter, including
    # float serialization. It supplies only missing stock in old pocket masks.
    intact=(body^slab(9.201,9.802)).translate([0,0,-.601])
    for q in contacts:
        x,y=q[:2];pocket=box(x-1.3,y-1.3,x+1.3,y+1.3)
        if region.covers(pocket):continue
        p=nearest_points(Point(x,y),safe)[1];nx,ny=p.coords[0]
        newp=box(nx-1.3,ny-1.3,nx+1.3,ny+1.3)
        assert region.covers(newp.buffer(1.69))
        oldmask=block(2.6002,2.6002,.602,[x-1.3001,y-1.3001,8.599])
        fill=intact^oldmask
        # Preserve the inclined wall (top Z4.4), restore the veneer back Z8.6.
        oldcuts.append(block(2.6002,2.6002,4.8,[x-1.3001,y-1.3001,4.40001]))
        fills.append(fill)
        newcuts.append(block(2.6,2.6,.5,[nx-1.3,ny-1.3,8.5]))
        newteeth.append(block(1.2,1.2,4.9,[nx-.6,ny-.6,4.3]))
        changes.append(dict(old_xy_mm=[x,y],new_xy_mm=[nx,ny],
            pocket_edge_margin_mm=region.boundary.distance(newp),
            restored_stock_mm3=fill.volume(),new_probe_assembly_xyz_mm=[nx,ny,7.85]))
    assert changes
    union=lambda parts:mf.Manifold.batch_boolean(parts,mf.OpType.Add)
    result=((body-union(oldcuts))+union(fills)-union(newcuts))+union(newteeth)
    assert result.status()==mf.Error.NoError
    removed=body-result;added=result-body
    protected_loss=(removed^slab(9.20001,1000)).volume()
    protected_gain=(added^slab(9.20001,1000)).volume()
    assert abs(protected_loss)+abs(protected_gain)<1e-5
    assert abs((removed^slab(-1000,4.39999)).volume())<1e-5
    pieces=[p for p in result.decompose() if p.volume()>1e-6]
    pieces.sort(key=lambda p:p.volume(),reverse=True)
    remnants=[]
    for fragment in pieces[1:]:
        bounds=np.array(fragment.bounding_box()).reshape(2,3)
        center=bounds.mean(0)
        distance=min(np.linalg.norm(center[:2]-r['old_xy_mm']) for r in changes)
        assert fragment.volume()<1 and bounds[0,2]>4.39999 and bounds[1,2]<8.6 and distance<4
        remnants.append(dict(volume_mm3=fragment.volume(),bounds_mm=bounds.tolist(),distance_to_old_connection_mm=distance))
        result-=fragment
    assert len([p for p in result.decompose() if p.volume()>1e-6])==1
    rim=section(region.difference(region.buffer(-1.2))).extrude(.3).translate([0,0,8.65])
    missing_rim=abs(((intact-result)^rim).volume())
    assert missing_rim<.0002,missing_rim
    return result,dict(connections=changes,removed_mm3=removed.volume(),added_mm3=added.volume(),
        protected_front_difference_mm3=abs(protected_loss)+abs(protected_gain),
        missing_stock_in_1_2mm_perimeter_band_mm3=missing_rim,
        removed_detached_old_stem_remnants=remnants,
        connected_components=1,watertight=mesh(result).is_volume)

def patch_project(source,target,specs):
    project=saved(source);files=read(source);original=dict(files)
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    model=ET.fromstring(files['3D/3dmodel.model']);changed=[];records=[]
    for name,pose,region,contacts in specs:
        row=project.rows[name];assert len(row['parts'])==1
        current=row['parts'][0]['mesh'].copy();current.apply_transform(row['T'])
        current.apply_transform(np.linalg.inv(pose));body=solid(current)
        candidate,evidence=repair(body,region,contacts)
        cm=mesh(candidate);cm.apply_transform(pose)
        assert np.max(abs(cm.bounds[0]- (row['parts'][0]['mesh'].vertices@row['T'][:3,:3].T+row['T'][:3,3]).min(0)))<.001
        cm.apply_transform(np.linalg.inv(row['T']))
        oid=next(k for k,v in project.configs.items() if v.find("metadata[@key='name']").get('value')==name)
        co=model.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']").find(tag('components'))[0]
        asset=co.get(P+'path').lstrip('/');child=ET.fromstring(files[asset]);resources=child.find(tag('resources'))
        # Project reader already applies the component transform.
        cm.apply_transform(np.linalg.inv(transform(co.get('transform'))))
        obj=resources.find(f"{tag('object')}[@id='{co.get('objectid')}']");old=obj.find(tag('mesh'))
        normal=np.linalg.inv(row['T'])[:3,:3]@pose[:3,2]
        temp=ET.Element('resources');mesh_xml(temp,int(co.get('objectid')),cm,block_front=True,front_normal=normal)
        obj.remove(old);obj.append(temp[0].find(tag('mesh')))
        files[asset]=xml(child);changed.append(asset)
        stat=cfg.find(f"object[@id='{oid}']/part/mesh_stat")
        if stat is not None:stat.set('face_count',str(len(cm.faces)))
        evidence.update(name=name,plate=row['plate'],asset=asset,pose=pose.tolist())
        records.append(evidence)
    files['Metadata/model_settings.config']=xml(cfg)
    # Stored preview/toolpaths belong to the old mesh. Do not deliver them.
    stale=[n for n in files if n.endswith('.gcode') or n.endswith('.gcode.md5')]
    for n in stale:del files[n]
    allowed=set(changed)|{'Metadata/model_settings.config'}|set(stale)
    assert all(files[n]==v for n,v in original.items() if n not in allowed)
    write(target,files)
    return dict(source=str(source),source_sha256=sha(source),target=str(target),target_sha256=sha(target),
        global_settings_and_saved_poses_byte_preserved=True,changed_assets=changed,objects=records,
        stale_toolpaths_removed=stale,physical_validation_pending=True)

def build():
    WORK.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);SAMPLE_OUT.mkdir(parents=True,exist_ok=True)
    production=ROOT/'Letter.3mf';baseline=WORK/'Letter-before.3mf'
    if not baseline.exists():shutil.copyfile(production,baseline)
    samplebase=WORK/'ERYONE-r3-before.3mf'
    if not samplebase.exists():shutil.copyfile(SAMPLE,samplebase)
    evidence=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())
    plan=builder.load_plan();p=saved(baseline);specs=[]
    for i,s in enumerate(evidence['skins']):
        pose=np.array(s['assembly_to_printer']);iv=np.linalg.inv(pose)
        contacts=np.array(s['carrier']['bond_probes_print_xyz_mm'])@iv[:3,:3].T+iv[:3,3]
        name=next(n for n in p.rows if n.startswith(f'V{i+1} '))
        specs.append((name,pose,shape(plan['skin_regions'][i]),contacts))
    main=patch_project(baseline,WORK/'Letter-corrected.3mf',specs)
    # The supplied Desktop r3 was translated on its plate by Bambu Studio.
    # Infer only that translation from the exact saved sample bounds.
    old=json.loads((ROOT/'output/Dara-A2L-Hammered-Finish-ERYONE-r3/validation.json').read_text())
    sample=saved(samplebase);name,row=next(iter(sample.rows.items()))
    sm=row['parts'][0]['mesh'].copy();sm.apply_transform(row['T'])
    delta=sm.bounds-np.array(old['sample_bounds_mm']);assert np.max(np.ptp(delta,axis=0))<.0001
    pose=specs[0][1].copy();pose[:3,3]+=delta.mean(0)
    contacts=specs[0][3]
    world=contacts@pose[:3,:3].T+pose[:3,3]
    keep=np.all((world>sm.bounds[0]+.7)&(world<sm.bounds[1]-.7),axis=1)
    sample_report=patch_project(samplebase,SAMPLE_OUT/'Dara-A2L-Hammered-Finish-ERYONE-r4-Editable.3mf',
        [(name,pose,specs[0][2],contacts[keep])])
    for title,data in [('Letter',main),('ERYONE-r4',sample_report)]:
        (REPORT/(title+'-geometry.json')).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({t:[len(r['connections']) for r in d['objects']] for t,d in [('Letter',main),('sample',sample_report)]}),flush=True)

if __name__=='__main__':build()
