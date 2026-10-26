# Dara project: agreed constants and change rules

These instructions apply to this entire repository. Their purpose is to keep
production and physical tests consistent. Read this file before changing any
geometry, print project, slicer settings, sample, or release documentation.

## Authority and change control

- The user's explicit instructions are authoritative. An agreement already made
  in the conversation counts; do not ask for the same permission again.
- Do not change a constant below without the user's explicit agreement to that
  change. A general request to fix, validate, simplify, optimize, or make a test
  does not authorize unrelated changes to these constants.
- Before a proposed exception, identify the exact old/new values, why the change
  is needed, and which files/plates it affects. Continue independent inspection
  and validation while awaiting any required agreement.
- Never edit this file to authorize your own exception. Record an agreed change
  here when it changes the ongoing baseline.
- Preserve all other saved settings and geometry. No opportunistic cleanup,
  reorientation, profile substitution, recoloring, or added assembly hardware.

## Locked print constants

The following values were verified in the saved production project on
2026-10-19. They apply to structural bodies and joint samples on either printer,
except for the explicit existing solid regions below.

| Setting | Required value |
| --- | --- |
| Sparse infill density | **8%** (`sparse_infill_density = 8%`) |
| Sparse infill pattern | **Gyroid** (`sparse_infill_pattern = gyroid`) |
| Nozzle diameter | **0.4 mm** |
| Layer height | **0.20 mm** |
| Initial layer height | **0.20 mm** |
| Wall loops | **4** |
| Top shell layers | **5** |
| Bottom shell layers | **5** |
| Build plate | **Textured PEI Plate** |
| Filament slots | **1 white, 2 wood tan, 3 copper silk, 4 Azurite blue**, except the approved Knot/Letter cleanup below |
| Artwork width | **914.4 mm / 36 inches** |

- Existing screw reinforcement modifiers remain **100% infill**. Veneers and
  their bonded carriers remain solid with their saved **100% infill** settings.
  Do not remove these exceptions or spread them to structural bodies/samples.
- The approved October 25 solid-lap exception below uses **100% rectilinear**
  only in both halves of each Knot overlap. Surrounding bodies remain 8% gyroid.
- Preserve the saved material boundaries, filament profiles, top-surface finish
  directions, object rotations, supports, brims, cooling, speeds, temperatures,
  and purge settings unless the requested change specifically covers them.
- Veneer tree supports stay enabled. Preserve the approved bonded wall carriers,
  fused necks, bed bands and saved orientation; modeled restraint does not prove
  that unsupported spans will print. A support-enabled flag does not establish
  local backing.
- The saved veneer rotation is shared across all three veneers: 55-degree lean
  and the existing in-plane orientation. Do not auto-orient individual veneers.

## Printer and project identity

- **Approved Knot white support base, 2026-10-25:** after observing blue
  first-layer supports from Auto selection, the user explicitly requested
  **support base Auto → slot 1 white** (`support_filament = 1`, previously 0),
  preserving the blue labels, followed by all-ten-plate reslicing, support-color
  verification, commit and push to main. **Support interface remains Auto**
  (`support_interface_filament = 0`). Preserve normal supports, gaps, spacing,
  paint, all geometry/modifiers, poses, CAD/STL and every other saved setting.
  Verify actual base/body support is white and inspect all support, interface
  and transition toolpaths for blue; labels remain slot 3 blue. Native reopen
  and evidence belong in `release/knot-white-support-base-r1/`. This supersedes
  the exact first-layer-label container/slices below; physical finish and
  support removal remain unqualified.

- **Approved Knot first-layer identifiers, 2026-10-25:** the user requested
  permanent metallic-blue plate and part numbers and confirmed all ten Knot
  pieces, followed by a push to main. Add flush **P1 F1 through P10 F10** text
  to the bed-facing **Z0–0.20 mm** layer using ten color-only modifiers with
  **extruder 3**, the existing SUNLU PLA Metallic Azurite blue. Text is **8 mm
  tall**, bold, and mirrored in bed X to read normally from the underside.
  Place it within continuous body stock, clear of joints, screw reinforcement
  and holes. Preserve original mesh stock, all existing material regions,
  the 28 solid-lap modifiers, 50 Z12.4 screw modifiers, top five blue layers,
  poses, support paint and every saved process/material setting. All ten plates
  require fresh native slices and native reopen. Synchronize label STLs, CAD
  references and the release catalog; evidence is in
  `release/knot-first-layer-labels-r1/`. This explicitly adds first-layer blue
  in addition to the existing five blue top layers. Physical label legibility
  and durability have not been observed.

