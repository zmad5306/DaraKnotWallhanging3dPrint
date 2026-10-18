# Dara knot wall hanging

**Current project: [Dara.3mf](Dara.3mf)** — open **as a project** in Bambu Studio. The full artwork is optimized for the **Bambu Lab A2L, 0.4 mm nozzle, 0.20 mm layers**, with **8% gyroid structural bodies**, four walls, five top/bottom layers, local solid screw reinforcement and solid veneers.

The fresh A2L layout has **10 knot sections / 14 knot joints**, including **six fully hidden behind the M**, two partly covered and six fully exposed. The M has **four flat cores and three flat-backed hammered veneers**, leaving just **two short visible M seams** totaling approximately 24 mm in front projection. All convex crown and hammer texture is in the veneers. Visible cosmetic edges have zero nominal gap, with fitting/glue clearance underneath; cover bands are omitted.

The complete project contains **20 natively sliced plates and 61 assembly pieces**. Every veneer uses the same complete rotation and has its face plane along bed Y. Bonded sacrificial fins, diagonal bracing and grounded starter shoes restrain the silk; trees supplement them. Keep all saved rotations and use the coordinated A2L knot, M and mounting hardware together.

**Veneer hold, October 18:** the printed A1 coupons exposed an inaccessible starter-shoe weld and unwanted L-shaped lip. **Do not print A2L veneer plates 15–17 yet.** Their geometry is unchanged. First confirm clean removal using the revised A1 test below; the knot, flat cores and accessories are unaffected.

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

The [combined A1 sample project](output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf) contains the revised veneer carriers on **plate 2** and the revised knot joint on **plate 3**. The latest knot revision changes **plate 3 only**; plates **1 and 2 retain their exact saved geometry, placement, settings and G-code**. The [printable sample checklist](output/pdf/Dara-Sample-Production-Checklist.pdf) still applies to the same 11 pieces.

The new carriers replace the continuous shoe with **separate grounded starter ribs**, **1.2 mm cut necks**, **0.4 mm rear recesses** and **3 mm clearance behind the veneer**. There is no intended permanent perimeter flange. Use lined cauls to support the hammered face, cut the necks individually flush with the surrounding rear lands, and remove carrier stock progressively. Sand the back on the granite plate, preserving locator pockets and seam edges. Confirm the back lies flat and the seam closes without a lip before gluing. Keep the common saved veneer orientation.

See the [actual mesh preview](output/development/m-veneer-cosmetic-fit/M-veneer-fin-test.png), [geometry/cutter-access checks](output/development/m-veneer-cosmetic-fit/M-clean-trim-carrier-validation.json), and [carrier regression checks](output/development/m-veneer-cosmetic-fit/M-clean-trim-regression-validation.json). The [latest preservation report](output/development/m-veneer-cosmetic-fit/Zero-gap-plate-preservation.json) records the unchanged fixtures and copper test plate. Physical cutting, silk adhesion and finish still need this revised print. This revision has **not** been applied to the full-size A1 or A2L veneers.

**Knot test, plate 3:** the sides stay 68 mm wide through the lap and its transition into the coupon ends. The receiving lap has three bed-printed feet plus outer skirts, seating on upward-printed floors at assembly Z0.8. Supported underside stock has 0.8 mm clearance and cannot set the joint height; the skirts close the outside walls without a visible groove. The receiver's hidden back is recessed 0.8 mm. Preserve its saved Z placement and finish direction. White and wood roof levels have been put on exact layer boundaries; native toolpaths confirm matching assembled white/blue height of 13.6 mm and wood crests of 10.0 mm on both halves. The locating-key fit is retained.

Remove supports from the bulk underside, key roofs, foot sides and behind the skirts. Remove brim/burrs around the feet and skirts without sanding down their bed-printed bearing faces. Clean the tongue pocket floors, seat the feet and outer skirts, then check the seam in grazing light and with a straightedge. Dry-fit in the existing white-face jig before adhesive. See [actual mesh sections](output/development/m-veneer-cosmetic-fit/Ribbon-bed-datum-v1-sections.png) and [native height/datum checks](output/development/m-veneer-cosmetic-fit/Ribbon-bed-datum-native-validation.json). This is a revised local joint test; production knot geometry is unchanged pending physical confirmation, including evaluation of the hidden rear recess and joint strength.

The [original solid-M baseline](reference/production/Dara-Solid-M-Baseline.3mf), [14-joint knot study](working/review/a2l-hidden-joints/lean-candidate.json) and [M layout study](working/review/a2l-m-joints/README.md) are retained as historical design sources.

![Dara knot wall hanging concept: white, wood tan, blue edge and copper M](output/renderings/Dara-Navy-Wall-White-Wood-Copper-Blue-Ribbon-Edge.png)

Concept rendering; actual print seams, texture, material finish and mounting follow the production project.
