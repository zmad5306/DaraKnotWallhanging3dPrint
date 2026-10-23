"""Apply Hilbert only to Knot's white show face; preserve blue/brown and joints."""
import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
from organize_root_projects import rows, compare, dump, sha, ASSET, clean_relations
from development_3mf import props
from promote_veneer_wall_cradle import read, write, setmeta, EXE

WORK = ROOT / '.work/knot-white-hilbert-r1'
REPORT = ROOT / 'release/knot-white-hilbert-r1'
BASE = WORK / 'Knot-before.3mf'
EDIT = WORK / 'Knot-editable.3mf'
FINAL = WORK / 'Knot-final.3mf'
NATIVE = WORK / 'native'
SOURCE_SHA = '8a76b70a1c1430d74a16ec06c9689827d33f3902afb1d7de90e4436072c251c3'
RANGES = 'Metadata/layer_config_ranges.xml'


def protected():
    paths = [p for p in ROOT.glob('*.3mf') if p.name != 'Knot.3mf']
    paths += list(ROOT.glob('Knot STL/*.stl')) + [ROOT / 'Knot.scad']
    paths += [ROOT / 'release/samples/Dara-A2L-Hammered-Finish-ERYONE-r4.3mf']
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}


def build():
    assert sha(ROOT / 'Knot.3mf') == SOURCE_SHA
    WORK.mkdir(parents=True, exist_ok=True); REPORT.mkdir(parents=True, exist_ok=True)
    if not BASE.exists():
        shutil.copyfile(ROOT / 'Knot.3mf', BASE)
        for name in ['AGENTS.md', 'release/root-projects/catalog.json',
                     'release/root-projects/gcode-sha256.json', 'release/root-projects/README.md']:
            path = WORK / 'initial' / name; path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
    files = read(BASE); assert RANGES not in files
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    changes = []
    for obj in cfg.findall('object'):
        blue = [p for p in obj.findall('part') if props(p).get('extruder') == '4']
        assert len(blue) == 1 and 'top_surface_pattern' not in props(blue[0])
        setmeta(blue[0], 'top_surface_pattern', 'monotonicline')
        changes.append(dict(object=props(obj)['name'], blue_volume_id=blue[0].get('id'),
            blue_pattern=['monotonicline inherited', 'monotonicline explicit']))
    ranges = ET.Element('objects')
    for i in range(1, 11):
        obj = ET.SubElement(ranges, 'object', id=str(i))
        interval = ET.SubElement(obj, 'range', min_z='13.0', max_z='13.6')
        # Native height ranges carry these GUI defaults. They preserve the
        # existing height and inherit each volume's filament assignment.
        ET.SubElement(interval, 'option', opt_key='layer_height').text = '0.2'
        ET.SubElement(interval, 'option', opt_key='extruder').text = '0'
        ET.SubElement(interval, 'option', opt_key='top_surface_pattern').text = 'hilbertcurve'
    files[RANGES] = ET.tostring(ranges, encoding='utf-8', xml_declaration=True)
    for name in list(files):
        if ASSET.fullmatch(name) or name in ['Metadata/slice_info.config', 'Metadata/filament_sequence.json']:
            del files[name]
    for plate in cfg.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key', '').endswith('_file'): plate.remove(md)
    files['Metadata/model_settings.config'] = ET.tostring(cfg, encoding='utf-8', xml_declaration=True)
    clean_relations(files); write(EDIT, files)
    dump(REPORT / 'provenance.json', dict(source='Knot.3mf', source_sha256=SOURCE_SHA,
        editable_sha256=sha(EDIT), protected_before=protected(),
        show_face_pattern=['monotonicline', 'hilbertcurve'], height_range_mm=[13, 13.6],
        blue_overrides=changes, unchanged_top_line_width_mm=.42,
        brown_settings_unchanged=True, geometry_changes=False,
        source_documentation='https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp'))
    print('Built show-face-only Hilbert; blue explicitly monotonic; brown and joints unchanged.', flush=True)