- **Approved solid Knot laps, 2026-10-25:** the user reported "Solids work
  wonderfully" after `Dara-A2L-Joint-Solid-Laps-r3.3mf`, SHA-256
  `6898ed006c82b81beafe6a90012c3e59d23e4124a75daf22d50db93e8a2a447c`,
  and explicitly requested propagation to the main Knot project, commit and
  push. Apply the accepted **100% rectilinear** fill (`sparse_infill_density =
  100%`, `sparse_infill_pattern = zig-zag`) to **both overlapping halves of all
  14 joints** using 28 local modifiers. The masks cover joint-local X0–18 mm,
  Z0–13.5 and each actual lap's full projected outline. Preserve the original
  model stock, keys, grooves, glue reliefs, removed pads, all color geometry,
  poses and global settings. Surrounding bodies stay **8% gyroid**; infill-first
  stays **off** and supports stay **normal(auto)**. All 50 screw modifiers stay
  100% with their original pattern and Z12.4 caps; the solid-lap masks must not
  overlap those bolster footprints. Five top layers and five blue layers remain.
  All ten plates require fresh native slices and native reopen; synchronize
  the new modifier STLs, `Knot.scad` references and release catalog. Evidence is
  in `release/knot-solid-laps-r1/`. This supersedes the prior production hash
  and slices while preserving the historical evidence chain. The user's report
  establishes sample success; the actual printed hash/printer were not
  independently observed, and full-size performance is not yet confirmed.

- **Approved main Letter promotion, 2026-10-25:** the user explicitly required
  the corrected veneers in the main `Letter.3mf`, followed by commit and push.
  The main six-plate project now contains the corrected Left/Right/Center
  veneers on plates 4–6. Promote the exact candidate meshes, support paint,
  poses and object settings; preserve the five core meshes, reinforcement,
  poses and object/volume overrides on plates 1–3. Bambu shares the corrected
  process and filament limits across the project, so the 23 candidate settings
  apply globally and **all six plates are freshly sliced**. Printing uses
  **220 C nozzle, 55 C Textured PEI bed, 30–60 mm/s XY extrusion commands and
  1500/2500 mm/s2 maximum printing/travel acceleration**. The core plates also
  use these limits; their old stored slices are superseded. Structural 8%
  gyroid, solid veneer/carrier overrides, 0.4 mm nozzle, 0.20 mm layers, four
  walls, five top/bottom layers, materials, cooling and all other settings are
  preserved. The left carrier's 0.15 mm end step and two center-carrier steps
  are replaced with continuous tapers; the right carrier geometry is retained.
  All three full-height veneers and all six native command streams are checked;
  veneer/support material totals 904.10 g. Native reopening passes. Exact
  changes, hashes, inspections and physical limitations are recorded in
  `release/letter-veneer-correction/`. The separate output projects are now
  historical; use the main `Letter.3mf`. The whole-part physical shift remains
  unexplained, and this promotion does not imply a successful physical print.

- **Approved meaningful veneer names, 2026-10-25:** the user requested names
  without versions. From the assembled artwork's front, **V1 = Left letter
  veneer, V2 = Right letter veneer, V3 = Center letter veneer**. Root
  `Letter.3mf` selector plates 4–6 and their objects/parts now use these names;
  the old conflicting saved plate-number prefixes are removed. The initial
  name-only revision preserved all six G-code files, geometry, paint, settings
  and poses; its evidence is retained in `release/letter-veneer-names/`.
  The subsequent main-file promotion above supersedes those container and slice
  hashes. The preceding **`output/Letter Veneers/Letter Veneers.3mf`** candidate
  is historical; its names and corrections are now in the main file.
  The user clarified that the physical failure was on **Plate 5 of Letter**,
  and that they have not printed or inspected the other veneers. Do not resolve
  the old selector/saved-name ambiguity by assumption or claim the other veneers
  were physically evaluated. Full-height digital inspection covers all three;
  the whole-part physical shift remains unresolved.

