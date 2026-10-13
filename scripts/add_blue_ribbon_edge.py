"""Add flush Azurite edging to the existing white/wood/copper project.

Derive the line from the continuous CAD artwork BEFORE part clipping, so no
accent follows manufacturing seams. Source meshes and placements stay intact.
Stage, slice in Bambu Studio, then validate before publishing the candidate.
"""
import argparse
import ast
import copy
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from build_jointed_bambu_project import ROOT, P, tag, xml, mesh_object, uid, read_array
from add_weave_test_coupon import read_zip, write_zip, NAME
from colorize_print_project import setmeta, read_mesh
from validate_print_project import digest, transform
import numpy as np
import trimesh
import manifold3d
from shapely import affinity, union_all
from shapely.geometry import Polygon, mapping
from shapely.geometry.polygon import orient

WORK = ROOT / '.work/blue-ribbon-edge'
REVIEW = ROOT / 'working/review/blue-ribbon-edge'
CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'
WIDTH = 1.5
GAP = 1.25  # white land between the blue thread and the actual weave footprint
BOTTOM, TOP = 12.9, 13.5
COLOR = '#295D8A'


def artwork(text, name):
    body = text.split('module ' + name + '() {', 1)[1].split('\n}', 1)[0]
    polys = []
    for points, paths in re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity', body, re.S):
        pts, rings = ast.literal_eval(points), ast.literal_eval(paths)
        polys.append(Polygon([pts[j] for j in rings[0]], [[pts[j] for j in r] for r in rings[1:]]))
    assert polys
    return affinity.scale(union_all(polys), .75, .75, origin=(0, 0))


def polygons(shape):
    if shape.geom_type == 'Polygon':
        return [shape]
    return [p for p in shape.geoms if p.geom_type == 'Polygon' and p.area > 1e-7]


def section(shape):
    rings = []
    for poly in polygons(shape):
        poly = orient(poly, 1)
        rings.append(np.array(poly.exterior.coords)[:-1])
        rings.extend(np.array(r.coords)[:-1] for r in poly.interiors)
    return manifold3d.CrossSection(rings)


def as_mesh(solid):
    raw = solid.to_mesh64()
    mesh = trimesh.Trimesh(raw.vert_properties, raw.tri_verts, process=True)
    assert mesh.is_volume
    return mesh


def in_print_coordinates(shape, placement):
    return affinity.translate(affinity.rotate(shape, placement[0], origin=(0, 0)),
                              -placement[1][0], -placement[1][1])


def coupon_shape(shape, cad):
    """Exactly replay the existing F7 coupon's assembly-to-crop transform."""
    j = read_array(cad, 'frame_joints')[0]
    p = read_array(cad, 'frame_placements')[6]
    mesh = trimesh.load_mesh(ROOT / 'working/stl/Dara-Photo-Frame-A1-Jointed/F7.stl')
    mesh.apply_translation([*p[1], -p[3]])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-p[0]), [0, 0, 1]))
    mesh.apply_translation([-j[2][0], -j[2][1], 0])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-j[3]), [0, 0, 1]))
    crop = trimesh.creation.box(extents=[140, 24, 40])
    crop.apply_translation([-40, -78, 10])
    mesh = trimesh.boolean.intersection([mesh, crop], engine='manifold')
    origin = mesh.bounds.mean(axis=0)
    result = affinity.rotate(affinity.translate(shape, -j[2][0], -j[2][1]), -j[3], origin=(0, 0))
    return affinity.translate(result, -origin[0], -origin[1])


