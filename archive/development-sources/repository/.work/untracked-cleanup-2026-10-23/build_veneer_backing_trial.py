"""Small A/B physical trial and matching full-plate backing experiment.

Only separate trial files are written. Production remains untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
import shapely
from development_3mf import solid,mesh,write_project,save_json,sha,centered,tag,xml
from validate_production_split import Project,distance
from build_a2l_flush_joint_test import protected
from check_fin_toolpaths import check_fin_bonds
from check_veneer_layer_overlap import parse,coverage
from validate_print_project import scan_gcode

OUT=ROOT/'working/bambu/Dara-A2L-Veneer-Backing-Trial'
WORK=ROOT/'.work/veneer-backing-trial'
SOURCE=ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf'
CASES=['A-Fins-Only','B-Rear-Backing','Full-V2-Rear-Backing']
Y0=199.191184296509-.8
Y1=222.70772605515498+.8
Z0=240.


def paint_rear(path,m,pose):
    av=(m.vertices-pose[:3,3])@pose[:3,:3]
    near_back=np.all((av[m.faces,2]>=8.5999)&(av[m.faces,2]<=9.0001),axis=1)
    rear=(m.face_normals@(-pose[:3,2])>.9999)&near_back
    assert rear.any()
    with zipfile.ZipFile(path) as z:files={n:z.read(n) for n in z.namelist()}
    child=ET.fromstring(files['3D/Objects/1000.model'])
    triangles=child.find(tag('resources')).find(tag('object')).find(tag('mesh')).find(tag('triangles'))
    assert len(triangles)==len(m.faces)
    for i,t in enumerate(triangles):
        if rear[i]:
            assert t.get('paint_supports')!='8'
            t.set('paint_supports','4')
    files['3D/Objects/1000.model']=xml(child)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in files.items():z.writestr(n,data)
    return int(rear.sum()),float(m.area_faces[rear].sum())


def build():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    fingerprints=protected()
    project=Project(SOURCE);native=Project(ROOT/'Dara.3mf')
    row=project.rows['V2 A2L hammered veneer and sacrificial fins']
    full=solid(row['parts'][0]['mesh']).transform(row['T'][:3])
    geometry=json.loads((SOURCE.parent/'M-geometry-validation.json').read_text())
    pose=np.array(geometry['skins'][1]['assembly_to_printer'])
    crop=mf.Manifold.cube([50,Y1-Y0,325-Z0]).translate([50,Y0,Z0])
    cropped=full^crop
    assert (cropped-full).volume()<1e-7
    coupon=cropped.translate([0,0,-Z0])
    # Connect the two cropped fin feet without filling the space beneath the
    # veneer where the tree roots must grow. This bar is identical in A and B.
    foot=mf.Manifold.cube([3,Y1-Y0+.8,1.2]).translate([63,Y0-.4,0])
    coupon+=foot
    assert len([c for c in coupon.decompose() if c.volume()>1e-6])==1
    coupon_mesh=mesh(coupon)
    records={}
    for name in CASES:
        is_full=name.startswith('Full')
        m=mesh(full) if is_full else coupon_mesh.copy()
        T=np.eye(4) if is_full else centered(m,xy=[165,160])
        local_pose=pose.copy()
        if not is_full:local_pose[2,3]-=Z0
        test_pose=T@local_pose
        st=dict(row['settings'])
        if not is_full:st.update(brim_width='4',brim_type='outer_only')
        if name.startswith('A-'):
            st['enable_support']='0'
        else:
            st.update(support_interface_spacing='0',support_interface_top_layers='2')
        title=('EXPERIMENT ONLY - ' if is_full else 'Physical veneer A-B trial - ')+name
        settings=dict(native.settings,print_settings_id=title,wipe_tower_x=['285'],wipe_tower_y=['160'])
        if name.startswith('A-'):settings['enable_support']='0'
        path=(WORK/name/'input.3mf') if is_full else OUT/(name+'-Editable.3mf')
        path.parent.mkdir(parents=True,exist_ok=True)
        entry=dict(name=name,parts=[dict(mesh=m,settings=row['parts'][0]['settings'])],
            settings=st,transform=T,block_front=True,front_normal=pose[:3,2])
        write_project(path,[[entry]],title,settings_update=settings)
        count,area=(0,0.) if name.startswith('A-') else paint_rear(path,m,local_pose)
        delta=test_pose[:3,3]-pose[:3,3]
        probes=geometry['skins'][1]['carrier']['bond_probes_print_xyz_mm']
        if not is_full:probes=[p for p in probes if 50<p[0]<100 and Y0<p[1]<Y1 and p[2]>Z0+.5]
        probes=(np.array(probes)+delta).tolist()
        assert len(probes)>=8
        records[name]=dict(input=str(path.relative_to(ROOT)),input_sha256=sha(path),
            bounds_mm=(m.bounds+T[:3,3]).tolist(),volume_mm3=m.volume,
            assembly_to_test_printer=test_pose.tolist(),source_print_translation_mm=delta.tolist(),
            bond_probes_print_xyz_mm=probes,rear_enforced_triangles=count,rear_enforced_area_mm2=area,
            source_mesh_unchanged=is_full,original_fins_spacing_mm=23.516541758646,
            sample_new_base_bar_mm=None if is_full else [3,Y1-Y0+.8,1.2],
            sample_brim_width_mm=0 if is_full else 4,
            support_enabled=not name.startswith('A-'),
            rear_interface_spacing_mm=.5 if name.startswith('A-') else 0)
        sidecar=json.loads(path.with_suffix('.json').read_text())
        sidecar.update(source_project=str(SOURCE.relative_to(ROOT)),source_sha256=sha(SOURCE),
            source_plate=16,physical_confirmation_pending=True)
        save_json(path.with_suffix('.json'),sidecar)
    assert protected()==fingerprints
    save_json(OUT/'geometry-validation.json',dict(status='DIGITAL_GEOMETRY_PASS_PHYSICAL_TEST_PENDING',
        protected_project_sha256=fingerprints,source_sha256=sha(SOURCE),source_plate=16,
        crop_source_print_bounds_mm=[[50,Y0,Z0],[100,Y1,325]],tests=records))
    print(json.dumps({n:{k:r[k] for k in ['bounds_mm','volume_mm3','rear_enforced_area_mm2']} for n,r in records.items()},indent=2),flush=True)


def replace_control():
    """Correct only A, preserving the exact B and full-plate experiment files."""
    old='A-Current-Supports';new=CASES[0]
    report_path=OUT/'geometry-validation.json'
    report=json.loads(report_path.read_text())
    assert old in report['tests'] and new not in report['tests']
    previous=json.loads((OUT/'native-validation.json').read_text())
    assert previous['evidence_sha256']['geometry-validation.json']==sha(report_path)
    assert protected()==report['protected_project_sha256']
    archive=WORK/'superseded-current-support-control'
    archive.mkdir(parents=True,exist_ok=True)
    for filename in ['geometry-validation.json','native-validation.json','README.md',
                     old+'.3mf',old+'-Editable.3mf',old+'-Editable.json','backing-comparison.png']:
        (archive/filename).write_bytes((OUT/filename).read_bytes())
    path=OUT/(new+'-Editable.3mf')
    with zipfile.ZipFile(OUT/(old+'-Editable.3mf')) as z:files={n:z.read(n) for n in z.namelist()}
    st=json.loads(files['Metadata/project_settings.config'])
    st['enable_support']='0';st['print_settings_id']=st['print_settings_id'].replace(old,new)
    files['Metadata/project_settings.config']=json.dumps(st,indent=2).encode()
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    for e in cfg.iter('metadata'):
        if e.get('value'):e.set('value',e.get('value').replace(old,new))
        if e.get('key')=='enable_support':e.set('value','0')
    for obj in cfg.findall('object'):
        assert any(e.get('key')=='enable_support' and e.get('value')=='0' for e in obj.findall('metadata'))
    files['Metadata/model_settings.config']=xml(cfg)
    root=ET.fromstring(files['3D/3dmodel.model'])
    for e in root.findall(tag('metadata')):
        if e.text:e.text=e.text.replace(old,new)
    files['3D/3dmodel.model']=xml(root)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    side=json.loads((OUT/(old+'-Editable.json')).read_text())
    side['title']=side['title'].replace(old,new)
    for r in side['records']:r['name']=r['name'].replace(old,new)
    side.update(native_slice_validated=False,physical_confirmation_pending=True)
    for k in ['native_project','native_sha256']:side.pop(k,None)
    save_json(path.with_suffix('.json'),side)
    r=report['tests'].pop(old)
    r.update(input=str(path.relative_to(ROOT)),input_sha256=sha(path),support_enabled=False)
    report['tests']={new:r,**report['tests']}
    report['control_correction']=dict(supersedes=old,reason='Old control generated trees; replace with zero slicer supports to isolate fins-only printing.',
        prior_report_archive=str(archive.relative_to(ROOT)),
        unchanged_B_native_sha256=sha(OUT/'B-Rear-Backing.3mf'))
    save_json(report_path,report)
    a=Project(path);b=Project(OUT/'B-Rear-Backing-Editable.3mf')
    am=next(iter(a.rows.values()));bm=next(iter(b.rows.values()))
    av=am['parts'][0]['mesh'].vertices@am['T'][:3,:3].T+am['T'][:3,3]
    bv=bm['parts'][0]['mesh'].vertices@bm['T'][:3,:3].T+bm['T'][:3,3]
    assert np.array_equal(av,bv)
    assert np.array_equal(am['parts'][0]['mesh'].faces,bm['parts'][0]['mesh'].faces)
    print('A-Fins-Only source created with supports disabled globally and on the object. A/B model geometry is exactly identical.',flush=True)


def slice_all(selected=None):
    records=json.loads((OUT/'geometry-validation.json').read_text())['tests']
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for name,r in records.items():
        if selected and name!=selected:continue
        folder=WORK/name;folder.mkdir(parents=True,exist_ok=True)
        with (folder/'cli.log').open('w') as log:
            p=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf',
                '--outputdir',str(folder),str(ROOT/r['input'])],cwd=exe.parent,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        p.check_returncode();print('Sliced '+name,flush=True)


def backing_check(m,pose,support,step=.5):
    av=(m.vertices-pose[:3,3])@pose[:3,:3]
    flat=(m.face_normals@(-pose[:3,2])>.9999)&np.all(np.abs(av[m.faces,2]-8.6)<1e-4,axis=1)
    lands=shapely.union_all(shapely.polygons(av[m.faces[flat],:2]))
    xmin,ymin,xmax,ymax=lands.bounds
    x,y=np.meshgrid(np.arange(xmin+.371*step,xmax,step),np.arange(ymin+.619*step,ymax,step))
    xy=np.column_stack([x.ravel(),y.ravel()]);xy=xy[shapely.contains_xy(lands,xy[:,0],xy[:,1])]
    xyz=np.column_stack([xy,np.full(len(xy),8.6)])@pose[:3,:3].T+pose[:3,3]
    bins=np.ceil(xyz[:,2]/.2).astype(int);hit=np.zeros(len(xy),bool)
    for band in np.unique(bins):
        ids=np.flatnonzero(bins==band)
        for k in range(-4,1):
            z=round((band+k)*.2,4);rows=support.get(z,[])
            if not rows:continue
            dz=xyz[ids,2]-z;valid=ids[(dz>=.05)&(dz<=.6001)]
            if len(valid):hit[valid]|=coverage(xyz[valid,:2],np.zeros(len(valid)),rows)[0]
    return dict(sample_points=len(xy),points_with_nearby_support=int(hit.sum()),
        rear_support_proximity_percent=100*float(hit.mean()),grid_spacing_mm=step),xy,hit


def validate(samples_only=False):
    report=json.loads((OUT/'geometry-validation.json').read_text());results={};plots=[]
    previous=json.loads((OUT/'native-validation.json').read_text()) if samples_only else None
    sample_meshes=[]
    for name,r in report['tests'].items():
        if samples_only and name.startswith('Full'):
            assert sha(ROOT/r['input'])==r['input_sha256']
            assert sha(WORK/name/'sliced.3mf')==previous['tests'][name]['native_sha256']
            results[name]=previous['tests'][name]
            continue
        src=Project(ROOT/r['input']);native=Project(WORK/name/'sliced.3mf')
        assert src.rows.keys()==native.rows.keys() and src.settings==native.settings
        before=src.rows[name];after=native.rows[name]
        assert len(before['parts'])==len(after['parts'])==1
        for key in ['extruder','enable_support','sparse_infill_density','brim_width','outer_wall_speed','inner_wall_speed','support_interface_spacing','support_interface_top_layers']:
            assert before['settings'].get(key)==after['settings'].get(key),(name,key)
        a=before['parts'][0]['mesh'].copy();a.apply_transform(before['T'])
        b=after['parts'][0]['mesh'].copy();b.apply_transform(after['T'])
        error=distance(a.vertices,b.vertices);assert error<.001 and b.is_volume
        raw=native.z.read('Metadata/plate_1.gcode');gcode=raw.decode()
        assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
        scan=scan_gcode(gcode);lo,hi=np.array(scan['bead_xy_bounds_mm'])
        margin=float(min(*lo,*(np.array([330,320])-hi)));assert margin>.5
        scan['conservative_bed_edge_clearance_mm']=margin
        assert set(scan['model_extrusion_z_by_filament_mm'])=={'3'}
        assert max(scan['model_extrusion_z_by_filament_mm']['3'])<325
        assert min(scan['model_extrusion_z_by_filament_mm']['3'])==.2
        bond=check_fin_bonds(gcode,r)
        model,support=parse(gcode)
        support_moves=sum(scan['features'].get(f,0) for f in ['Support','Support interface'])
        if name.startswith('A-'):
            assert after['settings']['enable_support']=='0'
            assert native.settings['enable_support']=='0'
            assert support_moves==0 and not support,('Control still has printed supports',support_moves,len(support))
        near,xy,hit=backing_check(b,np.array(r['assembly_to_test_printer']),support,1 if name.startswith('Full') else .5)
        warnings=[w.attrib for pl in ET.fromstring(native.z.read('Metadata/slice_info.config')).findall('plate') for w in pl.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
        estimate=json.loads((WORK/name/'result.json').read_text())['sliced_plates'][0]
        results[name]=dict(maximum_mesh_pose_error_mm=error,scan=scan,fin_bonds=bond,
            rear_backing=near,support_layer_count=len(support),slicer_warnings=warnings,
            support_extrusion_moves=support_moves,
            estimated_seconds=estimate['total_predication'],estimated_filament_g=sum(f['total_used_g'] for f in estimate['filaments']),
            native_sha256=sha(WORK/name/'sliced.3mf'),gcode_sha256=hashlib.sha256(raw).hexdigest())
        if not name.startswith('Full'):
            plots.append((name,xy,hit));sample_meshes.append(b)
        print(name,json.dumps({k:results[name][k] for k in ['rear_backing','estimated_seconds','estimated_filament_g']}),flush=True)
    # Confirm that A and B actually exercise substantially different backing.
    # These checks establish an A/B contrast, not a physical-quality threshold.
    a=results['A-Fins-Only']['rear_backing']['rear_support_proximity_percent']
    b=results['B-Rear-Backing']['rear_backing']['rear_support_proximity_percent']
    assert a==0 and b-a>40,(a,b)
    pair_error=distance(sample_meshes[0].vertices,sample_meshes[1].vertices)
    assert pair_error<.001
    assert results['Full-V2-Rear-Backing']['rear_backing']['rear_support_proximity_percent']>70
    assert protected()==report['protected_project_sha256']
    if 'control_correction' in report:
        assert sha(OUT/'B-Rear-Backing.3mf')==report['control_correction']['unchanged_B_native_sha256']
    for name in CASES[:2]:
        path=OUT/(name+'.3mf');path.write_bytes((WORK/name/'sliced.3mf').read_bytes())
        side=OUT/(name+'-Editable.json');d=json.loads(side.read_text())
        d.update(native_slice_validated=True,native_project=path.name,native_sha256=sha(path));save_json(side,d)
    save_json(OUT/'native-validation.json',dict(status='DIGITAL_PASS_READY_FOR_SMALL_PHYSICAL_TRIAL',
        physical_prints_performed=False,production_and_A1_preserved=True,tests=results,
        A_has_zero_support_toolpaths=True,maximum_A_B_native_geometry_difference_mm=pair_error,
        unchanged_full_plate_result_reused=samples_only,
        support_measurement='Rear-land sample point inside nominal support bead XY footprint, 0.05-0.60 mm below. Proximity screen, not effective support contact or physical flatness.',
        builder_sha256=sha(Path(__file__))))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(9,5),layout='constrained')
    for ax,(name,xy,hit) in zip(axes,plots):
        ax.scatter(xy[~hit,0],xy[~hit,1],c='#cccccc',s=8,marker='s',linewidths=0)
        ax.scatter(xy[hit,0],xy[hit,1],c='#1a9165',s=8,marker='s',linewidths=0)
        ax.set_aspect('equal');ax.set_title(name);ax.set_xlabel('Assembly X (mm)');ax.set_ylabel('Assembly Y (mm)')
    fig.suptitle('Same veneer patch and fin gap: gray = no nearby tree path; green = nearby path')
    fig.savefig(OUT/'backing-comparison.png',dpi=150);plt.close(fig)
    if 'control_correction' in report:
        # Retire only the exact old control files already copied to the archive.
        archive=ROOT/report['control_correction']['prior_report_archive']
        for suffix in ['.3mf','-Editable.3mf','-Editable.json']:
            path=OUT/('A-Current-Supports'+suffix)
            if path.exists():
                assert path.resolve().parent==OUT.resolve()
                assert sha(path)==sha(archive/path.name)
                path.unlink()
    print('Published only the two small A/B physical-trial projects. Production unchanged.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','replace-control','slice','validate'])
    p.add_argument('--case',choices=CASES);p.add_argument('--samples-only',action='store_true')
    args=p.parse_args()
    if args.action=='slice':slice_all(args.case)
    elif args.action=='validate':validate(args.samples_only)
    elif args.action=='replace-control':replace_control()
    else:build()
