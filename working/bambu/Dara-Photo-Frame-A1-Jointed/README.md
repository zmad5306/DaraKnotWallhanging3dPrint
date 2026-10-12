# Complete A1 print project

[Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) contains one
complete assembly: 39 distinct production parts and 70 assembly pieces across
plates 1-29, plus **nine fit-test pieces on plate 30** (79 pieces total).
It includes editable models, local infill modifiers, plate thumbnails, and sliced
toolpaths. The file is stored with Git LFS; run `git lfs pull` after cloning.

The [four-page part and plate map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf)
shows the 29 production plates: frame and M assembly positions, backer and wall-block
locations, and the three shared production plate layouts. Assembly maps all use
the same front-view orientation. Plate 30 is described in the
[fit-test guide](../../stl/Dara-Print-Checks/README.md).

| Plates | Parts | Quantity |
| --- | --- | --- |
| 01-20 | F1-F20 | One section per matching plate |
| 21-26 | M1-M6 | One section per plate, in order |
| 27 | Backer1, Backer3, Backer5, Backer7 | One each |
| 28 | Backer2, Backer4, Backer6, Backer8 | One each |
| 29 | B1-B4 and Retainer | One of each block and 32 retainers |
| 30 | Photo, B1, M and lap fit tests | Nine test pieces; print first |

## Print settings

- Bambu Lab A1, 0.4 mm nozzle, Generic PLA, textured PEI plate, 0.2 mm layers.
- Four wall loops and 15% gyroid infill for the body.
- Local 100% infill around M screw seats and pilots, photo-tab screws, wall-block
  screws, wall keyhole seats, and retainer screw seats. The lap tongues and roots
  use the normal body settings. This follows the reference's modifier placement;
  its physical joint test used six walls and 30% infill, not four walls and 15%.
- All parts keep their original scale and rear-down print orientations.
- Backers print four per plate, by layer, with no brim or supports. Their minimum
  spacing is about 1.8 mm, with a 1.5 mm model clearance from the bed edge.
- The tightest frame and M plates use a 1 mm brim and zero additional support-base
  expansion to keep their generated toolpaths on the bed.

The supplied project was sliced in Bambu Studio 02.08.02.61. All 30 plates finished
without slicer warnings. Extrusion paths, including support and brim widths, stay
inside the 256 mm bed; the corrected minimum checked edge clearance is 0.673 mm
on plate 06. Estimated
production use is 3.254 kg of PLA and 111.7 hours. Plate 30 adds 160.18 g and
5 h 30 min, for approximately 3.414 kg and 117.2 hours total. These are slicer estimates.

[project-validation.json](project-validation.json) records the final project hash,
part quantities and source hashes, placements, modifiers, per-plate estimates,
toolpath bounds, and the geometry comparison after Bambu Studio re-export. All
normal meshes match the source STLs within 0.0001 mm. Purchased screws and
reference M washers are not printed parts.

[PRINT-READINESS.md](PRINT-READINESS.md) records the final review, hardware list,
assembly order, and required physical fit checks. The user confirmed on
2026-10-12 that the current photo, wall-block, and M hardware fits are untested.
The digital audit does not qualify those fits or the wall mounting load.

The tracked `scripts/validate_print_project.py` independently verifies current
source hashes and solids, assembled interference, lap order, all 3MF placements,
82 reinforcement modifiers (73 production and nine test), plate quantities, and saved G-code bounds. It accepts
Bambu's compact decimals such as `E.123` and `I-.5`, which the earlier scratch
checker missed. [final-review.json](final-review.json) contains the corrected
audit. The original production toolpaths are byte-identical after adding plate 30.

```powershell
python -m unittest discover -s scripts -p test_validate_print_project.py
python scripts/validate_print_project.py
```

## Rebuilding

`python scripts/build_jointed_bambu_project.py`, run from the repository root,
creates the initial **unsliced, 29-plate production** 3MF and layout report from the validated STL set
and tracked joint-test preset. It replaces the output project and report. The
supplied sliced project was subsequently exported and verified in Bambu Studio.
Re-slice and refresh validation before replacing that published artifact.

To add the test plate after building/saving the production project, run
`python scripts/append_print_check_plate.py`. It exports the nine named coupons
and stages `.work/print-check-plate/with-tests.3mf`. Slice plate 30 in Bambu Studio;
the saved project uses the production four-wall/15% profile and local solid screw
zones, not a whole-coupon 100% infill override. `scripts/combine_print_check_slice.py`
combines the slicer's test-only export with the untouched production project and
produces a candidate for `scripts/validate_print_project.py`. See its module
documentation; publishing is separate from staging and validation.

The PDF uses the saved project's actual object-to-plate mapping, checked against
the validation report, and projects the source meshes into their CAD assembly
positions. To regenerate it from the validated project:

```powershell
python scripts/build_part_layout_map.py prepare
python scripts/build_part_layout_map.py render
```

The prepare stage needs numpy, shapely, and trimesh. The render stage needs
reportlab and can run with a separate Python interpreter. Intermediate map data
goes in ignored `.work/part-layout-map/`; the final PDF goes in `output/pdf/`.
