"""Remove Knot model brims; verify blue first-layer extrusion stays in the IDs."""
import argparse
import collections
import json
import re
import shutil
import xml.etree.ElementTree as ET
import set_knot_white_support_base as shared
from shapely import union_all
from shapely.geometry import LineString, shape
import manifold3d as mf
from development_3mf import solid
from develop_cosmetic_joints import cross_section
from set_knot_white_support_base import (
    ROOT, read, write, digest, props, ASSET, dump, sha, protected, LOCKS,
    rows, compare, extrusion_paths, signatures, support_summary, SUPPORT, OTHER,
    scan_gcode, np, MultiPoint, check_startup_tower, check_tower,
)

WORK=ROOT/'.work/knot-no-brim-r1'
REPORT=ROOT/'release/knot-no-brim-r1'
BASE,EDIT,FINAL=[WORK/n for n in ('before.3mf','editable.3mf','final.3mf')]
SOURCE_SHA='d7fba1c2820d34181bf1a9f5828c8b499b3969ab59fee15016c830cadd4d3c74'
CHANGE={'brim_type':['outer_only','no_brim']}
GCODE_CHANGE=CHANGE


def bind():
    shared.WORK,shared.EDIT,shared.FINAL,shared.BASE,shared.CHANGE=WORK,EDIT,FINAL,BASE,CHANGE


def assess_contact():
    _,objects=rows(BASE);result=[]
    for obj in objects:
        body=mf.Manifold.batch_boolean([solid(p['mesh']) for p in obj['parts'] if p['subtype']=='normal_part'],mf.OpType.Add)
        contact=cross_section(body,.1)
        islands=list(contact.geoms) if hasattr(contact,'geoms') else [contact]
        result.append(dict(plate=obj['plate'],body_contact_area_mm2=contact.area,
            body_contact_components=len(islands),component_areas_mm2=sorted(p.area for p in islands),
            bounds_mm=list(contact.bounds),height_mm=13.5))
    assert min(r['body_contact_area_mm2'] for r in result)>36000
    assert min(a for r in result for a in r['component_areas_mm2'])>18000
    return result


def build():
    assert digest(ROOT/'Knot.3mf')==SOURCE_SHA
    WORK.mkdir(parents=True,exist_ok=True)
    if not BASE.exists():shutil.copyfile(ROOT/'Knot.3mf',BASE)
    assert digest(BASE)==SOURCE_SHA
    files=read(BASE);old=json.loads(files['Metadata/project_settings.config'])
    assert old['brim_type']=='outer_only' and old['support_filament']=='1'
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    assert not any(m.get('key')=='brim_type' for m in cfg.iter('metadata'))
    files['Metadata/project_settings.config'],count=re.subn(
        rb'("brim_type"\s*:\s*)"outer_only"',
        rb'\g<1>"no_brim"',files['Metadata/project_settings.config'])
    assert count==1
    assert json.loads(files['Metadata/project_settings.config'])=={**old,'brim_type':'no_brim'}
    for name in list(files):
        if ASSET.fullmatch(name) or name in ('Metadata/slice_info.config','Metadata/filament_sequence.json'):del files[name]
    files['Metadata/model_settings.config']=re.sub(rb'\s*<metadata key="(?:gcode|thumbnail|thumbnail_no_light|top|pick)_file" value="[^"]*"\s*/>',b'',files['Metadata/model_settings.config'])
    for name in list(files):
        if name.endswith('.rels'):
            def keep(match):
                rel=ET.fromstring(match[0])
                return match[0] if rel.get('TargetMode')=='External' or rel.get('Target').lstrip('/') in files else b''
            files[name]=re.sub(rb'<Relationship\s[^>]+/>',keep,files[name])
    write(EDIT,files,BASE)
    dump(REPORT/'provenance.json',dict(source_project='Knot.3mf',source_project_sha256=SOURCE_SHA,
        editable_sha256=digest(EDIT),changed_setting=CHANGE,protected_before=protected(),
        source_catalog_entry=json.loads((ROOT/'release/root-projects/catalog.json').read_text())['Knot'],
        authorization='User asks whether model brims are needed; remove if unnecessary, commit and push, and investigate the blue first-layer outline.',
        brim_reference='https://help.prusa3d.com/article/skirt-and-brim_133969',
        bed_contact=assess_contact(),
        intent='Remove narrow 1 mm model brims from broad, low PLA bodies. Retain all support and purge-tower settings; physical brimless adhesion remains unqualified.'))
    print('Built editable project: brim_type outer_only -> no_brim only.',flush=True)


