"""Pin Knot support bases to white; retain blue IDs and every other setting.

Revision-specific source, native slicing, complete support-color inspection,
model-path comparison, protected-file checks and native reopen precede publish.
"""
import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'.work/python-libs')]
import numpy as np
from shapely.geometry import MultiPoint
from organize_root_projects import rows,compare
from remove_unused_project_filaments import read,write,digest,props,ASSET
from development_3mf import xml
from revert_knot_infill_first import protected,LOCKS
import revert_knot_infill_first as native_driver
from validate_print_project import TOKEN,scan_gcode
from check_a2l_towers import check_startup_tower,check_tower

WORK=ROOT/'.work/knot-white-support-base-r1'
REPORT=ROOT/'release/knot-white-support-base-r1'
BASE,EDIT,FINAL=[WORK/n for n in ('before.3mf','editable.3mf','final.3mf')]
SOURCE_SHA='b33d28f0fc7277758928321a09196929a53d5c63b5503548a51b408cb4f6e626'
CHANGE={'support_filament':['0','1']}
SUPPORT={'Support','Support interface','Support transition'}
OTHER={'Prime tower','Brim','Skirt'}


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')


def sha(data):return hashlib.sha256(data).hexdigest()


def build():
    assert digest(ROOT/'Knot.3mf')==SOURCE_SHA
    WORK.mkdir(parents=True,exist_ok=True)
    if not BASE.exists():shutil.copyfile(ROOT/'Knot.3mf',BASE)
    assert digest(BASE)==SOURCE_SHA
    files=read(BASE);old=json.loads(files['Metadata/project_settings.config'])
    assert old['support_filament']==old['support_interface_filament']=='0'
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    assert len(cfg.findall('plate'))==10
    assert not any(m.get('key') in ('support_filament','support_interface_filament') for m in cfg.iter('metadata'))
    files['Metadata/project_settings.config'],count=re.subn(rb'("support_filament"\s*:\s*)"0"',rb'\g<1>"1"',files['Metadata/project_settings.config'])
    assert count==1 and json.loads(files['Metadata/project_settings.config'])=={**old,'support_filament':'1'}
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
        authorization='Set support base to white and keep labels blue; reslice all ten plates, verify support colors, commit and push to main.',
        interface_setting='Auto (0), unchanged; actual colors inspected after slicing'))
    print('Built: support_filament 0 -> 1 only; interface stays Auto and all meshes remain unchanged.',flush=True)


def native(reopen=False):
    native_driver.WORK,native_driver.EDIT,native_driver.FINAL=WORK,EDIT,FINAL
    native_driver.native(reopen)


def assemble():
    old,edited,sliced=[read(p) for p in (BASE,EDIT,WORK/'native/sliced.3mf')]
    expected={**json.loads(old['Metadata/project_settings.config']),'support_filament':'1'}
    assert json.loads(edited['Metadata/project_settings.config'])==expected==json.loads(sliced['Metadata/project_settings.config'])
    native_check=compare(EDIT,WORK/'native/sliced.3mf');assert not native_check['settings_changes']
    cfg=ET.fromstring(old['Metadata/model_settings.config']);ec=ET.fromstring(edited['Metadata/model_settings.config']);nc=ET.fromstring(sliced['Metadata/model_settings.config'])
    assert [ET.tostring(o) for o in cfg.findall('object')]==[ET.tostring(o) for o in ec.findall('object')]
    for a,b in zip(cfg.findall('plate'),nc.findall('plate')):
        for md in list(a.findall('metadata')):a.remove(md)
        for md in b.findall('metadata'):a.insert(0,copy.deepcopy(md))
        ai,bi=a.find('model_instance'),b.find('model_instance')
        # Native save renumbers objects after the label modifiers were added.
        # Keep original model IDs; bind the fresh G-code's identify_id by plate.
        assert props(cfg.find(f"object[@id='{props(ai)['object_id']}']"))['name']==props(nc.find(f"object[@id='{props(bi)['object_id']}']"))['name']
        for md in ai.findall('metadata'):
            if md.get('key')=='identify_id':md.set('value',props(bi)['identify_id'])
    final=dict(old);final['Metadata/project_settings.config']=edited['Metadata/project_settings.config'];final['Metadata/model_settings.config']=xml(cfg)
    for name,data in sliced.items():
        if ASSET.fullmatch(name) or name in ('Metadata/slice_info.config','Metadata/filament_sequence.json'):final[name]=data
    assert all(final[n]==v for n,v in old.items() if n.startswith('3D/'))
    write(FINAL,final,BASE);compare(EDIT,FINAL)
    return native_check


