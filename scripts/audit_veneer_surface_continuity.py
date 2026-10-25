"""Inspect every veneer layer against exact saved mesh sections; no printer actions.

This checks file continuity, not physical stability or the cause of a printed shift.
"""
import hashlib
import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
import shapely
from shapely.strtree import STRtree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from validate_production_split import Project
from check_veneer_layer_overlap import parse

SOURCE = ROOT / 'Letter.3mf'
OUT = ROOT / '.work/veneer-full-height'
PROVENANCE = ROOT / 'release/letter-veneer-correction/validation.json'
NAMES = ['Left letter veneer', 'Right letter veneer', 'Center letter veneer']


def section(tri, z):
    # Slice actual triangle edges, without constructing a replacement triangulation.
    points = []
    ids = []
    for a, b in [(0, 1), (1, 2), (2, 0)]:
        lo = tri[:, a, 2] < z
        hi = tri[:, b, 2] < z
        mask = lo != hi
        t = (z-tri[mask, a, 2])/(tri[mask, b, 2]-tri[mask, a, 2])
        points.append(tri[mask, a, :2] + t[:, None]*(tri[mask, b, :2]-tri[mask, a, :2]))
        ids.append(np.flatnonzero(mask))
    ids = np.concatenate(ids)
    order = np.argsort(ids, kind='stable')
    assert len(ids) % 2 == 0
    assert np.array_equal(ids[order][::2], ids[order][1::2])
    return np.concatenate(points)[order].reshape(-1, 2, 2)


