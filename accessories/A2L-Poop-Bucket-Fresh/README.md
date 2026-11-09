# A2L poop bucket

Current fresh parametric design, approved November 9, 2026. A gray bucket with a
green Bambu mark, triangular front wall, full-height back and rear walls, a
pillar wall that rises toward the back, and a chute that slopes into the bucket.

![Gray bucket with green front logo](preview.png)

## Files

- [Bambu Studio project](A2L-Poop-Bucket-SUNLU-PLA-Plus-2.0.3mf) — open **as a project**
  to retain colors, printer, supports and settings. Slot 1 is gray; slot 2 green.
- [Standalone parametric CAD](Bucket.scad) — no external geometry or library imports.
- [Combined STL](Bucket.stl) — closed single solid with the raised logo; STL does not store colors.
- [Gray body STL](Gray-Body.stl) and [green logo STL](Green-Logo.stl) — matching coordinates;
  import together as parts of one object if rebuilding the color project.

## Printing

| Setting | Saved value |
| --- | --- |
| Printer | Bambu Lab A2L, 0.4 mm nozzle |
| Material, both colors | SUNLU PLA+ 2.0, embedded A2L project adaptation |
| Colors | 1 gray `#555555`; 2 green `#00CC00` |
| Nozzle / Textured PEI bed | 220 C / 65 C, first and subsequent layers |
| Flow / maximum volumetric speed | 1.0 / 22 mm3/s |
| Layers | 0.20 mm, including the first layer |
| Walls / top / bottom | 4 / 5 / 5 |
| Infill | 8% gyroid |
| Supports | Automatic trees, default style |
| Adhesion / color changes | Automatic brim; prime tower enabled |
| Estimate | 10 h 38 min; 316.1 g gray + 28.7 g green = 344.7 g |

The estimate includes supports, color changes and the purge tower. Map the two
project colors to the desired loaded spools when sending the print. No live AMS
slot assignment or print command was sent.

The installed SUNLU PLA+ 2.0 material settings supply the flow, density,
temperature and volumetric values. A2L-specific start G-code, fast flush,
pre-start fan, overhang cooling threshold, engineering-plate and retraction
fields come from the saved A2L profile. Both color slots use identical settings.
The exact source snapshots and adapted profile are in `reference/`. Local
presets were not altered, and no new material calibration is implied.

## Geometry and source

The approved r3 body remains unchanged except for the requested logo material
split and 0.4 mm front relief. Body dimensions are 110 x 255 x 160.804 mm;
the complete envelope, including chute and logo, is **128 x 255.4 x 160.804 mm**.
The 32 mm tall logo is embedded 0.8 mm into the front wall. Floor and wall
thicknesses are 1.98 mm and 2 mm.

Functional interface dimensions remain 41.275 mm front reach, 15.621 mm rear
return, 49.6568 mm pillar gap, 15.08125 mm (19/32 inch) inside radius and 12.7 mm
(1/2 inch) convex tip radius. Chute projection/rise are 18/8 mm at a 58 mm root.

The shell is constructed from fresh parametric polygons, offsets and extrusions.
No prior downloaded/remixed bucket mesh is imported or traced. The Bambu mark
is transcribed from the vector bundled with Bambu Studio; it is Bambu Lab's
brand mark, not original artwork claimed by this project. The archived r3 CAD
and provenance record are in `reference/`. The earlier accessory and old listing
covers depict a different, historical design.

CAD `Assembly` preview displays the finished colors. F6/export produces the
exact solid or selected color part. Quick `GrayBody` preview shows the intact
wall to avoid an OpenCSG preview defect; F6 exports its actual logo recess.

## Verification

Native OpenSCAD exports form a closed body. The final silhouette equals the
approved r3 body plus the front mark; color parts have no volume overlap.
Bambu Studio 02.09.01.70 sliced and reopened the saved project successfully,
with actual tree generation and both material assignments retained. Sliced
beads, including the tower and supports, stay at least **18.784 mm** from the
A2L bed edges. The native export is retained without repacking its metadata.
See [validation.json](validation.json) for hashes, settings and checks.

Full-bucket physical fit, printer movement clearance, color finish and support
removal have not been observed. Design approval does not establish a successful
full-size print.

`build_project.py` packages the fresh CAD exports and verifies the native project.
The seven Dara root projects and historical bucket geometry/projects are unchanged.
