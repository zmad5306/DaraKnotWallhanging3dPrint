"""Switch current Knot from tree(auto) to normal(auto), with native validation.

Reuses the preceding rollback's preservation, joint and toolpath checks. Does
not change support activation, paint, clearances, object overrides or geometry.
"""
import argparse
import copy
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import revert_knot_infill_first as check
import audit_knot_rollback_joints as joints
from remove_unused_project_filaments import read, write, dump, digest, props, ASSET

ROOT=check.ROOT
WORK=ROOT/'.work/knot-normal-supports-r1'
REPORT=ROOT/'release/knot-normal-supports-r1'
BASE=WORK/'before.3mf'
EDIT=WORK/'editable.3mf'
FINAL=WORK/'final.3mf'
SOURCE_SHA='388cf37776eebfb59c714b5d0d54e4f8f52d3eff70e7a51da2df81fccfba92e4'
CHANGE={'support_type':['tree(auto)','normal(auto)']}
check.WORK,check.REPORT,check.BASE,check.EDIT,check.FINAL=WORK,REPORT,BASE,EDIT,FINAL
check.SETTING_CHANGE=CHANGE
check.LOCKS={**check.LOCKS,'support_type':'normal(auto)'}
joints.WORK,joints.REPORT=WORK,REPORT


def build():
    source=ROOT/'Knot.3mf'; assert digest(source)==SOURCE_SHA
    catalog=json.loads((ROOT/'release/root-projects/catalog.json').read_text())
    assert catalog['Knot']['sha256']==SOURCE_SHA
    WORK.mkdir(parents=True,exist_ok=True)
    if not BASE.exists(): shutil.copyfile(source,BASE)
    assert digest(BASE)==SOURCE_SHA
    files=read(BASE); s=json.loads(files['Metadata/project_settings.config'])
    assert s['support_type']=='tree(auto)' and s['support_style']=='default'
    assert s['is_infill_first']=='0'
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    assert len(cfg.findall('object'))==len(cfg.findall('plate'))==10
    for obj in cfg.findall('object'):
        assert props(obj)['enable_support']=='1' and props(obj)['support_interface_spacing']=='0.2'
    assert not any(m.get('key') in ('support_type','support_style') for m in cfg.iter('metadata'))
    files['Metadata/project_settings.config'],count=re.subn(
        rb'("support_type"\s*:\s*)"tree\(auto\)"',rb'\g<1>"normal(auto)"',files['Metadata/project_settings.config'])
    assert count==1
    expected=copy.deepcopy(s); expected['support_type']='normal(auto)'
    assert json.loads(files['Metadata/project_settings.config'])==expected
    for n in list(files):
        if ASSET.fullmatch(n) or n in ('Metadata/slice_info.config','Metadata/filament_sequence.json'): del files[n]
    files['Metadata/model_settings.config']=re.sub(
        rb'\s*<metadata key="(?:gcode|thumbnail|thumbnail_no_light|top|pick)_file" value="[^"]*"\s*/>',b'',files['Metadata/model_settings.config'])
    for n in list(files):
        if n.endswith('.rels'):
            def retained(m):
                rel=ET.fromstring(m[0])
                return m[0] if rel.get('TargetMode')=='External' or rel.get('Target').lstrip('/') in files else b''
            files[n]=re.sub(rb'<Relationship\s[^>]+/>',retained,files[n])
    write(EDIT,files,BASE)
    dump(REPORT/'provenance.json',dict(source_project='Knot.3mf',source_project_sha256=SOURCE_SHA,
        editable_sha256=digest(EDIT),changed_setting=CHANGE,source_catalog_entry=catalog['Knot'],
        protected_before=check.protected(),user_request='Switch the knot to normal supports instead of trees.',
        support_activation='Existing per-object enable_support = 1 retained on all ten objects',
        support_style='default retained',support_on_build_plate_only='1 retained',
        physical_support_cleanup_and_joint_fit_unqualified=True))
    print('Built normal(auto) support project; every other option and all geometry preserved.',flush=True)


def geometry():
    joints.geometry(EDIT)


def publish():
    report=json.loads((REPORT/'validation.json').read_text()); proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(FINAL)==report['project_sha256'] and digest(ROOT/'Knot.3mf')==SOURCE_SHA
    assert check.protected()==proof['protected_before']==report['protected_after']
    catpath=ROOT/'release/root-projects/catalog.json'; catalog=json.loads(catpath.read_text())
    assert catalog['Knot']==proof['source_catalog_entry']
    catalog['Knot'].update(sha256=digest(FINAL),normal_supports_validation='release/knot-normal-supports-r1/validation.json')
    hp=ROOT/'release/root-projects/gcode-sha256.json'; hashes=json.loads(hp.read_text())
    hashes['Knot']={f"plate_{p['plate']}":p['gcode_sha256'] for p in report['plates']}
    # Stage and atomically replace the explicitly named production container;
    # do not truncate a valid release if Windows rejects an open-for-write.
    staged=WORK/'publish.3mf'
    target=ROOT/'Knot.3mf'
    assert staged.resolve().is_relative_to(ROOT.resolve()) and target.resolve().parent==ROOT.resolve()
    shutil.copyfile(FINAL,staged)
    assert digest(staged)==report['project_sha256'] and digest(target)==SOURCE_SHA
    staged.replace(target)
    dump(catpath,catalog); dump(hp,hashes)
    shutil.copyfile(REPORT/'native-result.json',ROOT/'release/root-projects/Knot-native.json')
    assert digest(ROOT/'Knot.3mf')==report['project_sha256'] and check.protected()==proof['protected_before']
    print('Updated root Knot.3mf with ten validated normal-support slices.',flush=True)


