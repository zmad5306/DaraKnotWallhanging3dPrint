> Promoted to the main [Letter.3mf](../../Letter.3mf). Use that file. This separate candidate is historical; see the [current validation](../../release/letter-veneer-correction/README.md).

> Superseded filename: the current correction candidate is [Letter Veneers](<../Letter Veneers/README.md>), with meaningful plate/object names and no version in its filename. This folder is historical evidence.

**Superseded for this investigation by `../Dara-A2L-Veneers-ERYONE-r10/Dara-A2L-Veneers-ERYONE-r10.3mf`, which applies the user-supplied ERYONE spool temperature and speed limits. This r9 file remains unchanged as historical evidence.**

# Veneer carrier-edge and acceleration candidate r9

**Status: digitally checked candidate. The reported whole-part shift is not proven resolved. No printer job was sent.**

One current candidate: `Dara-A2L-Veneers-Carrier-Motion-r9.3mf`, A2L/H2S-compatible saved production printer profile, three plates V1/V2/V3. Open as a project. Root `Letter.3mf` remains unchanged, including its core plates and stored slices. This candidate has not replaced the six-plate production baseline.

## Changes and limits

- V1: replace the abrupt 0.15 mm carrier end jog at layers 692–694 with a continuous taper over the adjacent 17.6 mm of the existing carrier edge. Add 1.581 mm³ of material; remove none above numerical tolerance.
- V3: the same correction at its two carrier ends near layers 6–7. Add 1.933 mm³. V2 geometry is unchanged.
- These additions stay within the existing carrier thickness, assembly Z3.2–4.4. Decorative veneer surfaces, connections, rear/web walls, openings and bed bands retain their geometry.
- Bambu ignores the saved per-object default/travel acceleration settings. This candidate applies project-level printing acceleration of 1500 mm/s² and travel acceleration of 2500 mm/s². Explicit outer-wall and top-surface acceleration also cap at 1500; initial-layer travel caps at 2500. Existing first-layer printing acceleration remains 500. All model/support extrusion and travel commands were checked after slicing.
- The exact changed project values are default 6000→1500, outer wall 5000→1500, top surface 2000→1500, travel 8000→2500, and initial-layer travel 6000→2500 mm/s². This is why the candidate isolates the veneers: those settings cannot be reliably limited to their objects inside the shared six-plate Letter project.
- Print/travel speed settings, flow, temperatures, cooling, retraction, material profile, 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers, Textured PEI, gyroid and solid veneers remain unchanged. Tree supports and the shared 55° lean remain. Bed placement differs only by native serialization below 0.0001 mm.

The original V1 native path shows Y=68.190 mm at its front carrier end throughout the reported band, while the rear end changes Y=251.960→251.810 mm. The user reports a physical shift across both ends and the decorative part. The one-end mesh jog does not explain that whole-part displacement. Neither the acceleration correction nor the geometry correction establishes the physical cause. The support wall's changing finish may respond to speed/cooling/acceleration transitions; that causal link is unconfirmed.

## Verification

Native Bambu Studio 02.08.02.61 sliced all three plates with exit code 0. Saved editable geometry/settings were compared with the native output. Toolpath MD5 checksums passed; extrusion stays within the bed. Model extrusion exists at all 102 previously moved edge connections (30/29/43). No new slice warning was reported; the native project retains only the existing traditional-timelapse compatibility warning if present. These checks do not establish adhesion, restraint, bond strength, removal or appearance.

At V1 layers 691–696, the former abrupt 0.150 mm end jump is reduced to at most 0.002 mm per layer. Through Z134–143, the newly sliced decorative outside path differs from the original by at most 0.0108 mm (V1), 0.0002 mm (V2) and 0.0082 mm (V3); the original decorative geometry is retained. This path comparison includes native seam/rounding effects and does not diagnose the printed displacement.

| Veneer | Plate | Native estimated time | Material including supports |
|---|---:|---:|---:|
| V1 | 1 | 23h 2m | 332.06 g |
| V2 | 2 | 22h 19m | 317.22 g |
| V3 | 3 | 19h 9m | 254.82 g |

Combined material: **904.10 g**, below the 1000 g requirement. All are full-size veneers; this is not a cropped test. No new physical result exists.

Source `Letter.3mf` SHA-256: `8e391762ecb8415b77680a7bd4825e94afe37951d831bcfe41f6a43f31b16d4a`.

Candidate SHA-256: `0eeb8b60ce2624a802416906e51126d4e63d879b2f00ab30b63f86e1339b7b75`.

The adjacent SCAD/STL files are exact mesh-based snapshots of this candidate. `validation.json` contains native estimates, settings comparisons, command-limit measurements, geometry changes and source hashes. `carrier-edges-before-after.png` plots the measured native carrier-edge paths.
