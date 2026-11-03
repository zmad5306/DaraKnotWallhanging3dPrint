from pathlib import Path
import json,zipfile,hashlib,re,sys,xml.etree.ElementTree as E
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
OUT=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r3'
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split('path=OUT/')[0],ns)
load,read_geometry,sha=ns['load'],ns['read_geometry'],ns['sha'];C,P=ns['C'],ns['P']
sys.path.insert(0,str(ROOT/'scripts'))
from validate_print_project import scan_gcode
report=json.loads((W/'promotion.json').read_text())
source=load(Path(report['source_project']));editable=load(W/'r3-editable.3mf');saved=load(W/'slice/sliced.3mf')
baseline=json.loads(Path(report['source_project']).with_name('validation.json').read_text())
expected=baseline['effective_settings']
source_settings=json.loads(source['Metadata/project_settings.config'])
expected_settings=dict(source_settings,**report['settings_changes'])
def norm(v):
 if isinstance(v,list):return tuple(norm(x) for x in v)
 if isinstance(v,str):
  try:return float(v)
  except ValueError:return v
 return v
def configs(files):
 cfg=E.fromstring(files['Metadata/model_settings.config'])
 return {ns['props'](o)['name']:{'object':ns['props'](o),
  'parts':[{k:v for k,v in ns['props'](p).items() if k in source_settings or k=='extruder'} for p in o.findall('part')]}
  for o in cfg.findall('object')}
source_cfg=configs(source)
for package in [editable,saved]:
 s=json.loads(package['Metadata/project_settings.config'])
 differences={k:[expected_settings.get(k),s.get(k)] for k in set(s)|set(expected_settings)
              if norm(expected_settings.get(k))!=norm(s.get(k))}
 assert not differences,differences
 for k,v in expected.items():assert s[k]==v,(k,s[k],v)
 assert configs(package)==source_cfg
 cfg=E.fromstring(package['Metadata/model_settings.config'])
 assert len(cfg.findall('plate'))==1 and len(cfg.findall('object'))==5
