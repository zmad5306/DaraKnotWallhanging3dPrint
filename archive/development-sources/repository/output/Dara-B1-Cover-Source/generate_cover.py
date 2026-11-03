"""Regenerate B1 with the original geometry functions, without slicing/publishing.

Added for this handoff. Original functions are unchanged in scripts/.
Requires Python 3.10+ and requirements.txt. Output remains an unresolved model.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_hammered_bands as b
from prepare_cover_crown_test import shape

region, floor, top = shape(1)
body = b.boolean([b.band_envelope(region, top),
                  b.envelope(floor, region.bounds, .25)], 'difference')
assert body.is_volume and body.is_watertight and body.body_count == 1
manifest = json.loads((ROOT / 'export-manifest.json').read_text())
body.apply_translation(manifest['assembly_to_export_translation_mm'])
target = ROOT / 'regenerated-B1-cover.stl'
body.export(target)
reference = b.trimesh.load_mesh(ROOT / 'B1-cover.stl', process=True)
error = max(b.cKDTree(reference.vertices).query(body.vertices)[0].max(),
            b.cKDTree(body.vertices).query(reference.vertices)[0].max())
assert error < .0001, error
print(target)
print(f'{len(body.faces)} triangles; maximum vertex difference {error:.9f} mm')
