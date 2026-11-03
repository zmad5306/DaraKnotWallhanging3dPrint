from pathlib import Path
import json,sys,zipfile,hashlib,re,xml.etree.ElementTree as E
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
OUT=ROOT/'output/Sanding-Block-Thread-Test-A1-PLA-t1'
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split('path=OUT/')[0],ns)
load,read_geometry,sha=ns['load'],ns['read_geometry'],ns['sha'];C=ns['C']
sys.path.insert(0,str(ROOT/'scripts'))
from validate_print_project import scan_gcode
report=json.loads((W/'build.json').read_text())
source=load(Path(report['source']));editable=load(W/'test-editable.3mf');saved=load(W/'slice/sliced.3mf')
result=json.loads((W/'slice/result.json').read_text());assert result['return_code']==0
assert result['sliced_plates'][0]['warning_message']==''
expected=json.loads(Path(report['source']).with_name('validation.json').read_text())['effective_settings']
original_settings=json.loads(source['Metadata/project_settings.config'])
edit_settings=json.loads(editable['Metadata/project_settings.config'])
settings_diff={k:[original_settings.get(k),edit_settings.get(k)] for k in set(original_settings)|set(edit_settings) if original_settings.get(k)!=edit_settings.get(k)}
assert set(settings_diff)=={'print_settings_id'}
def overrides(package):
 cfg=E.fromstring(package['Metadata/model_settings.config']);out={}
 for o in cfg.findall('object'):
  part=o.find('part');name=ns['props'](part)['name']
  out[name]={}
  for key,node in [('object',o),('part',part)]:
   out[name][key]={k:v for k,v in ns['props'](node).items() if k in original_settings and k!='name'}
 return out
original_overrides=overrides(source)
for package in [editable,saved]:
 settings=json.loads(package['Metadata/project_settings.config'])
 for k,v in expected.items():assert settings[k]==v,(k,settings[k],v)
 cfg=E.fromstring(package['Metadata/model_settings.config'])
 assert len(cfg.findall('object'))==4 and len(cfg.findall('plate'))==1
 for name,ov in overrides(package).items():assert ov==original_overrides[name],(name,ov,original_overrides[name])
 # Compare every effective process setting; native serialization may normalize
 # numeric text but must not change the value.
 def canonical(v):
  if isinstance(v,list):return tuple(canonical(x) for x in v)
  if isinstance(v,str):
   try:return float(v)
   except ValueError:return v
  return v
 diffs={k:[edit_settings.get(k),settings.get(k)] for k in set(edit_settings)|set(settings)
        if canonical(edit_settings.get(k))!=canonical(settings.get(k))}
 if package is saved:report['native_settings_serialization_differences']=diffs
 assert not diffs,diffs
a=read_geometry(editable);b=read_geometry(saved);assert set(a)==set(b)
geometry=[]
for name,m in b.items():
 err=max(cKDTree(a[name].vertices).query(m.vertices)[0].max(),cKDTree(m.vertices).query(a[name].vertices)[0].max())
 assert err<.0001,(name,err)
 assert m.is_volume and abs(m.bounds[0,2])<.0001,(name,m.is_watertight,m.bounds.tolist())
 section=m.section(plane_origin=[0,0,.1],plane_normal=[0,0,1]);assert section is not None
 geometry.append({'name':name,'mesh_roundtrip_error_mm':err,'watertight':bool(m.is_volume),'bed_contact':True,'bounds_mm':m.bounds.tolist()})
paint=[]
for package in [editable,saved]:
 counts=[]
 for n,v in package.items():
  if n.startswith('3D/Objects/') and n.endswith('.model'):
   counts.append(sum(x.get('paint_supports')=='8' for x in E.fromstring(v).iter(C+'triangle')))
 assert len(counts)==4 and min(counts)>0
 paint.append(sorted(counts))
assert paint[0]==paint[1]
g=saved['Metadata/plate_1.gcode'].decode();conf=dict(re.findall(r'^; (\w+) = (.*)$',g,re.M))
for k,v in expected.items():
 if k=='filament_settings_id':continue
 assert conf.get(k)==(v[0] if isinstance(v,list) else v),(k,conf.get(k),v)