- **Approved ERYONE spool limits, 2026-10-25:** the user supplied **190–220 C
  nozzle, 55–70 C bed and 30–60 mm/s printing speed**, and explicitly requested
  compliance for all three veneers. These limits are now saved in the main
  `Letter.3mf` under the promotion above. Printing remains **220 C nozzle / 55 C Textured
  PEI bed**. Explicit flushing is now **220 C** (previous automatic result
  240 C), and the saved nozzle-range maximum is **220 C** (was 240 C).
  All three fresh native slices have checked **30–60 mm/s XY extrusion
  feedrates**, including carriers and generated supports. Outer walls remain
  40 mm/s; inner walls change 80 to 60; infill, top and support speeds cap at
  60. Small-perimeter/cooling minima and severe-overhang settings become 30;
  filament bridge speed changes 25 to 30. Preserve cooling fan values, flow,
  volumetric limit, retraction, geometry, paint and poses. Non-extruding travel,
  printer priming/calibration, 140 C nozzle probing, off commands and physical
  acceleration/deceleration are separate from the requested printing range.
  The main file retains the carrier-edge corrections and verified project-level
  **1500/2500 mm/s2 printing/travel acceleration**. The successful historical
  ERYONE sample and local user presets remain unchanged. Current differences,
  hashes and native checks are in `release/letter-veneer-correction/validation.json`.
  The reported whole-part shift remains unresolved, and candidate bridge/overhang
  behavior and full-size finish remain physically unqualified.

- **Accepted knot joint sample and production publication, 2026-10-25:** after
  receiving `Dara-A2L-Joint-Photo-Retainer-Bolster-r2.3mf`, the user reported
  "Joints are ok" and requested propagation, commit and push. Record this as
  user-reported joint-fit success for the current r2 J3 F2/F3 sample, SHA-256
  `c0e48a0b2f7c8bf8adcc696b9785d4ff49359dd9104536ca486a1ec50055154d`.
  The actual printed hash/printer were not independently observed. This report
  does not confirm screw-bolster surface appearance or full-size performance.
  The accepted sample is an unchanged crop of current `Knot.3mf`, SHA-256
  `aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46`;
  its geometry and effective settings are already present in production.
  Publish that matching project with **infill-first OFF**, **normal(auto)
  supports**, all 14 existing joints and ten current native slices. No new
  joint dimensions or regeneration are required. Preserve the Z12.4 screw
  modifiers and all other constants. The earlier r1 sample is withdrawn for
  selecting an M through-hole instead of a photo-retainer blind-hole bolster.
  Evidence: `release/knot-joint-approval-r1/`.

- **Approved normal knot supports, 2026-10-24:** the user requested switching
  Knot from trees to normal supports. In root `Knot.3mf`, **`support_type =
  normal(auto)` replaces `tree(auto)`** for all ten F1–F10 plates. Preserve
  `support_style = default`, existing per-object support activation and paint,
  build-plate-only support, the **0.20 mm object interface spacing**, **0.20 mm
  top gap**, geometry, poses, materials and every other setting. **Infill-first
  stays off.** All ten plates require fresh native slices. Evidence is in
  `release/knot-normal-supports-r1/`; the preceding rollback report retains its
  historical hashes. Letter's veneer tree supports remain unchanged. Support
  removal and full-size joint fit remain physically unqualified.

- **Approved infill-first rollback, 2026-10-24:** the user reports that the first
  three full-size knot pieces, printed for a second time, have keys that do not
  fit the joint grooves, and explicitly requested reverting infill-first.
  In current root `Knot.3mf`, **`is_infill_first = 0` replaces 1** globally on
  all ten plates. This supersedes the infill-first portion of the October 22
  correction below. Keep each object's **0.20 mm support-interface spacing**,
  the **0.20 mm support top gap**, all geometry/keys/grooves, removed lap pads,
  materials, poses, reinforcement and every other process/material setting.
  Reslice all ten plates; do not restore any historical infill-first slice.
  Evidence is in `release/knot-infill-first-revert-r1/`. The user's full-size
  fit failure supersedes any implication that the earlier curve test qualified
  joint fit. The exact printed hash/printer were not independently observed;
  infill-first is the user's suspected cause, not a digitally proven diagnosis.
  The rollback itself remains physically unqualified.

- **Approved unused filament removal, 2026-10-23:** the user requested removing
  unused copper from `Knot.3mf`, then white, wood and blue from `Letter.3mf`,
  followed by commit/push. Knot now has **1 white SUNLU PLA Basic, 2 wood tan
  SUNLU PLA Basic, 3 Azurite blue SUNLU PLA Metallic** (old blue slot 4 becomes
  3). Letter has only **slot 1 ERYONE Ultra Silk Copper**, retaining the exact
  successful sample profile identity and all saved values from former slot 3.
  The removed slots were unused by every object, volume and stored slice.
  Preserve all retained material parameters, surviving purge matrix entries,
  process settings, object/volume overrides, geometry, support paint and poses.
  All ten Knot and six Letter plates have fresh native slices using the new
  slot numbers; five blue layers and the existing reinforcement remain intact.
  This supersedes prior slot numbering and exact container/toolpath hashes for
  these two projects only. CAD/STL, other projects and user preset files remain
  unchanged. Source hashes, native checks and current hashes are recorded in
  `release/unused-filaments-r1/`. Physical qualification is unchanged.

