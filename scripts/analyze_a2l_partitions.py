"""Search fresh planar partitions for the A2L; keep production CAD untouched.

Requires numpy, scipy, shapely >=2 and Pillow. Outputs an analysis candidate,
not production meshes or G-code. All geometry is in finished millimetres.
"""
import ast
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from shapely import affinity, line_merge, union_all
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import polygonize

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'
OUT = ROOT / 'working/review/a2l-optimization'
BED = np.array([330., 320.])
USABLE = BED - 3  # 1.5 mm clearance at each edge
A = np.deg2rad(np.arange(0, 180, .5))
C, S = np.cos(A), np.sin(A)


def array(text, name):
    return json.loads(re.search(r'^' + name + r'\s*=\s*(\[.*?\]);', text, re.M | re.S)[1])


def artwork(text, name):
    body = text.split('module ' + name + '() {', 1)[1].split('\n}', 1)[0]
    result = []
    for points, paths in re.findall(r'polygon\(points = (\[.*?\]), paths = (\[.*?\]), convexity', body, re.S):
        xy, rings = ast.literal_eval(points), ast.literal_eval(paths)
        result.append(Polygon([xy[i] for i in rings[0]], [[xy[i] for i in ring] for ring in rings[1:]]))
    return affinity.scale(union_all(result), .75, .75, origin=(0, 0))


def polygons(g):
    if g.geom_type == 'Polygon':
        return [] if g.is_empty else [g]
    return [p for q in getattr(g, 'geoms', []) for p in polygons(q)]


def lines(g):
    if g.geom_type == 'LineString':
        return [] if g.length < .001 else [g]
    return [p for q in getattr(g, 'geoms', []) for p in lines(q)]


def fit(g, refine=False):
    v = np.asarray(g.convex_hull.exterior.coords)[:-1]
    def dims(a):
        c, s = np.cos(a), np.sin(a)
        return np.stack([np.ptp(v[:, 0, None]*c-v[:, 1, None]*s, axis=0),
                         np.ptp(v[:, 0, None]*s+v[:, 1, None]*c, axis=0)], axis=-1)
    dd = dims(A)
    k = np.argmin((dd/USABLE).max(axis=1))
    angle = A[k]
    if refine:
        opt = minimize_scalar(lambda a: float((dims(np.array([a]))[0]/USABLE).max()),
                              bounds=(angle-math.pi/360, angle+math.pi/360), method='bounded',
                              options={'xatol': 1e-12})
        angle = opt.x
    d = dims(np.array([angle]))[0]
    rot = affinity.rotate(g, math.degrees(angle), origin=(0, 0))
    center = (np.array(rot.bounds[:2])+np.array(rot.bounds[2:]))/2
    return dict(utilization=float((d/USABLE).max()), footprint_mm=d.tolist(),
                rotation_deg=math.degrees(angle), rotated_center_mm=center.tolist())


def partition(whole, cuts):
    return [p for p in polygonize(union_all([whole.boundary, *cuts]))
            if whole.covers(p.representative_point()) and p.area > .001]


def shared_seams(parts):
    result = []
    for i, p in enumerate(parts):
        for j, q in enumerate(parts[:i]):
            for l in lines(line_merge(p.intersection(q))):
                if l.length > 1:
                    result.append((i, j, l))
    return result


def fresh_layout(whole, h):
    center = box(-h, -h, h, h)
    rays = [LineString([(0, 0), (1000*math.cos(t), 1000*math.sin(t))]).difference(center)
            for t in np.deg2rad(np.arange(8)*45)]
    return partition(whole, [center.boundary, *rays])


