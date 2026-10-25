# Accepted knot joint sample and production publication — October 25, 2026

Current production: root **`Knot.3mf`**, A2L, ten plates F1–F10. All existing joints use the geometry of the accepted production-derived test, with **infill-first OFF** and **normal(auto) supports**.

The user reported: "Joints are ok, propagate them into the project as well as the infill first change. Commit and push when done."

This follows the current **Dara-A2L-Joint-Photo-Retainer-Bolster-r2.3mf**: J3, F2 tongue/F3 socket, both locating keys and a photo-retainer blind-hole bolster. Record this as user-reported sample joint-fit success. The actual printed hash and printer were not independently observed. The user did not confirm bolster surface appearance, screw retention or full-size performance. The earlier full-size fit failure remains recorded; r1 is withdrawn because it selected an M through-hole reinforcement.

## What is published

The accepted r2 was cropped from this exact production project. A fresh comparison of every retained volume and effective setting confirms that the matching geometry is already present. **No joint dimensions were changed during publication, and no new reslice was needed.** The existing ten native slices already contain the requested infill-first rollback and normal supports. The changes from the previously committed project are the two authorized settings and regenerated slice assets, with geometry, material profiles, poses, support paint and object/volume settings preserved.

Structural 8% gyroid, 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers and Textured PEI remain. All 42 lap pads remain removed; all 50 screw modifiers remain 100% infill capped at Z12.4. Five blue layers remain. Letter, the other root projects and adjacent CAD/STLs are unchanged.

## Verification and exact files

- Production SHA-256: `aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46`.
- Accepted supplied r2 SHA-256: `c0e48a0b2f7c8bf8adcc696b9785d4ff49359dd9104536ca486a1ec50055154d`.
- `validation.json`: fresh sample-to-production crop/setting comparisons, all ten G-code settings, protected hashes and links to the exact supporting evidence.
- [Normal-support verification](../knot-normal-supports-r1/README.md): all 14 joints, 28 keys, 140 key-layer path checks, native slices/reopen, support backing, removed pads, five-layer screw skin, colors, bounds and checksums.
- [Accepted sample evidence](../../output/Dara-A2L-Joint-Photo-Retainer-Bolster-r2/README.md): crop provenance, explicit photo-retainer identification and native toolpaths. Its 3MF remains local/ignored under the existing tracked-project inventory rule; the root production 3MF is the published print artifact.

The full root audit covers seven projects / 30 plates and the current preset snapshots. Knot's stored estimate remains **78h 57m / 2284.10 g**. No printer job was sent.

After pulling, run `git lfs pull` and `python scripts/audit_root_projects.py` to verify the published production files.
