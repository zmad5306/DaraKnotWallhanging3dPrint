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
- Veneer tree supports stay enabled. Preserve the bonded fins and their saved
  orientation; the fins restrain the veneer and do not prove that unsupported
  spans will print. A support-enabled flag does not establish local backing.
- The saved veneer rotation is shared across all three veneers: 55-degree lean
  and the existing in-plane orientation. Do not auto-orient individual veneers.

## Printer and project identity

- The main production project is root **`Dara.3mf`**, for the **A2L**.
  `working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf` is its named complete
  copy; `Dara-A2L-Editable.3mf` in that folder is its generating source.
- A2L plates **1-10** are the knot, **11-14** the M cores, and **15-17** the M
  veneers. Keep the M parts unchanged unless the user explicitly requests an
  M change, including their geometry, settings, placements and stored slices.
- `working/bambu/Dara-A1-Companion/` contains the matching A1 accessories. Keep
  it unchanged unless explicitly requested. Its plates 1-3 replace A2L plates
  18-20; all production M parts remain on the A2L.
- The older complete A1 design is historical and is not the current production
  baseline. Its settings and joints must not silently replace A2L settings.
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
- The current direct reference is
  `working/bambu/Dara-A2L-Production-Joint-Sample/Dara-A2L-Production-Joint-Sample.3mf`.
  It is cropped from production J4, with corrected straight crop boundaries.
  Its outline validation does not qualify joint fit. As of 2026-10-19, a
  successful physical result for this revision has not been reported.
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