def details(whole, parts, text):
    seams = shared_seams(parts)
    # A single total order guarantees a lap assembly DAG. Center sections first;
    # lower outside sections precede upper ones to clear the existing M holes.
    order = sorted(range(len(parts)), key=lambda i: (len(parts[i].interiors) != 0,
                                                    parts[i].representative_point().y,
                                                    parts[i].representative_point().x))
    rank = {i: k for k, i in enumerate(order)}
    joints, domains, envelopes = [], [], list(parts)
    for i, j, l in seams:
        tongue, socket = sorted([i, j], key=rank.get)
        ends = np.asarray([l.coords[0], l.coords[-1]])
        t = (ends[1]-ends[0])/np.linalg.norm(ends[1]-ends[0])
        n = np.array([-t[1], t[0]])
        xy = ends.mean(axis=0)
        if parts[tongue].covers(Point(xy+n*.1)):
            n = -n
        t = np.array([-n[1], n[0]])
        def patch(lo, hi, pad):
            return Polygon([xy+n*u+t*v for u, v in [(lo, -l.length/2-pad),
                           (hi, -l.length/2-pad), (hi, l.length/2+pad), (lo, l.length/2+pad)]])
        # Same maximum X extent as tested_tongue_xz, clipped to continuous stock.
        # The axis cuts cross straight rails. Limit their trimming span to
        # the local rail so the tool cannot wrap into a neighboring corner.
        pad = 22 if l.length > 90 else 2
        extension = whole.intersection(patch(-1, 18, pad))
        domain = whole.intersection(patch(-1.5, 20, pad))
        envelopes[tongue] = envelopes[tongue].union(extension)
        domains.append(domain)
        joints.append(dict(tongue=tongue+1, socket=socket+1, xy_mm=xy.tolist(),
                           normal_deg=math.degrees(math.atan2(n[1], n[0])),
                           span_mm=l.length, trimming_span_padding_mm=pad, key_offsets_mm=[-l.length/2+11, l.length/2-11],
                           line=mapping(l)))
    hardware = []
    for kind, rows, radius in [('M screw', array(text, 'screw_mounts'), 8.5),
                               ('M locator', array(text, 'dowel_mounts'), 4.)]:
        for k, r in enumerate(rows):
            hardware.append((kind, k+1, Point(r[2]).buffer(radius)))
    anchors = np.asarray(array(text, 'photo_anchors'))*.75
    normals = np.asarray(array(text, 'photo_normals'))
    for k, xy in enumerate((anchors+normals*9.5).reshape(-1, 2)):
        hardware.append(('photo pilot', k+1, Point(xy).buffer(4.6)))
    conflicts = []
    for kind, k, g in hardware:
        hits = [j+1 for j, d in enumerate(domains) if g.intersection(d).area > .001]
        if hits:
            conflicts.append(dict(kind=kind, index=k, joints=hits))
    fits = [fit(p, True) for p in envelopes]
    separation = min(a.distance(b) for k, (_, _, a) in enumerate(seams) for _, _, b in seams[k+1:])
    overlap = max(a.intersection(b).area for k, a in enumerate(domains) for b in domains[k+1:])
    return dict(joints=joints, domains=domains, envelopes=envelopes, fits=fits,
                assembly_order=[i+1 for i in order], hardware_conflicts=conflicts,
                minimum_seam_separation_mm=separation, maximum_lap_domain_overlap_mm2=overlap)


def wall_sites(parts, domains, knot, text):
    records = []
    for k, m in enumerate(array(text, 'wall_mounts')):
        old = np.asarray(m[1], float)
        candidates = []
        for x in np.arange(80, 197, 2):
            xy = np.array([math.copysign(x, old[0]), old[1]])
            key_shapes = [box(xy[0]+v-10.5, xy[1]+m[2]-5.5,
                              xy[0]+v+10.5, xy[1]+m[2]+5.5) for v in m[3]]
            pilots = [Point(xy+[v, m[4]]).buffer(3.6) for v in m[5]]
            # Keys only need 3.3 mm backing; pilots need full knot rail thickness.
            if not all(knot.covers(g) for g in pilots):
                continue
            allsites = union_all([*key_shapes, *pilots])
            if any(allsites.distance(d) < 2 for d in domains):
                continue
            owners = [i+1 for i, p in enumerate(parts) if p.buffer(1e-7).covers(allsites)]
            if len(owners) != 1:
                continue
            candidates.append((np.linalg.norm(xy-old), xy, owners[0]))
        if not candidates:
            records.append(dict(block=k+1, resolved=False))
            continue
        distance, xy, owner = min(candidates, key=lambda c: c[0])
        records.append(dict(block=k+1, resolved=True, original_xy_mm=old.tolist(),
                            candidate_xy_mm=xy.tolist(), distance_mm=float(distance), section=owner))
    return records


