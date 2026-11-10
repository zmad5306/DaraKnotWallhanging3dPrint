# A2L Poop Bucket

A single-gray bucket with a plain triangular front, full-height back and rear
walls, a rising pillar wall and a catch chute.

![A2L Poop Bucket](preview.png)

## Files

- [Bambu Studio project](A2L-Poop-Bucket-SUNLU-PLA-Plus-2.0.3mf) — open as a project.
- [Standalone parametric CAD](Bucket.scad) — no external meshes or libraries.
- [STL](Bucket.stl) — one closed body, with no logo or separate color parts.

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
| Estimate | 6 h 46 min; 289.4 g including supports |

## Dimensions

The body is 110 x 255 x 160.804 mm. The complete envelope including the chute
is 132.296 x 255 x 160.804 mm. Floor thickness is 1.98 mm and walls are 2 mm.

The printer-facing wall and chute use dimensions measured from the reference
bucket the owner reports fits: 58.026 mm exposed wall below the chute,
22.296 mm projection, 64.016 mm upper edge and 62.348 mm lower edge at the tip.
The root joins the inside wall without an inward shelf. The earlier 18 mm,
8 mm-rise chute is superseded. The front logo and its material partition are removed.

The pillar interface remains 41.275 mm front reach, 15.621 mm rear return,
49.6568 mm nominal gap, 15.08125 mm (19/32 inch) inside curves and a 12.7 mm
(1/2 inch) convex rear tip. The enlarged body and its existing placement are retained.

## Verification

OpenSCAD exports one closed body. The wall/chute section matches the source
dimensions; its maximum deviation from the measured reference section is
0.084 mm at rounded transitions. Geometry outside the chute matches the
accepted unmarked body. Both native slicing and reopening show zero support
extrusions inside the collection cavity, zero color changes and no purge tower.
The saved material parameters are retained from gray slot 1 of the prior project.

See [validation.json](validation.json) and the [reference dimensions](reference/printer-chute-dimensions.json).
The owner reports that the reference bucket fits. A physical print of this
single-color bucket has not yet been observed.

`build_project.py` rebuilds from this CAD and `reference/current-project-settings.json`.
Historical two-color evidence remains in `history/`. The Bambu PLA Basic
publication package is maintained outside this repository.
