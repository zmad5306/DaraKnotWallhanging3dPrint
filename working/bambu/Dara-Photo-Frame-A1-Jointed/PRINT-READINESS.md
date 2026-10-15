# Printing and assembly - complete hammered Dara - 2026-10-15

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf), identical to the root [Dara.3mf](../../../Dara.3mf). Open as a project in Bambu Studio. All 32 plates have saved slices. The copper has been realigned for Y bed motion, and all 32 plates have been re-sliced with gentle motion limits. The full-color knot joint practice pair remains on plate 32. No job has been sent to the printer.

**Current mirrored seam revision:** F1-F20 now form 32 seams, all 67.3-75.1 mm long, with repeated left/right and top/bottom placement. The 129/181 mm cuts are removed. The same 18 mm keyed-lap profile, key clearances, artwork and overall size are retained. The largest frame footprint is 252.124 x 252.073 mm, leaving at least 1.917 mm to a centered 256 mm bed before brim/support. The smallest verified frame toolpath edge clearance, including beads, brim and supports, is 0.832 mm. [Seam comparison](../../review/mirrored-joints/seam-comparison.png) · [Current release report](mirrored-joints-validation.json) · [Updated map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf).

Two M screw positions move 1.5 and 6 mm, one locator moves 1.5 mm, and five photo-tab screw positions move 5.0-16.8 mm along their openings. Matching rear holes and reinforcement zones are updated in the hammered M1/M3/M6. Its visible face and band seats are preserved. Use this revision's frame and revised M pieces together; the previous mounting positions do not all match.

**Continuous cover crowns:** Plate **31** contains five rebuilt covers and a fresh native slice. Each visible face follows one circular-section crown, swept linearly across its width. The underside and footprint are preserved within 0.0002 mm; M seats and the modeled adhesive allowance are unchanged. The new faces are fuller by up to 1.38 mm. All five meshes are watertight single solids, their bevel errors stay below 0.00101 mm, and support paths clear the broad visible faces. [Current release checks](cover-crown-validation.json).

**Surface-path check:** the repeated junction tracks across the broad faces are removed. Interior command junction counts change from **67/90/133/133/133** to **2/1/0/0/0** for Bands 1–5. The three remaining transitions are isolated near the ends of Bands 1 and 2; they are included in the [before/after comparison](../../review/continuous-covers/before-after-paths.png). This revision has not been physically printed.

Classic walls and arc fitting remain enabled at **0.05 mm** resolution. Plates 1-20, 21, 23 and 26 have fresh native slices. Plates 22, 24, 25 and 27-32 retain their previous saved slices, including the continuous covers. Saved copper orientations, support settings, motion limits and filament assignments are retained. Frame print rotations and purge-tower positions follow the new sections.

## Plate selection

- **1-20:** F1-F20 frame sections.
- **21-26:** M1-M6 hammered sections at 55 degrees, face planes along Y, regenerated tree supports.
- **27-28:** eight backers.
- **29:** four wall blocks and 32 retainers.
- **30:** optional white/wood/blue finish sample.
- **31:** five separate copper cover bands, Band1-Band5. The old copper coupon is removed.
- **32:** unchanged full-color lap-profile pair for an epoxy mock glue-up, supports and purge tower included. Its two unscaled halves, originally cropped from the previous F7/F4 layout, assemble to 74 x 68 x 13.5 mm. They retain the same current 18 mm keyed-lap profile; they are not crops of the new section boundaries. The tongue is on the left, socket on the right. Use them to practice epoxy application, masking, clamping and squeeze-out cleanup. [Joint layout](../../review/knot-glue-sample/joint-sample.png).

Filament slots: **1 white / 2 wood tan / 3 copper silk / 4 Azurite blue**. Map those to the actual spools. A1, 0.4 mm nozzle, textured PEI, 0.2 mm layers. Keep the saved scale, orientations and per-object settings. The copper profile is the tilted hammered setup, with 0.98 filament flow; the earlier flat coupon-C profile is superseded.

Physical band seating and full-size printing remain unverified. Tall M sections are a larger physical print than the successful joint coupon. The saved project includes orientations and support painting.

