# Dara A2L completion plan

Updated October 18, 2026. Branch `codex/m-veneer-cosmetic-fit`.

The A2L is now the chosen printer. The user approved replacing existing full-size prints for the cleanest result, the fresh 14-joint knot, four flat M cores and three veneers, the standard 0.4 mm nozzle, 0.20 mm layers and **8% gyroid structural infill**. Veneers and their bonded carriers remain solid. The earlier 15% full-size target is superseded.

The production project is [Dara.3mf](../Dara.3mf), with its [A2L guide and validation](../working/bambu/Dara-Photo-Frame-A2L/README.md). The alternate [A1 project](../working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf) has the same carrier correction on all six veneers. All A1 sample projects remain separate and unchanged by this production update.

## Chosen layout

| Item | Prior A1 | A2L |
| --- | ---: | ---: |
| Knot sections | 20 | 10 |
| Knot joints | 32 | 14 |
| M flat cores / hidden joints | 6 / 5 | 4 / 3 |
| M veneers / visible seams | 6 / 5 | 3 / 2 |
| M visible seam length, front projection | 316.9 mm | 24.3 mm |

Six A2L knot joints are completely behind the band-free M with at least the intended 2 mm front-view margin, two are partly covered and six fully exposed. Eight have some visible portion. These counts exclude M seams; oblique viewing angles can reveal more than a front projection.

The knot uses new partitions in the continuous stock rather than joined A1 pieces. Its 18 mm laps preserve hidden fitting clearance while all cosmetic walls butt at zero nominal gap. Hidden seating pads control flushness separately from glue relief, and secondary pockets permit small axial variation. Material boundaries and the global weave remain continuous across the new cuts.

The four M cores print flat, with all convex crown and hammer texture in flat-backed veneers. All three veneers use one complete shared rotation, including the same in-plane direction. The 55-degree face planes run along bed Y; turning all artwork 90 degrees together within that plane allows full sweeps using the A2L height. Never rotate an individual veneer to pack it. Knot fill directions compensate for each saved XY rotation.

The matching attachment layout moves conflicting screws/pilots away from the new laps, changes the locators to one round datum plus one axial slot per new core, and relocates all four wall-block centers. Use all matching A2L parts together. Exact coordinates and the tongue-first assembly order are in [production-plan.json](../working/bambu/Dara-Photo-Frame-A2L/production-plan.json).

## Split printing between A1 and A2L

The [A1 companion](../working/bambu/Dara-A1-Companion/README.md) contains three plates with 44 current-design accessories: eight backers, four wall blocks and 32 retainers. Print its full set once; skip plates **18–20** of the complete A2L file. The A2L prints **1–17**, including **every M core and veneer**. The accessory geometry is shared, with actual printer-specific profiles and native slices. All veneers retain the same A2L finish orientation.

## Physical confirmation still required

1. Print one demanding full knot pair. Dry-fit the zero-gap cosmetic wall, check all three visible colors in grazing light, assess 8% stiffness and verify pad seating under light clamping.
2. Print one full M core and veneer. Confirm that the silk stays restrained through the tall print, then assess the actual cupping and fin-removal access. Digital rear-area allocation and bracing checks do not measure material stiffness or bond strength.
3. Cut the narrow necks through their rear recesses and remove the separate grounded ribs and fins progressively while cradling the face. Sand the hidden flat back on the granite plate without rounding seam edges or removing seating features.
4. Dry-fit all four cores flat, then all three veneers. Check the two crown seams and consistent reflection before adhesive. Use the successful sample adhesive process, keep glue inside hidden relief and keep stops/closing lands clean.
5. Dry-assemble the knot in the documented tongue-first order. Verify the M pin/screw fit and rear access, photo/backer/retainer clearances and wall blocks.
6. Record the representative print results on the [printable guide/checklist](../output/pdf/Dara-A2L-Print-Guide.pdf), then print the remaining plates. Adjust only when a physical result justifies it; regenerate matching geometry and reslice affected plates after any rotation or fit change.

## Retained studies and tests

- [14-joint knot study and comparison previews](../working/review/a2l-hidden-joints/lean-candidate.json); [A1 vs A2L installed view](../working/review/a2l-hidden-joints/A1-vs-A2L-14-installed.png).
- [Four-core / three-veneer M study](../working/review/a2l-m-joints/README.md). Its proposed layout is now modeled in the production A2L project; the study remains a historical design record.
- [Unchanged A1 test project](../output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf) and [sample checklist](../output/pdf/Dara-Sample-Production-Checklist.pdf). Plate 1 fixtures remain valid. Sample body settings are 8% gyroid; the full A2L carriers differ because the panels are larger and have a different shared in-plane pose.
- [Original solid-M baseline](../reference/production/Dara-Solid-M-Baseline.3mf) and [previous A1 veneer release](../working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf).

For the PC, pull this branch, run `git lfs pull`, then `python scripts/audit_dara_release.py`. Open the 3MF **as a project** to retain the saved A2L profiles, per-object settings, material assignments, rotations and slices.
