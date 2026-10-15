# Printing and assembly - complete hammered Dara - 2026-10-15

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf), identical to the root [Dara.3mf](../../../Dara.3mf). Open as a project in Bambu Studio. All 32 plates have saved slices. The copper has been realigned for Y bed motion, and all 32 plates have been re-sliced with gentle motion limits. The full-color knot joint practice pair remains on plate 32. No job has been sent to the printer.

**Cover crown and bevel repairs applied:** Plate **31** contains all five repaired covers and a fresh native slice. A smooth show-face field replaces the nearest-edge crown crease; the mating undersides, footprint, glue allowance and M seats are preserved. Saved orientations and process settings remain in place. The other 31 slices are unchanged. Physical surface finish remains unverified. [Current release checks](cover-crown-validation.json).

## Plate selection

- **1-20:** F1-F20 frame sections.
- **21-26:** M1-M6 hammered sections at 55 degrees, face planes along Y, regenerated tree supports.
- **27-28:** eight backers.
- **29:** four wall blocks and 32 retainers.
- **30:** optional white/wood/blue finish sample.
- **31:** five separate copper cover bands, Band1-Band5. The old copper coupon is removed.
- **32:** optional full-color F7/F4 knot joint pair for an epoxy mock glue-up, supports and purge tower included. Its two unscaled F7/F4 halves assemble to 74 × 68 × 13.5 mm; the tongue is on the left, socket on the right. Use them to practice epoxy application, masking, clamping and squeeze-out cleanup. [Joint layout](../../review/knot-glue-sample/joint-sample.png).

Filament slots: **1 white / 2 wood tan / 3 copper silk / 4 Azurite blue**. Map those to the actual spools. A1, 0.4 mm nozzle, textured PEI, 0.2 mm layers. Keep the saved scale, orientations and per-object settings. The copper profile is the tilted hammered setup, with 0.98 filament flow; the earlier flat coupon-C profile is superseded.

Physical band seating and full-size printing remain unverified. Tall M sections are a larger physical print than the successful joint coupon. The saved project includes orientations and support painting.

The broad copper face planes now run along the A1 bed's Y travel, with the 55-degree lean across X. Each part is rotated within that plane to fit at its original scale. M1 and M3 reach approximately 238 and 241 mm; the other four are 63-102 mm tall. Tree supports are regenerated with 3 mm branch diameter and two walls. A 6 mm outer object brim is requested; where the tilted part has no first-layer area, the generated tree base supplies the anchoring.

Project-wide X/Y limits are 1,000 mm/s² acceleration and 150 mm/s speed. Process travel and default print acceleration are 1,000 mm/s²; outer walls, top surfaces and the first layer use 500 mm/s². Major process speeds are capped at 150 mm/s. All 32 plates were re-sliced, including the frame and optional samples. These conservative settings increase print time; they do not prove physical adhesion or eliminate sway.

## Material and time

All 32 plates: **4,101.62 g / 262 h 34 min**. Assembly excluding optional plates 30 and 32: **4,041.93 g / 258 h 39 min**. Copper plates 21–26 and 31: **1,048.29 g / 94 h 06 min**. Cover plate 31: **16.96 g / 1 h 57 min**. Estimates include supports and purge. Optional plate 30 uses **18.42 g / 1 h 21 min**; plate 32 uses **41.27 g / 2 h 33 min**. Per-plate details are in [the release report](cover-crown-validation.json).

## Assembly supplies

| Purchased item | Quantity | Use |
| --- | --- | --- |
| Selected #6-19 x 1/2-inch pan-head plastic thread-forming screws | 50 | 32 tabs + 8 wall-block screws + 10 M screws |
| 10 mm OD x 4 mm ID x 1 mm washers | 10 | M screws only |
| Wall fasteners/anchors or strips appropriate to the wall and load | As required | Wall installation |
| Adhesive proven on the chosen PLA and lap sample | As required | Structural laps and copper cover bands |

The original rear screw and locator geometry is preserved. Different screws or washers change the tested clearances.

## Assembly order

Label parts as they leave each plate. Remove support residue from the rear, lap and band underside without reshaping mating shoulders. Dry-fit on a flat surface first. Lower sockets onto previously placed tongues:

- **Frame:** F1, F2, F8, F15, F19, F20, F3, F14, F18, F11, F17, F9, F16, F12, F6, F7, F13, F10, F5, F4.
- **New M:** M2, M4, M6, M1, M3, M5. M1 lowers onto M2 and M4; M3 onto M2 and M6; M5 onto M2.

Do not mix the new M with old flat or earlier hammered sections: the cuts moved. Bond structural laps with the backs aligned, check the frame locators, then fit and bond the decorative bands into their seats. A band bridges the visible seam; it should not be used to force a misaligned joint flat.

Viewed from the front:

| Cover | Position | Joint |
| --- | --- | --- |
| Band1 | Upper right crown | M2/M3 |
| Band2 | Upper left crown | M2/M1 |
| Band3 | Lower left arm | M4/M1 |
| Band4 | Lower right arm | M6/M3 |
| Band5 | Center stem | M2/M5 |

Band ends follow the artwork and are not interchangeable. Nominal band width is 12 mm, thickness 1.2 mm before the bevel and less than 0.033 mm of crown smoothing, seated in a 13.2 mm recess with 0.15 mm modeled adhesive allowance. Actual dry-fit height depends on the adhesive layer. [Assembled geometry](../../review/hammered-bands/assembled-bands.png).

After bonding and curing, seat the M on its locating pins and install ten screws/washers from the rear. The white wall blocks **B1/B2/B3/B4** fit **F3/F5/F16/F18** respectively; these are different pieces from copper Band1-Band5. Install the backers and four retainers per photo. Check that the four wall faces share a plane and photo hardware clears the wall before mounting.

## Verification scope

The hammered meshes, placements, supports, copper assignment and local solid screw regions passed native round-trip and toolpath checks. All 22 rear M mounting regions match the original geometry. The new plate 32 pair is cropped at full scale from the production F7/F4 meshes and color modifiers; its bodies are watertight with zero modeled interference when assembled. Native slicing verifies all three colors and support/interface toolpaths. The Y correction preserves geometry and non-copper placements, repaints support eligibility for the rotated copper, and regenerates all 32 slices. Motion-limit commands, bed clearance and decorative-face support clearance are checked in the new report. All 32 G-code checksums and both distributed project hashes pass.

[Current release report](cover-crown-validation.json) records all plate hashes and the latest cover checks. Historical flat-M reports, STL exports and the PDF part map are superseded for M cuts and plate 31. The [frame edge audit](../../review/clean-edges/README.md) documents the retained frame geometry. Digital checks do not establish physical fit, cosmetic finish or wall-load capacity.

```powershell
python scripts/audit_dara_release.py
```
