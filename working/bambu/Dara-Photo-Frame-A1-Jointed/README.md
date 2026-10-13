# Complete A1 print project

[Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) contains 70 production pieces on plates 1-29 and two separate material tests on plates 30-31: **72 pieces on 31 plates**. The previously printed hardware and lap coupons have been removed from the project; their STL files remain available.

The project includes editable models, local infill and color modifiers, thumbnails, and sliced toolpaths. Use Git LFS to retrieve it after cloning. If Bambu Studio asks to regenerate Preview when opening the editable file, use **Slice all** with its saved settings.

| Plates | Contents |
| --- | --- |
| 01-20 | F1-F20, one frame section per plate |
| 21-26 | M1-M6, one copper letter section per plate |
| 27 | Backer1, Backer3, Backer5, Backer7 |
| 28 | Backer2, Backer4, Backer6, Backer8 |
| 29 | B1-B4 and 32 retainers |
| 30 | One short white/wood/blue weave sample |
| 31 | One copper Test-M-Letter sample |

The [four-page part and plate map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf) still describes the unchanged production assignments. See the [test guide](../../stl/Dara-Print-Checks/README.md) for the two material tests.

## Curve repair

All 12 reviewed bends on F1, F2, F6, F8, F13, F15, and F19 have been smoothed in the native CAD. The five fabric-facing boundaries and their blue offsets were updated together. Maximum outline adjustment is **0.305 mm**. The other 32 production STLs, joints, hardware interfaces, photo clearance, plate placements, and slicing settings are preserved.

All 31 plates were re-sliced. The [final repair review](../../review/curve-repair/README.md) includes before/after curves, actual saved toolpath close-ups at all 12 locations, and passing geometry and color-path audits. Bambu's white diamond symbols are seam markers; they do not specify white extrusion in the blue stripe. Plate 30 remains the physical finish and purge check.

## Flush blue ribbon edging

The white rails carry a **1.5 mm-wide Azurite blue thread**, with a **1.25 mm white gap** from the wood-facing edge. The blue ends level with the white face: its modifier occupies **Z=12.9-13.5 mm**. The color modifier assigns filament within the solid. Its path follows the repaired outline described above.

The path is generated on the continuous assembled artwork before clipping into F1-F20, so it does not outline manufacturing seams. See the [actual CAD color map](../../review/blue-ribbon-edge/assembly-color-map.png) and [design record](../../review/blue-ribbon-edge/design.json). Plate 30 includes the same line on both white rails for a finish/purge check.

Blue prints on **layers 66-68**, at nozzle heights **13.2, 13.4 and 13.6 mm**, after the wood layers have finished. That adds three changes; sections with taller white M locating pins add a fourth return to white. Total changes are **11 per ordinary frame/test plate**, or **12 on F4, F7, F9, F10, F12, F14, F16 and F18**. No layer mixes wood and blue.

