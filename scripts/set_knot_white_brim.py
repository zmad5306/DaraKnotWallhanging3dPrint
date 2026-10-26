"""Make Knot's tear-away brim white with a native first-layer filament order."""
import argparse
import collections
import json
import re
import shutil
import xml.etree.ElementTree as ET
import set_knot_white_support_base as shared
from shapely import union_all
from shapely.geometry import LineString
from set_knot_white_support_base import (
    ROOT, read, write, digest, props, ASSET, dump, sha, protected, LOCKS,
    rows, compare, extrusion_paths, signatures, support_summary, SUPPORT, OTHER,
    scan_gcode, np, MultiPoint, check_startup_tower, check_tower,
)

WORK=ROOT/'.work/knot-white-brim-r1'
REPORT=ROOT/'release/knot-white-brim-r1'
BASE,EDIT,FINAL=[WORK/n for n in ('before.3mf','editable.3mf','final.3mf')]
SOURCE_SHA='9fe693f6b5b6ebfc363ecaada107172337c0fd962a80d956ed5fc8fd90dc5427'
CHANGE={'first_layer_print_sequence':[['0'],['1','3','2']]}
GCODE_CHANGE={'first_layer_print_sequence':['0','1,3,2']}


def bind():
    shared.WORK,shared.EDIT,shared.FINAL,shared.BASE,shared.CHANGE=WORK,EDIT,FINAL,BASE,CHANGE


def build():
    assert digest(ROOT/'Knot.3mf')==SOURCE_SHA
    WORK.mkdir(parents=True,exist_ok=True)
    if not BASE.exists():shutil.copyfile(ROOT/'Knot.3mf',BASE)
    assert digest(BASE)==SOURCE_SHA
    files=read(BASE);old=json.loads(files['Metadata/project_settings.config'])
    assert old['first_layer_print_sequence']==['0'] and old['support_filament']=='1'
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    assert not any(m.get('key')=='first_layer_print_sequence' for m in cfg.iter('metadata'))
    files['Metadata/project_settings.config'],count=re.subn(
        rb'("first_layer_print_sequence"\s*:\s*)\[\s*"0"\s*\]',
        rb'\g<1>["1", "3", "2"]',files['Metadata/project_settings.config'])
    assert count==1
    assert json.loads(files['Metadata/project_settings.config'])=={**old,'first_layer_print_sequence':['1','3','2']}
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
        authorization='User reported the tear-away perimeter still blue after approving white supports, blue labels, all ten fresh slices, commit and push to main.',
        source_reference='https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/GCode/ToolOrdering.cpp',
        intent='White first on layer one assigns the brim to white. Other-layer ordering remains Auto; no brim dimensions or geometry change.'))
    print('Built editable project: first-layer order Auto -> white, blue, wood.',flush=True)


def native(reopen=False):
    bind();shared.native(reopen)