def extrusion_paths(text):
    """Read all non-custom positive XY G1 extrusion, including indented T codes.

    Each tuple is tool, feature, width, start XYZ, end XYZ. Special machine
    selectors such as T1000/T65535 are not filament indexes.
    """
    x=y=z=e=0.;relative=False;xyz=False;tool=None;feature='Custom';width=None;paths=[]
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        elif line.startswith(('; LINE_WIDTH: ','; WIDTH: ')):width=float(line.split(': ',1)[1])
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if re.fullmatch(r'T[0-2]',cmd):tool=int(cmd[1:])+1
        elif cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ('G90','G91'):xyz=cmd=='G91'
        elif cmd=='G92':
            v={k:float(n) for k,n in TOKEN.findall(code)};x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ('G0','G1','G2','G3'):
            v={k:float(n) for k,n in TOKEN.findall(code)}
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e
            if de>0 and feature!='Custom' and math.hypot(nx-x,ny-y)>1e-7:
                assert cmd=='G1' and tool in (1,2,3) and width is not None
                paths.append((tool,feature,width,(x,y,z),(nx,ny,nz)))
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    return paths


def parser_check():
    text='''G90
M83
  T2 ; indented startup tool selection
G1 Z.2
; FEATURE: Support
; LINE_WIDTH: 0.5
G1 X10 E.1
G1 X11 E-.1
T0
G1 X12 E.2
; FEATURE: Support interface
G1 X13 E.1
T1000 O0
; FEATURE: Bottom surface
G1 X14 E.1
'''
    actual=extrusion_paths(text)
    assert [(p[0],p[1]) for p in actual]==[(3,'Support'),(1,'Support'),(1,'Support interface'),(1,'Bottom surface')]
    assert actual[1][3]==(11.,0.,.2)


def signatures(paths,include_tool=True):
    return sorted(((p[0],) if include_tool else ())+(p[1],p[2],*sorted((p[3],p[4]))) for p in paths)


def support_summary(paths):
    counts=collections.defaultdict(collections.Counter);heights=collections.defaultdict(set)
    for p in paths:
        if p[1] not in SUPPORT:continue
        counts[p[1]][str(p[0])]+=1;heights[p[1],str(p[0])].add(round(p[4][2],4))
    return {feature:{tool:dict(segments=count,z_mm=sorted(heights[feature,tool])) for tool,count in tools.items()} for feature,tools in counts.items()}


