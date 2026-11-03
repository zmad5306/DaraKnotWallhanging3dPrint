> Promoted to the main [Letter.3mf](../../Letter.3mf). Use that file. This separate candidate is historical; see the [current validation](../../release/letter-veneer-correction/README.md).

# Letter Veneers

Open **[Letter Veneers.3mf](<Letter Veneers.3mf>) as a project**. This is the current correction candidate, with the production A2L printer profile and all three full-size veneers. Names describe the assembled letter viewed from the front; they contain no version numbers.

| Plate | Name | Estimated time | Material including supports |
|---|---|---:|---:|
| 1 | Left letter veneer | 25h 42m | 332.06 g |
| 2 | Right letter veneer | 24h 52m | 317.22 g |
| 3 | Center letter veneer | 21h 04m | 254.82 g |

Combined material is **904.10 g**, below the 1,000 g limit. Adjacent SCAD/STL files match this project. Use the 3MF to retain settings, support paint and poses.

The root `Letter.3mf` now uses the same meaningful veneer names on its selector plates 4–6. That root change is **names only**: its six stored G-code files, geometry, settings and poses remain byte-identical. The corrections below are in this separate `Letter Veneers.3mf`, not the root six-plate project.

## Corrections and inspection

- The left carrier's 0.15 mm end step near Z138.4–138.8 is replaced by a continuous taper. Two comparable near-bed steps on the center carrier are corrected. The right carrier had no corresponding step. Decorative faces, original veneer edges, fused connections, wall thicknesses, end bands, support paint and saved orientations remain intact.
- Project-level printing/travel acceleration is limited to **1,500/2,500 mm/s²**. The old object-level limits were ineffective in native output. These settings are isolated in the separate veneer project to preserve the core plates.
- The user's spool limits govern all three slices: **220°C printing nozzle, 55°C Textured PEI bed and 30–60 mm/s commanded model/support extrusion**. Startup flushing is also 220°C. All extrusion commands were audited with zero range violations. Non-extruding travel, priming/calibration, the saved 140°C probing routine and off commands are separate.
- Outer-wall setting remains 40 mm/s; infill, inner-wall and support settings cap at 60. Cooling slowdown, small-perimeter and severe-overhang minimums are 30. Saved fan values, 0.98 flow, 7.5 mm³/s volumetric limit and retraction remain unchanged.
- All three veneers have 1,469 inspected decorative-face layers, Z3.6–297.2, with no missing 0.20 mm layers. Exact mesh-section comparisons found no broad face displacement. Both carrier ends were traced throughout their heights. Top/bottom transition outliers were checked against the complete mesh: they are perimeter closures or the end of a narrowing tip, rather than a whole-wall translation. The [inspection plot](all-veneer-continuity.png), [transition plot](carrier-end-transitions.png) and JSON records retain the measurements.
- All three slices were generated successfully by Bambu Studio 02.08.02.61 before the name-only change. Bed bounds, checksums, all 102 moved edge connections and the requested extrusion limits passed. Renaming preserved the complete native G-code files exactly. The named project then passed native reopen/export with exit 0: all three names survived, geometry differed by 0 mm, and settings, paint and poses matched. This verification ran outside the restricted sandbox after its startup restrictions prevented the earlier attempts. No interactive UI reopen is claimed.

The 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers, solid veneer/carrier overrides, gyroid pattern, tree supports, bed bands and shared 55-degree orientation remain saved. No printer job was sent.

## Physical evidence

The user reports the failure on **Plate 5 of Letter** and has not printed or inspected the other veneers. The former selector/name conflict is retained in the evidence: selector 4 was named “5 - V1,” while selector 5 was named “6 - V2.” The photos show a reported whole-part/carrier shift, including both ends of the printed wall, photographed from the printer's right side. The exact printed file hash was not independently obtained.

**The physical whole-part shift remains unexplained.** The carrier-edge and speed/acceleration corrections do not prove that this failure is resolved. This candidate has no physical result; its full-size stability, finish and changed bridge/overhang behavior remain unqualified.

Current project SHA-256: `6bcfc5bbc39382607d28d6a840f66e96b66051d22ca4df30ca41900f99c468f1`.

`validation.json` contains settings, native command checks, poses and provenance; `name-preservation.json` proves the names-only packaging change. Earlier numbered candidates are historical and superseded by this filename.
