# Separate weave/blue-edge and copper tests

Open the [complete Bambu project](../../bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf). The previously printed hardware/lap coupons have been removed from the plate layout. Their standalone STL files are retained here.

| Plate | Piece | Materials and settings | Estimate |
| --- | --- | --- | --- |
| 30 | Test-Weave-Full-Width | White/wood/Azurite blue Generic PLA; 65 C bed | 18.42 g; 0 h 59 min |
| 31 | Test-M-Letter | SUNLU Silk 2.0 Copper Red trial; 55 C bed | 24.81 g; 1 h 29 min |

Both use the A1, 0.4 mm nozzle, 0.2 mm layers, four walls, and 15% gyroid. Copper retains its local solid screw zone and prints with zero filament changes on its own plate.

The **2026-10-14 copper finish trial** uses 30 mm/s top surfaces, 50 mm/s internal solid infill, 40 mm/s outer walls, eight top layers with 1.6 mm minimum top thickness, and a trial flow ratio of 0.96. Copper-only filament overrides select 0.6 mm Normal Lift and disable sideways wiping before retraction. Nozzle/bed temperatures remain 220/55 C; the top pattern remains Monotonic line with ironing off. These changes are also applied to M1-M6, with new slices on plates 21-26 and 31. All other plate toolpaths and all geometry are unchanged.

Reopen the current 3MF before printing plate 31. Inspect the top for trenches, raised ridges, gaps between lines, and any additional stringing from disabling wipe. Flow 0.96 is a trial, not a measured spool calibration; the user reports that the test is looking good while printing, with completed-print inspection pending. [Saved settings and toolpath checks](../../bambu/Dara-Photo-Frame-A1-Jointed/silk-finish-trial.json).

The weave coupon is **68.36 x 24.00 x 13.50 mm**, cropped from the clean reconstructed F7 mesh. Both white side rails remain intact; only the short ends are cut. The recessed backing and raised threads include the alternating **3.3 x 1.5 x 0.3 mm crossing pads**. Wood is assigned at Z=8.4-9.9 mm, layers 43-50, with eight wood/white color changes. A **1.5 mm blue line**, inset **1.25 mm** from the weave, finishes flush on each rail. Blue uses slot 4 and occupies layers 66-68 (three more changes, **11 total**). Inspect the actual texture, blue opacity and clean white boundaries in Preview's Filament view and on the printed sample.

![Short weave test on plate 30](../../bambu/Dara-Photo-Frame-A1-Jointed/fit-test-plate.png)

![Copper test on plate 31](../../bambu/Dara-Photo-Frame-A1-Jointed/copper-test-plate.png)

The model thumbnails use the base color for filament modifiers; sliced Filament Preview shows the final wood and blue assignments. [Plate 30 manifest](plate-30-manifest.json) and [plate 31 manifest](plate-31-manifest.json) record source hashes, placements, and audited slice results. The standalone [weave STL](Test-Weave-Full-Width.stl) has no color settings; use the complete 3MF for the three-color test.

## Previously printed fit coupons

The photo, B1 wall-block/socket, M interface pair, and F7/F4 lap pair remain as standalone STL files for reference. The user reports insufficient photo room with the former 2.0 mm recess, possibly due to support roughness. [Test-Photo-Frame.stl](Test-Photo-Frame.stl) and [Photo-Fit-Sample.stl](Photo-Fit-Sample.stl) now use a **2.4 mm rabbet**, leaving 0.8 mm beyond the existing 1.6 mm backer. The backer and tab samples retain their dimensions. The revised physical fit is unverified. Other archived coupons retain their earlier geometry; the [manifest](manifest.json) records per-file source hashes. These fit coupons are not added to the current 31-plate layout.

Test-M-Letter on plate 31 remains the original crop of M5, including its screw stack and locating holes. For any repeated fit check, use its retained Test-M-Frame mate, a selected #6-19 x 1/2-inch plastic thread-forming screw, and a 10 mm OD x 4 mm ID x 1 mm washer. The outside cropped edges are sample boundaries, not mating features.
