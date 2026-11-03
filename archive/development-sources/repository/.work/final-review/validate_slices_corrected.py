import collections
import json
import math
from pathlib import Path
import re
import sys
import zipfile

folder = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
plate_count = len(json.loads((Path.cwd() / 'working/bambu/Dara-Photo-Frame-A1-Jointed/project-validation.json').read_text())['plate_layout'])
records = []
token = re.compile(r'([XYZEFIJP])([+-]?(?:\d+(?:\.\d*)?|\.\d+))')
for plate in range(1, plate_count + 1):
    path = folder / f'plate_{plate}.gcode'
    with zipfile.ZipFile('working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf') as archive:
        text = archive.read(f'Metadata/plate_{plate}.gcode').decode('utf-8')
    assert '; EXECUTABLE_BLOCK_END' in text, (plate, 'incomplete')
    for setting in ['wall_loops = 4', 'sparse_infill_density = 15%', 'sparse_infill_pattern = gyroid', 'layer_height = 0.2']:
        assert '; ' + setting + '\n' in text, (plate, setting)
    mass = float(re.search(r'total filament weight \[g\] : ([\d.]+)', text)[1])
    duration = re.search(r'total estimated time: ([^\n]+)', text)[1]
    seconds = sum(int(n) * {'h': 3600, 'm': 60, 's': 1}[u] for n, u in re.findall(r'(\d+)([hms])', duration))
    feature = 'Custom'
    features = collections.Counter()
    x = y = z = 0.
    lo = [math.inf, math.inf]
    hi = [-math.inf, -math.inf]
    bead_lo = [math.inf, math.inf]
    bead_hi = [-math.inf, -math.inf]
    line_width = .5
    paths = 0
    relative_e = False
    e_position = 0.
    for line in text.splitlines():
        if line.startswith('; FEATURE: '):
            feature = line.split(': ', 1)[1]
        if line.startswith('; LINE_WIDTH: '):
            line_width = float(line.split(': ', 1)[1])
        if line.startswith('M83'):
            relative_e = True
        elif line.startswith('M82'):
            relative_e = False
        elif line.startswith('G92 '):
            v = dict((k, float(n)) for k, n in token.findall(line.split(';')[0]))
            e_position = v.get('E', e_position)
        elif line.startswith(('G0 ', 'G1 ', 'G2 ', 'G3 ')):
            v = dict((k, float(n)) for k, n in token.findall(line.split(';')[0]))
            nx, ny, nz = v.get('X', x), v.get('Y', y), v.get('Z', z)
            de = v.get('E', 0 if relative_e else e_position) - (0 if relative_e else e_position)
            if de > 0 and feature != 'Custom' and ('X' in v or 'Y' in v):
                points = [(x, y), (nx, ny)]
                if line.startswith(('G2 ', 'G3 ')):
                    cx, cy = x + v.get('I', 0), y + v.get('J', 0)
                    radius = math.hypot(x - cx, y - cy)
                    a, b = math.atan2(y - cy, x - cx), math.atan2(ny - cy, nx - cx)
                    ccw = line.startswith('G3 ')
                    span = ((b - a) if ccw else (a - b)) % (2 * math.pi)
                    for q in (0, math.pi / 2, math.pi, math.pi * 1.5):
                        d = ((q - a) if ccw else (a - q)) % (2 * math.pi)
                        if d <= span + 1e-6:
                            points.append((cx + radius * math.cos(q), cy + radius * math.sin(q)))
                for point in points:
                    for axis in (0, 1):
                        lo[axis] = min(lo[axis], point[axis])
                        hi[axis] = max(hi[axis], point[axis])
                        bead_lo[axis] = min(bead_lo[axis], point[axis] - line_width / 2)
                        bead_hi[axis] = max(bead_hi[axis], point[axis] + line_width / 2)
                paths += 1
                features[feature] += 1
            x, y, z = nx, ny, nz
            if 'E' in v:
                e_position = e_position + v['E'] if relative_e else v['E']
    print(f'Plate {plate}: {paths} extrusion moves checked', flush=True)
    assert paths > 0
    clearance = min(*bead_lo, *(256 - n for n in bead_hi))
    if clearance < -0.01:
        print('Edge review:', plate, lo, hi, clearance)
    records.append({'plate': plate, 'weight_g': mass, 'estimated_seconds': seconds,
                    'extruding_xy_bounds_mm': [lo, hi], 'conservative_bed_edge_clearance_mm': clearance,
                    'features': dict(features), 'settings_verified': True})
report = {'all_plates_sliced': True, 'plate_count': plate_count, 'all_extrusions_within_bed': all(r['conservative_bed_edge_clearance_mm'] >= 0 for r in records),
          'total_weight_g': sum(r['weight_g'] for r in records),
          'total_estimated_seconds': sum(r['estimated_seconds'] for r in records),
          'minimum_edge_clearance_mm': min(r['conservative_bed_edge_clearance_mm'] for r in records),
          'plates': records}
(folder / 'slice-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'plates'}, indent=2))
assert report['all_extrusions_within_bed']