source_mesh_files={n:v for n,v in source.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
assert all(editable[n]==v for n,v in source_mesh_files.items())
meshes_before=read_geometry(source);meshes_after=read_geometry(saved)
assert set(meshes_before)==set(meshes_after)
geometry=[]
for name,a in meshes_before.items():
 b=meshes_after[name]
 error=max(cKDTree(a.vertices).query(b.vertices)[0].max(),cKDTree(b.vertices).query(a.vertices)[0].max())
 assert error<.00001,(name,error)
 assert b.is_volume and abs(b.bounds[0,2])<.00001
 geometry.append(dict(part=name,unchanged_mesh_max_error_mm=error,watertight=bool(b.is_volume),bounds_mm=b.bounds.tolist()))
def paint_arrays(files):
 r=E.fromstring(files['3D/3dmodel.model']);cfg=E.fromstring(files['Metadata/model_settings.config'])
 tops={o.get('id'):o for o in r.find(C+'resources')};result={}
 for o in cfg.findall('object'):
  name=ns['props'](o)['name'];co=tops[o.get('id')].find(C+'components/'+C+'component')
  child=E.fromstring(files[co.get(P+'path').lstrip('/')])
  mesh=child.find(f"{C}resources/{C}object[@id='{co.get('objectid')}']/{C}mesh")
  triangles=list(mesh.find(C+'triangles'))
  result[name]=[t.get('paint_supports','') for t in triangles]
 return result
original_paint=paint_arrays(source);new_paint=paint_arrays(saved)
assert original_paint==new_paint
sl=json.loads((W/'slice/result.json').read_text());assert sl['return_code']==0
assert sl['sliced_plates'][0]['warning_message']==''
g=saved['Metadata/plate_1.gcode'].decode();config=dict(re.findall(r'^; (\w+) = (.*)$',g,re.M))
for k,v in expected.items():
 if k=='filament_settings_id':continue
 assert config.get(k)==(v[0] if isinstance(v,list) else v),(k,config.get(k),v)
assert config['print_settings_id']==expected_settings['print_settings_id']
md5=hashlib.md5(saved['Metadata/plate_1.gcode']).hexdigest()
assert saved['Metadata/plate_1.gcode.md5'].decode().strip().lower()==md5
audit=scan_gcode(g);assert audit['conservative_bed_edge_clearance_mm']>5
assert audit['features']['Support']>0 and audit['features']['Sparse infill']>0
# Recheck the newly generated full-project support paths, including arcs.
support_source=ROOT/'.work/sanding-thread-review/verify_supports.py'
code=support_source.read_text().replace("for variant in ['r1','r2']:","for variant in ['r3']:")
code=code.replace("W/(variant+'-slice/sliced.3mf')","RELEASE_W/'slice/sliced.3mf'")
code=code.replace("W/'r2-support-check.json'","RELEASE_W/'support-check.json'")
code=code.replace("W/(variant+'-'+name+'-support.npy')","RELEASE_W/(variant+'-'+name+'-support.npy')")
exec(compile(code,str(support_source),'exec'),{'__file__':str(support_source),'RELEASE_W':W})
supports=json.loads((W/'support-check.json').read_text())
assert all(r['samples_within_expanded_envelope']==0 for r in supports['r3']['regions'].values())
info=E.fromstring(saved['Metadata/slice_info.config']);info.find("plate/metadata[@key='printer_model_id']").set('value','N2S')
saved['Metadata/slice_info.config']=E.tostring(info,encoding='utf-8',xml_declaration=True)
p=OUT/'Sanding-Block-Quarter-Sheet-A1-PLA-r3.3mf'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in saved.items():z.writestr(n,v)
assert load(p)['Metadata/plate_1.gcode']==saved['Metadata/plate_1.gcode']
after={p:sha(Path(p)) for p in report['protected_before']};assert after==report['protected_before']
report.update(project=str(p),project_sha256=sha(p),protected_after=after,
 effective_settings=expected,geometry_validation=geometry,support_paint_unchanged=True,
 support_extrusion_check=supports,toolpath_validation=audit,gcode_md5=md5,native_slice_result=sl,
 estimated_seconds=sl['sliced_plates'][0]['total_predication'],
 estimated_pla_g=sl['sliced_plates'][0]['filaments'][0]['total_used_g'],
 physical_thread_test_passed=True,full_block_physical_print_reported=False,
 paper_mm=[228.6,69.85],generator=str(W/'prepare.py'))
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
(OUT/'thread-fit-result.json').write_text(json.dumps(report['physical_thread_test'],indent=2))
(OUT/'preview.png').write_bytes(saved['Metadata/plate_1.png'])
(OUT/'README.txt').write_text(f'''Quarter-sheet sanding block - current full project r3 - A1 PLA

{p.name}
SHA-256: {sha(p)}
Open as a project in Bambu Studio to retain settings and support-blocking paint.
One plate with all five complete parts. Estimate: 4 h 21 min, 116.61 g PLA.

PROMOTION AFTER THREAD TEST
The user reports: "Threads are good make the updates to the full project."
This records a successful thread-fit result for the supplied t1 test:
{report['test_project']}
Test SHA-256: {report['test_sha256']}
Saved test printer/material: Bambu Lab A1, Generic PLA @BBL A1.
The test was cropped directly from full r2, preserving thread geometry,
clearances, orientation and support-blocking paint. No further thread resize
is needed. r3 promotes that same full design and records the successful test.

PRESERVED
All five complete parts, original print rotations, bed positions, colors,
thread diameters/pitch/clearances, and support-blocking paint match full r2.
The test crops and shortened test grip are not used as full-size parts.
All print settings and object/part overrides remain the same; only the
process/revision title and descriptive project metadata change.
Both thread pairs exclude supports; normal snug supports remain elsewhere.

PAPER AND SETTINGS
228.6 x 69.85 mm (9 x 2-3/4 inches): four short-way strips from a 9 x 11 sheet.
Bambu Lab A1, 0.4 mm nozzle, Generic PLA @BBL A1, blue saved material.
220 C nozzle, 65 C Textured PEI Plate. 0.20 mm initial/subsequent layers.
4 walls, 5 top/bottom layers, 8% gyroid. One material.

VALIDATION
Fresh native Bambu Studio 02.08.02.61 slice completed without printability
warnings. Full mesh positions, dimensions and per-face support paint match
r2. Every effective saved setting and object/part override was compared;
required settings were also checked in G-code. Five closed solids, bed
contact, extrusion bounds, and G-code checksum verified.
New support paths checked with arcs and bead-width padding: no support
extrusion samples in any of the four threaded areas.
Source r2, successful t1 and unrelated Dara.3mf hashes remain unchanged.
Details and source hashes are in validation.json. No printer job was sent.

PHYSICAL SCOPE
Thread fit is supported by the user's successful t1 result. Full-block paper
grip, sanding performance and whole-project support removal are not yet
reported. This release makes no further thread or material changes.

SOURCE
Full r2: {report['source_project']}
SHA-256: {report['source_sha256']}
Original design: DeepDiverDude, MakerWorld model 2370141.
https://makerworld.com/en/models/2370141-compact-sanding-block-international-standards
Original Standard Digital File License retained.
''')
# Preserve the printed test and source 3MF bytes; update their external status.
test=Path(report['test_project']);test_report=json.loads(test.with_name('validation.json').read_text())
test_report.update(physical_fit_verified=True,physical_fit_scope='User-reported thread fit on t1; not a full assembly print.',
 physical_thread_test=report['physical_thread_test'],promoted_full_project=str(p),promoted_full_project_sha256=sha(p))
test.with_name('validation.json').write_text(json.dumps(test_report,indent=2))
test.with_name('PHYSICAL-RESULT.txt').write_text(f'''t1 thread test: USER-REPORTED PASS, 2026-10-22
User: "Threads are good make the updates to the full project."
Test SHA-256: {report['test_sha256']}
Current full project: {p}
Full project SHA-256: {sha(p)}
The supplied test used A1/PLA settings. Thread fit only; full assembly not reported.
The test 3MF has not changed.
''')
readme=test.with_name('README.txt');text=readme.read_text().replace('This test is not yet physically qualified.',
 'User reports the threads are good (2026-10-22). Thread fit passed; see\nPHYSICAL-RESULT.txt. The same setup is promoted to the full r3 project.')
readme.write_text(text)
src=Path(report['source_project']);src.with_name('SUPERSEDED-BY-r3.txt').write_text(f'''r2 is retained as the unchanged source of the successful t1 thread test.
Use the current full project: {p}
SHA-256: {sha(p)}
Same full geometry and support paint; freshly sliced and associated with t1 pass.
''')
sr=src.with_name('README.txt');text=sr.read_text()
prefix=f'ARCHIVED SOURCE: Current full project is r3. See SUPERSEDED-BY-r3.txt.\nThe t1 thread test passed and its unchanged setup is promoted to r3.\n\n'
if not text.startswith('ARCHIVED SOURCE:'):sr.write_text(prefix+text)
assert after=={p:sha(Path(p)) for p in after}
print(json.dumps({'project':str(p),'sha256':sha(p),'seconds':report['estimated_seconds'],'grams':report['estimated_pla_g'],
 'physical_thread_test_passed':True,'mesh_errors_mm':[x['unchanged_mesh_max_error_mm'] for x in geometry]},indent=2))
