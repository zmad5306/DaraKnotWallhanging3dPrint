# Complete A1 print project - clean curves

**Copper finish update, 2026-10-14:** the current project includes the SUNLU Silk 2.0 Copper Red trial on plates 21-26 and 31. Print plate 31 first: **24.81 g, 1 h 29 min**. All seven copper plates were re-sliced and the complete project was audited. [Trial settings and checks](silk-finish-trial.json). The user reports that the test print is looking good so far; the completed-print result is pending.

[Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) contains the corrected native models and fresh saved slices for **72 pieces on 31 plates**. This supersedes the earlier local curve repair. Use Git LFS after cloning to retrieve the binary files.

The complete frame artwork has been rebuilt from tangent straight lines and circular arcs. The earlier repair removed sharp local bends but missed broad waves. All 26 boundary loops are now reconstructed; the 31 lap trimming domains and 20 section masks are regenerated from the same continuous geometry, so the old traced edges cannot clip the cleaned curves. Fabric boundaries, blue offsets, eight photo openings and matching backers follow the same source.

The largest outline movement is 1.461 mm at a formerly irregular small corner. Small artwork corners use 1.5 mm fillets; overall bounds remain 914.4 x 914.4 mm. Every frame STL and all eight backers were regenerated. The six M, four wall-block and one retainer STL files are byte-identical to the preceding revision. Tested lap/key profiles, seam transforms, screw features, mounting interfaces, saved placements and slicer settings are preserved. Rabbets remain 2.4 mm deep, backers 1.6 mm thick, with 0.3 mm edge clearance.

The color-mask calculation also uses direct intersections with the original STL triangles. The previous 3D slicing helper could introduce a false triangular notch at an oblique weave seam. A regression check covers that location, and all wood/blue modifiers are regenerated with the corrected method. Solid-change verification checks every distinct vertex-height interval directly, avoiding the same coplanar Boolean artifact.

| Plates | Contents |
| --- | --- |
| 01-20 | F1-F20, one frame section per plate |
| 21-26 | M1-M6, one copper section per plate |
| 27 | Backer1, Backer3, Backer5, Backer7 |
| 28 | Backer2, Backer4, Backer6, Backer8 |
| 29 | B1-B4 and 32 retainers |
| 30 | White/wood/blue weave and edge sample |
| 31 | Copper M sample |

[Part and plate map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf). [Assembly guide](PRINT-READINESS.md). [Full edge review](../../review/clean-edges/README.md).

## Saved geometry and settings

The 3MF retains all colors and modifiers. STL files contain geometry only. Slot order: **1 white Generic PLA / 2 wood tan Generic PLA / 3 copper Generic PLA Silk / 4 Azurite blue Generic PLA**. Match these to the loaded AMS Lite spools.

A1, 0.4 mm nozzle, textured plate, 0.2 mm layers, four walls, 15% gyroid, with 74 local solid screw/mounting zones. Nozzle 220 C; white/wood/blue plates use a 65 C bed, copper plates 55 C. Copper uses 40 mm/s outer walls, 30 mm/s top surfaces, 50 mm/s internal solid infill, eight top layers and 1.6 mm minimum top thickness. Its trial flow ratio is 0.96, with 0.6 mm Normal Lift and sideways pre-lift wipe disabled. Monotonic line and no ironing are retained. Copper/blue maximum volumetric flow remains 7.5 mm3/s. Rear-down placements and scale are retained. Backers use no brim/support; tight frame/M plates retain the 1 mm brim. Flushing into models is disabled.

The weave has 3.3 x 1.5 mm crossing pads, raised 0.3 mm above the 0.6 mm grid. Wood modifiers follow the actual relief at Z=8.4-9.9 mm, layers 43-50. The flush blue line is 1.5 mm wide with a 1.25 mm white land from the weave; its modifier is Z=12.9-13.5 mm, sliced on layers 66-68 at heights 13.2/13.4/13.6 mm. Wood and blue do not share a layer. Blue-to-white flush remains 650 mm3.

There are 11 filament changes per ordinary frame/test plate, or 12 on sections with taller white locating pins. Plate 31 is copper only. The color modifiers have been rebuilt from the clean continuous outline before section clipping; they do not follow manufacturing seams.

## Saved-file checks

- All 39 production STLs and both material test meshes are valid solids with matching source hashes.
- All 70 assembly pieces pass the interference check; maximum numerical overlap is 0.000236 mm3 (tolerance 0.01 mm3).
- Every frame, M and backer perimeter was compared with its CAD boundary: 34 parts, maximum boundary error 0.000033 mm.
- All 26 canonical outline loops and 320 line/arc primitives have tangent joins; maximum chord approximation is 0.001999 mm.
- Saved white/blue perimeter paths cover all 56 large circular arcs on all 20 frame plates: 348 arcs checked, maximum radial error 0.010984 mm (limit 0.06 mm).
- All 63 blue-bearing layers pass the blue-mask and white-intrusion checks. The white diamonds in Preview are seam markers, separate from extrusion paths.
- All 41 normal project meshes match the STLs within 0.0001 mm; 74 reinforcement, 21 wood and 21 blue modifiers pass validation.
- Seven copper plates were re-sliced for the finish trial; the other 24 plates retain their prior slices. All 31 plates were audited: 6,867,463 extrusion moves checked, minimum bed-edge clearance 0.634 mm, including bead widths, brim/support and towers. Custom printer purge/wipe/parking routines are excluded.

| Material | All 31 plates, including support/purge |
| --- | ---: |
| White | 2,761.10 g |
| Wood tan | 222.30 g |
| Copper silk | 473.85 g |
| Azurite blue | 28.67 g |

Production plates 1-29: **3,442.69 g; 133 h 58 min**. Plate 30: **18.42 g; 0 h 59 min**. Plate 31: **24.81 g; 1 h 29 min**. Total: **3,485.92 g; 136 h 26 min**. These are slicer estimates.

[project-validation.json](project-validation.json) records settings, placement and slice provenance. [final-review.json](final-review.json) is the independent audit. Plate 30 (68.36 x 24.00 x 13.50 mm) is the physical finish/purge test. The digital pass is not a physical print result. If Bambu asks to regenerate Preview, use Slice all with the saved settings.

## Rebuilding

See the [complete edge rebuild sequence](../../review/clean-edges/README.md#rebuilding). Historical weave/rabbet/local-repair scripts describe earlier revisions.
