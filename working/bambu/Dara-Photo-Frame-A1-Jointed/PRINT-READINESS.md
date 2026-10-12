# Final print review - 2026-10-12

**Digital review: passed. Ready to start fit-test printing. Full production
release remains conditional on the hardware checks below.** The user confirmed
that the current photo tabs, keyed wall blocks, and flat-back M hardware fits
have not been physically tested. No physical test was performed during this review.

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) for production:
Bambu Lab A1, 0.4 mm nozzle, Generic PLA, textured PEI plate, 0.2 mm layers,
four walls, 15% gyroid, and the saved local 100% modifiers. Keep the 100% scale,
orientations, plate assignments, and support/brim overrides. Plate 30 now contains
the nine fit-test pieces. Production plates 1-29 retain their original models,
settings and byte-identical G-code.

## Verified against the saved files

- Source CAD hash matches the export manifest; every STL hash matches its record.
- All 39 distinct STLs are single, watertight, consistently wound solids with
  positive volume, rest at Z=0, and fit the A1 model footprint allowance.
- All 70 assembled pieces were reconstructed from their native placement data.
  The largest intersection is 0.000160 mm3, within the 0.01 mm3 numerical tolerance.
  Frame/M laps, M locators, backers, closed tabs, and wall keys have no material
  interference at the saved dimensions. This is a nominal CAD fit check.
- All 48 normal meshes in the final 3MF match their source geometry within 0.0001 mm.
  All instance placements and 82 solid modifiers were checked; each modifier
  intersects its intended printable part.
- All 29 production plates contain the expected pieces and toolpaths: 20 frame
  sections, six M sections, eight backers, four blocks, and 32 tabs.
  Plate 30 adds nine test pieces: photo frame/backer/tab, B1 block/socket,
  the current M5/F14 interface pair, and the current F7/F4 lap pair.
- All saved non-custom extrusion moves were checked, including the 7,058,670
  production moves and the added test plate, including compact
  decimals, arc extrema, support, brim and bead widths. Minimum conservative
  bed clearance is **0.673 mm on F6 / plate 06**. The model paths stay on the bed.
  Printer purge, wipe and parking routines are intentionally outside this check.
- Estimated production use remains **3,254.07 g and 111 h 39 min 49 s**.
  These are slicer estimates including its supports/brims; test prints and retries
  require additional filament.
  The included plate 30 adds **160.18 g and 5 h 30 min**.
- The four-page part/plate map was rendered and visually reviewed. Its labels,
  quantities and front-view orientation agree with the project mapping.

The old bounds checker skipped numbers such as `E.123`, which excluded many
extrusions. That verification defect is fixed in the tracked
[validator](../../../scripts/validate_print_project.py), with five regression
tests. The corrected report is [final-review.json](final-review.json); the
original project's slice summary has also been refreshed. Previously reported
0.826 mm clearance should be replaced by 0.673 mm.

## First-print sequence

1. Print **plate 30 - PRINT FIRST - Hardware and lap fit tests** from the saved
   project. All [nine coupons](../../stl/Dara-Print-Checks/README.md) are already sliced.
   Test with the actual screws, photo/backer stack, and intended wall screw.
   Check key seating, tab rotation, screw grip, and removal of support from the
   keyhole channel. The M coupons retain the actual M5 pin spacing, relieved
   second hole, and screw stack; use the specified 1 mm washer. Do not force
   a fit or scale an individual mating part.
2. Print **F14 on plate 14 and M5 on plate 25**. Test their shared screw and
   both locating pins, with the specified 1 mm washer. M5 must sit flush on the
   rail without forcing the locators or bottoming the screw.
3. Check and bond the lap pair from plate 30 using the intended adhesive. It is
   cropped from the actual current F7/F4 joint and uses the **production four-wall /
   15% preset**, with no lap infill override. The previously successful reference
   used six walls and 30% infill; its strength result does not validate this
   lighter production preset.
4. After these checks pass, print the remaining production plates. Inspect the
   first layer especially closely on plate 06; the saved brim/support placement
   has little spare bed margin. A changed brim, support setting, filament profile,
   nozzle, or placement requires re-slicing and renewed bounds inspection.

Nominal bridge/support generation passes digital inspection, but support removal,
surface quality, printer dimensional error, screw grip, adhesive durability and
full assembled wall load still require physical checking. The provided B1 coupon
tests one wall-key pattern; check every final B1-B4 against its assigned frame
section before bonding the frame. No adhesive-strip weight rating is established.

## Assembly supplies and order

| Purchased item | Quantity | Use |
| --- | --- | --- |
| Selected #6-19 x 1/2-inch pan-head plastic thread-forming screws | 50 | 32 tabs + 8 wall-block screws + 10 M screws |
| 10 mm OD x 4 mm ID x 1 mm washers | 10 | M screws only |
| Wall fasteners/anchors or strips appropriate to the actual wall and load | Chosen for installation | Separate from the 50 assembly screws |
| Adhesive proven on the chosen PLA and lap sample | As required | Keyed laps require a bonded assembly |

The M screw stack provides 7.7 mm engagement, 1 mm nominal tip clearance, and
1.8 mm front cover. Photo and block screws provide 9.7 mm engagement, 1 mm tip
clearance, and 2.8 mm front cover. Different screw or washer dimensions change
these clearances.

Label parts as they leave the plate. All map positions use the front view.
Dry-fit first on a flat surface, then bond following the CAD's tongue-before-socket
order; lower each socket onto the earlier tongues:

- **Frame:** F1, F2, F8, F15, F19, F20, F3, F14, F18, F11, F17, F9, F16,
  F12, F6, F7, F13, F10, F5, F4.
- **M:** M1, M6, M2, M4, M3, M5.

After the bonded assemblies have cured, seat M on the locating pins and install
its ten screws/washers from the rear. B1/B2/B3/B4 fit F3/F5/F16/F18 respectively.
Install the backers and four tabs per photo. Verify all four wall faces seat in
one plane and the photo hardware clears the wall before mounting. A digital
pass does not establish a safe load rating for the completed hanging.

## Recheck

From the repository root, with numpy, trimesh and manifold3d available:

```powershell
python -m unittest discover -s scripts -p test_validate_print_project.py
python scripts/validate_print_project.py
```

This audits the existing saved artifacts and writes `final-review.json`; it does
not overwrite or re-slice the production 3MF. Re-export and re-slice deliberately
if physical testing requires changes to the design or process.
