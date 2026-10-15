"""Stage a flat copper coupon and an SVG for Bambu Studio native debossing."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from build_jointed_bambu_project import P, R, IDENTITY, meta, mesh_object, model, tag, uid, trimesh, np
from tune_silk_project import OBJECT_SETTINGS, read_zip, write_zip, sha, xml
from shapely.geometry import MultiPoint, box
from shapely.ops import voronoi_diagram

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/copper-emboss'
SVG = ROOT / 'working/Copper-Irregular-Recesses.svg'
TITLE = 'Copper native SVG recess test - 25 mm'
OVERRIDES = dict(OBJECT_SETTINGS, name=TITLE, extruder='3', enable_support='0',
                 brim_type='no_brim', sparse_infill_density='15%', sparse_infill_pattern='gyroid')


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(14102026)
    points = []
    for y in [-8.5, -2.8, 2.8, 8.5]:
        for x in [-8.5, -2.8, 2.8, 8.5]:
            points.append([x + rng.uniform(-1, 1), y + rng.uniform(-1, 1)])
    cells = []
    for region in voronoi_diagram(MultiPoint(points)).geoms:
        cell = region.intersection(box(-11.4, -11.4, 11.4, 11.4))
        # 0.9 mm webs between neighboring cuts; round corners in XY only.
        cell = cell.buffer(-.45).buffer(-.45).buffer(.45, quad_segs=6)
        assert cell.geom_type == 'Polygon' and cell.area > 8
        cells.append(cell)
    cells.sort(key=lambda p: (p.centroid.y, p.centroid.x))
    gap = min(a.distance(b) for i, a in enumerate(cells) for b in cells[i+1:])
    assert gap >= .89999 and len(cells) == 16
    paths = []
    for cell in cells:
        coords = [(x + 12.5, 12.5 - y) for x, y in cell.exterior.coords]
        paths.append('M ' + ' L '.join(f'{x:.4f},{y:.4f}' for x, y in coords[:-1]) + ' Z')
    SVG.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="25mm" height="25mm" viewBox="0 0 25 25">\n'
                   + '\n'.join(f'  <path fill="black" d="{p}"/>' for p in paths) + '\n</svg>\n')
    preserved = {name: sha(ROOT / name) for name in ['Dara.3mf',
        'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']}
    source = read_zip(ROOT / 'Dara.3mf')
    settings = json.loads(source['Metadata/project_settings.config'])
    settings.update(print_settings_id=TITLE, print_sequence='by layer', enable_prime_tower='0', enable_support='0')
    mesh = trimesh.creation.box([25, 25, 4])
    mesh.apply_translation([0, 0, 2])
    files = {'[Content_Types].xml': source['[Content_Types].xml'],
        '_rels/.rels': source['_rels/.rels'],
        'Metadata/project_settings.config': json.dumps(settings, indent=2).encode()}
    root = model()
    del root.attrib['xmlns:p']
    for key, value in [('Application', 'BambuStudio-02.08.02.61'), ('BambuStudio:3mfVersion', '1'), ('Title', TITLE)]:
        ET.SubElement(root, tag('metadata'), name=key).text = value
    obj = ET.SubElement(ET.SubElement(root, tag('resources')), tag('object'), id='1000', type='model', attrib={'{' + P + '}UUID': uid()})
    path = '3D/Objects/Flat-Coupon.model'
    ET.SubElement(ET.SubElement(obj, tag('components')), tag('component'), objectid='1001', transform=IDENTITY,
                  attrib={'{' + P + '}path': '/' + path, '{' + P + '}UUID': uid()})
    child = model()
    mesh_object(ET.SubElement(child, tag('resources')), 1001, mesh)
    files[path] = xml(child)
    build = ET.SubElement(root, tag('build'), attrib={'{' + P + '}UUID': uid()})
    ET.SubElement(build, tag('item'), objectid='1000', printable='1', transform='1 0 0 0 1 0 0 0 1 128 128 0', attrib={'{' + P + '}UUID': uid()})
    relationships = ET.Element('Relationships', xmlns=R)
    ET.SubElement(relationships, 'Relationship', Target='/' + path, Id='rel-1', Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    config = ET.Element('config')
    obj = ET.SubElement(config, 'object', id='1000')
    for key, value in OVERRIDES.items():
        meta(obj, key, value)
    part = ET.SubElement(obj, 'part', id='1001', subtype='normal_part')
    meta(part, 'name', 'Flat 25 x 25 x 4 mm base')
    ET.SubElement(part, 'mesh_stat', face_count='12', edges_fixed='0', degenerate_facets='0', facets_removed='0', facets_reversed='0', backwards_edges='0')
    plate = ET.SubElement(config, 'plate')
    for key, value in [('plater_id', 1), ('plater_name', TITLE), ('locked', 'false'), ('filament_map_mode', 'Auto For Flush'), ('filament_maps', '1 1 1 1'), ('filament_volume_maps', '0 0 0 0')]:
        meta(plate, key, value)
    instance = ET.SubElement(plate, 'model_instance')
    for key, value in [('object_id', 1000), ('instance_id', 0), ('identify_id', 101)]:
        meta(instance, key, value)
    files.update({'3D/3dmodel.model': xml(root), '3D/_rels/3dmodel.model.rels': xml(relationships), 'Metadata/model_settings.config': xml(config)})
    write_zip(WORK / 'base.3mf', files)
    (WORK / 'manifest.json').write_text(json.dumps(dict(preserved_hashes=preserved, pockets=16,
        svg=str(SVG), minimum_web_mm=gap, expected_pattern_bounds_mm=[-10.95, -10.95, 10.95, 10.95],
        base_dimensions_mm=[25, 25, 4], recess_depth_mm=.4), indent=2))
    print(json.dumps(dict(base=str(WORK / 'base.3mf'), svg=str(SVG), pockets=len(cells), gap_mm=gap)))


if __name__ == '__main__':
    stage()
