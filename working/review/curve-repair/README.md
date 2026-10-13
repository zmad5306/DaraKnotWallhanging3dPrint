> Historical reference: superseded by the complete clean-edge reconstruction in working/review/clean-edges. The original traced geometry and local repair are retained as history, not current production evidence.

# Curve repair and final review â€” 2026-10-13

**All 12 identified curve defects are repaired. Geometry and cosmetic checks pass on the freshly sliced 31-plate project.** Use the current [Dara-Photo-Frame-A1-Complete.3mf](../../bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf). The [original review](../curve-artifacts/README.md) preserves the before-repair evidence.

The repaired CAD, production STLs, color modifiers, and saved extrusion paths agree. The white diamonds in the user's screenshot are Bambu's seam visualization; they are not white-filament commands. Actual white/blue paths were reviewed independently of those symbols.

## What changed

The twelve local outline bends were smoothed on F1, F2, F6, F8, F13, F15, and F19. At the five fabric-facing locations, the fabric boundary was changed together with the adjoining white rail, and the blue edge was regenerated from that boundary. The local smoothing uses a 2.5 mm Gaussian kernel, 0.25 mm samples, and a gradual taper to the exact original vertices at 14 mm along either side of each defect.

The largest boundary shift is **0.305 mm**; the reported plate-one blue-edge bend moves by at most **0.220 mm**. Total changed outline area is 9.752 mmÂ². The assembled outline bounds and topology are preserved. See the [before/after overlays](before-after-curves.png), [repaired assembly color map](assembly-color-map.png), and [measured source changes](source-repair.json).

All 39 production parts were exported from the repaired native CAD and compared as solids. Only the seven expected frame sections changed. The other **32 STL files are byte-identical** to their pre-repair versions. The solid differences stay within the reviewed neighborhoods. Joints, hardware interfaces, the 2.4 mm photo rabbets, weave detail away from those boundaries, plate placements, and print settings remain intact. The minimum separation between outline changes and any protected hardware region is 3.632 mm. [Geometry verification](geometry-verification.json).

## Repaired locations in the saved toolpaths

Each close-up below is drawn from the final G-code. The original review contains corresponding before images. All twelve close-ups and all seven changed full-plate surface plots were visually inspected after re-slicing.

| Location | Plate / part | Boundary | Maximum outline shift |
| --- | --- | --- | ---: |
| [C01](after/C01-toolpath.png) | 1 / F1 | Fabric / blue | 0.220 mm |
| [C02](after/C02-toolpath.png) | 1 / F1 | Outside white | 0.131 mm |
| [C03](after/C03-toolpath.png) | 2 / F2 | Fabric / blue | 0.106 mm |
| [C04](after/C04-toolpath.png) | 2 / F2 | Fabric / blue | 0.141 mm |
| [C05](after/C05-toolpath.png) | 2 / F2 | Outside white | 0.303 mm |
| [C06](after/C06-toolpath.png) | 6 / F6 | Outside white | 0.132 mm |
| [C07](after/C07-toolpath.png) | 8 / F8 | Fabric / blue | 0.110 mm |
| [C08](after/C08-toolpath.png) | 8 / F8 | Outside white | 0.132 mm |
| [C09](after/C09-toolpath.png) | 13 / F13 | Outside white | 0.134 mm |
| [C10](after/C10-toolpath.png) | 15 / F15 | Fabric / blue | 0.144 mm |
| [C11](after/C11-toolpath.png) | 15 / F15 | Outside white | 0.304 mm |
| [C12](after/C12-toolpath.png) | 19 / F19 | Outside white | 0.305 mm |

## Final checks

