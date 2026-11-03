"""Package the current, unresolved B1 cover for independent inspection."""
import ast
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import prepare_hammered_bands as b
from colorize_print_project import read_mesh

OUT = ROOT / 'output/Dara-B1-Cover-Source'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / 'Dara-Cover-Smooth-Crown-Test.3mf'
files = b.read_zip(SOURCE)
root = ET.fromstring(files['3D/3dmodel.model'])
item = root.find(b.tag('build')).find(b.tag('item'))
parent = root.find(b.tag('resources')).find(b.tag('object'))
component = parent.find(b.tag('components')).find(b.tag('component'))
child_path = component.get('{' + b.P + '}path').lstrip('/')
child = ET.fromstring(files[child_path])
obj = child.find(b.tag('resources')).find(b.tag('object'))
mesh = read_mesh(obj)
assert mesh.is_volume and mesh.is_watertight and mesh.body_count == 1
assert len(mesh.faces) == 67892

# The published STL is extracted, not regenerated or repaired.
stl = OUT / 'B1-cover.stl'
mesh.export(stl)
check = b.trimesh.load_mesh(stl, process=True)
assert check.is_watertight and check.is_volume and check.body_count == 1
error = float(b.cKDTree(check.vertices).query(mesh.vertices)[0].max())
assert error < .00001

# OpenSCAD uses the opposite polyhedron winding convention to this mesh.
with (OUT / 'B1-cover.scad').open('w', newline='\n') as f:
    f.write('// Exact mesh from Dara-Cover-Smooth-Crown-Test.3mf; millimeters.\n')
    f.write('// Created for this handoff. Faceted mesh CAD, not the original parametric generator.\n')
    f.write('// The reported print/preview defect is unresolved. No geometry changes here.\n')
    f.write('polyhedron(points=[\n')
    f.write(',\n'.join('[' + ','.join(format(float(x), '.17g') for x in v) + ']' for v in mesh.vertices))
    f.write('\n], faces=[\n')
    f.write(',\n'.join('[' + ','.join(str(int(x)) for x in face[::-1]) + ']' for face in mesh.faces))
    f.write('\n], convexity=10);\n')

# Preserve the actual original generator scripts and their local import closure.
pending = ['prepare_cover_crown_test', 'prepare_cover_edge_test', 'prepare_hammered_bands']
copied = set()
while pending:
    name = pending.pop()
    path = ROOT / 'scripts' / (name + '.py')
    if name in copied or not path.exists():
        continue
    copied.add(name)
    target = OUT / 'scripts' / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
        if isinstance(node, ast.ImportFrom) and node.module:
            pending.append(node.module.split('.')[0])
        elif isinstance(node, ast.Import):
            pending.extend(a.name.split('.')[0] for a in node.names)

cad = Path('working/Dara-Photo-Frame-A1-Jointed.scad')
(OUT / cad).parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(ROOT / cad, OUT / cad)
shutil.copy2(SOURCE, OUT / SOURCE.name)
cached = b.np.load(ROOT / '.work/cover-crown/B1.npz')
original = b.trimesh.Trimesh(cached['vertices'], cached['faces'], process=False)
offset = mesh.bounds.mean(axis=0) - original.bounds.mean(axis=0)
manifest = {
    'source_3mf': SOURCE.name,
    'source_3mf_sha256': b.sha(SOURCE),
    'mesh_entry': child_path,
    'units': 'millimeter',
    'status': 'Current revision supplied for inspection. Reported defect unresolved.',
    'triangles': len(mesh.faces),
    'vertices': len(mesh.vertices),
    'bounds_mm': mesh.bounds.tolist(),
    'volume_mm3': float(mesh.volume),
    'stl_export_max_vertex_error_mm': error,
    'assembly_to_export_translation_mm': offset.tolist(),
    'build_transform': b.transform(item.get('transform')).tolist(),
    'component_transform': b.transform(component.get('transform')).tolist(),
    'original_source_scripts': sorted(copied),
}
(OUT / 'export-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

wrapper = '''"""Regenerate B1 with the original geometry functions, without slicing/publishing.

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
'''
(OUT / 'generate_cover.py').write_text(wrapper)
(OUT / 'requirements.txt').write_text(
    'numpy==2.2.6\nscipy==1.15.3\nshapely==2.1.2\ntrimesh==5.1.1\nmanifold3d==3.5.4\nnetworkx==3.4.2\n')

# This is a plain-text handoff note, not a project documentation change.
(OUT / 'README.txt').write_text('''B1 COVER: EXACT CURRENT MODEL AND SOURCE

This is the latest Dara-Cover-Smooth-Crown-Test revision shown in the disputed
slicer preview. The reported defect remains unresolved. This package makes no
repair or geometry change and is not a newly validated print recommendation.

OPEN THESE FILES
  B1-cover.stl: cover mesh extracted directly from the included 3MF, with the
    same triangles. Units are millimeters. Native object coordinates are used;
    the print tilt/bed placement is NOT baked into this STL.
  B1-cover.scad: self-contained OpenSCAD polyhedron of that exact cover mesh.
    Created for this handoff. It is faceted mesh CAD, not a feature-based model.
  Dara-Cover-Smooth-Crown-Test.3mf: exact existing Bambu project, with orientation,
    settings and painted supports. STL and SCAD do not carry these settings.

ORIGINAL CODE AND CAD
  scripts/prepare_cover_crown_test.py: latest cover shape and build pipeline.
  scripts/prepare_cover_edge_test.py: footprint and original seating surface.
  scripts/prepare_hammered_bands.py: band layout, dimensions, crown and meshing.
  Other scripts/ files are the original local imports required by those files.
  working/Dara-Photo-Frame-A1-Jointed.scad: original full-project CAD/outline
    consumed by Python. This file alone DOES NOT contain the later Python-built
    hammered M and cover-band revisions. There was no STEP/Fusion/FreeCAD solid
    model of this cover; its original editable definition is the Python code.

REGENERATE THE COVER ONLY
  python -m pip install -r requirements.txt
  python generate_cover.py

generate_cover.py is a new convenience wrapper around the unchanged original
geometry functions. It writes regenerated-B1-cover.stl and compares it with
the extracted mesh. It does not alter the input 3MF or run Bambu Studio.
The old pipeline CLI scripts expect additional repository intermediates;
use this wrapper for a self-contained B1 geometry rebuild.

export-manifest.json records the source hash, geometry checks and transforms.
SHA256SUMS.txt records hashes of the files in this handoff.
''')

def archive():
    paths = sorted(p for p in OUT.rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts and p.name != 'SHA256SUMS.txt')
    hashes = [hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(OUT).as_posix() for p in paths]
    (OUT / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n')
    archive_path = OUT.with_suffix('.zip')
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in [*paths, OUT / 'SHA256SUMS.txt']:
            z.write(p, (Path(OUT.name) / p.relative_to(OUT)).as_posix())
    print(json.dumps({'archive': str(archive_path), 'files': len(paths) + 1,
                      'source_scripts': len(copied), 'manifest': manifest}, indent=2))

if __name__ == '__main__':
    archive()