def native(info=False):
    folder = WORK / 'reopen' if info else NATIVE; folder.mkdir(parents=True, exist_ok=True)
    args = ['--info'] if info else ['--slice', '0', '--export-3mf', 'sliced.3mf']
    for attempt in range(3):
        with (folder / 'run.log').open('w') as log:
            result = subprocess.run([str(EXE), *args, '--outputdir', str(folder), str(FINAL if info else EDIT)],
                cwd=EXE.parent, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode != 3221225477: break
    result.check_returncode()
    data = json.loads((folder / 'result.json').read_text()); assert data['return_code'] == 0
    if not info: assert [p['id'] for p in data['sliced_plates']] == list(range(1, 11))
    print('Native reopen passed.' if info else 'Ten native plates sliced.', flush=True)


def path_signature(paths, predicate):
    """Compare extruded centerlines independent of travel order and reversal."""
    selected = []
    for slot, feature, ends in paths:
        if predicate(slot, feature, ends):
            a, b = [tuple(round(v, 3) for v in p) for p in ends]
            selected.append((slot, feature, *min(a, b), *max(a, b)))
    selected.sort()
    return dict(segments=len(selected), sha256=hashlib.sha256(repr(selected).encode()).hexdigest())


def directions(paths):
    a = np.asarray([p[2] for p in paths if p[0] == 1 and p[1] == 'Top surface' and abs(p[2][1][2]-13.6)<.001])
    d = a[:, 1, :2] - a[:, 0, :2]; lengths = np.linalg.norm(d, axis=1)
    theta = np.arctan2(d[:, 1], d[:, 0]); total = float(lengths.sum())
    # Short Hilbert strokes magnify 0.001 mm G-code coordinate rounding.
    # Fit perpendicular axes circularly instead of splitting one direction at
    # an arbitrary histogram bin edge; allow one degree of rounding error.
    axis = float((np.angle(np.sum(lengths*np.exp(4j*theta)))/4) % (np.pi/2))
    angles = np.degrees(theta) % 180; base = np.degrees(axis)
    distances = [np.abs((angles-base-offset+90)%180-90) for offset in [0,90]]
    fractions = [float(lengths[d<1].sum()/total) for d in distances]
    return dict(top_two_angles_deg=[float(base),float(base+90)],
                top_two_length_fractions=fractions, total_length_mm=total,
                segments=len(a))


def range_config(files):
    root = ET.fromstring(files[RANGES]); result = []
    for obj in root.findall('object'):
        rr = obj.findall('range'); assert len(rr) == 1
        r = rr[0]
        result.append((obj.get('id'), float(r.get('min_z')), float(r.get('max_z')),
                       {v.get('opt_key'): v.text for v in r.findall('option')}))
    assert len(result) == 10
    for _, low, high, values in result:
        assert (low, high) == (13., 13.6)
        assert values == dict(extruder='0', layer_height='0.2', top_surface_pattern='hilbertcurve')
    return result


def validate():
    from validate_ribbon_bed_datum import segments
    from validate_print_project import scan_gcode
    from check_a2l_towers import check_startup_tower, check_tower
    from mesh_sections import mesh_slice
    import shapely
    from shapely.geometry import MultiPoint
    assert sha(BASE) == SOURCE_SHA
    proof = json.loads((REPORT / 'provenance.json').read_text())
    assert sha(EDIT) == proof['editable_sha256'] and protected() == proof['protected_before']
    old, edited, sliced = read(BASE), read(EDIT), read(NATIVE / 'sliced.3mf')
    settings, objects = rows(EDIT)
    assert old['Metadata/project_settings.config'] == edited['Metadata/project_settings.config']
    assert all(edited[n] == data for n, data in old.items() if n.endswith('.model'))
    a, b = [ET.fromstring(f['Metadata/model_settings.config']) for f in [old, edited]]
    for x, y in zip(a.findall('object'), b.findall('object')):
        expected = copy.deepcopy(x)
        for part in expected.findall('part'):
            if props(part).get('extruder') == '4': setmeta(part, 'top_surface_pattern', 'monotonicline')
        assert ET.tostring(expected) == ET.tostring(y)
    assert range_config(edited) == range_config(sliced)
    roundtrip = compare(EDIT, NATIVE / 'sliced.3mf')
    assert not roundtrip['settings_changes']
    locks = dict(sparse_infill_density='8%', sparse_infill_pattern='gyroid', layer_height='0.2',
        initial_layer_print_height='0.2', wall_loops='4', top_shell_layers='5', bottom_shell_layers='5',
        curr_bed_type='Textured PEI Plate', is_infill_first='1', support_top_z_distance='0.2',
        top_surface_line_width='0.42', top_surface_pattern='monotonicline')
    for k,v in locks.items(): assert settings[k] == v
    assert settings['printer_model'] == 'Bambu Lab A2L' and settings['nozzle_diameter'] == ['0.4']
    results = json.loads((NATIVE / 'result.json').read_text())
    info = ET.fromstring(sliced['Metadata/slice_info.config'])
    records = []
    for obj in objects:
        n = obj['plate']; name = f'Metadata/plate_{n}.gcode'
        raw = sliced[name]; text = raw.decode(); oldtext = old[name].decode()
        assert hashlib.md5(raw).hexdigest().upper() == sliced[name+'.md5'].decode().strip().upper()
        gc = dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$', text, re.M))
        for k,v in locks.items(): assert gc[k] == v, (n,k,gc[k])
        assert gc['nozzle_diameter'] == '0.4' and '; EXECUTABLE_BLOCK_END' in text
        ps = segments(text, {1:'knot'}, single_object=True)['knot']
        prior = segments(oldtext, {1:'knot'}, single_object=True)['knot']
        preserve = {}
        for label, select in [
            ('brown_all_model_extrusions', lambda s,f,p:s==2),
            ('blue_all_model_extrusions', lambda s,f,p:s==4),
            ('white_joints_and_all_extrusions_below_show_face', lambda s,f,p:s==1 and p[1][2]<13.59),
            ('white_above_show_face', lambda s,f,p:s==1 and p[1][2]>13.61),
            ('white_show_face_walls', lambda s,f,p:s==1 and abs(p[1][2]-13.6)<.001 and f in ['Outer wall','Inner wall'])]:
            oldsig, sig = path_signature(prior, select), path_signature(ps, select)
            assert oldsig == sig, (n,label,oldsig,sig)
            preserve[label] = sig
        angles = directions(ps); oldangles = directions(prior)
        assert min(angles['top_two_length_fractions'])>.2 and sum(angles['top_two_length_fractions'])>.9, angles
        assert abs(abs(angles['top_two_angles_deg'][0]-angles['top_two_angles_deg'][1])-90)<1, angles
        # White centerlines must not enter the unchanged blue material region.
        t = obj['transform']; blue = next(p['mesh'].copy() for p in obj['parts'] if p['settings'].get('extruder')=='4')
        blue.apply_transform(t); blue_shape = mesh_slice(blue, 13.3)
        lines = np.array([p[2] for p in ps if p[0]==1 and abs(p[2][1][2]-13.6)<.001])[:, :, :2]
        line_shapes = shapely.linestrings(lines)
        intrusion = float(shapely.length(shapely.intersection(line_shapes, blue_shape.buffer(-.03))).sum())
        assert intrusion < .01, (n, intrusion)
        scan, oldscan = scan_gcode(text), scan_gcode(oldtext)
        assert scan['model_extrusion_z_by_filament_mm'] == oldscan['model_extrusion_z_by_filament_mm']
        low, high = np.array(scan['bead_xy_bounds_mm']); bed = float(min(*low, *(np.array([330,320])-high)))
        assert bed>.5
        hulls = [MultiPoint((p['mesh'].vertices @ t[:3,:3].T+t[:3,3])[:,:2]).convex_hull for p in obj['parts'] if p['subtype']=='normal_part']
        top = max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values())
        tower = check_tower(text,hulls,[0,0,330,320]); tower.pop('actual_tower_convex_envelope')
        startup = check_startup_tower(settings,hulls,3,top,n)
        pi = next(p for p in info.findall('plate') if props(p)['index']==str(n))
        warnings = [w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings)
        estimate = next(p for p in results['sliced_plates'] if p['id']==n)
        records.append(dict(plate=n, gcode_sha256=hashlib.sha256(raw).hexdigest(), gcode_md5_verified=True,
            unchanged_extrusion_signatures=preserve, white_top_directions=angles, previous_white_top_directions=oldangles,
            white_centerline_length_inside_blue_mm=intrusion, bed_clearance_mm=bed,
            model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'], tower=tower, startup_tower=startup,
            warnings=warnings, seconds=estimate['total_predication'], grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        if n==3: preview(prior,ps)
        dump(WORK / 'progress.json', records)
        print(f'Plate {n}: white Hilbert verified; blue, brown, joints and boundaries preserved.',flush=True)
    # Transplant fresh native plate assets, retaining exact original geometry.
    final = dict(old); final[RANGES] = edited[RANGES]
    config = ET.fromstring(edited['Metadata/model_settings.config'])
    native_config = ET.fromstring(sliced['Metadata/model_settings.config'])
    for x,y in zip(config.findall('plate'), native_config.findall('plate')):
        for md in list(x.findall('metadata')): x.remove(md)
        for md in y.findall('metadata'): x.insert(0,copy.deepcopy(md))
        for md in x.find('model_instance').findall('metadata'):
            if md.get('key')=='identify_id': md.set('value',props(y.find('model_instance'))['identify_id'])
    final['Metadata/model_settings.config'] = ET.tostring(config,encoding='utf-8',xml_declaration=True)
    for name,data in sliced.items():
        if ASSET.fullmatch(name) or name in ['Metadata/slice_info.config','Metadata/filament_sequence.json']: final[name]=data
    write(FINAL,final); compare(EDIT,FINAL); range_config(final); native(info=True)
    assert protected()==proof['protected_before']
    report = dict(project='Knot.3mf',project_sha256=sha(FINAL),source_sha256=SOURCE_SHA,
        editable_sha256=sha(EDIT),native_project_sha256=sha(NATIVE/'sliced.3mf'),
        all_mesh_assets_and_poses_unchanged=True, all_cad_stl_unchanged=True,
        white_show_face_pattern='hilbertcurve', height_range_mm=[13,13.6], top_line_width_mm=.42,
        brown_blue_joint_and_pin_toolpath_geometry_preserved=True,
        screw_modifiers_preserved_at_z12_4=True, modifier_count=50,
        previous_reinforcement_validation='release/knot-reinforcement-skin-r1/validation.json',
        plates=records,total_seconds=sum(p['seconds'] for p in records),total_grams=sum(p['grams'] for p in records),
        native_roundtrip=roundtrip,native_reopen=json.loads((WORK/'reopen/result.json').read_text()),
        protected_after=protected(),physical_finish_confirmation_pending=True,printer_job_sent=False)
    dump(REPORT/'validation.json',report)
    shutil.copyfile(NATIVE/'result.json',REPORT/'native-result.json')
    print('All ten plates validated and final project reopened.',flush=True)


def preview(before,after):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    site=json.loads((ROOT/'release/knot-reinforcement-skin-r1/validation.json').read_text())['plates'][2]['shell_continuity'][0]['center_bed_xy_mm']
    fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    for ax,ps,title in zip(axes,[before,after],['Current straight white finish','Hilbert white; original blue trim']):
        for slot,color in [(1,'#555555'),(4,'#1779ab')]:
            a=np.asarray([p[2] for p in ps if p[0]==slot and abs(p[2][1][2]-13.6)<.001])
            ax.add_collection(LineCollection(a[:,:,:2],colors=color,linewidths=.65))
        ax.set(xlim=(site[0]-9,site[0]+12),ylim=(site[1]-10,site[1]+10),aspect='equal',title=title,xlabel='Bed X (mm)',ylabel='Bed Y (mm)')
    fig.suptitle('Knot plate 3: actual native extrusion paths at Z13.6 mm')
    fig.savefig(REPORT/'white-blue-before-after.png',dpi=180);plt.close(fig)


def publish():
    report=json.loads((REPORT/'validation.json').read_text())
    assert sha(FINAL)==report['project_sha256'] and sha(ROOT/'Knot.3mf')==SOURCE_SHA
    assert protected()==report['protected_after']
    path=ROOT/'release/root-projects/catalog.json';catalog=json.loads(path.read_text());entry=catalog['Knot']
    _,objects=rows(FINAL)
    for row,obj in zip(entry['objects'],objects):
        assert row['name']==obj['name']
        for saved,part in zip(row['parts'],obj['parts']): saved['settings']=part['settings']
    shutil.copyfile(FINAL,ROOT/'Knot.3mf');entry['sha256']=sha(ROOT/'Knot.3mf')
    entry['validation']='release/knot-white-hilbert-r1/validation.json'
    entry['height_ranges']=[dict(min_z=13,max_z=13.6,layer_height=.2,extruder=0,top_surface_pattern='hilbertcurve')]
    dump(path,catalog)
    path=ROOT/'release/root-projects/gcode-sha256.json';hashes=json.loads(path.read_text())
    hashes['Knot']={f"plate_{p['plate']}":p['gcode_sha256'] for p in report['plates']};dump(path,hashes)
    shutil.copyfile(REPORT/'native-result.json',ROOT/'release/root-projects/Knot-native.json')
    assert protected()==report['protected_after']
    print('Published white-only Hilbert. CAD/STL geometry is unchanged.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['build', 'slice', 'reopen','validate','publish'])
    args = parser.parse_args()
    if args.action == 'build': build()
    elif args.action in ['slice','reopen']: native(args.action == 'reopen')
    else: globals()[args.action]()
