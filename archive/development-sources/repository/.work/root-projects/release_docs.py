from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,hashlib
R=Path.cwd();out=R/'release/root-projects';cat=json.loads((out/'catalog.json').read_text())
rows=[];slices={}
for title,row in cat.items():
 with zipfile.ZipFile(R/row['project']) as z:
  ps=E.fromstring(z.read('Metadata/slice_info.config')).findall('plate')
  props=lambda n:{m.get('key'):m.get('value') for m in n.findall('metadata')}
  secs=sum(int(props(p)['prediction']) for p in ps);grams=sum(float(props(p)['weight']) for p in ps)
  rows.append(f'| {title} | {len(ps)} | {secs//3600}h {(secs%3600)//60:02d}m | {grams:.2f} g |')
  slices[title]={f'plate_{i}':hashlib.sha256(z.read(f'Metadata/plate_{i}.gcode')).hexdigest() for i in range(1,len(ps)+1)}
(out/'gcode-sha256.json').write_text(json.dumps(slices,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'README.md').write_text('''# Root project release — October 22, 2026

The user requested root Knot (A2L), Letter (A2L), and supporting A1 projects with adjacent CAD/STL, and removal of all other 3MF files from source control. The follow-up explicitly allowed multiple supporting projects for different A1 settings, and added the sanding block and photo cut aligner. The user selected **keeping both locally saved layouts exactly** after being told they contain 12 crate clips and one photo guide.

| Project | Plates | Native time | Material |
| --- | ---: | ---: | ---: |
'''+ '\n'.join(rows)+'''

These are slicer estimates, not observed print times.

## Preservation evidence

- `sources.json`: exact input paths and SHA-256 hashes. Stencils were recovered from commit `3005467` without changing the checkout. Other inputs were read from the existing local files; their hashes were checked unchanged after packaging.
- `letter-preservation.json`: exact retained volume topology, coordinates, object/volume settings, support paint and bed poses. Former plates 11–17 become 1–7; only display-grid offsets, plate references and tower-array indexing change. All seven G-code payloads are unchanged.
- `small-parts-preservation.json`: the original 44 accessories plus six current jig pieces, unchanged. Independent inputs reused numeric mesh IDs; these were namespaced before native slicing to avoid Bambu treating different pieces as shared meshes. Actual geometry and settings were compared after native saving.
- `*-slice-preservation.json`: fresh native slices retain the input geometry, paint, bed poses and effective settings. Bambu's source-matrix bookkeeping and empty preset metadata normalization are listed separately. No empty preset field is treated as permission to change a process value.
- `*-native.json`: native Bambu return codes and slicing estimates. All are successful. Traditional timelapse notices persist; no geometric or plate-boundary warning remains in the saved slices.
- `cad-validation.json`: all seven OpenSCAD entry files parsed successfully. CAD is explicitly mesh-based, using the adjacent STL volumes. Original design development remains available separately; no parametric feature history is claimed for these snapshots.
- `catalog.json`: current project, CAD and per-volume STL hashes, geometry bounds, settings, material regions, modifiers and placements. `gcode-sha256.json` identifies every stored plate toolpath.

Knot and Sanding Block are byte-identical copies of their selected source projects. Letter retains its existing native slices. Small Parts, Crate Clips, Photo Cut Aligner and Crate Stencils were freshly sliced. The local clip and guide layouts were preserved; the source projects were not overwritten. No printer job was sent.

The quick audit is `python scripts/audit_root_projects.py`. It uses only Python's standard library and validates the tracked/root 3MF inventory, checksums, printer/process constants, plate assignments and G-code checksums. Deep mesh/pose comparisons are recorded against the same hashes. No physical validation is implied by these checks.

## Physical evidence carried forward

The r3 full-curve knot test was reported successful; the full-size corrected knot remains physically unqualified. The 42 lap pads removed in the earlier correction stay removed. The successful supplied r3 test remains recoverable from commit `5dab12a` in Git/LFS history.

The sanding thread test was reported good. The complete current r4 retains those threads and support blocking; only the clamp's 1.174806-degree bed rotation was added in its own chat. That orientation, complete paper grip, jig fit/retention, clip fit, guide stiffness/clarity, stencil print/spray behavior and full-size veneer anti-warp performance are not newly qualified here.

The sanding block is a personal adaptation of DeepDiverDude's Compact Sanding Block – International Standards, supplied under the Standard Digital File License. Attribution and restrictions remain applicable; see the root guide.

Historical reports under working/output/reference remain records of their exact revisions. Their old project links may require retrieving the relevant commit; they are not additional current print choices. No Git history was rewritten.
''',encoding='utf-8',newline='\n')
(out/'Glue-Jigs.md').write_text('''# Veneer glue aligners — Small Parts plates 4 and 5

Plate 4 contains the center **r3** V (crotch) and B (stem bottom) pieces. Plate 5 contains side **r1** L1/L2 for the left veneer and R1/R2 for the right. The cores must already be glued together and still off the knot. Left/right are viewed from the finished front.

Use the existing #6-19 × ½-inch pan-head plastic thread-forming screws with 10 mm OD × 1 mm washers, one per guide. The underside recesses have supports: clean the screw bore, washer seat, brim and support residue before fitting. Each guide registers the actual core/veneer edges and fastens to an existing rear mounting hole. The screws retain the guides; weights and a caul above the veneer supply glue pressure.

1. Place the core back up. Fit the guides and start the screws loosely from underneath.
2. Seat each guide gently against its locating edges, then snug by hand. Do not use screw force to distort the core or guide.
3. Turn the assembly face up and dry-fit the veneer with its original seating features engaged. Confirm free seating, aligned edges and stable guides before glue.
4. Keep adhesive off the guides and locating features. Add release film, a caul and weights. Support other loaded regions at the same **10.4 mm height** so the core does not flex.
5. After curing, support the assembly and remove the screws from underneath. Retain that hardware for mounting the M.

Guides retain 0.15 mm clearance per side and 0.85 mm glue-line relief. Recesses are 12 mm diameter × 4 mm deep around 4.4 mm bores. With the specified screw/washer, engagement is 5.3 mm; the nominal head clears the table by 0.5 mm. Check actual screw heads while dry-fitting. Physical fit, retention and glue release remain unconfirmed.

The original center r1/r2 guides were withdrawn and are not included. The six current guides share the companion's saved white PLA / 0.20 mm / 8% gyroid settings, with their existing 1 mm brims and tree supports. The other accessory plates retain their own original overrides.
''',encoding='utf-8',newline='\n')
# Flag retired entry points as historical, without rewriting their evidence.
for folder,current in [
('working/bambu/Dara-Photo-Frame-A2L','Knot.3mf and Letter.3mf'),
('working/bambu/Dara-A2L-Knot-Infill-First','Knot.3mf'),
('working/bambu/Dara-A1-Companion','Small Parts.3mf'),
('working/bambu/Dara-A2L-Production-Joint-Sample','the root project guide'),
('output/Dara-A2L-Photo-Curve-Infill-First-r3','Knot.3mf')]:
 p=R/folder/'README.md'
 if p.exists():
  s=p.read_text(encoding='utf-8');p.write_text('> **Historical record:** the 3MF files in this folder are retired from source control. Use '+current+' at the repository root. This document records the original revision; retrieve commit `5dab12a` and its LFS objects if the historical projects are needed.\n\n'+s,encoding='utf-8',newline='\n')
# Native stdout is empty in this Windows build; JSON results are the useful evidence.
for p in out.glob('*.log'):
 if p.stat().st_size==0:p.unlink()
print('Wrote release evidence and retained physical-fit instructions.')
