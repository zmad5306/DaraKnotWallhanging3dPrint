from pathlib import Path
import json,zipfile,hashlib,re,sys,xml.etree.ElementTree as E
import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union
import shapely
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
ns={'__file__':str(ROOT/'.work/sanding-block/finalize.py')}
exec((ROOT/'.work/sanding-block/finalize.py').read_text().split('path=OUT/')[0],ns)
load,read_geometry,sha,tf=ns['load'],ns['read_geometry'],ns['sha'],ns['transform'];C,P=ns['C'],ns['P']
report=json.loads((W/'r4-change.json').read_text())
src=Path(report['source_project']);source=load(src);editable=load(W/'r4-editable.3mf');saved=load(W/'r4-slice/sliced.3mf')
base_settings=json.loads(source['Metadata/project_settings.config']);want=dict(base_settings,**report['process_metadata_change'])
def norm(v):
    if isinstance(v,list):return tuple(norm(x) for x in v)
    if isinstance(v,str):
        try:return float(v)
        except ValueError:return v
    return v
def configs(files):
    r=E.fromstring(files['Metadata/model_settings.config'])
    return {ns['props'](o)['name']:{'object':ns['props'](o),'parts':[{k:v for k,v in ns['props'](p).items() if k in base_settings or k=='extruder'} for p in o.findall('part')]} for o in r.findall('object')}
def mesh_and_paint(files):
    root=E.fromstring(files['3D/3dmodel.model']);cfg=E.fromstring(files['Metadata/model_settings.config'])
    tops={o.get('id'):o for o in root.find(C+'resources')};out={}
    for o in cfg.findall('object'):
        name=ns['props'](o)['name'];co=tops[o.get('id')].find(C+'components/'+C+'component')
        ch=E.fromstring(files[co.get(P+'path').lstrip('/')]);mesh=ch.find(f"{C}resources/{C}object[@id='{co.get('objectid')}']/{C}mesh")
        out[name]=E.tostring(mesh)
    return out
for pack in [editable,saved]:
    s=json.loads(pack['Metadata/project_settings.config'])
    diff={k:[want.get(k),s.get(k)] for k in set(want)|set(s) if norm(want.get(k))!=norm(s.get(k))}
    assert not diff,diff
    assert configs(pack)==configs(source)
    assert mesh_and_paint(pack)==mesh_and_paint(source),'Geometry or face paint changed'
old=read_geometry(source);new=read_geometry(saved);expected=read_geometry(editable)
geometry=[]
for name,m in new.items():
    error=float(np.max(np.abs(m.vertices-expected[name].vertices)))
    assert error<1e-5 and m.is_volume and abs(m.bounds[0,2])<1e-5,(name,error)
    if name!='Lock - quarter sheet':assert np.array_equal(m.vertices,old[name].vertices)
    geometry.append({'name':name,'roundtrip_max_coordinate_error_mm':error,'volume_valid':bool(m.is_volume),'bounds_mm':m.bounds.tolist(),'unchanged_pose':name!='Lock - quarter sheet'})
lock=new['Lock - quarter sheet'];idx=report['flat_vertex_indices']
assert lock.vertices[idx,2].max()<.002
sl=json.loads((W/'r4-slice/result.json').read_text());assert sl['return_code']==0 and sl['sliced_plates'][0]['warning_message']==''
g=saved['Metadata/plate_1.gcode'].decode();gcfg=dict(re.findall(r'^; (\w+) = (.*)$',g,re.M))
locked=json.loads(src.with_name('validation.json').read_text())['effective_settings']
for k,v in locked.items():
    if k=='filament_settings_id':continue
    assert gcfg.get(k)==(v[0] if isinstance(v,list) else v),(k,gcfg.get(k),v)
md5=hashlib.md5(saved['Metadata/plate_1.gcode']).hexdigest();assert saved['Metadata/plate_1.gcode.md5'].decode().strip().lower()==md5
sys.path.insert(0,str(ROOT/'scripts'));from validate_print_project import scan_gcode
audit=scan_gcode(g);assert audit['conservative_bed_edge_clearance_mm']>5
# Recheck native support paths against the four physically accepted thread envelopes.
support_source=ROOT/'.work/sanding-thread-review/verify_supports.py'
code=support_source.read_text().replace("for variant in ['r1','r2']:","for variant in ['r4']:")
code=code.replace("W/(variant+'-slice/sliced.3mf')","RELEASE_W/'r4-slice/sliced.3mf'")
code=code.replace("W/'r2-support-check.json'","RELEASE_W/'r4-support-check.json'")
code=code.replace("W/(variant+'-'+name+'-support.npy')","RELEASE_W/(variant+'-'+name+'-support.npy')")
exec(compile(code,str(support_source),'exec'),{'__file__':str(support_source),'RELEASE_W':W})
supports=json.loads((W/'r4-support-check.json').read_text());assert all(r['samples_within_expanded_envelope']==0 for r in supports['r4']['regions'].values())
# Evaluate the leading edge using actual extruded bead footprints on layer one.
def edge_check(path):
    segs=json.loads(path.read_text());models=[s for s in segs if s['feature'] not in ['Brim','Skirt'] and not s['feature'].startswith('Support')]
    first=[s for s in models if abs(s['pts'][0][2]-.2)<.001]
    second=[s for s in models if abs(s['pts'][0][2]-.4)<.001]
    footprint=unary_union([LineString(np.array(s['pts'])[:,:2]).buffer(s['width']/2) for s in first])
    pts=[]
    for s in second:
        p=np.array(s['pts'])
        for a,b in zip(p[:-1],p[1:]):
            pts.extend(a+(b-a)*np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/.1)+2))[:,None])
    pts=np.array(pts);pts=pts[(pts[:,0]>136)&(pts[:,0]<202)&(pts[:,1]<155)]
    distances=shapely.distance(shapely.points(pts[:,:2]),footprint)
    b1=np.concatenate([s['pts'] for s in first]);b2=np.concatenate([s['pts'] for s in second])
    return {'first_layer_model_bounds_mm':[b1.min(axis=0).tolist(),b1.max(axis=0).tolist()],
            'second_layer_model_bounds_mm':[b2.min(axis=0).tolist(),b2.max(axis=0).tolist()],
            'layer_two_leading_edge_samples':len(pts),'max_centerline_outside_previous_bead_mm':float(distances.max()),
            'sampling_interval_mm':.1,'region':'bed X136..202, Y<155 at Z0.4; excludes side corners'}
