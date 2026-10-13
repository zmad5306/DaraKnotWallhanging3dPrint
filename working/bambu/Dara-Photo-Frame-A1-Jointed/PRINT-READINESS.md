# Print review - clean curves - 2026-10-13

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf). All frame edges, native clipping masks, blue boundaries and backers are rebuilt together and every plate has fresh slices. The [complete review](../../review/clean-edges/README.md) replaces the earlier local-bend assessment.

The complete frame artwork has been rebuilt from tangent straight lines and circular arcs. The earlier repair removed sharp local bends but missed broad waves. All 26 boundary loops are now reconstructed; the 31 lap trimming domains and 20 section masks are regenerated from the same continuous geometry, so the old traced edges cannot clip the cleaned curves. Fabric boundaries, blue offsets, eight photo openings and matching backers follow the same source.

The largest outline movement is 1.461 mm at a formerly irregular small corner. Small artwork corners use 1.5 mm fillets; overall bounds remain 914.4 x 914.4 mm. Every frame STL and all eight backers were regenerated. The six M, four wall-block and one retainer STL files are byte-identical to the preceding revision. Tested lap/key profiles, seam transforms, screw features, mounting interfaces, saved placements and slicer settings are preserved. Rabbets remain 2.4 mm deep, backers 1.6 mm thick, with 0.3 mm edge clearance.

The color-mask calculation also uses direct intersections with the original STL triangles. The previous 3D slicing helper could introduce a false triangular notch at an oblique weave seam. A regression check covers that location, and all wood/blue modifiers are regenerated with the corrected method. Solid-change verification checks every distinct vertex-height interval directly, avoiding the same coplanar Boolean artifact.

Plate **30** is the **68.36 x 24.00 x 13.50 mm** white/wood/blue sample. Inspect the crossing detail, smooth edges, blue opacity and clean white beside the blue. Plate **31** is the copper M sample. The earlier hardware/lap tests were printed; the revised 2.4 mm photo clearance and these surface tests do not yet have recorded physical results.

## Saved-file checks

- All 39 production STLs and both material test meshes are valid solids with matching source hashes.
- All 70 assembly pieces pass the interference check; maximum numerical overlap is 0.000236 mm3 (tolerance 0.01 mm3).
- Every frame, M and backer perimeter was compared with its CAD boundary: 34 parts, maximum boundary error 0.000033 mm.
- All 26 canonical outline loops and 320 line/arc primitives have tangent joins; maximum chord approximation is 0.001999 mm.
- Saved white/blue perimeter paths cover all 56 large circular arcs on all 20 frame plates: 348 arcs checked, maximum radial error 0.010984 mm (limit 0.06 mm).
- All 63 blue-bearing layers pass the blue-mask and white-intrusion checks. The white diamonds in Preview are seam markers, separate from extrusion paths.
- All 41 normal project meshes match the STLs within 0.0001 mm; 74 reinforcement, 21 wood and 21 blue modifiers pass validation.
- All 31 plates were re-sliced: 6,911,436 extrusion moves checked, minimum bed-edge clearance 0.634 mm, including bead widths, brim/support and towers. Custom printer purge/wipe/parking routines are excluded.

Production plates 1-29: **3,402.87 g; 126 h 49 min**. Plate 30: **18.42 g; 0 h 59 min**. Plate 31: **23.28 g; 1 h 10 min**. Total: **3,444.57 g; 128 h 59 min**. These are slicer estimates.

## Assembly supplies and order

| Purchased item | Quantity | Use |
| --- | --- | --- |
| Selected #6-19 x 1/2-inch pan-head plastic thread-forming screws | 50 | 32 tabs + 8 wall-block screws + 10 M screws |
| 10 mm OD x 4 mm ID x 1 mm washers | 10 | M screws only |
| Wall fasteners/anchors or strips appropriate to the actual wall and load | Chosen for installation | Separate from the 50 assembly screws |
| Adhesive proven on the chosen PLA and lap sample | As required | Keyed laps require a bonded assembly |

The M screw stack provides 7.7 mm engagement, 1 mm nominal tip clearance, and
1.8 mm front cover. Photo and block screws provide 9.7 mm engagement, 1 mm tip
clearance, and 2.8 mm front cover. Different screw or washer dimensions change
these clearances.

Label parts as they leave the plate. All map positions use the front view.
Dry-fit first on a flat surface, then bond following the CAD's tongue-before-socket
order; lower each socket onto the earlier tongues:

- **Frame:** F1, F2, F8, F15, F19, F20, F3, F14, F18, F11, F17, F9, F16,
  F12, F6, F7, F13, F10, F5, F4.
- **M:** M1, M6, M2, M4, M3, M5.

After the bonded assemblies have cured, seat M on the locating pins and install
its ten screws/washers from the rear. B1/B2/B3/B4 fit F3/F5/F16/F18 respectively.
Install the backers and four tabs per photo. Verify all four wall faces seat in
one plane and the photo hardware clears the wall before mounting. A digital
pass does not establish a safe load rating for the completed hanging.


## Recheck

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/audit_clean_mesh_edges.py
python scripts/validate_print_project.py
python scripts/review_curve_artifacts.py --output working/review/clean-edges/after --repaired-findings working/review/curve-artifacts/review.json
python scripts/review_clean_edges.py --project working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf --baseline working/bambu/Dara-Photo-Frame-A1-Jointed/project-validation.json
```
