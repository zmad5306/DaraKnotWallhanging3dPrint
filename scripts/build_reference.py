"""Rebuild the standalone design reference from the archived production package.

Usage: python scripts/build_reference.py --source-package PATH
Requires numpy, shapely and trimesh for extraction only. OpenSCAD itself needs
none of these packages, STL files, fonts, or external outline files.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.work/python-libs').is_dir():
    sys.path.insert(0, str(ROOT / '.work/python-libs'))

import numpy as np
import trimesh
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, LineString, box, shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union


SCAD_HEADER = '''// DARA WALL HANGING - CLEAN DESIGN REFERENCE
// Units: millimetres. Artwork faces +Z; +Y is up in the front view.
// Continuous design geometry: no part divisions or manufacturing features.
// This file is self-contained: no STL imports, includes, or installed fonts.
// The 48-inch master is uniformly scaled to 36 inches (75%) in X, Y and Z.

/* [Display] */
view_mode = "model"; // [model:3D reference, drawing:Flat front drawing]
show_knot = true;
show_letter = true;
show_fabric = true;
fabric_style = "woven"; // [woven:Open fabric pattern, plain:Simple fabric surface]

/* [Overall size - mm] */
overall_width = 914.4;

/* [Master proportions - before uniform scaling] */
// These master dimensions are all multiplied by overall_width / 1219.2.
// At 36 inches: knot depth 13.5 mm; M front Z=24 mm; fabric depth 0.6 mm.
knot_depth = 18;
letter_back_z = 18;
letter_depth = 14;
fabric_back_z = 12;
fabric_depth = 0.8;
fabric_pitch = 8;
fabric_thread_width = 2;

/* [Reference colours] */
knot_colour = [0.76, 0.79, 0.75];
fabric_colour = [0.57, 0.49, 0.36];
letter_colour = [0.96, 0.91, 0.79];

/* [Hidden] */
master_width = 1219.2;
uniform_scale = overall_width / master_width;
// Front orthographic view on opening. Rotate normally to inspect the depth.
$vpt = [0, 0, 0];
$vpr = [0, 0, 0];
$vpd = overall_width * 2.75;
$fn = 32;

assert(overall_width > 0 && knot_depth > 0 && letter_depth > 0);
assert(fabric_pitch > fabric_thread_width && fabric_thread_width > 0);
assert(fabric_back_z >= 0 && fabric_depth > 0);
assert(fabric_back_z + fabric_depth <= knot_depth);
assert(letter_back_z >= knot_depth);

// Outline modules below hold the artwork; these modules describe its depth.
// The knot rails have a plain, continuous section. The M is a single outline.
module knot_reference() {
    linear_extrude(height = knot_depth, convexity = 30)
        knot_outline();
}

module letter_reference() {
    translate([0, 0, letter_back_z])
        linear_extrude(height = letter_depth, convexity = 10)
            letter_outline();
}

// Only the visible decorative fabric: open threads, with no backing sheet,
// lower walls, end ties, braces, or additional support geometry.
// The tiny edge overlap joins the thread tips to the surrounding rails.
module fabric_pattern() {
    intersection() {
        offset(delta = 0.15) fabric_outline();
        if (fabric_style == "plain") {
            square([master_width + 4, master_width + 4], center = true);
        } else {
            union() {
                for (i = [-ceil(master_width / (2 * fabric_pitch)):
                           ceil(master_width / (2 * fabric_pitch))]) {
                    translate([i * fabric_pitch, 0])
                        square([fabric_thread_width, master_width + 4], center = true);
                    translate([0, i * fabric_pitch])
                        square([master_width + 4, fabric_thread_width], center = true);
                }
            }
        }
    }
}

module fabric_reference() {
    translate([0, 0, fabric_back_z])
        linear_extrude(height = fabric_depth, convexity = 30)
            fabric_pattern();
}

module reference_model() {
    if (show_knot) color(knot_colour) knot_reference();
    if (show_fabric) color(fabric_colour) fabric_reference();
    if (show_letter) color(letter_colour) letter_reference();
}

// Occlude the fabric and knot below the M in the flat drawing as in the model.
// Export this view to SVG or DXF when a 1:1 design drawing is needed.
module reference_drawing() {
    if (show_knot) color(knot_colour) difference() {
        knot_outline();
        if (show_letter) letter_outline();
    }
    if (show_fabric) color(fabric_colour) difference() {
        fabric_pattern();
        if (show_knot) knot_outline();
        if (show_letter) letter_outline();
    }
    if (show_letter) color(letter_colour) letter_outline();
}

scale([uniform_scale, uniform_scale, uniform_scale])
    if (view_mode == "drawing") reference_drawing();
    else reference_model();

// FROZEN ARTWORK OUTLINES
// Approved knot boundary; rounded channel ends and two local curve cleanups.
// M reconstructed from visible face contours with the old 0.16 mm seams closed.
// Polygon coordinates preserve the manuscript letter without a font dependency.
// Rebuild with scripts/build_reference.py; provenance records the input hashes.

'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polygons(g):
    return [g] if isinstance(g, Polygon) else list(g.geoms)


def scad_outline(name, geometry):
    lines = [f'module {name}() {{']
    for p in polygons(geometry):
        p = orient(p, 1)
        points, paths = [], []
        for ring in [p.exterior, *p.interiors]:
            coords = list(ring.coords)[:-1]
            paths.append(list(range(len(points), len(points) + len(coords))))
            points.extend(coords)
        lines.append('    polygon(points = [')
        for i in range(0, len(points), 5):
            row = ', '.join(f'[{x:.4f}, {y:.4f}]' for x, y in points[i:i+5])
            lines.append('        ' + row + (',' if i+5 < len(points) else ''))
        lines.append('    ], paths = [')
        for i, path in enumerate(paths):
            lines.append('        [' + ', '.join(map(str, path)) + ']' + (',' if i+1 < len(paths) else ''))
        lines.append('    ], convexity = 30);')
    lines.append('}\n')
    return '\n'.join(lines)


def clean_channels(grooves):
    # Same 24 symmetric channel end locations and 2 mm corner radius used by
    # the visual cleanup in the package, without any of its support additions.
    ends = [
        (True, 271.5518021849426, -69.5, 1, 8),
        (False, 24.01110382197192, 316.8, 1, 8),
        (True, 361.35001221105495, -69.5, -1, 365.68-361.35001221105495),
        (False, 114.03927919843565, 316.8, -1, 121.84-114.03927919843565),
        (True, 361.29, 316.8, -1, 365.68-361.29),
        (True, 271.539, 316.8, 1, 8),
    ]
    original = grooves
    for rotation in (0, 90, 180, 270):
        localgrooves = affinity.rotate(original, -rotation, origin=(0, 0))
        for horizontal, end, centre, direction, depth in ends:
            probe = Point(end-direction*3, centre) if horizontal else Point(centre, end-direction*3)
            comp = next(g for g in localgrooves.geoms if g.contains(probe))
            angle = (0 if horizontal else -90) + (180 if direction == -1 else 0)
            local = affinity.rotate(comp, angle, origin=(0, 0))
            tip, start = direction*end, direction*end-depth
            transverse = direction*(centre if horizontal else -centre)
            section = local.intersection(LineString([(start, -700), (start, 700)]))
            pieces = list(section.geoms) if hasattr(section, 'geoms') else [section]
            section = min(pieces, key=lambda g: g.distance(Point(start, transverse)))
            lo, hi = section.bounds[1], section.bounds[3]
            zone = box(start, lo-3, tip+3, hi+3)
            cap = box(start-2, lo, tip, hi).buffer(-2).buffer(2, quad_segs=16).intersection(zone)
            zone = affinity.rotate(zone, rotation-angle, origin=(0, 0))
            cap = affinity.rotate(cap, rotation-angle, origin=(0, 0))
            grooves = grooves.difference(zone).union(cap)

    # Smooth only the two known traced kinks; no tile geometry is involved.
    changes = []
    for centre in [(-303.54, -478.6), (-303.54, 478.6)]:
        comp = min(grooves.geoms, key=lambda p: p.boundary.distance(Point(centre)))
        a = np.array(comp.exterior.coords)
        lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(a, axis=0), axis=1))]
        count = math.ceil(lengths[-1]/0.35)
        distances = np.arange(count)*lengths[-1]/count
        pts = np.column_stack([np.interp(distances, lengths, a[:, i]) for i in (0, 1)])
        sigma = 3/(lengths[-1]/count)
        shifts = np.arange(-math.ceil(3*sigma), math.ceil(3*sigma)+1)
        weights = np.exp(-0.5*(shifts/sigma)**2)
        weights /= weights.sum()
        smooth = sum(w*np.roll(pts, int(k), axis=0) for k, w in zip(shifts, weights))
        distance = np.linalg.norm(pts-np.array(centre), axis=1)
        blend = np.clip((13-distance)/5, 0, 1)
        fixed = Polygon(pts+(smooth-pts)*blend[:, None]).simplify(0.01, preserve_topology=True)
        region = Point(centre).buffer(14, quad_segs=32)
        replacement = comp.difference(region).union(fixed.intersection(region))
        changes.append({'centre_mm': centre, 'max_boundary_change_mm': comp.hausdorff_distance(replacement)})
        grooves = grooves.difference(comp).union(replacement)
    return grooves, changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-package', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_package.resolve()
    data_path = source/'project-data.json'
    master_path = source/'source/approved-knot-master.geojson'
    data = json.loads(data_path.read_text())
    rails0 = shape(json.loads(master_path.read_text()))
    holes = sorted([Polygon(q) for q in rails0.interiors], key=lambda q: q.area, reverse=True)
    grooves0 = unary_union([holes[i] for i in [*range(1, 9), *range(21, 25)]])
    silhouette = rails0.union(grooves0)
    grooves, curve_changes = clean_channels(grooves0)
    rails = silhouette.difference(grooves)

    faces, letter_sources = [], []
    for record in data['parts']:
        if '/letter/' not in record['file']:
            continue
        path = source/record['file']
        mesh = trimesh.load_mesh(path)
        mesh.apply_transform(record['assembly_transform'])
        faces.append(unary_union([
            Polygon(tri[:, :2]) for tri, normal in zip(mesh.triangles, mesh.face_normals)
            if normal[2] > 0.9 and tri[:, 2].mean() > 30.9
            and Polygon(tri[:, :2]).area > 1e-7
        ]))
        letter_sources.append({'file': record['file'], 'sha256': digest(path)})

    segmented_letter = unary_union(faces)
    letter = segmented_letter.buffer(0.12, join_style=2).buffer(-0.12, join_style=2)
    # Overlay operations leave microscopic slivers near the repaired ends.
    # Quantize before simplification so the serialized polygons stay valid and
    # OpenSCAD's extrusion triangulator never sees duplicate/near-coincident edges.
    letter = set_precision(letter, 0.001).simplify(0.02, preserve_topology=True)
    rails = set_precision(rails, 0.001).simplify(0.02, preserve_topology=True)
    grooves = set_precision(grooves, 0.001).simplify(0.02, preserve_topology=True)
    assert rails.is_valid and grooves.is_valid and letter.is_valid
    assert isinstance(rails, Polygon) and isinstance(letter, Polygon)
    assert len(letter.interiors) == 0, 'Unexpected hole left in the M'
    assert len(grooves.geoms) == 12
    assert np.allclose(rails.bounds, [-609.6, -609.6, 609.6, 609.6])

    output = ROOT/'reference'
    output.mkdir(exist_ok=True)
    text = SCAD_HEADER + '\n'.join([
        scad_outline('knot_outline', rails),
        scad_outline('fabric_outline', grooves),
        scad_outline('letter_outline', letter),
    ])
    scad = output/'Dara-Clean-Reference.scad'
    scad.write_text(text, encoding='utf-8')
    provenance = {
        'purpose': 'Continuous theoretical design reference; no manufacturing features',
        'source_package': source.name,
        'inputs': [
            {'file': 'project-data.json', 'sha256': digest(data_path)},
            {'file': 'source/approved-knot-master.geojson', 'sha256': digest(master_path)},
            *letter_sources,
        ],
        'outline_processing': {
            'channel_ends_rounded': 24,
            'channel_corner_radius_mm': 2,
            'local_curve_cleanups': curve_changes,
            'M_seam_closing_radius_mm': 0.12,
            'outline_simplification_tolerance_mm': 0.02,
            'coordinate_grid_mm': 0.001,
            'M_closed_seam_area_mm2': letter.area-segmented_letter.area,
        },
        'uniform_scale': 0.75,
        'master_dimensions_mm': {
            'knot_width': 1219.2, 'knot_height': 1219.2, 'knot_depth': 18,
            'M_width': letter.bounds[2]-letter.bounds[0],
            'M_height': letter.bounds[3]-letter.bounds[1],
            'M_back_z': 18, 'M_front_z': 32,
            'fabric_back_z': 12, 'fabric_front_z': 12.8,
        },
        'outline_checks': {
            'valid_polygons': True, 'continuous_knot_outline': True,
            'continuous_M_outline': True, 'M_holes': 0, 'fabric_regions': 12,
        },
        'omitted': ['part seams', 'tongues', 'sockets', 'dowels', 'screw bosses',
                    'wall mounts', 'photo clips and recesses', 'rear labels',
                    'fabric backing', 'fabric support walls', 'end ties', 'braces'],
        'fabric': 'Schematic 1.5 mm open grid at 6 mm pitch, 0.6 mm thick; 0.1125 mm edge overlap',
        'scad_sha256': digest(scad),
    }
    provenance['reference_dimensions_mm'] = {
        key: round(value * provenance['uniform_scale'], 6)
        for key, value in provenance['master_dimensions_mm'].items()
    }
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(f'Saved {scad} ({scad.stat().st_size:,} bytes)')
    print(json.dumps(provenance['reference_dimensions_mm'], indent=2))


if __name__ == '__main__':
    main()
