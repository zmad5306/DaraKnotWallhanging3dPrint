# Individual jointed-frame STL exports

Generated from [Dara-Photo-Frame-A1-Jointed.scad](../../Dara-Photo-Frame-A1-Jointed.scad)
at its saved defaults: 914.4 mm overall width, woven frame surface, keyed lap
joints, M mounting holes and locating pins, photo screw pilots, and wall-block
slots. These are binary STL files in **millimetres**. The frame exports include restored alternating
3.3 x 1.5 mm crossing pads, 0.3 mm above the thread grid. The joints and
hardware interfaces retain their dimensions; M and accessory STLs are unchanged.
Photo rabbets are now 2.4 mm deep, leaving 0.8 mm for a photo and surface
clearance beyond the existing 1.6 mm backer. This adds 0.4 mm to accommodate
the reported clearance issue and possible support roughness.

| Files | Part | Print quantity |
| --- | --- | --- |
| `F1.stl`–`F20.stl` | Frame sections | 1 each |
| `M1.stl`–`M6.stl` | Letter sections | 1 each |
| `Backer1.stl`–`Backer8.stl` | Photo backers | 1 each |
| `B1.stl`–`B4.stl` | Keyed wall blocks | 1 each |
| `Retainer.stl` | Universal rotating photo tab | 32 |

There are **39 distinct STL files and 70 printed pieces** for one assembly.
Backer numbers match the CAD's `backer_index`: clockwise from the upper opening
on the left side, viewed from the front. B1/B2 are upper left/right and B3/B4
lower left/right in that same front view. Their matching frame sections are
F3, F5, F16, and F18, respectively. Screws and the reference M-mount washers
are purchased hardware. Fit-test coupons and assembly/detail views are not
assembly parts and are not included in this set.

Frame and letter sections retain the CAD's saved flat rotations and rear-down
placements. Backers lie flat; wall blocks have their flat wall faces down and
keys up. Every file contains one connected solid at Z=0. Centre each part on
its own print bed without changing its scale. The exports do not include
slicer settings, supports, or brims.

[manifest.json](manifest.json) records the source SHA-256, OpenSCAD version,
per-part selectors, STL SHA-256 hashes, sizes, triangle counts, volumes, and
validation results. Validation requires a single watertight solid with
consistent winding and positive volume, Z=0 placement, and at least 1.5 mm
of clearance to the edge of a centred 256 mm bed (0.001 mm numerical tolerance).
The files use the native CAD geometry, with the embedded preview cache disabled.

To regenerate from the repository root, with OpenSCAD, Python, numpy, and
trimesh installed:

```powershell
python scripts/export_jointed_stls.py
```

Use `--openscad "path/to/openscad.exe"` if it is not on PATH or in the default
Windows installation directory, and `--jobs 3` to set render concurrency.
Temporary meshes and render logs go in ignored `.work/stl-export/`.

STL files are tracked through the root `.gitattributes` Git LFS rule. The root
`.gitignore` explicitly permits this production export folder. With Git LFS
installed, normal `git add` stores pointers in Git and the binary meshes in LFS;
after cloning, use `git lfs pull` to retrieve the meshes.