def document():
    report=json.loads((REPORT/'validation.json').read_text())
    assert digest(ROOT/'Knot.3mf')==report['project_sha256']
    def atomic_text(path,text):
        assert path.resolve().is_relative_to(ROOT.resolve())
        staged=WORK/(path.parent.name+'-'+path.name+'.pending')
        staged.write_text(text,encoding='utf-8',newline='\n')
        staged.replace(path)
    before=json.loads((ROOT/'release/knot-infill-first-revert-r1/validation.json').read_text())
    def duration(seconds):
        minutes=round(seconds/60)
        return f'{minutes//60}h {minutes%60:02d}m'
    table='\n'.join(f"| F{p['plate']} / {p['plate']} | {duration(p['seconds'])} | {p['grams']:.2f} g |" for p in report['plates'])
    text=f'''# Knot normal supports — October 24, 2026

Current file: **root `Knot.3mf`**, Bambu Lab A2L, ten plates F1–F10. Open as a project.

The user requested normal supports instead of trees. The only setting change is **`support_type`: `tree(auto)` → `normal(auto)`**. All ten plates have fresh native Bambu Studio 02.08.02.61 slices.

Infill-first stays **off**. Support style remains `default`; supports remain enabled per object. Saved support paint, build-plate-only support, 0.20 mm object interface spacing, 0.20 mm top and bottom gaps, interface layers, support speeds/material and every other parameter are preserved. Structural 8% gyroid, 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers and Textured PEI remain. Original geometry, poses, CAD/STL, filament profiles and the other six root projects are unchanged. Letter's veneer tree supports are unchanged.

## Verification

- Exact comparison of all project settings and every G-code configuration: only support type differs.
- Native slice/save and final native reopen comparisons retain geometry, poses, paint and object/volume settings. Protected artifacts are hashed before/after.
- All ten G-codes contain `normal(auto)`, `is_infill_first = 0`, positive support and support-interface extrusion, valid checksums, and verified bed/tower clearance including actual supports.
- All 14 joints / 28 keys measured from embedded triangles; 140 current key/groove path comparisons preserve walls preceding fill and nonoverlapping idealized commanded bead envelopes. Minimum commanded clearance: **{report['minimum_commanded_key_clearance_mm']:.4f} mm**.
- All 42 removed lap-pad sites, five blue layers, all 50 Z12.4 reinforcement modifiers and five-layer top-skin continuity remain. Actual top-surface directions are preserved. Stored notices concern unavailable traditional timelapse only.

Commanded bead envelopes do not measure deposited PLA, sag, support residue or physical fit. **Normal-support removal and full-size joint fit remain physically unqualified.** The preceding reported full-size fit failure remains recorded; this change does not establish its cause. No printer job was sent.

Normal supports include Bambu's `Support transition` paths inside joint grooves. These are classified as removable support, excluded from model-fit measurements, and included in bed/tower clearance checks. An initial audit flag exposed this previously unhandled support label; the parser was corrected and the current checks rerun. Groove support material must be removed before assembly; digital checks do not establish cleanup quality.

## Native estimates

| Piece / plate | Time | Material |
| --- | ---: | ---: |
{table}
| **Total** | **{duration(report['total_seconds'])}** | **{report['total_grams']:.2f} g** |

Previous tree-support source: {duration(before['total_seconds'])}, {before['total_grams']:.2f} g. These are slicer estimates, not measured print outcomes.

## Exact files and evidence

- Current project SHA-256: `{report['project_sha256']}`
- Source project SHA-256: `{report['source_project_sha256']}`
- `provenance.json`: source, single authorized setting change and protected hashes.
- `validation.json`: native roundtrip/reopen, per-plate checks, checksums and estimates.
- `joint-geometry.json` and `joint-toolpaths.json`: current geometry and emitted-path measurements.
- `native-result.json` and `native-reopen.json`: native completion results.

The previous rollback and older release evidence retain their original hashes and are linked through the source chain. Run `python scripts/audit_root_projects.py` for the current release audit.
'''
    atomic_text(REPORT/'README.md',text)
    path=ROOT/'release/root-projects/README.md'; text=path.read_text(encoding='utf-8')
    text=re.sub(r'^\| Knot \|[^\n]+',f"| Knot | 10 | {duration(report['total_seconds'])} | {report['total_grams']:.2f} g |",text,flags=re.M)
    text=text.replace('Current root `Knot.3mf` has `is_infill_first = 0` and ten fresh native slices after the reported full-size key/groove fit failure.',
        'The preceding rollback set `is_infill_first = 0` and generated ten fresh native slices after the reported full-size key/groove fit failure. The normal-support revision above supersedes that exact container and its slices while retaining infill-first off.')
    note='''## Knot normal supports, 2026-10-24

Current root `Knot.3mf` uses **normal(auto)** supports on all ten F1–F10 plates at the user's request. Infill-first stays off. Only support type changes; saved support activation/paint, build-plate-only support, 0.20 mm object interface spacing and top gap, all other settings, geometry and poses remain. All ten plates are resliced and the final project passes native reopen. Actual support/interface extrusion, bed/tower clearance, current key/groove paths, colors, pad removal and reinforcement skin are checked. CAD/STL and the other six projects, including Letter's veneer tree supports, remain byte-identical. See [the current verification record](../knot-normal-supports-r1/README.md). Support cleanup and physical joint fit remain unqualified.

'''
    assert '## Knot normal supports, 2026-10-24' not in text
    text=text.replace('## Knot infill-first rollback, 2026-10-24',note+'## Knot infill-first rollback, 2026-10-24')
    atomic_text(path,text)
    print('Updated current support release documentation and estimates.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['build','slice','geometry','validate','publish','document'])
    action=parser.parse_args().action
    if action=='slice': check.native()
    elif action=='validate': check.validate()
    else: globals()[action]()
