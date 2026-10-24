# Unused filament removal — October 23, 2026

The user requested removing unused copper from Knot and unused white, wood and
blue from Letter, then committing and pushing both projects.

| Project | Previous slots | Current slots |
| --- | --- | --- |
| Knot | 1 white, 2 wood, 3 unused copper, 4 blue | 1 white SUNLU PLA Basic, 2 wood SUNLU PLA Basic, 3 blue SUNLU PLA Metallic |
| Letter | 1 unused white, 2 unused wood, 3 ERYONE copper, 4 unused blue | 1 ERYONE Ultra Silk Copper |

All removed slots were unused by object/volume assignments and stored native
slices. Every surviving filament value is copied exactly from its former slot,
including temperatures, flow, cooling, retraction and profile identity. The
retained purge matrix entries are unchanged. The material arrays and object
assignments are compacted consistently, including AMS drying tuples. These are
project changes; the user's installed filament presets are unchanged.

The ten Knot plates and six Letter plates were natively resliced in Bambu
Studio 02.08.02.61. The final containers retain the original geometry, poses,
support paint and object/volume settings except the requested slot indexes.
Native save/reopen comparisons verify every edited project setting, effective
object/volume setting, mesh and pose. CAD and STL files remain byte-identical.

Actual native extrusion moves were checked for material-specific layer heights,
bead bounds and bed clearance. Knot retains five blue layers at printed
Z12.8/13.0/13.2/13.4/13.6, with the original modifier spanning Z12.5–13.5. All
G-code checksums are verified, and G-code configuration changes are limited to
the compacted filament arrays and native nozzle mapping. Only the existing
traditional-timelapse notices remain. Native path order and timing may differ
slightly after reslicing; this is not a claim of byte-identical command streams.

| Project | Native time | Material |
| --- | ---: | ---: |
| Knot | 81h 02m | 2278.10 g |
| Letter | 72h 17m | 1223.80 g |

`provenance.json` records the source hashes and exact array changes.
`knot-validation.json` and `letter-validation.json` tie those sources to the
current projects, unchanged archive entries, native round trips and per-plate
checks. The corresponding `*-native.json` files contain the slicer results.
Earlier release evidence remains tied to the exact preceding revisions.

All other root projects and the successful ERYONE sample are unchanged. Physical
qualification is unchanged; no printer job was sent.
