# Dara knot wall hanging

**Current project: [Dara.3mf](Dara.3mf)** — open **as a project** in Bambu Studio. The full artwork is optimized for the **Bambu Lab A2L, 0.4 mm nozzle, 0.20 mm layers**, with **8% gyroid structural bodies**, four walls, five top/bottom layers, local solid screw reinforcement and solid veneers.

The fresh A2L layout has **10 knot sections / 14 knot joints**, including **six fully hidden behind the M**, two partly covered and six fully exposed. The M has **four flat cores and three flat-backed hammered veneers**, leaving just **two short visible M seams** totaling approximately 24 mm in front projection. All convex crown and hammer texture is in the veneers. Visible cosmetic edges have zero nominal gap, with fitting/glue clearance underneath; cover bands are omitted.

The complete project contains **20 natively sliced plates and 61 assembly pieces**. Every veneer uses the same complete rotation and has its face plane along bed Y. Bonded sacrificial fins, diagonal bracing and grounded starter shoes restrain the silk; trees supplement them. Keep all saved rotations and use the coordinated A2L knot, M and mounting hardware together.

- [A2L printing, cleanup and assembly guide](working/bambu/Dara-Photo-Frame-A2L/README.md)
- [Printable maps and production checklist](output/pdf/Dara-A2L-Print-Guide.pdf)
- [Completion plan and physical checks](docs/PROJECT-GAME-PLAN.md)
- [Native and geometry validation](working/bambu/Dara-Photo-Frame-A2L/release-validation.json)
- [Named complete A2L project](working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf) and [editable source project](working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf)

Filament slots: **1 white / 2 wood tan / 3 copper silk / 4 Azurite blue**. The artwork remains 36 inches / 914.4 mm across. Print a representative full knot joint and one full M core/veneer first to confirm 8% stiffness, actual seam closure, reflection and tall silk restraint before the remaining plates. Physical fit, adhesion and wall-mount load performance still need confirmation.

For another computer, pull branch `codex/m-veneer-cosmetic-fit`, run `git lfs pull`, then `python scripts/audit_dara_release.py`. The production 3MF contains the editable meshes, material assignments, native A2L machine commands and stored slices.

## Printing the matching small parts on the A1

The [A1 companion project](working/bambu/Dara-A1-Companion/Dara-A1-Companion.3mf) has **three plates / 44 matching pieces**: all eight backers, four wall blocks and 32 photo retainers. Use its [plate mapping and instructions](working/bambu/Dara-A1-Companion/README.md). With that file, skip **A2L plates 18–20** and print **A2L plates 1–17**. All four M cores and all three veneers stay on the A2L. The complete A2L file remains available as the all-on-one-printer option.

## Preserved A1 projects and tests

The [previous complete A1 veneer project](working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf) remains unchanged: 36 plates, six flat cores and six veneers. Its F/C/V identifiers and mounts differ from the A2L release. Use its [A1 guide](working/bambu/Dara-Photo-Frame-A1-Jointed/PRINT-READINESS.md) only with that file.

The [combined A1 sample project](output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf) and [printable sample checklist](output/pdf/Dara-Sample-Production-Checklist.pdf) also remain unchanged, including plate 1 fixtures. Those coupons establish local fit/adhesive behavior; the full A2L veneer carriers are regenerated for their larger panels and common in-plane orientation.

The [original solid-M baseline](reference/production/Dara-Solid-M-Baseline.3mf), [14-joint knot study](working/review/a2l-hidden-joints/lean-candidate.json) and [M layout study](working/review/a2l-m-joints/README.md) are retained as historical design sources.

![Dara knot wall hanging concept: white, wood tan, blue edge and copper M](output/renderings/Dara-Navy-Wall-White-Wood-Copper-Blue-Ribbon-Edge.png)

Concept rendering; actual print seams, texture, material finish and mounting follow the production project.
