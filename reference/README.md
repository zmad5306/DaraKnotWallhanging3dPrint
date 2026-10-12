# Dara — clean design reference

Open Dara-Clean-Reference.scad in OpenSCAD and press F5.
This one file is self-contained and can be moved or copied on its own.

The reference is 36 x 36 inches (914.4 x 914.4 mm), scaled to 75% of the
48-inch master in X, Y and Z. It retains the knot, manuscript M, open photo
areas and decorative fabric. It is a continuous theoretical design with simple
sections. There are no part seams, joints, mounts, fabric backing, lower
support walls, braces, or end ties.

The fabric is a schematic open grid, 1.5 mm threads at 6 mm pitch and 0.6 mm
thick. The top parameters can hide it or show a plain surface. They also
control overall size, component visibility, depth and reference colours.

Default depths: knot Z=0 to 13.5 mm, fabric Z=9 to 9.6 mm, M Z=13.5 to 24 mm.
overall_width controls uniform scaling of all parts, thicknesses and offsets.
The other dimension parameters describe the 48-inch master before scaling.
Set view_mode to "drawing" for a flat front drawing suitable for SVG export.

The front, angle and back PNGs are direct OpenSCAD previews. The SVG is the
full-size flat drawing. provenance.json records source hashes and outline
cleanup; verification.json records the full geometry checks.

Keep this as the design baseline for the next stage. Develop manufacturing
features in a separate model. The existing production package is separate.
