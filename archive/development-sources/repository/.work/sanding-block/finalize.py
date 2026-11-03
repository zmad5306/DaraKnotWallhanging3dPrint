from pathlib import Path
import hashlib,json,re,shutil,sys,zipfile,xml.etree.ElementTree as ET
import numpy as np
import trimesh
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
W=Path(__file__).resolve().parent
OUT=ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PETG'
sys.path.insert(0,str(ROOT/'scripts'))
from validate_print_project import scan_gcode
C='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        return {n:z.read(n) for n in z.namelist()}
def props(o):return {e.get('key'):e.get('value') for e in o.findall('metadata') if e.get('key')}
def transform(s):
    t=np.eye(4)
    if s:t[:3]=np.array([float(v) for v in s.split()]).reshape(4,3).T
    return t
def read_geometry(files):
    r=ET.fromstring(files['3D/3dmodel.model'])
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    names={o.get('id'):props(o)['name'] for o in cfg.findall('object')}
    top={o.get('id'):o for o in r.find(C+'resources')}
    result={}
    for item in r.find(C+'build'):
        oid=item.get('objectid');o=top[oid]
        co=o.find(C+'components/'+C+'component')
        ch=ET.fromstring(files[co.get(P+'path').lstrip('/')])
        ob=next(a for a in ch.find(C+'resources') if a.get('id')==co.get('objectid'))
        m=ob.find(C+'mesh')
        vs=np.array([[float(v.get(k)) for k in ('x','y','z')] for v in m.find(C+'vertices')])
        fs=np.array([[int(f.get(k)) for k in ('v1','v2','v3')] for f in m.find(C+'triangles')])
        t=transform(item.get('transform'))@transform(co.get('transform'))
        vs=vs@t[:3,:3].T+t[:3,3]
        # Validate the indexed topology as stored. Tolerance-based welding of
        # already-indexed float32 vertices can itself create nonmanifold edges.
        tm=trimesh.Trimesh(vs,fs,process=False)
        result[names[oid]]=tm
    return result
path=OUT/'Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'
editable=load(path);sliced=load(W/'slice-clean/sliced.3mf')
result=json.loads((W/'slice-clean/result.json').read_text())
assert result['return_code']==0
assert result['sliced_plates'][0]['warning_message']==''
expected={'printer_model':'Bambu Lab A1','printer_settings_id':'Bambu Lab A1 0.4 nozzle',
          'nozzle_diameter':['0.4'],'sparse_infill_density':'8%','sparse_infill_pattern':'gyroid',
          'wall_loops':'4','top_shell_layers':'5','bottom_shell_layers':'5',
          'layer_height':'0.2','initial_layer_print_height':'0.2',
          'curr_bed_type':'Textured PEI Plate','filament_type':['PETG'],
          'filament_settings_id':['Generic PETG @BBL A1'],'enable_support':'1',
          'support_type':'normal(auto)','enable_prime_tower':'0'}
for package in [editable,sliced]:
    s=json.loads(package['Metadata/project_settings.config'])
    for k,v in expected.items():assert s[k]==v,(k,s[k],v)
    cfg=ET.fromstring(package['Metadata/model_settings.config'])
    for obj in cfg.findall('object'):
        for node in [obj]+obj.findall('part'):
            d=props(node)
            for k,v in expected.items():
                if k in d:assert d[k]==v,(k,d[k],v)
    assert len(cfg.findall('object'))==5 and len(cfg.findall('plate'))==1

a,b=read_geometry(editable),read_geometry(sliced)
assert set(a)==set(b)
geometry=[]
for name in a:
    ma,mb=a[name],b[name]
    err=max(cKDTree(ma.vertices).query(mb.vertices)[0].max(),
            cKDTree(mb.vertices).query(ma.vertices)[0].max())
    assert err<1e-4,(name,err)
    assert mb.is_volume and abs(mb.bounds[0,2])<1e-4, (name,mb.is_watertight,mb.is_winding_consistent,mb.volume,mb.bounds.tolist())
    section=mb.section(plane_origin=[0,0,.1],plane_normal=[0,0,1])
    assert section is not None
    geometry.append(dict(name=name,max_vertex_roundtrip_error_mm=float(err),
                         watertight=bool(mb.is_volume),bed_contact_cross_section=True,
                         on_bed_bounds_mm=mb.bounds.tolist()))
g=sliced['Metadata/plate_1.gcode'].decode()
config=dict(re.findall(r'^; (\w+) = (.*)$',g,re.M))
for k,v in expected.items():
    if k=='filament_settings_id':continue
    scalar=v[0] if isinstance(v,list) else v
    assert config.get(k)==scalar,(k,config.get(k),scalar)
digest=hashlib.md5(sliced['Metadata/plate_1.gcode']).hexdigest()
assert sliced['Metadata/plate_1.gcode.md5'].decode().strip().lower()==digest
audit=scan_gcode(g)
assert audit['conservative_bed_edge_clearance_mm']>5
assert audit['features']['Support']>0 and audit['features']['Support interface']>0
assert audit['features']['Sparse infill']>0
assert 'Prime tower' not in audit['features']
assert list(audit['model_extrusion_z_by_filament_mm'])==['1']
info=ET.fromstring(sliced['Metadata/slice_info.config'])
pid=json.loads(Path(r'C:\Program Files\Bambu Studio\resources\profiles\BBL\machine\Bambu Lab A1.json').read_text())['model_id']
info.find("plate/metadata[@key='printer_model_id']").set('value',pid)
sliced['Metadata/slice_info.config']=ET.tostring(info,encoding='utf-8',xml_declaration=True)
shutil.copy2(path,W/'editable-validated.3mf')
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
    for n,data in sliced.items():z.writestr(n,data)
