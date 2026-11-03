"""Remove only the print-upper gusset from saved r1; preserve the saved setup."""
from pathlib import Path
import hashlib, json, re, subprocess, sys, zipfile, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import manifold3d as mf
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, LineString, box
import development_3mf as d
from mesh_sections import mesh_slice
from validate_print_project import scan_gcode, transform, props, TOKEN

OUT=Path(__file__).resolve().parent
WORK=ROOT/'.work/dara-crate-clips-r2'
OLD=ROOT/'output/Dara-Crate-Clips-A1-PETG-r1'
SOURCE=OLD/'Dara-Crate-Clips-A1-PETG-r1.3mf'
SOURCE_EDIT=OLD/'Dara-Crate-Clips-A1-PETG-r1-Editable.3mf'
EDIT=OUT/'Dara-Crate-Clips-A1-PETG-r2-Editable.3mf'
FINAL=OUT/'Dara-Crate-Clips-A1-PETG-r2.3mf'
TITLE='Dara crate clips - A1 SUNLU PETG - 8% gyroid - r2'
LOCKED=dict(layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',
    top_shell_layers='5',bottom_shell_layers='5',sparse_infill_density='8%',
    sparse_infill_pattern='gyroid',nozzle_diameter=['0.4'],curr_bed_type='Textured PEI Plate')

def load(p):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        return {n:z.read(n) for n in z.namelist()}

def save(p,f):
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in f.items():z.writestr(n,b)

def protected():
    paths=[ROOT/'Dara.3mf',ROOT/'AGENTS.md',SOURCE,SOURCE_EDIT,OLD/'build_clips.py']
    paths+=list((ROOT/'working/bambu/Dara-A1-Companion').glob('*.3mf'))
    paths+=list((ROOT/'working/bambu/Dara-Photo-Frame-A2L').glob('Dara-A2L-*.3mf'))
    return {str(p):d.sha(p) for p in paths}

def differences(a,b):
    return {k:dict(before=a.get(k),after=b.get(k)) for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)}

def cube(lo,hi):return mf.Manifold.cube(tuple(np.array(hi)-lo)).translate(lo)

