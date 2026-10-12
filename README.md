# Dara knot wall hanging

The editable feature model is [working/Dara-Photo-Frame.scad](working/Dara-Photo-Frame.scad).
The clean reference remains unchanged. The working CAD adds rear photo rabbets
to the eight outer openings, 1.6 mm removable backers, and four identical printed
sliding retainers per backer in integral rear T tracks. There are no screw holes.
The rabbets overlap the openings by 4 mm and allow 0.4 mm for a photo; backers
have 0.3 mm edge clearance. Tracks project 3.2 mm behind the original rear face,
and the slider grips project 4.5 mm. Push each slider inward to retain the backer;
pull it outward to remove it. Short tapered ribs provide friction retention.

The weave has a continuous solid CAD backing down to the rear face, allowing
the slicer to generate infill and solid skins without modeled internal partitions.
The knot retains its original outline, with no M-shaped platform underneath the
separate letter. The M is a closed, flat-bottomed solid, 10.5 mm thick.

Use `view_mode` to select `assembly`, `frame`, `M`, `exploded`, `backer`, `retainer`,
or `fit_sample`. `backer_index` selects openings 1–8, clockwise starting at the
upper opening on the left side in the front view. `retainers_open` shows the sliders withdrawn.
`frame` excludes the M and removable hardware; `M` isolates the letter with its
bottom at Z=0. `exploded` lifts the M and separates the rear hardware for inspection.
The fit sample is a CAD detail of the track, keeper, and backer edge. PLA sliding
fit is provisional until physically checked; `slide_clearance` and `lock_rib`
adjust it. Hardware dimensions are finished millimetres. This stage supplies
CAD only, without print segmentation or production exports.

The clean design reference is [reference/Dara-Clean-Reference.scad](reference/Dara-Clean-Reference.scad).
Use this as the visual baseline for future work. It is a standalone OpenSCAD file
with continuous artwork outlines and editable display/dimension parameters.

![Clean reference, front view](reference/Dara-Clean-Reference-front.png)

The reference is 914.4 x 914.4 mm (36 x 36 inches), uniformly scaled to 75% of
the original in X, Y and Z. It keeps the manuscript M, open photo areas, and
decorative fabric. It has no part seams,
joints, connectors, mounts, photo-retaining features, rear labels, fabric backing,
support walls, cross-braces, or end ties. The fabric is represented by a thin open
grid; the knot rails and M have simple solid sections. This is the design target,
before decisions about print segmentation and construction.

Open the SCAD in OpenSCAD and press F5. The top parameters toggle the knot, M,
and fabric. `fabric_style = "plain"` shows the fabric as a simple surface;
`view_mode = "drawing"` produces a flat front drawing for SVG/DXF export.
The default model has 13.5 mm knot depth, fabric at Z=9 to 9.6 mm, and the
M at Z=13.5 to 24 mm. The M follows the existing visible outline, approximately
600 x 359 mm. Fabric threads are 1.5 mm wide at 6 mm pitch and 0.6 mm thick.
`overall_width` controls uniform scaling of every part, including thicknesses
and offsets. The other dimension parameters describe the original 48-inch
master before scaling. Colours distinguish the components for review.

- [Angled view](reference/Dara-Clean-Reference-angle.png)
- [Rear view](reference/Dara-Clean-Reference-back.png)
- [Full-size vector drawing](reference/Dara-Clean-Reference-drawing.svg)
- [Source and outline processing record](reference/provenance.json)
- [Geometry verification](reference/verification.json)

The SCAD embeds native polygon outlines and needs no STL files, external fonts,
or Python installation. Keep this reference separate from future production
models. A matching review copy is saved in the existing Nextcloud package under
`CAD/Clean-Reference/`.

The optional `scripts/build_reference.py --source-package PATH` command
reconstructs the initial reference from the archived package (requires numpy,
shapely and trimesh). It uses the approved knot master and visible M face
contours, closes the M seams, and applies the channel-end and local curve
cleanup recorded in `provenance.json`. Running it overwrites the SCAD and resets
its parameters; make future design edits deliberately and regenerate previews
after changes.