def native(reopen=False):
    bind();shared.native(reopen)


def validate():
    bind();shared.parser_check();proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(BASE)==SOURCE_SHA and digest(EDIT)==proof['editable_sha256'] and protected()==proof['protected_before']
    native_check=shared.assemble();files=read(FINAL);old=read(BASE);settings,objects=rows(FINAL)
    for k,v in {**LOCKS,'support_type':'normal(auto)','support_filament':'1','support_interface_filament':'0','nozzle_diameter':['0.4'],
                'brim_width':'1','brim_object_gap':'0.1','brim_type':'no_brim','first_layer_print_sequence':['1','3','2'],'other_layers_print_sequence':['0'],'prime_tower_brim_width':'2'}.items():assert settings[k]==v,(k,settings[k])
    labels=json.loads((ROOT/'release/knot-first-layer-labels-r1/validation.json').read_text())['labels']
    result=json.loads((WORK/'native/result.json').read_text());info=ET.fromstring(files['Metadata/slice_info.config']);records=[]
    for obj in objects:
        n=obj['plate'];name=f'Metadata/plate_{n}.gcode';raw=files[name];text=raw.decode();oldtext=old[name].decode()
        assert raw!=old[name] and shared.hashlib.md5(raw).hexdigest()==files[name+'.md5'].decode().strip().lower()
        cfg=lambda txt:dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',txt,re.M))
        a,b=cfg(oldtext),cfg(text);delta={k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)}
        assert delta==GCODE_CHANGE,(n,delta)
        paths=extrusion_paths(text);before=extrusion_paths(oldtext)
        support=support_summary(paths)
        assert set(support['Support'])=={'1'} and all('3' not in tools for tools in support.values())
        brim=[p for p in paths if p[1]=='Brim'];oldbrim=[p for p in before if p[1]=='Brim']
        assert not brim and oldbrim and {p[0] for p in oldbrim}=={1},(n,'Brim still present')
        assert not any(p[1]=='Skirt' for p in paths+before)
        model=[p for p in paths if p[1] not in SUPPORT|OTHER];oldmodel=[p for p in before if p[1] not in SUPPORT|OTHER]
        model_equal=signatures(model)==signatures(oldmodel)
        assert model_equal,(n,'Model path geometry/materials/widths changed')
        support_equal=signatures([p for p in paths if p[1] in SUPPORT])==signatures([p for p in before if p[1] in SUPPORT])
        contacts={'Support interface','Support transition'}
        contact_equal=signatures([p for p in paths if p[1] in contacts])==signatures([p for p in before if p[1] in contacts])
        bed_equal=signatures([p for p in paths if p[1]=='Support' and p[4][2]==.2])==signatures([p for p in before if p[1]=='Support' and p[4][2]==.2])
        assert contact_equal and bed_equal,(n,'Support contact paths/materials changed')
        blue=[p for p in model if p[0]==3 and abs(p[4][2]-.2)<1e-6];assert blue
        label=next(l for l in labels if l['plate']==n);mask=shape(label['bed_outline'])
        # Centerlines must stay inside the exact glyphs. At curved glyph corners,
        # the nominal-width bead approximation can slightly exceed the polygon.
        centers=union_all([LineString([p[3][:2],p[4][:2]]) for p in blue])
        center_outside=centers.difference(mask).length
        assert center_outside<.000001,(n,'Blue centerline outside label',center_outside)
        blue_beads=union_all([LineString([p[3][:2],p[4][:2]]).buffer(p[2]/2,cap_style=2) for p in blue])
        outside=blue_beads.difference(mask.buffer(.05)).area
        assert outside<.001,(n,'Blue first-layer model extrusion outside ID',outside)
        first_blue=[p for p in paths if p[0]==3 and p[4][2]==.2]
        assert all(p[1]=='Prime tower' or p in blue for p in first_blue)
        outer=[p for p in model if p[1]=='Outer wall' and p[4][2]==.2 and not mask.buffer(1).intersects(LineString([p[3][:2],p[4][:2]]))]
        assert outer and {p[0] for p in outer}=={1}
        old_blue=[p for p in oldmodel if p[0]==3 and p[4][2]==.2]
        assert signatures(blue)==signatures(old_blue)
        first_tools=list(dict.fromkeys(p[0] for p in paths if abs(p[4][2]-.2)<1e-6 and p[1]!='Prime tower'))
        assert first_tools==[1,3],(n,first_tools)
        scan=scan_gcode(text);assert scan['model_extrusion_z_by_filament_mm']['3']==[.2,12.8,13,13.2,13.4,13.6]
        lo,hi=np.array(scan['bead_xy_bounds_mm']);clearance=float(min(*lo,*(np.array([330,320])-hi)));assert clearance>.5
        tr=obj['transform'];hulls=[MultiPoint((p['mesh'].vertices@tr[:3,:3].T+tr[:3,3])[:,:2]).convex_hull for p in obj['parts'] if p['subtype']=='normal_part']
        top=max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values())
        startup=check_startup_tower(settings,hulls,3,top,n);tower=check_tower(text,hulls,[0,0,330,320]);tower.pop('actual_tower_convex_envelope')
        pi=next(p for p in info.findall('plate') if props(p)['index']==str(n));warnings=[w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings)
        estimate=next(p for p in result['sliced_plates'] if p['id']==n)
        records.append(dict(plate=n,source_gcode_sha256=sha(old[name]),gcode_sha256=sha(raw),md5_verified=True,gcode_setting_changes=delta,
            source_brim_segments=len(oldbrim),brim_segments=0,no_model_brim_extrusion=True,
            no_skirt_extrusion=True,support_after=support,all_support_base_white=True,no_blue_support_extrusion=True,
            first_layer_blue_outside_label_area_mm2=outside,first_layer_blue_confined_to_label_and_purge_tower=True,
            first_layer_blue_centerline_outside_exact_glyphs_mm=center_outside,label_bead_corner_allowance_mm=.05,
            first_layer_nonlabel_outer_wall_slots=[1],first_layer_nonlabel_outer_wall_segments=len(outer),
            first_layer_blue_label_segments=len(blue),first_layer_filament_order=first_tools,
            model_path_geometry_materials_widths_identical=model_equal,support_path_geometry_materials_widths_identical=support_equal,
            interface_transition_geometry_materials_widths_identical=contact_equal,first_layer_support_geometry_materials_widths_identical=bed_equal,
            model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],bed_clearance_mm=clearance,startup_tower=startup,tower=tower,warnings=warnings,
            seconds=estimate['total_predication'],grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        dump(WORK/'validation-progress.json',records)
        print(f'Plate {n}: zero brim; {len(blue)} blue ID segments; all nonlabel outer walls white; blue outside ID {outside:.8f} mm2.',flush=True)
    native(True);reopened=compare(FINAL,WORK/'reopen/reopened.3mf');assert not reopened['settings_changes']
    assert protected()==proof['protected_before']
    dump(REPORT/'validation.json',dict(project='Knot.3mf',project_sha256=digest(FINAL),source_project_sha256=SOURCE_SHA,changed_setting=CHANGE,
        native_roundtrip=native_check,native_reopen=reopened,fresh_native_slices=True,native_reopen_verified=True,
        all_other_project_settings_preserved=True,geometry_poses_paint_object_volume_overrides_preserved=True,
        all_original_3d_archive_entries_byte_identical=True,all_cad_stl_unchanged=True,
        preserved_archive_entries_sha256={n:sha(v) for n,v in old.items() if files.get(n)==v},
        changed_archive_entries=sorted(n for n in set(old)|set(files) if old.get(n)!=files.get(n)),
        plates=records,total_seconds=sum(p['seconds'] for p in records),total_grams=sum(p['grams'] for p in records),
        evidence_sha256={'provenance.json':digest(REPORT/'provenance.json')},protected_after=protected(),
        printer_job_sent=False,physical_print_outcome_unqualified=True))
    shutil.copyfile(WORK/'native/result.json',REPORT/'native-result.json');shutil.copyfile(WORK/'reopen/result.json',REPORT/'native-reopen.json')


def publish():
    r=json.loads((REPORT/'validation.json').read_text());p=json.loads((REPORT/'provenance.json').read_text())
    assert digest(FINAL)==r['project_sha256'] and digest(ROOT/'Knot.3mf')==SOURCE_SHA and protected()==p['protected_before']
    catpath=ROOT/'release/root-projects/catalog.json';cat=json.loads(catpath.read_text());assert cat['Knot']==p['source_catalog_entry']
    cat['Knot'].update(sha256=r['project_sha256'],no_brim_validation='release/knot-no-brim-r1/validation.json')
    hp=ROOT/'release/root-projects/gcode-sha256.json';hashes=json.loads(hp.read_text());hashes['Knot']={f"plate_{v['plate']}":v['gcode_sha256'] for v in r['plates']}
    staged=WORK/'publish.3mf';shutil.copyfile(FINAL,staged);staged.replace(ROOT/'Knot.3mf')
    dump(catpath,cat);dump(hp,hashes);shutil.copyfile(REPORT/'native-result.json',ROOT/'release/root-projects/Knot-native.json')
    assert protected()==p['protected_before']


def preview():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig,axes=plt.subplots(2,5,figsize=(17,9),facecolor='#222831')
    for n,ax in enumerate(axes.ravel(),1):
        paths=extrusion_paths((WORK/f'native/plate_{n}.gcode').read_text())
        first=[p for p in paths if abs(p[4][2]-.2)<1e-6]
        assert not any(p[1]=='Brim' for p in first)
        groups=[('#b0b5bc',.4,[p for p in first if p[1] not in SUPPORT|OTHER and p[0]!=3]),
                ('#737d89',.6,[p for p in first if p[1] in SUPPORT]),
                ('#68acff',1.1,[p for p in first if p[1] not in SUPPORT|OTHER and p[0]==3])]
        for color,width,pool in groups:
            ax.add_collection(LineCollection([[p[3][:2],p[4][:2]] for p in pool],colors=color,linewidths=width))
        ax.set(xlim=(-8,338),ylim=(-8,328),aspect='equal',facecolor='#222831')
        ax.set_title(f'Plate {n} / F{n}',color='white',fontsize=11);ax.axis('off')
    fig.suptitle('Actual first-layer extrusion: no model brims, blue IDs only',color='white',fontsize=17)
    fig.text(.5,.065,'White model  |  Gray: white supports  |  Blue: permanent ID  |  No blue perimeter extrusion',ha='center',color='white',fontsize=11)
    fig.text(.5,.035,'View from above. IDs read normally underneath. Purge towers omitted; their settings are unchanged.',ha='center',color='#bbc3cc',fontsize=10)
    fig.subplots_adjust(left=.015,right=.985,bottom=.13,top=.88,hspace=.30,wspace=.10)
    fig.savefig(REPORT/'first-layer-no-brim.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)


def document():
    r=json.loads((REPORT/'validation.json').read_text());p=json.loads((REPORT/'provenance.json').read_text())
    assert digest(ROOT/'Knot.3mf')==r['project_sha256']
    def duration(s):
        m=round(s/60);return f'{m//60}h {m%60:02d}m'
    table='\n'.join(f"| {v['plate']} / F{v['plate']} | {p['bed_contact'][v['plate']-1]['body_contact_area_mm2']/100:.1f} | {v['brim_segments']} | {v['first_layer_blue_label_segments']} | {duration(v['seconds'])} | {v['grams']:.2f} g |" for v in r['plates'])
    text=f'''# Knot model brims removed — October 26, 2026

Current production file: root **Knot.3mf**, A2L, ten plates.

The user reported difficult brim cleanup, requested removal if unnecessary,
commit/push, and pointed out a blue outline in a first-layer preview. They
confirmed that preview came from the repository's Knot.3mf.

## Decision and exact change

The bodies are only **13.5 mm tall** and each has **36952–49592 mm2** of bed
contact. The smallest separate contact island is **18406 mm2**. These are broad,
low PLA bodies on the saved **65 C Textured PEI** plate, rather than tall parts
depending on small feet. Removing their narrow 1 mm adhesion brims is a reasonable
tradeoff for easier cleanup. This is a geometry-based assessment, not physical
proof against corner lifting. Brimless adhesion remains unqualified.

[Prusa's brim guidance](https://help.prusa3d.com/article/skirt-and-brim_133969)
explains that brims increase contact area, particularly for tall objects with a
small base and groups of small objects, and suggests at least 3 mm for useful
additional adhesion. The measured contact areas here are from the actual saved
production meshes at Z0.1, not estimates from a screenshot.

Only **brim_type: outer_only → no_brim** changes. Dormant brim width/gap remain
1/0.1 mm. All supports, their paint and spacing, white base material, interface
Auto, white-first filament order, **2 mm purge-tower brim**, geometry, material
regions, blue IDs and upper blue trim, CAD/STLs and every other saved setting
remain unchanged. No new adhesion devices or geometry are added.

## Native validation

All ten plates have fresh native slices and final native reopening.

![Actual first-layer extrusion with no model brims](first-layer-no-brim.png)

- **Zero Brim extrusion** and zero Skirt extrusion on every plate.
- Every first-layer blue model centerline is inside the exact ID glyphs, with
  zero centerline length outside. Nominal bead footprints remain within 0.05 mm
  of the glyphs, allowing the slicer's rounded-corner/width approximation.
  There are **no blue first-layer part-outline extrusion commands**.
- All first-layer outer-wall segments away from the label use white slot 1.
  Blue on the separate purge tower remains necessary and is excluded from the
  illustration. Labels retain their exact source paths and backing.
- All model path geometry, filament assignments, feature types and widths match
  the preceding release exactly, including all upper-layer artwork and joints.
- Support base/body remains white. No blue appears in support, interface or
  transition extrusion. Contact paths and first-layer support paths are identical;
  complete support equality is separately recorded per plate.
- Original 3D archive entries, stock, poses, object/volume settings and paint
  remain intact. All adjacent CAD/STL and other production projects are unchanged.
- G-code configuration changes only in brim_type; checksums, bed/tower clearance,
  native warnings and reopening pass. Only the existing timelapse notices remain.

| Plate / part | Bed contact cm2 | Brim segments | Blue ID segments | Time | Material |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}
| **Total** | | **0** | | **{duration(r['total_seconds'])}** | **{r['total_grams']:.2f} g** |

## Blue preview outline

The previous saved file also had no blue first-layer outline extrusion: its model
paths are identical to this revision, and its brims were white. The visible edge
in the screenshot is therefore not represented by a blue extrusion around the
part in the checked saved command stream.

The local Bambu preference **Always show shells in preview** is enabled
(`show_shells_in_preview = true`). Bambu's
[preview renderer](https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/GCodeRenderer/BaseRenderer.cpp)
can overlay transparent model geometry separately from G-code extrusion. This is
a plausible explanation for the screenshot, not a visually confirmed diagnosis.
The computer-use helper failed to launch Bambu with
`accessibility window-opened handler did not become ready`; native command-line
slicing/reopening worked. No local preference was changed. To inspect extrusion
alone, turn off **Always show shells in preview** in Preferences and reslice;
the [preference definition](https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/Preferences.cpp)
specifies that reslicing is needed after changing it.

`preview-investigation.json` records this distinction. Digital checks do not
establish physical adhesion, support cleanup, label finish or full-size fit.
No printer job was sent.

Project SHA-256: `{r['project_sha256']}`.

Source SHA-256: `{SOURCE_SHA}`.

See `provenance.json`, `validation.json`, `native-result.json` and
`native-reopen.json` for source identity, preservation and per-plate checks.
Earlier release records retain their historical hashes.
Run `python scripts/audit_root_projects.py` after pulling.
'''
    (REPORT/'README.md').write_text(text,encoding='utf-8',newline='\n')
    path=ROOT/'release/root-projects/README.md';text=path.read_text(encoding='utf-8')
    text=re.sub(r'^\| Knot \|[^\n]+',f"| Knot | 10 | {duration(r['total_seconds'])} | {r['total_grams']:.2f} g |",text,flags=re.M)
    path.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','slice','validate','publish','preview','document'])
    action=parser.parse_args().action;(native if action=='slice' else globals()[action])()
