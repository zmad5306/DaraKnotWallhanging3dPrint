"""Add flush, underside-readable metallic-blue plate/part IDs to current Knot.

Only ten new color modifiers are added. All source stock, modifiers, settings,
paint and poses remain exact; fresh native slices supply the printing result.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'.work/python-libs')]
import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import Polygon, box, mapping, shape, MultiPoint
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties, findfont
import manifold3d as mf
from development_3mf import solid, mesh, mesh_xml, model, tag, xml, meta, uid, P, R, IDENTITY
from develop_cosmetic_joints import cross_section
from build_a2l_project import prism
from organize_root_projects import rows, compare, BOOKKEEPING, grid, pitch, clean_relations
from remove_unused_project_filaments import read, write, digest, props, ASSET
import promote_knot_solid_laps as laps
from audit_knot_rollback_joints import paths_with_width
from validate_print_project import scan_gcode
from check_a2l_towers import check_startup_tower, check_tower

WORK = ROOT/'.work/knot-first-layer-labels-r1'
REPORT = ROOT/'release/knot-first-layer-labels-r1'
BASE, EDIT, FINAL = [WORK/n for n in ('before.3mf', 'editable.3mf', 'final.3mf')]
SOURCE_SHA = '78f22d0ff7e22da7e27a3fd4c761c1aa815a5bb26c3acea3392cbd23797c52e6'
PREFIX = 'Blue first-layer ID - '
FONT = Path(findfont(FontProperties(family='DejaVu Sans', weight='bold')))


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8', newline='\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def effective(settings):
    return {k:v for k,v in settings.items() if k not in BOOKKEEPING}


def protected():
    paths = [p for p in ROOT.glob('*.3mf') if p.name != 'Knot.3mf']
    paths += [p for p in ROOT.glob('*.scad') if p.name != 'Knot.scad']
    paths += [p for p in ROOT.glob('* STL/*.stl') if p.parent.name != 'Knot STL']
    paths += list((ROOT/'release/samples').glob('*.3mf'))
    return {p.relative_to(ROOT).as_posix():digest(p) for p in paths}


def lettering(text):
    result = Polygon()
    for contour in TextPath((0,0), text, size=100, prop=FontProperties(fname=str(FONT))).to_polygons():
        result = result.symmetric_difference(Polygon(contour))
    a,b,c,d = result.bounds
    result = affinity.translate(result, -(a+c)/2, -(b+d)/2)
    # Reflection in bed X makes the word read normally when viewed from below.
    return affinity.scale(result, xfact=-8/(d-b), yfact=8/(d-b), origin=(0,0)).simplify(.003, preserve_topology=True)


def transform_polygon(poly, t):
    return affinity.affine_transform(poly, [t[0,0],t[0,1],t[1,0],t[1,1],t[0,3],t[1,3]])


def placement(obj, letters):
    body = mf.Manifold.batch_boolean([solid(p['mesh']) for p in obj['parts'] if p['subtype']=='normal_part'], mf.OpType.Add)
    contact = cross_section(body,.1).intersection(cross_section(body,.19))
    guards = shapely.union_all([cross_section(solid(p['mesh']),.1) for p in obj['parts']
        if p['settings'].get('name')=='Local solid screw reinforcement' or p['settings'].get('name','').startswith(laps.PREFIX)])
    safe = transform_polygon(contact.difference(guards.buffer(3)),obj['transform'])
    w = letters.bounds[2]-letters.bounds[0]
    x0,y0,x1,y1 = safe.bounds
    xx,yy = np.meshgrid(np.arange(x0+w/2+3,x1-w/2-3,2), np.arange(y0+7,y1-7,2))
    x,y = xx.ravel(),yy.ravel()
    boxes = shapely.box(x-w/2,y-4,x+w/2,y+4)
    ok = shapely.contains(safe.buffer(-3), boxes)
    assert ok.any(), (obj['plate'],'No safe 8 mm label location')
    candidates = np.flatnonzero(ok)
    distances = shapely.distance(boxes[candidates],safe.boundary)
    i = candidates[np.argmax(distances)]
    bed = affinity.translate(letters,float(x[i]),float(y[i]))
    assembly = transform_polygon(bed,np.linalg.inv(obj['transform']))
    assert contact.contains(assembly.buffer(2.9))
    assert assembly.distance(guards)>3
    return assembly, dict(center_bed_xy_mm=[float(x[i]),float(y[i])],
        width_mm=w,height_mm=8.0,bed_outline=mapping(bed),assembly_outline=mapping(assembly),
        minimum_body_edge_clearance_mm=assembly.distance(contact.boundary),
        minimum_joint_screw_modifier_clearance_mm=assembly.distance(guards))


def compare_original(path):
    a,aa = rows(BASE); b,bb = rows(path)
    assert a==b and len(aa)==len(bb)==10
    result=[]
    for old,new in zip(aa,bb):
        assert old['settings']==new['settings'] and old['name']==new['name']
        assert np.max(abs(old['transform']-new['transform']))<.0001
        assert len(new['parts'])==len(old['parts'])+1
        errors=[]
        for p,q in zip(old['parts'],new['parts']):
            assert p['subtype']==q['subtype'] and p['paint']==q['paint']
            assert effective(p['settings'])==effective(q['settings'])
            assert p['settings'].get('name')==q['settings'].get('name')
            assert np.array_equal(p['mesh'].faces,q['mesh'].faces)
            error=float(np.max(abs(p['mesh'].vertices-q['mesh'].vertices)))
            assert error<.0001
            errors.append(error)
        label=new['parts'][-1]
        assert label['subtype']=='modifier_part' and effective(label['settings'])=={'extruder':'3'}
        assert label['settings']['name']==PREFIX+f"P{new['plate']} F{new['plate']}"
        assert np.allclose(label['mesh'].bounds[:,2],[0,.2],atol=.000001)
        result.append(dict(plate=new['plate'],original_volumes=len(old['parts']),
            original_meshes_paint_settings_poses_preserved=True,max_mesh_error_mm=max(errors)))
    return result


def build():
    assert digest(ROOT/'Knot.3mf')==SOURCE_SHA
    WORK.mkdir(parents=True,exist_ok=True); REPORT.mkdir(parents=True,exist_ok=True)
    if not BASE.exists(): shutil.copyfile(ROOT/'Knot.3mf',BASE)
    assert digest(BASE)==SOURCE_SHA
    settings,objects=rows(BASE); original=read(BASE); files=dict(original)
    cfg=ET.fromstring(files['Metadata/model_settings.config']); root=ET.fromstring(files['3D/3dmodel.model'])
    rels=ET.fromstring(files['3D/_rels/3dmodel.model.rels']); records=[]
    for obj in objects:
        n=obj['plate']; label=f'P{n} F{n}'
        outline,record=placement(obj,lettering(label)); m=mesh(prism(outline,0,.2))
        pid=11000+n; path=f'3D/Objects/first_layer_id_f{n}.model'
        child=model(); mesh_xml(ET.SubElement(child,tag('resources')),pid,m); files[path]=xml(child)
        top=root.find(tag('resources')).find(f"{tag('object')}[@id='{obj['id']}']")
        ET.SubElement(top.find(tag('components')),tag('component'),objectid=str(pid),transform=IDENTITY,
            attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
        part=ET.SubElement(cfg.find(f"object[@id='{obj['id']}']"),'part',id=str(pid),subtype='modifier_part')
        meta(part,'name',PREFIX+label); meta(part,'extruder','3')
        ET.SubElement(part,'mesh_stat',face_count=str(len(m.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        ET.SubElement(rels,'{'+R+'}Relationship',Target='/'+path,Id=f'rel-first-layer-id-{n}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        records.append(dict(plate=n,part=f'F{n}',text=label,z_mm=[0,.2],extruder=3,**record))
        print(f'{label}: 8 mm height, {record["width_mm"]:.1f} mm width; {record["minimum_body_edge_clearance_mm"]:.1f} mm edge clearance.',flush=True)
    for name in list(files):
        if ASSET.fullmatch(name) or name in ('Metadata/slice_info.config','Metadata/filament_sequence.json'):del files[name]
    for p in cfg.findall('plate'):
        for md in list(p.findall('metadata')):
            if md.get('key') in ('gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file'):p.remove(md)
    files['3D/3dmodel.model']=xml(root); files['Metadata/model_settings.config']=xml(cfg)
    files['3D/_rels/3dmodel.model.rels']=xml(rels); clean_relations(files)
    assert all(files[n]==v for n,v in original.items() if n.startswith('3D/Objects/'))
    assert files['Metadata/project_settings.config']==original['Metadata/project_settings.config']
    write(EDIT,files,BASE)
    dump(REPORT/'provenance.json',dict(source_project_sha256=SOURCE_SHA,editable_sha256=digest(EDIT),
        source_catalog_entry=json.loads((ROOT/'release/root-projects/catalog.json').read_text())['Knot'],
        original_cad_sha256=digest(ROOT/'Knot.scad'),protected_before=protected(),
        original_knot_stl_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in (ROOT/'Knot STL').glob('*.stl')},
        font_name='DejaVu Sans Bold',font_sha256=digest(FONT),font_polygon_tolerance_mm=.003,
        user_authorization='All ten Knot pieces; first-layer metallic blue plate and part IDs; push to main.',labels=records))
    dump(REPORT/'editable-preservation.json',compare_original(EDIT))


def configure_native():
    laps.WORK,laps.REPORT,laps.BASE,laps.EDIT,laps.FINAL=WORK,REPORT,BASE,EDIT,FINAL
    laps.compare_original=compare_original


def native():
    configure_native(); laps.native()


def assemble():
    configure_native(); return laps.assemble_final()


def validate():
    proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(BASE)==SOURCE_SHA and digest(EDIT)==proof['editable_sha256']
    assert protected()==proof['protected_before']
    original_check,native_check=assemble()
    files=read(FINAL); old=read(BASE); settings,objects=rows(FINAL)
    info=ET.fromstring(files['Metadata/slice_info.config']); result=json.loads((WORK/'native/result.json').read_text())
    locks={**laps.LOCKS,'support_type':'normal(auto)','nozzle_diameter':['0.4']}
    for key,value in locks.items():assert settings[key]==value
    records=[]; keypaths={}
    for obj,label in zip(objects,proof['labels']):
        n=obj['plate']; name=f'Metadata/plate_{n}.gcode'; raw=files[name]; text=raw.decode()
        assert raw!=old[name] and hashlib.md5(raw).hexdigest()==files[name+'.md5'].decode().strip().lower()
        config=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.M))
        oldconfig=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',old[name].decode(),re.M))
        assert config==oldconfig,(n,{k:[oldconfig.get(k),v] for k,v in config.items() if oldconfig.get(k)!=v})
        paths=paths_with_width(text,obj['transform']); oldpaths=paths_with_width(old[name].decode(),obj['transform'])
        before=laps.angles(oldpaths); after=laps.angles(paths)
        assert before.keys()==after.keys() and all(abs((v-after[k]+90)%180-90)<=.5 for k,v in before.items())
        first=[p for p in paths if abs(p[2][1,2]-.2)<.0001]; blue=[p for p in first if p[0]==3]
        assert blue
        outline=shape(label['assembly_outline'])
        bands=shapely.union_all([shapely.LineString(p[2][:,:2]).buffer(p[3]/2,quad_segs=8) for p in blue])
        coverage=bands.intersection(outline).area/outline.area
        assert coverage>.96,(n,coverage)
        glyphs=[]
        for glyph in outline.geoms:
            covered=bands.intersection(glyph).area/glyph.area
            assert covered>.94,(n,covered)
            assert not glyph.buffer(-.5).is_empty,'Label stroke too thin'
            glyphs.append(covered)
        assert len(glyphs)==len(label['text'].replace(' ',''))
        spill=bands.difference(outline.buffer(.12)).area
        assert spill<.1,(n,spill)
        white=shapely.union_all([shapely.LineString(p[2][:,:2]).buffer(p[3]/2,quad_segs=8) for p in first if p[0]==1])
        interior=outline.buffer(-.2)
        overlap=white.intersection(interior).area
        assert overlap<.1,(n,overlap)
        # The next solid white layer must back every letter.
        backing=shapely.union_all([shapely.LineString(p[2][:,:2]).buffer(p[3]/2,quad_segs=8) for p in paths if abs(p[2][1,2]-.4)<.0001 and p[0]==1])
        backing_fraction=backing.intersection(outline).area/outline.area
        assert backing_fraction>.98,(n,backing_fraction)
        scan=scan_gcode(text)
        assert scan['model_extrusion_z_by_filament_mm']['3']==[.2,12.8,13,13.2,13.4,13.6]
        lo,hi=np.array(scan['bead_xy_bounds_mm']);clearance=float(min(*lo,*(np.array([330,320])-hi)))
        assert clearance>.5 and scan['features'].get('Support',0)>0 and scan['features'].get('Support interface',0)>0
        tr=obj['transform']; hulls=[MultiPoint((p['mesh'].vertices@tr[:3,:3].T+tr[:3,3])[:,:2]).convex_hull for p in obj['parts'] if p['subtype']=='normal_part']
        top=max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values())
        startup=check_startup_tower(settings,hulls,3,top,n); tower=check_tower(text,hulls,[0,0,330,320]);tower.pop('actual_tower_convex_envelope')
        keypaths[n]=[p for p in paths if 5.19<=p[2][1,2]<=6.01]
        # Unchanged dense lap and upper-surface model paths are checked as
        # geometric segment sets, independently of travel order and purge moves.
        def signatures(ps):
            return sorted((p[0],p[1],round(p[3],4),tuple(sorted(tuple(np.round(q,4)) for q in p[2]))) for p in ps if p[2][1,2]>.201)
        upper_identical=signatures(paths)==signatures(oldpaths)
        assert upper_identical,(n,'Unexpected model path change above the first layer')
        pi=next(p for p in info.findall('plate') if props(p)['index']==str(n)); warnings=[w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
        est=next(p for p in result['sliced_plates'] if p['id']==n)
        records.append(dict(plate=n,text=label['text'],source_gcode_sha256=sha(old[name]),gcode_sha256=sha(raw),
            md5_verified=True,global_gcode_config_unchanged=True,label_coverage_fraction=coverage,
            glyph_coverage_fractions=glyphs,white_backing_coverage_fraction=backing_fraction,
            white_overlap_inside_blue_mm2=overlap,blue_spill_beyond_012mm_mm2=spill,
            model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],bed_clearance_mm=clearance,
            startup_tower=startup,tower=tower,warnings=warnings,top_surface_directions_preserved=True,
            upper_model_path_segments_identical=upper_identical,
            seconds=est['total_predication'],grams=sum(f['total_used_g'] for f in est['filaments'])))
        dump(WORK/'validation-progress.json',records)
        print(f'F{n}: label coverage {coverage:.2%}, white backing {backing_fraction:.2%}, upper paths identical={upper_identical}.',flush=True)
    laps.joints.WORK,laps.joints.REPORT=WORK,REPORT
    jointpaths=laps.joints.toolpaths(keypaths)
    configure_native(); laps.native(True)
    reopened=compare(FINAL,WORK/'reopen/reopened.3mf'); compare_original(WORK/'reopen/reopened.3mf')
    assert not reopened['settings_changes'] and protected()==proof['protected_before']
    assert all(files[n]==v for n,v in old.items() if n.startswith('3D/Objects/'))
    dump(REPORT/'validation.json',dict(project='Knot.3mf',project_sha256=digest(FINAL),source_project_sha256=SOURCE_SHA,
        original_meshes_settings_support_paint_and_poses_preserved=True,all_global_settings_preserved=True,
        original_object_checks=original_check,native_roundtrip=native_check,native_reopen=reopened,
        fresh_native_slices=True,native_reopen_verified=True,labels=proof['labels'],plates=records,
        minimum_commanded_key_clearance_mm=jointpaths['minimum_commanded_clearance_mm'],
        preserved_archive_entries_sha256={n:sha(v) for n,v in old.items() if files.get(n)==v},
        total_seconds=sum(r['seconds'] for r in records),total_grams=sum(r['grams'] for r in records),
        protected_after=protected(),printer_job_sent=False,physical_label_legibility_unqualified=True,
        evidence_sha256={n:digest(REPORT/n) for n in ('provenance.json','editable-preservation.json','joint-toolpaths.json')}))
    shutil.copyfile(WORK/'native/result.json',REPORT/'native-result.json')
    shutil.copyfile(WORK/'reopen/result.json',REPORT/'native-reopen.json')


def preview():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    proof=json.loads((REPORT/'provenance.json').read_text()); _,objects=rows(FINAL if FINAL.exists() else EDIT)
    files=read(FINAL) if FINAL.exists() else None
    fig,axes=plt.subplots(5,2,figsize=(13,13))
    for ax,obj,label in zip(axes.ravel(),objects,proof['labels']):
        outline=shape(label['bed_outline']); center=np.array(label['center_bed_xy_mm'])
        # Reflect the actual bed coordinates to show the finished underside.
        if files:
            ps=paths_with_width(files[f"Metadata/plate_{obj['plate']}.gcode"].decode(),np.eye(4))
            for slot,color in [(1,'#d4d6d8'),(3,'#215b9b')]:
                segments=[p[2][:,:2]*[-1,1] for p in ps if abs(p[2][1,2]-.2)<.0001 and p[0]==slot]
                ax.add_collection(LineCollection(segments,colors=color,linewidths=1.6))
        else:
            for poly in outline.geoms:
                ax.fill(-np.array(poly.exterior.xy[0]),poly.exterior.xy[1],color='#215b9b')
                for hole in poly.interiors:ax.fill(-np.array(hole.xy[0]),hole.xy[1],color='white')
        ax.set(xlim=(-center[0]-30,-center[0]+30),ylim=(center[1]-9,center[1]+9),aspect='equal',title=f"Plate {obj['plate']} / part F{obj['plate']} — underside")
        ax.axis('off')
    fig.suptitle('Knot: metallic-blue first-layer identifiers\n'+('Actual native first-layer extrusion centerlines' if files else 'Color modifier outlines'),fontsize=16)
    fig.tight_layout(rect=[0,0,1,.95]); fig.savefig(REPORT/'underside-labels.png',dpi=180);plt.close(fig)


def publish():
    proof=json.loads((REPORT/'provenance.json').read_text()); report=json.loads((REPORT/'validation.json').read_text())
    assert digest(FINAL)==report['project_sha256'] and digest(ROOT/'Knot.3mf')==SOURCE_SHA
    assert protected()==proof['protected_before']
    catpath=ROOT/'release/root-projects/catalog.json'; catalog=json.loads(catpath.read_text()); entry=catalog['Knot']
    assert entry==proof['source_catalog_entry']
    settings,objects=rows(FINAL); cad=ROOT/'Knot.scad'; assert digest(cad)==proof['original_cad_sha256']
    lines=[cad.read_text().rstrip(),'','// Flush blue underside identifiers, only Z0..0.20 mm.']
    newstls={}
    for obj,saved in zip(objects,entry['objects']):
        part=obj['parts'][-1]; n=obj['plate']; rel=f'Knot STL/F{n}-first-layer-blue-id.stl'; path=ROOT/rel
        path.write_bytes(part['mesh'].export(file_type='stl')); newstls[rel]=digest(path)
        saved['parts'].append(dict(file=rel,sha256=digest(path),subtype=part['subtype'],settings=part['settings'],faces=len(part['mesh'].faces),bounds=part['mesh'].bounds.tolist()))
        offset=grid(n-1,10,pitch(settings))
        lines += [f'// Plate {n}: {part["settings"]["name"]}',f'if ((plate == 0 || plate == {n}) && show_modifiers)',
            f' translate(plate == 0 ? {json.dumps([float(offset[0]),float(offset[1]),0])} : [0,0,0])',
            f'  multmatrix({json.dumps(obj["transform"].tolist())})',f'   color("#215B9B") import("{rel}", convexity=20);','']
    cad.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8',newline='\n')
    entry.update(sha256=report['project_sha256'],cad_sha256=digest(cad),
        unique_stl=len({p['file'] for o in entry['objects'] for p in o['parts']}),labels_validation='release/knot-first-layer-labels-r1/validation.json')
    report.update(new_modifier_stls=newstls,cad_sha256=digest(cad),
        original_knot_stls_unchanged=all(digest(ROOT/n)==h for n,h in proof['original_knot_stl_hashes'].items()))
    assert report['original_knot_stls_unchanged']; dump(REPORT/'validation.json',report)
    shutil.copyfile(FINAL,ROOT/'Knot.3mf'); dump(catpath,catalog)
    hp=ROOT/'release/root-projects/gcode-sha256.json'; hashes=json.loads(hp.read_text())
    hashes['Knot']={f"plate_{p['plate']}":p['gcode_sha256'] for p in report['plates']};dump(hp,hashes)
    shutil.copyfile(REPORT/'native-result.json',ROOT/'release/root-projects/Knot-native.json')
    assert protected()==proof['protected_before']


def document():
    r=json.loads((REPORT/'validation.json').read_text())
    assert digest(ROOT/'Knot.3mf')==r['project_sha256']
    def duration(s):
        m=round(s/60)
        return f'{m//60}h {m%60:02d}m'
    table='\n'.join(f"| {p['text']} | {duration(p['seconds'])} | {p['grams']:.2f} g |" for p in r['plates'])
    text=f'''# Knot permanent underside identifiers — October 25, 2026

Current project: **root `Knot.3mf`**, Bambu Lab A2L, ten plates.

The user requested metallic-blue plate/part numbers in the first layer and
confirmed all ten Knot pieces. Each has **P1 F1 through P10 F10** printed flush
in its existing underside, using the saved slot 3 SUNLU PLA Metallic Azurite
blue. P means plate; F is the existing part identifier. Text is **8 mm tall**,
32–47 mm wide, DejaVu Sans Bold, mirrored in bed X so it reads normally when
viewed from below. The color mask covers **Z0–0.20 mm only**. Every glyph has
an interior at least 1 mm wide and sits clear of body edges, joints, holes and
screw modifiers. Nothing protrudes from or is removed from the part.

![Actual native first-layer paths viewed from the underside](underside-labels.png)

## Preservation and validation

- Ten new color-only modifiers; all original embedded mesh entries remain
  byte-identical, including stock, keys, grooves, reliefs, color regions, the
  28 solid-lap masks and all 50 Z12.4 screw reinforcements.
- All project settings, original object/volume overrides, paint and poses
  are preserved. Structural 8% gyroid, local 100% rectilinear laps, four walls,
  five top/bottom layers, 0.4 mm nozzle, 0.20 mm layers, textured PEI, normal
  supports and infill-first off remain. The five blue show-face layers remain.
- All ten plates freshly sliced with native Bambu Studio and the final editable
  geometry/settings reopened natively. The delivered project retains all ten
  new G-codes; the CLI reopen export omits its toolpath cache.
- Every glyph is present in the native first-layer extrusion paths. Minimum
  label coverage is {min(p['label_coverage_fraction'] for p in r['plates']):.2%};
  minimum white second-layer backing is {min(p['white_backing_coverage_fraction'] for p in r['plates']):.2%}.
  Blue model extrusion occurs only at Z0.20 and the original five upper layers
  Z12.8/13.0/13.2/13.4/13.6. These percentages measure commanded bead coverage,
  not physically deposited material.
- Checked G-code settings/checksums, bed and tower clearance including supports
  and brims, unchanged top-surface directions, and 140 key/groove layer pairs.
  Minimum commanded key clearance: {r['minimum_commanded_key_clearance_mm']:.4f} mm.
  Native warnings are limited to the existing traditional-timelapse notice.
- Model extrusion segment geometry, filament assignments, feature types and
  widths above the first layer match the preceding solid-lap release on every
  plate, including the lap fill and screw skins. Travel and purge are excluded
  from this comparison; all saved settings remain unchanged.
- Adjacent label STLs, `Knot.scad`, catalog and slice hashes are synchronized.
  All pre-existing Knot STLs and other root projects/CAD/STLs remain unchanged.

These digital checks do not establish physical label legibility/durability,
full-size joint fit or surface quality. No printer job was sent.

## Native estimates

| Identifier | Time | Material |
| --- | ---: | ---: |
{table}
| **Total** | **{duration(r['total_seconds'])}** | **{r['total_grams']:.2f} g** |

Estimates include supports and purge structures. First-layer blue adds color
changes and purge material with the existing saved purge settings.

Production SHA-256: `{r['project_sha256']}`.

Source SHA-256: `{SOURCE_SHA}` (accepted solid-lap production revision).

`provenance.json`, `editable-preservation.json`, `validation.json`,
`joint-toolpaths.json`, `native-result.json` and `native-reopen.json` bind the
checks to these files. Prior solid-lap/sample reports remain historical evidence
for the source geometry. Run `python scripts/audit_root_projects.py` after pulling.
'''
    (REPORT/'README.md').write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','slice','validate','preview','publish','document'])
    action=parser.parse_args().action
    (native if action=='slice' else globals()[action])()