Slot 4 is [SUNLU PLA Metal Azurite](https://www.amazon.com/dp/B0H3SFMXKW), represented by `#295D8A`, using a Generic PLA starting profile with 7.5 mm3/s maximum flow. The saved blue-to-white flush is 650 mm3, with flushing into the model disabled. Print plate 30 to check the actual metallic finish, opacity and white cleanliness before the frame plates; these settings have not been physically verified.

## Photo rabbet clearance

All photo rabbets are now **2.4 mm deep**, increased from 2.0 mm after the printed backer left insufficient room for the photo. The backer remains **1.6 mm** thick, leaving **0.8 mm total for the photo and surface clearance**: the original 0.4 mm photo allowance plus 0.4 mm to accommodate supported-surface roughness.

The native CAD, preview cache, F1-F20 STLs, and sliced project use the deeper recess. [Geometry verification](../../review/rabbet-clearance/geometry-verification.json) checks every frame section and confirms that the revision only removes material in the 2.0-2.4 mm rabbet depth band. The restored weave, joints, screws, tabs, and other parts retain their geometry. The [optional photo-frame coupon](../../stl/Dara-Print-Checks/Test-Photo-Frame.stl) is updated separately; plates 30 and 31 retain only their material tests. The new physical fit has not yet been checked.

## Restored weave

F1-F20 and the short F7 sample now include the older alternating crossing detail: **3.3 x 1.5 mm crossing pads raised 0.3 mm above the 0.6 mm thread grid**, on a 6 mm pitch. Adjacent crossings alternate direction. The native CAD, embedded preview meshes, STL exports, and sliced project agree. Frame joints, hardware interfaces, and production plate placements retain their dimensions. The rear photo rabbet has the additional clearance described above.

Wood modifiers follow the recessed backing, threads, and raised crossings at Z=8.4-9.9 mm. They no longer fill the relief with a flat prism in model view. Wood prints in place on layers **43-50**, with **eight wood/white filament changes**, followed later by the blue changes described above. Keep these modifiers when editing; plain STL files do not retain color assignments.

[Geometry comparison](../../review/weave-restoration/texture-comparison.png) and [geometry verification](../../review/weave-restoration/geometry-verification.json) document the restoration. Those reports describe the preceding weave-only revision; the separate rabbet report above records this subsequent clearance change.

## Saved print settings

- Bambu Lab A1, 0.4 mm nozzle, textured PEI plate, 0.2 mm layers, four walls, 15% gyroid.
- Filament 1: white `#FFFFFF`, Generic PLA; filament 2: wood tan `#C2AB84`, ordinary Generic PLA; filament 3: copper `#B87333`, Generic PLA Silk; filament 4: Azurite blue `#295D8A`, Generic PLA.
- Match those colors to the actual AMS Lite spools in the print dialog.
- Nozzle 220 C. White/wood/blue plates use a 65 C bed; copper plates, including plate 31, use 55 C throughout printing.
- Copper outer walls and top surfaces run at 40 mm/s. Copper and blue maximum volumetric speed is 7.5 mm3/s; white/wood use 12 mm3/s.
- 74 local 100% infill modifiers: 73 production screw/keyhole zones and the copper test screw zone. Lap tongues and roots use the normal body settings.
- Original rear-down orientations and 100% scale are retained. Backers print four per plate, by layer, without supports or brim. Tight frame/M plates retain their 1 mm brim and zero extra support-base expansion.
- Prime towers remain clear of the pieces. Flushing into objects, infill, and supports is disabled.

All 31 plates finished slicing in Bambu Studio 02.08.02.61. The independent audit checked 7,347,762 extrusion moves including bead widths, brims, support, and towers. Minimum bed-edge clearance is **0.673 mm**. The only slicer notices concern unsupported traditional timelapse on the single-color plates; leave timelapse off for those plates.

| Material | All 31 plates, including support and purge/towers |
| --- | ---: |
| White | 2761.15 g |
| Wood tan | 222.40 g |
| Copper silk | 432.50 g |
| Azurite blue | 28.67 g |

Production plates 1-29: **3,403.00 g; 126 h 57 min**. Plate 30: **18.44 g; 0 h 59 min**. Plate 31: **23.28 g; 1 h 10 min**. Total: **3,444.72 g; 129 h 7 min**. These are slicer estimates.

[project-validation.json](project-validation.json) records the final hash, source hashes, quantities, plate positions, settings, and slice estimates. [final-review.json](final-review.json) independently verifies the geometry, 74 reinforcement modifiers, 21 wood and 21 blue modifiers, filament assignments, and saved toolpaths. All 41 normal meshes match their source STLs within 0.0001 mm. [PRINT-READINESS.md](PRINT-READINESS.md) retains the hardware and assembly guide.

## Rebuilding and checking

The [curve repair record](../../review/curve-repair/README.md#rebuilding-this-revision) documents the current native export, modifier refresh, all-plate slice, and publication sequence. It uses the preserved pre-repair four-color project under `.work/curve-repair/`. Earlier weave, rabbet, and blue-edge scripts describe their own historical revisions; running their publication steps alone does not recreate this repaired project.

To audit the published artifacts without changing the project:

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/validate_print_project.py
python scripts/review_curve_artifacts.py --output working/review/curve-repair/after --repaired-findings working/review/curve-artifacts/review.json
```