def validate():
    parser_check();proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(BASE)==SOURCE_SHA and digest(EDIT)==proof['editable_sha256'] and protected()==proof['protected_before']
    native_check=assemble();files=read(FINAL);old=read(BASE);settings,objects=rows(FINAL)
    for k,v in {**LOCKS,'support_type':'normal(auto)','support_filament':'1','support_interface_filament':'0','nozzle_diameter':['0.4']}.items():assert settings[k]==v
    result=json.loads((WORK/'native/result.json').read_text());info=ET.fromstring(files['Metadata/slice_info.config']);records=[]
    for obj in objects:
        n=obj['plate'];name=f'Metadata/plate_{n}.gcode';raw=files[name];text=raw.decode();oldtext=old[name].decode()
        assert raw!=old[name] and hashlib.md5(raw).hexdigest()==files[name+'.md5'].decode().strip().lower()
        cfg=lambda txt:dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',txt,re.M))
        a,b=cfg(oldtext),cfg(text);delta={k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)}
        assert delta==CHANGE,(n,delta)
        paths=extrusion_paths(text);before=extrusion_paths(oldtext)
        support=support_summary(paths);old_support=support_summary(before)
        assert set(support['Support'])=={'1'}
        assert all('3' not in tools for tools in support.values()),(n,support)
        assert support['Support interface'] and support['Support transition']
        assert old_support['Support']['3']['z_mm']==[.2]
        first=[p for p in paths if p[1]=='Support' and abs(p[4][2]-.2)<1e-6]
        assert first and {p[0] for p in first}=={1}
        model=[p for p in paths if p[1] not in SUPPORT|OTHER]
        oldmodel=[p for p in before if p[1] not in SUPPORT|OTHER]
        equal=signatures(model)==signatures(oldmodel)
        assert equal,(n,'Model path geometry/materials/widths changed')
        blue=[p for p in model if p[0]==3 and abs(p[4][2]-.2)<1e-6]
        assert blue and len(blue)==sum(p[0]==3 and abs(p[4][2]-.2)<1e-6 for p in oldmodel)
        support_geometry_equal=signatures([p for p in paths if p[1] in SUPPORT],False)==signatures([p for p in before if p[1] in SUPPORT],False)
        contact_features={'Support interface','Support transition'}
        contact_equal=signatures([p for p in paths if p[1] in contact_features])==signatures([p for p in before if p[1] in contact_features])
        assert contact_equal,(n,'Interface/transition contact paths or materials changed')
        first_support_equal=signatures(first,False)==signatures([p for p in before if p[1]=='Support' and abs(p[4][2]-.2)<1e-6],False)
        assert first_support_equal,(n,'Support bed-contact geometry changed')
        scan=scan_gcode(text)
        assert scan['model_extrusion_z_by_filament_mm']['3']==[.2,12.8,13,13.2,13.4,13.6]
        lo,hi=np.array(scan['bead_xy_bounds_mm']);clearance=float(min(*lo,*(np.array([330,320])-hi)));assert clearance>.5
        tr=obj['transform'];hulls=[MultiPoint((p['mesh'].vertices@tr[:3,:3].T+tr[:3,3])[:,:2]).convex_hull for p in obj['parts'] if p['subtype']=='normal_part']
        top=max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values())
        startup=check_startup_tower(settings,hulls,3,top,n);tower=check_tower(text,hulls,[0,0,330,320]);tower.pop('actual_tower_convex_envelope')
        pi=next(p for p in info.findall('plate') if props(p)['index']==str(n));warnings=[w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings)
        estimate=next(p for p in result['sliced_plates'] if p['id']==n)
        records.append(dict(plate=n,source_gcode_sha256=sha(old[name]),gcode_sha256=sha(raw),md5_verified=True,gcode_setting_changes=delta,
            support_before=old_support,support_after=support,all_support_base_white=True,no_blue_support_extrusion=True,
            first_layer_support_white_segments=len(first),first_layer_blue_label_segments=len(blue),
            model_path_geometry_materials_widths_identical=equal,support_path_geometry_widths_identical=support_geometry_equal,
            interface_transition_geometry_materials_widths_identical=contact_equal,first_layer_support_geometry_widths_identical=first_support_equal,
            model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],bed_clearance_mm=clearance,startup_tower=startup,tower=tower,warnings=warnings,
            seconds=estimate['total_predication'],grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        dump(WORK/'validation-progress.json',records)
        print(f'Plate {n}: all base support white; no blue supports; {len(blue)} blue label segments; model paths identical; support geometry identical={support_geometry_equal}.',flush=True)
    native(True);reopened=compare(FINAL,WORK/'reopen/reopened.3mf');assert not reopened['settings_changes']
    assert protected()==proof['protected_before']
    dump(REPORT/'validation.json',dict(project='Knot.3mf',project_sha256=digest(FINAL),source_project_sha256=SOURCE_SHA,changed_setting=CHANGE,
        native_roundtrip=native_check,native_reopen=reopened,fresh_native_slices=True,native_reopen_verified=True,
        all_other_project_settings_preserved=True,geometry_poses_paint_object_volume_overrides_preserved=True,
        all_original_3d_archive_entries_byte_identical=True,all_cad_stl_unchanged=True,
        preserved_archive_entries_sha256={n:sha(v) for n,v in old.items() if files.get(n)==v},
        changed_archive_entries=[n for n in set(old)|set(files) if old.get(n)!=files.get(n)],
        plates=records,total_seconds=sum(p['seconds'] for p in records),total_grams=sum(p['grams'] for p in records),
        evidence_sha256={'provenance.json':digest(REPORT/'provenance.json')},protected_after=protected(),
        parser_indented_tool_and_leading_decimal_extrusion_regression_passed=True,printer_job_sent=False,physical_print_outcome_unqualified=True))
    shutil.copyfile(WORK/'native/result.json',REPORT/'native-result.json');shutil.copyfile(WORK/'reopen/result.json',REPORT/'native-reopen.json')


def publish():
    r=json.loads((REPORT/'validation.json').read_text());p=json.loads((REPORT/'provenance.json').read_text())
    assert digest(FINAL)==r['project_sha256'] and digest(ROOT/'Knot.3mf')==SOURCE_SHA and protected()==p['protected_before']
    catpath=ROOT/'release/root-projects/catalog.json';cat=json.loads(catpath.read_text());assert cat['Knot']==p['source_catalog_entry']
    cat['Knot'].update(sha256=r['project_sha256'],white_support_base_validation='release/knot-white-support-base-r1/validation.json')
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
        groups=[('Other model','#727b84',.4,[p for p in first if p[1] not in SUPPORT|OTHER and p[0]!=3]),
            ('White support','#ffffff',.6,[p for p in first if p[1] in SUPPORT]),
            ('Blue ID','#68acff',1.1,[p for p in first if p[1] not in SUPPORT|OTHER and p[0]==3])]
        assert groups[1][3] and all(p[0]==1 for p in groups[1][3]) and groups[2][3]
        for _,color,width,pool in groups:
            ax.add_collection(LineCollection([[p[3][:2],p[4][:2]] for p in pool],colors=color,linewidths=width))
        ax.set(xlim=(-8,338),ylim=(-8,328),aspect='equal',facecolor='#222831')
        ax.set_title(f'Plate {n} / F{n}',color='white',fontsize=11);ax.axis('off')
    fig.suptitle('Actual first-layer paths on all ten plates',color='white',fontsize=17)
    fig.text(.5,.065,'White: support base assigned to slot 1  |  Blue: permanent ID assigned to slot 3  |  Gray: other model paths',ha='center',color='white',fontsize=11)
    fig.text(.5,.035,'Viewed from above the bed. IDs are mirrored here so they read normally on the finished underside.',ha='center',color='#bbc3cc',fontsize=10)
    fig.subplots_adjust(left=.015,right=.985,bottom=.13,top=.88,hspace=.30,wspace=.10)
    fig.savefig(REPORT/'first-layer-support-colors.png',dpi=160,facecolor=fig.get_facecolor());plt.close(fig)


def document():
    r=json.loads((REPORT/'validation.json').read_text());assert digest(ROOT/'Knot.3mf')==r['project_sha256']
    def duration(s):
        m=round(s/60);return f'{m//60}h {m%60:02d}m'
    table='\n'.join(f"| {p['plate']} / F{p['plate']} | {p['first_layer_support_white_segments']} | {p['first_layer_blue_label_segments']} | {duration(p['seconds'])} | {p['grams']:.2f} g |" for p in r['plates'])
    interfaces={t for p in r['plates'] for t in p['support_after']['Support interface']}
    text=f'''# Knot white support bases — October 25, 2026

Current production: root **Knot.3mf**, Bambu Lab A2L, ten plates.

The user observed blue supports after the first-layer labels were added and
explicitly approved fixing the support base to white, reslicing all ten plates,
verifying support colors, and committing/pushing to main.

The sole saved setting change is **support_filament: 0 (Auto) → 1 (white)**.
**support_interface_filament stays 0 (Auto)**. The existing **P1 F1 through
P10 F10** labels remain blue slot 3 in Z0–0.20 mm, 8 mm tall and underside-readable.
Original stock, all modifiers, material profiles, poses, support paint, normal
support type, gaps, interface spacing, density, patterns and all other saved
settings remain unchanged. All CAD and STL files are byte-identical.

## Actual native command checks

All ten plates have fresh native slices and native reopen verification.
Every positive support extrusion is classified by its actual tool selection:

![Actual first-layer support and label paths](first-layer-support-colors.png)

- Every **Support** base/body segment uses **slot 1 white**, including layer one.
- **No blue extrusion** appears in Support, Support interface or Support transition.
- Actual interface filament slots across the project: **{', '.join(sorted(interfaces))}**;
  the selector remains Auto. Detailed per-feature, per-slot layer lists are in
  `validation.json`.
- Each blue label has the same model extrusion segments as the preceding release.
  All model segment geometry, filament assignments, feature types and widths
  match the source on every layer, including labels, solid laps and upper skins.
- Support interfaces/transitions retain their exact path geometry, widths and
  material assignments. First-layer support bed-contact paths retain their exact
  geometry/widths with white replacing blue. Native support-body hatch paths
  above that layer are regenerated for the explicit white assignment; they are
  not claimed identical. Saved density, support pattern, gaps and all other
  parameters remain unchanged, and no floating-region warning is reported.
- The earlier release did contain blue base support at Z0.20 on all ten plates.
  The previous model-path verification excluded support features and missed this
  material assignment. This revision checks all three support feature classes.
- The parser checks indented startup tool commands, leading-decimal extrusion,
  relative/absolute extrusion, retractions and special non-filament T commands.
  A focused regression fixture verifies the indentation/decimal cases.
- All G-code configurations differ only by support_filament; checksums, bed/tower
  clearances including support and brim, source geometry/settings preservation
  and the final native reopen pass. No unexpected native warnings remain.

Counts below are actual first-layer extrusion segments, not separate objects.

| Plate / part | White support segments | Blue label segments | Time | Material |
| --- | ---: | ---: | ---: | ---: |
{table}
| **Total** | | | **{duration(r['total_seconds'])}** | **{r['total_grams']:.2f} g** |

Times/material are slicer estimates including supports and purge. Digital checks
do not establish physical support removal, label finish or full-size fit.
No printer job was sent.

Project SHA-256: `{r['project_sha256']}`.

Source SHA-256: `{SOURCE_SHA}`.

`provenance.json`, `validation.json`, `native-result.json` and
`native-reopen.json` record the exact source/change, per-plate colors and checks.
Earlier first-layer-label evidence remains a historical source record.
Run `python scripts/audit_root_projects.py` after pulling.
'''
    (REPORT/'README.md').write_text(text,encoding='utf-8',newline='\n')
    path=ROOT/'release/root-projects/README.md';text=path.read_text(encoding='utf-8')
    text=re.sub(r'^\| Knot \|[^\n]+',f"| Knot | 10 | {duration(r['total_seconds'])} | {r['total_grams']:.2f} g |",text,flags=re.M)
    path.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','slice','validate','publish','preview','document'])
    action=p.parse_args().action;(native if action=='slice' else globals()[action])()