def run():
    OUT.mkdir(exist_ok=True, parents=True)
    project = Project(SOURCE)
    fig, axs = plt.subplots(3, 3, figsize=(15, 10))
    reports = []
    for i, name in enumerate(NAMES,1):
        obj = project.rows[name]
        raw = project.z.read(f'Metadata/plate_{obj["plate"]}.gcode')
        cache = OUT / f'plate_{i}.pkl'
        if cache.exists():
            saved = pickle.loads(cache.read_bytes())
            assert saved[0] == hashlib.sha256(raw).hexdigest()
            model, support = saved[1:]
        else:
            model, support = parse(raw.decode())
            cache.write_bytes(pickle.dumps((hashlib.sha256(raw).hexdigest(), model, support)))
        # Native export bakes the rotation into vertices. Recover assembly axes
        # from the recorded production pose, while sectioning native coordinates.
        provenance = json.loads(PROVENANCE.read_text())
        pose = np.array(provenance['assembly_to_printer_by_plate'][str(i)])
        mesh = obj['parts'][0]['mesh']
        printed = np.asarray(mesh.vertices) @ obj['T'][:3, :3].T + obj['T'][:3, 3]
        tri = printed[mesh.faces]
        assembled = (tri-pose[:3, 3]) @ pose[:3, :3]
        normal = np.cross(assembled[:, 1]-assembled[:, 0], assembled[:, 2]-assembled[:, 0])
        # Only the actual decorative front, excluding perimeter sides and carrier.
        tri = tri[(normal[:, 2] > 1e-10) & (assembled[:, :, 2].min(axis=1) > 10.49)]
        low = tri[:, :, 2].min(axis=1)
        high = tri[:, :, 2].max(axis=1)
        start = np.argsort(low)
        rows = []
        ends = []
        for z in sorted(model):
            lines = np.array([s[:4] for s in model[z] if s[5] == 'Outer wall']).reshape(-1, 2, 2)
            if not len(lines):
                continue
            mid = lines.mean(axis=1)
            assembly = (np.column_stack((mid, np.full(len(mid), z-.1)))-pose[:3, 3]) @ pose[:3, :3]
            carrier = lines[(assembly[:, 2] > 3) & (assembly[:, 2] < 4.6)]
            if len(carrier):
                ends.append([z, float(carrier[:, :, 1].min()), float(carrier[:, :, 1].max())])
            front = lines[assembly[:, 2] > 10.25]
            if not len(front):
                continue
            candidates = start[:np.searchsorted(low[start], z-.1, side='right')]
            candidates = candidates[high[candidates] >= z-.1]
            segments = section(tri[candidates], z-.1)
            if not len(segments):
                continue
            # Uniform length sampling avoids over-weighting short tessellation edges.
            length = np.linalg.norm(front[:, 1]-front[:, 0], axis=1)
            n = np.maximum(1, np.ceil(length/.5).astype(int))
            which = np.repeat(np.arange(len(front)), n)
            along = (np.arange(n.sum())-np.repeat(np.cumsum(n)-n, n)+.5)/n[which]
            pts = front[which, 0]+along[:, None]*(front[which, 1]-front[which, 0])
            tree = STRtree(shapely.linestrings(segments))
            nearest = tree.nearest(shapely.points(pts))
            distance = shapely.distance(shapely.points(pts), tree.geometries[nearest])
            # Do not discard outliers: report whole sample distribution.
            rows.append([z, len(pts), float(np.median(distance)), *np.quantile(distance, [.05, .95]).tolist(), float(distance.max())])
            if len(rows) % 400 == 0:
                print(name, 'front layers', len(rows), flush=True)
        a = np.array(rows)
        e = np.array(ends)
        np.savez_compressed(OUT / f'plate_{i}-continuity.npz', front=a, carrier_ends=e)
        jumps = np.diff(a[:, 2])
        peaks = np.argsort(abs(jumps))[-10:]
        full = a[(a[:, 0] >= 3.6) & (a[:, 0] <= 297.2)]
        assert len(full) == 1469 and np.allclose(np.diff(full[:, 0]), .2)
        # The first/last roof layers include the horizontal perimeter closure.
        # Keep their values in evidence, but screen coherent front displacement
        # over the continuous decorative face rather than that closure transition.
        interior = full[(full[:, 0] >= 4) & (full[:, 0] <= 296.8)]
        rec = dict(name=name, plate=obj['plate'], gcode_sha256=hashlib.sha256(raw).hexdigest(),
                   front_layers=len(full), front_z_range_mm=[float(full[0, 0]), float(full[-1, 0])],
                   missing_front_layers=0, median_mesh_distance_mm=[float(full[:, 2].min()), float(full[:, 2].max())],
                   continuous_face_z_range_mm=[4, 296.8],
                   continuous_face_median_mesh_distance_mm=[float(interior[:, 2].min()), float(interior[:, 2].max())],
                   maximum_adjacent_median_change_mm=float(abs(np.diff(interior[:, 2])).max()),
                   perimeter_closure_layers=full[(full[:, 0]<4)|(full[:, 0]>296.8)].tolist(),
                   peak_changes=[[float(a[k+1, 0]), float(jumps[k])] for k in peaks],
                   maximum_sample_distance_mm=float(full[:, 5].max()),
                   carrier_layers=len(e), carrier_z_range_mm=[float(e[0, 0]), float(e[-1, 0])],
                   carrier_reported_band=e[(e[:, 0] >= 137.8) & (e[:, 0] <= 139.4)].tolist())
        rec['carrier_largest_changes'] = []
        for col in [1, 2]:
            diff = np.diff(e[:, col])
            ids = np.argsort(abs(diff))[-12:]
            rec['carrier_largest_changes'].append([[float(e[k+1, 0]), float(diff[k])] for k in ids])
        # Threshold concerns coherent layer displacement, not exact bead geometry.
        assert rec['maximum_adjacent_median_change_mm'] < .01, rec
        ax = axs[i-1, 0]
        ax.plot(a[:, 0], a[:, 2]);ax.fill_between(a[:, 0], a[:, 3], a[:, 4], alpha=.2)
        ax.set_title(name+' — decorative surface');ax.set_ylabel('Path distance from mesh (mm)')
        ax.set_ylim(.15, .27)
        for j in [1, 2]:
            ax = axs[i-1, j]
            ax.plot(e[:, 0], e[:, j]);ax.set_title(name+' — '+('front' if j == 1 else 'rear')+' carrier end')
            ax.set_ylabel('Printer Y (mm)');ax.ticklabel_format(useOffset=False)
        reports.append(rec)
        print(name, json.dumps({k:rec[k] for k in ['front_layers', 'median_mesh_distance_mm', 'maximum_adjacent_median_change_mm', 'maximum_sample_distance_mm', 'carrier_largest_changes']}), flush=True)
    for ax in axs.flat:
        ax.set_xlabel('Print height Z (mm)');ax.grid(alpha=.3);ax.axvspan(138.2, 138.8, alpha=.15, color='purple')
    fig.suptitle('All three veneers — full-height native toolpaths compared with exact saved mesh sections\nDigital continuity inspection; physical whole-part shift remains unresolved')
    fig.tight_layout(rect=[0, 0, 1, .94]);fig.savefig(OUT/'all-veneer-continuity.png', dpi=150)
    report = dict(source=str(SOURCE), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  method='Actual triangle intersections at layer midpoint; outer-wall points sampled at <=0.5 mm; no replacement surface interpolation. All outer carrier end extrema included.',
                  limits='Digital continuity only. Native path offsets vary with width, corners and mesh simplification. Does not establish physical print stability or explain whole-part shift.',
                  checks=reports)
    (OUT/'continuity.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,default=SOURCE)
    parser.add_argument('--out',type=Path,default=OUT)
    parser.add_argument('--provenance',type=Path,default=PROVENANCE)
    args=parser.parse_args()
    SOURCE=args.project.resolve();OUT=args.out.resolve();PROVENANCE=args.provenance.resolve()
    run()
