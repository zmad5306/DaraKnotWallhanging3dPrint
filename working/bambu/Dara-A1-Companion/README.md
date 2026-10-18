# A1 companion for the current A2L artwork

Open **[Dara-A1-Companion.3mf](Dara-A1-Companion.3mf) as a project** in Bambu Studio. It contains five native A1 plates and 46 pieces taken from the current coordinated A2L design. C3/C4 here match the **four-core M**. The file embeds the actual Bambu Lab A1 0.4 mm machine and filament profiles, with 0.20 mm layers, 8% gyroid bodies, four walls, five top/bottom layers and the existing local solid screw reinforcement.

| A1 companion plate | Contents | Replaces full A2L project plate | Filament |
| --- | --- | --- | --- |
| 1 | Photo backers 1, 3, 5, 7 | 18 | White, slot 1 |
| 2 | Photo backers 2, 4, 6, 8 | 19 | White, slot 1 |
| 3 | Wall blocks B1–B4 and all 32 photo retainers | 20 | White, slot 1 |
| 4 | Flat M core C3 | 13 | Copper silk, slot 3 |
| 5 | Flat M core C4 | 14 | Copper silk, slot 3 |

**Print each piece once.** If using this companion, skip plates **13, 14, 18, 19 and 20** in the complete A2L project. Print A2L plates **1–12 and 15–17** for the remaining knot, cores C1/C2 and all three veneers. The full A2L project remains complete for anyone choosing to print everything there.

The backers stay flat, without supports or brims. Wall blocks retain their matching key patterns and local reinforcement; native trees support their hidden features. Retainers print flat without supports or brims. C3/C4 print fully flat with 1 mm brims and no supports. C3 has a small XY rotation adjustment to provide more A1 bed margin; C4 retains its A2L XY rotation. Their actual model and modifier meshes are unchanged. All veneer geometry and finish orientation remain in the A2L project.

Each plate uses one filament, so the prime tower is disabled. Keep slots 1 and 3 consistent with the full project; unused tan/blue slots are retained for familiar material mapping. The white plates are grouped first so the three accessory plates can print before switching to copper cores.

Native validation checks the actual 256 × 256 × 256 mm A1 bounds, complete G-code, correct filament slots, support policy, 8% body settings, local 100% modifiers, exact matching geometry from the A2L source and native geometry/pose preservation. The native machine startup/change/end commands are verified against the installed A1 profile. Physical screw fit and assembly still need confirmation in the chosen filaments.

`Dara-A1-Companion-Editable.3mf` is the source without saved slices. Use the complete companion for printing. Rebuild with `scripts/build_a1_companion.py`; audit the distributed file using `python scripts/audit_a1_companion.py`. Pull the branch and run `git lfs pull` on the PC before opening it.

## Native print estimates

| A1 plate | Time | Filament |
| --- | ---: | ---: |
| 1, four backers | 2 h 19 min | 99.4 g |
| 2, four backers | 2 h 19 min | 99.4 g |
| 3, blocks and retainers | 5 h 00 min | 144.9 g |
| 4, core C3 | 2 h 29 min | 63.1 g |
| 5, core C4 | 2 h 03 min | 51.3 g |
| **Total** | **about 14 h 10 min** | **458.1 g** |

Estimates include support and brim. The smallest checked bead-inclusive A1 edge margin is 1.5 mm on the backer plates; C3 has 2.81 mm after its brim. Keep the saved layouts.
