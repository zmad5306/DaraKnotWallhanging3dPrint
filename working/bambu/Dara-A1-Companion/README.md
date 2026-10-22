> **Historical record:** the 3MF files in this folder are retired from source control. Use Small Parts.3mf at the repository root. This document records the original revision; retrieve commit `5dab12a` and its LFS objects if the historical projects are needed.

# A1 companion for the current A2L artwork

Open **[Dara-A1-Companion.3mf](Dara-A1-Companion.3mf) as a project** in Bambu Studio. It contains three native A1 plates and 44 accessories taken from the coordinated A2L design. **Every M core and veneer stays on the A2L.** The companion embeds the actual Bambu Lab A1 0.4 mm machine and filament profiles, with 0.20 mm layers, 8% gyroid bodies, four walls, five top/bottom layers and existing local solid screw reinforcement.

| A1 companion plate | Contents | Replaces A2L plate | Filament |
|---|---|---|---|
| 1 | Backers 1, 3, 5, 7 | 18 | White, slot 1 |
| 2 | Backers 2, 4, 6, 8 | 19 | White, slot 1 |
| 3 | B1–B4 wall blocks + 32 photo retainers | 20 | White, slot 1 |

**Print each piece once.** With this companion, print **A2L plates 1–17**, and skip A2L **18–20**. The complete A2L project retains its accessories as an optional all-on-one-printer route.

Backers stay flat without supports or brims. Wall blocks retain their matching key patterns and local reinforcement; native trees support hidden features. Retainers print flat without supports or brims. No M pieces are in this project. All three plates are single filament, with the prime tower disabled.

| A1 plate | Native estimate | Filament |
|---|---|---|
| 1 | 2 h 19 min | 99.4 g |
| 2 | 2 h 19 min | 99.4 g |
| 3 | 5 h 00 min | 144.9 g |

Estimates include support and brim; about **9 h 38 min / 343.7 g** total. The smallest bead-inclusive A1 edge margin is 1.5 mm on the backer plates. Keep saved layouts. Physical fit and load checks remain pending.

`Dara-A1-Companion-Editable.3mf` is the source without saved slices. Use the complete companion for printing. Rebuild with `scripts/build_a1_companion.py`; audit using `python scripts/audit_a1_companion.py`. Pull the branch and run `git lfs pull` on the PC before opening it.