md5=hashlib.md5(saved['Metadata/plate_1.gcode']).hexdigest();assert saved['Metadata/plate_1.gcode.md5'].decode().strip().lower()==md5
audit=scan_gcode(g);assert audit['conservative_bed_edge_clearance_mm']>5
assert audit['features']['Sparse infill']>0
assert sum(audit['features'].get(k,0) for k in ['Support','Support interface','Support transition'])>0
support=json.loads((W/'support-check.json').read_text())
assert all(x['samples_within_expanded_envelope']==0 for x in support['t1']['regions'].values())
info=E.fromstring(saved['Metadata/slice_info.config']);info.find("plate/metadata[@key='printer_model_id']").set('value','N2S')
saved['Metadata/slice_info.config']=E.tostring(info,encoding='utf-8',xml_declaration=True)
p=OUT/'Sanding-Block-Thread-Test-A1-PLA-t1.3mf'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for n,v in saved.items():z.writestr(n,v)
assert load(p)['Metadata/plate_1.gcode']==saved['Metadata/plate_1.gcode']
after={p:sha(Path(p)) for p in report['protected_before']};assert after==report['protected_before']
plate=result['sliced_plates'][0]
report.update(project=str(p),project_sha256=sha(p),protected_after=after,
 effective_settings=expected,settings_comparison=settings_diff,saved_mesh_validation=geometry,
 support_paint_faces_preserved=paint[1],support_extrusion_check=support,toolpath_validation=audit,
 gcode_md5=md5,native_slice_result=result,estimated_seconds=plate['total_predication'],
 estimated_pla_g=plate['filaments'][0]['total_used_g'],physical_fit_verified=False)
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
(OUT/'preview.png').write_bytes(saved['Metadata/plate_1.png'])
(OUT/'README.txt').write_text(f'''Sanding block thread fit test t1 - A1 PLA

CURRENT TEST
{p.name}
SHA-256: {sha(p)}
One plate, four parts. Open as a project in Bambu Studio.
Estimate: 1 hour 19 minutes, 26.66 g PLA. No print job was sent.

WHAT IT TESTS
Both full-length thread pairs from the support-corrected quarter-sheet r2.
No thread diameter, pitch (2.813538 mm), lead-in or clearance changes.
Support-blocking paint is preserved on the retained original faces.
The known earlier PLA symptom was: both pairs start, then bind.
This test is not yet physically qualified.

PAIRING AND CHECK
1A Top threaded socket goes with 1B Top screw.
2A Rear threaded shaft goes with 2B Rear thumbwheel nut.
The object names identify the pairs in Bambu Studio. They are not embossed.
Remove the small amount of support outside the threads. Let parts cool.
Try each pair separately by hand. Check rotation and axial travel before
the screw head or nut reaches its normal seating shoulder/stop.
Report whether each pair runs freely, and how many turns it makes before
binding if it does. Do not mistake normal seating for binding or force it.
No sandpaper or clamp assembly is needed for this fit check.

SETTINGS
Bambu Lab A1, 0.4 mm nozzle, Generic PLA @BBL A1, saved blue material.
220 C nozzle, 65 C Textured PEI Plate. 0.20 mm initial/subsequent layers,
4 walls, 5 top/bottom layers, 8% gyroid. Normal snug supports outside threads.
All effective print settings and object/part overrides match r2; only the
process name changes. Original physical print orientations are retained.

SOURCE AND CROPS
Source: {report['source']}
Source SHA-256: {report['source_sha256']}
Only this saved r2 supplies the geometry; the full project is unchanged.
Crops use r2 plate coordinates in millimeters:
Base: X 58.5..81.5, Y 59..90, Z 4..35.
Tighteneer: X 58.6..81.4, Y 142..184, Z 6..45.
Screw: X 180..220, Y 45..85, Z 8.4..40 (shortens only the grip below threads).
Nut: unchanged whole part.
The complete padded thread envelopes fit inside these crop boxes.
Each crop is moved in XY onto the test plate and seated on the bed. Z moves
are -4 mm Base, -6 mm Tighteneer, -8.4 mm Screw, 0 mm Nut: whole-layer offsets.
No feet, pads or new mechanisms were added. Unthreaded Lock is omitted.
Cropping changes surrounding body/grip stock; this checks threads, not full
assembly strength, paper fit or full-block printing behavior.

VALIDATION
Native Bambu Studio 02.08.02.61 slice succeeds with no printability warnings.
Four closed solid meshes and bed contact checked. Crops agree with exact
source intersections; the full padded threaded areas are retained.
Native saved geometry matches editable geometry within 0.0001 mm.
Support paint and all effective process/object/part settings preserved.
Editable 3MF, sliced 3MF and G-code settings checked; checksum and bed bounds
verified. Arc-aware support path samples at <=0.2 mm spacing, with bead-width
padding, show zero support extrusion samples in all four thread envelopes.
Source r2 and Dara.3mf hashes unchanged. Details are in validation.json.

Original design by DeepDiverDude, MakerWorld model 2370141.
Original Standard Digital File License retained.
''')
print(json.dumps({'file':str(p),'sha256':sha(p),'seconds':report['estimated_seconds'],'grams':report['estimated_pla_g'],'geometry':geometry},indent=2))