- **Approved SUNLU preset defaults and copper preset, 2026-10-23:** promote
  the previously retained overrides into the user's local Bambu Studio presets:
  A2L **SUNLU PLA Basic** and **SUNLU PLA Metallic** use **65 C** Textured PEI
  first/subsequent temperatures, and Metallic on **both A1 and A2L** uses
  **7.5 mm3/s** maximum volumetric speed. A1 Basic stays at 65 C and 12 mm3/s.
  All other preset fields and existing identities are preserved. The user also
  requested **SUNLU PLA Silk Copper**, created for A1 and A2L from the actual
  saved Generic PLA Silk slot 3 in Small Parts and Knot respectively: **220 C**
  nozzle first/subsequent, **55 C** Textured PEI bed, **0.98** flow, **7.5 mm3/s**,
  **60-80%** fan, **20 mm/s** minimum cooling speed and **0.5 mm** retraction.
  Preserve every other production-derived copper parameter, including each
  printer's saved start G-code. This creates named presets only; it does not
  reassign project copper or replace Letter's approved ERYONE profile.
  Existing 3MF files and slices remain byte-identical during these local preset
  operations. Letter's unused Basic/Metallic slots retain their embedded 55 C
  settings and 12 mm3/s Metallic limit; Photo Cut Aligner's unused Metallic slot
  retains 12 mm3/s. Do not silently reapply new defaults to those saved projects.
  Current preset snapshots and native validation are in
  `release/sunlu-profile-defaults-r2/` and `release/sunlu-silk-copper-r1/`.
  Local installation is verified; Bambu cloud synchronization is pending normal
  app sync and has not been independently observed. Physical status is unchanged.

- **Approved SUNLU PLA identities, 2026-10-23:** the user requested replacing
  Generic PLA with their saved SUNLU PLA Basic presets and supplied SUNLU PLA
  Metallic for Azurite blue. After comparison, the user explicitly approved
  retaining existing project overrides. In the six root PLA projects, former
  Generic PLA slots use the matching A1/A2L SUNLU PLA Basic profile; Azurite
  slot 4 uses SUNLU PLA Metallic. Preserve Knot's **65 C** Textured PEI bed
  first/subsequent settings (the A2L preset then defaulted to 55 C), and the blue
  **7.5 mm3/s** maximum volumetric speed in Knot and Small Parts (the Metallic
  presets then defaulted to 12). All other compared preset parameters matched the saved
  slots. Basic and Metallic then had identical parameters on each printer and
  distinct profile identities. Preserve copper silk, Letter's approved ERYONE,
  transparent PLA, PETG, colors, all geometry and every process/material value.
  Only profile names/vendor/IDs, slice material IDs, three G-code identity
  comments and checksums change; all 29 stored native command streams remain
  byte-identical outside those comments. The successful ERYONE sample stays
  byte-identical. Current hashes, preset snapshots and preservation evidence
  are in `release/sunlu-pla-r1/validation.json`; earlier geometry and physical
  reports remain records of their source revisions. No reslice or new physical
  qualification is implied.

- **Approved Letter ERYONE filament, 2026-10-23:** the user reported the supplied
  Desktop `Dara-A2L-Hammered-Finish-ERYONE-r3.3mf` was "a raging success" and
  requested promotion of its filament to `Letter.3mf`. The supplied file is
  byte-identical to the tracked **ERYONE r4 with r8 wall-base cleanup**, SHA-256
  `b82b2356c92c14640b4107405c0fde04488d61ced29d34821572c8b84003f0f6`;
  the Desktop filename still says r3. Letter slot **3** now carries the exact
  saved **ERYONE Ultra Silk Copper - production baseline @BBL A2L** profile
  identity (including its saved sample suffix) and **ERYONE** vendor. All
  printing parameters already matched: **220 C** nozzle first/subsequent,
  **55 C** Textured PEI bed, **0.98** flow, **7.5 mm3/s** maximum volumetric speed,
  **60-80%** fan and **20 mm/s** minimum cooling speed. Preserve all geometry,
  colors, poses, process settings, object/volume overrides and other slots.
  All six native command streams are retained exactly; only the two filament
  identity comments and their checksums change. No reslice was needed. Retain
  Letter's existing AMS dryer arrays and six-plate tower arrays. Evidence and
  current hashes are in `release/letter-eryone-r1/validation.json`. This records
  user-reported sample success, not full-size Letter qualification; the actual
  printer/printed file hash were not independently observed.

