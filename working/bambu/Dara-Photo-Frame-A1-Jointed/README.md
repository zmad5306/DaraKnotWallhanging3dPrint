# Complete A1 print project

[Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) contains one
complete assembly: 39 distinct production parts and 70 assembly pieces across
plates 1-29, plus **ten test pieces on plate 30** (80 pieces total).
It includes editable models, local infill modifiers, plate thumbnails, and sliced
toolpaths. The file is stored with Git LFS; run `git lfs pull` after cloning.
Studio regenerates Preview when reopening the editable project; use **Slice all**
with the saved settings if it requests slicing again.

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
| 30 | Photo, B1, M, lap and full-width weave tests | Ten test pieces; print first |

Plate 30 includes a **68.45 x 24 x 13.5 mm** full-width sample cropped from F7.
Both white rails and the recessed wood weave use the production geometry and
layer settings. The three small photo coupons were moved to make space.

## Print settings

- Bambu Lab A1, 0.4 mm nozzle, textured PEI plate, 0.2 mm layers.
- Project filament 1: **white `#FFFFFF`, Generic PLA** - frame, backers,
  wall blocks, retainers, and test-piece bodies except the M letter.
- Project filament 2: **wood tan `#C2AB84`, Generic PLA** - the recessed weave
  and its backing skin on F1-F20 and Test-Weave-Full-Width. This is ordinary wood-colored PLA.
- Project filament 3: **copper `#B87333`, Generic PLA Silk** - M1-M6 and
  Test-M-Letter. Copper outer walls and top surfaces run at 40 mm/s.
- Match these project colors to the loaded AMS Lite spools in the print dialog;
  the project numbers are not a requirement to use particular physical slots.
- Nozzle 220 C. Saved textured-plate temperatures are 65 C for white/wood
  and 55 C for copper. The mixed test plate starts at 55 C and switches to
  65 C in its saved toolpath. Copper uses the Generic PLA Silk flow/retraction
  profile, with a 7.5 mm3/s maximum volumetric speed (white/wood: 12 mm3/s).
  Colors are display approximations of the filament.
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

The production meshes and joints are unchanged. Twenty-one filament
modifiers (20 frame sections plus the weave test) assign wood only at Z=8.4-9.6 mm: a 0.6 mm backing skin plus the
0.6 mm raised weave. This keeps the recess between threads wood-colored too.
The weave is printed in place; no separate inserts or painting are required.
Keep the modifiers when editing. Plain STL exports do not retain color settings.

The frame plates use six mixed-color layers (layers 43-48), with six filament
changes per plate. Prime towers are placed in clear areas; flushing into the
model, infill, and supports is disabled to keep residual dark color out of white
surfaces. Plate 30 switches white/copper through the letter coupon's height,
with wood added on layers 43-48, for 59 changes in total. Production M plates and white accessory plates
each use one filament.

The supplied project was sliced in Bambu Studio 02.08.02.61. All 30 plates
finished. Extrusion paths, including support, brim, and prime-tower bead widths,
stay inside the 256 mm bed. The minimum checked edge clearance is
0.673 mm on plate 06. Plates 21-29 carry only the slicer's
`not_support_traditional_timelapse` notices; leave timelapse off when printing
those plates. No other slice notices were recorded.

| Filament | All 30 plates, including fit tests and purge/towers |
| --- | ---: |
| White | 2884.38 g |
| Wood tan | 206.03 g |
| Copper silk | 444.00 g |

Production plates 1-29 total **3329.69 g and 120 h 31 min**.
Plate 30 adds **204.72 g and 8 h 24 min**.
Combined: **3534.41 g and 128 h 55 min**.
These are slicer estimates; small rounding differences from the GUI total are
normal. The planned stock of 3.5 kg white, 1 kg wood, and 1 kg copper covers this
slice, leaving approximately 0.616 kg white,
0.794 kg wood, and
0.556 kg copper for calibration and retries.

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
82 reinforcement modifiers (73 production and nine test), 21 weave-color
modifiers, filament assignments, plate quantities, and saved G-code bounds. It accepts
Bambu's compact decimals such as `E.123` and `I-.5`, which the earlier scratch
checker missed. [final-review.json](final-review.json) contains the corrected
audit. Plate 30 was re-sliced after adding the weave sample; the saved production
G-code on plates 1-29 is byte-identical to the previous AMS version.

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

To apply the AMS palette to a saved **single-filament** complete 30-plate project:

```powershell
python scripts/colorize_print_project.py --source path/to/single-color-complete.3mf --output .work/ams-colors/colored.3mf
```

Open the staged project in Bambu Studio and use **Slice all**. From that same
unchanged project, use **Save Project As** for editable models and **Export all
sliced file** for the G-code export. Combine and audit them before publishing:

```powershell
python scripts/combine_ams_slices.py --models .work/ams-colors/models.3mf --slices .work/ams-colors/models.gcode.3mf --output .work/ams-colors/complete.3mf
python scripts/validate_print_project.py --project .work/ams-colors/complete.3mf --baseline .work/ams-colors/complete.json --report .work/ams-colors/audit.json
```

The colorizer deliberately rejects an already-colored source. A full rebuild
must start from the single-filament project generation steps above. The saved
production 3MF already contains the palette, editable modifiers, and toolpaths.

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

To add the full-width weave coupon after the AMS project is ready, run
`python scripts/add_weave_test_coupon.py` against the nine-coupon version.
Open `.work/weave-coupon/with-weave.3mf`, select plate 30, use **Slice plate**,
and **Export plate sliced file**. Save an editable copy with **Save Project As**
to refresh the plate thumbnails. Combine the single-plate export while
preserving production toolpaths, then audit before publishing:

```powershell
python scripts/add_weave_test_coupon.py --slices .work/weave-coupon/plate30.gcode.3mf --previews .work/weave-coupon/previews.3mf
python scripts/validate_print_project.py --project .work/weave-coupon/complete-with-weave.3mf --baseline .work/weave-coupon/complete-with-weave.json --report .work/weave-coupon/audit.json
```
