# Dara knot wall hanging

Open the root 3MF files **as projects** in Bambu Studio to retain their saved printers, materials and settings. These are the only Bambu projects maintained in source control. Supporting A1 projects are separated where their settings differ.

| Project | Printer | Plates | Contents | CAD / STL |
| --- | --- | ---: | --- | --- |
| [Knot](Knot.3mf) | A2L | 10 | Full-size F1–F10, solid laps, normal supports, infill-first off | [CAD](Knot.scad) / [STL](<Knot STL/>) |
| [Letter](Letter.3mf) | A2L | 6 | Five M cores, three hammered veneers with r6 wall carriers | [CAD](Letter.scad) / [STL](<Letter STL/>) |
| [Small Parts](<Small Parts.3mf>) | A1 | 5 | Eight photo backers, four wall blocks, 32 retainers and six veneer glue aligners | [CAD](<Small Parts.scad>) / [STL](<Small Parts STL/>) |
| [Crate Clips PETG](<Small Parts - Crate Clips PETG.3mf>) | A1 | 1 | The locally saved 12-clip layout; upper gussets removed, supports off | [CAD](<Small Parts - Crate Clips PETG.scad>) / [STL](<Small Parts - Crate Clips PETG STL/>) |
| [Photo Cut Aligner](<Small Parts - Photo Cut Aligner.3mf>) | A1 | 1 | The locally saved single Backer 2 honeycomb guide; SUNLU transparent PLA | [CAD](<Small Parts - Photo Cut Aligner.scad>) / [STL](<Small Parts - Photo Cut Aligner STL/>) |
| [Sanding Block PLA](<Small Parts - Sanding Block PLA.3mf>) | A1 | 1 | All five r4 parts, confirmed thread setup and corrected clamp orientation | [CAD](<Small Parts - Sanding Block PLA.scad>) / [STL](<Small Parts - Sanding Block PLA STL/>) |
| [Crate Stencils](<Small Parts - Crate Stencils.3mf>) | A1 | 6 | Three THIS END UP tiles and three FRAGILE tiles | [CAD](<Small Parts - Crate Stencils.scad>) / [STL](<Small Parts - Crate Stencils STL/>) |

## Plate order and settings

The six PLA projects now use the user's **SUNLU PLA Basic** identities for former Generic PLA slots and **SUNLU PLA Metallic** for Azurite blue slot 4. Printing parameters remain unchanged: Knot keeps its 65 C Textured PEI bed, and blue in Knot and Small Parts keeps its 7.5 mm3/s flow limit as approved project overrides. Letter's ERYONE copper, other silk, transparent PLA and PETG are preserved. All 29 stored native toolpaths retain their print commands; profile metadata and checksums were updated. See the [SUNLU preset comparison and migration](release/sunlu-pla-r1/README.md).

The local [SUNLU preset defaults](release/sunlu-profile-defaults-r2/README.md) now include 65 C Textured PEI temperatures for A2L Basic/Metallic and a 7.5 mm3/s Metallic flow limit on both printers. The new [SUNLU PLA Silk Copper](release/sunlu-silk-copper-r1/README.md) presets copy the saved copper settings for A1 and A2L. These preset updates do not change saved projects or Letter's ERYONE assignment. Current preset JSON snapshots are provided in those release folders.

**Knot:** all 14 joints now have **100% rectilinear fill in both overlapping lap halves**, promoted from the r3 test after the user reported "Solids work wonderfully." Surrounding bodies remain **8% gyroid**; **normal supports and infill-first off** remain. All ten plates are freshly sliced and natively reopened. Original joint geometry, color boundaries, poses, support settings, all 50 Z12.4 screw-bolster caps and five top layers are preserved. See the [solid-lap production checks](release/knot-solid-laps-r1/README.md). The user-reported sample success does not independently qualify full-size performance. The [earlier r2 joint approval](release/knot-joint-approval-r1/README.md), [normal-support change](release/knot-normal-supports-r1/README.md) and [infill-first rollback](release/knot-infill-first-revert-r1/README.md) remain historical records.

**Letter:** user-consolidated six-plate project: C1 on 1, C2 on 2, C3/C4/C5 on 3, and V1/V2/V3 on 4–6. Slot 3 uses the ERYONE Ultra Silk Copper profile from the successful supplied sample: 220 C nozzle, 55 C Textured PEI bed, 0.98 flow and 7.5 mm3/s maximum volumetric speed. These printing parameters already matched the existing project. All six native print command streams are retained; their filament identity comments and checksums are updated. The current veneer edge correction, wall-base cleanup, CAD/STL, poses and process settings are preserved; infill-first remains off. See the [ERYONE promotion record](release/letter-eryone-r1/README.md).

