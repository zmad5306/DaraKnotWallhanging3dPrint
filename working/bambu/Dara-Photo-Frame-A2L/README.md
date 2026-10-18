# Dara A2L production project

Open **Dara-A2L-Complete.3mf as a project** in Bambu Studio. The repository-root `Dara.3mf` is an identical copy. `Dara-A2L-Editable.3mf` is the generating source without stored slices. Use the complete file for printing. Both use the actual installed **Bambu Lab A2L 0.4 nozzle** machine/process/material profiles, including A2L startup and shutdown commands; 330 × 320 × 325 mm build volume.

**Veneer plates 15–17 corrected:** all three saved production veneers now have separate grounded ribs and accessible cut necks. The continuous welded shoe that caused the L-shaped lip has been removed. Cutter windows, post-trim perimeter, supported-area coverage, tall-rib bracing, preserved front geometry and native bond extrusion are checked on every panel. Print a representative veneer first to confirm physical cleanup. See the [saved-project audit](../../../output/development/m-veneer-cosmetic-fit/All-veneer-production-audit.json).

The artwork remains 914.4 mm across. Fresh cuts in the continuous artwork produce ten knot sections with fourteen joints: six fully hidden behind the band-free M, two partly covered and six fully exposed. Counts exclude the M. The M has five flat cores with four hidden keyed joints and three veneers with two visible fork seams, 105.6 mm total in front projection, crossing the broad fork. The two outer sweeps and their narrow arch crowns are continuous veneers. C4/C5 share core plate 14.

| Plates | Contents | Construction |
| --- | --- | --- |
| 1–10 | F1–F10 knot | 8% gyroid, 4 walls, 5 top/bottom layers; local solid screw zones |
| 11–14 | C1–C5 flat M cores | 8% gyroid; 8.4 mm flat main body, planar mushroom keys |
| 15–17 | V1–V3 copper silk veneers and bonded fin carriers | 100% infill; all convex crown and hammer texture in veneer |
| 18 | Backers 1, 3, 5, 7 | Flat, no brim/support |
| 19 | Backers 2, 4, 6, 8 | Flat, no brim/support |
| 20 | Four wall blocks and 32 photo retainers | Matching coordinated rear hardware |

62 assembly pieces on 20 plates. Filament slots: **1 white, 2 wood tan, 3 copper silk, 4 blue**. All plates use 0.20 mm layers. Supports, carriers and purge add consumable material beyond the assembled artwork.

## Optional A1 companion

Use [Dara-A1-Companion.3mf](../Dara-A1-Companion/Dara-A1-Companion.3mf) to print the eight backers, four wall blocks and 32 retainers on the A1. It uses the exact matching A2L-design accessory meshes and an actual A1 profile. Its [three-plate guide](../Dara-A1-Companion/README.md) maps the parts. Skip **18, 19, 20** in this complete A2L project when printing those on the A1; print **A2L plates 1–17**. All five M cores and all three veneers stay on the A2L.

## Fit and finish

Every knot cosmetic wall closes at zero nominal gap above Z8; hidden 18 mm laps have three seating pads, a 0.40 mm recessed adhesive region, secondary locator relief and squeeze-out reservoirs. The real upper edge checks cover the white rail, weave and accent heights. Zero nominal gap still requires checking the physical printed fit.

The M has flat front/back structural bodies and flat veneer backs, with a 0.20 mm planar glue space. Three seating pads establish each veneer's level, with a round datum and an axial relief pocket. The front retains the global hammered field and maximum local height 12.7 mm. No cover bands are needed. Keep adhesive off the seating pads and cosmetic edge lands.

All three veneers share **the entire same rotation**: a 55-degree lean, with all artwork turned 90 degrees together within that plane. Their show planes contain bed Y, and assembly Y rises in printer Z. This permits whole sweeps within the A2L's height. **Do not auto-orient or rotate individual veneers.** Knot top-fill directions are compensated for each saved XY rotation to match the assembled 135-degree direction.