- **User-saved crate clip filament revision, 2026-10-23:** preserve the saved
  `Small Parts - Crate Clips PETG.3mf` with **SUNLU PETG @BBL A1** replacing
  Generic PETG. Its saved nozzle temperatures are **250 C first layer / 245 C
  subsequent layers**, Textured PEI bed **60 C**, flow ratio **0.94**, maximum
  volumetric speed **9 mm3/s**, fan **10-30%**, and minimum cooling slowdown
  speed **10 mm/s**. All twelve clip meshes, placements, object/volume settings
  and locked structural constants are unchanged. This user save contains no
  stored G-code; slice it before printing. Earlier clip time/material estimates
  describe the previous Generic PETG slice. See
  `release/root-projects/crate-clips-user-save-r1-validation.json`.

- **Approved deeper blue knot trim, 2026-10-23:** the user requested two more
  blue layers for sanding allowance. In `Knot.3mf`, extend all ten blue color
  modifiers downward from nominal **Z12.9 to Z12.5 mm**, keeping the top at
  **Z13.5 mm**. This changes the blue depth from **0.60 to 1.00 mm** and native
  blue extrusion from **three to five 0.20 mm layers**. Keep the original blue
  XY outline and upper geometry, flat white/blue surface, monotonic-line finish,
  brown texture, all 50 Z12.4 screw modifiers and five solid top layers. All
  other geometry, poses and process/material settings remain unchanged. Update
  only the ten blue companion STLs and retain their `Knot.scad` references.
  Current slices and checks are in `release/knot-blue-five-layers-r1/`; this
  supersedes the exact container hash in the earlier restoration below.
  Physical sanding allowance and surface finish remain unqualified.

- **Approved removal of white knot Hilbert finish, 2026-10-23:** the user
  requested removing Hilbert while preserving the hidden screw reinforcement.
  Restore the exact screw-skin release from `c8f8f7a`: original monotonic-line
  white surface pattern and finish directions, with all 50 solid screw
  modifiers still capped at **Z12.4 mm** beneath five continuous top layers.
  Remove the Hilbert height ranges and redundant blue pattern overrides;
  retain the original brown/blue geometry, settings and toolpaths. The project
  and ten stored native slices at that revision exactly matched the screw-skin release
  (SHA-256 `8a76b70a1c1430d74a16ec06c9689827d33f3902afb1d7de90e4436072c251c3`).
  CAD/STL, poses and every other print setting remain unchanged. The Hilbert
  revision in `release/knot-white-hilbert-r1/` is withdrawn; restoration evidence
  is in `release/knot-white-hilbert-removal-r2/`. Physical finish remains pending.

- **Approved knot screw-skin correction, 2026-10-23:** the user reported visible
  circles over the screw reinforcement and requested correction, commit and
  push. In `Knot.3mf` only, all 50 local solid screw modifiers end at **Z12.4 mm**
  instead of Z17.0, below the nominal Z13.5 show face. Keep their XY geometry,
  lower Z0 extent and **100% infill**. Preserve the five solid top layers,
  structural 8% gyroid, all actual screw holes, normal/color meshes, support
  paint, poses and every process/material setting. Do not regenerate the old
  full-height modifiers. All ten plates have fresh native slices; matching
  modifier STLs remain referenced by `Knot.scad`. Evidence is in
  `release/knot-reinforcement-skin-r1/`. Physical surface finish remains pending.

- **Approved stencil speed revision, 2026-10-23:** in `Small Parts - Crate Stencils.3mf`, first-layer infill speed is **50 mm/s** (was 105), internal solid infill speed is **80 mm/s** (was 250), and top-surface speed is **80 mm/s** (was 200). All six plates were resliced. Preserve every other setting and all geometry/poses. This speed-only revision follows reported continuous grinding and bed detachment on the A1 with SUNLU bone-white PLA; the cause is unconfirmed and the revision remains physically unqualified. Evidence: `release/root-projects/stencil-speed-r1-validation.json`.

- **Approved wall-nub cleanup, 2026-10-23:** remove only obsolete triangular
  connection bases from the current main project and ERYONE sample, then
  commit/push. `Letter.3mf` V1/V2/V3 have 25/23/34 bases trimmed flush to the
  existing inclined wall at assembly Z4.4; the current ERYONE r4 sample has 10.
  Keep filenames, all active connections, restored veneer edges, wall thickness,
  end bands, settings and poses unchanged. Preserve core plate 1–3 meshes and
  stored toolpaths exactly. Current cleanup hashes/evidence are recorded in
  `release/veneer-nub-cleanup-r8/`; r7 evidence records the pre-cleanup revision.
  Physical qualification remains pending.