The broad copper face planes now run along the A1 bed's Y travel, with the 55-degree lean across X. Each part is rotated within that plane to fit at its original scale. M1 and M3 reach approximately 238 and 241 mm; the other four are 63-102 mm tall. Tree supports are regenerated with 3 mm branch diameter and two walls. A 6 mm outer object brim is requested; where the tilted part has no first-layer area, the generated tree base supplies the anchoring.

Project-wide X/Y limits are 1,000 mm/s² acceleration and 150 mm/s speed. Process travel and default print acceleration are 1,000 mm/s²; outer walls, top surfaces and the first layer use 500 mm/s². Major process speeds are capped at 150 mm/s. All 32 plates were re-sliced, including the frame and optional samples. These conservative settings increase print time; they do not prove physical adhesion or eliminate sway.

## Material and time

All 32 plates: **4,090.55 g / 261 h 34 min**. Assembly excluding optional plates 30 and 32: **4,030.86 g / 257 h 39 min**. Copper plates 21–26 and 31: **1,049.74 g / 94 h 15 min**. Cover plate 31: **18.52 g / 2 h 05 min**. Estimates include supports and purge. Optional plate 30 uses **18.42 g / 1 h 21 min**; plate 32 uses **41.27 g / 2 h 33 min**. Per-plate details are in [the release report](mirrored-joints-validation.json).

## Assembly supplies

| Purchased item | Quantity | Use |
| --- | --- | --- |
| Selected #6-19 x 1/2-inch pan-head plastic thread-forming screws | 50 | 32 tabs + 8 wall-block screws + 10 M screws |
| 10 mm OD x 4 mm ID x 1 mm washers | 10 | M screws only |
| Wall fasteners/anchors or strips appropriate to the wall and load | As required | Wall installation |
| Adhesive proven on the chosen PLA and lap sample | As required | Structural laps and copper cover bands |

Rear screw and locator dimensions are preserved; three M mounting locations are revised as described above. Different screws or washers change the modeled clearances.

## Assembly order

Label parts as they leave each plate. Remove support residue from the rear, lap and band underside without reshaping mating shoulders. Dry-fit on a flat surface first. Lower sockets onto previously placed tongues:

- **Frame:** F1, F2, F6, F8, F13, F15, F19, F20, F11, F12, F9, F16, F10, F18, F3, F14, F5, F7, F17, F4.
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

Band ends follow the artwork and are not interchangeable. Nominal band width is 12 mm, seated in a 13.2 mm recess with 0.15 mm modeled adhesive allowance. The rebuilt circular crowns have at least 1.2 mm nominal broad-face skin, approximately 0.955 mm at the bevel, and up to 2.514 mm thickness where needed to keep the crown continuous above the original seat. Actual dry-fit height depends on the adhesive layer. The [earlier assembled view](../../review/hammered-bands/assembled-bands.png) identifies the cover positions; it predates these fuller crowns.

After bonding and curing, seat the M on its locating pins and install ten screws/washers from the rear. The white wall blocks **B1/B2/B3/B4** fit **F3/F5/F16/F18** respectively; these are different pieces from copper Band1-Band5. Install the backers and four retainers per photo. Check that the four wall faces share a plane and photo hardware clears the wall before mounting.

## Verification scope

All 20 frame bodies are watertight single solids with no modeled interference between sections. All 10 screw sites and 12 locator sites align with the actual hammered M, and seated frame/M solids have no modeled collision after accounting for sub-0.00001 mm transform rounding. Original artwork and the keyed-lap tool are unchanged. Native round-trip geometry differs by at most 0.000011 mm; white, wood and blue layer ranges, copper support clearance, motion-limit commands and bed fit pass. The edge check covers all 56 canonical large arcs, with maximum saved perimeter radial error 0.0365 mm. The complete release opens and saves in Bambu Studio. All 32 G-code checksums and both distributed project hashes pass.

[Current release report](mirrored-joints-validation.json) records all plate hashes and seam/mount checks. The [earlier cover report](cover-crown-validation.json) remains the evidence for the unchanged crowns. The updated PDF map shows the current frame and hammered M; flat-M STL exports are historical. [Current frame edge audit](../../review/mirrored-joints/perimeter-review.json). Digital checks do not establish physical fit, cosmetic finish or wall-load capacity.

```powershell
python scripts/audit_dara_release.py
```
