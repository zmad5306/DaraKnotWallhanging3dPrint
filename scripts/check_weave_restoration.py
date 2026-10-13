"""Compare restored frame STLs with a saved pre-restoration 3MF.

Checks that nothing meaningful was removed and that changes below/above the
crossing band are numerical noise. The regular project validator separately
checks assembled interference, source hashes, placements and sliced toolpaths.
"""
import argparse
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from build_jointed_bambu_project import ROOT, tag, P
from colorize_print_project import read_mesh
from validate_print_project import transform, props, digest
import trimesh


def symmetric_volume(a, b):
    return abs(trimesh.boolean.difference([a, b], engine='manifold').volume) + abs(
        trimesh.boolean.difference([b, a], engine='manifold').volume)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    records = []
    with zipfile.ZipFile(args.baseline) as z:
        config = ET.fromstring(z.read('Metadata/model_settings.config'))
        root = ET.fromstring(z.read('3D/3dmodel.model'))
        for i in range(1, 21):
            name = f'F{i}'
            obj = next(o for o in config.findall('object') if props(o)['name'] == name)
            pid = obj.find("part[@subtype='normal_part']").get('id')
            resource = root.find(tag('resources')).find(f"{tag('object')}[@id='{obj.get('id')}']")
            comp = next(c for c in resource.find(tag('components')) if c.get('objectid') == pid)
            child = ET.fromstring(z.read(comp.get('{'+P+'}path').lstrip('/')))
            old = read_mesh(child.find(tag('resources')).find(f"{tag('object')}[@id='{pid}']"))
            old.apply_transform(transform(comp.get('transform')))
            new = trimesh.load_mesh(ROOT / f'working/stl/Dara-Photo-Frame-A1-Jointed/{name}.stl')
            removed = abs(trimesh.boolean.difference([old, new], engine='manifold').volume)
            unchanged_errors = []
            for low, high in [(0, 9.598), (9.902, 30)]:
                clip = trimesh.creation.box(extents=[600, 600, high-low])
                clip.apply_translation([0, 0, (high+low)/2])
                a = trimesh.boolean.intersection([old, clip], engine='manifold')
                b = trimesh.boolean.intersection([new, clip], engine='manifold')
                unchanged_errors.append(symmetric_volume(a, b))
            assert removed < .02 and max(unchanged_errors) < .02, (name, removed, unchanged_errors)
            added = new.volume - old.volume
            assert added > 1
            records.append({'part': name, 'removed_volume_mm3': removed,
                            'lower_body_symmetric_difference_mm3': unchanged_errors[0],
                            'above_relief_symmetric_difference_mm3': unchanged_errors[1],
                            'added_relief_volume_mm3': added})
    report = {'baseline_sha256': digest(args.baseline), 'tolerance_mm3': .02,
              'unchanged_bands_mm': [[0, 9.598], [9.902, 30]], 'all_passed': True, 'parts': records}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(f'All 20 frame bodies unchanged outside crossing relief; maximum difference '
          f'{max(max(p[k] for k in ("lower_body_symmetric_difference_mm3", "above_relief_symmetric_difference_mm3")) for p in records):.6f} mm3')


if __name__ == '__main__':
    main()
