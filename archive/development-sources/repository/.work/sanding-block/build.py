"""Personal adaptation of DeepDiverDude's Compact Sanding Block.

All dimensions in mm. No Dara production files are modified.
"""
from pathlib import Path
import hashlib, json, sys, zipfile, xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as mf

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
OUT = ROOT / 'output/Sanding-Block-Quarter-Sheet-A1-PETG'
OUT.mkdir(parents=True, exist_ok=True)
SRC = Path(r'C:\Users\Zach\Downloads\Sanding_Block.3mf')
PROFILE = Path(r'C:\Program Files\Bambu Studio\resources\profiles\BBL')
sys.path.insert(0, str(ROOT/'scripts'))
from build_jointed_bambu_project import C, P, R, IDENTITY, tag, uid, meta, xml, model
from development_3mf import mesh_xml, mesh as from_solid, solid

SCALE = 228.6 / 162.5
WIDTH = 69.85
CUT = 11.0 * SCALE
EXTRA = (WIDTH - 23*SCALE)/2
TITLE = 'Quarter sheet sanding block - A1 PETG - 8% gyroid - r1'
protected = [ROOT/'Dara.3mf', SRC]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
protected_before = {str(p):sha(p) for p in protected}

def resolve(kind, name):
    paths = list((PROFILE/kind).rglob(name+'.json'))
    assert len(paths) == 1, (name, paths)
    d = json.loads(paths[0].read_text())
    r = resolve(kind, d['inherits']) if d.get('inherits') else {}
    for inc in d.get('include', []): r.update(resolve(kind, inc))
    r.update({k:v for k,v in d.items() if k not in (
        'inherits','include','name','type','from','instantiation','description',
        'compatible_printers','setting_id')})
    return r

def tf(text):
    a = np.eye(4); a[:3] = np.array(list(map(float,text.split()))).reshape(4,3).T
    return a

def widen(m):
    # Preserve the entire central 22 mm of the original geometry (including
    # circular threads). Add two constant-section strips just inside side faces.
    r = m.rotate((90,0,0))
    top, rest = r.split_by_plane((0,0,1), CUT)
    mid, bottom = rest.split_by_plane((0,0,1), -CUT)
    upper_fill = r.slice(CUT).extrude(EXTRA).translate((0,0,CUT))
    lower_fill = r.slice(-CUT).extrude(EXTRA).translate((0,0,-CUT-EXTRA))
    return (mid + top.translate((0,0,EXTRA)) + bottom.translate((0,0,-EXTRA))
            + upper_fill + lower_fill).rotate((-90,0,0))

with zipfile.ZipFile(SRC) as z:
    original = {n:z.read(n) for n in z.namelist()}
cfg = ET.fromstring(original['Metadata/model_settings.config'])
src_root = ET.fromstring(original['3D/3dmodel.model'])
poses = {int(e.get('objectid')):tf(e.get('transform')) for e in src_root.find(tag('build'))}
src_objects = {int(e.get('id')):e for e in src_root.find(tag('resources'))}
settings = json.loads(original['Metadata/project_settings.config'])
settings.update(resolve('machine','Bambu Lab A1 0.4 nozzle'))
settings.update(resolve('process','0.20mm Standard @BBL A1'))
settings.update(resolve('filament','Generic PETG @BBL A1'))
settings.update(
    printer_model='Bambu Lab A1', printer_settings_id='Bambu Lab A1 0.4 nozzle',
    print_compatible_printers=['Bambu Lab A1 0.4 nozzle'],
    printer_variant='0.4', print_settings_id=TITLE, print_sequence='by layer',
    filament_settings_id=['Generic PETG @BBL A1'], filament_ids=['GFG99'],
    filament_colour=['#A6A9AA'], filament_multi_colour=['#A6A9AA'],
    filament_self_index=['1'], filament_map=['1'], filament_map_2=['1'],
    filament_volume_map=['0'], default_filament_profile=['Generic PETG @BBL A1'],
    inherits_group=['','Generic PETG @BBL A1','Bambu Lab A1 0.4 nozzle'],
    sparse_infill_density='8%', sparse_infill_pattern='gyroid',
    wall_loops='4', top_shell_layers='5', bottom_shell_layers='5',
    layer_height='0.2', initial_layer_print_height='0.2',
    curr_bed_type='Textured PEI Plate', enable_prime_tower='0',
    enable_support='1', support_type='normal(auto)', support_style='snug', support_threshold_angle='30',
    support_on_build_plate_only='0', brim_type='auto_brim', brim_width='5',
    support_top_z_distance='0.2', support_bottom_z_distance='0.2',
)
files = {'[Content_Types].xml':original['[Content_Types].xml'],
         '_rels/.rels':original['_rels/.rels'],
         'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()}
root = model(); del root.attrib['xmlns:p']
for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),
            ('Title',TITLE),('Designer','DeepDiverDude; personal size adaptation'),
            ('License','Standard Digital File License'),
            ('Description','For 228.6 x 69.85 mm sandpaper. Original model 2370141 by DeepDiverDude. Uniform mechanism enlargement plus two side extensions. Physical PETG fit not yet verified.')]:
    ET.SubElement(root,tag('metadata'),name=k).text=v
resources=ET.SubElement(root,tag('resources'))
build=ET.SubElement(root,tag('build'),attrib={'{'+P+'}UUID':uid()})
config=ET.Element('config')
rels=ET.Element('Relationships',xmlns=R)
plate=ET.SubElement(config,'plate')
for k,v in [('plater_id',1),('plater_name','Quarter sheet - all five parts'),
            ('locked','false'),('filament_maps','1'),('filament_volume_maps','0')]:
    meta(plate,k,v)
