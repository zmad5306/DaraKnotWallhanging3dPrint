# Root project release — October 22, 2026

The user requested root Knot (A2L), Letter (A2L), and supporting A1 projects with adjacent CAD/STL, and removal of all other 3MF files from source control. The follow-up explicitly allowed multiple supporting projects for different A1 settings, and added the sanding block and photo cut aligner. The user selected **keeping both locally saved layouts exactly** after being told they contain 12 crate clips and one photo guide.

| Project | Plates | Native time | Material |
| --- | ---: | ---: | ---: |
| Knot | 10 | 80h 43m | 2271.96 g |
| Letter | 6 | 72h 19m | 1223.65 g |
| Small Parts | 5 | 13h 49m | 476.53 g |
| Small Parts - Crate Clips PETG | 1 | 4h 12m | 104.23 g |
| Small Parts - Photo Cut Aligner | 1 | 0h 33m | 6.66 g |
| Small Parts - Sanding Block PLA | 1 | 4h 20m | 116.65 g |
| Small Parts - Crate Stencils | 6 | 5h 10m | 162.47 g |

Letter retains the user-saved six-plate consolidation and now contains fresh slices after the approved veneer edge correction. Current hashes and checks are in `../veneer-edge-r7/`; `letter-consolidation.json` records the earlier unsliced input. The veneers and all supports total 903.96 g. The requested ERYONE r4 finish sample is tracked in `../samples/` and declared in its catalog. All values are slicer estimates, not observed print times.

## Preservation evidence

- `sources.json`: exact input paths and SHA-256 hashes. Stencils were recovered from commit `3005467` without changing the checkout. Other inputs were read from the existing local files; their hashes were checked unchanged after packaging.
- `letter-preservation.json`: exact retained volume topology, coordinates, object/volume settings, support paint and bed poses. Former plates 11–17 become 1–7; only display-grid offsets, plate references and tower-array indexing change. All seven G-code payloads are unchanged.
- `small-parts-preservation.json`: the original 44 accessories plus six current jig pieces, unchanged. Independent inputs reused numeric mesh IDs; these were namespaced before native slicing to avoid Bambu treating different pieces as shared meshes. Actual geometry and settings were compared after native saving.
- `*-slice-preservation.json`: fresh native slices retain the input geometry, paint, bed poses and effective settings. Bambu's source-matrix bookkeeping and empty preset metadata normalization are listed separately. No empty preset field is treated as permission to change a process value.
- `*-native.json`: native Bambu return codes and slicing estimates. All are successful. Traditional timelapse notices persist; no geometric or plate-boundary warning remains in the saved slices.
- `cad-validation.json`: all seven OpenSCAD entry files parsed successfully. CAD is explicitly mesh-based, using the adjacent STL volumes. Original design development remains available separately; no parametric feature history is claimed for these snapshots.
- `catalog.json`: current project, CAD and per-volume STL hashes, geometry bounds, settings, material regions, modifiers and placements. `gcode-sha256.json` identifies every stored plate toolpath.

Knot and Sanding Block are byte-identical copies of their selected source projects. Letter now includes fresh slices after the veneer edge correction. Small Parts, Crate Clips, Photo Cut Aligner and Crate Stencils were freshly sliced. The local clip and guide layouts were preserved; the source projects were not overwritten. No printer job was sent.

The quick audit is `python scripts/audit_root_projects.py`. It uses only Python's standard library and validates the tracked/root 3MF inventory, checksums, printer/process constants, plate assignments and G-code checksums. Deep mesh/pose comparisons are recorded against the same hashes. No physical validation is implied by these checks.

## Physical evidence carried forward

The r3 full-curve knot test was reported successful; the full-size corrected knot remains physically unqualified. The 42 lap pads removed in the earlier correction stay removed. The successful supplied r3 test remains recoverable from commit `5dab12a` in Git/LFS history.

The sanding thread test was reported good. The complete current r4 retains those threads and support blocking; only the clamp's 1.174806-degree bed rotation was added in its own chat. That orientation, complete paper grip, jig fit/retention, clip fit, guide stiffness/clarity, stencil print/spray behavior and full-size veneer anti-warp performance are not newly qualified here.

The sanding block is a personal adaptation of DeepDiverDude's Compact Sanding Block – International Standards, supplied under the Standard Digital File License. Attribution and restrictions remain applicable; see the root guide.

Historical reports under working/output/reference remain records of their exact revisions. Their old project links may require retrieving the relevant commit; they are not additional current print choices. No Git history was rewritten.