def build():
    OUT.mkdir(exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    before=protected();source=load(SOURCE);src_edit=load(SOURCE_EDIT)
    old_report=json.loads((OLD/'validation.json').read_text())
    assert d.sha(SOURCE)==old_report['current_sha256']
    assert d.sha(SOURCE_EDIT)==old_report['editable_sha256']
    old_settings=json.loads(source['Metadata/project_settings.config'])
    settings=dict(old_settings,enable_support='0',print_settings_id=TITLE)
    assert set(differences(old_settings,settings))=={'enable_support','print_settings_id'}
    # Assembly Y=10..14 is print Z=24..28 in the saved side-down pose.
    # Subtract only material outside the upright X=-4 and above flange Z=4.
    removal=cube((-25,10,4),(-4,14,27.9))
    root=ET.fromstring(src_edit['3D/3dmodel.model']);entries=[];records=[]
    for it in root.find(d.tag('build')):
        parts,st=d.read_object(src_edit,it.get('objectid'));assert len(parts)==1
        old=parts[0]['mesh'];s=d.solid(old);new=s-removal;m=d.mesh(new)
        removed=s-new;added=new-s;expected=s^removal
        assert abs(added.volume())<1e-7 and removed.volume()>800
        assert abs((removed-expected).volume())<1e-7 and abs((expected-removed).volume())<1e-7
        assert m.is_volume and len(m.split())==1
        assert np.max(np.abs(m.bounds-old.bounds))<1e-7
        assert mesh_slice(old,2).symmetric_difference(mesh_slice(m,2)).area<1e-7
        assert abs((new^cube((.4,-14,10),(30,14,23.5))).volume())<1e-7
        assert abs((new^mf.Manifold.cylinder(40,7,7,96).translate((-15,0,4.001))).volume())<1e-7
        hole=Polygon(mesh_slice(m,2).interiors[0]);assert abs(hole.bounds[2]-hole.bounds[0]-4.7625)<1e-5
        T=transform(it.get('transform'));old_placed=old.copy();old_placed.apply_transform(T)
        placed=m.copy();placed.apply_transform(T)
        assert mesh_slice(old_placed,1).symmetric_difference(mesh_slice(placed,1)).area<1e-5
        # Upper layers now have the same C profile as those below the old gusset.
        assert mesh_slice(placed,24.1).symmetric_difference(mesh_slice(placed,23.9)).area<1e-5
        entries.append(dict(name=st['name'],parts=[dict(mesh=m,subtype='normal_part',settings=parts[0]['settings'])],
                            transform=T,settings={k:v for k,v in st.items() if k not in (None,'name')}))
        records.append(dict(name=st['name'],removed_mm3=removed.volume(),added_mm3=added.volume(),
                            removed_only_from_upper_gusset=True,lower_gusset_unchanged=True,
                            bounds_mm=placed.bounds.tolist(),transform=T.tolist(),
                            screw_center_print_mm=(np.array([-15.,0.,2.])@T[:3,:3].T+T[:3,3]).tolist()))
    assert len(entries)==8
    m.export(OUT/'Dara-Crate-Clip-r2.stl')
    d.source=lambda:source;d.source_path=lambda:SOURCE
    poses=d.write_project(EDIT,[entries],TITLE,settings_update=settings)
    f=load(EDIT);cfg=ET.fromstring(f['Metadata/model_settings.config'])
    cfg.find("plate/metadata[@key='filament_maps']").set('value','1')
    cfg.find("plate/metadata[@key='filament_volume_maps']").set('value','0')
    f['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True);save(EDIT,f)
    # Every effective value other than support toggle/revision is preserved.
    assert json.loads(f['Metadata/project_settings.config'])==settings
    report=dict(revision='r2',source=str(SOURCE),source_sha256=d.sha(SOURCE),
        source_editable=str(SOURCE_EDIT),source_editable_sha256=d.sha(SOURCE_EDIT),
        production_reference=old_report['production_reference'],
        production_dimensions_source=old_report['source'],production_dimensions_source_sha256=old_report['source_sha256'],
        protected_before=before,dimensions_mm=old_report['dimensions_mm'],quantity=8,
        change='Remove print-upper gusset only (assembly Y10..14, print Z24..28); disable supports.',
        preserved='Bed-side gusset, spacer, lip, round screw hole, clearance, orientation, placement and all other effective print settings.',
        material=old_report['material'],settings_changes_from_r1=differences(old_settings,settings),
        geometry_changes=records,poses=poses,editable_sha256=d.sha(EDIT),locked_settings=LOCKED,
        physical_fit_verified=False,shipping_load_tested=False,print_job_sent=False)
    d.save_json(OUT/'validation.json',report)
    assert protected()==before
    slice_dir=WORK/'slice';slice_dir.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (WORK/'slice.log').open('w',encoding='utf8') as log:
        run=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(slice_dir),str(EDIT)],
                           cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert run.returncode==0,(WORK/'slice.log').read_text(errors='replace')[-3000:]
    print('Native slice complete',flush=True)

def inspect_hole_paths(gcode,records):
    x=y=z=e=0.;rel_e=False;rel_xyz=False;feature='Custom'
    checks=[dict(name=r['name'],bridge_moves=0,overhang_moves=0,maximum_bridge_move_mm=0.,bridge_z_mm=set()) for r in records]
    for raw in gcode.splitlines():
        line=raw.strip()
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if cmd=='M83':rel_e=True
        elif cmd=='M82':rel_e=False
        elif cmd in ('G90','G91'):rel_xyz=cmd=='G91'
        elif cmd=='G92':
            v={k:float(n) for k,n in TOKEN.findall(code)}
            x,y,z,e=v.get('X',x),v.get('Y',y),v.get('Z',z),v.get('E',e)
        elif cmd in ('G0','G1'):
            v={k:float(n) for k,n in TOKEN.findall(code)}
            nx,ny,nz=[old+v.get(k,0) if rel_xyz else v.get(k,old) for k,old in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if rel_e else v.get('E',e)-e
            if de>0 and feature in ('Bridge','Overhang wall') and 11.4<=nz<=16.8 and (nx!=x or ny!=y):
                linegeom=LineString([(x,y),(nx,ny)])
                for r,c in zip(records,checks):
                    cx,cy,_=r['screw_center_print_mm'];region=box(cx-2.8,cy-2.5,cx+2.8,cy+2.5)
                    if linegeom.intersects(region):
                        c['overhang_moves' if feature=='Overhang wall' else 'bridge_moves']+=1
                        if feature=='Bridge':
                            c['maximum_bridge_move_mm']=max(c['maximum_bridge_move_mm'],linegeom.intersection(region).length)
                            c['bridge_z_mm'].add(round(nz,4))
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if rel_e else v.get('E',e)
    for c in checks:
        c['bridge_z_mm']=sorted(c['bridge_z_mm'])
        assert c['bridge_moves']>0 and c['maximum_bridge_move_mm']<6,c
    return checks

def validate():
    report=json.loads((OUT/'validation.json').read_text());source=load(SOURCE)
    edit=load(EDIT);sliced=load(WORK/'slice/sliced.3mf')
    result=json.loads((WORK/'slice/result.json').read_text());p=result['sliced_plates'][0]
    assert result['return_code']==0 and p['warning_message']=='',result
    old_settings=json.loads(source['Metadata/project_settings.config'])
    expected={**LOCKED,'printer_model':'Bambu Lab A1','printer_settings_id':'Bambu Lab A1 0.4 nozzle',
        'filament_type':['PETG'],'filament_settings_id':old_settings['filament_settings_id'],
        'nozzle_temperature':['255'],'nozzle_temperature_initial_layer':['255'],
        'textured_plate_temp':['80'],'textured_plate_temp_initial_layer':['80'],
        'filament_max_volumetric_speed':['8'],'enable_support':'0','enable_prime_tower':'0'}
    diffs={}
    old_overrides={props(o)['name']:[props(o),*[props(p) for p in o.findall('part')]]
                   for o in ET.fromstring(edit['Metadata/model_settings.config']).findall('object')}
    for label,pkg in [('editable',edit),('sliced',sliced)]:
        s=json.loads(pkg['Metadata/project_settings.config']);diffs[label]=differences(old_settings,s)
        assert set(diffs[label])=={'enable_support','print_settings_id'},diffs[label]
        for k,v in expected.items():assert s[k]==v,(label,k,s[k],v)
        cfg=ET.fromstring(pkg['Metadata/model_settings.config'])
        assert len(cfg.findall('object'))==8 and len(cfg.findall('plate'))==1
        for o in cfg.findall('object'):
            assert len(o.findall('part'))==1 and o.find('part').get('subtype')=='normal_part'
            for node in [o]+o.findall('part'):
                for k,v in props(node).items():
                    if k in expected:assert v==expected[k],(k,v)
                    # Only descriptive metadata may be added by native export.
                    if k in old_settings:assert k in ('extruder','name') or v==old_settings[k],(k,v)
    root=ET.fromstring(sliced['3D/3dmodel.model'])
    origids={props(o)['name']:o.get('id') for o in ET.fromstring(edit['Metadata/model_settings.config']).findall('object')}
    geometry=[];found=[]
    for it in root.find(d.tag('build')):
        pp,st=d.read_object(sliced,it.get('objectid'));a,_=d.read_object(edit,origids[st['name']])
        m=pp[0]['mesh'];ma=a[0]['mesh'];ma.apply_translation(m.bounds.mean(0)-ma.bounds.mean(0))
        err=max(cKDTree(ma.vertices).query(m.vertices)[0].max(),cKDTree(m.vertices).query(ma.vertices)[0].max())
        assert err<1e-4 and m.is_volume and len(m.split())==1
        T=transform(it.get('transform'));m.apply_transform(T)
        index=int(np.argmin([np.max(np.abs(m.bounds-np.array(r['bounds_mm']))) for r in report['geometry_changes']]))
        assert np.max(np.abs(m.bounds-np.array(report['geometry_changes'][index]['bounds_mm'])))<1e-4
        assert np.max(np.abs(T[:3,:3]-np.array(report['geometry_changes'][index]['transform'])[:3,:3]))<1e-7
        found.append(index)
        assert abs(m.bounds[0,2])<1e-4 and np.all(m.bounds[0,:2]>10) and np.all(m.bounds[1]<246)
        contact=mesh_slice(m,.1).area;assert contact>300
        geometry.append(dict(name=st['name'],mesh_roundtrip_error_mm=float(err),bounds_mm=m.bounds.tolist(),bed_contact_mm2=contact))
    assert sorted(found)==list(range(8))
    g=sliced['Metadata/plate_1.gcode'].decode();gc=dict(re.findall(r'^; (\w+) = (.*)$',g,re.M))
    for k,v in expected.items():
        if k=='filament_settings_id':continue
        assert gc.get(k)==(v[0] if isinstance(v,list) else v),(k,gc.get(k),v)
    digest=hashlib.md5(sliced['Metadata/plate_1.gcode']).hexdigest()
    assert sliced['Metadata/plate_1.gcode.md5'].decode().strip().lower()==digest
    audit=scan_gcode(g)
    assert not any(n.startswith('Support') and count>0 for n,count in audit['features'].items())
    assert audit['features'].get('Sparse infill',0)>0 and 'Prime tower' not in audit['features']
    assert audit['conservative_bed_edge_clearance_mm']>10
    assert list(audit['model_extrusion_z_by_filament_mm'])==['1']
    zs=audit['model_extrusion_z_by_filament_mm']['1'];assert len(zs)==140
    assert max(abs(z/.2-round(z/.2)) for z in zs)<.001
    holes=inspect_hole_paths(g,report['geometry_changes'])
    info=ET.fromstring(sliced['Metadata/slice_info.config'])
    warnings=[e.attrib for e in info.findall('plate/warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    srcinfo=ET.fromstring(source['Metadata/slice_info.config'])
    pid=srcinfo.find("plate/metadata[@key='printer_model_id']").get('value')
    info.find("plate/metadata[@key='printer_model_id']").set('value',pid)
    sliced['Metadata/slice_info.config']=ET.tostring(info,encoding='utf-8',xml_declaration=True)
    save(FINAL,sliced);(OUT/'native-plate-preview.png').write_bytes(sliced['Metadata/plate_1.png'])
    assert protected()==report['protected_before']
    report.update(current_file=FINAL.name,current_sha256=d.sha(FINAL),native_slice_validated=True,
        expected_effective_settings=expected,full_settings_differences=diffs,mesh_validation=geometry,
        native_result=result,native_warnings=warnings,toolpath_validation=audit,round_hole_toolpaths=holes,
        support_extrusion_moves=0,gcode_md5=digest,protected_after=protected(),
        estimated_seconds=p['total_predication'],estimated_petg_g=p['filaments'][0]['total_used_g'])
    d.save_json(OUT/'validation.json',report)
    manifest=json.loads(EDIT.with_suffix('.json').read_text());manifest.update(native_slice_validated=True,
        current_sliced_project=FINAL.name,current_sliced_sha256=d.sha(FINAL),validation_report='validation.json')
    d.save_json(EDIT.with_suffix('.json'),manifest)
    minutes=round(report['estimated_seconds']/60)
    (OUT/'README.txt').write_text(f'''Dara crate clips - A1 SUNLU PETG - r2 - NO SUPPORTS

CURRENT: {FINAL.name}
SHA-256: {d.sha(FINAL)}
Eight clips on one A1 plate. Open the 3MF as a PROJECT.
Supersedes r1. No printer job was sent.

CHANGE
Removed only the print-upper gusset: assembly Y=10..14 mm, print Z=24..28 mm.
The 4 mm bed-side gusset remains. Supports disabled; actual G-code contains
zero support, support interface or support transition extrusion.
Every other effective project setting is preserved from saved r1.
Rotations and all eight placements are unchanged.

UNCHANGED FIT
10 mm backer offset, matching the production wall-block bodies.
Fits a 13.5 mm full-height knot edge with 0.4 mm top/side clearance.
6.35 mm (1/4 inch) retaining overlap, 28 mm width, 4 mm retaining lip/upright.
Round 4.7625 mm (3/16 inch) screw hole through the 4 mm screw flange.
14 mm clear head/driver envelope; use a suitable pan-head screw for your OSB.
Avoid recessed weave, joints, M parts/pins, photo tabs and rear screws.
Place opposing clips around the knot, preserving full lip overlap.

PRINT
A1, 0.4 mm nozzle, Textured PEI Plate, SUNLU PETG (Generic PETG base).
255 C nozzle / 80 C bed / 8 mm3/s volumetric limit, unchanged from r1.
0.20 mm first/subsequent layers, 4 walls, 5 top/bottom layers, 8% gyroid.
Keep the saved side-down orientation: remaining gusset is against the bed.
Supports OFF. No brim or prime tower. Single material in slot 1.
Estimate for eight clips: {minutes//60} h {minutes%60} min / {report['estimated_petg_g']:.2f} g.

CHECKS
Exact mesh subtraction verified: only the upper gusset was removed.
Lower gusset, screw hole, spacer, lip, cavity and overall bounds are unchanged.
Eight closed connected solids; bed contact, saved poses and mesh roundtrip checked.
Native slice completed without printability warnings. Round-hole bridge/overhang
paths inspected on every clip; all 140 layers at 0.20 mm, bounds and checksum checked.
Editable/sliced settings and G-code verified, including zero support extrusion.
Production and all protected source project hashes unchanged.

Physical r2 fit, PETG hole-arch quality and shipping-load resistance are untested.
The remaining round hole prints with a small unsupported arch; check screw fit
and clear any strings after printing. This is not a measured shipping-load rating.
See validation.json for source hashes, geometry deltas, settings and toolpaths.
''',encoding='utf8')
    (OLD/'SUPERSEDED-BY-r2.txt').write_text('Superseded by ../Dara-Crate-Clips-A1-PETG-r2/Dara-Crate-Clips-A1-PETG-r2.3mf\n'
        'r2 removes the print-upper gusset and disables all supports, per user request.\n'
        'The r1 3MF files are retained unchanged for traceability. Use r2 for the revised clips.\n',encoding='utf8')
    d.save_json(OUT/'SHA256SUMS.json',{p.name:d.sha(p) for p in [FINAL,EDIT,OUT/'Dara-Crate-Clip-r2.stl',OUT/'build_clips.py']})
    print(json.dumps(dict(file=str(FINAL),sha256=d.sha(FINAL),minutes=minutes,grams=report['estimated_petg_g'],
        support_moves=0,hole_paths=holes[0],warnings=warnings),indent=2))

if __name__=='__main__':
    if '--validate' not in sys.argv:build()
    validate()
