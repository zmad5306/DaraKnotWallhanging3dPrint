> Promoted to the main [Letter.3mf](../../Letter.3mf). Use that file. This separate candidate is historical; see the [current validation](../../release/letter-veneer-correction/README.md).

> Superseded filename: the current correction candidate is [Letter Veneers](<../Letter Veneers/README.md>), with meaningful plate/object names and no version in its filename. This folder is historical evidence.

# Current ERYONE veneer candidate r10

`Dara-A2L-Veneers-ERYONE-r10.3mf` supersedes the r9 candidate for this investigation. Open it as a project. It contains all three full-size veneers, on plates 1–3, using the saved A2L/H2S-compatible production printer profile. Root `Letter.3mf` remains unchanged.

## User-supplied spool limits

The user supplied **190–220°C nozzle, 55–70°C bed, 30–60 mm/s print speed** on 2026-10-25. These limits, rather than a different generic ERYONE product's specification, govern this revision.

- Printing nozzle: **220°C**, first and subsequent layers. The saved upper temperature recommendation is corrected from 240 to 220°C.
- Textured PEI bed: **55°C**, first and subsequent layers.
- Startup filament flushing: **220°C**, replacing the previously resolved 240°C automatic flush temperature. The native machine-start template is unchanged; its material-dependent temperature resolves to the corrected value.
- All model, carrier and generated support XY extrusion commands are **30–60 mm/s**. Outer-wall setting remains 40, first-layer wall setting remains 50, inner walls reduce 80→60, and infill/top/support settings cap at 60. Small-perimeter and cooling slowdown minimums are 30. Filament bridge speed changes 25→30; severe-overhang settings change 10→30 to meet the requested lower bound. The exact 18 global changes and three object changes are in `validation.json`.
- Print/travel acceleration remains capped at **1500/2500 mm/s²** from r9. Cooling fan settings, 7.5 mm³/s volumetric limit, 0.98 flow and retraction remain unchanged.

Print speed here means the feedrate of commands that move in XY while extruding the part or support. Non-extruding travel remains 500 mm/s maximum. Retraction, startup priming/calibration, and actual acceleration/deceleration through corners are separate. The printer retains its 140°C nozzle-probing routine and normal off commands; all model/support extrusion occurs with a 220°C nozzle target and 55°C bed target.

## Preservation and verification

All geometry, support paint, plate poses, solid veneer settings, tree supports, bed bands, connections and r9 carrier-edge corrections are retained. Editable mesh assets are byte-identical to r9. Native serialization was compared: faces and paint match, and vertex/placement differences stay below 0.0001 mm. The 0.4 mm nozzle, 0.20 mm initial/subsequent layers, four walls, five top/bottom layers, Textured PEI and gyroid pattern remain unchanged. Geometry source snapshots are adjacent SCAD/STL files.

All three plates were freshly sliced with Bambu Studio 02.08.02.61, clean process exit 0. Every model/support extrusion command was checked for the requested speed and temperature ranges; **zero out-of-range commands**. Checksums, bed bounds, acceleration limits and all 102 previously moved edge connections passed. The only native warnings remain the existing traditional-timelapse warnings (10018003 and 1000C003). No printer job was sent.

| Veneer | Plate | Estimated time | Material including supports |
|---|---:|---:|---:|
| V1 | 1 | 25h 42m | 332.06 g |
| V2 | 2 | 24h 52m | 317.22 g |
| V3 | 3 | 21h 04m | 254.82 g |

Combined material: **904.10 g**, below 1000 g.

**Physical status:** no r10 print has been evaluated. The reported whole-part rearward shift remains unresolved; compliance with the spool limits does not establish its cause or prove it corrected. In particular, the revised bridge/overhang minimum is faster than r9 and its physical finish/support behavior remains unqualified.

Source r9 SHA-256: `0eeb8b60ce2624a802416906e51126d4e63d879b2f00ab30b63f86e1339b7b75`.

Current r10 SHA-256: `b2d2a7b0299ddc1b604d557f5c90d2f4052297461487a1afc6fa47136d164ee9`.

Rebuild/audit commands, from the repository root: `python scripts/set_veneer_eryone_spool_limits.py build`, then `slice`, `validate`, and `package`. The original source hash is checked before building. Root production project hashes are checked during validation and packaging.