- **Approved veneer edge correction, 2026-10-22:** the user requested correction
  of both the main project and the supplied Desktop ERYONE r3 sample, followed
  by commit/push. Current `Letter.3mf` retains the six-plate consolidation and
  now contains fresh native slices. Its V1/V2/V3 edge-crossing cleanup pockets
  and connections move inward (30/29/43 respectively). The 2.60 mm square,
  0.40 mm deep pockets retain their dimensions; moved pockets leave at least
  1.69 mm of perimeter stock. Restore the original nominal Z8.6 back/side edge
  at old pockets and remove their obsolete upper stems. The complete perimeter
  has a checked 1.20 mm continuous rim. New 1.20 mm square necks connect the
  existing inclined wall at Z4.3 to the veneer at Z9.2. Keep the original
  continuous walls, openings, end bands, orientations, tree supports, interior
  connections, artwork, core geometry and effective print/material settings.
  Do not regenerate the former edge-open pockets from historical builders.
  The matching current finish sample is **ERYONE r4**, with 15 moved edge
  connections, tracked at `release/samples/Dara-A2L-Hammered-Finish-ERYONE-r4.3mf`
  as the explicitly requested exception to the seven-production-project-only
  tracked 3MF inventory. See `release/veneer-edge-r7/` for exact hashes and
  fresh validation. Physical cleanup, fit and anti-warp performance remain
  unqualified for this revision.

- **User consolidation, 2026-10-22:** `Letter.3mf` supersedes the seven-plate layout below: C1 on 1, C2 on 2, C3/C4/C5 on 3, veneers V1/V2/V3 on 4–6. Preserve the user-saved geometry/settings/poses except for the approved edge correction above. It originally had no stored slices; the corrected revision has fresh slices.

- **Approved root organization, 2026-10-22:** the user requested root projects
  with adjacent CAD and STL, removal of all other Bambu projects from source
  control, then explicitly allowed separate supporting projects for different
  A1 settings and requested the sanding block and photo cut aligner.
- Current root **`Knot.3mf`** is the corrected A2L F1â€“F10 project, ten plates.
  **`Letter.3mf`** is the A2L M, seven plates: cores on 1â€“4 and veneers on 5â€“7.
  These map to former Dara plates 11â€“17. Preserve their geometry, settings,
  bed poses and original stored toolpaths. Infill-first stays off in Letter.
- Root **`Small Parts.3mf`** is the A1 companion plus glue aligners: original
  backers on 1â€“2, wall blocks/retainers on 3, center r3 jigs on 4 and side r1
  jigs on 5. Their common saved process and object overrides are preserved.
- Separate root A1 projects preserve their different settings:
  **`Small Parts - Crate Clips PETG.3mf`**, **`Small Parts - Photo Cut Aligner.3mf`**,
  **`Small Parts - Sanding Block PLA.3mf`** and **`Small Parts - Crate Stencils.3mf`**.
  The user explicitly chose the exact locally saved **12-clip and single-guide
  layouts**, not the original eight-piece sets. Keep the latest sanding r4
  clamp rotation and physically confirmed thread setup. The existing stencil
  exception is 0% sparse infill, gyroid, two walls and four top/bottom layers.
- Adjacent SCAD files are exact mesh-based CAD snapshots referencing their STL
  folders, not parametric feature histories. Keep them synchronized with the
  3MF geometry and release catalog. The seven root projects are the only
  tracked 3MF files. Retired projects remain in Git history/local ignored files.
  Historical references to Dara.3mf and working Bambu paths below identify the
  sources of past changes; they do not reinstate those paths as current releases.
- The older complete A1 design is historical and is not the current production
  baseline. Its settings and joints must not silently replace A2L settings.
