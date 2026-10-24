# Root project release — October 22, 2026

The user requested root Knot (A2L), Letter (A2L), and supporting A1 projects with adjacent CAD/STL, and removal of all other 3MF files from source control. The follow-up explicitly allowed multiple supporting projects for different A1 settings, and added the sanding block and photo cut aligner. The user selected **keeping both locally saved layouts exactly** after being told they contain 12 crate clips and one photo guide.

| Project | Plates | Native time | Material |
| --- | ---: | ---: | ---: |
| Knot | 10 | 81h 02m | 2278.10 g |
| Letter | 6 | 72h 17m | 1223.80 g |
| Small Parts | 5 | 13h 49m | 476.53 g |
| Small Parts - Crate Clips PETG | 1 | Needs slicing | Not estimated |
| Small Parts - Photo Cut Aligner | 1 | 0h 33m | 6.66 g |
| Small Parts - Sanding Block PLA | 1 | 4h 20m | 116.65 g |
| Small Parts - Crate Stencils | 6 | 7h 49m | 162.47 g |

Letter retains the user-saved six-plate consolidation, the veneer edge correction and the approved wall-nub cleanup. Its only filament is now slot 1, the successful sample's ERYONE Ultra Silk Copper identity, moved from former slot 3 without changing its parameters. Knot now has only white, wood tan and Azurite blue in slots 1–3. Both projects have fresh native slices after removing their unused filaments. Current hashes/checks are in `../unused-filaments-r1/`; `../letter-eryone-r1/` records the preceding profile promotion, `../veneer-nub-cleanup-r8/` records the identical geometry, and `../veneer-edge-r7/` records the edge correction before cleanup. The veneers and all supports total 904.11 g. The requested ERYONE r4 finish sample is tracked in `../samples/` and declared in its catalog, with the user's October 23 success report. All values are slicer estimates, not observed print times.

## Preservation evidence

- `../unused-filaments-r1/`: current Knot/Letter slot cleanup and fresh native slices. Copper was unused in Knot; white, wood and blue were unused in Letter. Retained profiles, parameter values, geometry, poses, support paint, object/volume overrides and surviving purge entries are preserved. Blue moves from 4 to 3, and Letter copper from 3 to 1. All CAD/STL files, other projects and the ERYONE sample are unchanged. Historical validation reports retain their source hashes, linked through the new preservation records.
- `../sunlu-profile-defaults-r2/` and `../sunlu-silk-copper-r1/`: current local user preset snapshots and native import checks. The approved Basic/Metallic defaults are installed, and a separate SUNLU Silk Copper custom filament has A1/A2L presets copied from saved copper slot 3. These operations preserve every production 3MF byte and do not replace Letter's ERYONE assignment.
- `../sunlu-pla-r1/validation.json`: the preceding SUNLU PLA Basic/Metallic profile promotion in six PLA projects. Every printing parameter, mesh, pose and object/volume override was preserved. The user approved retaining Knot's 65 C Textured PEI bed and the 7.5 mm3/s blue flow limits in Knot and Small Parts as project overrides. At that revision all 29 native command streams remained byte-identical outside three profile identity comments. Knot and Letter are now superseded by the unused-slot cleanup above; the remaining projects still match this report. The successful ERYONE sample and PETG project remain unchanged.
- `sources.json`: exact input paths and SHA-256 hashes. Stencils were recovered from commit `3005467` without changing the checkout. Other inputs were read from the existing local files; their hashes were checked unchanged after packaging.
- `letter-preservation.json`: exact retained volume topology, coordinates, object/volume settings, support paint and bed poses. Former plates 11–17 become 1–7; only display-grid offsets, plate references and tower-array indexing change. All seven G-code payloads are unchanged.
- `small-parts-preservation.json`: the original 44 accessories plus six current jig pieces, unchanged. Independent inputs reused numeric mesh IDs; these were namespaced before native slicing to avoid Bambu treating different pieces as shared meshes. Actual geometry and settings were compared after native saving.
- `*-slice-preservation.json`: fresh native slices retain the input geometry, paint, bed poses and effective settings. Bambu's source-matrix bookkeeping and empty preset metadata normalization are listed separately. No empty preset field is treated as permission to change a process value.
- `*-native.json`: native Bambu return codes and slicing estimates. These successful results describe their respective saved slices; the Crate Clips result is historical because the later SUNLU PETG user save contains no G-code. Traditional timelapse notices persist; no geometric or plate-boundary warning remains in the stored slices.
- `cad-validation.json`: all seven OpenSCAD entry files parsed successfully. CAD is explicitly mesh-based, using the adjacent STL volumes. Original design development remains available separately; no parametric feature history is claimed for these snapshots.
- `catalog.json`: current project, CAD and per-volume STL hashes, geometry bounds, settings, material regions, modifiers and placements. `gcode-sha256.json` identifies every stored plate toolpath.

