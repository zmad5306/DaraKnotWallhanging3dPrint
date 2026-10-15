# Complete A1 print project - hammered M and copper bands

Open [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) **as a project** in Bambu Studio. It is identical to [Dara.3mf](../../../Dara.3mf) at the repository root. Both contain **75 assembly pieces and one optional sample on 31 plates**, with saved native slices. Updated 2026-10-15.

| Plates | Contents |
| --- | --- |
| 01-20 | F1-F20 frame sections, original white/wood/blue geometry and slices |
| 21-26 | M1-M6 full-size hammered sections, tilted 55 degrees, tree supports included |
| 27 | Backer1, Backer3, Backer5, Backer7 |
| 28 | Backer2, Backer4, Backer6, Backer8 |
| 29 | Wall blocks B1-B4 and 32 retainers |
| 30 | Optional white/wood/blue weave and edge sample |
| 31 | Five separate smooth copper covers, named Band1-Band5 |

Slot order remains **1 white / 2 wood tan / 3 copper silk / 4 Azurite blue**. Match the project slots to the loaded spools before printing. Keep the saved orientation, scale, object overrides and support painting. No print job was sent.

## Copper M

The original 599.88 x 358.74 mm outline and all 22 rear mounting features are retained. The new balanced cuts carry keyed laps and recessed seats for five separate smooth bands. These M sections replace the old flat M entirely; do not mix revisions. Band1-Band5 are decorative copper pieces, distinct from wall blocks B1-B4.

The 55-degree orientations, hammered texture, native tree supports and ten local solid screw regions come from the validated banded candidate. Copper slot 3 now uses **0.98 filament flow**, 220 C nozzle, 55 C textured bed and a 7.5 mm3/s volumetric limit. The M and bands have their own saved support, brim and shell overrides: four walls, 15% gyroid in the bodies, five top layers, three bottom layers and no ironing. Thin bands slice solid. This supersedes the earlier flat coupon-C settings.

The small tilted hammered joint was printed successfully. The newer cover-band seating and full-size parts have not yet been physically verified. The separate [small band test](../../../Dara-Hammered-Band-Test.3mf) remains available: 21.27 g and about 1 h 30 min. [Actual assembled geometry](../../review/hammered-bands/assembled-bands.png).

## Frame, backers and hardware

The other 24 plates retain their prior models, object settings, placements, native G-code and preview assets. The frame keeps its reconstructed tangent curves, wood relief and flush blue edging. Rabbets remain 2.4 mm deep for 1.6 mm backers. Frame/backer dimensions and mounting hardware are unchanged.

## Estimates and checks

All 31 plates, including the optional sample: **4,048.42 g and 162 h 56 min**. Assembly pieces without plate 30: **4,030.00 g and 161 h 56 min**. Copper plates 21-26 and 31: **1,036.36 g and 53 h 41 min**, including supports. These are Studio estimates; allow additional material for the test and retries.

[Current integration validation](hammered-integration-validation.json) records every plate's estimate and G-code hash. Native Studio import and slicing passed for all seven replacement plates. Geometry, support painting and ten screw modifiers match the source candidate. Copper uses filament 3 throughout the model and support toolpaths. All 31 saved G-code checksums pass, and the two distributed project copies match.

[Printing and assembly](PRINT-READINESS.md) contains the current order and band locations. The older `project-validation.json`, `final-review.json`, copper-finish reports and PDF part map describe the preceding flat-M project; their frame evidence remains relevant, but their M geometry, plate 31 and totals are superseded. The current M source is `scripts/prepare_hammered_bands.py`, not the old M STL exports.

## Recheck and regeneration

After `git lfs pull`, run:

```powershell
python scripts/integrate_hammered_dara.py audit
```

The integration script preserves an immutable baseline in `.work/integrated-hammered-dara`, imports the committed banded candidate, re-slices plates 21-26 and 31, verifies, then publishes both normal project paths. Its actions are `stage`, `slice`, `verify`, `publish` and `audit`. Staging expects the preceding flat-M Dara file (available in Git revision `d03621c`); it refuses to silently replace a different baseline. Native slicing requires the installed Bambu Studio CLI. Geometry dependencies are the same as the hammered generator.

Do not run the historical flat-copper tuning/publishing scripts against this release.
