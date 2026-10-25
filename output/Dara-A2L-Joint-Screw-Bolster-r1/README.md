# WITHDRAWN: wrong screw location

The user identified on October 25, 2026 that this sample includes an M mounting through-hole reinforcement, not the photo-retainer blind-hole bolster beneath the exposed face. It does not satisfy the requested surface test. Do not use r1 for that test. The replacement is **Dara-A2L-Joint-Photo-Retainer-Bolster-r2.3mf**, in the adjacent `Dara-A2L-Joint-Photo-Retainer-Bolster-r2` folder. The original 3MF is retained unchanged as a record. The digital checks below verified the wrong feature and do not establish suitability.

# Current joint + screw-bolster sample, r1

Print **Dara-A2L-Joint-Screw-Bolster-r1.3mf** as a **Bambu Studio project** on the **A2L / 0.4 mm nozzle / Textured PEI**. One plate contains both mating pieces. Estimate: **1h 44m / 39.80 g** including the saved supports and purge tower.

- **A / left:** production J2 F3 tongue, retaining both original locating keys.
- **B / right:** production J2 F1 socket, both matching grooves and one complete original screw bolster. An existing production alignment pin within the crop is also retained.
- The complete solid modifier ends at **Z12.4**, below the nominal **Z13.5** show face. All five native top layers at Z12.8–13.6 cross its boundary.

This is a direct crop of current root Knot.3mf, with **normal(auto) supports and infill-first OFF**. Structural **8% gyroid**, 0.20 mm initial/regular layers, four walls, five top/bottom layers, original 100% screw reinforcement, 0.20 mm support top gap and object interface spacing are preserved. Slots remain **1 white, 2 wood tan, 3 Azurite blue**, with their exact saved production profiles and values.

## Printing and checking

1. Open this exact 3MF as a project to retain the saved settings and A2L slices.
2. Remove normal supports, including the support/interface material from both grooves. Dry-fit A into B before gluing or sanding. Check both keys seat and the front surfaces meet flush.
3. Inspect the show face over the screw-bolster region for a visible circular boundary. Record fit, support cleanup and surface appearance against this r1 file.

Digital validation passes; **physical fit, cleanup and surface finish are not yet established**. No print job was sent.

## Source and exact crop

- Source: root `Knot.3mf`, SHA-256 `aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46`.
- Sample SHA-256: `8229ed33c45aae2a29ce10df0b178d7ef1ad225bcc8f1cd8c61d9ece846d7a15`.
- Source joint: J2, F3 tongue / F1 socket. Full-scale, unchanged joint geometry, two complete keys and one complete screw modifier.
- Joint-local crop: **X −18 to +44 mm, Y −32 to +48 mm**, Z −0.01 to 20 mm. Local X follows the source joint normal; origin/angle and the assembly polygon are recorded in `geometry-validation.json`.
- Nominal crop envelope: 62 × 80 mm. Both source rotations, all thicknesses and in-crop features remain. The existing alignment pin reaches Z16.5.
- Cropping and translation-only bed repositioning are the only geometry/pose operations. Sample name and single-plate tower arrays are the only global-setting differences. Tower X285 / Y160. No fit clearance, material boundary, support spacing, reinforcement height or surface finish was redesigned.

`geometry-validation.json` records exact per-volume intersections, source hashes, complete bolster retention, connected bodies and clean crop edges without split photo-opening scallops. `validation.json` records native roundtrip/reopen, full setting comparisons, both key clearances, groove backing with a 0.20 mm air gap, pad removal, five-layer screw skin, bed/tower clearance, warnings, checksums and estimates. All production projects and CAD/STLs remain byte-identical.

Bambu's sample G-code configuration footer reports independent support layer height as 1, while production's footer reports 0; both editable projects retain the same saved value of 1. A separate diagnostic slice using 0 produced **identical printer commands**, including all support moves. This footer difference does not change this sample's toolpaths. The diagnostic is retained only in scratch; the delivered project preserves production's saved setting.

This is the sole current joint/bolster test supplied for this request. Earlier production-joint, flush-joint and infill-first samples are historical and must not be substituted for this file.

## Three-pass re-audit, October 25, 2026

The exact delivered r1 archive above remains byte-identical. `three-pass-audit.json` records an additional audit requested after delivery:

1. **Geometry:** compare all seven embedded volumes with fresh intersections of the current production meshes; inspect the complete assembled joint, 30 key/groove width probes and vertical clearances. The complete screw modifier is retained. All 50 production modifiers also remain capped at Z12.4.
2. **Settings:** compare every global, object and volume setting. Only the documented sample name and tower arrays differ from production. Normal supports, infill-first off, 8% gyroid, material parameters and original rotations remain.
3. **Native slice and toolpaths:** reslice the exact delivered file, then separately audit both its stored slice and the fresh slice. Both pass ten key clearance checks, six local groove-support probes with a 0.20 mm air gap, five bolster-skin layers, color layers, bed/tower clearance and checksum checks. Neither slice reports a printability warning. The complete root-project audit also passes.

Minimum idealized commanded key clearance is **0.1281 mm** in both slices. This is a commanded-path measurement, not measured printed clearance. The bolster remains **1.10 mm below the nominal show face**. Its five top layers comprise the existing bridge layer followed by four solid layers. Commanded bead coverage around the bolster matches production: approximately 92.53% in the bridge layer and 99.87–99.98% in the four layers above it. The bridge spacing is present in production too; these percentages do not measure physical voids or guarantee the printed finish.

Fresh slicing is **not byte-identical** to the stored commands: differences include small coordinates/extrusion values and fill segmentation. Settings are identical; the maximum resaved mesh-coordinate difference is 0.0000002 mm. The fresh estimate changes by −0.69 seconds and −0.0103 g. Both slices independently pass the checks above. The fresh diagnostic stays in scratch and does not replace the supplied r1 file.
