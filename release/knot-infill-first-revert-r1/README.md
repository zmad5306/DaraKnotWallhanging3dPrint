# Knot infill-first rollback — October 24, 2026

> Historical source revision: the subsequent [normal-support revision](../knot-normal-supports-r1/README.md) changes only support type and reslices all ten plates. Infill-first remains off. The hashes and checks below describe the exact rollback source before that support change.

Current file: **root `Knot.3mf`**, Bambu Lab A2L, ten plates F1–F10. Open it as a project.

The user reports that the first three full-size pieces, printed a second time, have keys that do not fit their joint grooves. The user requested infill-first off. The exact printed file hash/printer were not independently observed. The cause is not established by digital checks.

## Change

`is_infill_first`: **1 → 0**, globally. All ten plates have fresh native slices from Bambu Studio 02.08.02.61. No key/groove dimensions or other process/material options were changed. Object support-interface spacing stays 0.20 mm; support top gap stays 0.20 mm.

The original 8% gyroid, 0.4 mm nozzle, 0.20 mm initial/regular layers, four walls, five top/bottom layers, Textured PEI, three filament profiles, temperatures, speeds, flow, colors, poses, supports and purge settings remain. All CAD/STL and the other six root projects remain byte-identical. All 42 removed lap pads remain absent. All 50 solid screw modifiers remain at Z12.4; the five blue layers remain at native Z12.8–13.6.

## Checks actually performed

1. **Settings and preservation:** full setting dictionaries and every G-code configuration differ only in `is_infill_first`. Original geometry, support paint, object/volume overrides and actual poses are retained. Native slicing and final native reopen were compared with the editable source. Protected files were hashed before/after.
2. **Current joint meshes:** original triangle sections of all 14 joints / 28 keys, including 420 transverse probes. Keys measure approximately 3.00 mm; primary grooves 3.30 mm; relieved secondary grooves 4.40 mm. Key tops are Z6.00 and groove roofs Z6.30. Minimum nominal section clearance is about 0.149 mm. Serialized meshes contain only overlap slivers below 0.0001 mm thickness; the largest is about 0.0000271 mm. No release geometry was welded or regenerated.
3. **Actual emitted paths:** 140 key/groove layer comparisons at Z5.2, 5.4, 5.6, 5.8 and 6.0. Key walls precede fill. Idealized commanded bead envelopes do not overlap; minimum separation is **0.1279 mm**. All ten plate checksums, bed/tower clearances, material heights, finish directions, 42 pad sites and five-layer screw-skin continuity checks pass. Stored notices concern unavailable traditional timelapse only.

The bead envelopes use commanded G1 positions and line widths. They do not measure actual deposited PLA, sag, swelling, shrinkage or support residue. The original `is_infill_first = 0` behavior also restores the former photo-rabbet feature order; no substitute geometry or support change was introduced.

## Estimates

| Piece / plate | Native time | Material |
| --- | ---: | ---: |
| F1 / 1 | 8h 08m | 225.21 g |
| F2 / 2 | 7h 11m | 208.84 g |
| F3 / 3 | 9h 03m | 249.29 g |
| F4 / 4 | 9h 03m | 251.92 g |
| F5 / 5 | 7h 16m | 208.68 g |
| F6 / 6 | 7h 52m | 222.49 g |
| F7 / 7 | 7h 25m | 205.49 g |
| F8 / 8 | 8h 52m | 248.96 g |
| F9 / 9 | 8h 43m | 251.21 g |
| F10 / 10 | 7h 26m | 206.02 g |
| **Total** | **81h 00m** | **2278.10 g** |

These are slicer estimates. **The rollback is physically unqualified.** The earlier full-curve test does not establish full-size key fit. The already printed pieces are not changed by this file update. No printer job was sent.

## Identity and evidence

- Current SHA-256: `388cf37776eebfb59c714b5d0d54e4f8f52d3eff70e7a51da2df81fccfba92e4`
- Source SHA-256: `a4e5fdde354253f504c466807361e058a0523213ccc28c365ca3aa9186b67992`
- `provenance.json`: exact source, authorized change and protected hashes.
- `validation.json`: saved/native/reopened comparisons, per-plate checks and estimates.
- `joint-geometry.json`: current embedded-mesh measurements.
- `joint-toolpaths.json`: commanded envelope and ordering checks, with physical limits.
- `native-result.json` and `native-reopen.json`: native slicer results.

Earlier reports remain historical and are linked through the source hash; they are not rewritten to describe this rollback. The old infill-first full-size configuration is withdrawn. Run `python scripts/audit_root_projects.py` to check the current distributed files and evidence chain.
