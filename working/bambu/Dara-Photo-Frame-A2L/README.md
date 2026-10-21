# Dara A2L production project

**Joint correction, October 19:** all **42 raised lower-lap pads** are removed across the **14 knot joints**, following the user's physical result: trimming the three pads gave a good fit with flush white and brown faces. Only the raised **0.20 mm** stock is removed, leaving the surrounding lap at **Z4.8**. Plates **1–10** are resliced at the existing **8% gyroid** settings; mortises, keys, adhesive recesses, visible geometry and material assignments are retained. At that revision, plates **11–20** and every A1 companion file were preserved; the October 21 update below replaces only veneer plates **15–17**. See [geometry and pad toolpaths](joint-pad-removal-validation.json) and [protected-plate hashes](joint-pad-unchanged-plates.json). The sample was switched to the A1; this records that physical result without claiming a full-size A2L print has already passed.

Open **Dara-A2L-Complete.3mf as a project** in Bambu Studio. The repository-root `Dara.3mf` is an identical copy. `Dara-A2L-Editable.3mf` is the generating source without stored slices. Use the complete file for printing. Both use the actual installed **Bambu Lab A2L 0.4 nozzle** machine/process/material profiles, including A2L startup and shutdown commands; 330 × 320 × 325 mm build volume.

**Veneer support update, October 21:** plates **15–17** now use the approved **r6 wall cradle with end ties**, with the old base framework removed and two thin bed ties at the open ends of each plate. The three fresh native slices total **902.59 g** including all veneers and supports (**331.91 / 317.20 / 253.49 g**, about **60 h 1 min** combined). Plates **1–14 and 18–20**, all M cores, knot joints and A1 files are preserved. See [promotion checks](veneer-wall-promotion-validation.json), [unchanged-plate hashes](veneer-wall-unchanged-plates.json) and [end-tie bed view](veneer-end-tie-bed-preview.png). The user approved this file promotion; full-height rigidity, adhesion, silk warping and cleanup have not been physically qualified.

The artwork remains 914.4 mm across. Fresh cuts in the continuous artwork produce ten knot sections with fourteen joints: six fully hidden behind the band-free M, two partly covered and six fully exposed. Counts exclude the M. The M has five flat cores with four hidden keyed joints and three veneers with two short visible crown seams, 24.3 mm total in front projection. The structural backing stays continuous behind both veneer seams; its nearest joint is 116.9 mm away. Core joints remain in the broad fork, stem and lower sweeps. C4/C5 share core plate 14.

| Plates | Contents | Construction |
| --- | --- | --- |
| 1–10 | F1–F10 knot | 8% gyroid, 4 walls, 5 top/bottom layers; local solid screw zones |
| 11–14 | C1–C5 flat M cores | 8% gyroid; 8.4 mm flat main body, planar mushroom keys |
| 15–17 | V1–V3 copper silk veneers and bonded wall carriers | 100% infill; all convex crown and hammer texture in veneer |
| 18 | Backers 1, 3, 5, 7 | Flat, no brim/support |
| 19 | Backers 2, 4, 6, 8 | Flat, no brim/support |
| 20 | Four wall blocks and 32 photo retainers | Matching coordinated rear hardware |

62 assembly pieces on 20 plates. Filament slots: **1 white, 2 wood tan, 3 copper silk, 4 blue**. All plates use 0.20 mm layers. Supports, carriers and purge add consumable material beyond the assembled artwork.

## Optional A1 companion

Use [Dara-A1-Companion.3mf](../Dara-A1-Companion/Dara-A1-Companion.3mf) to print the eight backers, four wall blocks and 32 retainers on the A1. It uses the exact matching A2L-design accessory meshes and an actual A1 profile. Its [three-plate guide](../Dara-A1-Companion/README.md) maps the parts. Skip **18, 19, 20** in this complete A2L project when printing those on the A1; print **A2L plates 1–17**. All five M cores and all three veneers stay on the A2L.

## Fit and finish

Every knot cosmetic wall closes at zero nominal gap above Z8. Hidden 18 mm laps retain their keys, a 0.40 mm recessed adhesive region, secondary locator relief and squeeze-out reservoirs. The three raised seating pads have been removed; the former pad locations now finish at Z4.8. Clean supports and burrs, dry-fit the seam and check the white/wood faces against a flat reference before gluing. The real upper edge checks cover the white rail, weave and accent heights.

The M has flat front/back structural bodies and flat veneer backs, with a 0.20 mm planar glue space. Three seating pads establish each veneer's level, with a round datum and an axial relief pocket. The front retains the global hammered field and maximum local height 12.7 mm. No cover bands are needed. Keep adhesive off the seating pads and cosmetic edge lands.

