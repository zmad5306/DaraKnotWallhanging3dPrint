# A2L M: short veneer seams and staggered structural joints

The production M uses five flat structural cores and three flat-backed veneers. The two short veneer seams are restored at the thin arch crowns: about 12.1 mm each, 24.3 mm total in front projection. The backing stays continuous beneath those seams.

![Actual core and veneer seam overlay](M-staggered-seam-layout.png)

The four hidden core joints remain in the broad fork, stem and lower sweeps. The nearest core and veneer seams are 116.9 mm apart, with no crossings or aligned seam runs. Core joints are at least 18 mm apart. The 18 mm mushroom keys have at least 10 mm of surrounding artwork around each head and stay clear of the veneer seams.

All five cores print flat at 8% gyroid. C1/C2 upper sections use plates 11/12, C3 stem uses plate 13, and C4/C5 lower sections share plate 14. Veneers V1/V2/V3 stay on plates 15-17: left sweep, right sweep, then central section. The project still has 20 plates. Knot and accessory plates retain their geometry and saved toolpaths. All ten M screw and eight frame-pin positions are retained.

The three veneers share the same complete 55-degree print rotation, with the show planes along bed Y. Removable carriers retain separate grounded ribs, recessed cut necks and 3 mm rear access. Surface texture and zero-gap face closure are preserved.

The specification is [staggered-layout.json](staggered-layout.json). Regenerate the M with `scripts/repartition_a2l_M.py plan`, `scripts/build_a2l_project.py M`, and `scripts/repartition_a2l_M.py package`; validate geometry and native slices before publishing. The comparison report is [evaluation.json](evaluation.json), and production checks are [M-joint-layout-validation.json](../../bambu/Dara-Photo-Frame-A2L/M-joint-layout-validation.json).