Each veneer has separate grounded starter ribs, sacrificial solid fins, 1.2 mm cut necks in 0.4 mm rear recesses, diagonal bracing, a connected bed frame and a perimeter guard. Native trees supplement these. Fin bodies leave 3 mm of rear cutting access. Allocation uses a 0.75 mm rear-area grid, maximum distance to actual bonds, area per bond and tributary width. There are **16 / 16 / 5 broad fins** on V1/V2/V3, plus the separate starter ribs; tall ribs are included in the bracing checks. Population reduction never overrides coverage. These are geometric screening criteria, not measured silk-PLA strength limits.

Remove ordinary trees, cradle the hammered face, and cut the 1.2 mm necks individually through their rear recesses. Remove fin stock, starter ribs, braces and the perimeter guard progressively. Cut flush with the surrounding rear lands, then sand the bonding back flat on the granite plate; preserve stops, pockets, seam edges and front texture. No carrier flange belongs in the finished piece. Dry-fit all five cores and all three veneers before adhesive.

## Mounting and assembly

Use this release's knot and M together: attachment sites have been coordinated with the new lap and core-key locations. The ten M screws and eight frame pins retain their positions. Round datum and relieved bore roles are assigned within each new core; keyed joints and the continuous veneer also locate the two small lower cores. Each moved wall block retains its matching key pattern, but its center on the artwork has moved. Photo pilots are kept out of lap regions. Backers and universal retainers retain their existing geometry.

Knot tongue-first glue order: **F9 → F8 → F10 → F7 → F2 → F5 → F4 → F3 → F1 → F6**. Lower sockets onto earlier tongues; dry-fit the whole sequence before glue. Bond the core keys on a flat reference, fit the veneers, then mount the assembled M on its pins and rear screws. Check screwdriver access and photo hardware before final bonding. Use the previously tested adhesive process and light clamping with soft cauls and release film.

## Prime tower and warm-up notices

The towers use the A2L's forced **Y160** line and saved legal X positions. Studio had been overriding the previous corner positions when loading the project. The prior corrected file was verified in Studio without the collision banner. This carrier update retains those exact tower-bearing models, settings and saved toolpaths; all native startup collision checks pass. A fresh visual check of this file is recorded as pending because the Mac was locked. Adjoining same-material model volumes let Studio check actual empty knot openings while preserving each section as one physical piece. The knot still has ten pieces and fourteen assembly joints. Actual tower-to-other-extrusion clearance is at least **11.96 mm**, including supports and brims. Keep the saved positions. See the [clearance correction](../../../docs/A2L-PRIME-TOWER-CLEARANCE.md).

The A2L thermal-preconditioning notice explains its warm-up duration and bed-zone guides. It is informational; its preference and the feature remain enabled as before.

## Validation and printing

The generating and verification scripts are `scripts/build_a2l_project.py` and `scripts/validate_a2l_project.py`. `production-plan.json` records all new cuts, mounting coordinates and visibility. Geometry, native round-trip, bead bounds, fin-bond toolpaths, material assignments, surface direction and reopen evidence are in the validation JSON files here. Run `python scripts/audit_dara_release.py` after pulling Git LFS files on another computer.

Print one demanding full joint pair and a flat core first. Confirm the revised carrier cleanup on the A1 sample or a representative full veneer before printing the remaining set. Check the 8% body's stiffness, actual zero-gap closure, finish direction and silk restraint. Digital validation does not establish physical adhesion or a wall-mount load rating. The A1 sample has the carrier trial on plate 2 and a revised ribbon joint on plate 3. The latest ribbon revision preserves plates 1 and 2 exactly; production knot joints retain their earlier seating design pending that trial.

See [printable maps and production checklist](../../../output/pdf/Dara-A2L-Print-Guide.pdf). Keep the archived [A1 complete project](../Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf) separate: its section IDs and mounts do not interchange with this A2L build.
