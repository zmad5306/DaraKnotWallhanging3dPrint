# Knot solid laps — October 25, 2026

Current production file: **root `Knot.3mf`**, Bambu Lab A2L, ten plates F1–F10.

The user reported **"Solids work wonderfully"** after the supplied r3 solid-lap sample and requested promotion, commit and push. Both halves of **all 14 overlapping joints** now use the accepted **100% rectilinear** fill. Bambu serializes Rectilinear as `zig-zag`. Each new modifier covers joint-local X0–18 mm and Z0–13.5 across the actual lower lap's projected outline; the matching upper half receives the same footprint. This extends the successful sample across the full joint width without changing any printable geometry. The projection masks simplify only sub-micron edges (maximum allowed outline error 0.0001 mm); no original mesh is simplified or regenerated.

The source has 28 new local settings modifiers. All original embedded body, color and screw-modifier mesh files remain **byte-identical**. The new masks add no printed stock and do not fill the key clearances, glue recesses, holes or removed pads.

## Preserved settings and reinforcement

Surrounding bodies remain **8% gyroid**. Infill-first stays **off**; supports stay **normal(auto)** with the same paint, build-plate-only activation, 0.20 mm interface spacing and 0.20 mm top gap. Nozzle 0.4 mm, layers 0.20 mm, four walls, five top/bottom layers, textured PEI, materials, temperatures, speeds, cooling, brims, poses and finish directions remain unchanged.

All **50 screw reinforcement modifiers end at Z12.4**, preserving their original 100% infill and pattern beneath the five top layers. None of the new lap masks overlaps any screw-bolster footprint. Five blue layers remain. Letter, all other root projects, their CAD/STL and the approved ERYONE sample remain byte-identical.

## Verification

- Compared every original volume, support-paint record, pose and effective setting before and after the change and after native reopen.
- Fresh native slices on all ten plates; complete G-code configurations remain identical to their source configurations, with valid checksums.
- Checked actual dense fill throughout all 28 lap regions and retained sparse fill outside them. The inherited spacing of bridge layers over supports is preserved. Commanded line-width coverage is recorded in `lap-toolpaths.json`.
- Checked all 14 joints / 28 keys geometrically and **140** key/groove layer pairs in actual native paths. Minimum commanded key clearance: **0.1279 mm**.
- Verified all 42 removed lower-lap pad sites, support backing and 0.20 mm gaps at all 28 grooves, color assignments, surface directions, all 50 bolster caps and five-layer continuity, plus bed/tower clearance including supports.
- Reopened the final project natively and synchronized 14 new shared modifier STLs, 28 CAD references and the release catalog. All pre-existing Knot STLs remain unchanged.

The physical sample result is user-reported. The actual printed hash/printer were not independently observed. Full-size fit, clamping performance and surface finish for this promoted revision remain unconfirmed. No print job was sent.

## Native estimates

| Piece | Time | Material |
| --- | ---: | ---: |
| F1 | 8h 16m | 252.03 g |
| F2 | 7h 21m | 219.40 g |
| F3 | 9h 11m | 266.52 g |
| F4 | 9h 14m | 267.51 g |
| F5 | 7h 27m | 219.62 g |
| F6 | 8h 00m | 249.52 g |
| F7 | 7h 34m | 220.22 g |
| F8 | 9h 03m | 262.21 g |
| F9 | 9h 00m | 264.58 g |
| F10 | 7h 34m | 220.50 g |
| **Total** | **82h 41m** | **2442.13 g** |

These are slicer estimates, including supports and purge structures.

## Files and evidence

- Production SHA-256: `78f22d0ff7e22da7e27a3fd4c761c1aa815a5bb26c3acea3392cbd23797c52e6`
- Source production SHA-256: `aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46` (preceding committed Knot revision).
- Accepted sample: `Dara-A2L-Joint-Solid-Laps-r3.3mf`, SHA-256 `6898ed006c82b81beafe6a90012c3e59d23e4124a75daf22d50db93e8a2a447c`.
- `provenance.json` records the user's result/authorization, exact source, masks and protected files.
- `validation.json`, `joint-geometry.json`, `joint-toolpaths.json` and `lap-toolpaths.json` record current checks.
- `native-result.json` and `native-reopen.json` record native completion.

Earlier rollback, normal-support and r2 approval reports retain their historical hashes. Run `python scripts/audit_root_projects.py` to audit the current release and its source chain. The accepted sample evidence lives in `output/Dara-A2L-Joint-Solid-Laps-r3/`; the repository's existing production-only 3MF inventory is preserved.
