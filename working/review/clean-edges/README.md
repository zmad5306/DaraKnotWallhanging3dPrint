# Complete edge reconstruction - 2026-10-13

The complete frame artwork has been rebuilt from tangent straight lines and circular arcs. The earlier repair removed sharp local bends but missed broad waves. All 26 boundary loops are now reconstructed; the 31 lap trimming domains and 20 section masks are regenerated from the same continuous geometry, so the old traced edges cannot clip the cleaned curves. Fabric boundaries, blue offsets, eight photo openings and matching backers follow the same source.

The largest outline movement is 1.461 mm at a formerly irregular small corner. Small artwork corners use 1.5 mm fillets; overall bounds remain 914.4 x 914.4 mm. Every frame STL and all eight backers were regenerated. The six M, four wall-block and one retainer STL files are byte-identical to the preceding revision. Tested lap/key profiles, seam transforms, screw features, mounting interfaces, saved placements and slicer settings are preserved. Rabbets remain 2.4 mm deep, backers 1.6 mm thick, with 0.3 mm edge clearance.

The color-mask calculation also uses direct intersections with the original STL triangles. The previous 3D slicing helper could introduce a false triangular notch at an oblique weave seam. A regression check covers that location, and all wood/blue modifiers are regenerated with the corrected method. Solid-change verification checks every distinct vertex-height interval directly, avoiding the same coplanar Boolean artifact.

## Verified results

- All 39 production STLs and both material test meshes are valid solids with matching source hashes.
- All 70 assembly pieces pass the interference check; maximum numerical overlap is 0.000236 mm3 (tolerance 0.01 mm3).
- Every frame, M and backer perimeter was compared with its CAD boundary: 34 parts, maximum boundary error 0.000033 mm.
- All 26 canonical outline loops and 320 line/arc primitives have tangent joins; maximum chord approximation is 0.001999 mm.
- Saved white/blue perimeter paths cover all 56 large circular arcs on all 20 frame plates: 348 arcs checked, maximum radial error 0.010984 mm (limit 0.06 mm).
- All 63 blue-bearing layers pass the blue-mask and white-intrusion checks. The white diamonds in Preview are seam markers, separate from extrusion paths.
- All 41 normal project meshes match the STLs within 0.0001 mm; 74 reinforcement, 21 wood and 21 blue modifiers pass validation.
- All 31 plates were re-sliced: 6,911,436 extrusion moves checked, minimum bed-edge clearance 0.634 mm, including bead widths, brim/support and towers. Custom printer purge/wipe/parking routines are excluded.

The before-project measurement on plates 1 and 2 found radial deviations up to 0.373 mm. The current test measures gradual deviation from the canonical circle, rather than relying only on the former isolated-angle threshold.

## Evidence

- [All 26 outline comparisons](outline-comparison.png), [full M outline](letter-outline.png), [current color map](assembly-color-map.png).
- [CAD joins and chord errors](cad-rebuild.json), [section partition proof](partition-rebuild.json), [solid changes and unchanged interfaces](geometry-verification.json).
- [Every frame/M/backer mesh perimeter](mesh-edge-review.json), [saved circular perimeter paths](perimeter-review.json), [before measurement](before-perimeter-review.json).
- [Full 31-plate integrity audit](integrity-review.json), [63-layer color audit](after/review.json).
- [Plate 1 saved toolpaths](after/plate-01-surface.png), [plate 2](after/plate-02-surface.png). `after/plate-03-surface.png` through `after/plate-20-surface.png` and plate 30 cover the other frame surfaces; C01-C12 show the original reported defect neighborhoods.

Project SHA-256: `56560e6c587f65be8c4c0d9d915d6aeffbd1abb138849a393db517bd1d3f919d`

CAD SHA-256: `a9677ae7f54c7915ae49eb8ab8799b935db688ba573a1e67e71430d154cf017f`

These checks cover digital geometry and saved slices. Plate 30 remains the physical surface/color test. The revised photo clearance and assembled load rating have not been physically verified. No printer job was sent.

## Rebuilding

On a fresh delivered copy, first run `python scripts/prepare_clean_revision.py` to preserve the matching starting files. It refuses to overwrite existing revision evidence. Install numpy, shapely, trimesh, manifold3d and matplotlib for the Python tools; scipy is needed only for refitting. OpenSCAD is required for native exports.

```powershell
python scripts/rebuild_clean_cad.py
python scripts/rebuild_clean_partitions.py
python scripts/export_jointed_stls.py --jobs 3
python scripts/refresh_clean_project.py
python scripts/audit_clean_mesh_edges.py
```

The canonical `working/geometry/clean-frame-primitives.json` is portable and does not require refitting. `fit_clean_outlines.py` documents the original fitting method and requires the retained historical source; it is not needed for replay. The project refresh compares against a preserved baseline under `.work/edge-quality` and retains all existing settings. Before a new revision, preserve its starting CAD, 3MF, validation JSON and STLs there; never substitute an unrelated project.

Open the staged `clean-edges.3mf` in Bambu Studio, save models as `models.3mf`, Slice all 31 plates, then Export all sliced file as `models.gcode.3mf`. Combine them with `combine_ams_slices.py`. Run the full geometry/toolpath audit, cosmetic/color audit and `review_clean_edges.py` against that same candidate and baseline. `publish_clean_project.py` refuses publication without matching passing hashes and coverage. Refresh the part map and package only after publication.