Knot retains the original monotonic-line white finish and now has five blue trim layers (1.00 mm) for the requested sanding allowance. The blue color modifiers extend downward by 0.40 mm; the flush show face and visible outlines are unchanged. All 50 screw reinforcement modifiers remain at Z12.4 beneath five continuous top layers. Brown texture, other geometry, poses and all process/material settings are preserved. All ten plates have fresh native slices, and the ten blue companion STLs are synchronized. Current checks are in `../knot-blue-five-layers-r1/`; `../knot-white-hilbert-removal-r2/` and `../knot-reinforcement-skin-r1/` record the source revisions. The Hilbert revision remains withdrawn. Sanding Block retains its selected source geometry and printing parameters; the SUNLU revision updates its filament identity metadata. Letter includes fresh slices after the veneer edge correction. Small Parts, Photo Cut Aligner and Crate Stencils retain their native slices. Crate Clips requires a fresh slice after the user-saved SUNLU PETG profile change. The local clip and guide layouts were preserved; the source projects were not overwritten. No printer job was sent.

The quick audit is `python scripts/audit_root_projects.py`. It uses only Python's standard library and validates the tracked/root 3MF inventory, checksums, printer/process constants, plate assignments and G-code checksums. Deep mesh/pose comparisons are recorded against the same hashes. No physical validation is implied by these checks.

## Physical evidence carried forward

The r3 full-curve knot test was reported successful; the full-size corrected knot remains physically unqualified. The 42 lap pads removed in the earlier correction stay removed. The successful supplied r3 test remains recoverable from commit `5dab12a` in Git/LFS history.

The sanding thread test was reported good. The complete current r4 retains those threads and support blocking; only the clamp's 1.174806-degree bed rotation was added in its own chat. That orientation, complete paper grip, jig fit/retention, clip fit, guide stiffness/clarity, stencil print/spray behavior and full-size veneer anti-warp performance are not newly qualified here.

The sanding block is a personal adaptation of DeepDiverDude's Compact Sanding Block – International Standards, supplied under the Standard Digital File License. Attribution and restrictions remain applicable; see the root guide.

Historical reports under working/output/reference remain records of their exact revisions. Their old project links may require retrieving the relevant commit; they are not additional current print choices. No Git history was rewritten.

## Stencil speed revision, 2026-10-23

The user reported continuous nozzle grinding and eventual bed detachment with SUNLU bone-white PLA on the A1. The user then approved changing only first-layer infill speed from 105 to 50 mm/s, internal solid infill from 250 to 80 mm/s, and top surface from 200 to 80 mm/s. All six plates were natively resliced. Geometry, poses, object/volume settings, CAD/STL and all other process/material settings remain unchanged. Actual extrusion speeds and G-code configuration were checked on every plate; the final project reopened successfully. Only the traditional-timelapse notices remain. See `stencil-speed-r1-validation.json` for hashes, preservation checks and per-plate time/material estimates. This speed-only revision has not been physically printed; the cause of the grinding remains unconfirmed.

## Crate clip user save, 2026-10-23

The latest user-saved crate clip project uses SUNLU PETG @BBL A1 in place of Generic PETG. Nozzle temperatures are 250 C for the first layer and 245 C afterward; the Textured PEI bed is 60 C, flow ratio 0.94, maximum volumetric speed 9 mm3/s, fan 10-30%, and minimum cooling slowdown speed 10 mm/s. All twelve clip meshes, poses, object/volume settings and locked structural settings are unchanged. The saved project no longer contains G-code and must be sliced before printing. The previous 4h 12m / 104.23 g estimate and Crate Clips native/slice-preservation reports describe the earlier Generic PETG revision, not this save. Current file hashes, the complete setting diff and preservation checks are in `crate-clips-user-save-r1-validation.json`. The project itself was preserved byte-for-byte during repository cleanup.