All three veneers share **the entire same rotation**: a 55-degree lean, with all artwork turned 90 degrees together within that plane. Their show planes contain bed Y, and assembly Y rises in printer Z. This permits whole sweeps within the A2L's height. **Do not auto-orient or rotate individual veneers.** Knot top-fill directions are compensated for each saved XY rotation to match the assembled 135-degree direction.

Each veneer retains its original fused attachment necks and rear trim pockets. The carrier is a **1.20 mm continuous inclined wall**, a **1.00 mm rear wall** and **two 1.00 mm connecting walls**. The inclined wall reaches the bed across its width. Two **4 mm wide × 0.60 mm thick bands**, one at each open end, tie the front and rear walls at the bed in three layers to keep the ends from splaying. Their outer edges are flush with the wall ends. The misplaced r5 bands beneath the interior connecting walls have been removed; the connecting walls themselves remain intact. No old perimeter guard, curved local rail, crossbar lattice, broad center strip, starter feet or isolated tall starter posts remain.

The rear and connecting walls have 35 pointed lightening openings across the three plates: 28 × 48 mm, with 60-degree roof slopes, 12 mm minimum edge borders and 16 mm grid lands. The inclined backing behind the veneer remains solid. Native tree supports remain enabled; the original fused necks provide the modeled connection from the veneer to the bed-attached walls. Cutter access openings were not requested and are not a claimed feature of this revision.

Support the hammered face while removing sacrificial stock progressively. Preserve the original neck locations, rear lands, locator pockets, seam edges and front texture. No carrier material belongs in the finished assembly. The new wall carrier's physical removal method and resulting finish have not been qualified; the old fin-carrier cutter-access results do not apply to the new walls. Dry-fit all five cores and all three veneers before adhesive.

## Mounting and assembly

Use this release's knot and M together: attachment sites have been coordinated with the new lap and core-key locations. The ten M screws and eight frame pins retain their positions. Round datum and relieved bore roles are assigned within each new core; keyed joints and the continuous veneer also locate the two small lower cores. Each moved wall block retains its matching key pattern, but its center on the artwork has moved. Photo pilots are kept out of lap regions. Backers and universal retainers retain their existing geometry.

Knot tongue-first glue order: **F9 → F8 → F10 → F7 → F2 → F5 → F4 → F3 → F1 → F6**. Lower sockets onto earlier tongues; dry-fit the whole sequence before glue. Bond the core keys on a flat reference, fit the veneers, then mount the assembled M on its pins and rear screws. Check screwdriver access and photo hardware before final bonding. Use the previously tested adhesive process and light clamping with soft cauls and release film.

## Prime tower and warm-up notices

The towers use the A2L's forced **Y160** line and saved legal X positions. The preceding pad-free project was opened fresh in Studio without collision or floating-region banners. Its ten tower-bearing knot plates are byte-preserved in this wall-carrier update. The current full file passed a native reopen; the three new veneer slices report no collision or floating-region warnings. Fresh GUI inspection of this exact updated file remains pending. The native checks include bead-width-aware tower clearance, supports and brims on every newly sliced knot plate. Adjoining same-material model volumes let Studio check actual empty knot openings while preserving each section as one physical piece. Keep the saved placements. See the [native validation](native-validation.json) and [clearance correction](../../../docs/A2L-PRIME-TOWER-CLEARANCE.md).

The A2L thermal-preconditioning notice explains its warm-up duration and bed-zone guides. It is informational; its preference and the feature remain enabled as before.

## Validation and printing

The saved `Dara-A2L-Editable.3mf` is the authoritative geometry source. This support-only promotion used `scripts/promote_veneer_wall_cradle.py`, `scripts/validate_veneer_wall_promotion.py` and `scripts/install_veneer_wall_cradle.py`. Legacy fin regeneration is blocked so it cannot silently restore the removed structure. `production-plan.json` records all new cuts, mounting coordinates and visibility. Geometry, native round-trip, bead bounds, fin-bond toolpaths, material assignments, surface direction and reopen evidence are in the validation JSON files here. Run `python scripts/audit_dara_release.py` after pulling Git LFS files on another computer.

Check the first full-size corrected A2L joint for closure, flushness and 8% body stiffness before repeating the remaining knot plates. The pad-removal correction follows the user's successful manually trimmed sample; older A1 joint variants are historical and do not define this production joint. The M and veneer checks remain separate: confirm carrier cleanup, finish direction and silk restraint. Digital validation does not establish physical adhesion or a wall-mount load rating.

The printable guide's part maps remain applicable; its printed SHA, estimates and fin-carrier description predate the current corrections. Use this project's saved slices and this guide's wall-carrier description for the current file.

See [printable maps and production checklist](../../../output/pdf/Dara-A2L-Print-Guide.pdf). Keep the archived [A1 complete project](../Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf) separate: its section IDs and mounts do not interchange with this A2L build.
