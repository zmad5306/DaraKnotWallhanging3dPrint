import sys,json,re
from pathlib import Path
sys.path.insert(0,'scripts')
import prepare_y_stable_dara as p
root=p.ROOT;pkg=p.PACKAGE;review=p.REVIEW
r=json.loads((p.WORK/'normal-validation.json').read_text());t=json.loads((p.WORK/'test-validation.json').read_text())
rows=r['changed_plates'];cu=[x for x in rows if x['plate'] in p.MPLATES];assembly=[x for x in rows if x['plate'] not in [30,32]]
row32=next(x for x in rows if x['plate']==32);row30=next(x for x in rows if x['plate']==30)
def time(s):return f'{int(s)//3600} h {(int(s)%3600)//60:02d} min'
def estimate(rs):return f'{sum(x["weight_g"] for x in rs):,.2f} g and {time(sum(x["seconds"] for x in rs))}'
motion='The broad copper face planes now run along the A1 bed\'s Y travel, with the 55-degree lean across X. Each part is rotated within that plane to fit at its original scale. M1 and M3 reach approximately 238 and 241 mm; the other four are 63-102 mm tall. Tree supports are regenerated with 3 mm branch diameter and two walls. A 6 mm outer object brim is requested; where the tilted part has no first-layer area, the generated tree base supplies the anchoring.'
limits='Project-wide X/Y limits are 1,000 mm/s² acceleration and 150 mm/s speed. Process travel and default print acceleration are 1,000 mm/s²; outer walls, top surfaces and the first layer use 500 mm/s². Major process speeds are capped at 150 mm/s. All 32 plates were re-sliced, including the frame and optional samples. These conservative settings increase print time; they do not prove physical adhesion or eliminate sway.'
cost=f'All 32 plates: **{estimate(rows)}**. Assembly without optional plates 30 and 32: **{estimate(assembly)}**. Copper plates 21-26 and 31: **{estimate(cu)}**. Optional plate 30: **{estimate([row30])}**; plate 32: **{estimate([row32])}**. Estimates include supports and purge. Copper exceeds one 1 kg spool before retries.'
rootfile=root/'README.md';text=rootfile.read_text(encoding='utf-8');tail=text[text.index('**Earlier full-size tilted candidate'):]
intro=f'''# Dara knot wall hanging

**Current complete print file, 2026-10-15: [Dara.3mf](Dara.3mf).** Open as a project in Bambu Studio. All **32 plates** are sliced, with **75 assembly pieces and three optional test pieces**. Plates **21-26** contain the full-size hammered M; **31** has its five copper cover bands; **32** has the full-color F7/F4 epoxy mock glue-up pair. Copper is **slot 3**. [Printing and assembly](working/bambu/Dara-Photo-Frame-A1-Jointed/PRINT-READINESS.md).

**Y-bed correction:** {motion} {limits} [Orientation, support previews and current validation](working/review/y-stable-dara/README.md).

The corrected [Dara-Hammered-Band-Test.3mf](Dara-Hammered-Band-Test.3mf) contains the real joint crops in their production parents' new orientations, plus the full-size curved band. Estimate: **{t['total_weight_g']:.2f} g and {time(t['total_seconds'])}**. [Test instructions](Dara-Hammered-Band-Test.txt). Full-height adhesion and physical band seating remain unverified; reopen this saved project rather than printing an older cached slice.

The separate [Dara-Hammered-Bands-Candidate.3mf](Dara-Hammered-Bands-Candidate.3mf) contains the same Y-aligned copper geometry on seven plates, using copper **slot 1**. The original 599.88 x 358.74 mm M outline, all 22 mounting features, joint clearances, bands and texture are retained. [Assembled geometry](working/review/hammered-bands/assembled-bands.png). Do not mix these sections with earlier M revisions.

{cost}

'''
rootfile.write_text(intro+tail,encoding='utf-8')
f=pkg/'README.md';s=f.read_text(encoding='utf-8')
s=s.replace('original white/wood/blue geometry and slices','original white/wood/blue geometry, re-sliced with gentle motion')
s=s.replace('tilted 55 degrees, tree supports included','55 degrees, face planes along Y, regenerated trees')
s=s.replace('The 55-degree orientations, hammered texture, native tree supports and ten local solid screw regions come from the validated banded candidate.',motion+' The hammered texture and ten local solid screw regions are retained.')
s=s.replace('21.27 g and about 1 h 30 min',f'{t["total_weight_g"]:.2f} g and {time(t["total_seconds"])}')
s=s.replace('The frame, backer, hardware and weave-sample plates retain their prior models, object settings, placements, native G-code and preview assets.','The frame, backer, hardware and weave-sample plates retain their models, object settings and placements. Their slices and previews were regenerated for the project-wide motion limits.')
s=re.sub(r'All 32 plates, including both optional tests:.*?\n\n',cost+'\n\n'+limits+'\n\n',s,flags=re.S)
s=re.sub(r'\[Current validation\]\(knot-glue-sample-validation.json\).*?\n\n', '[Current validation](y-stability-validation.json) records every plate estimate and G-code hash, native geometry round trips, support contacts, motion commands and unchanged instances. All 32 checksums pass and both normal project copies match. The [earlier knot report](knot-glue-sample-validation.json) records the source crop and full-color sample checks; the [earlier hammered report](hammered-integration-validation.json) records original mounting-region checks. Their hashes and estimates describe prior releases.\n\n',s,flags=re.S)
s += '\nThe Y correction is applied by `scripts/prepare_y_stable_dara.py` using `stage`, `slice`, `verify`, `render` and `publish`. It expects the files from commit `85d0690` and refuses to reinterpret later placements. The updated `scripts/prepare_hammered_bands.py` also uses the Y-aligned placement rule for future generation. [Details](../../review/y-stable-dara/README.md).\n'
f.write_text(s,encoding='utf-8')
f=pkg/'PRINT-READINESS.md';s=f.read_text(encoding='utf-8')
s=s.replace('The latest addition is the full-color knot joint practice pair on plate 32; the preceding 31 plates are unchanged.','The copper has been realigned for Y bed motion, and all 32 plates have been re-sliced with gentle motion limits. The full-color knot joint practice pair remains on plate 32.')
s=s.replace('new M1-M6 hammered sections at 55 degrees, tree supports included.','M1-M6 hammered sections at 55 degrees, face planes along Y, regenerated tree supports.')
s=s.replace('21.27 g and about 1 h 30 min',f'{t["total_weight_g"]:.2f} g and {time(t["total_seconds"])}')
s=s.replace('## Material and time',motion+'\n\n'+limits+'\n\n## Material and time')
s=re.sub(r'The assembly pieces require an estimated.*?\n\n',cost+' Per-plate details are in [the current report](y-stability-validation.json).\n\n',s,flags=re.S)
s=s.replace('Adding plate 32 preserves the preceding 31 plates\' resources, settings, placements and G-code.','The Y correction preserves geometry and non-copper placements, repaints support eligibility for the rotated copper, and regenerates all 32 slices. Motion-limit commands, bed clearance and decorative-face support clearance are checked in the new report.')
s=s.replace('[Current report](knot-glue-sample-validation.json)','[Current report](y-stability-validation.json)')
s=s.replace('still applies to the preserved frame plates','still documents the retained frame geometry; all frame plates have now been re-sliced')
f.write_text(s,encoding='utf-8')
f=root/'Dara-Hammered-Band-Test.txt';s=f.read_text(encoding='utf-8')
s=s.replace('55 degrees and already sliced with tree supports.','55 degrees with their broad face planes along Y and the lean across X.\nT2 and T3 use their full-size parents\' rotations, with regenerated trees.\nThe saved process and X/Y motion limits are conservative: 1000 mm/s2\nacceleration, 150 mm/s speed, with 500 mm/s2 outer walls and top surfaces.')
s=re.sub(r'Studio estimate:.*?supports included\.',f'Studio estimate: {t["total_weight_g"]:.2f} g and {time(t["total_seconds"])}, supports included.',s)
s=s.replace('working/review/hammered-bands/test-validation.json','working/review/y-stable-dara/test-validation.json').replace('working/review/hammered-bands/test-supports.png','working/review/y-stable-dara/test-supports.png')
s += '\nThe 6 mm outer object brim applies where Studio can generate one. The\ntilted pieces are also anchored by tree support bases. This small sample\nchecks finish and fit; it does not establish adhesion or sway at full height.\n'
f.write_text(s,encoding='utf-8')
f=root/'working/review/knot-glue-sample/README.md';s=f.read_text(encoding='utf-8')
s=re.sub(r'\*\*Studio estimate:\*\* .*?This includes',f'**Current Studio estimate:** {row32["weight_g"]:.2f} g total, {time(row32["seconds"])}. This includes',s)
s=s.replace('All preceding 31 plate assets and production meshes/settings are unchanged.','That report describes the original addition of the sample. The later [Y-bed correction](../y-stable-dara/README.md) retains its geometry, orientation and colors but re-slices it with gentler project-wide motion limits; use the [current project audit](../../bambu/Dara-Photo-Frame-A1-Jointed/y-stability-validation.json) for current G-code hashes and estimates.')
f.write_text(s,encoding='utf-8')
table=[]
for i in range(1,7):
 c=r['choices'][f'M{i}'];a=next(x for x in rows if x['plate']==20+i)
 table.append(f'| M{i} | {20+i} | '+ ' × '.join(f'{v:.1f}' for v in c['build_extent_mm'])+f' | {a["conservative_bed_edge_clearance_mm"]:.2f} | {a["weight_g"]:.2f} | {time(a["seconds"])} |')
