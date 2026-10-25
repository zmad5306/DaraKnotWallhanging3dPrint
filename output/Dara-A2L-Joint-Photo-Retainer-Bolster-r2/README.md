# Current photo-retainer bolster + joint test — r2

**Physical update, October 25:** the user reported **"Joints are ok"** and requested propagation, commit and push. This is recorded as user-reported joint-fit success following this current r2 sample; the actual printed hash/printer were not independently observed. Screw-bolster surface appearance was not confirmed. The exact matching production project is published with infill-first off and normal supports; see [the publication record](../../release/knot-joint-approval-r1/README.md). The original sample archive and digital validation evidence remain unchanged.

**Use `Dara-A2L-Joint-Photo-Retainer-Bolster-r2.3mf`.** A2L / 0.4 mm nozzle / Textured PEI. One plate with both mating pieces. Open as a Bambu Studio **project**. Estimate: **2h 01m / 47.04 g** including supports and purge tower.

**r1 is withdrawn because it selected an M mounting through-hole reinforcement.** Its previous digital checks did not establish that it contained the requested photo-retainer feature. This r2 replaces it for the user's test.

- **A / left:** current production J3, F2 tongue, both locating keys.
- **B / right:** current production J3, F3 socket, both grooves and the complete **photo-retainer screw bolster beneath the exposed face**.
- The retainer has a **3.175 mm blind hole from the back ending at Z10.7**, with uninterrupted material up to the **Z13.5 show face**. Its **14 mm diameter / 100% infill** reinforcement modifier ends at **Z12.4**, leaving the saved five top layers above it. This is not an M through hole.

The matching modifier center is assembly XY (-212.403702, 287.837097) mm, matched to production photo-anchor index 6 (zero-based flattened index). The native mesh and actual G-code are checked for the blind bore and covered face; the generic modifier name alone is not accepted as identification.

## Print and inspect

1. Use the saved A2L project and its original three slots: **1 white, 2 wood tan, 3 Azurite blue**.
2. Remove the normal supports from both joint grooves. Dry-fit both keys before gluing or sanding and check that the visible faces meet flush. Normal support material also fills the retainer blind hole; clear it from the back if testing the screw. Support removal remains physically unqualified.
3. Inspect the unbroken show face directly opposite the photo-retainer blind hole for the unwanted circular mark. `feature-guide.png` locates that region on the assembled sample.

**Infill-first is OFF; supports are normal(auto).** Structural 8% gyroid, 0.20 mm initial/regular layers, four walls, five top/bottom layers, 0.20 mm support top gap and interface spacing, material profiles, finish directions and original rotations remain. The screw modifier alone retains 100% infill. No production file is changed and no printer job is sent. Digital checks do not establish physical fit, cleanup or surface appearance.

## Exact source and changes

- Source: current `Knot.3mf`, SHA-256 `aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46`.
- Sample SHA-256: `c0e48a0b2f7c8bf8adcc696b9785d4ff49359dd9104536ca486a1ec50055154d`.
- Full-scale J3 crop: joint-local **X −14 to +66 mm, Y −38 to +38 mm**, Z −0.01 to 20 mm. Envelope 80 × 76 × 13.5 mm.
- Crop only; joint dimensions, both complete keys, blind screw hole, photo opening, material boundaries and complete reinforcement are unchanged. The edge reliefs are portions of the actual production photo openings, verified against the source, not new recesses. Both pieces remain connected.
- Translation-only placement, sample label and single-plate tower arrays are the only packaging differences. Tower X285 / Y160. No M mounting through-hole reinforcement is included.

`geometry-validation.json` records source comparisons and semantic photo-retainer identification. `photo-retainer-audit.json` separately checks that exact feature in the native mesh and toolpaths. `validation.json` records the settings, joint clearances, support backing, five top layers, native reopen, checksums, estimates and protected-file hashes.

Bambu's sample G-code footer retains independent support layer height 1 while production records its normalized value 0. The editable setting remains 1 in both projects. A diagnostic slice using 0 is required to produce identical printer commands before release; the delivered project preserves production's saved setting.