def palette(settings):
    assert settings['filament_colour'] == ['#FFFFFF', '#C2AB84', '#B87333']
    # Native Bambu project serialization stores per-filament arrays with one
    # entry per slot; retain all existing entries and copy ordinary PLA for #4.
    for key, value in list(settings.items()):
        if isinstance(value, list) and len(value) == 3:
            settings[key] = value + [copy.deepcopy(value[0])]
        elif key.startswith('filament_dev_ams_drying_') and isinstance(value, list) and len(value) in (6, 12):
            settings[key] = value + value[:len(value)//3]
    settings['filament_colour'][3] = COLOR
    settings['filament_multi_colour'][3] = COLOR
    settings['filament_self_index'][3] = '4'
    settings['filament_settings_id'][3] = 'Generic PLA @BBL A1'
    settings['filament_ids'][3] = 'GFL99'
    settings['filament_max_volumetric_speed'][3] = '7.5'
    # The metallic appearance needs a conservative flow limit. Use the
    # existing 220 C PLA temperature and 65 C textured bed as test settings.
    if 'inherits_group' in settings:
        settings['inherits_group'] = settings['inherits_group'][:4] + [''] + settings['inherits_group'][4:]
    old = np.array(settings['flush_volumes_matrix']).reshape(3, 3)
    matrix = np.array([['0', '280', '280', '280'], ['420', '0', '280', '280'],
                       ['600', '420', '0', '420'], ['650', '500', '500', '0']])
    matrix[:3, :3] = old
    settings['flush_volumes_matrix'] = matrix.ravel().tolist()
    settings['flush_volumes_vector'] = settings['flush_volumes_vector'] + ['140', '140']
    settings['print_settings_id'] = 'Dara AMS - white wood copper - flush Azurite edge'
    assert settings['textured_plate_temp'] == ['65', '65', '55', '65']


def plot(cad, blue, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as PlotPath
    def draw(ax, shape, color):
        for p in polygons(shape):
            p = orient(p, 1)
            vertices, codes = [], []
            for ring in [p.exterior, *p.interiors]:
                coords = list(ring.coords)
                vertices.extend(coords)
                codes.extend([PlotPath.MOVETO] + [PlotPath.LINETO] * (len(coords)-2) + [PlotPath.CLOSEPOLY])
            ax.add_patch(PathPatch(PlotPath(vertices, codes), facecolor=color, edgecolor='none'))
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='#20334a')
    ax.set_facecolor('#20334a')
    draw(ax, artwork(cad, 'fabric_outline'), '#C2AB84')
    draw(ax, artwork(cad, 'knot_outline'), '#FFFFFF')
    draw(ax, blue, COLOR)
    draw(ax, artwork(cad, 'letter_outline'), '#B87333')
    ax.set(xlim=(-485, 485), ylim=(-485, 485), aspect='equal')
    ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(output, dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)


def stage(source, baseline):
    WORK.mkdir(exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    base = json.loads(baseline.read_text())
    assert base['project_sha256'] == digest(source)
    cad = CAD.read_text()
    knot = artwork(cad, 'knot_outline')
    fabric = artwork(cad, 'fabric_outline').buffer(.1125, quad_segs=16)
    # Follow only the fabric-facing edge, not the outside or part cut edges.
    blue = (fabric.buffer(GAP + WIDTH, quad_segs=16) - fabric.buffer(GAP, quad_segs=16)).intersection(knot)
    blue = blue.simplify(.001, preserve_topology=True)
    assert blue.is_valid and blue.area > 1000
    files = read_zip(source)
    root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    settings = json.loads(files['Metadata/project_settings.config'])
    palette(settings)
    objects = {o.get('id'): o for o in root.find(tag('resources'))}
    children = {n: ET.fromstring(d) for n, d in files.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
    next_id = max(int(o.get('id')) for r in [root, *children.values()] for o in r.find(tag('resources'))) + 1
    placements = read_array(cad, 'frame_placements')
    evidence, masks = [], []
    for obj in config.findall('object'):
        from validate_print_project import props
        name = props(obj)['name']
        if not (re.fullmatch(r'F\d+', name) or name == NAME):
            continue
        comps = objects[obj.get('id')].find(tag('components'))
        part = obj.find("part[@subtype='normal_part']")
        comp = next(c for c in comps if c.get('objectid') == part.get('id'))
        child = children[comp.get('{'+P+'}path').lstrip('/')]
        res = child.find(tag('resources'))
        mesh = read_mesh(next(o for o in res if o.get('id') == part.get('id')))
        matrix = transform(comp.get('transform'))
        mesh.apply_transform(matrix)
        body = manifold3d.Manifold(manifold3d.Mesh64(mesh.vertices, mesh.faces.astype(np.uint64)))
        local = coupon_shape(blue, cad) if name == NAME else in_print_coordinates(blue, placements[int(name[1:])-1])
        expected = section(local) ^ body.slice((BOTTOM + TOP)/2)
        assert expected.area() > 10, name
        for z in (BOTTOM+.001, TOP-.001):
            outside = (expected - body.slice(z).offset(.0001)).area()
            assert outside < .02, (name, z, outside)
        mask = as_mesh(expected.extrude(TOP-BOTTOM).translate([0, 0, BOTTOM]))
        assert abs(mask.volume - expected.area()*(TOP-BOTTOM)) < .01
        original = ROOT / ('working/stl/Dara-Print-Checks' if name == NAME else 'working/stl/Dara-Photo-Frame-A1-Jointed') / (name+'.stl')
        evidence.append(dict(part=name, area_mm2=expected.area(), volume_mm3=mask.volume,
            source_stl_sha256=digest(original), z_mm=[BOTTOM, TOP], triangles=len(mask.faces),
            connected_regions=len(mask.split()), printable_geometry_unchanged=True))
        if name != NAME:
            placed = mask.copy()
            p = placements[int(name[1:])-1]
            placed.apply_translation([*p[1], -p[3]])
            placed.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-p[0]), [0,0,1]))
            masks.append(placed)
        mask.apply_transform(np.linalg.inv(matrix))
        mesh_object(res, next_id, mask)
        nc = copy.deepcopy(comp)
        nc.set('objectid', str(next_id)); nc.set('{'+P+'}UUID', uid()); comps.append(nc)
        npart = ET.SubElement(obj, 'part', id=str(next_id), subtype='modifier_part', uuid=uid())
        setmeta(npart, 'name', name + ' - Flush Azurite ribbon edging')
        setmeta(npart, 'extruder', 4)
        ET.SubElement(npart, 'mesh_stat', face_count=str(len(mask.faces)), edges_fixed='0',
                      degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
        next_id += 1
        print(name, 'blue area', round(expected.area(), 2), flush=True)
    assert len(evidence) == 21
    for plate in config.findall('plate'):
        for key, value in [('filament_maps', '1 1 1 1'), ('filament_volume_maps', '0 0 0 0')]:
            setmeta(plate, key, value)
        if props(plate)['plater_id'] == '30':
            setmeta(plate, 'plater_name', '30 - White wood and blue edge test')
        for md in list(plate.findall('metadata')):
            if md.get('key', '').endswith('_file'):
                plate.remove(md)
    files = {n:d for n,d in files.items() if not n.startswith('Metadata/') or n in
             ('Metadata/model_settings.config', 'Metadata/project_settings.config')}
    files['3D/3dmodel.model'] = xml(root)
    files['Metadata/model_settings.config'] = xml(config)
    files['Metadata/project_settings.config'] = json.dumps(settings, indent=2).encode()
    for n, child in children.items():
        files[n] = xml(child)
    output = WORK / 'blue-edge.3mf'
    write_zip(output, files)
    spec = dict(prior_project_sha256=digest(source), source_cad_sha256=digest(CAD),
        filament_slot=4, filament_color=COLOR, filament_name='SUNLU PLA Metal Azurite',
        filament_url='https://www.amazon.com/dp/B0H3SFMXKW',
        width_mm=WIDTH, white_gap_to_weave_mm=GAP, z_mm=[BOTTOM, TOP], flush=True,
        path_method='Offset continuous assembled fabric footprint, intersect original white rails, then clip each printed section.',
        new_color_modifiers=21, masks=evidence, physical_tested=False,
        purge_to_white_mm3=650, physical_geometry_unchanged=True)
    base.update(project_sha256=digest(output), blue_ribbon_edge=spec)
    base['settings'] = {k: settings[k] for k in base['settings']}
    base['test_plate']['sliced'] = False
    base['test_plate']['blue_color_modifier_count'] = 1
    base['plate_layout'][29]['name'] = 'White wood and blue edge test'
    base['test_plate']['plate_layouts'] = copy.deepcopy(base['plate_layout'][29:])
    for key in ('bambu_studio_slice', 'bambu_studio_round_trip', 'bambu_studio_slice_warnings', 'ams_color_workflow'):
        base.pop(key, None)
    (WORK/'staged.json').write_text(json.dumps(base, indent=2)+'\n')
    (REVIEW/'design.json').write_text(json.dumps(spec, indent=2)+'\n')
    (WORK/'edge-footprint.geojson').write_text(json.dumps(mapping(blue)))
    trimesh.util.concatenate(masks).export(WORK/'assembled-blue-mask.stl')
    plot(cad, blue, REVIEW/'assembly-color-map.png')
    print(output)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, default=WORK/'baseline.3mf')
    ap.add_argument('--baseline', type=Path, default=WORK/'baseline.json')
    args = ap.parse_args()
    stage(args.source, args.baseline)