notes=f'''# A1 Y-bed correction — 2026-10-15

Use the normal [Dara.3mf](../../../Dara.3mf), its identical [package copy](../../bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf), or the corrected [small band test](../../../Dara-Hammered-Band-Test.3mf). All are saved native projects with slices. No print job was started or changed.

{motion}

The previous placement search minimized the bed footprint without a Y-axis constraint. The replacement fixes world yaw at 90 degrees and searches the rotation within the face for the lowest height that fits. Every original face normal maps to approximately (0.81915, 0, 0.57358): the face contains Y, and the lean is across X. T2 and T3 inherit the M2/M3 parent rotations. No geometry is scaled, cropped again for manufacture, or repartitioned. Joint, texture, cover-band, screw and locator geometry remains unchanged.

| Section | Plate | Model X × Y × Z (mm) | Bead edge clearance (mm) | Grams | Time |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(table)}

Clearance includes support paths, bead widths and arc extrema. Heights are model dimensions; slicing uses 0.2 mm layers. M1 and M3 are close to the printer's height limit, so their physical stability remains unverified despite passing the digital fit checks.

![Native copper support paths](normal-supports.png)

{limits}

The export explicitly contains `M201 X1000 Y1000` and `M203 X150 Y150` axis limits. This matters because conditional firmware inspection code can leave a higher `M204 S5000` request active until the next feature change. The report preserves those raw requested maxima and separately records the Y-axis bounds under the emitted axis limits. No generated G-code was patched. These are configuration checks, not measurements of printer motion. The [Bambu source](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/GCode.cpp) is the reference for generated motion commands; this release is checked against the locally installed Studio's actual output.

Supports use the saved tree process, 3 mm branch diameter and two walls. Eligibility is recalculated in the new orientation while blocking the decorative surface and mounting bores. Actual interface paths are checked against the face/seat envelope. Some tilted sections have no model area on layer 1 and therefore no separate `Brim` feature: the slicer builds their anchors as first-layer `Support`. The report records the actual tree-base footprint and does not equate a requested 6 mm brim with a guaranteed continuous brim around every tree.

{cost}

The band test is **{t['total_weight_g']:.2f} g / {time(t['total_seconds'])}**. It uses the real parent orientations but is too short to validate full-height sway. Keep the standard 100% print-speed setting when evaluating these limits; changing the speed mode changes the trial.

![Native test support paths](test-supports.png)

## Verification and reproduction

[Normal project](normal-validation.json), [small test](test-validation.json), and [seven-plate copper project](candidate-validation.json) record hashes, settings, native mesh comparisons, support contacts, bed bounds, motion commands and estimates. All 78 normal-project instances are retained, including 32 retainers and the full-color epoxy pair. Non-copper geometry and placements are preserved; every plate is freshly sliced. Earlier frame plate 6 has 0.634 mm bead clearance, unchanged from its baseline; the stricter 1.5 mm minimum applies to the newly oriented copper plates.

`scripts/prepare_y_stable_dara.py` migrates the exact pre-correction release from commit `85d0690`. Its immutable input copies and slicer intermediates live in ignored `.work/y-stable-dara`; it refuses a different input hash. Sequence: `stage`, `slice test`, `verify test`, `slice normal`, `verify normal`, `slice candidate`, `verify candidate`, `render test`, `render normal`, `publish`. Native slicing requires the installed Bambu Studio CLI. The general copper generator now uses the same Y-alignment helper for future generation. The untouched historical geometry reports retain the old placement transforms; the current poses are in these new reports.

Run `python scripts/integrate_hammered_dara.py audit` to check the distributed normal project and all 32 G-code hashes. Physical adhesion, support removal, glue fit and full-height stability remain to be tested.
'''
(review/'README.md').write_text(notes,encoding='utf-8')
print(cost)
