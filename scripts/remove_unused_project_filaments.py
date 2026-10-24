"""Remove the user-specified unused slots; natively regenerate affected slices.

Revision-specific migration: geometry and surviving material settings are exact
source copies. Backups and hash guards prevent applying this to another revision.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/unused-filaments-r1'
REPORT = ROOT / 'release/unused-filaments-r1'
EXE = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
KEEP = {'Knot': [0, 1, 3], 'Letter': [2]}
DRYER = {'filament_dev_ams_drying_ams_limitations': 2,
         'filament_dev_ams_drying_temperature': 4,
         'filament_dev_ams_drying_time': 4}
ASSET = re.compile(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)(\d+)(?:_small)?\.(?:png|json|gcode(?:\.md5)?)$')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(path.read_bytes())


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: z.read(n) for n in z.namelist()}


def write(path, files, source):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as z, zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
        infos = {i.filename: i for i in z.infolist()}
        for n, data in files.items():
            out.writestr(infos.get(n, n), data)


def props(node):
    return {m.get('key'): m.get('value') for m in node.findall('metadata')}


def protected():
    paths = [p for p in ROOT.glob('*.3mf') if p.stem not in KEEP]
    paths += list(ROOT.glob('*.scad')) + list(ROOT.glob('* STL/*.stl'))
    paths += list((ROOT / 'release/samples').glob('*.3mf'))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def compact_settings(s, keep):
    result = copy.deepcopy(s)
    preset = json.loads(next((ROOT / 'release/sunlu-silk-copper-r1/presets').glob('*A2L*.json')).read_text())
    count = len(s['filament_settings_id'])
    assert count == 4
    for k, v in s.items():
        if not isinstance(v, list):
            continue
        if k in DRYER:
            width = DRYER[k]
            assert len(v) == width * count
            result[k] = [x for i in keep for x in v[i*width:(i+1)*width]]
        elif (k in preset or k.startswith('filament_')) and len(v) == count:
            result[k] = [v[i] for i in keep]
        elif k in ('different_settings_to_system', 'inherits_group'):
            assert v == [''] * (count + 2)
            result[k] = [''] * (len(keep) + 2)
        elif k == 'flush_volumes_matrix':
            assert len(v) == count * count
            result[k] = [v[i*count+j] for i in keep for j in keep]
        elif k == 'flush_volumes_vector':
            assert len(v) == count * 2
            result[k] = [x for i in keep for x in v[i*2:i*2+2]]
        elif len(v) >= 4:
            assert k in {'bed_heat_soak_area', 'head_wrap_detect_zone', 'printable_area',
                         'wipe_tower_x', 'wipe_tower_y'}, (k, v)
    result['filament_self_index'] = [str(i+1) for i in range(len(keep))]
    # These are automatic selectors, not material array indexes.
    for k in ('solid_infill_filament', 'sparse_infill_filament', 'support_filament',
              'support_interface_filament', 'wall_filament'):
        assert s[k] == '0'
    return result


def compact_model(raw, keep):
    cfg = ET.fromstring(raw)
    mapping = {str(old+1): str(new+1) for new, old in enumerate(keep)}
    for md in cfg.iter('metadata'):
        key, value = md.get('key', ''), md.get('value')
        if key == 'extruder':
            assert value in mapping, ('Removed filament is used', value)
        elif key in ('filament_maps', 'filament_volume_maps'):
            assert len(value.split()) == 4
        elif any(x in key for x in ('filament', 'extruder', 'sequence')):
            assert key == 'filament_map_mode', (key, value)
    # Preserve all formatting and metadata except the authorized index changes.
    def replace(m):
        key, value = m[2].decode(), m[4].decode()
        if key == 'extruder':
            value = mapping[value]
        else:
            value = ' '.join(value.split()[i] for i in keep)
        return m[1] + m[2] + m[3] + value.encode() + m[5]
    return re.sub(rb'(<metadata key=")(extruder|filament_maps|filament_volume_maps)(" value=")([^"]*)(")', replace, raw)


def build():
    WORK.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((ROOT / 'release/root-projects/catalog.json').read_text())
    sourcefile = WORK / 'sources.json'
    if not sourcefile.exists():
        dump(sourcefile, catalog)
    assert json.loads(sourcefile.read_text()) == catalog
    records = {}
    for title, keep in KEEP.items():
        source = ROOT / (title + '.3mf')
        assert digest(source) == catalog[title]['sha256']
        before = WORK / title / 'before.3mf'
        before.parent.mkdir(exist_ok=True)
        if not before.exists():
            shutil.copyfile(source, before)
        assert digest(before) == digest(source)
        files = read(before)
        s = json.loads(files['Metadata/project_settings.config'])
        info = ET.fromstring(files['Metadata/slice_info.config'])
        used = {int(f.get('id'))-1 for f in info.iter('filament')}
        assert used == set(keep), (title, used)
        updated = compact_settings(s, keep)
        files['Metadata/project_settings.config'] = (json.dumps(updated, indent=2)+'\n').encode()
        files['Metadata/model_settings.config'] = compact_model(files['Metadata/model_settings.config'], keep)
        # Old cached slices refer to the previous indexes. Let Bambu create all
        # new slices, sequences and plate thumbnails from the edited project.
        for n in list(files):
            if ASSET.fullmatch(n) or n in ('Metadata/slice_info.config', 'Metadata/filament_sequence.json'):
                del files[n]
        files['Metadata/model_settings.config'] = re.sub(
            rb'\s*<metadata key="[^"]*_file" value="[^"]*"\s*/>', b'', files['Metadata/model_settings.config'])
        for n in list(files):
            if not n.endswith('.rels'):
                continue
            def retained_relation(m):
                rel = ET.fromstring(m[0])
                return m[0] if rel.get('TargetMode') == 'External' or rel.get('Target').lstrip('/') in files else b''
            files[n] = re.sub(rb'<Relationship\s[^>]+/>', retained_relation, files[n])
        editable = before.parent / 'editable.3mf'
        write(editable, files, before)
        records[title] = dict(source_project_sha256=digest(before), editable_sha256=digest(editable),
                              slot_map={str(i+1): j+1 for j, i in enumerate(keep)},
                              removed_slots=[i+1 for i in range(4) if i not in keep],
                              removed_profiles=[s['filament_settings_id'][i] for i in range(4) if i not in keep],
                              retained_profiles=updated['filament_settings_id'],
                              project_setting_changes={k: {'before': s[k], 'after': updated[k]}
                                                       for k in s if s[k] != updated[k]})
        print(title + ': unused slots removed; retained material values and original geometry preserved.', flush=True)
    dump(REPORT / 'provenance.json', dict(projects=records, protected_before=protected()))


def native(title, reopen=False):
    folder = WORK / title / ('reopen' if reopen else 'native')
    folder.mkdir(parents=True, exist_ok=True)
    source = WORK / title / ('final.3mf' if reopen else 'editable.3mf')
    args = ['--info', '--export-3mf', 'reopened.3mf'] if reopen else ['--slice', '0', '--export-3mf', 'sliced.3mf']
    with (folder / 'run.log').open('w') as log:
        result = subprocess.run([str(EXE), *args, '--outputdir', str(folder), str(source)],
                                cwd=EXE.parent, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    result.check_returncode()
    data = json.loads((folder / 'result.json').read_text())
    assert data['return_code'] == 0
    if not reopen:
        assert [p['id'] for p in data['sliced_plates']] == list(range(1, 11 if title == 'Knot' else 7))
    print(title + (': native reopen passed.' if reopen else ': native slicing complete.'), flush=True)


def validate(title):
    sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
    from organize_root_projects import compare
    from validate_print_project import scan_gcode
    from apply_sunlu_pla_profiles import config, locks
    proof = json.loads((REPORT / 'provenance.json').read_text())
    source = proof['projects'][title]
    folder = WORK / title
    assert digest(folder / 'before.3mf') == source['source_project_sha256']
    assert digest(folder / 'editable.3mf') == source['editable_sha256']
    assert protected() == proof['protected_before']
    original, edited, sliced = [read(folder / n) for n in ('before.3mf', 'editable.3mf', 'native/sliced.3mf')]
    oldsettings = json.loads(original['Metadata/project_settings.config'])
    s = json.loads(edited['Metadata/project_settings.config'])
    assert s == compact_settings(oldsettings, KEEP[title])
    assert json.loads(sliced['Metadata/project_settings.config']) == s
    roundtrip = compare(folder / 'editable.3mf', folder / 'native/sliced.3mf')
    assert not roundtrip['settings_changes']
    for n in original:
        if n.startswith('3D/') and not n.endswith('.rels'):
            assert original[n] == edited[n], n
    cfg = ET.fromstring(compact_model(original['Metadata/model_settings.config'], KEEP[title]))
    nc = ET.fromstring(sliced['Metadata/model_settings.config'])
    for a, b in zip(cfg.findall('plate'), nc.findall('plate')):
        assert len(a.findall('model_instance')) == len(b.findall('model_instance'))
        for md in list(a.findall('metadata')):
            a.remove(md)
        for md in b.findall('metadata'):
            a.insert(0, copy.deepcopy(md))
        for ai, bi in zip(a.findall('model_instance'), b.findall('model_instance')):
            assert props(ai)['object_id'] == props(bi)['object_id']
            for md in ai.findall('metadata'):
                if md.get('key') == 'identify_id':
                    md.set('value', props(bi)['identify_id'])
    final = dict(original)
    final['Metadata/project_settings.config'] = edited['Metadata/project_settings.config']
    final['Metadata/model_settings.config'] = ET.tostring(cfg, encoding='utf-8', xml_declaration=True)
    for n, data in sliced.items():
        if ASSET.fullmatch(n) or n in ('Metadata/slice_info.config', 'Metadata/filament_sequence.json'):
            final[n] = data
    # Original model/volume metadata is preserved exactly except slot indexes;
    # native identifiers belong only to the updated plate slice cache.
    before_cfg = ET.fromstring(compact_model(original['Metadata/model_settings.config'], KEEP[title]))
    assert [ET.tostring(o) for o in before_cfg.findall('object')] == [ET.tostring(o) for o in cfg.findall('object')]
    allowed = {'Metadata/project_settings.config', 'Metadata/model_settings.config',
               'Metadata/slice_info.config', 'Metadata/filament_sequence.json'}
    allowed |= {n for n in final if ASSET.fullmatch(n)}
    unchanged = {n: sha(v) for n, v in original.items() if n not in allowed}
    assert all(sha(final[n]) == h for n, h in unchanged.items())
    for k, value in locks(title).items():
        assert s[k] == value
    assert s['is_infill_first'] == ('1' if title == 'Knot' else '0')
    info = ET.fromstring(final['Metadata/slice_info.config'])
    sequence = json.loads(final['Metadata/filament_sequence.json'])
    count = len(KEEP[title])
    results = json.loads((folder / 'native/result.json').read_text())
    mapping = {str(i+1): str(j+1) for j, i in enumerate(KEEP[title])}
    records = []
    for i, plate in enumerate(info.findall('plate'), 1):
        assert props(plate)['index'] == str(i)
        used = {int(f.get('id')) for f in plate.findall('filament')}
        assert used == set(range(1, count+1))
        for f in plate.findall('filament'):
            j = int(f.get('id')) - 1
            assert f.get('color') == s['filament_colour'][j]
            assert f.get('tray_info_idx') == s['filament_ids'][j]
        for layer in plate.iter('layer_filament_list'):
            assert all(0 <= int(x) < count for x in layer.get('filament_list').split())
        seq = sequence['plate_' + str(i)]
        assert len(seq['optimal_assignment']) == count
        assert all(1 <= x <= count for x in seq['sequence'])
        warnings = [w.attrib for w in plate.findall('warning')]
        assert all(w['msg'] == 'not_support_traditional_timelapse' for w in warnings)
        name = f'Metadata/plate_{i}.gcode'
        raw, prior = final[name], original[name]
        assert hashlib.md5(raw).hexdigest().upper() == final[name+'.md5'].decode().strip().upper()
        a, b = config(prior), config(raw)
        changed = {k.decode() for k in a.keys() | b.keys() if a.get(k) != b.get(k)}
        assert changed <= set(source['project_setting_changes']) | {'filament_map_2'}, changed
        for k, value in locks(title).items():
            assert b[k.encode()].decode() == (value[0] if isinstance(value, list) else value)
        text = raw.decode()
        assert '; EXECUTABLE_BLOCK_END' in text
        for tool in re.findall(r'^\s*T([0-9]+)(?:\s|$)', text, re.M):
            assert int(tool) in set(range(count)) | {1000, 65535}, tool
        # Scan actual extruding moves, including arc extrema and bead widths.
        oldscan, scan = scan_gcode(prior.decode()), scan_gcode(text)
        expected_z = {mapping[k]: v for k, v in oldscan['model_extrusion_z_by_filament_mm'].items()}
        assert scan['model_extrusion_z_by_filament_mm'] == expected_z
        if title == 'Knot':
            assert expected_z['3'] == [12.8, 13.0, 13.2, 13.4, 13.6]
        assert set(scan['features']) == set(oldscan['features'])
        bounds_error = max(abs(x-y) for aa, bb in zip(scan['bead_xy_bounds_mm'], oldscan['bead_xy_bounds_mm']) for x, y in zip(aa, bb))
        assert bounds_error < .05, (title, i, bounds_error)
        low, high = scan['bead_xy_bounds_mm']
        clearance = min(*low, 330-high[0], 320-high[1])
        assert clearance > .5, (title, i, clearance)
        estimate = next(p for p in results['sliced_plates'] if p['id'] == i)
        grams = sum(f['total_used_g'] for f in estimate['filaments'])
        oldgrams = sum(map(float, re.search(rb'; total filament weight \[g\] : ([^\r\n]+)', prior)[1].split(b',')))
        assert abs(grams - oldgrams) < .2, (title, i, grams, oldgrams)
        records.append(dict(plate=i, source_gcode_sha256=sha(prior), gcode_sha256=sha(raw),
                            checksum_verified=True, gcode_configuration_changed_keys=sorted(changed),
                            model_z_by_filament_mm=expected_z, extrusion_moves_checked=scan['extrusion_moves_checked'],
                            original_extrusion_moves=oldscan['extrusion_moves_checked'],
                            bead_bounds_difference_mm=bounds_error, bed_clearance_mm=clearance,
                            warnings=warnings, seconds=estimate['total_predication'], grams=grams,
                            previous_grams=oldgrams))
        print(f'{title} plate {i}: retained settings, colors, layer heights, bounds and checksum verified.', flush=True)
    finalpath = folder / 'final.3mf'
    write(finalpath, final, folder / 'before.3mf')
    compare(folder / 'editable.3mf', finalpath)
    assert protected() == proof['protected_before']
    dump(REPORT / (title.lower() + '-validation.json'), dict(
        **source, project=title+'.3mf', project_sha256=digest(finalpath),
        all_retained_material_parameters_preserved=True, all_process_parameters_preserved=True,
        geometry_and_poses_byte_preserved=True, object_volume_overrides_preserved_except_slot_indexes=True,
        preserved_archive_entries_sha256=unchanged, native_roundtrip=roundtrip,
        plates=records, total_seconds=sum(p['seconds'] for p in records),
        total_grams=sum(p['grams'] for p in records), protected_after=protected(),
        fresh_native_slices=True, physical_status_unchanged=True, printer_job_sent=False))
    shutil.copyfile(folder / 'native/result.json', REPORT / (title.lower()+'-native.json'))
    print(title + ': final project validated.', flush=True)


def publish():
    catalogpath = ROOT / 'release/root-projects/catalog.json'
    catalog = json.loads(catalogpath.read_text())
    assert catalog == json.loads((WORK / 'sources.json').read_text())
    gpath = ROOT / 'release/root-projects/gcode-sha256.json'
    gcode = json.loads(gpath.read_text())
    proof = json.loads((REPORT / 'provenance.json').read_text())
    assert protected() == proof['protected_before']
    for title in KEEP:
        reportpath = REPORT / (title.lower()+'-validation.json')
        r = json.loads(reportpath.read_text())
        row = catalog[title]
        assert digest(ROOT / row['project']) == r['source_project_sha256']
        finalpath = WORK / title / 'final.3mf'
        assert digest(finalpath) == r['project_sha256']
        # Native save/reopen must preserve every edited project setting.
        reopened = read(WORK / title / 'reopen/reopened.3mf')
        final = read(finalpath)
        assert json.loads(reopened['Metadata/project_settings.config']) == json.loads(final['Metadata/project_settings.config'])
        sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
        from organize_root_projects import compare
        r['final_native_reopen'] = compare(finalpath, WORK / title / 'reopen/reopened.3mf')
        r['native_reopen_verified'] = True
        dump(reportpath, r)
        row.update(sha256=r['project_sha256'], filament_cleanup_validation=reportpath.relative_to(ROOT).as_posix(),
                   filament_settings_id=r['retained_profiles'])
        for obj in row['objects']:
            for settings in [obj['settings']] + [p['settings'] for p in obj['parts']]:
                if 'extruder' in settings:
                    settings['extruder'] = str(r['slot_map'][settings['extruder']])
        if title == 'Letter':
            row['filament_slot_1'] = row.pop('filament_slot_3')
        gcode[title] = {'plate_'+str(p['plate']): p['gcode_sha256'] for p in r['plates']}
        shutil.copyfile(finalpath, ROOT / row['project'])
    dump(catalogpath, catalog)
    dump(gpath, gcode)
    print('Both root projects and release catalog updated.', flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'build':
        build()
    elif sys.argv[1] == 'slice':
        native(sys.argv[2])
    elif sys.argv[1] == 'reopen':
        native(sys.argv[2], True)
    elif sys.argv[1] == 'validate':
        validate(sys.argv[2])
    elif sys.argv[1] == 'publish':
        publish()
