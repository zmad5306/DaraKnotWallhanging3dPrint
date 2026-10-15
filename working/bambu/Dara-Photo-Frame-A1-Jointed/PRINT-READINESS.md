# Printing and assembly - complete hammered Dara - 2026-10-15

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf), identical to the root [Dara.3mf](../../../Dara.3mf). Open as a project in Bambu Studio. All 32 plates have saved slices. The latest addition is the full-color knot joint practice pair on plate 32; the preceding 31 plates are unchanged. No job has been sent to the printer.

## Plate selection

- **1-20:** F1-F20 frame sections.
- **21-26:** new M1-M6 hammered sections at 55 degrees, tree supports included.
- **27-28:** eight backers.
- **29:** four wall blocks and 32 retainers.
- **30:** optional white/wood/blue finish sample.
- **31:** five separate copper cover bands, Band1-Band5. The old copper coupon is removed.
- **32:** optional full-color F7/F4 knot joint pair for an epoxy mock glue-up, supports and purge tower included. [Layout and instructions](../../review/knot-glue-sample/README.md).

Filament slots: **1 white / 2 wood tan / 3 copper silk / 4 Azurite blue**. Map those to the actual spools. A1, 0.4 mm nozzle, textured PEI, 0.2 mm layers. Keep the saved scale, orientations and per-object settings. The copper profile is the tilted hammered setup, with 0.98 filament flow; the earlier flat coupon-C profile is superseded.

Physical band seating and full-size printing remain unverified. The separate [small band test](../../../Dara-Hammered-Band-Test.3mf) uses 21.27 g and about 1 h 30 min. Tall M sections are a larger physical print than the successful joint coupon. The normal project is prepared for printing without requiring manual rotations or support additions.

## Material and time

The assembly pieces require an estimated **4,030.00 g and 161 h 56 min**, including supports and purge. Optional plate 30 adds **18.42 g and 59 min**; optional plate 32 adds **41.27 g and 1 h 46 min**. Copper alone is **1,036.36 g and 53 h 41 min**. The M therefore exceeds a single 1 kg copper spool before tests or retries. Per-plate estimates are in [the current report](knot-glue-sample-validation.json).

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

Band ends follow the artwork and are not interchangeable. Nominal band width is 12 mm, thickness 1.2 mm, seated in a 13.2 mm recess with 0.15 mm modeled adhesive allowance. Actual dry-fit height depends on the adhesive layer. [Assembled geometry](../../review/hammered-bands/assembled-bands.png).

After bonding and curing, seat the M on its locating pins and install ten screws/washers from the rear. The white wall blocks **B1/B2/B3/B4** fit **F3/F5/F16/F18** respectively; these are different pieces from copper Band1-Band5. Install the backers and four retainers per photo. Check that the four wall faces share a plane and photo hardware clears the wall before mounting.

## Verification scope

The hammered meshes, placements, supports, copper assignment and local solid screw regions passed native round-trip and toolpath checks. All 22 rear M mounting regions match the original geometry. The new plate 32 pair is cropped at full scale from the production F7/F4 meshes and color modifiers; its bodies are watertight with zero modeled interference when assembled. Native slicing verifies all three colors and support/interface toolpaths. Adding plate 32 preserves the preceding 31 plates' resources, settings, placements and G-code. All 32 G-code checksums and both distributed project hashes pass.

[Current report](knot-glue-sample-validation.json), [prior hammered integration](hammered-integration-validation.json). The earlier flat-M reports and PDF map are historical for M cuts and plate 31 and do not show the new plate 32. The prior [frame edge audit](../../review/clean-edges/README.md) still applies to the preserved frame plates. Epoxy assembly behavior needs the physical sample; digital checks do not establish physical fit or a wall-load rating.

```powershell
python scripts/integrate_hammered_dara.py audit
```
