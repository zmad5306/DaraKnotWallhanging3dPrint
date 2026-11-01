"""Repair only plate 5's two receding brace edges from the saved Letter mesh."""
import sys, json, copy, shutil, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import manifold3d as mf
import trimesh
from scipy.spatial import cKDTree
import promote_veneer_wall_cradle as p
from development_3mf import solid,mesh,mesh_xml
from audit_veneer_surface_continuity import section
WORK=ROOT/'.work/letter-rear-braces-r1'
SOURCE=ROOT/'Letter.3mf'

def build():
    WORK.mkdir(parents=True,exist_ok=True)
    baseline=WORK/'before.3mf'
    if not baseline.exists():shutil.copyfile(SOURCE,baseline)
    assert p.sha(SOURCE)==p.sha(baseline)
    files=p.read(baseline)
    cfg,plate,obj,path,child,old,t=p.selected(files,5)
    assert p.props(obj)['name']=='Right letter veneer'
    v=p.vertices(old)@t[:3,:3].T+t[:3,3]
    ot=list(old.find(p.tag('triangles')))
    f=np.array([[int(q.get(k)) for k in ('v1','v2','v3')] for q in ot])
    om=trimesh.Trimesh(v,f,process=False)
    uv,ui=np.unique(v,axis=0,return_inverse=True);uf=ui[f]
    valid=(uf[:,0]!=uf[:,1])&(uf[:,1]!=uf[:,2])&(uf[:,0]!=uf[:,2])
    original_id=mf.Manifold.reserve_ids(1)
    body=mf.Manifold(mf.Mesh64(uv,uf[valid].astype(np.uint64),
        run_index=np.array([0,int(valid.sum())*3],dtype=np.uint64),
        run_original_id=np.array([original_id],dtype=np.uint32),
        face_id=np.flatnonzero(valid).astype(np.uint64)))
    assert body.status()==mf.Error.NoError
    provenance=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())['skins'][1]['carrier']
    patches=[];records=[]
    for web in provenance['webs']:
        profile=np.array(web['xz_profile']);rear=profile[0,0];top=profile[np.argmax(profile[:,1])]
        # Fill the receding edge with the existing 1 mm web thickness.
        # The 0.05 mm inset into the existing web avoids a touching-only union.
        poly=[[rear,0],[rear+.05,0],(profile[1]+[.05,0]).tolist(),(top+[.05,0]).tolist(),[rear,float(top[1])]]
        patch=mf.CrossSection([poly]).extrude(1).transform([[1,0,0,0],[0,0,1,web['y_mm']-.5],[0,1,0,0]])
        patches.append(patch)
        records.append(dict(y_mm=web['y_mm'],thickness_mm=1,old_rear_edge_xz_mm=profile[:3].tolist(),new_rear_edge_x_mm=float(rear),top_z_mm=float(top[1]),patch_xz_mm=poly))
    mask=mf.Manifold.batch_boolean(patches,mf.OpType.Add)
    candidate=body+mask
    removed=float((body-candidate).volume());outside=float(((candidate-body)-mask).volume())
    assert abs(removed)<1e-5 and abs(outside)<1e-5
    cm=mesh(candidate)
    pose=np.array(provenance['assembly_to_printer'])
    actual=np.array([q.get('paint_supports')=='8' for q in ot])
    expected=om.face_normals@pose[:3,2]>.01
    mismatch=float(om.area_faces[actual!=expected].sum())
    resources=p.ET.Element(p.tag('resources'));mesh_xml(resources,1,cm,True,pose[:3,2])
    replacement=resources[0].find(p.tag('mesh'))
    raw=candidate.to_mesh64();assert len(raw.tri_verts)==len(cm.faces)
    origins=np.zeros(len(cm.faces),dtype=bool)
    for i,oid in enumerate(raw.run_original_id):
        if oid==original_id:origins[int(raw.run_index[i])//3:int(raw.run_index[i+1])//3]=True
    for face,original,index in zip(replacement.find(p.tag('triangles')),origins,raw.face_id):
        if original:
            face.attrib.pop('paint_supports',None)
            for k,val in ot[int(index)].attrib.items():
                if k not in ('v1','v2','v3'):face.set(k,val)
    inv=np.linalg.inv(t);local=cm.vertices@inv[:3,:3].T+inv[:3,3]
    for vertex,point in zip(replacement.find(p.tag('vertices')),local):
        for k,val in zip(('x','y','z'),point):vertex.set(k,format(float(val),'.12g'))
    parent=next(o for o in child.find(p.tag('resources')) if o.find(p.tag('mesh')) is old)
    parent.remove(old);parent.append(replacement);files[path]=p.xml(child)
    obj.find('part/mesh_stat').set('face_count',str(len(cm.faces)))
    for md in obj.findall('metadata'):
        if 'face_count' in md.attrib:md.set('face_count',str(len(cm.faces)))
    files['Metadata/model_settings.config']=p.xml(cfg)
    p.write(WORK/'editable.3mf',files)
    np.savez_compressed(WORK/'geometry.npz',before_v=om.vertices,before_f=om.faces,after_v=cm.vertices,after_f=cm.faces)
    report=dict(source_sha256=p.sha(baseline),editable_sha256=p.sha(WORK/'editable.3mf'),plate=5,name='Right letter veneer',patches=records,removed_volume_mm3=removed,difference_outside_patches_mm3=outside,added_volume_mm3=float((candidate-body).volume()),paint_rule_mismatch_area_mm2=mismatch,changed_asset=path,physical_qualification=False)
    p.save_json(WORK/'geometry.json',report)
    print(json.dumps(report),flush=True)

def preview():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    a=np.load(WORK/'geometry.npz');fig,axs=plt.subplots(1,3,figsize=(12,4))
    for ax,z in zip(axs,[60,180,240]):
        for key,color in [('before','#b74a36'),('after','#247765')]:
            lines=section(a[key+'_v'][a[key+'_f']],z)
            ax.add_collection(LineCollection(lines,colors=color,linewidths=1.3,label=key))
        ax.set(xlim=(54,76),ylim=(134,142),aspect='equal',title=f'Brace 1 at Z {z} mm',xlabel='Bed X (mm)');ax.grid(alpha=.2)
    axs[0].legend();fig.suptitle('Plate 5: fill the gap to the rear wall; keep the 1 mm brace thickness')
    fig.tight_layout();fig.savefig(WORK/'join-correction.png',dpi=160)

def validate():
    import organize_root_projects as org
    from check_veneer_layer_overlap import parse
    from set_veneer_eryone_spool_limits import audit_commands
    import shapely
    native=WORK/'plate-5/sliced.3mf'
    report=json.loads((WORK/'geometry.json').read_text())
    report['native_preservation']=org.compare(WORK/'editable.3mf',native,{5:5})
    before=p.read(WORK/'before.3mf');files=p.read(WORK/'editable.3mf');one=p.read(native)
    raw=one['Metadata/plate_5.gcode']
    assert hashlib.md5(raw).hexdigest().upper()==one['Metadata/plate_5.gcode.md5'].decode().strip().upper()
    report['commands']=audit_commands(raw.decode());assert report['commands']['out_of_range_count']==0
    model,support=parse(raw.decode())
    checks=[]
    for patch in report['patches']:
        y=patch['y_mm'];rear=patch['new_rear_edge_x_mm'];top=patch['top_z_mm']
        edge=np.array(patch['old_rear_edge_xz_mm']);bad=[];count=0
        for z,rows in model.items():
            if z<.8 or z>top-.3:continue
            old_x=float(np.interp(z-.1,edge[:,1],edge[:,0]))
            # Local union of actual nominal extrusion footprints, including
            # path widths. Require one connected area from the rear wall
            # into the pre-existing brace on every full-height layer.
            vals=np.array([r[:5] for r in rows]);ends=vals[:,:4].reshape(-1,2,2)
            take=(ends[:,:,1].min(axis=1)<=y+1)&(ends[:,:,1].max(axis=1)>=y-1)&(ends[:,:,0].min(axis=1)<=old_x+1.5)&(ends[:,:,0].max(axis=1)>=rear-1)
            lines=shapely.linestrings(ends[take]);beads=shapely.buffer(lines,vals[take,4]/2+.002)
            region=shapely.box(rear-1,y-.48,old_x+1.2,y+.48)
            footprint=shapely.intersection(shapely.union_all(beads),region)
            a=shapely.box(rear-.2,y-.45,rear+.2,y+.45)
            b=shapely.box(old_x+.15,y-.45,old_x+.45,y+.45)
            joined=any(shapely.intersects(g,a) and shapely.intersects(g,b) for g in shapely.get_parts(footprint))
            count+=1
            if not joined:bad.append(z)
        checks.append(dict(y_mm=y,layers_checked=count,failed_layers=bad))
        print('Join',y,'layers',count,'failed',bad[:20],flush=True)
    report['native_join_checks']=checks
    p.save_json(WORK/'join-validation.json',report)
    assert all(not q['failed_layers'] for q in checks),checks
    # Merge just the new plate's native assets into the unchanged container.
    cfg=p.ET.fromstring(files['Metadata/model_settings.config']);sc=p.ET.fromstring(one['Metadata/model_settings.config'])
    old=cfg.findall('plate')[4];new=copy.deepcopy(sc.findall('plate')[4])
    p.setmeta(new.find('model_instance'),'object_id',p.props(old.find('model_instance'))['object_id'])
    index=list(cfg).index(old);cfg.remove(old);cfg.insert(index,new)
    files['Metadata/model_settings.config']=p.xml(cfg)
    info=p.ET.fromstring(files['Metadata/slice_info.config']);si=p.ET.fromstring(one['Metadata/slice_info.config'])
    old=next(q for q in info.findall('plate') if p.props(q)['index']=='5');new=next(q for q in si.findall('plate') if p.props(q)['index']=='5')
    index=list(info).index(old);info.remove(old);info.insert(index,copy.deepcopy(new));files['Metadata/slice_info.config']=p.xml(info)
    seq=json.loads(files['Metadata/filament_sequence.json']);seq['plate_5']=json.loads(one['Metadata/filament_sequence.json'])['plate_5'];files['Metadata/filament_sequence.json']=json.dumps(seq).encode()
    files.update({n:v for n,v in one.items() if p.plate_asset(n,5)})
    for number in [1,2,3,4,6]:
        assert all(files[n]==v for n,v in before.items() if p.plate_asset(n,number))
    assert files['Metadata/project_settings.config']==before['Metadata/project_settings.config']
    result=json.loads((ROOT/'release/root-projects/Letter-native.json').read_text())
    new_result=json.loads((WORK/'plate-5/result.json').read_text())
    assert new_result['return_code']==0
    result['sliced_plates'][4]=new_result['sliced_plates'][0]
    mass=sum(f['total_used_g'] for q in result['sliced_plates'] if q['id']>=4 for f in q['filaments'])
    assert mass<1000
    warnings=[w.attrib for q in si.findall('plate') for w in q.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    report.update(veneer_total_g=mass,plate5_native_result=new_result,warnings=warnings,protected_plate_assets_byte_identical=[1,2,3,4,6],settings_byte_identical=True)
    p.write(WORK/'corrected.3mf',files)
    report['corrected_sha256']=p.sha(WORK/'corrected.3mf')
    p.save_json(WORK/'validation.json',report);p.save_json(WORK/'combined-native.json',result)
    print('Validated and merged plate 5; total veneer mass',mass,flush=True)

def reopen():
    import subprocess
    folder=WORK/'reopen';folder.mkdir(exist_ok=True)
    with (folder/'native.log').open('w') as log:
        r=subprocess.run([str(p.EXE),'--export-3mf','reopened.3mf','--outputdir',str(folder),str(WORK/'corrected.3mf')],cwd=p.EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert r.returncode==0,r.returncode
    import organize_root_projects as org
    p.save_json(WORK/'reopen.json',org.compare(WORK/'corrected.3mf',folder/'reopened.3mf'))

def publish():
    import organize_root_projects as org
    report=json.loads((WORK/'validation.json').read_text())
    report['native_reopen']=json.loads((WORK/'reopen.json').read_text())
    assert p.sha(SOURCE)==report['source_sha256']
    assert p.sha(WORK/'corrected.3mf')==report['corrected_sha256']
    shutil.copyfile(WORK/'corrected.3mf',SOURCE)
    out=ROOT/'release/letter-rear-braces-r1';out.mkdir(exist_ok=True)
    org.REPORT=WORK/'cad';org.REPORT.mkdir(exist_ok=True);org.TITLES=['Letter'];org.export_cad()
    catalog=json.loads((ROOT/'release/root-projects/catalog.json').read_text())
    catalog['Letter'].update(json.loads((org.REPORT/'catalog.json').read_text())['Letter'])
    catalog['Letter']['rear_brace_validation']='release/letter-rear-braces-r1/validation.json'
    p.save_json(ROOT/'release/root-projects/catalog.json',catalog)
    hashes=json.loads((ROOT/'release/root-projects/gcode-sha256.json').read_text())
    hashes['Letter']['plate_5']=hashlib.sha256(p.read(SOURCE)['Metadata/plate_5.gcode']).hexdigest()
    p.save_json(ROOT/'release/root-projects/gcode-sha256.json',hashes)
    shutil.copyfile(WORK/'combined-native.json',ROOT/'release/root-projects/Letter-native.json')
    p.save_json(out/'validation.json',report)
    for name in ['join-correction.png','geometry.json']:shutil.copyfile(WORK/name,out/name)
    print('Published',report['corrected_sha256'],flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='build':build();preview()
    elif action=='slice':
        p.WORK=WORK;p.EDIT=WORK/'editable.3mf';p.slice_plate(5)
    elif action=='validate':validate()
    elif action=='reopen':reopen()
    elif action=='publish':publish()
