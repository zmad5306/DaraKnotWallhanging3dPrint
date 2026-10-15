# Complete A1 print project - hammered M and copper bands

Open [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) **as a project** in Bambu Studio. It is identical to [Dara.3mf](../../../Dara.3mf) at the repository root. Both contain **75 assembly pieces and three optional test pieces on 32 plates**, with saved native slices. Updated 2026-10-15.

| Plates | Contents |
| --- | --- |
| 01-20 | F1-F20 frame sections, original white/wood/blue geometry, re-sliced with gentle motion |
| 21-26 | M1-M6 full-size hammered sections, 55 degrees, face planes along Y, regenerated trees |
| 27 | Backer1, Backer3, Backer5, Backer7 |
| 28 | Backer2, Backer4, Backer6, Backer8 |
| 29 | Wall blocks B1-B4 and 32 retainers |
| 30 | Optional white/wood/blue weave and edge sample |
| 31 | Five separate smooth copper covers, named Band1-Band5 |
| 32 | Full-color F7/F4 knot joint pair for epoxy assembly practice |

Slot order remains **1 white / 2 wood tan / 3 copper silk / 4 Azurite blue**. Match the project slots to the loaded spools before printing. Keep the saved orientation, scale, object overrides and support painting. No print job was sent.

## Copper M

The original 599.88 x 358.74 mm outline and all 22 rear mounting features are retained. The new balanced cuts carry keyed laps and recessed seats for five separate smooth bands. These M sections replace the old flat M entirely; do not mix revisions. Band1-Band5 are decorative copper pieces, distinct from wall blocks B1-B4.

The broad copper face planes now run along the A1 bed's Y travel, with the 55-degree lean across X. Each part is rotated within that plane to fit at its original scale. M1 and M3 reach approximately 238 and 241 mm; the other four are 63-102 mm tall. Tree supports are regenerated with 3 mm branch diameter and two walls. A 6 mm outer object brim is requested; where the tilted part has no first-layer area, the generated tree base supplies the anchoring. The hammered texture and ten local solid screw regions are retained. Copper slot 3 now uses **0.98 filament flow**, 220 C nozzle, 55 C textured bed and a 7.5 mm3/s volumetric limit. The M and bands have their own saved support, brim and shell overrides: four walls, 15% gyroid in the bodies, five top layers, three bottom layers and no ironing. Thin bands slice solid. This supersedes the earlier flat coupon-C settings.

The small tilted hammered joint was printed successfully. The newer cover-band seating and full-size parts have not yet been physically verified. The separate [small band test](../../../Dara-Hammered-Band-Test.3mf) remains available: 25.11 g and 3 h 01 min. [Actual assembled geometry](../../review/hammered-bands/assembled-bands.png).

## Frame, backers and hardware

The frame, backer, hardware and weave-sample plates retain their models, object settings and placements. Their slices and previews were regenerated for the project-wide motion limits. The frame keeps its reconstructed tangent curves, wood relief and flush blue edging. Rabbets remain 2.4 mm deep for 1.6 mm backers. Frame/backer dimensions and mounting hardware are unchanged.

Plate **32** adds two unscaled crops of the actual F7/F4 keyed lap, preserving its white/wood/blue surfaces and each parent's print orientation. The pair measures **74 x 68 x 13.5 mm assembled** and has room to trial epoxy squeeze-out, masking and clamps. Supports and a purge tower are sliced. [Sample layout and instructions](../../review/knot-glue-sample/README.md).

## Estimates and checks

All 32 plates: **4,101.64 g and 262 h 32 min**. Assembly without optional plates 30 and 32: **4,041.95 g and 258 h 36 min**. Copper plates 21-26 and 31: **1,048.31 g and 94 h 03 min**. Optional plate 30: **18.42 g and 1 h 21 min**; plate 32: **41.27 g and 2 h 33 min**. Estimates include supports and purge. Copper exceeds one 1 kg spool before retries.

Project-wide X/Y limits are 1,000 mm/s² acceleration and 150 mm/s speed. Process travel and default print acceleration are 1,000 mm/s²; outer walls, top surfaces and the first layer use 500 mm/s². Major process speeds are capped at 150 mm/s. All 32 plates were re-sliced, including the frame and optional samples. These conservative settings increase print time; they do not prove physical adhesion or eliminate sway.

[Current validation](y-stability-validation.json) records every plate estimate and G-code hash, native geometry round trips, support contacts, motion commands and unchanged instances. All 32 checksums pass and both normal project copies match. The [earlier knot report](knot-glue-sample-validation.json) records the source crop and full-color sample checks; the [earlier hammered report](hammered-integration-validation.json) records original mounting-region checks. Their hashes and estimates describe prior releases.

[Printing and assembly](PRINT-READINESS.md) contains the current order and band locations. The older `project-validation.json`, `final-review.json`, copper-finish reports and PDF part map describe the preceding flat-M project; their frame evidence remains relevant, but their M geometry, plate 31 and totals are superseded. The current M source is `scripts/prepare_hammered_bands.py`, not the old M STL exports.

## Recheck and regeneration

After `git lfs pull`, run:

```powershell
python scripts/integrate_hammered_dara.py audit
```

The integration script preserves an immutable baseline in `.work/integrated-hammered-dara`, imports the committed banded candidate, re-slices plates 21-26 and 31, verifies, then publishes both normal project paths. Its actions are `stage`, `slice`, `verify`, `publish` and `audit`. Staging expects the preceding flat-M Dara file (available in Git revision `d03621c`); it refuses to silently replace a different baseline. Native slicing requires the installed Bambu Studio CLI. Geometry dependencies are the same as the hammered generator.

`scripts/add_knot_glue_sample.py` adds plate 32 to the 31-plate release from commit `c109cbc`, with `stage`, `slice`, `verify`, and `publish` actions. It preserves all earlier plate resources and settings. The audit command above checks the latest published report.

Do not run the historical flat-copper tuning/publishing scripts against this release.

The Y correction is applied by `scripts/prepare_y_stable_dara.py` using `stage`, `slice`, `verify`, `render` and `publish`. It expects the files from commit `85d0690` and refuses to reinterpret later placements. The updated `scripts/prepare_hammered_bands.py` also uses the Y-aligned placement rule for future generation. [Details](../../review/y-stable-dara/README.md).
