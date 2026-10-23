# Maintained dependency: Project is used by correct_veneer_edge_connections.py.
# Standalone audit modes target the retired production layout, not today's release.
"""Read-only checks of the saved A2L release and matching A1 accessories.

Writes fresh evidence under working/review/production-final; never reslices or
changes a production package. Run with the repository's geometry dependencies.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from shapely.geometry import MultiPoint
from development_3mf import solid, transform, props, tag
from validate_print_project import scan_gcode
from check_a2l_towers import check_tower, check_startup_tower
from check_fin_toolpaths import check_fin_bonds
import build_a2l_project as builder

OUT = ROOT / 'working/review/production-final'
A2L = ROOT / 'working/bambu/Dara-Photo-Frame-A2L'
A1 = ROOT / 'working/bambu/Dara-A1-Companion'
P = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
TARGETS = [(ROOT/'Dara.3mf', A2L/'Dara-A2L-Editable.3mf', A2L, 20, 62),
           (A1/'Dara-A1-Companion.3mf', A1/'Dara-A1-Companion-Editable.3mf', A1, 3, 44)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


class Project:
    def __init__(self, path):
        self.path = path
        self.z = zipfile.ZipFile(path)
        self.settings = json.loads(self.z.read('Metadata/project_settings.config'))
        self.cfg = ET.fromstring(self.z.read('Metadata/model_settings.config'))
        self.root = ET.fromstring(self.z.read('3D/3dmodel.model'))
        self.objects = {o.get('id'): o for o in self.root.find(tag('resources'))}
        self.configs = {o.get('id'): o for o in self.cfg.findall('object')}
        self.items = {o.get('objectid'): o for o in self.root.find(tag('build'))}
        self.assets = {}
        self.meshes = {}
        self.rows = {}
        area = np.array([[float(n) for n in p.split('x')] for p in self.settings['printable_area']])
        size = area.max(axis=0)-area.min(axis=0)
        cols = math.ceil(math.sqrt(len(self.cfg.findall('plate'))))
        for pi, plate in enumerate(self.cfg.findall('plate')):
            for inst in plate.findall('model_instance'):
                oid = props(inst)['object_id']
                T = transform(self.items[oid].get('transform'))
                T[:2, 3] -= [pi % cols*size[0]*1.2, -(pi//cols)*size[1]*1.2]
                st = props(self.configs[oid])
                parts = []
                components = {c.get('objectid'): c for c in self.objects[oid].find(tag('components'))}
                for part in self.configs[oid].findall('part'):
                    co = components[part.get('id')]
                    path = co.get(P+'path').lstrip('/')
                    if path not in self.assets:
                        self.assets[path] = ET.fromstring(self.z.read(path))
                    key = (path, part.get('id'))
                    if key not in self.meshes:
                        child = self.assets[path].find(tag('resources')).find(f"{tag('object')}[@id='{part.get('id')}']")
                        mesh = child.find(tag('mesh'))
                        v = np.array([[float(e.get(k)) for k in ('x','y','z')] for e in mesh.find(tag('vertices'))])
                        f = np.array([[int(e.get(k)) for k in ('v1','v2','v3')] for e in mesh.find(tag('triangles'))])
                        self.meshes[key] = trimesh.Trimesh(v, f, process=False)
                    m = self.meshes[key].copy()
                    m.apply_transform(transform(co.get('transform')))
                    parts.append(dict(mesh=m, subtype=part.get('subtype'), settings=props(part)))
                self.rows[st['name']] = dict(parts=parts, settings=st, T=T, plate=pi+1)


def distance(a, b):
    return float(max(cKDTree(a).query(b)[0].max(), cKDTree(b).query(a)[0].max()))


def geometry():
    projects = []
    loaded = []
    profile_root = Path.home()/'AppData/Roaming/BambuStudio/system/BBL'
    if profile_root.exists():
        builder.PROFILE = profile_root
    for path, editable, folder, plate_count, piece_count in TARGETS:
        p, src = Project(path), Project(editable)
        loaded.append(p)
        assert len(p.cfg.findall('plate')) == plate_count
        assert len(p.rows) == len(p.items) == piece_count
        assert p.rows.keys() == src.rows.keys()
        machine = builder.resolved_profile('machine', p.settings['printer_model']+' 0.4 nozzle')
        keys = ['machine_start_gcode','machine_end_gcode','change_filament_gcode',
                'layer_change_gcode','time_lapse_gcode','printable_area','printable_height',
                'bed_exclude_area','nozzle_diameter']
        assert all(p.settings[k] == machine[k] for k in keys)
        checks = []
        for name, row in p.rows.items():
            old = src.rows[name]
            assert row['plate'] == old['plate'] and len(row['parts']) == len(old['parts'])
            errors = []
            model = []
            normals = []
            for part, before in zip(row['parts'], old['parts']):
                assert part['subtype'] == before['subtype']
                m = part['mesh']
                assert m.is_volume, (name, 'non-volume mesh')
                a = m.vertices @ row['T'][:3,:3].T + row['T'][:3,3]
                b = before['mesh'].vertices @ old['T'][:3,:3].T + old['T'][:3,3]
                error = distance(a,b)
                assert error < .001, (name,error)
                errors.append(error)
                for key in ['extruder','sparse_infill_density']:
                    assert part['settings'].get(key) == before['settings'].get(key), (name,key)
                if part['subtype'] == 'normal_part':
                    model.append(a)
                    normals.append(solid(m))
            combined = normals[0]
            for body in normals[1:]:
                combined += body
            components = [b for b in combined.decompose() if b.volume() > 1e-7]
            exact_components = len(components)
            serialization_gap = 0.
            if exact_components != 1:
                assert exact_components == 2, (name,exact_components)
                serialization_gap = float(components[0].min_gap(components[1], .001))
                assert serialization_gap < .00001, (name,serialization_gap)
                # Native serialization can leave a few nanometres between
                # adjoining slicer volumes. Record the exact count and gap;
                # evaluate the contact graph at 0.00001 mm, without changing
                # geometry or claiming an exact manifold union.
            v = np.concatenate(model)
            lo, hi = v.min(axis=0), v.max(axis=0)
            bed = [330,320,325] if plate_count == 20 else [256,256,256]
            assert np.all(lo >= [.49,.49,-.001]) and np.all(hi <= np.array(bed)+.001), (name,lo,hi)
            effective = dict(p.settings, **{k:v for k,v in row['settings'].items() if k})
            assert effective['sparse_infill_density'] == ('100%' if name.startswith('V') else '8%')
            assert all(effective[k] == val for k,val in [('wall_loops','4'),('top_shell_layers','5'),('bottom_shell_layers','5')])
            checks.append(dict(name=name, plate=row['plate'], parts=len(row['parts']), connected_components=1,
                               connectivity_tolerance_mm=.00001,
                               exact_boolean_components=exact_components,serialization_gap_mm=serialization_gap,
                               component_volumes_mm3=[q.volume() for q in components],
                               bounds_mm=[lo.tolist(),hi.tolist()], editable_pose_and_mesh_error_mm=max(errors)))
        projects.append(dict(project=str(path.relative_to(ROOT)), sha256=sha(path),
                             current_machine_profile_matches=True, checked_profile_keys=keys,
                             profile_root=str(builder.PROFILE), objects=checks))
        print(path.name, 'geometry:', len(checks), 'connected objects passed', flush=True)
    mapping = json.loads((A1/'companion-plan.json').read_text())['mapping']
    accessory_checks = []
    for row in mapping:
        a = loaded[0].rows[row['source_name']]
        b = loaded[1].rows[row['name']]
        assert a['plate'] == row['A2L_plate'] and b['plate'] == row['A1_plate']
        assert len(a['parts']) == len(b['parts'])
        errors = [distance(x['mesh'].vertices, y['mesh'].vertices) for x,y in zip(a['parts'],b['parts'])]
        assert max(errors) < .00001, (row['name'],errors)
        accessory_checks.append(dict(name=row['name'], maximum_mesh_error_mm=max(errors)))
    connected = all(o['connected_components'] == 1 for p in projects for o in p['objects'])
    save('geometry.json', dict(status='PASS' if connected else 'REVIEW_CONNECTIVITY', projects=projects, matching_accessories=accessory_checks,
                               A2L_print_plates=list(range(1,18)), A1_print_plates=[1,2,3], assembly_pieces=62))


def toolpaths(first=1, last=99):
    reports = []
    carrier = json.loads((A2L/'M-geometry-validation.json').read_text())['skins']
    towers = json.loads((A2L/'tower-placement.json').read_text())['plates']
    for path, _, folder, count, _ in TARGETS:
        if first > count:
            continue
        p = Project(path)
        prior = json.loads((folder/'native-validation.json').read_text())
        rows = []
        info = ET.fromstring(p.z.read('Metadata/slice_info.config'))
        for pi in range(first,min(count,last)+1):
            raw = p.z.read(f'Metadata/plate_{pi}.gcode')
            text = raw.decode()
            r = scan_gcode(text)
            old = prior['plates'][pi-1]
            assert hashlib.sha256(raw).hexdigest() == old['gcode_sha256']
            assert np.allclose(r['bead_xy_bounds_mm'],old['bead_xy_bounds_mm'],atol=1e-8)
            bed = np.array([330,320] if count == 20 else [256,256])
            lo,hi = np.array(r['bead_xy_bounds_mm'])
            margin = float(min(*lo,*(bed-hi)))
            assert margin > .5
            maximum = max(z for zs in r['model_extrusion_z_by_filament_mm'].values() for z in zs)
            assert maximum <= (325 if count == 20 else 256)
            tools = set(r['model_extrusion_z_by_filament_mm'])
            expected = {'1','2','4'} if count == 20 and pi <= 10 else {'3'} if count == 20 and 11 <= pi <= 17 else {'1'}
            assert tools == expected, (pi, tools, expected)
            warnings = [w.attrib for w in info.findall('plate')[pi-1].findall('warning')]
            assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings), warnings
            row = dict(plate=pi,gcode_sha256=old['gcode_sha256'],extrusion_moves_checked=r['extrusion_moves_checked'],
                       bead_xy_bounds_mm=r['bead_xy_bounds_mm'],bed_margin_mm=margin,
                       maximum_model_z_mm=maximum,filament_slots=sorted(tools),warnings=warnings,
                       seconds=old['seconds'],weight_g=old['weight_g'])
            if count == 20:
                hulls = []
                for obj in p.rows.values():
                    if obj['plate'] != pi: continue
                    T = obj['T']
                    for part in obj['parts']:
                        if part['subtype'] == 'normal_part':
                            v = part['mesh'].vertices @ T[:3,:3].T + T[:3,3]
                            hulls.append(MultiPoint(v[:,:2]).convex_hull)
                row['startup_tower'] = check_startup_tower(p.settings,hulls,len(tools),maximum,pi)
                if pi <= 10:
                    row['tower'] = check_tower(text.replace('; LINE_WIDTH: ', '; WIDTH: '),hulls,towers[pi-1]['reserved_envelope_mm'])
                else:
                    assert not r['features'].get('Prime tower',0)
                if 11 <= pi <= 14:
                    assert not any(r['features'].get(k,0) for k in ['Support','Support interface'])
                if 15 <= pi <= 17:
                    row['fin_bonds'] = check_fin_bonds(text,carrier[pi-15]['carrier'])
            else:
                assert not r['features'].get('Prime tower',0)
                if pi < 3:
                    assert not any(r['features'].get(k,0) for k in ['Support','Support interface','Brim'])
            rows.append(row)
            save(f'toolpaths-progress-{first}-{last}.json',dict(status='IN_PROGRESS',completed_projects=reports,
                                                current_project=str(path.relative_to(ROOT)),plates=rows))
            print(path.name, 'plate', pi, 'passed;', round(margin,3), 'mm margin', flush=True)
        reports.append(dict(project=str(path.relative_to(ROOT)),sha256=sha(path),plates=rows))
    filename = 'toolpaths.json' if (first,last)==(1,99) else f'toolpaths-{first}-{last}.json'
    save(filename,dict(status='PASS',projects=reports,custom_machine_routines_excluded_from_bed_bounds=True))


def joint_datums():
    project = Project(ROOT/'Dara.3mf')
    plan = json.loads((A2L/'production-plan.json').read_text())
    proof = json.loads((A2L/'frame-geometry-validation.json').read_text())
    sample_dir = ROOT/'output/development/m-veneer-cosmetic-fit'
    sample = json.loads((sample_dir/'Ribbon-bed-datum-native-validation.json').read_text())
    assert sha(sample_dir/'All-Development-Tests-A1-Sliced.3mf') == sample['project_sha256']
    rows = []
    for joint, record in zip(plan['frame_joints'], proof['joints']):
        for index, sign, role in [(joint[0],1,'tongue_top'),(joint[1],-1,'socket_underside')]:
            parts = project.rows[f'F{index+1} A2L knot']['parts']
            for point in record['seating_pads_xy']:
                area = 0.
                for part in parts:
                    if part['subtype'] != 'normal_part': continue
                    mesh = part['mesh']
                    centers = mesh.triangles_center
                    selected = ((mesh.face_normals[:,2]*sign > .999)
                                & (abs(centers[:,2]-5) < 1e-6)
                                & (np.linalg.norm(centers[:,:2]-point,axis=1) < 1.5))
                    area += float(mesh.area_faces[selected].sum())
                assert area > 1, (record['joint'],role,area)
                rows.append(dict(joint=record['joint'],part=f'F{index+1}',role=role,
                                 assembly_z_mm=5,contact_area_mm2=area))
    assert len(rows) == 84
    save('production-joint-difference.json',dict(status='CONFIRMED_SAMPLE_NOT_PROPAGATED',
         production_project_sha256=sha(ROOT/'Dara.3mf'),production_contact_faces=rows,
         production_seating_z_mm=5,latest_sample_seating_z_mm=.8,
         latest_sample_revision=sample['revision'],latest_sample_project_sha256=sample['project_sha256']))
    print('Confirmed 84 Z5 production contact faces; latest sample uses Z0.8 bed datums.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['geometry','toolpaths','joint-datums'])
    parser.add_argument('--first', type=int, default=1)
    parser.add_argument('--last', type=int, default=99)
    args = parser.parse_args()
    if args.mode == 'geometry': geometry()
    elif args.mode == 'joint-datums': joint_datums()
    else: toolpaths(args.first,args.last)
