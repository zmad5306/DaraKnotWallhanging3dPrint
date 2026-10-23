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
| Filament slots | **1 white, 2 wood tan, 3 copper silk, 4 Azurite blue** |
| Artwork width | **914.4 mm / 36 inches** |

- Existing screw reinforcement modifiers remain **100% infill**. Veneers and
  their bonded carriers remain solid with their saved **100% infill** settings.
  Do not remove these exceptions or spread them to structural bodies/samples.
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

- **Approved white knot Hilbert finish, 2026-10-23:** the user requested a
  Hilbert curve finish on the white knot surfaces and explicitly excluded the
  already textured brown regions. In `Knot.3mf`, use `hilbertcurve` only in the
  Z13.0–13.6 height range containing the main white show face. Keep the native
  range defaults at 0.20 mm layer height and extruder 0 (inherit). All ten blue
  color modifiers explicitly retain `top_surface_pattern = monotonicline`;
  brown modifier settings remain unchanged. Keep top line width **0.42 mm**,
  five solid top layers, the Z12.4 screw modifiers and every other setting.
  Lower joint surfaces and taller locating-pin tops retain their prior paths.
  Geometry, CAD/STL and bed poses are unchanged. Current native slices and
  validation are in `release/knot-white-hilbert-r1/`. Fabric-like appearance,
  sheen and feel remain physically unqualified.

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
  unchanged. In this separate project only, `is_infill_first = 1` replaces 0;
  each knot object's `support_interface_spacing = 0.2` replaces inherited 0.5.
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