- **Separate corrected knot project, 2026-10-22:** use
  `Knot.3mf` (originally the separate working-folder project)
  for full-size F1-F10, replacing the knot plates 1-10 in the main project for
  printing. Plate numbers match. The user reported the r3 full-curve test
  worked, then explicitly chose a separate knot project to keep M settings
  unchanged. At that revision, `is_infill_first = 1` replaced 0; the October 24
  rollback above supersedes this setting for the current root Knot project.
  Each knot object's `support_interface_spacing = 0.2` replaced inherited 0.5
  and remains in effect.
  Preserve the 0.20 mm support top gap, geometry, all other process settings,
  modifiers and actual bed poses. Bambu applies infill-first globally;
  object overrides were verified ineffective. Do not enable it in the shared
  main project. This correction originally left the combined main and M/A1
  files unchanged; the later root organization above supersedes file packaging.
  The successful supplied r3 file SHA-256 is
  `5fc8fe29ea2993bdceaf690744506bd14bf757982a76b6937e9e7ce4b9192bb0`;
  the locally printed hash was not independently read. Full-size physical
  print quality and support cleanup remain unqualified.
- A joint sample may be prepared for the A1 when the user requests that printer.
  Use an actual A1 machine profile and reslice for the A1. Preserve the locked
  process constants; do not reuse A2L machine commands or stored slices.
- **After any printer or preset switch, recheck density AND pattern**, along
  with the other constants and all object/volume overrides. Do not assume a
  process preset survives the switch. Grid is not an acceptable substitute for
  gyroid. Machine-specific changes do not authorize unrelated process changes.
- Open a 3MF **as a project** to retain its configuration. A preset's display
  name is not evidence of its effective settings. Keep names stable; new sample
  process names should include `8% gyroid` to make the intended setup visible.

## Consistent production-derived tests

1. Start from the actual saved production project. Record its path and SHA-256,
   the source objects/joint, and the exact crop boundaries. Do not substitute an
   older test, a newly generated approximation, or an unqualified draft.
2. For a request for a sample **from production**, preserve the joint geometry,
   fit clearances, seating features, thicknesses, colors, modifiers, print
   orientation and effective process settings inside the crop. Cropping and
   necessary bed/tower repositioning must be listed separately from design
   changes. Check that crop boundaries do not create misleading side scallops.
3. For an explicitly requested design experiment, state the specific variable
   being changed and keep the rest of the baseline fixed. Do not add feet, pads,
   spacers, cutouts, recessed backs, new mortises or other mechanisms incidentally.
4. Compare the full production and sample settings, including object and volume
   overrides. Every difference must have a stated purpose within the request.
   Verify the locked settings in the saved editable project, sliced project,
   and G-code configuration, not just a label or a screenshot.
5. Validate geometry and actual native toolpaths relevant to the test: mating
   clearances, intended show-face heights/colors, side continuity, bed contact,
   supports where needed, printable bounds, tower clearance and checksum.
   Investigate floating-region, collision and similar printability warnings
   before handing the file over. Report which checks were actually performed.
6. Supply one clearly identified current test, its exact filename/revision and
   hash, printer, changed variable (or "unchanged production joint"), settings,
   and slicer time/material estimate. Clearly mark superseded/failed samples;
   do not offer several unexplained variants or silently replace a test being
   printed. No printer job is sent without an explicit request to print.
7. Keep the geometry source, saved slices and validation evidence synchronized.
   A stale G-code file or validation report is not evidence for a changed mesh.
   Hash protected files before/after. If an authorized change updates a shared
   production container, also compare protected plate geometry, settings and
   stored toolpaths so unrelated plates remain unchanged.

## Physical evidence and the route to production

- Digital checks establish what the files contain, not successful physical fit,
  material adhesion, flushness, support cleanup or full-size veneer stability.
  Never describe an unprinted revision as "tested", "proven" or ready for the
  production run because its mesh or slice passes.
- Tie each physical result to the exact test revision and printer/settings used.
  An earlier general statement that fit/cleanup passed does not qualify a later
  joint. Do not repeatedly ask about a supposed successful test that never ran.
- Current joint history: the original reported lip was 0.005-0.007 inch. The
  later supplied flush-joint test was reported to fail badly, with a high upper
  lap, side cutouts and white in the brown fabric. Mortise binding is a user
  suspicion, not a measured diagnosis. The later simple-joint draft is unqualified.
- **Physical update, 2026-10-24:** the user reports the first three full-size
  knot pieces were printed for a second time and their keys do not fit the
  grooves. Record this as a reported full-size joint-fit failure, not merely
  pending qualification. The requested infill-first rollback does not itself
  establish fit or resolve the already printed pieces.
- `working/bambu/Dara-A2L-Flush-Joint-Test/` and the fins-only veneer comparison
  in `working/bambu/Dara-A2L-Veneer-Backing-Trial/` have withdrawal notices. Do not
  recommend or promote them based on older passing reports or stale README text.
