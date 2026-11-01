# Letter plate 5 rear-brace correction

The user reported a support-to-back-wall gap and clarified that the affected
plate is **5, Right letter veneer**. Inspection of the saved production mesh
confirmed that both connecting braces receded from the vertical rear wall.
The larger gap was about 14.5 mm at print height Z240 mm. This was modeled
geometry, not merely a preview artifact or a tree-support setting.

The correction adds stock only along the two receding edges, connecting them
to the rear-wall center plane X56.687525719 mm in plate coordinates. Both
braces retain their 1.00 mm thickness and original maximum heights. The
original stock, openings, decorative veneer, fused necks, bed bands, poses,
support paint on surviving source surfaces, and all saved printing settings
are preserved. Boolean face provenance carries the original support paint
onto retained and subdivided source faces. New faces use the existing
normal-based paint rule.

Plate 5 has a fresh Bambu Studio slice. Actual nominal extrusion footprints
connect the rear wall to the existing brace on every checked full-height
layer: 1,346 layers for the first brace and 1,456 for the second, from Z0.8 mm
to within 0.3 mm of each brace tip. Checks include nominal bead widths and a
0.002 mm numerical tolerance; they do not measure physical fusion strength.
The native project reopens with matching geometry, support paint, settings,
and poses. Plates 1/2/3/4/6 retain their original stored print assets.

Total saved veneer and support material is **906.44 g** for plates 4–6.
The corrected main `Letter.3mf`, adjacent Right veneer STL, and release
catalog are synchronized. `Letter.scad` retains its existing STL reference.
Earlier release evidence describes earlier hashes and remains historical.

See `validation.json` for source/output hashes, native validation, layer
checks, and material totals; `geometry.json` records the exact added masks.
The repair adds 2,029.23 mm³ and removes no original stock within numerical
boolean tolerance. `join-correction.png` shows three mesh cross sections.

No physical print of this correction has been observed. The previously
reported whole-part shift remains unexplained. No print job was sent.
