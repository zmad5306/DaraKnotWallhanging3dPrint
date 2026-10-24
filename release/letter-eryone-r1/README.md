# Letter ERYONE filament promotion — October 23, 2026

The user reported, "This test was a raging success," and requested its filament
in the main Letter project. The supplied file is
`C:\Users\Zach\Desktop\Dara-A2L-Hammered-Finish-ERYONE-r3.3mf`, SHA-256
`b82b2356c92c14640b4107405c0fde04488d61ced29d34821572c8b84003f0f6`.
It exactly matches the tracked ERYONE **r4 with r8 wall-base cleanup** sample;
the Desktop filename retains r3. The supplied file and tracked sample are unchanged.

`Letter.3mf` slot 3 now uses the sample's exact ERYONE Ultra Silk Copper profile
name, including its saved sample filename suffix, and ERYONE vendor. The five
cores and three veneers all use slot 3. The actual printing parameters already
matched, including the following values:

| Parameter | Saved value |
| --- | --- |
| Printer / nozzle | Bambu Lab A2L / 0.4 mm |
| Nozzle first / subsequent | 220 / 220 C |
| Textured PEI first / subsequent | 55 / 55 C |
| Filament flow ratio | 0.98 |
| Maximum volumetric speed | 7.5 mm3/s |
| Minimum / maximum fan | 60 / 80% |
| Minimum cooling slowdown speed | 20 mm/s |
| Layers / walls / top / bottom | 0.20 mm / 4 / 5 / 5 |
| Structural infill | 8% gyroid |
| Veneers and bonded carriers | Existing 100% overrides |

The complete source comparison is in `validation.json`. Outside filament
identity, the only global differences from the sample are the process display
name, six-plate tower arrays and AMS dryer array serialization. Those existing
Letter fields are retained. They do not change extrusion. All three veneer
object overrides also match the successful sample.

No slicing was needed: all six native command streams, and every byte outside
the two filament identity comments, are unchanged. Those two comments now
match the saved project and sample; each G-code MD5 and the release SHA-256
catalog are updated. All geometry assets, support paint, object/volume settings,
poses, thumbnails, plate metadata, estimates and CAD/STL are preserved exactly.
The project was reopened successfully by Bambu Studio's native CLI. The
validation records hashes, locked settings and the protected files.

The retained estimates are **72h 17m / 1,223.80 g** for all six plates and
**60h 5m / 904.11 g** for the three veneers including supports. Existing native
geometry and toolpath checks remain applicable because their inputs and printer
commands are unchanged. No new geometric qualification or native reslice is
claimed. Only the existing traditional-timelapse notices remain.

The physical result is the user's success report for the supplied sample.
The file contains the A2L profile; the actual printer and printed-file hash were
not independently observed. No separate measured fit or finish results were
provided, and full-size Letter anti-warp performance remains unqualified.
No printer job was sent.

`scripts/promote_letter_eryone.py` records the guarded migration from the exact
previous Letter hash. `python scripts/audit_root_projects.py` checks the current
release without modifying it. Older r7/r8 reports remain historical records.
