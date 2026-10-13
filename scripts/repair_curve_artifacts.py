"""Locally fair the twelve reviewed trace defects, preserving other CAD features.

Uses the immutable before-review coordinates and a backed-up source. Changes
are confined to +/-14 mm of each vertex along its outline. Shared fabric/rail
edges are changed together. No manufacturing selectors or dimensions change.
"""
import json
import re
from pathlib import Path

from validate_print_project import ROOT, CAD, digest
from add_blue_ribbon_edge import artwork, polygons
from review_curve_artifacts import curve_candidates, outline
import numpy as np
from shapely import affinity, union_all
from shapely.geometry import Polygon, Point, LineString
from shapely.geometry.polygon import orient

WORK = ROOT / '.work/curve-repair'
REVIEW = ROOT / 'working/review/curve-repair'


def smooth_ring(coords, centers):
    """Gaussian fairing with a quintic taper to exact untouched vertices."""
    xy = np.asarray(coords)[:-1]
    length = np.linalg.norm(np.roll(xy, -1, axis=0)-xy, axis=1)
    s = np.r_[0., np.cumsum(length)]
    perimeter = s[-1]
    closed = np.vstack([xy, xy[0]])

    def interpolate(t):
        t = np.asarray(t) % perimeter
        return np.stack([np.interp(t, s, closed[:, k]) for k in (0, 1)], axis=-1)

    centers_s = []
    for center in centers:
        d = np.linalg.norm(xy-center, axis=1)
        assert d.min() < 1e-6
        centers_s.append(s[d.argmin()])
    signed = lambda values, c: (values-c+perimeter/2) % perimeter-perimeter/2
    keep = np.ones(len(xy), dtype=bool)
    for c in centers_s:
        keep &= np.abs(signed(s[:-1], c)) >= 14
    sample_s = np.concatenate([s[:-1][keep]]+[(c+np.linspace(-14, 14, 113)) % perimeter for c in centers_s])
    sample_s = np.unique(sample_s)
    result = interpolate(sample_s)
    shifts = np.linspace(-10, 10, 201)
    weights = np.exp(-.5*(shifts/2.5)**2)
    weights /= weights.sum()
    for c in centers_s:
        d = np.abs(signed(sample_s, c))
        active = d < 14
        t = np.clip((14-d[active])/7, 0, 1)
        blend = t**3*(10-15*t+6*t*t)
        smoothed = np.sum(interpolate(sample_s[active, None]+shifts)*weights[None, :, None], axis=1)
        result[active] += (smoothed-result[active])*blend[:, None]
    return result


def serialize(name, shape):
    lines = ['module '+name+'() {']
    for p in polygons(affinity.scale(shape, 1/.75, 1/.75, origin=(0, 0))):
        p = orient(p, 1)
        pts, paths = [], []
        for ring in [p.exterior, *p.interiors]:
            coordinates = list(ring.coords)[:-1]
            paths.append(list(range(len(pts), len(pts)+len(coordinates))))
            pts.extend(coordinates)
        lines.append('    polygon(points = [')
        for i in range(0, len(pts), 5):
            lines.append('        '+', '.join(f'[{x:.6f}, {y:.6f}]' for x, y in pts[i:i+5])+
                         (',' if i+5 < len(pts) else ''))
        lines.extend(['    ], paths = '+json.dumps(paths)+', convexity = 30);'])
    return '\n'.join(lines)+'\n}'