- **Veneer support requirement, 2026-10-21:** the user clarified that the carrier
  must tie the silk PLA veneer to the bed to restrain warping; merely backing it
  with detachable supports is insufficient. The material limit is **under
  1,000 g for all three veneers and their complete support structures combined**.
  `output/Dara-A2L-Veneer-Wall-Cradle-r1/` is withdrawn after the user's design
  rejection. It retained necks and feet but removed intervening starter-rib
  bodies. Whole-model connectivity and extrusion at necks did not establish
  restraint during growth. This was not a reported physical print failure.
  The user also rejected r2 because its long narrow bed posts remain fragile;
  `output/Dara-A2L-Veneer-Wall-Cradle-r2/` is withdrawn. The revised carrier
  must use continuous braced walls reaching the bed instead of isolated posts.
  Separate candidates did not replace root `Dara.3mf` until the explicit
  promotion approval below. Geometry or slice checks do not establish physical
  anti-warp performance.
  The user subsequently requested removing the obsolete local base rails,
  crossbars, center strip and starter feet, while tying the front and rear walls
  together with a thin band printed on the bed. Keep this base restraint when
  reducing support material; do not restore the discarded perimeter framework.
- **Approved wall-carrier promotion, 2026-10-21:** the user explicitly requested
  replacing the existing veneer plates in the main Dara project, then committing
  and pushing. A2L plates **15-17** use **wall-cradle-r6-end-ties**: continuous 1.20 mm
  inclined backing, 1.00 mm rear wall and two 1.00 mm connecting walls, with two
  **4.00 mm wide by 0.60 mm high bed bands** per plate. The user clarified that
  these bands belong at the **two open ends**, flush with the wall ends, to keep
  them from splaying. They replace the r5 bands beneath the interior webs;
  do not add extra interior bands. The 35 pointed rear/web
  openings remain; the outer guard and obsolete local base framework are removed.
  All three veneers and all supports slice at **902.59 g combined**. Preserve
  the original veneer and fused-neck geometry, rotations and process settings.
  Plates **1-14 and 18-20**, M cores, corrected knot joints and all A1 files stay
  unchanged. The root/named complete projects and editable source are synchronized.
  This approval authorizes the file promotion before physical qualification;
  rigidity, adhesion, silk warping resistance and removal remain untested.
- The current direct reference is
  `working/bambu/Dara-A2L-Production-Joint-Sample/Dara-A2L-Production-Joint-Sample.3mf`.
  It is cropped from production J4, with corrected straight crop boundaries.
  Its outline validation does not qualify joint fit.
- **Physical update, 2026-10-19:** the user reports, "I trimmed the 3 little
  nipples off the bottom lap and it fits nice." Record this as a successful
  fit after physical removal of the three lower-lap pads, not a pass for the
  original untrimmed design. It points to pad interference; do not assume the
  mortise needs widening. In the follow-up, the user confirmed that **both the
  white and brown front surfaces are flush and the previous lip is gone**.
  The user also reported switching the sample to the A1 and seeing grid infill;
  the exact locally resliced settings/file have not been inspected. Keep those
  circumstances with the physical result rather than labeling it an A2L test
  at the saved 8% gyroid settings. This report alone does not authorize an
  unrelated redesign or establish final production readiness.
- **Approved production correction, 2026-10-19:** the user explicitly requested
  eliminating the three lower-lap pads and propagating that joint to production.
  Remove only their 0.20 mm raised stock, leaving the surrounding lap at Z4.8,
  across all 14 knot joints (42 pads). Preserve mortises, keys, glue recesses,
  visible outlines, colors and process settings; reslice A2L plates 1-10.
  Keep M/A1 and plates 11-20 unchanged. Do not restore these pads in subsequent
  production regeneration. The saved reference sample above remains a record
  of the untrimmed source used for the physical correction, not the new release.
- Progress in order: establish a consistent reference test; diagnose the
  observed failure; agree any change to locked constants; validate the specific
  correction; obtain a physical result for that revision; then carry the same
  correction into the authorized production joints and reslice affected plates.
  Do not substitute another design during promotion. A test on a different
  printer is not proof of the full production printer/material process.
- Report the result directly: what changed, what stayed fixed, what was checked,
  and what physical result remains unknown. Investigate a user's conflicting
  observation without dismissing it or inventing a cause.

## Repository hygiene

- Keep unrelated work intact. Stage only files for the requested change; do not
  sweep existing modified/untracked files into a commit.
- Commit and push when authorized; confirm the remote revision and any Git LFS
  upload before claiming the files are available on another computer.
- Updating these instructions alone must not rebuild or alter print artifacts.