# Preserve the original print rotations; reposition on the A1 bed.
centers = {2:(70,75), 4:(70,164), 10:(169,164), 6:(147,65), 8:(201,65)}
records=[]; assembly={}; original_assembly={}
for obj in cfg.findall('object'):
    oid=int(obj.get('id')); part=obj.find('part'); pid=int(part.get('id'))
    props={e.get('key'):e.get('value') for e in part.findall('metadata')}
    source_name=props['name']; name=source_name.removesuffix('.stl')
    tm=trimesh.load_mesh(WORK/source_name)
    m=solid(tm).scale((SCALE,)*3)
    base_scaled=m
    if name in ('Base','Tighteneer','Lock'):
        m=widen(m)
        assert m.status()==mf.Error.NoError
        central=mf.Manifold.cube((1000,2*CUT,1000),True)
        assert ((m^central)-(base_scaled^central)).volume()<1e-5
        assert ((base_scaled^central)-(m^central)).volume()<1e-5
    # Plane splits can create sub-micron slivers which collapse when Bambu saves
    # float32 vertices. Remove those numerical edges before the native roundtrip.
    m=m.simplify(.001)
    changed=from_solid(m)
    assert changed.is_volume
    changed.export(OUT/(name+'.stl'))
    # Original source offsets reconstruct the designed assembly.
    offset=np.array([float(props['source_offset_'+a]) for a in 'xyz'])
    assembly[name]=m.translate(offset*SCALE)
    original_assembly[name]=base_scaled.translate(offset*SCALE)
    rot=poses[oid][:3,:3]
    v=changed.vertices@rot.T
    t=np.eye(4);t[:3,:3]=rot
    t[:2,3]=np.array(centers[oid])-(v.min(0)[:2]+v.max(0)[:2])/2
    t[2,3]=-v[:,2].min()
    path=f'3D/Objects/{name}.model'
    child=model(); cr=ET.SubElement(child,tag('resources'));mesh_xml(cr,pid,changed)
    files[path]=xml(child)
    top=ET.SubElement(resources,tag('object'),id=str(oid),type='model',attrib={'{'+P+'}UUID':uid()})
    comps=ET.SubElement(top,tag('components'))
    ET.SubElement(comps,tag('component'),objectid=str(pid),transform=IDENTITY,
                  attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
    ET.SubElement(rels,'Relationship',Target='/'+path,Id=f'rel-{oid}',
                  Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    co=ET.SubElement(config,'object',id=str(oid))
    meta(co,'name',name+' - quarter sheet');meta(co,'extruder','1')
    pc=ET.SubElement(co,'part',id=str(pid),subtype='normal_part')
    meta(pc,'name',name);meta(pc,'extruder','1')
    ET.SubElement(pc,'mesh_stat',face_count=str(len(changed.faces)),edges_fixed='0',
                  degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
    ET.SubElement(build,tag('item'),objectid=str(oid),printable='1',
                  transform=' '.join(format(float(x),'.12g') for x in t[:3].T.reshape(-1)),
                  attrib={'{'+P+'}UUID':uid()})
    ins=ET.SubElement(plate,'model_instance')
    for k,val in [('object_id',oid),('instance_id',0),('identify_id',oid)]:meta(ins,k,val)
    placed=changed.copy();placed.apply_transform(t)
    rec=dict(name=name,object_id=oid,size_mm=changed.extents.tolist(),
             bounds_on_bed_mm=placed.bounds.tolist(),watertight=bool(changed.is_volume),
             components=len(m.decompose()),volume_mm3=changed.volume,
             preserved_center_width_mm=2*CUT if name in ('Base','Lock','Tighteneer') else None)
    records.append(rec)
    print(name,rec,flush=True)
    placed.export(WORK/(name+'-placed.stl'))

# All source mating surfaces are unchanged by the width extensions.
intersections=[]
names=list(assembly)
for i,a in enumerate(names):
    for b in names[i+1:]:
        before=(original_assembly[a]^original_assembly[b]).volume()
        after=(assembly[a]^assembly[b]).volume()
        intersections.append(dict(parts=[a,b],source_scaled_mm3=before,adapted_mm3=after))
        print('Intersection',a,b,before,after,flush=True)
        assert after <= before+1e-3, (a,b,before,after)
for r in records:
    lo,hi=np.array(r['bounds_on_bed_mm'])
    assert min(lo[:2])>8 and max(hi[:2])<248 and abs(lo[2])<1e-6
for i,a in enumerate(records):
    for b in records[i+1:]:
        alo,ahi=np.array(a['bounds_on_bed_mm'])[:,:2]
        blo,bhi=np.array(b['bounds_on_bed_mm'])[:,:2]
        assert np.any(ahi+6 < blo) or np.any(bhi+6 < alo), (a['name'],b['name'])

files.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(rels),
              'Metadata/model_settings.config':xml(config)})
editable=OUT/'Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'
with zipfile.ZipFile(editable,'w',zipfile.ZIP_DEFLATED) as z:
    for n,data in files.items():z.writestr(n,data)
report=dict(source=str(SRC),source_sha256=sha(SRC),
            source_model_url='https://makerworld.com/en/models/2370141-compact-sanding-block-international-standards',
            source_profile='23mm - Single Color',paper_mm=[228.6,69.85],
            uniform_scale=SCALE,side_extension_per_side_mm=EXTRA,
            mesh_cleanup_tolerance_mm=.001,
            parts=records,assembly_intersections=intersections,
            editable_project_sha256=sha(editable),native_slice_validated=False,
            physical_fit_verified=False,protected_before=protected_before,
            protected_after={str(p):sha(p) for p in protected})
assert report['protected_before']==report['protected_after']
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print(editable,flush=True)
