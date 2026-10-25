"""User-requested infill-first rollback, starting from the saved root Knot.

Change one process option, discard stale caches, slice natively, and preserve
the original geometry/paint/poses and all other options. Never send a print.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
from remove_unused_project_filaments import read, write, dump, digest, sha, props, ASSET, EXE

WORK = ROOT / '.work/knot-infill-first-revert-r1'
REPORT = ROOT / 'release/knot-infill-first-revert-r1'
BASE = WORK / 'before.3mf'
EDIT = WORK / 'editable.3mf'
FINAL = WORK / 'final.3mf'
SETTING_CHANGE = {'is_infill_first': ['1', '0']}
LOCKS = dict(sparse_infill_density='8%', sparse_infill_pattern='gyroid',
             layer_height='0.2', initial_layer_print_height='0.2', wall_loops='4',
             top_shell_layers='5', bottom_shell_layers='5', curr_bed_type='Textured PEI Plate',
             is_infill_first='0', support_top_z_distance='0.2')


def protected():
    paths = [p for p in ROOT.glob('*.3mf') if p.name != 'Knot.3mf']
    paths += list(ROOT.glob('*.scad')) + list(ROOT.glob('* STL/*.stl'))
    paths += list((ROOT / 'release/samples').glob('*.3mf'))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def build():
    WORK.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((ROOT / 'release/root-projects/catalog.json').read_text())
    source_hash = digest(ROOT / 'Knot.3mf')
    assert source_hash == catalog['Knot']['sha256']
    if not BASE.exists():
        shutil.copyfile(ROOT / 'Knot.3mf', BASE)
    assert digest(BASE) == source_hash
    files = read(BASE)
    old = json.loads(files['Metadata/project_settings.config'])
    assert old['is_infill_first'] == '1'
    new = copy.deepcopy(old)
    new['is_infill_first'] = '0'
    for k, v in LOCKS.items():
        assert new[k] == v, (k, new[k])
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    assert len(cfg.findall('plate')) == len(cfg.findall('object')) == 10
    assert not any(m.get('key') == 'is_infill_first' for m in cfg.iter('metadata'))
    files['Metadata/project_settings.config'], count = re.subn(
        rb'("is_infill_first"\s*:\s*)"1"', rb'\g<1>"0"', files['Metadata/project_settings.config'])
    assert count == 1 and json.loads(files['Metadata/project_settings.config']) == new
    for n in list(files):
        if ASSET.fullmatch(n) or n in ('Metadata/slice_info.config', 'Metadata/filament_sequence.json'):
            del files[n]
    files['Metadata/model_settings.config'] = re.sub(
        rb'\s*<metadata key="(?:gcode|thumbnail|thumbnail_no_light|top|pick)_file" value="[^"]*"\s*/>', b'', files['Metadata/model_settings.config'])
    for n in list(files):
        if n.endswith('.rels'):
            def retained(m):
                rel = ET.fromstring(m[0])
                return m[0] if rel.get('TargetMode') == 'External' or rel.get('Target').lstrip('/') in files else b''
            files[n] = re.sub(rb'<Relationship\s[^>]+/>', retained, files[n])
    write(EDIT, files, BASE)
    dump(REPORT / 'provenance.json', dict(source_project='Knot.3mf', source_project_sha256=source_hash,
        editable_sha256=digest(EDIT), changed_setting={'is_infill_first': ['1', '0']},
        source_catalog_entry=catalog['Knot'], protected_before=protected(),
        user_report='First three full-size knot pieces printed for a second time; keys do not fit joint grooves. User attributes failure to infill-first and requests reversal.',
        printed_file_hash_and_printer_not_independently_observed=True,
        cause_not_established_by_digital_checks=True))
    print('Built editable project: only is_infill_first changed 1 -> 0; stale slices removed.', flush=True)


def native(reopen=False):
    folder = WORK / ('reopen' if reopen else 'native')
    folder.mkdir(parents=True, exist_ok=True)
    args = ['--info', '--export-3mf', 'reopened.3mf'] if reopen else ['--slice', '0', '--export-3mf', 'sliced.3mf']
    source = FINAL if reopen else EDIT
    with (folder / 'run.log').open('w') as log:
        result = subprocess.run([str(EXE), *args, '--outputdir', str(folder), str(source)],
            cwd=EXE.parent, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    data = json.loads((folder / 'result.json').read_text())
    assert data['return_code'] == 0
    if not reopen:
        assert [p['id'] for p in data['sliced_plates']] == list(range(1, 11))
    print('Native reopen passed.' if reopen else 'All ten plates sliced natively.', flush=True)


def validate():
    import math
    import collections
    import numpy as np
    from shapely.geometry import MultiPoint
    from organize_root_projects import rows, compare
    from validate_print_project import scan_gcode
    from check_a2l_towers import check_startup_tower, check_tower
    from correct_knot_reinforcement_skin import crossings
    from audit_knot_rollback_joints import paths_with_width, toolpaths
    proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(BASE)==proof['source_project_sha256'] and digest(EDIT)==proof['editable_sha256']
    assert protected()==proof['protected_before']
    old,edited,sliced=[read(p) for p in (BASE,EDIT,WORK/'native/sliced.3mf')]
    original_settings=json.loads(old['Metadata/project_settings.config'])
    s,objects=rows(EDIT)
    expected=copy.deepcopy(original_settings)
    for key,(before,after) in SETTING_CHANGE.items():
        assert expected[key]==before
        expected[key]=after
    assert s==expected==json.loads(sliced['Metadata/project_settings.config'])
    native_check=compare(EDIT,WORK/'native/sliced.3mf'); assert not native_check['settings_changes']
    cfg=ET.fromstring(old['Metadata/model_settings.config']); nc=ET.fromstring(sliced['Metadata/model_settings.config'])
    ec=ET.fromstring(edited['Metadata/model_settings.config'])
    assert [ET.tostring(o) for o in cfg.findall('object')]==[ET.tostring(o) for o in ec.findall('object')]
    for a,b in zip(cfg.findall('plate'),nc.findall('plate')):
        assert len(a.findall('model_instance'))==len(b.findall('model_instance'))==1
        for md in list(a.findall('metadata')): a.remove(md)
        for md in b.findall('metadata'): a.insert(0,copy.deepcopy(md))
        ai,bi=a.find('model_instance'),b.find('model_instance')
        assert props(ai)['object_id']==props(bi)['object_id']
        for md in ai.findall('metadata'):
            if md.get('key')=='identify_id': md.set('value',props(bi)['identify_id'])
    final=dict(old)
    final['Metadata/project_settings.config']=edited['Metadata/project_settings.config']
    final['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
    for n,data in sliced.items():
        if ASSET.fullmatch(n) or n in ('Metadata/slice_info.config','Metadata/filament_sequence.json'): final[n]=data
    allowed={'Metadata/project_settings.config','Metadata/model_settings.config','Metadata/slice_info.config','Metadata/filament_sequence.json'}
    allowed|={n for n in final if ASSET.fullmatch(n)}
    unchanged={n:sha(v) for n,v in old.items() if n not in allowed}
    assert all(sha(final[n])==h for n,h in unchanged.items())
    for n in old:
        if n.startswith('3D/') and not n.endswith('.rels'): assert old[n]==edited[n]==final[n],n
    for k,v in LOCKS.items(): assert s[k]==v
    assert s['printer_model']=='Bambu Lab A2L' and s['nozzle_diameter']==['0.4']
    count=blue=0
    for obj in objects:
        assert obj['settings']['support_interface_spacing']=='0.2'
        assert obj['settings']['enable_support']=='1'
        for part in obj['parts']:
            effective={**s,**obj['settings'],**part['settings']}
            reinforcement=part['settings'].get('name')=='Local solid screw reinforcement'
            for k,v in LOCKS.items():
                assert effective[k]==('100%' if reinforcement and k=='sparse_infill_density' else v),(obj['name'],k)
            if reinforcement:
                assert np.allclose(part['mesh'].bounds[:,2],[0,12.4],atol=1e-6); count+=1
            if part['settings'].get('extruder')=='3':
                assert np.allclose(part['mesh'].bounds[:,2],[12.5,13.5],atol=1e-6); blue+=1
    assert count==50 and blue==10
    geometry=json.loads((REPORT/'joint-geometry.json').read_text())
    assert geometry['project_sha256']==digest(EDIT) and geometry['key_count']==28
    plan=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())
    frame=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/frame-geometry-validation.json').read_text())
    info=ET.fromstring(final['Metadata/slice_info.config'])
    results=json.loads((WORK/'native/result.json').read_text())
    assert results['return_code']==0 and len(info.findall('plate'))==10
    records=[]; pad_checks=[]; keypaths={}
    def angles(paths):
        groups=collections.defaultdict(collections.Counter)
        for slot,feature,ends,width in paths:
            delta=ends[1]-ends[0]; length=float(np.linalg.norm(delta[:2]))
            if feature=='Top surface' and length>.5:
                a=round(((math.degrees(math.atan2(delta[1],delta[0])))%180)*2)/2
                groups[(slot,round(float(ends[1,2]),2))][a]+=length
        return {k:v.most_common(1)[0][0] for k,v in groups.items() if sum(v.values())>10}
    for obj in objects:
        number=obj['plate']; name=f'Metadata/plate_{number}.gcode'; raw=final[name]; text=raw.decode()
        assert sha(raw)!=sha(old[name]),('Stale slice',number)
        assert hashlib.md5(raw).hexdigest()==final[name+'.md5'].decode().strip().lower()
        assert '; EXECUTABLE_BLOCK_END' in text
        config=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.M))
        before_config=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',old[name].decode(),re.M))
        diff={k:[before_config.get(k),config.get(k)] for k in set(config)|set(before_config) if before_config.get(k)!=config.get(k)}
        assert diff==SETTING_CHANGE,(number,diff)
        for k,v in LOCKS.items(): assert config[k]==v,(number,k,config[k])
        assert config['nozzle_diameter']=='0.4'
        scan=scan_gcode(text); lo,hi=np.array(scan['bead_xy_bounds_mm'])
        assert scan['features'].get('Support',0)>0 and scan['features'].get('Support interface',0)>0
        clearance=float(min(*lo,*(np.array([330,320])-hi))); assert clearance>.5
        assert scan['model_extrusion_z_by_filament_mm']['3']==[12.8,13.0,13.2,13.4,13.6]
        assert set(scan['model_extrusion_z_by_filament_mm'])=={'1','2','3'}
        t=obj['transform']
        hulls=[MultiPoint((p['mesh'].vertices@t[:3,:3].T+t[:3,3])[:,:2]).convex_hull for p in obj['parts'] if p['subtype']=='normal_part']
        top=max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values()); assert top<=325
        startup=check_startup_tower(s,hulls,3,top,number)
        tower=check_tower(text,hulls,[0,0,330,320]); tower.pop('actual_tower_convex_envelope')
        paths=paths_with_width(text,t)
        oldpaths=paths_with_width(old[name].decode(),t)
        before_angles,after_angles=angles(oldpaths),angles(paths)
        assert before_angles.keys()==after_angles.keys()
        for k,v in before_angles.items(): assert abs((v-after_angles[k]+90)%180-90)<=.5,(number,k,v,after_angles[k])
        keypaths[number]=[p for p in paths if 5.19<=p[2][1,2]<=6.01]
        a=np.array([p[2] for p in paths]); starts=a[:,0,:2]; deltas=a[:,1,:2]-starts; lengths=(deltas*deltas).sum(axis=1)
        for j,pr in zip(plan['frame_joints'],frame['joints']):
            if j[0]!=number-1: continue
            for xy in pr['seating_pads_xy']:
                target=np.array(xy); frac=np.clip(((target-starts)*deltas).sum(axis=1)/lengths,0,1)
                near=np.linalg.norm(starts+frac[:,None]*deltas-target,axis=1)<.65
                height=float(a[near,:,2].max()); assert abs(height-4.8)<.001
                pad_checks.append(dict(joint=pr['joint'],plate=number,xy_assembly_mm=xy,maximum_model_z_mm=height))
        shell=[p for p in paths if 12.79<=p[2][1,2]<=13.61]; skin=[]
        for p in obj['parts']:
            if p['settings'].get('name')!='Local solid screw reinforcement': continue
            bounds=p['mesh'].bounds; center=bounds[:,:2].mean(axis=0); radius=float(np.ptp(bounds[:,0])/2)
            cross=crossings(shell,center,radius); assert min(cross.values())>=5,(number,center,cross)
            skin.append(dict(center_assembly_mm=center.tolist(),crossing_segments=cross))
        layer_orders={}
        for label,ps in [('before',oldpaths),('after',paths)]:
            features=[p[1] for p in ps if abs(p[2][1,2]-2.6)<.001]
            if 'Bridge' in features and 'Overhang wall' in features:
                layer_orders[label]=dict(first_bridge=features.index('Bridge'),first_overhang_wall=features.index('Overhang wall'))
        pi=next(p for p in info.findall('plate') if props(p)['index']==str(number))
        warnings=[w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
        estimate=next(p for p in results['sliced_plates'] if p['id']==number)
        records.append(dict(plate=number,source_gcode_sha256=sha(old[name]),gcode_sha256=sha(raw),md5_verified=True,
            gcode_setting_changes=diff,model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],
            support_extrusion_moves=scan['features']['Support'],support_interface_extrusion_moves=scan['features']['Support interface'],
            support_transition_extrusion_moves=scan['features'].get('Support transition',0),
            bed_clearance_mm=clearance,startup_tower=startup,tower=tower,warnings=warnings,
            top_surface_directions_preserved=True,screw_skin_continuity=skin,photo_rabbet_layer_order=layer_orders,
            seconds=estimate['total_predication'],grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        dump(WORK/'validation-progress.json',records)
        print(f'Plate {number}: configuration, extrusion, lap pads, screw skin, colors and bounds checked.',flush=True)
    assert len(pad_checks)==42
    jointpaths=toolpaths(keypaths)
    write(FINAL,final,BASE)
    final_check=compare(EDIT,FINAL); assert not final_check['settings_changes']
    native(True)
    reopen_check=compare(FINAL,WORK/'reopen/reopened.3mf'); assert not reopen_check['settings_changes']
    assert protected()==proof['protected_before']
    report=dict(project='Knot.3mf',project_sha256=digest(FINAL),source_project_sha256=proof['source_project_sha256'],
        editable_sha256=digest(EDIT),native_project_sha256=digest(WORK/'native/sliced.3mf'),
        changed_setting=SETTING_CHANGE,all_other_project_settings_preserved=True,
        geometry_poses_paint_byte_preserved=True,object_volume_overrides_preserved=True,
        preserved_archive_entries_sha256=unchanged,native_roundtrip=native_check,final_geometry_check=final_check,
        native_reopen_verified=True,native_reopen_geometry_check=reopen_check,fresh_native_slices=True,
        protected_after=protected(),plates=records,removed_pad_toolpath_checks=pad_checks,
        joint_geometry_report=(REPORT/'joint-geometry.json').relative_to(ROOT).as_posix(),
        joint_geometry_report_sha256=digest(REPORT/'joint-geometry.json'),
        joint_toolpath_report=(REPORT/'joint-toolpaths.json').relative_to(ROOT).as_posix(),
        joint_toolpath_report_sha256=digest(REPORT/'joint-toolpaths.json'),
        minimum_commanded_key_clearance_mm=jointpaths['minimum_commanded_clearance_mm'],
        blue_layer_count=5,blue_modifier_count=10,modifier_count=50,
        all_five_top_shell_layers_cross_former_modifier_boundary=True,
        total_seconds=sum(r['seconds'] for r in records),total_grams=sum(r['grams'] for r in records),
        physical_fit_confirmation_pending=True,printer_job_sent=False)
    dump(REPORT/'validation.json',report)
    shutil.copyfile(WORK/'native/result.json',REPORT/'native-result.json')
    shutil.copyfile(WORK/'reopen/result.json',REPORT/'native-reopen.json')
    print('All project checks passed.',flush=True)


def publish():
    report=json.loads((REPORT/'validation.json').read_text()); proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(FINAL)==report['project_sha256'] and digest(ROOT/'Knot.3mf')==proof['source_project_sha256']
    assert protected()==proof['protected_before']==report['protected_after']
    catpath=ROOT/'release/root-projects/catalog.json'; catalog=json.loads(catpath.read_text())
    assert catalog['Knot']==proof['source_catalog_entry']
    catalog['Knot'].update(sha256=digest(FINAL),infill_first_revert_validation='release/knot-infill-first-revert-r1/validation.json')
    hashespath=ROOT/'release/root-projects/gcode-sha256.json'; hashes=json.loads(hashespath.read_text())
    hashes['Knot']={f"plate_{r['plate']}":r['gcode_sha256'] for r in report['plates']}
    shutil.copyfile(FINAL,ROOT/'Knot.3mf')
    dump(catpath,catalog); dump(hashespath,hashes)
    shutil.copyfile(REPORT/'native-result.json',ROOT/'release/root-projects/Knot-native.json')
    assert digest(ROOT/'Knot.3mf')==report['project_sha256'] and protected()==proof['protected_before']
    print('Updated root Knot.3mf and current release hashes.',flush=True)


def document():
    report=json.loads((REPORT/'validation.json').read_text())
    assert digest(ROOT/'Knot.3mf')==report['project_sha256']
    def duration(seconds):
        minutes=round(seconds/60)
        return f'{minutes//60}h {minutes%60:02d}m'
    table='\n'.join(f"| F{p['plate']} / {p['plate']} | {duration(p['seconds'])} | {p['grams']:.2f} g |" for p in report['plates'])
    text=f'''# Knot infill-first rollback — October 24, 2026

Current file: **root `Knot.3mf`**, Bambu Lab A2L, ten plates F1–F10. Open it as a project.

The user reports that the first three full-size pieces, printed a second time, have keys that do not fit their joint grooves. The user requested infill-first off. The exact printed file hash/printer were not independently observed. The cause is not established by digital checks.

## Change

`is_infill_first`: **1 → 0**, globally. All ten plates have fresh native slices from Bambu Studio 02.08.02.61. No key/groove dimensions or other process/material options were changed. Object support-interface spacing stays 0.20 mm; support top gap stays 0.20 mm.

The original 8% gyroid, 0.4 mm nozzle, 0.20 mm initial/regular layers, four walls, five top/bottom layers, Textured PEI, three filament profiles, temperatures, speeds, flow, colors, poses, supports and purge settings remain. All CAD/STL and the other six root projects remain byte-identical. All 42 removed lap pads remain absent. All 50 solid screw modifiers remain at Z12.4; the five blue layers remain at native Z12.8–13.6.

## Checks actually performed

1. **Settings and preservation:** full setting dictionaries and every G-code configuration differ only in `is_infill_first`. Original geometry, support paint, object/volume overrides and actual poses are retained. Native slicing and final native reopen were compared with the editable source. Protected files were hashed before/after.
2. **Current joint meshes:** original triangle sections of all 14 joints / 28 keys, including 420 transverse probes. Keys measure approximately 3.00 mm; primary grooves 3.30 mm; relieved secondary grooves 4.40 mm. Key tops are Z6.00 and groove roofs Z6.30. Minimum nominal section clearance is about 0.149 mm. Serialized meshes contain only overlap slivers below 0.0001 mm thickness; the largest is about 0.0000271 mm. No release geometry was welded or regenerated.
3. **Actual emitted paths:** 140 key/groove layer comparisons at Z5.2, 5.4, 5.6, 5.8 and 6.0. Key walls precede fill. Idealized commanded bead envelopes do not overlap; minimum separation is **{report['minimum_commanded_key_clearance_mm']:.4f} mm**. All ten plate checksums, bed/tower clearances, material heights, finish directions, 42 pad sites and five-layer screw-skin continuity checks pass. Stored notices concern unavailable traditional timelapse only.

The bead envelopes use commanded G1 positions and line widths. They do not measure actual deposited PLA, sag, swelling, shrinkage or support residue. The original `is_infill_first = 0` behavior also restores the former photo-rabbet feature order; no substitute geometry or support change was introduced.

## Estimates

| Piece / plate | Native time | Material |
| --- | ---: | ---: |
{table}
| **Total** | **{duration(report['total_seconds'])}** | **{report['total_grams']:.2f} g** |

These are slicer estimates. **The rollback is physically unqualified.** The earlier full-curve test does not establish full-size key fit. The already printed pieces are not changed by this file update. No printer job was sent.

## Identity and evidence

- Current SHA-256: `{report['project_sha256']}`
- Source SHA-256: `{report['source_project_sha256']}`
- `provenance.json`: exact source, authorized change and protected hashes.
- `validation.json`: saved/native/reopened comparisons, per-plate checks and estimates.
- `joint-geometry.json`: current embedded-mesh measurements.
- `joint-toolpaths.json`: commanded envelope and ordering checks, with physical limits.
- `native-result.json` and `native-reopen.json`: native slicer results.

Earlier reports remain historical and are linked through the source hash; they are not rewritten to describe this rollback. The old infill-first full-size configuration is withdrawn. Run `python scripts/audit_root_projects.py` to check the current distributed files and evidence chain.
'''
    (REPORT/'README.md').write_text(text,encoding='utf-8',newline='\n')
    path=ROOT/'release/root-projects/README.md'
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'^\| Knot \|[^\n]+',f"| Knot | 10 | {duration(report['total_seconds'])} | {report['total_grams']:.2f} g |",text,flags=re.M)
    text=text.replace('The r3 full-curve knot test was reported successful; the full-size corrected knot remains physically unqualified.',
        'The r3 full-curve knot test was reported successful. On October 24 the user reported that the first three full-size knot pieces, printed for a second time, had keys that did not fit their grooves. Infill-first was rolled back at the user\'s request; the rollback remains physically unqualified.')
    note='''
## Knot infill-first rollback, 2026-10-24

Current root `Knot.3mf` has `is_infill_first = 0` and ten fresh native slices after the reported full-size key/groove fit failure. This changes only infill-first; the 0.20 mm object support-interface spacing, 0.20 mm support top gap, geometry, keys/grooves, poses, materials and all other settings remain. CAD/STL and other projects are byte-identical. All 14 joints / 28 keys were measured from the current meshes; 140 emitted key/groove layer comparisons check commanded clearance and walls preceding fill. All ten configurations, checksums, bed/tower clearances, pad removals, finish directions, blue layers and screw skin were checked, followed by native reopen. See [the current rollback record](../knot-infill-first-revert-r1/README.md) for hashes, limits and estimates. Older Knot records below describe its source revisions. This is not a physical fit pass, and the cause of the reported failure remains unconfirmed.
'''
    assert '## Knot infill-first rollback, 2026-10-24' not in text
    text=text.replace('\n## Preservation evidence\n',note+'\n## Preservation evidence\n')
    path.write_text(text,encoding='utf-8',newline='\n')
    print('Documented the rollback, actual checks and unresolved physical fit.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'slice', 'validate', 'publish', 'document'])
    args = parser.parse_args()
    if args.action == 'slice':
        native()
    else:
        globals()[args.action]()
