from pathlib import Path
import json,zipfile,hashlib,re,sys,xml.etree.ElementTree as E
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
OUT=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r2'
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split('path=OUT/')[0],ns)
load,read_geometry,sha=ns['load'],ns['read_geometry'],ns['sha']
sys.path.insert(0,str(ROOT/'scripts'))
from validate_print_project import scan_gcode
C=ns['C'];P=ns['P']
report=json.loads((W/'r2-build.json').read_text())
source=load(Path(report['source_project']))
editable=load(W/'r2-editable.3mf');saved=load(W/'r2-slice/sliced.3mf')
sl=json.loads((W/'r2-slice/result.json').read_text())
assert sl['return_code']==0 and sl['sliced_plates'][0]['warning_message']==''
expected={'printer_model':'Bambu Lab A1','printer_settings_id':'Bambu Lab A1 0.4 nozzle',
 'nozzle_diameter':['0.4'],'filament_type':['PLA'],'filament_settings_id':['Generic PLA @BBL A1'],
 'nozzle_temperature':['220'],'nozzle_temperature_initial_layer':['220'],'textured_plate_temp':['65'],
 'textured_plate_temp_initial_layer':['65'],'sparse_infill_density':'8%','sparse_infill_pattern':'gyroid',
 'layer_height':'0.2','initial_layer_print_height':'0.2','wall_loops':'4','top_shell_layers':'5',
 'bottom_shell_layers':'5','curr_bed_type':'Textured PEI Plate','enable_support':'1','support_type':'normal(auto)',
 'support_style':'snug','enable_prime_tower':'0'}
settings_source=json.loads(source['Metadata/project_settings.config'])
settings_edit=json.loads(editable['Metadata/project_settings.config'])
assert {k for k in set(settings_source)|set(settings_edit) if settings_source.get(k)!=settings_edit.get(k)}=={'print_settings_id'}
for package in [editable,saved]:
 s=json.loads(package['Metadata/project_settings.config'])
 for k,v in expected.items():assert s[k]==v,(k,s[k],v)
 cfg=E.fromstring(package['Metadata/model_settings.config'])
 assert len(cfg.findall('object'))==5 and len(cfg.findall('plate'))==1
 for o in cfg.findall('object'):
  for n in [o]+o.findall('part'):
   d=ns['props'](n)
   for k,v in expected.items():
    if k in d:assert d[k]==v,(k,d[k],v)
 a=read_geometry(source);b=read_geometry(package)
 for name in a:
  av,bv=a[name].vertices,b[name].vertices
  assert a[name].faces.shape==b[name].faces.shape
  err=max(cKDTree(av).query(bv)[0].max(),cKDTree(bv).query(av)[0].max())
  assert err<.00001,(name,err)
  assert b[name].is_volume and abs(b[name].bounds[0,2])<.00001
  assert b[name].section(plane_origin=[0,0,.1],plane_normal=[0,0,1]) is not None
paint={}
for n,v in saved.items():
 if n.startswith('3D/Objects/') and n.endswith('.model'):
  x=E.fromstring(v)
  count=sum(t.get('paint_supports')=='8' for t in x.iter(C+'triangle'))
  if count:paint[n]=count
assert len(paint)==4,paint
geometry=[]
for name in a:
 m=b[name];err=max(cKDTree(a[name].vertices).query(m.vertices)[0].max(),cKDTree(m.vertices).query(a[name].vertices)[0].max())
 geometry.append(dict(part=name,unchanged_mesh_max_error_mm=err,watertight=bool(m.is_volume),bed_contact=True,bounds_mm=m.bounds.tolist()))
g=saved['Metadata/plate_1.gcode'].decode();conf=dict(re.findall(r'^; (\w+) = (.*)$',g,re.M))
for k,v in expected.items():
 if k=='filament_settings_id':continue
 assert conf.get(k)==(v[0] if isinstance(v,list) else v),(k,conf.get(k),v)
md5=hashlib.md5(saved['Metadata/plate_1.gcode']).hexdigest()
assert saved['Metadata/plate_1.gcode.md5'].decode().strip().lower()==md5
audit=scan_gcode(g)
assert audit['conservative_bed_edge_clearance_mm']>5
assert audit['features']['Support']>0 and audit['features']['Support interface']>0
supports=json.loads((W/'r2-support-check.json').read_text())
assert all(x['samples_within_expanded_envelope']==0 for x in supports['r2']['regions'].values())
assert all(x['samples_within_expanded_envelope']>0 for x in supports['r1']['regions'].values())
info=E.fromstring(saved['Metadata/slice_info.config'])
info.find("plate/metadata[@key='printer_model_id']").set('value','N2S')
saved['Metadata/slice_info.config']=E.tostring(info,encoding='utf-8',xml_declaration=True)
p=OUT/'Sanding-Block-Quarter-Sheet-A1-PLA-r2.3mf'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in saved.items():z.writestr(n,v)
assert load(p)['Metadata/plate_1.gcode']==saved['Metadata/plate_1.gcode']
report.update(project=str(p),project_sha256=sha(p),effective_settings=expected,
 saved_geometry_validation=geometry,paint_preserved_in_native_project=paint,
 support_comparison=supports,toolpath_validation=audit,gcode_md5=md5,native_slice_result=sl,
 estimated_seconds=sl['sliced_plates'][0]['total_predication'],
 estimated_pla_g=sl['sliced_plates'][0]['filaments'][0]['total_used_g'],
 digital_motion_check=json.loads((W/'r1-audit.json').read_text()),
 diagnosis='No pitch/scaling mismatch found. Native PLA r1 control slice places supports in all four thread envelopes. r2 removes those supports; physical cause and fit remain unconfirmed.',
 support_mechanism='Native blocked-support face paint, paint_supports=8; no additional volumes.',
 generator=str(W/'build_r2.py'),physical_fit_verified=False)
