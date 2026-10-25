# Knot normal supports — October 24, 2026

Current file: **root `Knot.3mf`**, Bambu Lab A2L, ten plates F1–F10. Open as a project.

**October 25 update:** the user reported "Joints are ok" after the current r2 J3 photo-retainer sample and approved production publication. That sample was cropped from this exact production hash. See [the publication record](../knot-joint-approval-r1/README.md). This updates sample joint-fit status only; the digital measurements below are unchanged, and full-size performance/bolster appearance remain unconfirmed.

The user requested normal supports instead of trees. The only setting change is **`support_type`: `tree(auto)` → `normal(auto)`**. All ten plates have fresh native Bambu Studio 02.08.02.61 slices.

Infill-first stays **off**. Support style remains `default`; supports remain enabled per object. Saved support paint, build-plate-only support, 0.20 mm object interface spacing, 0.20 mm top and bottom gaps, interface layers, support speeds/material and every other parameter are preserved. Structural 8% gyroid, 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers and Textured PEI remain. Original geometry, poses, CAD/STL, filament profiles and the other six root projects are unchanged. Letter's veneer tree supports are unchanged.

## Verification

- Exact comparison of all project settings and every G-code configuration: only support type differs.
- Native slice/save and final native reopen comparisons retain geometry, poses, paint and object/volume settings. Protected artifacts are hashed before/after.
- All ten G-codes contain `normal(auto)`, `is_infill_first = 0`, positive support and support-interface extrusion, valid checksums, and verified bed/tower clearance including actual supports.
- All 14 joints / 28 keys measured from embedded triangles; 140 current key/groove path comparisons preserve walls preceding fill and nonoverlapping idealized commanded bead envelopes. Minimum commanded clearance: **0.1279 mm**.
- All 42 removed lap-pad sites, five blue layers, all 50 Z12.4 reinforcement modifiers and five-layer top-skin continuity remain. Actual top-surface directions are preserved. Stored notices concern unavailable traditional timelapse only.

Commanded bead envelopes do not measure deposited PLA, sag, support residue or physical fit. **Normal-support removal and full-size joint fit remain physically unqualified.** The preceding reported full-size fit failure remains recorded; this change does not establish its cause. No printer job was sent.

Normal supports include Bambu's `Support transition` paths inside joint grooves. These are classified as removable support, excluded from model-fit measurements, and included in bed/tower clearance checks. An initial audit flag exposed this previously unhandled support label; the parser was corrected and the current checks rerun. Groove support material must be removed before assembly; digital checks do not establish cleanup quality.

## Native estimates

| Piece / plate | Time | Material |
| --- | ---: | ---: |
| F1 / 1 | 7h 36m | 225.49 g |
| F2 / 2 | 7h 10m | 209.51 g |
| F3 / 3 | 8h 47m | 249.93 g |
| F4 / 4 | 8h 53m | 252.60 g |
| F5 / 5 | 7h 14m | 209.46 g |
| F6 / 6 | 7h 20m | 222.60 g |
| F7 / 7 | 7h 14m | 206.28 g |
| F8 / 8 | 8h 46m | 249.77 g |
| F9 / 9 | 8h 42m | 251.72 g |
| F10 / 10 | 7h 15m | 206.74 g |
| **Total** | **78h 57m** | **2284.10 g** |

Previous tree-support source: 81h 00m, 2278.10 g. These are slicer estimates, not measured print outcomes.

## Exact files and evidence

- Current project SHA-256: `aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46`
- Source project SHA-256: `388cf37776eebfb59c714b5d0d54e4f8f52d3eff70e7a51da2df81fccfba92e4`
- `provenance.json`: source, single authorized setting change and protected hashes.
- `validation.json`: native roundtrip/reopen, per-plate checks, checksums and estimates.
- `joint-geometry.json` and `joint-toolpaths.json`: current geometry and emitted-path measurements.
- `native-result.json` and `native-reopen.json`: native completion results.

The previous rollback and older release evidence retain their original hashes and are linked through the source chain. Run `python scripts/audit_root_projects.py` for the current release audit.