edges={'r3':edge_check(W/'low-paths.json'),'r4':edge_check(W/'r4-check/low-paths.json')}
assert edges['r3']['max_centerline_outside_previous_bead_mm']>4
assert edges['r4']['max_centerline_outside_previous_bead_mm']<.1,edges
info=E.fromstring(saved['Metadata/slice_info.config']);info.find("plate/metadata[@key='printer_model_id']").set('value','N2S')
saved['Metadata/slice_info.config']=E.tostring(info,encoding='utf-8',xml_declaration=True)
OUT=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PLA-r4';OUT.mkdir(exist_ok=True)
target=OUT/'Sanding-Block-Quarter-Sheet-A1-PLA-r4.3mf'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for n,v in saved.items():z.writestr(n,v)
assert all(sha(Path(p))==h for p,h in report['protected_before'].items())
assert load(target)['Metadata/plate_1.gcode']==saved['Metadata/plate_1.gcode']
report.update(project=str(target),project_sha256=sha(target),geometry_validation=geometry,all_meshes_and_support_paint_unchanged=True,
              settings_changes={'print_settings_id':want['print_settings_id']},effective_settings=locked,toolpath_validation=audit,
              gcode_md5=md5,native_slice_result=sl,thread_support_check=supports,leading_edge_check=edges,
              estimated_seconds=sl['sliced_plates'][0]['total_predication'],estimated_pla_g=sl['sliced_plates'][0]['filaments'][0]['total_used_g'])
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
(OUT/'preview.png').write_bytes(saved['Metadata/plate_1.png'])
(OUT/'thread-fit-result.json').write_text(json.dumps(report['physical_thread_test'],indent=2))
(OUT/'README.txt').write_text(f'''Quarter-sheet sanding block - current full project r4 - A1 PLA

{target.name}
SHA-256: {sha(target)}
Open as a project in Bambu Studio to retain its saved configuration.
All five complete parts. Estimated 4 h 21 min, {report['estimated_pla_g']:.2f} g PLA.

CHANGED: Lock clamp print orientation only.
Rotated {report['rotation_degrees']:.6f} degrees using the minimum rotation to
align the existing flat underside with the bed, then seated at Z0.
Old face height varied by 0.2004 mm. Corrected variation is below 0.001 mm.
The old second layer extended about 5.2 mm beyond the first along the leading
edge. The fresh native slice now begins with the full flat footprint.
No model dimensions, meshes, threads, support paint or process values changed.
Other four parts retain exactly the same bed coordinates and settings.

A1, 0.4 mm nozzle, Generic PLA, 0.20 mm layers/initial layer, 4 walls,
5 top/bottom layers, 8% gyroid, Textured PEI, 220 C nozzle / 65 C bed.
Supports, brims, speeds and cooling preserved from r3.

VALIDATION: native Bambu slice succeeded without warnings; saved mesh and paint
comparison, pose/settings checks, first-layer/second-layer extrusion coverage,
bed bounds and G-code checksum passed. No support extrusion in the four
protected thread envelopes. Source r3, physical t1 test and Dara file unchanged.
Thread fit was reported good on t1. This new clamp orientation has not yet been
physically printed; surface quality and full assembly/paper grip remain unverified.
No printer job was sent.

SOURCE: {src}
Source SHA-256: {report['source_sha256']}
Personal adaptation of Compact Sanding Block - International Standards by
DeepDiverDude, https://makerworld.com/en/models/2370141-compact-sanding-block-international-standards
Standard Digital File License. Paper size 228.6 x 69.85 mm (9 x 2-3/4 inches).
''')
(src.parent/'SUPERSEDED-BY-r4.txt').write_text('Superseded by ../Sanding-Block-Quarter-Sheet-A1-PLA-r4/Sanding-Block-Quarter-Sheet-A1-PLA-r4.3mf\nThe r4 project levels the Lock underside on the bed. Meshes, working threads and process settings are unchanged.\nThe r3 file remains intact as a historical reference.\n')
print(json.dumps({'project':str(target),'sha256':sha(target),'edge_check':edges,'estimated_seconds':report['estimated_seconds'],'estimated_pla_g':report['estimated_pla_g']},indent=2))
