"""Combine Bambu's sliced test plate with the unchanged 29 production plates.

Bambu CLI's --slice 30 export contains only that plate's objects. This combines
its native mesh/configuration output with the production project, remapping IDs.
Writes a candidate plus validation input in .work; does not publish the candidate.
"""
import copy
import json
import xml.etree.ElementTree as ET
import zipfile

from append_print_check_plate import PACKAGE, WORK, sha
from build_jointed_bambu_project import C, P, R, tag, xml, uid
from validate_print_project import props


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: z.read(n) for n in z.namelist()}


def main():
    source = PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf'
    original = read_zip(source)
    sliced = read_zip(WORK / 'sliced-tests.3mf')
    test = json.loads((WORK / 'test-plate.json').read_text())
    slice_result = json.loads((WORK / 'result.json').read_text())
    assert slice_result['return_code'] == 0 and slice_result['plate_index'] == 30
    assert [p['id'] for p in slice_result['sliced_plates']] == [30]
    assert test['source_project_sha256'] == sha(source)
    root = ET.fromstring(original['3D/3dmodel.model'])
    config = ET.fromstring(original['Metadata/model_settings.config'])
    rels = ET.fromstring(original['3D/_rels/3dmodel.model.rels'])
    tr = ET.fromstring(sliced['3D/3dmodel.model'])
    tc = ET.fromstring(sliced['Metadata/model_settings.config'])
    src_objects = {o.get('id'): o for o in tr.find(tag('resources'))}
    src_configs = {props(o)['name']: o for o in tc.findall('object')}
    tp = next(p for p in tc.findall('plate') if props(p)['plater_id'] == '30')
    assert len(config.findall('plate')) == 29
    assert len(src_configs) == len(test['parts']) == 9
    id_map, new_objects, new_configs = {}, [], []
    for i, entry in enumerate(test['parts']):
        co = copy.deepcopy(src_configs[entry['name']]); old_oid = co.get('id'); oid = 1000 + i * 20
        obj = copy.deepcopy(src_objects[old_oid]); id_map[old_oid] = str(oid)
        comps = obj.find(tag('components'))
        paths = {c.get('{'+P+'}path').lstrip('/') for c in comps}
        assert len(paths) == 1
        child = ET.fromstring(sliced[next(iter(paths))])
        part_ids = {c.get('objectid'): str(oid + n) for n, c in enumerate(comps, 1)}
        new_path = f'3D/Objects/{entry["name"]}-sliced.model'
        for child_obj in child.find(tag('resources')):
            child_obj.set('id', part_ids[child_obj.get('id')])
        for c in comps:
            c.set('objectid', part_ids[c.get('objectid')]); c.set('{'+P+'}path', '/'+new_path)
            c.set('{'+P+'}UUID', uid())
        for part in co.findall('part'):
            part.set('id', part_ids[part.get('id')])
        obj.set('id', str(oid)); obj.set('{'+P+'}UUID', uid()); co.set('id', str(oid))
        new_objects.append(obj); new_configs.append(co)
        original[new_path] = xml(child)
        ET.SubElement(rels, '{'+R+'}Relationship', Target='/'+new_path, Id=f'test-{oid}',
                      Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    root.find(tag('resources')).extend(new_objects)
    for item in tr.find(tag('build')):
        item = copy.deepcopy(item); item.set('objectid', id_map[item.get('objectid')]); item.set('{'+P+'}UUID', uid())
        root.find(tag('build')).append(item)
    for inst in tp.findall('model_instance'):
        for md in inst.findall('metadata'):
            if md.get('key') == 'object_id': md.set('value', id_map[md.get('value')])
    config[:] = config.findall('object') + new_configs + config.findall('plate') + [tp] + config.findall('assemble')
    for key, value in props(tp).items():
        if key.endswith('_file') and value:
            original[value] = sliced[value]
    # Include the slicer's path bounds and checksums for the new plate too.
    for name, data in sliced.items():
        if name.startswith('Metadata/plate_30.') or name.startswith('Metadata/plate_30_'):
            original[name] = data
    si = ET.fromstring(original['Metadata/slice_info.config'])
    tsi = ET.fromstring(sliced['Metadata/slice_info.config'])
    assert len(tsi.findall('plate')) == 1
    si.append(tsi.find('plate'))
    original['Metadata/slice_info.config'] = xml(si)
    for md in root.findall(tag('metadata')):
        if md.get('name') == 'Description': md.text = '29 production plates plus plate 30 fit tests; four walls, 15% gyroid and local solid screw zones.'
    original['3D/3dmodel.model'] = xml(root)
    original['Metadata/model_settings.config'] = xml(config)
    ET.register_namespace('', R)
    original['3D/_rels/3dmodel.model.rels'] = xml(rels)
    ET.register_namespace('', C)
    candidate = WORK / 'complete-with-tests.3mf'
    with zipfile.ZipFile(candidate, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in original.items(): z.writestr(name, data)
    with zipfile.ZipFile(source) as before, zipfile.ZipFile(candidate) as after:
        for i in range(1, 30):
            path = f'Metadata/plate_{i}.gcode'
            assert before.read(path) == after.read(path)
        assert before.read('Metadata/project_settings.config') == after.read('Metadata/project_settings.config')
    test['sliced'] = True
    test['production_gcodes_byte_identical'] = True
    test['slicer_warnings'] = [p['warning_message'] for p in slice_result['sliced_plates'] if p.get('warning_message')]
    base = json.loads((PACKAGE / 'project-validation.json').read_text())
    base.update(project_sha256=sha(candidate), plates=30, pieces=79, production_plates=29,
                production_pieces=70, test_pieces=9, test_plate=test)
    base['plate_layout'].append(test['plate_layout'])
    # The legacy round-trip record describes the preserved production objects.
    base['bambu_studio_round_trip']['scope'] = 'Production plates 1-29; see final-review.json for all 30 plates.'
    (WORK / 'candidate-validation.json').write_text(json.dumps(base, indent=2) + '\n')
    print(str(candidate))


if __name__ == '__main__':
    main()