def validate():
    bind();shared.parser_check();proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(BASE)==SOURCE_SHA and digest(EDIT)==proof['editable_sha256'] and protected()==proof['protected_before']
    native_check=shared.assemble();files=read(FINAL);old=read(BASE);settings,objects=rows(FINAL)
    for k,v in {**LOCKS,'support_type':'normal(auto)','support_filament':'1','support_interface_filament':'0','nozzle_diameter':['0.4'],
                'brim_width':'1','brim_object_gap':'0.1','brim_type':'outer_only','first_layer_print_sequence':['1','3','2'],'other_layers_print_sequence':['0']}.items():assert settings[k]==v,(k,settings[k])
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
        assert brim and {p[0] for p in brim}=={1} and {p[0] for p in oldbrim}=={3}
        brim_equal=signatures(brim,False)==signatures(oldbrim,False)
        assert {(p[2],p[4][2]) for p in brim}=={(p[2],p[4][2]) for p in oldbrim}
        # Native loop start positions may split the same closed brim differently.
        outline=union_all([LineString([p[3][:2],p[4][:2]]) for p in brim])
        oldoutline=union_all([LineString([p[3][:2],p[4][:2]]) for p in oldbrim])
        brim_distance=outline.hausdorff_distance(oldoutline)
        brim_length_delta=abs(outline.length-oldoutline.length)
        assert brim_distance<.001 and brim_length_delta<.01,(n,brim_distance,brim_length_delta)
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
            brim_before_slots=sorted({p[0] for p in oldbrim}),brim_after_slots=[1],brim_white_segments=len(brim),brim_geometry_widths_identical=brim_equal,
            brim_outline_preserved_within_gcode_rounding=True,brim_outline_hausdorff_mm=brim_distance,brim_outline_length_delta_mm=brim_length_delta,
            all_brim_white=True,no_skirt_extrusion=True,support_after=support,all_support_base_white=True,no_blue_support_extrusion=True,
            first_layer_blue_label_segments=len(blue),first_layer_filament_order=first_tools,
            model_path_geometry_materials_widths_identical=model_equal,support_path_geometry_materials_widths_identical=support_equal,
            interface_transition_geometry_materials_widths_identical=contact_equal,first_layer_support_geometry_materials_widths_identical=bed_equal,
            model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],bed_clearance_mm=clearance,startup_tower=startup,tower=tower,warnings=warnings,
            seconds=estimate['total_predication'],grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        dump(WORK/'validation-progress.json',records)
        print(f'Plate {n}: {len(brim)} brim segments white; support white; {len(blue)} blue ID segments; model/contact paths identical; brim outline delta {brim_distance:.6f} mm.',flush=True)
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
    cat['Knot'].update(sha256=r['project_sha256'],white_brim_validation='release/knot-white-brim-r1/validation.json')
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
        groups=[('#727b84',.4,[p for p in first if p[1] not in SUPPORT|OTHER and p[0]!=3]),
                ('#cbd4db',.6,[p for p in first if p[1] in SUPPORT]),
                ('#ffffff',1.1,[p for p in first if p[1]=='Brim']),
                ('#68acff',1.1,[p for p in first if p[1] not in SUPPORT|OTHER and p[0]==3])]
        assert all(p[0]==1 for group in groups[1:3] for p in group[2]) and groups[2][2] and groups[3][2]
        for color,width,pool in groups:
            ax.add_collection(LineCollection([[p[3][:2],p[4][:2]] for p in pool],colors=color,linewidths=width))
        ax.set(xlim=(-8,338),ylim=(-8,328),aspect='equal',facecolor='#222831')
        ax.set_title(f'Plate {n} / F{n}',color='white',fontsize=11);ax.axis('off')
    fig.suptitle('Actual first-layer paths: white brims and supports, blue IDs',color='white',fontsize=17)
    fig.text(.5,.065,'Bright white: brim  |  Light gray: white support  |  Blue: permanent ID  |  Dark gray: model',ha='center',color='white',fontsize=11)
    fig.text(.5,.035,'View from above the bed. IDs read normally on the underside. Purge towers omitted from this illustration.',ha='center',color='#bbc3cc',fontsize=10)
    fig.subplots_adjust(left=.015,right=.985,bottom=.13,top=.88,hspace=.30,wspace=.10)
    fig.savefig(REPORT/'first-layer-brim-colors.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)


def document():
    r=json.loads((REPORT/'validation.json').read_text());assert digest(ROOT/'Knot.3mf')==r['project_sha256']
    def duration(s):
        m=round(s/60);return f'{m//60}h {m%60:02d}m'
    table='\n'.join(f"| {p['plate']} / F{p['plate']} | {p['brim_white_segments']} | {p['first_layer_blue_label_segments']} | {duration(p['seconds'])} | {p['grams']:.2f} g |" for p in r['plates'])
    text=f'''# Knot white tear-away brims — October 25, 2026

Current project: root **Knot.3mf**, Bambu Lab A2L, ten plates.

The user observed that the removable perimeter was still blue after the support
base correction. This perimeter is the **Brim** feature. The preceding release
assigned every brim segment to blue slot 3 on all ten plates. Support-color checks
did not cover brims; this revision checks both explicitly.

The only saved setting change is **first_layer_print_sequence: Auto [0] →
[1, 3, 2]**, white first, then blue, then wood if present. Actual first-layer
extrusion uses white then blue on all ten plates. Other-layer order remains Auto.
Brim width **1 mm**, object gap **0.1 mm** and **outer_only** mode are unchanged.
Support base stays explicitly white slot 1; its interface selector stays Auto.
The blue **P1 F1 through P10 F10** labels and five blue top layers remain intact.

## Native checks

All ten plates were freshly sliced and the final project reopened natively.

![Actual first-layer brim, support and label paths](first-layer-brim-colors.png)

- Every Brim extrusion uses **white slot 1**. No skirt extrusion is present.
- All support base/body extrusion uses **white slot 1**. There is no blue
  Support, Support interface or Support transition extrusion. Existing interface
  and transition material assignments remain unchanged.
- All model segment geometry, feature types, widths and material assignments
  are identical to the source, including first-layer IDs and upper skins.
- Support interface/transition paths and first-layer support bed-contact paths
  remain exactly identical. Native support-body hatch paths above layer one
  regenerate with the new ordering; these are not claimed identical.
- Brim loop start positions can move. Width and height are identical; the full
  outline agrees within **0.001 mm**, the coordinate rounding of the G-code,
  and total outline length differs by less than **0.01 mm** per plate. Maximum
  measured outline difference: **{max(p['brim_outline_hausdorff_mm'] for p in r['plates']):.6f} mm**.
- All original 3D archive entries are byte-identical; object/volume settings,
  support paint, poses, material boundaries, label STLs and CAD remain unchanged.
- Every G-code configuration differs only in first_layer_print_sequence.
  Checksums, printable bounds, startup/tower clearance and native reopening pass.
  No unexpected native warning is reported. Purge towers retain their necessary
  color changes and are excluded from the illustration above.

| Plate / part | White brim segments | Blue ID segments | Time | Material |
| --- | ---: | ---: | ---: | ---: |
{table}
| **Total** | | | **{duration(r['total_seconds'])}** | **{r['total_grams']:.2f} g** |

Times and material are slicer estimates including supports and purge.
Physical brim removal, label finish, durability and full-size fit remain
unqualified. No printer job was sent.

Project SHA-256: `{r['project_sha256']}`.

Source SHA-256: `{SOURCE_SHA}`.

Exact hashes, setting differences, per-feature material checks and native results
are in `provenance.json`, `validation.json`, `native-result.json` and
`native-reopen.json`. The preceding support-base and label reports retain their
historical hashes. Run `python scripts/audit_root_projects.py` after pulling.
'''
    (REPORT/'README.md').write_text(text,encoding='utf-8',newline='\n')
    path=ROOT/'release/root-projects/README.md';text=path.read_text(encoding='utf-8')
    text=re.sub(r'^\| Knot \|[^\n]+',f"| Knot | 10 | {duration(r['total_seconds'])} | {r['total_grams']:.2f} g |",text,flags=re.M)
    path.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','slice','validate','publish','preview','document'])
    action=parser.parse_args().action;(native if action=='slice' else globals()[action])()
