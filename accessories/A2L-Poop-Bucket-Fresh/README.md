# A2L Poop Bucket

A single-gray bucket with a plain triangular front, full-height back and rear
walls, a rising pillar wall and a catch chute.

![A2L Poop Bucket](preview.png)

## Files

- [Bambu Studio project](A2L-Poop-Bucket-SUNLU-PLA-Plus-2.0.3mf) â€” open as a project.
- [Standalone parametric CAD](Bucket.scad) â€” no external meshes or libraries.
- [STL](Bucket.stl) â€” one closed body, with no logo or separate color parts.

## Printing

| Setting | Saved value |
| --- | --- |
| Printer | Bambu Lab A2L, 0.4 mm nozzle |
| Material | SUNLU PLA+ 2.0, one gray slot #555555 |
| Nozzle / Textured PEI bed | 220 C / 65 C |
| Flow / maximum volumetric speed | 1.0 / 22 mm3/s |
| Layers | 0.20 mm, including the first layer |
| Walls / top / bottom | 4 / 5 / 5 |
| Infill | 8% gyroid |
| Supports | Automatic trees, default style, build plate only |
| Adhesion | Automatic brim |
| Purge tower / color changes | Disabled / zero |
| Estimate | 6 h 52 min; 292.8 g including supports |

## Dimensions

The body is 110 x 255 x 160.804 mm. The complete envelope including the chute
is 132.296 x 255 x 160.804 mm. Floor thickness is 1.98 mm and walls are 2 mm.

The printer housing measures **2.464 inches / 62.5856 mm** from the tabletop.
The chute underside begins at **2.504 inches / 63.6 mm**, leaving **0.040 inches /
1.0144 mm** nominal vertical clearance through the transition. The complete
chute is raised 5.574 mm while retaining its slope, thickness and 22.296 mm
projection. Its upper outer edge is **2.740 inches / 69.59 mm**; the lower edge
is 67.922 mm high. The root remains flush with the collection wall.
These mounting heights use the owner's measurement; the earlier reference
bucket height is historical.

The pillar interface remains 41.275 mm front reach, 15.621 mm rear return,
49.6568 mm nominal gap, 15.08125 mm (19/32 inch) inside curves and a 12.7 mm
(1/2 inch) convex rear tip. The enlarged body and its existing placement are retained.

## Verification

OpenSCAD exports one closed body. The complete external underside, including
the transition, clears the supplied housing height by at least 1 mm. Five
cross-sections verify that the chute is translated vertically with its slope
and thickness retained; the wall beneath it is extended. Geometry outside the
chute matches the accepted unmarked body. Native slicing and reopening show
zero support extrusion inside the cavity, zero color changes and no purge tower.
All saved print and material settings match the preceding single-gray project.

See [validation.json](validation.json) and the [printer clearance](reference/printer-clearance.json).
A physical print and fit check of this raised-chute revision have not yet been observed.

`build_project.py` rebuilds from this CAD and `reference/current-project-settings.json`.
Historical two-color evidence remains in `history/`. The Bambu PLA Basic
publication package is maintained outside this repository.