assert load(path)['Metadata/plate_1.gcode']==sliced['Metadata/plate_1.gcode']
report=json.loads((OUT/'validation.json').read_text())
report.update(editable_project_sha256=sha(W/'editable-validated.3mf'),
              project_sha256=sha(path),native_slice_validated=True,
              saved_geometry_roundtrip=geometry,toolpath_validation=audit,
              effective_settings=expected,printer_model_id=pid,
              gcode_md5=digest,native_slice_result=result,
              estimated_seconds=result['sliced_plates'][0]['total_predication'],
              estimated_petg_g=result['sliced_plates'][0]['filaments'][0]['total_used_g'],
              support_note='Snug automatic supports enabled to resolve native floating-cantilever warnings on widened body and tensioner.',
              assembly_check_scope='No additional overlap relative to scaled original CAD placement. Original screw/thread phase overlaps retained; this is not a physical thread-fit test.',
              generator=str(W/'build.py'))
assert all(sha(Path(p))==h for p,h in report['protected_before'].items())
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
(OUT/'preview.png').write_bytes(sliced['Metadata/plate_1.png'])
(OUT/'native-slice-result.json').write_text(json.dumps(result,indent=2))
parts=OUT/'parts';parts.mkdir(exist_ok=True)
for name in ['Base','Tighteneer','Lock','Nut','Screw']:
    source=OUT/(name+'.stl');dest=parts/source.name
    assert source.resolve().is_relative_to(OUT.resolve()) and dest.resolve().is_relative_to(OUT.resolve())
    if source.exists():source.replace(dest)
minutes=round(report['estimated_seconds']/60)
(OUT/'README.txt').write_text(f"""Quarter-sheet sanding block - A1 PETG - revision 1

CURRENT PROJECT
{path.name}
SHA-256: {sha(path)}

PAPER
228.6 x 69.85 mm (9 x 2-3/4 inches).
Cut a 9 x 11 inch sheet across its short dimension into four equal strips.
This is NOT the 4-1/2 x 5-1/2 inch quarter-sheet format.

DESIGN
Personal adaptation of Compact Sanding Block - International Standards,
by DeepDiverDude: {report['source_model_url']}
Source: {report['source']}
Source SHA-256: {report['source_sha256']}
Source profile: 23mm - Single Color.
Mechanism uniformly scaled by {report['uniform_scale']:.10f} so the designer's
162.5 mm paper strip specification becomes 228.6 mm.
Base, clamp and rear tensioner widened to 69.85 mm using two
{report['side_extension_per_side_mm']:.6f} mm constant-section side extensions.
Central threads stay circular; no nonuniform screw scaling.
Numerical mesh-edge cleanup uses a 0.001 mm tolerance for reliable saving.
Original print rotations retained; positions rearranged onto one A1 plate.

PRINT PROJECT
Bambu Lab A1, 0.4 mm nozzle, Generic PETG, Textured PEI Plate.
0.20 mm initial and subsequent layers; 4 walls; 5 top and 5 bottom layers.
8% gyroid. Single material. Automatic snug supports and automatic brim.
Saved Generic PETG temperatures: nozzle {config['nozzle_temperature']} C,
bed {config['textured_plate_temp']} C.
Bambu Studio estimate: {minutes//60} h {minutes%60} min, {report['estimated_petg_g']:.2f} g.
Open this 3MF as a project to retain its settings and stored slice.
If your PETG has a manufacturer-specific profile, select it and reslice.

ASSEMBLY
Remove supports, including those around the rear opening.
Fit the rear tensioner and its thumbwheel nut into the base.
Fit the front clamp with the top screw. Wrap the entire 9 x 2-3/4 inch strip
around the sanding surfaces, capture both ends beneath the clamp, tighten
the top screw, then turn the rear thumbwheel to tension the paper.

VALIDATION AND LIMITS
Five closed solid meshes; bed contact and plate spacing checked.
Saved mesh coordinates matched the editable source within 0.0001 mm.
Native Bambu Studio 02.08.02.61 slice completed with no printability warning.
Support and support-interface extrusion verified in actual G-code.
Settings checked in editable 3MF, sliced 3MF and G-code configuration.
G-code checksum and model/support extrusion bounds verified.
Source project and Dara.3mf hashes unchanged.
The target wrap is derived from the designer's stated paper length.
This revision has NOT been physically printed: PETG thread fit, paper grip,
support removal and real sandpaper thickness remain to be confirmed.
No printer job was sent.

See validation.json for exact measurements and checks.
Original creator's Standard Digital File License retained.
""",encoding='utf8')
print(json.dumps(dict(project=str(path),sha256=sha(path),seconds=report['estimated_seconds'],
                      grams=report['estimated_petg_g'],bed_clearance_mm=audit['conservative_bed_edge_clearance_mm'],
                      roundtrip_max_mm=max(v['max_vertex_roundtrip_error_mm'] for v in geometry)),indent=2))
