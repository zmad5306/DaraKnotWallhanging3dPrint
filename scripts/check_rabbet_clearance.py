"""Verify the deeper rabbet and unchanged geometry outside its depth band."""
import argparse
import json
from pathlib import Path
from build_jointed_bambu_project import ROOT
from check_weave_restoration import symmetric_volume
from validate_print_project import digest
import numpy as np
import trimesh


def floors(mesh, z):
    horizontal = (mesh.face_normals[:, 2] < -.99) & np.all(abs(mesh.triangles[:, :, 2]-z) < 1e-4, axis=1)
    return float(mesh.area_faces[horizontal].sum())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--original-stls', type=Path, default=ROOT/'.work/rabbet-clearance/original-stls')
    ap.add_argument('--report', type=Path, default=ROOT/'working/review/rabbet-clearance/geometry-verification.json')
    args = ap.parse_args()
    records = []
    for i in range(1, 21):
        name = f'F{i}'
        old_path = args.original_stls/(name+'.stl')
        new_path = ROOT/f'working/stl/Dara-Photo-Frame-A1-Jointed/{name}.stl'
        old, new = trimesh.load_mesh(old_path), trimesh.load_mesh(new_path)
        old_area, new_area = floors(old, 2), floors(new, 2.4)
        assert old_area > 1 and abs(old_area-new_area) < .02, (name, old_area, new_area)
        removed = old.volume-new.volume
        assert abs(removed-old_area*.4) < .03, (name, removed, old_area*.4)
        added = abs(trimesh.boolean.difference([new, old], engine='manifold').volume)
        assert added < .02, (name, added)
        errors = []
        for low, high in ((0, 1.998), (2.402, 30)):
            clip = trimesh.creation.box(extents=[600,600,high-low])
            clip.apply_translation([0,0,(high+low)/2])
            a = trimesh.boolean.intersection([old,clip], engine='manifold')
            b = trimesh.boolean.intersection([new,clip], engine='manifold')
            errors.append(symmetric_volume(a,b))
        assert max(errors) < .02, (name, errors)
        records.append(dict(part=name, old_sha256=digest(old_path), sha256=digest(new_path),
            old_floor_z_mm=2, floor_z_mm=2.4, floor_area_mm2=new_area,
            removed_volume_mm3=removed, expected_removed_volume_mm3=old_area*.4,
            added_volume_mm3=added, unchanged_band_errors_mm3=errors))
        print(f'{name}: rabbet 2.4 mm; other surfaces unchanged', flush=True)
    report = dict(all_passed=True, old_depth_mm=2, depth_mm=2.4, backer_thickness_mm=1.6,
        photo_and_surface_allowance_mm=.8, source_sha256=digest(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'),
        unchanged_bands_mm=[[0,1.998],[2.402,30]], numerical_tolerance_mm3=.02, parts=records)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