def main():
    REVIEW.mkdir(parents=True, exist_ok=True)
    before = (WORK/'original.scad').read_text()
    historical = json.loads((ROOT/'working/review/curve-artifacts/review.json').read_text())
    assert digest(WORK/'original.scad') == historical['source_cad_sha256']
    findings = historical['findings']
    knot, fabric = [artwork(before, name+'_outline') for name in ('knot', 'fabric')]
    assert len(findings) == 12 and len(polygons(knot)) == 1
    new_rings, shared_deltas = [], []
    for ri, ring in enumerate([knot.exterior, *knot.interiors]):
        targets = [r for r in findings if r['ring'] == ri]
        if targets:
            new_xy = smooth_ring(ring.coords, [r['assembly_xy_mm'] for r in targets])
            if any(r['affects_blue_edge'] for r in targets):
                assert all(r['affects_blue_edge'] for r in targets) and ri > 0
                # A knot hole is the corresponding fabric footprint. Apply its
                # exact signed delta so there is no gap or overlap at the join.
                shared_deltas.append((Polygon(ring), Polygon(new_xy)))
        else:
            new_xy = np.asarray(ring.coords)[:-1]
        new_rings.append(new_xy)
    new_knot = Polygon(new_rings[0], new_rings[1:])
    new_fabric = fabric
    for old, new in shared_deltas:
        new_fabric = new_fabric.difference(old.difference(new)).union(new.difference(old))
    assert new_knot.is_valid and new_fabric.is_valid
    # Original independently quantized outlines already overlap by 0.188 mm2.
    assert new_knot.intersection(new_fabric).area <= knot.intersection(fabric).area + 1e-6
    assert len(polygons(new_fabric)) == len(polygons(fabric))
    assert len(new_knot.interiors) == len(knot.interiors)
    assert np.allclose(new_knot.bounds, knot.bounds, atol=1e-6)
    delta = knot.symmetric_difference(new_knot)
    zones = union_all([Point(r['assembly_xy_mm']).buffer(14.01) for r in findings])
    assert delta.difference(zones).area < 1e-7
    assert knot.boundary.hausdorff_distance(new_knot.boundary) < .5
    assert not curve_candidates(new_knot)[0]
    assert not curve_candidates(new_fabric)[0]
    after = before
    for name, shape in [('knot_outline', new_knot), ('fabric_outline', new_fabric)]:
        after, count = re.subn(r'module '+name+r'\(\) \{.*?\n\}', lambda _: serialize(name, shape), after, count=1, flags=re.S)
        assert count == 1
    for name, shape in [('knot_outline', new_knot), ('fabric_outline', new_fabric)]:
        parsed = artwork(after, name)
        assert parsed.is_valid and parsed.symmetric_difference(shape).area < .002
        assert not curve_candidates(parsed)[0]
    CAD.write_text(after)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 4, figsize=(16, 12))
    records = []
    for ax, r in zip(axes.flat, findings):
        x, y = r['assembly_xy_mm']
        outline(ax, knot, '#d86742', 1.4)
        outline(ax, new_knot, '#16759b', 1.4)
        ax.set(xlim=(x-8, x+8), ylim=(y-8, y+8), aspect='equal')
        ax.set_title(r['id']+' / plate '+str(r['locations'][0]['plate']))
        ax.grid(alpha=.2)
        patch = Point(x, y).buffer(14.01)
        records.append(dict(id=r['id'], assembly_xy_mm=[x, y], plate=r['locations'][0]['plate'],
                            affects_blue_edge=r['affects_blue_edge'],
                            changed_area_mm2=delta.intersection(patch).area,
                            max_boundary_shift_mm=knot.boundary.intersection(patch).hausdorff_distance(new_knot.boundary.intersection(patch))))
    fig.suptitle('Local curve repairs - orange: original; blue: corrected', fontsize=16)
    fig.tight_layout(rect=(0, 0, 1, .97)); fig.savefig(REVIEW/'before-after-curves.png', dpi=180); plt.close(fig)
    report = dict(original_source_sha256=digest(WORK/'original.scad'),
                  method='Gaussian local fairing, sigma 2.5 mm, quintic taper between 7 and 14 mm, 0.25 mm sampling; shared rail/fabric edges updated together.',
                  findings_repaired=records, max_boundary_shift_mm=knot.boundary.hausdorff_distance(new_knot.boundary),
                  changed_outline_area_mm2=delta.area, changed_area_outside_reviewed_regions_mm2=delta.difference(zones).area,
                  outline_bounds_unchanged=True, isolated_curve_findings_after=0,
                  native_feature_code_unchanged=True)
    (REVIEW/'source-repair.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
