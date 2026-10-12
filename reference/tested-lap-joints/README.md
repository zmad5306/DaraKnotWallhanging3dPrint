# Tested keyed lap joint reference

These are the exact 75% straight and curved samples that Zach reported as
"rock solid" on 2026-10-12. Preserve these as the joint baseline for the
three-foot design. Their joint profiles are now used in
[the jointed manufacturing model](../../working/Dara-Photo-Frame-A1-Jointed.scad).
The production project uses four walls and 15% infill, so this six-wall, 30%
infill test does not establish the production joints' strength.

Open [Tested-Lap-Joints.scad](Tested-Lap-Joints.scad) in OpenSCAD.
It is self-contained and embeds the tested meshes as polyhedra, with no external
imports. This is a frozen geometry reference, not a parametric joint generator.
Select `view_mode` for assembled, exploded, or separated parts; select `part`
to isolate/export a component. Display settings do not resize the tested parts.
The preview shows one M boss and washer; the print project contains two of each.

![Exploded reference](preview.png)

The exact one-plate [Bambu project](Tested-Joints-One-Plate.3mf) is stored with
Git LFS and supplies the tested print preset for the complete production project.
Individual test STL exports and the original project remain in the Nextcloud
test package: `Tests/Integrated-Joint-Mount-Tests/Three-Foot-75pct/`.

## Joint dimensions and printing

- 18 mm lap overlap, 4.8 mm lower tongue thickness, 0.75 mm shoulder radius.
- Two rounded registration keys per joint, with nominal 0.15 mm hidden clearance.
- Nominal visible seam clearance 0.075 mm.
- Samples uniformly scaled to 75% in XYZ from the original four-foot tests;
  thickness is approximately 14.1 mm. Do not scale again when reusing them.
- Six wall loops, 30% gyroid infill, 0.2 mm layers, four bottom layers.
- Local 100% modifiers only around screw seats and M bosses; lap tongues and
  roots use the normal body settings. Yellow modifier regions are not printed
  as extra blocks. Use the archived 3MF to retain supports and modifiers.
- Slicer estimate: 112.6 g including supports, approximately 4 h 20 min.

## M attachment details

Hardware dimensions were retained when shrinking the joint samples: 12 mm
rear counterbore, 4 mm clearance hole and 1.6 mm screw-seat skin. Each M boss
has a centered 3.175 mm pilot, 12 mm deep, for the selected #6-19 x 1/2-inch
pan-head plastic thread-forming screw. Boss exterior is 10 mm diameter with
14 mm projection from a 3 mm base. Washer is 1 mm thick, 10 mm OD, 4 mm ID.
The straight sample's seat was moved inward to preserve surrounding material.

The user confirmed joint rigidity. Screw grip, adhesive choice, durability and
full-frame loading were not separately confirmed by that report. Keep this
qualification when reusing this reference.

## Verification and provenance

All six mesh types are watertight, single connected solids with positive volume.
Both pairs have no volumetric interference at their documented assembly offsets.
OpenSCAD preview was visually reviewed; a straight-tongue export matches source
volume within 0.01 cubic mm. See [verification.json](verification.json),
[provenance.json](provenance.json) and [slicing.json](slicing.json).
The assembly offsets restore the source sample alignment rather than positioning
parts by visual approximation. Existing clean reference and working CAD remain
separate from this archived, physically tested joint design.
