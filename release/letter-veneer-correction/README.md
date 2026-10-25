# Main Letter veneer correction

The user requested correcting all three full-size veneers, using the ERYONE spool limits, meaningful names without versions, and promotion into the main `Letter.3mf` followed by commit and push. **[Letter.3mf](../../Letter.3mf) is now the current file.** The separate output candidates are historical.

The left carrier had a 0.15 mm end step at the reported Z138.4–138.8 band. That step and two similar near-bed steps on the center carrier are replaced with continuous tapers. The right carrier had no matching step and its geometry is retained. The additions are confined to the existing inclined carrier thickness; decorative faces, veneer edges, connections, end bands, other walls, support paint and orientations are preserved. Exact geometry measurements are in `validation.json`.

All six plates use the corrected shared process and filament settings. All six are freshly sliced; no old core G-code is retained against changed project settings. All five core meshes, reinforcement, bed poses and object/volume overrides match the preceding main project. The cores now also use the approved limits; their printing speeds and acceleration therefore change.

- **220°C printing nozzle; 55°C Textured PEI bed; 220°C flushing.**
- **30–60 mm/s** commanded XY model/support extrusion; maximum **1500 mm/s²** printing and **2500 mm/s²** travel acceleration.
- Nozzle probing at 140°C, priming/calibration, non-extruding travel, retraction and off commands retain the saved machine routine. The printing range describes commanded feedrate, not instantaneous physical speed through corners.
- 0.4 mm nozzle, 0.20 mm initial/subsequent layers, four walls, five top/bottom layers, structural 8% gyroid, solid veneer/carrier overrides and tree supports remain. Cooling fans, 0.98 flow, 7.5 mm³/s volumetric limit, retraction and the ERYONE profile identity are preserved.

## Native verification

Bambu Studio 02.08.02.61 completed the six-plate slice and reopening/export with exit 0. Compared with the prepared input, native meshes have **0 mm vertex difference**, with identical faces, support paint and effective settings; original bed poses remain within the 0.0001 mm comparison tolerance. Only source-bookkeeping matrices change during native export. Every new G-code stream passes speed/temperature/acceleration, bounds and checksum checks. All 102 moved edge connections have model extrusion at their probes. The only native notices concern traditional timelapse.

All three fresh veneer slices have **1,469 inspected decorative-face layers**, Z3.6–297.2, with no missing 0.20 mm layers. Exact triangle-section comparisons and full-height traces of both carrier ends are saved in [the continuity report](continuity.json) and [plot](all-veneer-continuity.png). Apparent extrema jumps near the top/bottom were checked against complete mesh sections in [the transition inspection](transition-inspection.json) and [plot](carrier-end-transitions.png). These are narrowing-tip/perimeter-closure transitions, not a whole-wall translation. The left carrier's former step is continuous through the reported height.

| Plate | Contents | Estimated time | Material |
|---:|---|---:|---:|
| 1 | Core C1 | 5h 50m | 98.92 g |
| 2 | Core C2 | 4h 40m | 79.19 g |
| 3 | Cores C3/C4/C5 | 7h 56m | 141.58 g |
| 4 | Left letter veneer | 25h 42m | 332.06 g |
| 5 | Right letter veneer | 24h 52m | 317.22 g |
| 6 | Center letter veneer | 21h 04m | 254.82 g |

Veneers including supports: **904.10 g**, below 1,000 g. All six plates: **90h 07m**, **1223.79 g**. These are slicer estimates.

## Physical evidence and limits

The user reported the failed print as Plate 5 of Letter, photographed from the printer's right side, with a shift across the part and both ends of the support wall. The former saved name and selector numbering conflict is retained in the evidence; the exact printed hash was not obtained. The user has not printed or inspected the other veneers. All three were digitally inspected here.

**The cause of the physical whole-part shift remains unresolved.** This file contains the verified geometry/process corrections but has no successful physical print result. Full-size stability, finish and changed bridge/overhang behavior remain unqualified. No printer job was sent.

Main project SHA-256: `d8e0bd1a4664db2a75291ce2418578c4c37ef86f1459572aa742aef4018ace9c`.

Preceding named main project SHA-256: `75b14a311d5a92ad5cfd6fd4ff1a8228a19ed2e027a04b67b02439fd74905ecd`. Approved correction candidate SHA-256: `6bcfc5bbc39382607d28d6a840f66e96b66051d22ca4df30ca41900f99c468f1`. The preceding name-only preservation record remains in `../letter-veneer-names/`.

Run `python scripts/audit_root_projects.py` for the portable release audit. `scripts/audit_veneer_surface_continuity.py` inspects the current main project's three named veneers. `scripts/promote_letter_veneers.py` records the one-time promotion, native slicing and packaging procedure from the exact source hashes.
