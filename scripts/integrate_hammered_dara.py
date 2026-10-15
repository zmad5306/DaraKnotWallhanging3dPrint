"""Promote the supported hammered M and bands into the normal 31-plate Dara.

Keep unaffected meshes, overrides, placements and native slices unchanged.
Re-slice the seven replacement plates in the complete four-filament project.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import prepare_hammered_bands as bands

from prepare_hammered_bands import (
    ROOT, P, R, tag, uid, props, setmeta, xml, read_zip, write_zip, sha,
    np, model_entries, scan_gcode, support_paths, cKDTree, transform,
)

WORK = ROOT / '.work/integrated-hammered-dara'
PACKAGE = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
SOURCE = ROOT / 'Dara-Hammered-Bands-Candidate.3mf'
TARGETS = [ROOT / 'Dara.3mf', PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf']
PLATES = [21, 22, 23, 24, 25, 26, 31]
PROCESS = ['bottom_shell_layers', 'bridge_speed', 'brim_object_gap', 'brim_type',
           'brim_width', 'flush_into_support', 'support_critical_regions_only',
           'support_object_xy_distance', 'support_remove_small_overhang',
           'support_style', 'support_threshold_angle', 'support_type', 'top_shell_layers']
FILAMENT = ['filament_flow_ratio', 'filament_wipe', 'filament_z_hop', 'filament_z_hop_types']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def plate_offset(number, columns):
    return np.array([((number - 1) % columns) * 307.2, -((number - 1) // columns) * 307.2])


def setting_value(value):
    if isinstance(value, list):
        assert len(value) == 1
        return value[0]
    return value


def relationship_xml(root):
    # Studio's package reader expects unprefixed Relationship elements.
    ET.register_namespace('', R)
    data = xml(root)
    ET.register_namespace('', tag('model')[1:].split('}')[0])
    return data


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    baseline = WORK / 'baseline.3mf'
    if not baseline.exists():
        assert sha(TARGETS[0]) == sha(TARGETS[1])
        shutil.copy2(TARGETS[0], baseline)
    else:
        assert sha(baseline) == sha(TARGETS[0]), 'Production has changed since staging.'
    files, candidate = read_zip(baseline), read_zip(SOURCE)
    prior = json.loads((ROOT / 'working/review/hammered-bands/full-validation.json').read_text())
    assert prior['sha256'] == sha(SOURCE)
    settings = json.loads(files['Metadata/project_settings.config'])
    cs = json.loads(candidate['Metadata/project_settings.config'])
    old_settings = copy.deepcopy(settings)
    for key in FILAMENT:
        settings[key][2] = cs[key][0]
    settings['print_settings_id'] = 'Dara complete - hammered M and copper cover bands'
    root = ET.fromstring(files['3D/3dmodel.model'])
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    rels = ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    cr = ET.fromstring(candidate['3D/3dmodel.model'])
    cc = ET.fromstring(candidate['Metadata/model_settings.config'])
    resources, build = root.find(tag('resources')), root.find(tag('build'))
    removed = {props(i)['object_id'] for p in cfg.findall('plate')
               if int(props(p)['plater_id']) in PLATES for i in p.findall('model_instance')}
    assert len(removed) == 7
    removed_paths = {c.get('{'+P+'}path').lstrip('/') for o in resources
                     if o.get('id') in removed for c in o.find(tag('components'))}
    for parent in [resources, build]:
        for child in list(parent):
            if child.get('id', child.get('objectid')) in removed:
                parent.remove(child)
    for child in list(cfg):
        if ((child.tag == 'object' and child.get('id') in removed) or
                (child.tag == 'plate' and int(props(child)['plater_id']) in PLATES)):
            cfg.remove(child)
    assemble = cfg.find('assemble')
    if assemble is not None:
        for item in list(assemble):
            if item.get('object_id') in removed:
                assemble.remove(item)
    for rel in list(rels):
        if rel.get('Target').lstrip('/') in removed_paths:
            rels.remove(rel)
    for path in removed_paths:
        del files[path]
    for path in list(files):
        match = re.match(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)(\d+)[_.]', path)
        if match and int(match[1]) in PLATES:
            del files[path]
    # Studio's cut metadata only contains unused zero cut IDs, not our CAD laps.
    cuts = ET.fromstring(files.pop('Metadata/cut_information.xml'))
    assert all(c.get('connectors_cnt') == '0' for c in cuts.iter('cut_id'))
    si = ET.fromstring(files['Metadata/slice_info.config'])
    for p in list(si):
        if int(props(p)['index']) in PLATES:
            si.remove(p)
    source_configs = {o.get('id'): o for o in cc.findall('object')}
    source_build = {i.get('objectid'): i for i in cr.find(tag('build'))}
    mapping = []; object_index = 0
    for n, target_plate in enumerate(PLATES, 1):
        p = copy.deepcopy(next(p for p in cc.findall('plate') if int(props(p)['plater_id']) == n))
        setmeta(p, 'plater_id', target_plate)
        setmeta(p, 'plater_name', f'{target_plate:02d} - '+(f'M{n} hammered with band seats' if n <= 6 else 'Copper cover bands 1-5'))
        setmeta(p, 'enable_prime_tower', '0')
        for md in list(p.findall('metadata')):
            if md.get('key', '').endswith('_file'):
                p.remove(md)
        for inst in p.findall('model_instance'):
            oid = props(inst)['object_id']; co = copy.deepcopy(source_configs[oid])
            obj = copy.deepcopy(cr.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']"))
            old_name = props(co)['name'].split(' - ')[0]
            name = old_name if old_name.startswith('M') else 'Band'+old_name[1:]
            object_index += 1; new_id = str(10000 + object_index * 100)
            comps = obj.find(tag('components')); paths = {c.get('{'+P+'}path').lstrip('/') for c in comps}
            assert len(paths) == 1
            child = ET.fromstring(candidate[next(iter(paths))])
            ids = {c.get('objectid'): str(int(new_id)+k) for k, c in enumerate(comps, 1)}
            path = f'3D/Objects/Hammered-{name}.model'
            for o in child.find(tag('resources')):
                o.set('id', ids[o.get('id')])
            for c in comps:
                c.set('objectid', ids[c.get('objectid')]); c.set('{'+P+'}path', '/'+path); c.set('{'+P+'}UUID', uid())
            for part in co.findall('part'):
                part.set('id', ids[part.get('id')])
                if part.get('subtype') == 'normal_part':
                    setmeta(part, 'extruder', 3); setmeta(part, 'name', name)
            obj.set('id', new_id); obj.set('{'+P+'}UUID', uid()); co.set('id', new_id)
            setmeta(co, 'name', name+' - '+('hammered with band seats' if n <= 6 else 'smooth copper cover'))
            setmeta(co, 'extruder', 3)
            for key in PROCESS:
                setmeta(co, key, setting_value(cs[key]))
            resources.append(obj); cfg.append(co); files[path] = xml(child)
            ET.SubElement(rels, '{'+R+'}Relationship', Target='/'+path, Id='hammered-'+new_id,
                          Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
            item = copy.deepcopy(source_build[oid]); item.set('objectid', new_id); item.set('{'+P+'}UUID', uid())
            t = transform(item.get('transform')); t[:2,3] += plate_offset(target_plate, 6)-plate_offset(n, 3)
            item.set('transform', ' '.join(f'{v:.12g}' for v in t[:3,:].T.ravel())); build.append(item)
            setmeta(inst, 'object_id', new_id)
            mapping.append(dict(name=name, source_name=old_name, source_plate=n, plate=target_plate, object_id=new_id,
                                identify_id=props(inst)['identify_id']))
        cfg.append(p)
    cfg[:] = cfg.findall('object') + sorted(cfg.findall('plate'), key=lambda p:int(props(p)['plater_id'])) + cfg.findall('assemble')
    for md in root.findall(tag('metadata')):
        if md.get('name') == 'Title': md.text = 'Dara complete - supported hammered M and copper bands'
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': relationship_xml(rels),
                  'Metadata/model_settings.config': xml(cfg), 'Metadata/slice_info.config': xml(si),
                  'Metadata/project_settings.config': json.dumps(settings, indent=2).encode()})
    sequences = json.loads(files['Metadata/filament_sequence.json'])
    for n in PLATES: sequences.pop(f'plate_{n}', None)
    files['Metadata/filament_sequence.json'] = json.dumps(sequences).encode()
    write_zip(WORK / 'staged.3mf', files)
    report = dict(baseline_sha256=sha(baseline), candidate_sha256=sha(SOURCE), mapping=mapping,
                  process_overrides={k:setting_value(cs[k]) for k in PROCESS},
                  copper_filament_changes={k:[old_settings[k][2],settings[k][2]] for k in FILAMENT},
                  unchanged_plates=[n for n in range(1,32) if n not in PLATES])
    (WORK / 'staged.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Staged complete Dara: 31 plates, 45 distinct objects, copper in slot 3.', flush=True)


def slice_plates(plates):
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    for n in plates:
        assert n in PLATES
        out = WORK / f'plate-{n}'; out.mkdir(exist_ok=True)
        print('Slicing integrated plate', n, flush=True)
        with (out/'cli.log').open('w') as log:
            result = subprocess.run([str(exe), '--slice', str(n), '--export-3mf', 'sliced.3mf',
                                     '--outputdir', str(out), str(WORK/'staged.3mf')], cwd=exe.parent,
                                    stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, (n, result.returncode)
        info = json.loads((out/'result.json').read_text())
        assert info['return_code'] == 0 and info['plate_index'] == n
        print('Integrated plate', n, 'sliced', flush=True)


def selected_entries(files, names):
    subset = dict(files); root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    ids = {o.get('id') for o in config.findall('object') if props(o)['name'].split(' - ')[0] in names}
    build = root.find(tag('build'))
    for item in list(build):
        if item.get('objectid') not in ids: build.remove(item)
    subset['3D/3dmodel.model'] = xml(root)
    return model_entries(subset)


def merge_verify():
    staged = json.loads((WORK/'staged.json').read_text())
    assert sha(WORK/'baseline.3mf') == staged['baseline_sha256']
    assert sha(SOURCE) == staged['candidate_sha256']
    original = read_zip(WORK/'baseline.3mf'); files = read_zip(WORK/'staged.3mf')
    candidate = read_zip(SOURCE)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    info = ET.fromstring(files['Metadata/slice_info.config'])
    sequences = json.loads(files['Metadata/filament_sequence.json'])
    names = {r['name'] for r in staged['mapping']}
    expected = selected_entries(files, names); reference = model_entries(candidate)
    geometry = json.loads((ROOT/'working/review/hammered-bands/geometry-validation.json').read_text())
    geometry = {r['name']:r for r in geometry['parts']}
    _, outline, joints, _ = bands.layout()
    checks = []; mesh_checks = []
    for n in PLATES:
        rows = [r for r in staged['mapping'] if r['plate'] == n]
        sliced = read_zip(WORK/f'plate-{n}/sliced.3mf')
        result = json.loads((WORK/f'plate-{n}/result.json').read_text())
        assert result['return_code'] == 0 and result['plate_index'] == n
        sliced_settings=json.loads(sliced['Metadata/project_settings.config'])
        staged_settings=json.loads(files['Metadata/project_settings.config'])
        assert all(sliced_settings[k]==v for k,v in staged_settings.items())
        # Studio adds preset bookkeeping on export; no print setting changes.
        extra={k:v for k,v in sliced_settings.items() if k not in staged_settings}
        assert extra=={'different_settings_to_system':['']*6,'inherits_group':['']*6,'filament_map_2':['1']},extra
        actual = model_entries(sliced)
        assert set(actual) == {r['name'] for r in rows}
        sc = ET.fromstring(sliced['Metadata/model_settings.config'])
        for row in rows:
            name, source_name = row['name'], row['source_name']
            a, e, ref = actual[name], expected[name], reference[source_name]
            assert len(a) == len(e) == len(ref)
            co = next(o for o in sc.findall('object') if props(o)['name'].split(' - ')[0] == name)
            assert props(co)['extruder'] == '3'
            for k,v in staged['process_overrides'].items(): assert props(co)[k] == v, (name,k)
            for pa,pe,pr in zip(a,e,ref):
                refmesh = pr['mesh'].copy()
                refmesh.apply_translation([*(plate_offset(n,6)-plate_offset(row['source_plate'],3)),0])
                error = max(cKDTree(pa['mesh'].vertices).query(pe['mesh'].vertices)[0].max(),
                            cKDTree(pe['mesh'].vertices).query(pa['mesh'].vertices)[0].max(),
                            cKDTree(refmesh.vertices).query(pe['mesh'].vertices)[0].max(),
                            cKDTree(pe['mesh'].vertices).query(refmesh.vertices)[0].max())
                assert error < .00015, (name,error)
                assert pa['config'].get('subtype') == pe['config'].get('subtype') == pr['config'].get('subtype')
                for state in [4,8]:
                    assert (pa['paint']==state).sum() == (pe['paint']==state).sum() == (pr['paint']==state).sum()
                    areas = [v['mesh'].area_faces[v['paint']==state].sum() for v in [pa,pe,pr]]
                    assert max(areas)-min(areas) < max(.002,max(areas)*2e-6)
                if pa['config'].get('subtype') == 'modifier_part':
                    assert props(pa['config'])['sparse_infill_density'] == '100%'
                mesh_checks.append(dict(name=name,subtype=pa['config'].get('subtype'),max_vertex_error_mm=float(error)))
        stats = ET.fromstring(sliced['Metadata/slice_info.config'])
        assert len(stats.findall('plate')) == 1
        stat = stats.find('plate'); assert int(props(stat)['index']) == n
        assert props(stat)['outside'] == 'false' and props(stat)['pause_count'] == '0'
        assert {f.get('id') for f in stat.findall('filament')} == {'3'}
        assert {o.get('identify_id') for o in stat.findall('object')} == {r['identify_id'] for r in rows}
        assert all(w.get('msg') == 'not_support_traditional_timelapse' for w in stat.findall('warning'))
        setmeta(stat,'printer_model_id','N2S')
        first=float(props(stat).get('first_layer_time','0'))
        if not math.isfinite(first) or not 0 <= first <= float(props(stat)['prediction']):
            stat.remove(stat.find("metadata[@key='first_layer_time']"))
        gcode=sliced[f'Metadata/plate_{n}.gcode'];text=gcode.decode()
        checksum=sliced[f'Metadata/plate_{n}.gcode.md5'].decode().strip()
        assert hashlib.md5(gcode).hexdigest().lower() == checksum.lower()
        audit=scan_gcode(text)
        assert audit['conservative_bed_edge_clearance_mm'] >= 1.5
        assert set(audit['model_extrusion_z_by_filament_mm']) == {'3'}
        zs=audit.pop('model_extrusion_z_by_filament_mm')['3'];audit['model_z_range_mm']=[min(zs),max(zs)]
        assert .1999 <= min(zs) and max(zs)<250
        for f in ['Support','Support interface']: assert audit['features'].get(f,0)>0
        if n != 31: assert audit['features'].get('Sparse infill',0)>0
        assert not audit['features'].get('Ironing',0) and not audit['features'].get('Wipe tower',0)
        assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',text,re.M)
        paths, volumes=support_paths(text);centers=paths['Support interface'].mean(axis=1);face_checks=[]
        for row in rows:
            name,source_name=row['name'],row['source_name']
            body=reference[source_name][0]['mesh'].copy();body.apply_translation([*-plate_offset(row['source_plate'],3),0])
            t=np.array(geometry[source_name]['build_transform'])
            t[:2,3] += body.bounds.mean(axis=0)[:2]-128
            near=np.all(centers>=body.bounds[0]-2,axis=1)&np.all(centers<=body.bounds[1]+2,axis=1)
            local=bands.trimesh.transform_points(centers[near],np.linalg.inv(t))
            if source_name.startswith('B'):
                j=joints[int(source_name[1:])-1]
                footprint=bands.locate(bands.rect(-6,-j[4],6,j[4]),j[2],j[3]).intersection(outline.buffer(-.15))
            else:
                body.apply_transform(np.linalg.inv(t));footprint=bands.mesh_slice(body,9)
            interior=bands.shapely.contains(footprint.buffer(-.6),bands.shapely.points(local[:,:2]))
            floor=10.5+bands.crown(outline,local[interior,:2])-.6+.15
            delta=float(np.max(local[interior,2]-floor)) if interior.any() else None
            assert (delta is not None and delta<.12) if source_name.startswith('B') else (delta is None or delta<-2), (name,delta)
            face_checks.append(dict(name=name,interior_interface_points=int(interior.sum()),max_interface_above_band_underside_mm=delta))
        p=next(p for p in cfg.findall('plate') if int(props(p)['plater_id'])==n)
        sp=next(p for p in sc.findall('plate') if int(props(p)['plater_id'])==n)
        for md in sp.findall('metadata'):
            key,path=md.get('key'),md.get('value')
            if key.endswith('_file') and path:
                setmeta(p,key,path);files[path]=sliced[path]
        for path,data in sliced.items():
            if re.match(rf'Metadata/plate_{n}(?:\.|_)',path):files[path]=data
        sequences[f'plate_{n}']=json.loads(sliced['Metadata/filament_sequence.json'])[f'plate_{n}']
        assert sequences[f'plate_{n}']['sequence']==[3]
        info.append(stat)
        audit.update(plate=n,gcode_sha256=digest(gcode),weight_g=float(props(stat)['weight']),
                     seconds=int(props(stat)['prediction']),support_face_checks=face_checks,extrusion_volumes_mm3=volumes)
        checks.append(audit);print('Verified plate',n,audit['weight_g'],'g',audit['seconds'],'s',flush=True)
    info[:]=info.findall('header')+sorted(info.findall('plate'),key=lambda p:int(props(p)['index']))
    files['Metadata/model_settings.config']=xml(cfg);files['Metadata/slice_info.config']=xml(info)
    files['Metadata/filament_sequence.json']=json.dumps(sequences).encode()
    # Preserve every unaffected object, placement and its complete native plate assets.
    oldcfg=ET.fromstring(original['Metadata/model_settings.config'])
    oldroot=ET.fromstring(original['3D/3dmodel.model']);newroot=ET.fromstring(files['3D/3dmodel.model'])
    unchanged_ids={props(i)['object_id'] for p in oldcfg.findall('plate') if int(props(p)['plater_id']) not in PLATES for i in p.findall('model_instance')}
    preserved=[]
    for oid in unchanged_ids:
        old=oldcfg.find(f"object[@id='{oid}']");new=cfg.find(f"object[@id='{oid}']")
        assert xml(old)==xml(new)
        oo=oldroot.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
        no=newroot.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
        assert xml(oo)==xml(no)
        for c in oo.find(tag('components')):
            path=c.get('{'+P+'}path').lstrip('/');assert files[path]==original[path]
        olditems=[xml(i) for i in oldroot.find(tag('build')) if i.get('objectid')==oid]
        newitems=[xml(i) for i in newroot.find(tag('build')) if i.get('objectid')==oid]
        assert olditems==newitems
    for n in staged['unchanged_plates']:
        for path,data in original.items():
            m=re.match(r'Metadata/(?:plate_|plate_no_light_|top_|pick_)(\d+)[_.]',path)
            if m and int(m[1])==n: assert files[path]==data,path
        preserved.append(dict(plate=n,gcode_sha256=digest(files[f'Metadata/plate_{n}.gcode'])))
    oldsettings=json.loads(original['Metadata/project_settings.config']);newsettings=json.loads(files['Metadata/project_settings.config'])
    for k,v in oldsettings.items():
        if k in FILAMENT: assert all(v[i]==newsettings[k][i] for i in [0,1,3])
        elif k!='print_settings_id': assert newsettings[k]==v,k
    assert len(cfg.findall('plate'))==len(info.findall('plate'))==31
    assert len(cfg.findall('object'))==45 and len(newroot.find(tag('build')))==76
    assert sum(c['subtype']=='modifier_part' for c in mesh_checks)==10
    candidate_path=WORK/'complete.3mf';write_zip(candidate_path,files)
    totals=[dict(plate=int(props(p)['index']),weight_g=float(props(p)['weight']),seconds=int(props(p)['prediction'])) for p in info.findall('plate')]
    report=dict(date='2026-10-15',project_sha256=sha(candidate_path),baseline_sha256=staged['baseline_sha256'],
                hammered_candidate_sha256=staged['candidate_sha256'],plates=31,production_pieces=75,optional_test_pieces=1,
                copper_slot=3,changed_plates=checks,unchanged_native_plates=preserved,mesh_checks=mesh_checks,
                process_overrides=staged['process_overrides'],filament_changes=staged['copper_filament_changes'],
                all_plate_estimates=totals,total_weight_g=sum(p['weight_g'] for p in totals),
                total_seconds=sum(p['seconds'] for p in totals),physical_band_fit_pending=True,
                scope='Digital integration and native slicing; physical band fit and full-size printing remain unverified.')
    (WORK/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Complete Dara verified:',report['total_weight_g'],'g,',report['total_seconds'],'seconds',flush=True)


def publish():
    report=json.loads((WORK/'validation.json').read_text());candidate=WORK/'complete.3mf'
    assert sha(candidate)==report['project_sha256']
    for target in TARGETS:
        assert sha(target) in [report['baseline_sha256'],report['project_sha256']]
    for target in TARGETS:shutil.copy2(candidate,target)
    shutil.copy2(WORK/'validation.json',PACKAGE/'hammered-integration-validation.json')
    assert sha(TARGETS[0])==sha(TARGETS[1])==report['project_sha256']
    print('Published both normal Dara project files.',flush=True)


def audit_current():
    """Check the distributed files against the committed integration evidence."""
    report=json.loads((PACKAGE/'hammered-integration-validation.json').read_text())
    assert sha(TARGETS[0])==sha(TARGETS[1])==report['project_sha256']
    files=read_zip(TARGETS[0]);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    info=ET.fromstring(files['Metadata/slice_info.config'])
    assert len(cfg.findall('plate'))==len(info.findall('plate'))==31
    records=report['changed_plates']+report['unchanged_native_plates']
    for row in records:
        n=row['plate'];data=files[f'Metadata/plate_{n}.gcode']
        assert digest(data)==row['gcode_sha256']
        assert hashlib.md5(data).hexdigest().lower()==files[f'Metadata/plate_{n}.gcode.md5'].decode().strip().lower()
    for p in cfg.findall('plate'):
        for k,v in props(p).items():
            if k.endswith('_file') and v:assert v in files,v
    ids=[]
    for path,data in files.items():
        if path.endswith('.model'):
            r=ET.fromstring(data)
            ids.extend(o.get('id') for o in r.find(tag('resources')))
            for c in r.iter(tag('component')):
                assert c.get('{'+P+'}path').lstrip('/') in files
    assert len(ids)==len(set(ids))
    print('Both normal Dara files match the audited release; all 31 saved slices and checksums verified.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('action', choices=['stage','slice','verify','publish','audit'])
    ap.add_argument('plates', nargs='*', type=int); args = ap.parse_args()
    if args.action == 'stage': stage()
    elif args.action == 'slice': slice_plates(args.plates or PLATES)
    elif args.action == 'verify': merge_verify()
    elif args.action == 'publish': publish()
    else: audit_current()