**October 25 veneer correction:** the main [Letter.3mf](Letter.3mf) now contains **Left letter veneer**, **Right letter veneer** and **Center letter veneer** on plates 4–6, including the carrier-edge corrections and the approved ERYONE limits. Shared settings are 220 C printing nozzle, 55 C bed, 30–60 mm/s extrusion and 1500/2500 mm/s² print/travel acceleration. All six plates are freshly sliced and native-reopened; core geometry, reinforcement, poses and structural settings are preserved. All three veneers have full-height inspection, and their combined material estimate is 904.10 g. The separate output candidates are superseded. See the [current correction record](release/letter-veneer-correction/README.md). The physical whole-part shift remains unexplained; no successful print result is claimed.

The M has two short visible crown seams totaling 24.3 mm in front projection. The nearest core seam is 116.9 mm from a veneer seam, with no cross-layer seam intersections. This retains the latest correction to the former broad-fork layout description.

**Small Parts:** plates 1–2 are the original backer layouts; plate 3 contains the four wall blocks and 32 retainers; plate 4 is center jig r3 (V and B); plate 5 is side jig r1 (L1/L2/R1/R2). All use the original A1 companion process. See the [glue-jig fitting instructions](release/root-projects/Glue-Jigs.md).

**Separate A1 projects:** the PETG clips, transparent PLA guide, PLA sanding block and thin stencils retain their own saved profiles. The user explicitly chose to keep the local 12-clip and one-guide layouts exactly; the other seven tracing outlines are not added. The stencil sheets retain their existing 0% sparse infill, two walls and four top/bottom layers, giving solid 0.8 mm masks. Other projects keep 8% gyroid, 0.20 mm layers, four walls and five top/bottom layers; existing solid reinforcement and veneer overrides remain.

## CAD and STL

Each adjacent `.scad` is an exact **mesh-based OpenSCAD snapshot**, with a plate selector and optional modifier display. It references the adjacent STL folder. These are not reconstructed parametric feature histories. The original design development remains under `working/` and `scripts/`; historical generators can depend on retired projects and must not be used to overwrite the current release without review.

STLs are exported per material volume and modifier, with identical copies stored once. The SCAD and [catalog](release/root-projects/catalog.json) retain the saved placements, counts and material regions. STL alone cannot retain slicer settings, support paint or modifier semantics; use the 3MF for printing. The Letter snapshot includes its approved sacrificial carriers and fused necks.

## Verification and physical status

The **seven projects / 30 plates** include six sliced Letter plates. Current slice availability for each project is listed in the [release record](release/root-projects/README.md). Letter's ERYONE update preserves every mesh, support-paint record, pose, object/volume setting and native print command. OpenSCAD entry files previously passed parsing checks and the Letter CAD/STL are unchanged. Native notices concern unavailable traditional timelapse, not floating regions or bed collisions.

The earlier full-curve knot test, sanding thread test and supplied ERYONE hammered-finish sample were reported successful. The full-size knot joint-fit failure and subsequent r2 sample joint-fit success are recorded above; neither sample establishes full-size performance. The supplied Desktop ERYONE file retains an r3 filename but exactly matches the tracked r4 sample with r8 wall-base cleanup. Its success is recorded against that file's hash. Full-size Letter veneer performance remains unqualified. The corrected sanding clamp orientation, jig fit, local clip/guide layouts and stencil performance have not all been physically qualified by these digital checks. No printer job was sent.

After pulling this branch, run `git lfs pull` and `python scripts/audit_root_projects.py`. The [release record](release/root-projects/README.md) contains source hashes, preservation checks and estimates. `audit_dara_release.py` also routes to this current audit.

Retired 3MF files are removed from the current source tree, not erased from Git history. Local copies remain ignored; the former root Dara.3mf is retained locally under `.work/root-projects/retired/`. Older reports describe historical revisions rather than additional print choices.

Sanding block attribution: personal adaptation of [Compact Sanding Block – International Standards by DeepDiverDude](https://makerworld.com/en/models/2370141-compact-sanding-block-international-standards), supplied under the Standard Digital File License. Preserve its original attribution and license restrictions. Paper size: 228.6 × 69.85 mm (9 × 2¾ inches).
