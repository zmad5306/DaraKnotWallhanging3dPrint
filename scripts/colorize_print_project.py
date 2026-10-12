"""Stage the white/wood/copper AMS project without changing the source geometry.

Run against the saved, single-material project, then slice the staged output in
Bambu Studio. Re-running on a colorized file is deliberately rejected. Visible
weave is identified by the CAD's two horizontal surface levels. A filament
modifier colors the 0.6 mm backing skin and raised threads. Printable vertex
and triangle data stay unchanged; Bambu intersects the modifier at slicing.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from build_jointed_bambu_project import ROOT, P, tag, mesh_object, xml, meta, uid
from validate_print_project import props, transform
import numpy as np
import trimesh
import manifold3d
from shapely.geometry import Polygon, box
from shapely import union_all

PACKAGE = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
COLORS = ['#FFFFFF', '#C2AB84', '#B87333']
WOOD_BOTTOM = 8.4
WOOD_TOP = 9.6


def setmeta(el, key, value):
    for m in el.findall('metadata'):
        if m.get('key') == key:
            m.set('value', str(value))
            return
    meta(el, key, value)


def read_mesh(obj):
    vs = [[float(v.get(k)) for k in ('x', 'y', 'z')] for v in obj.findall(f'{tag("mesh")}/{tag("vertices")}/{tag("vertex")}')]
    fs = [[int(f.get(k)) for k in ('v1', 'v2', 'v3')] for f in obj.findall(f'{tag("mesh")}/{tag("triangles")}/{tag("triangle")}')]
    return trimesh.Trimesh(vs, fs, process=False)


def projection(mesh):
    triangles = mesh.triangles[np.abs(mesh.face_normals[:, 2]) > .001]
    return union_all([Polygon(t[:, :2]) for t in triangles]).buffer(0)


def weave_modifier(mesh):
    heights = mesh.triangles[:, :, 2]
    top = (mesh.face_normals[:, 2] > .99) & (
        np.all(np.abs(heights - 9.0) < 1e-4, axis=1) |
        np.all(np.abs(heights - 9.6) < 1e-4, axis=1))
    if not top.any():
        return None
    footprint = union_all([Polygon(t[:, :2]) for t in mesh.triangles[top]]).buffer(0).simplify(1e-5, preserve_topology=True)
    polygons = [footprint] if footprint.geom_type == 'Polygon' else list(footprint.geoms)
    contours = []
    from shapely.geometry.polygon import orient
    for p in polygons:
        p = orient(p, sign=1)
        contours.append(np.asarray(p.exterior.coords)[:-1])
        contours.extend(np.asarray(r.coords)[:-1] for r in p.interiors)
    solid = manifold3d.CrossSection(contours).extrude(WOOD_TOP - WOOD_BOTTOM + 1e-6).translate([0, 0, WOOD_BOTTOM])
    raw = solid.to_mesh64()
    mask = trimesh.Trimesh(raw.vert_properties[:, :3], raw.tri_verts, process=False)
    assert mask.is_volume
    return mask, {'modifier_volume_mm3': mask.volume, 'footprint_area_mm2': footprint.area,
                  'printable_mesh_unchanged': True}


def resolved_profile(folder, name):
    paths = list(folder.rglob(name + '.json'))
    assert len(paths) == 1, (name, paths)
    leaf = json.loads(paths[0].read_text())
    data = resolved_profile(folder, leaf['inherits']) if leaf.get('inherits') else {}
    data.update(leaf)
    return data


def filament_settings(settings, profiles):
    pla = resolved_profile(profiles, 'Generic PLA @BBL A1')
    silk = resolved_profile(profiles, 'Generic PLA Silk @BBL A1')
    for key in set(pla) | set(silk) | {k for k in settings if k.startswith('filament_')}:
        value = settings.get(key)
        if isinstance(value, list) and len(value) == 1:
            third = silk.get(key, value)
            settings[key] = value * 2 + [third[0] if isinstance(third, list) else value[0]]
    settings.update(filament_colour=COLORS, filament_multi_colour=COLORS,
                    filament_settings_id=['Generic PLA @BBL A1', 'Generic PLA @BBL A1', 'Generic PLA Silk @BBL A1'],
                    filament_ids=['GFL99', 'GFL99', 'GFL96'],
                    filament_self_index=['1', '2', '3'],
                    inherits_group=[''] * 5,
                    filament_map=['1', '1', '1'], filament_map_2=['1', '1', '1'],
                    filament_volume_map=['0', '0', '0'],
                    nozzle_temperature=['220', '220', '220'],
                    nozzle_temperature_initial_layer=['220', '220', '220'],
                    hot_plate_temp=['60'] * 3, hot_plate_temp_initial_layer=['60'] * 3,
                    textured_plate_temp=['60'] * 3, textured_plate_temp_initial_layer=['60'] * 3,
                    enable_prime_tower='1', prime_tower_width='35', prime_tower_brim_width='3',
                    flush_into_infill='0', flush_into_support='0', flush_into_objects='0',
                    flush_volumes_matrix=['0', '280', '280', '420', '0', '280', '600', '420', '0'],
                    flush_volumes_vector=['140'] * 6,
                    print_settings_id='Dara AMS - white frame - wood weave - copper M')
    # Purge volumes are conservative starting values in mm3, row=from/column=to.
    # Do not hide residual dark color in the thin white walls or support contact.


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf')
    ap.add_argument('--output', type=Path, default=ROOT / '.work/ams-colors/colored.3mf')
    ap.add_argument('--profiles', type=Path, default=Path('C:/Program Files/Bambu Studio/resources/profiles/BBL/filament'))
    args = ap.parse_args()
    with zipfile.ZipFile(args.source) as z:
        files = {n: z.read(n) for n in z.namelist()}
    settings = json.loads(files['Metadata/project_settings.config'])
    assert len(settings['filament_colour']) == 1, 'Use the single-material baseline, not an already colorized file.'
    filament_settings(settings, args.profiles)
    config = ET.fromstring(files['Metadata/model_settings.config'])
    root = ET.fromstring(files['3D/3dmodel.model'])
    objects = {o.get('id'): o for o in root.find(tag('resources'))}
    children = {n: ET.fromstring(data) for n, data in files.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
    next_id = max(int(o.get('id')) for r in [root, *children.values()] for o in r.find(tag('resources'))) + 1
    report = {'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'palette': [{'slot': i + 1, 'color': color, 'material': material} for i, (color, material) in enumerate(zip(COLORS, ['Generic PLA', 'Generic PLA', 'Generic PLA Silk']))],
              'wood_z_mm': [WOOD_BOTTOM, WOOD_TOP], 'parts': [], 'towers': []}
    footprints = {}
    for obj in config.findall('object'):
        name = props(obj)['name']
        components = objects[obj.get('id')].find(tag('components'))
        parts = obj.findall("part[@subtype='normal_part']")
        assert len(parts) == 1
        part = parts[0]
        comp = next(c for c in components if c.get('objectid') == part.get('id'))
        child = children[comp.get('{' + P + '}path').lstrip('/')]
        res = child.find(tag('resources'))
        mo = next(o for o in res if o.get('id') == part.get('id'))
        mesh = read_mesh(mo)
        matrix = transform(comp.get('transform'))
        mesh.apply_transform(matrix)
        footprints[obj.get('id')] = projection(mesh)
        is_copper = name.startswith('M') or name == 'Test-M-Letter'
        slot = 3 if is_copper else 1
        setmeta(obj, 'extruder', slot)
        setmeta(part, 'extruder', slot)
        if is_copper:
            setmeta(obj, 'outer_wall_speed', 40)
            setmeta(obj, 'top_surface_speed', 40)
        modifier = weave_modifier(mesh) if name.startswith('F') else None
        if modifier:
            wood, evidence = modifier
            wood.apply_transform(np.linalg.inv(matrix))
            mesh_object(res, next_id, wood)
            new_comp = copy.deepcopy(comp)
            new_comp.set('objectid', str(next_id))
            new_comp.set('{' + P + '}UUID', uid())
            components.append(new_comp)
            new_part = ET.SubElement(obj, 'part', id=str(next_id), subtype='modifier_part', uuid=uid())
            meta(new_part, 'name', name + ' - Wood weave and backing skin')
            meta(new_part, 'extruder', 2)
            ET.SubElement(new_part, 'mesh_stat', face_count=str(len(wood.faces)), edges_fixed='0',
                          degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
            next_id += 1
            report['parts'].append({'name': name, **evidence})
            print(f'{name}: wood modifier; original geometry preserved', flush=True)
    # Find conservative free rectangles for towers in the existing plate layout.
    from shapely.affinity import translate
    tower_x, tower_y = [], []
    for pi, plate in enumerate(config.findall('plate')):
        used = []
        for inst in plate.findall('model_instance'):
            oid = props(inst)['object_id']
            # Retainer has many instances; obtain the exact instance transform.
            instances = [b for b in root.find(tag('build')) if b.get('objectid') == oid]
            b = instances[int(props(inst)['instance_id'])]
            t = transform(b.get('transform'))[:3, 3] - [pi % 6 * 307.2, -(pi // 6) * 307.2, 0]
            used.append(translate(footprints[oid], t[0], t[1]))
        # Bambu's collision check uses each object's convex hull. Stay outside
        # it, including a 7 mm clearance, even when the actual part is concave.
        occupied = union_all([shape.convex_hull for shape in used]).buffer(7)
        # Measured ribbed tower+brim footprint is x/y -3.3 .. +27.8 for this
        # profile. Reserve -4 .. +34, and avoid Bambu's <15 mm X clamp.
        # Re-slicing and checking actual bounds remains required after changes.
        candidates = [(x, y) for y in range(214, 14, -4) for x in range(15, 215, 4)]
        at = next(((x, y) for x, y in candidates if not box(x - 4, y - 4, x + 34, y + 34).intersects(occupied)), None)
        multi = pi < 20 and any(p['name'] == f'F{pi + 1}' for p in report['parts']) or pi == 29
        assert at is not None or not multi, f'No prime tower room on plate {pi + 1}'
        at = at or (15, 190)
        tower_x.append(str(at[0])); tower_y.append(str(at[1]))
        report['towers'].append({'plate': pi + 1, 'xy': at, 'needed': multi})
        for m in list(plate.findall('metadata')):
            if m.get('key', '').endswith('_file'):
                plate.remove(m)
        setmeta(plate, 'filament_maps', '1 1 1')
        setmeta(plate, 'filament_volume_maps', '0 0 0')
    settings['wipe_tower_x'] = tower_x
    settings['wipe_tower_y'] = tower_y
    files['3D/3dmodel.model'] = xml(root)
    files['Metadata/model_settings.config'] = xml(config)
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    for n, r in children.items():
        files[n] = xml(r)
    # Remove stale single-color toolpaths, slice statistics and preview images.
    files = {n: d for n, d in files.items() if not (n.startswith('Metadata/') and
             (n.endswith(('.gcode', '.png', '.md5')) or 'slice_info' in n))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, d in files.items():
            z.writestr(n, d)
    report['output_sha256'] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Staged {args.output}', flush=True)


if __name__ == '__main__':
    main()