def draw(parts, proof, current, knot, fabric):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGB', (2200, 1280), '#f5f2ec')
    d = ImageDraw.Draw(im)
    fontpath = '/System/Library/Fonts/Supplemental/Arial.ttf'
    try:
        title = ImageFont.truetype(fontpath, 34)
        textfont = ImageFont.truetype(fontpath, 24)
        small = ImageFont.truetype(fontpath, 19)
    except OSError:
        title = textfont = small = ImageFont.load_default()
    colors = ['#afcbd4', '#e4cbb0', '#b9cdb5', '#d0bed7', '#ddc7a2', '#b7c4de',
              '#e0bdc7', '#c4d8bd', '#c9d8ce', '#dfd3b1', '#b7cbd8', '#d4c7b6']
    def pix(coords, ox, oy, scale=1):
        return [(ox+x*scale, oy-y*scale) for x, y in coords]
    def fill(g, color, ox, oy):
        mask = Image.new('L', im.size, 0)
        md = ImageDraw.Draw(mask)
        for p in polygons(g):
            md.polygon(pix(p.exterior.coords, ox, oy), fill=255)
            for r in p.interiors:
                md.polygon(pix(r.coords, ox, oy), fill=0)
        im.paste(color, (0, 0), mask)
    for ox in [550, 1650]:
        fill(fabric.buffer(.1125, join_style=2).union(knot), '#e6e1d7', ox, 650)
    fill(fabric, '#c2ab84', 550, 650)
    fill(knot, '#fffdf7', 550, 650)
    for j in current:
        a = math.radians(j[3]); t = np.array([-math.sin(a), math.cos(a)])
        ends = np.asarray(j[2])+np.array([-1, 1])[:, None]*t*(j[4]/2)
        d.line(pix(ends, 550, 650), fill='#a63d32', width=3)
    for i, p in enumerate(parts):
        fill(p, colors[i % len(colors)], 1650, 650)
        x, y = p.representative_point().coords[0]
        d.text((1650+x, 650-y), str(i+1), font=small, fill='#243542', anchor='mm')
    for j in proof['joints']:
        d.line(pix(j['line']['coordinates'], 1650, 650), fill='#a63d32', width=4)
    for w in proof['wall_mount_candidates']:
        if w['resolved']:
            x, y = w['candidate_xy_mm']
            d.rectangle((1650+x-70, 650-y-19, 1650+x+70, 650-y+19), outline='#365c79', width=2)
    d.text((80, 65), 'Current A1: 20 sections / 32 joints', font=title, fill='#203342')
    d.text((1180, 65), 'Fresh A2L layout: 12 sections / 16 joints', font=title, fill='#203342')
    d.text((1100, 1170), 'Same 914.4 mm artwork. Red = seams. Blue outlines = proposed rear wall blocks.',
           font=textfont, fill='#334a59', anchor='mm')
    d.text((1100, 1220), 'Partition and lap-envelope study; production meshes, toolpaths and physical fit are not validated.',
           font=small, fill='#596771', anchor='mm')
    im.save(OUT/'comparison.png')
    # Each independently rotated part shown against its actual 330 x 320 bed.
    im = Image.new('RGB', (1600, 1550), '#f5f2ec'); d = ImageDraw.Draw(im)
    for i, (g, f) in enumerate(zip(proof['envelopes'], proof['fits'])):
        col, row = i % 4, i//4
        ox, oy = col*400+200, row*480+255
        d.rectangle((ox-165, oy-160, ox+165, oy+160), fill='#e2e7e8', outline='#687b85', width=2)
        d.rectangle((ox-163.5, oy-158.5, ox+163.5, oy+158.5), outline='#a5b1b5', width=1)
        r = affinity.rotate(g, f['rotation_deg'], origin=(0, 0))
        r = affinity.translate(r, -f['rotated_center_mm'][0], -f['rotated_center_mm'][1])
        fill(r, colors[i % len(colors)], ox, oy)
        w, h = f['footprint_mm']
        d.text((ox, oy+190), f'{i+1}: {w:.1f} x {h:.1f} mm', font=small, fill='#203342', anchor='mm')
    d.text((800, 1500), '330 x 320 mm beds; 1.5 mm edge clearance; 18 mm tongue envelopes included.',
           font=small, fill='#334a59', anchor='mm')
    im.save(OUT/'bed-layout.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    text = CAD.read_text()
    knot, fabric = artwork(text, 'knot_outline'), artwork(text, 'fabric_outline')
    whole = knot.union(fabric.buffer(.1125, join_style=2))
    candidates = []
    # Entirely new cuts, not combinations of the current F1-F20 sections.
    for h in np.arange(110, 201, 2):
        parts = fresh_layout(whole, float(h))
        detail = details(whole, parts, text)
        score = max(f['utilization'] for f in detail['fits'])
        candidates.append((len(detail['hardware_conflicts']), score, float(h), parts, detail))
    valid = [c for c in candidates if c[1] <= 1 and c[4]['maximum_lap_domain_overlap_mm2'] < .001
             and c[4]['minimum_seam_separation_mm'] > 20]
    count, score, h, parts, detail = min(valid, key=lambda c: (c[0], c[1]))
    walls = wall_sites(parts, detail['domains'], knot, text)
    coverage_error = union_all(parts).symmetric_difference(whole).area
    part_overlap = sum(p.intersection(q).area for i, p in enumerate(parts) for q in parts[:i])
    report = dict(status='geometry candidate; no production remesh or G-code slice',
                  source_cad_sha256=hashlib.sha256(CAD.read_bytes()).hexdigest(),
                  source_layout_sha256=hashlib.sha256((ROOT/'working/geometry/mirrored-frame-layout.json').read_bytes()).hexdigest(),
                  bed_mm=BED.tolist(), edge_allowance_mm=1.5, usable_bed_mm=USABLE.tolist(),
                  overall_size_mm=914.4, knot_sections=len(parts), knot_joints=len(detail['joints']),
                  baseline_sections=20, baseline_joints=32,
                  reduction_percent=100*(32-len(detail['joints']))/32,
                  intact_photo_loops=sum(len(p.interiors) for p in parts),
                  family='axis-aligned center square with eight outer rays at 45 degree intervals',
                  center_half_size_mm=h, searched_center_half_sizes_mm=[110,200,2],
                  objective='minimum fixed M/photo hardware conflicts, then minimum worst bed utilization within the 12-section/16-joint family',
                  maximum_bed_utilization=score, coverage_error_mm2=coverage_error,
                  part_overlap_mm2=part_overlap,
                  minimum_seam_length_mm=min(j['span_mm'] for j in detail['joints']),
                  maximum_seam_length_mm=max(j['span_mm'] for j in detail['joints']),
                  minimum_seam_separation_mm=detail['minimum_seam_separation_mm'],
                  maximum_lap_domain_overlap_mm2=detail['maximum_lap_domain_overlap_mm2'],
                  existing_M_and_photo_hardware_conflicts=detail['hardware_conflicts'],
                  wall_mount_candidates=walls, assembly_order=detail['assembly_order'],
                  part_fits=detail['fits'], joints=detail['joints'],
                  parts=[mapping(p) for p in parts],
                  lap_envelopes=[mapping(p) for p in detail['envelopes']],
                  limitations=['Not a proven global minimum.', 'Wall-mount slots require relocation and regeneration.',
                               'Production weave, blue modifiers, rear features and lap solids have not been remeshed or sliced.',
                               'Footprints exclude purge-tower space, brim and supports; those must be checked in the final AMS layout.'])
    assert coverage_error < 1e-6 and part_overlap < 1e-7
    assert score <= 1 and not detail['hardware_conflicts']
    assert all(w['resolved'] for w in walls)
    (OUT/'candidate.json').write_text(json.dumps(report, indent=2)+'\n')
    detail['wall_mount_candidates'] = walls
    draw(parts, detail, array(text, 'frame_joints'), knot, fabric)
    summary = {k:v for k,v in report.items() if k not in ['parts','lap_envelopes','joints','source_cad_sha256','source_layout_sha256']}
    (OUT/'verification.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
