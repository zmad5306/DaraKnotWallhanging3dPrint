# Curve artifact review — 2026-10-13

**Historical review of the pre-repair project. All 12 findings below are now corrected in the current production file.** See the [completed repair and final checks](../curve-repair/README.md). The evidence below retains the original defects for comparison.

**Cosmetic review failed: 12 abrupt curve bends on plates 1, 2, 6, 8, 13, 15, and 19.** Five are on fabric-facing boundaries and propagate into the blue edging. The other seven are on the outside white outline. These are present in the CAD, STL vertices, and saved extrusion paths. They are not invalid meshes, so the preceding integrity audit did not flag them.

This review initially left the production CAD, STL, and 3MF files unchanged; the subsequent repair supersedes that version. See the original [assembly location map](assembly-findings.png), [source close-ups](curve-findings.png), and [machine-readable measurements](review.json).

## Plate-one screenshot

C01 is the kink in the reported curve. The original outline changes direction by **14.74 degrees** at assembled XY **(-160.7955, 420.74925) mm**, corresponding to plate-one bed XY **(39.1130, 113.4588) mm**. The vertex is 0.224 mm from the chord between its neighboring vertices; that measures the local bend, not the displacement required for a repair. The blue modifier offsets the same boundary, so the bend appears in the blue line and adjoining white rail. [The actual saved top-layer paths show it without any seam markers](C01-toolpath.png).

The small white diamonds in the screenshot are Bambu Studio's **Seams** visualization. The preview legend identifies them as white, and toggling Seams hides them. Bambu's [renderer source](https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/GCodeRenderer/LegacyRenderer.cpp) implements these as separate diamond symbols, independently of extrusion colors. They indicate starts/ends of perimeter loops; they do not command white filament there. A physical seam can still leave a small surface mark. This project uses aligned seams, a 15% seam gap, and no scarf seam.

## Confirmed curve locations

Coordinates below are printer-bed XY, in mm. Plate number and frame part number match for plates 1–20.

| ID / saved toolpath detail | Plate / part | Edge | Abrupt turn | Bed XY |
| --- | --- | --- | ---: | --- |
| [C01](C01-toolpath.png) | 1 / F1 | Fabric / blue | 14.74° | 39.11, 113.46 |
| [C02](C02-toolpath.png) | 1 / F1 | Outside white | 8.42° | 18.65, 104.67 |
| [C03](C03-toolpath.png) | 2 / F2 | Fabric / blue | 8.18° | 94.65, 187.28 |
| [C04](C04-toolpath.png) | 2 / F2 | Fabric / blue | 10.90° | 169.75, 192.20 |
| [C05](C05-toolpath.png) | 2 / F2 | Outside white | 18.62° | 13.60, 85.65 |
| [C06](C06-toolpath.png) | 6 / F6 | Outside white | 8.55° | 21.75, 161.16 |
| [C07](C07-toolpath.png) | 8 / F8 | Fabric / blue | 7.99° | 103.58, 221.51 |
| [C08](C08-toolpath.png) | 8 / F8 | Outside white | 8.47° | 195.76, 197.34 |
| [C09](C09-toolpath.png) | 13 / F13 | Outside white | 8.50° | 88.93, 32.94 |
| [C10](C10-toolpath.png) | 15 / F15 | Fabric / blue | 11.28° | 202.74, 91.36 |
| [C11](C11-toolpath.png) | 15 / F15 | Outside white | 18.65° | 102.82, 251.84 |
| [C12](C12-toolpath.png) | 19 / F19 | Outside white | 18.62° | 251.93, 150.08 |

These are inherited artwork defects. The current knot outline and the frozen clean reference have **0 mm² symmetric difference**. The blue-edge addition reveals the existing bends rather than introducing a new mismatch. All twelve locations match vertices in their production STLs to better than 0.001 mm; the separate integrity review also verifies the embedded 3MF meshes against those STLs.

## Coverage and results

- Re-ran the existing integrity audit across **31 plates, 41 distinct meshes, and 72 placed pieces**. Source hashes, assembled interference, placement, 74 reinforcement modifiers, 42 color modifiers, and **7,356,694 extrusion moves** pass those checks. The minimum computed bed-edge clearance remains 0.673 mm. [Fresh integrity report](integrity-review.json).
- Screened **6,668 source outline vertices**: 3,868 knot, 1,917 fabric, and 883 letter vertices. The fabric candidates duplicate five knot-boundary defects. The letter candidate at (-227.394, -179.36775) is an intentional straight-to-diagonal glyph corner, not the same kind of curve kink.
- Parsed the saved motion on **all 31 plates** independently: **7,157,551 model extrusion moves**, including 3,460,106 arcs. This smaller move count excludes supports, brims, and purge towers included in the bed-boundary audit.
- Checked blue and white paths on **all three blue layers of all 21 blue-bearing plates**: 13.2, 13.4, and 13.6 mm (slicer layer tops). **44,633 blue extrusion moves** remain inside their intended masks; maximum sampled centerline excursion is 0 mm. Complete line/arc approximations also have zero length outside a 0.03 mm mask tolerance.
- Checked **171,993 white extrusion moves** on those layers. Their centerlines have **zero length inside the blue core**, defined as the blue mask inset by 0.3 mm. This rules out white toolpaths crossing the interior of the stripe; it does not model molten-bead spreading or color contamination.
- Inspected the generated surface overviews for frame plates **1–20 and the weave sample on 30**, plus close-ups of the twelve findings. Each `plate-NN-surface.png` is drawn from saved G-code, without seam symbols. Wood is shown at its final crossing-pad layer; lower visible weave layers are intentionally absent from these diagnostic plots.
- **11 unit tests pass**, covering the existing bounds scanner and the new curvature/motion checks.

No additional isolated curve bends above the stated screening threshold were found in the remaining frame sections. This is not an artifact-free certification: the screening rule finds turns greater than 6° where the total absolute turn within ±5 mm of arc length is at most 45°. Designed corners and small-radius fillets are excluded, and smaller deviations may remain. A secondary 3° sensitivity scan produced ordinary tessellation/curve samples in addition to these locations; it was not used as a pass/fail criterion. Physical extrusion quality is untested.

## Original repair recommendation — now completed

Smooth the twelve local bends in the working artwork while preserving the intended silhouette and rail widths. At the five shared fabric boundaries, update the knot and fabric outlines together. Keep the frozen reference as provenance. Then regenerate affected frame meshes and wood/blue modifiers, re-slice the changed plates, and repeat both the integrity and cosmetic reviews. Hiding seam markers or changing seam placement does not repair the underlying curves.

The commands below were used against the original files. They are retained as history; use the current repair record's recheck commands to avoid replacing this original evidence.

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/validate_print_project.py --report working/review/curve-artifacts/integrity-review.json
python scripts/review_curve_artifacts.py
```

The original curve report records `cosmetic_review_passed: false`. The script is a review generator and returns normally when it successfully produces a report, even when defects are present. The current repaired project has a separate passing report.