- **31 plates, 41 distinct meshes, 72 pieces:** source hashes, watertight solids, source-to-project mesh agreement, all 70 assembled production pieces, and plate placement pass. All 41 project meshes match their source STLs within 0.0001 mm.
- **74 reinforcement and 42 color modifiers:** shapes and filament assignments pass. The continuous blue edging is checked against the repaired CAD.
- **7,347,762 extrusion moves:** bead-aware bed-boundary checks pass, including support, brims, and towers. Minimum computed edge clearance is 0.673 mm. Printer startup purge/wipe/parking routines are outside this model-path audit.
- **All 63 blue-bearing layers:** blue centerlines remain inside the intended masks, with zero measured outside length using a 0.03 mm tolerance. White centerlines have zero length inside the blue core, defined as the mask inset by 0.3 mm. This covers three blue layers on each of 21 frame/sample plates. The independent parser examined 7,148,546 model extrusion moves across all 31 plates.
- **Curve screening:** zero remaining isolated bends above the review threshold. The test identifies turns over 6 degrees with at most 45 degrees of total absolute turn within 5 mm along either side; intended sharp corners and tight fillets require visual judgment. The original twelve locations were additionally inspected in the actual saved paths.
- **11 unit tests pass**, covering the bounds scanner, curve screening, and motion parsing. The only slicer notices concern unsupported traditional timelapse on the single-color plates.

Evidence: [full integrity audit](integrity-review.json), [cosmetic audit](after/review.json), and [production validation record](../../bambu/Dara-Photo-Frame-A1-Jointed/project-validation.json). Estimated total for all plates is **3,444.72 g and 129 h 7 min**, including both material tests.

These checks establish the digital results above, not a guarantee of a flawless physical print. Smaller outline deviations and material behavior are outside the automated screening criterion. Print plate **30** first to check the blue/white transition, metallic finish, seam appearance, and raised weave; molten-filament spreading and purge cleanliness require that physical check. The separate plate 31 checks the copper finish. The earlier photo-clearance change also remains physically unverified.

## File identity

| File | SHA-256 |
| --- | --- |
| Repaired production 3MF | `7f1ad1439c0c90b751bd251baa1493716657f975249fb2e3b5e7c8c475f6173e` |
| Repaired native CAD | `0c6166d97fbc5490312e49fc3896ad284f9c866458d17f52123381659ddfd17d` |
| Pre-repair production 3MF | `aaeff8be8c38757c6c9564f9229f2f380e733f4ee6a12a6d2ec64c4b7c76749e` |
| Pre-repair native CAD | `6a36c93c064dc1b59ba02562f343b1ae2b3d563f72296fbaf79a3e5b58d98994` |

The frozen reference remains unchanged as provenance. Pre-repair CAD, STL, and project copies are preserved locally under `.work/curve-repair/`.

## Recheck the published files

From the repository root, with the project Python dependencies available:

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/validate_print_project.py
python scripts/review_curve_artifacts.py --output working/review/curve-repair/after --repaired-findings working/review/curve-artifacts/review.json
```

The curve script writes a report even if defects are found. Inspect `summary.cosmetic_review_passed` and `summary.surface_color_checks_passed`; an exit code alone is insufficient. The explicit output path preserves the historical before-review files.

## Rebuilding this revision

This revision's scripts use the preserved pre-repair `original.scad`, `original-stls/`, `baseline.3mf`, and `baseline.json` under `.work/curve-repair/`, plus the original findings under `working/review/curve-artifacts/`. Do not replace those inputs with the current files. They are local revision inputs, not a portable clean-clone build system.

```powershell
python scripts/repair_curve_artifacts.py
python scripts/export_jointed_stls.py --jobs 3
python scripts/refresh_curve_project.py
```

Open `.work/curve-repair/repaired-curves.3mf` in Bambu Studio 02.08.02.61, **Slice all**, **Save Project As** `.work/curve-repair/models.3mf`, and **Export all sliced file** as `.work/curve-repair/models.gcode.3mf` from the same project. Then:

```powershell
python scripts/combine_ams_slices.py --models .work/curve-repair/models.3mf --slices .work/curve-repair/models.gcode.3mf --baseline .work/curve-repair/staged.json --output .work/curve-repair/complete.3mf
python scripts/validate_print_project.py --project .work/curve-repair/complete.3mf --baseline .work/curve-repair/complete.json --report .work/curve-repair/audit.json
python scripts/review_curve_artifacts.py --project .work/curve-repair/complete.3mf --baseline .work/curve-repair/complete.json --output working/review/curve-repair/after --repaired-findings working/review/curve-artifacts/review.json
python scripts/publish_curve_project.py
```

The publisher requires matching successful integrity and cosmetic audits, unchanged slicing settings, and the expected CAD/project hashes before replacing the production package. It also refreshes the manifests and test-plate records.
