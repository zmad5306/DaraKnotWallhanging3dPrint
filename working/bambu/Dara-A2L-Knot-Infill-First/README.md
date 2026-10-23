> **Historical record:** the 3MF files in this folder are retired from source control. Use Knot.3mf at the repository root. This document records the original revision; retrieve commit `5dab12a` and its LFS objects if the historical projects are needed.

# Dara A2L knot — infill first, r1

**Print F1-F10 from `Dara-A2L-Knot-Infill-First.3mf`, opened as a project in Bambu Studio.** These are the ten full-size knot parts, with plate numbers matching plates 1-10 in the main project. The editable companion contains the same geometry and settings without stored slices.

Use the existing main `Dara.3mf` for the M parts on plates 11-17 and accessories on 18-20, or use the existing A1 companion for accessories. Skip the main project's old knot slices; do not print both sets.

The user reported the full-curve r3 infill-first test worked, requested production promotion, commit/push/PR, and then explicitly chose a separate knot project to preserve M settings. Bambu uses infill-first globally: saving it on individual objects did not change the actual path order. This project isolates the change to the knot while the root/named complete/editable main projects and A1 files remain byte-identical.

## Correction

- Print infill first: **OFF → ON** in this separate project.
- Support top interface spacing: **0.50 → 0.20 mm**, saved on each F1-F10 object.
- Preserve two top interface layers, the **0.20 mm top Z gap**, tree supports, bridge/overhang speeds, cooling, temperatures, flow, brims, and purge settings.

All ten parts retain their full production geometry, colors, orientation, actual bed positions, screw reinforcement modifiers and material boundaries. The 42 removed lower-lap pads stay removed. There is no crop or redesign. Moving from twenty plates to ten changes Studio's display-grid offsets and trims tower position arrays; it does not move parts or towers on their beds.

A2L / 0.4 mm nozzle / Textured PEI. **8% gyroid, 0.20 mm initial and regular layers, four walls, five top and bottom layers.** Existing local screw zones remain 100%. Filament slots remain 1 white, 2 wood tan, 3 copper silk, 4 Azurite blue. The knot uses slots 1, 2 and 4. The artwork remains 914.4 mm wide.

## Print estimates

Native Bambu Studio estimates include supports and purge: **2,271.96 g / 80 h 44 min** across all ten plates.

| Plate / part | Time | Material |
| --- | --- | --- |
| 1 / F1 | 8 h 06 min | 224.58 g |
| 2 / F2 | 7 h 10 min | 208.27 g |
| 3 / F3 | 9 h 02 min | 248.75 g |
| 4 / F4 | 9 h 02 min | 251.35 g |
| 5 / F5 | 7 h 15 min | 208.03 g |
| 6 / F6 | 7 h 49 min | 221.85 g |
| 7 / F7 | 7 h 24 min | 204.79 g |
| 8 / F8 | 8 h 51 min | 248.38 g |
| 9 / F9 | 8 h 42 min | 250.64 g |
| 10 / F10 | 7 h 24 min | 205.32 g |

## Verification and physical scope

`source-provenance.json` identifies the source objects and unchanged mesh hashes. `validation.json` records native slicing and reopening; full editable/native mesh, pose and effective-setting comparisons; actual first-supported-layer fill-before-wall order; material heights and finish directions; all 42 corrected lap locations; bed/tower clearances; G-code checksums; and main/A1 hashes before and after. Only traditional-timelapse compatibility notices are accepted. A saved native preview of plate 2 is included. No fresh GUI review or printer job is claimed.

The user's success applies to the supplied [r3 full-curve test](../../../output/Dara-A2L-Photo-Curve-Infill-First-r3/README.txt), a 4 mm high production cutaway. The locally printed hash was not independently read. **Full-size print quality, finish and support cleanup remain physically unqualified.**

Production source SHA-256: `64cd3a8d9a07f55028201c68f8c48ef1ad1fdcf32d4391811a3b5ab7eded5f13`.

Current sliced knot project SHA-256: `2510f6f9bd0139155d7aea0603b0e24c3e5c9ac414f946abf9aadf1464f9c356`.

`SHA256SUMS.txt` lists the delivered files. Build with `scripts/build_knot_infill_first_project.py` (`build`, `slice`, `reopen`, `validate`); run `scripts/audit_knot_infill_first.py` for the portable release audit. The builder is pinned to the recorded production hash and does not write to the main project.
