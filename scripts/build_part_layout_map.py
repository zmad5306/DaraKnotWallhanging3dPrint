"""Build the printable part map from the final 3MF, STL geometry, and CAD placements.

Run `python scripts/build_part_layout_map.py prepare` with numpy, shapely, and
trimesh, then `python scripts/build_part_layout_map.py render` with reportlab.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
STLS = ROOT / 'working/stl/Dara-Photo-Frame-A1-Jointed'
SCRATCH = ROOT / '.work/part-layout-map'
DATA = SCRATCH / 'layout-data.json'
OUTPUT = ROOT / 'output/pdf/Dara-Part-and-Plate-Map.pdf'


def prepare():
    sys.path.insert(0, str(ROOT / '.work/python-libs'))
    import numpy as np
    import shapely
    import trimesh
    from shapely import affinity
    from shapely.geometry import Point
    from shapely.ops import polylabel

    SCRATCH.mkdir(parents=True, exist_ok=True)
    report = json.loads((PACKAGE / 'project-validation.json').read_text())
    project = PACKAGE / report['project']
    digest = hashlib.sha256(project.read_bytes()).hexdigest()
    assert digest == report['project_sha256'], 'Project changed; refresh validation first.'
    cad = (ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()

    def array(name):
        return json.loads(re.search(r'^' + name + r'\s*=\s*(\[.*?\]);', cad, re.M | re.S)[1])

    def props(el):
        return {m.get('key'): m.get('value') for m in el.findall('metadata') if m.get('key')}

    with zipfile.ZipFile(project) as z:
        config = ET.fromstring(z.read('Metadata/model_settings.config'))
    names = {o.get('id'): props(o)['name'] for o in config.findall('object')}
    actual = {}
    for plate in config.findall('plate'):
        number = int(props(plate)['plater_id'])
        for instance in plate.findall('model_instance'):
            name = names[props(instance)['object_id']]
            item = actual.setdefault(name, {'plate': number, 'quantity': 0})
            assert item['plate'] == number
            item['quantity'] += 1
    assert len(actual) == 39 and sum(p['quantity'] for p in actual.values()) == 70
    assert len(config.findall('plate')) == 29

    def rings(geometry):
        polys = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)
        return [{'outer': list(p.exterior.coords), 'holes': [list(h.coords) for h in p.interiors]}
                for p in polys if p.area > .01]

    placements = {k: array(k + '_placements') for k in ['frame', 'M']}
    photos, walls = array('photo_centres'), array('wall_mounts')
    parts = {}
    silhouettes = {}
    for entry in report['parts']:
        name = entry['name']
        assert actual[name] == {'plate': entry['plate'], 'quantity': entry['quantity']}
        path = STLS / (name + '.stl')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['file_sha256']
        mesh = trimesh.load_mesh(path)
        triangles = mesh.triangles[:, :, :2]
        a, b = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
        areas = np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) / 2
        shape = shapely.union_all(shapely.polygons(triangles[areas > 1e-7]))
        silhouettes[name] = shape
        if name.startswith('F') or name.startswith('M'):
            family = 'frame' if name.startswith('F') else 'M'
            p = placements[family][int(name[1:]) - 1]
            assembled = affinity.rotate(affinity.translate(shape, *p[1]), -p[0], origin=(0, 0))
            anchor = Point(p[2])
            if not assembled.contains(anchor):
                poly = assembled if assembled.geom_type == 'Polygon' else max(assembled.geoms, key=lambda x: x.area)
                anchor = polylabel(poly, tolerance=1)
        elif name.startswith('Backer'):
            xy = np.array(photos[int(name[6:]) - 1]) * .75
            assembled = affinity.translate(shape, *xy)
            anchor = assembled.centroid
        elif name.startswith('B'):
            xy = walls[int(name[1:]) - 1][1]
            assembled = affinity.translate(shape, *xy)
            anchor = Point(xy)
        else:
            assembled = shape
            anchor = shape.centroid
        parts[name] = {**actual[name], 'print_outline': rings(shape), 'assembly_outline': rings(assembled),
                       'label_xy': list(anchor.coords)[0]}
    tabs = []
    anchors = np.array(array('photo_anchors')).reshape(-1, 2)
    normals = np.array(array('photo_normals')).reshape(-1, 2)
    for anchor, normal in zip(anchors, normals):
        shape = affinity.translate(silhouettes['Retainer'], 4.5, 0)
        shape = affinity.rotate(shape, math.degrees(math.atan2(normal[1], normal[0])), origin=(0, 0))
        tabs.append(rings(affinity.translate(shape, *(anchor * .75))))
    data = {'project': project.name, 'project_sha256': digest, 'parts': parts,
            'plate_layout': report['plate_layout'], 'tabs': tabs, 'settings': report['settings']}
    DATA.write_text(json.dumps(data), encoding='utf-8')
    print(f'Prepared {len(parts)} part footprints and {len(tabs)} installed tabs.')


def render():
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, Color
    from reportlab.lib.pagesizes import landscape, letter

    data = json.loads(DATA.read_text())
    assert hashlib.sha256((PACKAGE / data['project']).read_bytes()).hexdigest() == data['project_sha256']
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(letter), pageCompression=1)
    c.setTitle('Dara Part and Plate Map')
    c.setAuthor('Dara knot wall hanging project')
    W, H = landscape(letter)
    ink = HexColor('#20252A')
    muted = HexColor('#57616A')
    pale = HexColor('#E9ECEE')
    frame_colors = ['#C6DCE7', '#D7E8D2', '#EFDEC0', '#DAD3E8', '#EDD0CC']
    parts = data['parts']

    def text(x, y, value, size=10, font='Helvetica', color=ink):
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(x, y, value)

    def centered(x, y, value, size=10, font='Helvetica', color=ink):
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawCentredString(x, y, value)

    def page(title, subtitle, number):
        text(32, H - 39, title, 22, 'Helvetica-Bold')
        text(32, H - 59, subtitle, 10, color=muted)
        text(32, 23, 'Dara photo frame  |  29 plates  |  70 printed pieces  |  100% scale', 8.5, color=muted)
        c.setFont('Helvetica', 8.5)
        c.drawRightString(W - 32, 23, f'{number} / 4')

    def mapping(xy):
        return (257 + xy[0] * 450 / 980, 299 + xy[1] * 450 / 980)

    def outline(rings, transform=mapping, fill='#DDE3E6', stroke='#69747D', width=.55):
        c.setFillColor(HexColor(fill))
        c.setStrokeColor(HexColor(stroke))
        c.setLineWidth(width)
        path = c.beginPath()
        for poly in rings:
            for ring in [poly['outer']] + poly['holes']:
                for j, xy in enumerate(ring):
                    x, y = transform(xy)
                    (path.moveTo if j == 0 else path.lineTo)(x, y)
                path.close()
        c.drawPath(path, fill=1, stroke=1, fillMode=0)

    def label(name, xy=None, transform=mapping, small=False):
        x, y = transform(xy or parts[name]['label_xy'])
        size = 8 if small else 9
        width = max(32, len(name) * size * .57 + 8)
        c.setFillColor(Color(1, 1, 1, alpha=.94))
        c.roundRect(x - width / 2, y - 12, width, 25, 3, fill=1, stroke=0)
        centered(x, y + 2, name, size, 'Helvetica-Bold')
        centered(x, y - 8, f'Plate {parts[name]["plate"]:02d}', 7.5)

    def table(names, x=520, top=504, width=240, row_height=17):
        c.setFillColor(HexColor('#DDE3E6'))
        c.rect(x, top - 21, width, 21, fill=1, stroke=0)
        text(x + 9, top - 14, 'Part', 9, 'Helvetica-Bold')
        text(x + 132, top - 14, 'Plate', 9, 'Helvetica-Bold')
        text(x + 198, top - 14, 'Qty', 9, 'Helvetica-Bold')
        for i, name in enumerate(names):
            y = top - 21 - (i + 1) * row_height
            c.setFillColor(HexColor('#F4F6F7' if i % 2 == 0 else '#FFFFFF'))
            c.setStrokeColor(HexColor('#D9D9D9'))
            c.setLineWidth(.35)
            c.rect(x, y, width, row_height, fill=1, stroke=1)
            text(x + 9, y + 5, name, 9)
            text(x + 138, y + 5, f'{parts[name]["plate"]:02d}', 9)
            text(x + 205, y + 5, str(parts[name]['quantity']), 9)
        return top - 21 - len(names) * row_height

    def background_frame():
        for i in range(1, 21):
            outline(parts[f'F{i}']['assembly_outline'], fill='#F0F2F3', stroke='#B8C0C5', width=.35)

    page('Dara frame part layout', 'Front view of the frame sections with their Bambu Studio plate numbers', 1)
    for i in range(1, 21):
        outline(parts[f'F{i}']['assembly_outline'], fill=frame_colors[(i - 1) % len(frame_colors)])
    for i in range(1, 21):
        label(f'F{i}')
    table([f'F{i}' for i in range(1, 21)])
    text(520, 116, 'Read the two-line labels as', 10, 'Helvetica-Bold')
    text(520, 99, 'part number followed by print plate.', 10)
    text(520, 78, 'Frame width is 914.4 mm when assembled.', 9)
    centered(257, 62, 'TOP remains at the top of all assembly maps. Not a full-size template.', 8.5, color=muted)
    c.showPage()

    page('Dara letter part layout', 'Front view of the six M sections over the frame outline', 2)
    background_frame()
    for i in range(1, 7):
        outline(parts[f'M{i}']['assembly_outline'], fill=['#EDC7B4', '#E5D8AF', '#D9C7DF'][(i - 1) % 3], stroke='#786452', width=.75)
    for i in range(1, 7):
        label(f'M{i}')
    table([f'M{i}' for i in range(1, 7)], row_height=23)
    text(520, 306, 'How to use the map', 12, 'Helvetica-Bold')
    for i, line in enumerate(['Find the section in the assembled M,', 'then use its plate number to locate the',
                              'matching part in Bambu Studio.', '', 'The grey outline is the frame beneath',
                              'the M. Frame plates are on page 1.']):
        text(520, 284 - i * 16, line, 10)
    centered(257, 62, 'Same front-view orientation as page 1.', 8.5, color=muted)
    c.showPage()

    page('Dara backers and wall blocks', 'Rear components shown in front-view alignment so left and right match the other maps', 3)
    background_frame()
    for i in range(1, 9):
        outline(parts[f'Backer{i}']['assembly_outline'], fill='#DAD6E9', stroke='#81778F')
    for tab in data['tabs']:
        outline(tab, fill='#E3B568', stroke='#9B7636', width=.3)
    for i in range(1, 5):
        outline(parts[f'B{i}']['assembly_outline'], fill='#AAD4CD', stroke='#447C73', width=.65)
    for i in range(1, 9):
        label(f'Backer{i}')
    for i in range(1, 5):
        label(f'B{i}')
    table([f'Backer{i}' for i in range(1, 9)] + [f'B{i}' for i in range(1, 5)] + ['Retainer'])
    text(520, 232, 'Wall block locations', 11, 'Helvetica-Bold')
    for i, line in enumerate(['B1 on F3     B2 on F5', 'B3 on F16   B4 on F18', '', 'Gold tabs are the 32 Retainer copies.',
                              'Use four for each photo backer.', '', 'All wall blocks and retainers print on', 'Plate 29. Screws and washers are', 'purchased hardware.']):
        text(520, 212 - i * 15, line, 9.5)
    centered(257, 62, 'This is a front-view location guide, not a mirrored view of the rear.', 8.5, color=muted)
    c.showPage()

    page('Shared print plate layouts', 'Top views of the A1 beds in the saved project with each distinct part identified', 4)
    for column, pi in enumerate([26, 27, 28]):
        plate = data['plate_layout'][pi]
        left, bottom, side = 32 + column * 252, 279, 224
        centered(left + side / 2, 521, f'Plate {pi + 1:02d}', 14, 'Helvetica-Bold')
        c.setFillColor(HexColor('#F6F7F8'))
        c.setStrokeColor(HexColor('#8D969D'))
        c.setLineWidth(.6)
        c.rect(left, bottom, side, side, fill=1, stroke=1)
        def bed(xy):
            return left + xy[0] * side / 256, bottom + xy[1] * side / 256
        for item in plate['items']:
            name = item['name']
            dx, dy = item['xy']
            def placed(xy, dx=dx, dy=dy):
                return bed([xy[0] + dx, xy[1] + dy])
            color = '#DAD6E9' if name.startswith('Backer') else '#E3B568' if name == 'Retainer' else '#AAD4CD'
            outline(parts[name]['print_outline'], transform=placed, fill=color, stroke='#788087', width=.35)
            if name != 'Retainer':
                bounds = item['bounds']
                xy = [(bounds[0][a] + bounds[1][a]) / 2 for a in range(2)]
                x, y = bed(xy)
                centered(x, y - 3, name, 9, 'Helvetica-Bold')
        centered(left + side / 2, bottom - 15, '256 x 256 mm bed  |  top view', 8.5, color=muted)
        if pi < 28:
            centered(left + side / 2, 235, 'Four backers, one of each shown', 10)
        else:
            centered(left + side / 2, 235, 'B1-B4 plus 32 Retainer copies', 10)
    text(32, 187, 'Project settings', 12, 'Helvetica-Bold')
    text(32, 167, 'Bambu Lab A1   |   0.4 mm nozzle   |   PLA   |   0.2 mm layers', 10)
    text(32, 149, '4 wall loops   |   15% gyroid infill   |   Local 100% infill at screw and mounting points', 10)
    text(32, 115, 'Backers use no brim and print by layer. All parts retain their original scale.', 10)
    text(32, 97, 'Plates 01-20 each contain the matching F section. Plates 21-26 each contain one M section.', 10)
    text(32, 68, 'Project file: ' + data['project'], 9, color=muted)
    c.save()
    print(str(OUTPUT))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'render'])
    args = parser.parse_args()
    (prepare if args.stage == 'prepare' else render)()