after={p:sha(Path(p)) for p in report['protected_hashes']}
assert report['protected_hashes']==after
report['protected_hashes_after']=after
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
(OUT/'preview.png').write_bytes(saved['Metadata/plate_1.png'])
(OUT/'README.txt').write_text(f'''Quarter-sheet sanding block - A1 PLA - r2

CURRENT SUPPORT-CORRECTION CANDIDATE
{p.name}
SHA-256: {sha(p)}

Use Bambu Studio's Open as project to retain PLA and blocked-support paint.
One plate, five original-sized adapted parts. No print job has been sent.
Paper remains 228.6 x 69.85 mm (9 x 2-3/4 inches), four short-way strips
from a 9 x 11 inch sheet.

WHAT CHANGED
Uses the user's saved Generic PLA @BBL A1 profile: 220 C nozzle, 65 C bed.
Adds native blocked-support paint to the threaded areas of Base, Screw,
Nut and Tighteneer. Supports elsewhere remain enabled. Same geometry,
thread diameters, 2.813538 mm pitch, clearances, placements and rotations.
Relative to the user's saved PLA r1, the only global setting change is the
revision name. Normal snug supports and all other process settings remain.

PRINT SETTINGS
Bambu Lab A1, 0.4 mm nozzle, Textured PEI Plate.
0.20 mm initial/subsequent layers, 4 walls, 5 top/bottom layers, 8% gyroid.
Single PLA material, saved blue color. Estimate: 4 h 21 min, 116.61 g PLA.

FINDING AND LIMITS
The user reports both threaded connections start, then bind in PLA. PETG
supports were difficult to remove. The exact printed artifact hash is
unconfirmed. This symptom does not establish whether remaining support,
thread damage, distortion or insufficient printed clearance caused binding.
The current saved PLA r1 geometry matches the delivered r1 within 0.000004 mm.
Both thread pitches match. Digital rotation/axial travel is clear over
the sampled working range; the top screw eventually reaches its stop.
Re-slicing saved PLA r1 produces support extrusion in all four threaded
regions. Those supports may obstruct fit or damage threads during removal.
This is a concrete slice defect, not proof of the physical failure's cause.

r2 removes support extrusion from all four checked thread envelopes.
Check each threaded pair separately after support cleanup, before assembly.
Existing parts remain dimensionally compatible; reuse depends on whether
their threads can be fully cleaned and have not been damaged. Reprint only
the affected parts if appropriate. The unthreaded Lock geometry is unchanged.
r2 has not been physically printed or fit-qualified. Do not force a binding
thread. Further clearance changes would require the physical fit result.

VALIDATION
Native Bambu Studio 02.08.02.61 slice succeeded with no printability warnings.
All five printable meshes remain closed solids and unchanged within 0.00001 mm.
Bed contact, stored support paint, process settings, G-code checksum and
model/support extrusion bounds checked. Support paths sampled every 0.2 mm,
including arcs, with envelopes enlarged by bead half-width plus 0.11 mm.
No support samples in those enlarged thread envelopes; supports elsewhere
remain. Saved editable and native projects plus G-code settings verified.
The current r1 project, original download and Dara.3mf hashes are unchanged.
See validation.json for exact source hashes, measurements and checks.

SOURCE
Personal adaptation of DeepDiverDude's Compact Sanding Block:
https://makerworld.com/en/models/2370141-compact-sanding-block-international-standards
Original Standard Digital File License retained.
''')
old=Path(report['source_project']).parent
(old/'WITHDRAWN-r1.txt').write_text(f'''r1 is superseded for further printing by the support-correction candidate:
{p}

User clarified that both threaded connections start, then bind in PLA.
PETG support removal was also difficult. Exact printed artifact hash is
unconfirmed. The cause of binding has not been physically established.
The current saved r1 uses Generic PLA, despite PETG in its filename.
Current saved r1 SHA-256: {report['source_sha256']}
Its 3MF has been preserved unchanged. The previous README and validation
record describe the original PETG delivery, not this later user-resaved file.
Native PLA r1 re-slicing places supports in all four thread regions.
r2 blocks these supports while retaining geometry and the user's PLA settings.
r2 physical fit remains unverified.
''')
print(json.dumps({'project':str(p),'sha256':sha(p),'seconds':report['estimated_seconds'],'grams':report['estimated_pla_g'],'geometry':geometry},indent=2))
