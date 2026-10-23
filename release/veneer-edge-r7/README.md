# Veneer perimeter correction — October 22, 2026

Current files: root `Letter.3mf` and
`release/samples/Dara-A2L-Hammered-Finish-ERYONE-r4.3mf`.
The sample corrects the exact supplied Desktop r3 file, preserving its crop,
bed placement, filament profile and process. The original crop in production
coordinates was X208..330, Y67..165, Z0..75 mm. r4 supersedes r3. Saved object
and process labels still say r3; identify this correction by filename/hash.

The original cleanup pockets opened through the veneer edge. V1/V2/V3 now
move 30/29/43 connections inward; the sample moves 15. The pockets retain their
2.60 mm square footprint and 0.40 mm depth. New pocket positions leave at least
1.69 mm of perimeter stock. The complete perimeter has a checked 1.20 mm rim.
Old openings are filled from the same saved mesh's intact perimeter, restoring
the nominal Z8.6 back plane. Obsolete upper stems and their tiny detached
remnants are removed. New 1.20 mm square necks run from assembly Z4.3 to Z9.2.

The decorative surface above Z9.2, all core geometry, interior connections,
wall carrier below Z4.4, wall openings and two end bands are preserved.
The corrected meshes are watertight and remain connected to their carriers.
The six-plate layout, poses, filament profiles, cooling, speeds, supports and
effective process overrides remain fixed. Native saving normalizes only the
recorded empty preset bookkeeping. The original normal-based decorative-face
support-blocking rule is reapplied to the replacement triangulation; native
saving preserves that paint. The other six root projects are byte-identical.
Adjacent Letter STL/CAD and the release catalog are synchronized.

All six Letter plates and the sample were freshly sliced with Bambu Studio.
Editable/native geometry, poses, paint and effective settings were compared.
G-code confirms 8% gyroid globally, a 0.4 mm nozzle, 0.20 mm layers, four walls
and five top/bottom layers, with the saved 100% solid veneer/carrier exception.
Tree supports, slot 3 and Letter infill-first off are preserved.
All 102 moved production connections and 15 moved sample connections have
model extrusion in the native toolpaths. Toolpath bed bounds, startup tower
clearance and G-code checksums passed. Core toolpaths also fit the A2L bed.
There are no geometry warnings; only the existing traditional-timelapse notice.
Current Letter includes slices for all six plates; its input was unsliced.

| File / plates | Slicer time | Material including supports |
| --- | ---: | ---: |
| Letter, all six plates | 72h 19m | 1,223.65 g |
| Letter, veneers only, plates 4–6 | 60h 7m | 903.96 g |
| ERYONE r4 sample, A2L | 2h 26m | 34.15 g |

`release.json` records exact current/protected hashes. `*-geometry.json` records
source hashes, every old/new connection coordinate, volume/rim checks and stem
remnants. `*-native.json` records final slice hashes, preservation comparisons,
toolpath probes, warnings and estimates. `edge-comparison.png` shows actual
sample mesh sections at assembly Z8.8 before/after.

Physical cutting, flush seating, finish, adhesion and full-size anti-warp
performance remain unqualified. Let the print cool, support the face and cut
the individual necks through their hidden rear pockets; do not peel the carrier
off. No printer job was sent. Historical carrier builders retain obsolete
edge-open pockets and must not regenerate the current mesh-based release.
