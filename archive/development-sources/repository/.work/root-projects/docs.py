from pathlib import Path
import json
R=Path.cwd()
# Preserve the pre-existing README corrections in the new current guide.
(R/'README.md').write_text('''# Dara knot wall hanging

Open the root 3MF files **as projects** in Bambu Studio to retain their saved printers, materials and settings. These are the only Bambu projects maintained in source control. Supporting A1 projects are separated where their settings differ.

| Project | Printer | Plates | Contents | CAD / STL |
| --- | --- | ---: | --- | --- |
| [Knot](Knot.3mf) | A2L | 10 | Corrected full-size F1–F10, infill first | [CAD](Knot.scad) / [STL](<Knot STL/>) |
| [Letter](Letter.3mf) | A2L | 7 | Five M cores, three hammered veneers with r6 wall carriers | [CAD](Letter.scad) / [STL](<Letter STL/>) |
| [Small Parts](<Small Parts.3mf>) | A1 | 5 | Eight photo backers, four wall blocks, 32 retainers and six veneer glue aligners | [CAD](<Small Parts.scad>) / [STL](<Small Parts STL/>) |
| [Crate Clips PETG](<Small Parts - Crate Clips PETG.3mf>) | A1 | 1 | The locally saved 12-clip layout; upper gussets removed, supports off | [CAD](<Small Parts - Crate Clips PETG.scad>) / [STL](<Small Parts - Crate Clips PETG STL/>) |
| [Photo Cut Aligner](<Small Parts - Photo Cut Aligner.3mf>) | A1 | 1 | The locally saved single Backer 2 honeycomb guide; SUNLU transparent PLA | [CAD](<Small Parts - Photo Cut Aligner.scad>) / [STL](<Small Parts - Photo Cut Aligner STL/>) |
| [Sanding Block PLA](<Small Parts - Sanding Block PLA.3mf>) | A1 | 1 | All five r4 parts, confirmed thread setup and corrected clamp orientation | [CAD](<Small Parts - Sanding Block PLA.scad>) / [STL](<Small Parts - Sanding Block PLA STL/>) |
| [Crate Stencils](<Small Parts - Crate Stencils.3mf>) | A1 | 6 | Three THIS END UP tiles and three FRAGILE tiles | [CAD](<Small Parts - Crate Stencils.scad>) / [STL](<Small Parts - Crate Stencils STL/>) |

## Plate order and settings

**Knot:** plates 1–10 are F1–F10. The successful r3 full-curve test supplied the infill-first correction and 0.20 mm support-interface spacing. The support top gap remains 0.20 mm. The earlier 42 raised lower-lap pads remain removed. Mortises, keys, glue recesses, colors and remaining settings are preserved.

**Letter:** plates 1–4 contain C1, C2, C3, then C4/C5. Plates 5–7 contain V1, V2 and V3. These map directly to old Dara plates 11–17; all seven G-code payloads are byte-identical. Infill-first remains off. The approved r6 wall carriers retain the two 4 × 0.6 mm ties at the open ends. The three veneers and complete supports total 902.59 g. Keep the saved rotations.

The M has two short visible crown seams totaling 24.3 mm in front projection. The nearest core seam is 116.9 mm from a veneer seam, with no cross-layer seam intersections. This retains the latest correction to the former broad-fork layout description.

**Small Parts:** plates 1–2 are the original backer layouts; plate 3 contains the four wall blocks and 32 retainers; plate 4 is center jig r3 (V and B); plate 5 is side jig r1 (L1/L2/R1/R2). All use the original A1 companion process. See the [glue-jig fitting instructions](release/root-projects/Glue-Jigs.md).

**Separate A1 projects:** the PETG clips, transparent PLA guide, PLA sanding block and thin stencils retain their own saved profiles. The user explicitly chose to keep the local 12-clip and one-guide layouts exactly; the other seven tracing outlines are not added. The stencil sheets retain their existing 0% sparse infill, two walls and four top/bottom layers, giving solid 0.8 mm masks. Other projects keep 8% gyroid, 0.20 mm layers, four walls and five top/bottom layers; existing solid reinforcement and veneer overrides remain.

## CAD and STL

Each adjacent `.scad` is an exact **mesh-based OpenSCAD snapshot**, with a plate selector and optional modifier display. It references the adjacent STL folder. These are not reconstructed parametric feature histories. The original design development remains under `working/` and `scripts/`; historical generators can depend on retired projects and must not be used to overwrite the current release without review.

STLs are exported per material volume and modifier, with identical copies stored once. The SCAD and [catalog](release/root-projects/catalog.json) retain the saved placements, counts and material regions. STL alone cannot retain slicer settings, support paint or modifier semantics; use the 3MF for printing. The Letter snapshot includes its approved sacrificial carriers and fused necks.

## Verification and physical status

All **seven projects / 31 plates** contain native slices. Knot and the sanding block are byte-identical copies of their approved source projects; Letter retains its seven original slices. Small Parts, the local clip/guide layouts and the stencils were freshly sliced. Meshes, support paint, effective settings and actual bed poses were compared against the sources. OpenSCAD entry files passed parsing checks. Native notices concern unavailable traditional timelapse, not floating regions or bed collisions.

The full-curve knot test and sanding thread test were reported successful. The full-size knot, corrected sanding clamp orientation, veneer carrier performance, jig fit, local clip/guide layouts and stencil performance have not all been physically qualified by these digital checks. No printer job was sent.

After pulling this branch, run `git lfs pull` and `python scripts/audit_root_projects.py`. The [release record](release/root-projects/README.md) contains source hashes, preservation checks and estimates. `audit_dara_release.py` also routes to this current audit.

Retired 3MF files are removed from the current source tree, not erased from Git history. Local copies remain ignored; the former root Dara.3mf is retained locally under `.work/root-projects/retired/`. Older reports describe historical revisions rather than additional print choices.

Sanding block attribution: personal adaptation of [Compact Sanding Block – International Standards by DeepDiverDude](https://makerworld.com/en/models/2370141-compact-sanding-block-international-standards), supplied under the Standard Digital File License. Preserve its original attribution and license restrictions. Paper size: 228.6 × 69.85 mm (9 × 2¾ inches).
''',encoding='utf-8',newline='\n')
p=R/'AGENTS.md';s=p.read_text(encoding='utf-8');a=s.index('- The main production project');b=s.index('- The older complete A1 design',a)
s=s[:a]+'''- **Approved root organization, 2026-10-22:** the user requested root projects
  with adjacent CAD and STL, removal of all other Bambu projects from source
  control, then explicitly allowed separate supporting projects for different
  A1 settings and requested the sanding block and photo cut aligner.
- Current root **`Knot.3mf`** is the corrected A2L F1–F10 project, ten plates.
  **`Letter.3mf`** is the A2L M, seven plates: cores on 1–4 and veneers on 5–7.
  These map to former Dara plates 11–17. Preserve their geometry, settings,
  bed poses and original stored toolpaths. Infill-first stays off in Letter.
- Root **`Small Parts.3mf`** is the A1 companion plus glue aligners: original
  backers on 1–2, wall blocks/retainers on 3, center r3 jigs on 4 and side r1
  jigs on 5. Their common saved process and object overrides are preserved.
- Separate root A1 projects preserve their different settings:
  **`Small Parts - Crate Clips PETG.3mf`**, **`Small Parts - Photo Cut Aligner.3mf`**,
  **`Small Parts - Sanding Block PLA.3mf`** and **`Small Parts - Crate Stencils.3mf`**.
  The user explicitly chose the exact locally saved **12-clip and single-guide
  layouts**, not the original eight-piece sets. Keep the latest sanding r4
  clamp rotation and physically confirmed thread setup. The existing stencil
  exception is 0% sparse infill, gyroid, two walls and four top/bottom layers.
- Adjacent SCAD files are exact mesh-based CAD snapshots referencing their STL
  folders, not parametric feature histories. Keep them synchronized with the
  3MF geometry and release catalog. The seven root projects are the only
  tracked 3MF files. Retired projects remain in Git history/local ignored files.
  Historical references to Dara.3mf and working Bambu paths below identify the
  sources of past changes; they do not reinstate those paths as current releases.
''' + s[b:]
s=s.replace('`working/bambu/Dara-A2L-Knot-Infill-First/Dara-A2L-Knot-Infill-First.3mf`\n  for full-size','`Knot.3mf` (originally the separate working-folder project)\n  for full-size')
s=s.replace('  main project. Root/named complete/editable main projects and all M/A1 files\n  remain unchanged.','  main project. This correction originally left the combined main and M/A1\n  files unchanged; the later root organization above supersedes file packaging.')
p.write_text(s,encoding='utf-8',newline='\n')
# Allow only the named root projects; retain old STL exceptions unrelated to this reorganization.
p=R/'.gitignore';s=p.read_text();s='\n'.join(line for line in s.splitlines() if not (line.startswith('!') and '.3mf' in line))+'\n'
s+='\n# Current root projects and exact companion mesh exports.\n'
for t in json.loads((R/'release/root-projects/catalog.json').read_text()):s+=f'!/{t}.3mf\n!/{t} STL/*.stl\n'
p.write_text(s,encoding='utf-8',newline='\n')
p=R/'.gitattributes';s=p.read_text();s+='\n# Release hashes are portable across Windows and LF checkouts.\n/*.scad text eol=lf\n/release/root-projects/** text eol=lf\n'
p.write_text(s,encoding='utf-8',newline='\n')
print('Updated root guide, canonical project rules and tracked-file allowlist.')
