import sys,json,shutil,hashlib
from pathlib import Path
sys.path[:0]=['.work/python-libs','scripts']
import organize_root_projects as org
from development_3mf import sha
ROOT=Path.cwd();WORK=ROOT/'.work/veneer-face-r9';NATIVE=WORK/'native-veneers-r9';OUT=ROOT/'output/Dara-A2L-Veneers-Carrier-Motion-r9';OUT.mkdir(exist_ok=True)
TITLE='Dara-A2L-Veneers-Carrier-Motion-r9'
validation=json.loads((NATIVE/'validation.json').read_text());edge=json.loads((NATIVE/'edge-validation.json').read_text());geometry=json.loads((WORK/'edge-geometry.json').read_text())
motion=[]
for i in (1,2,3):
 d=json.loads((NATIVE/f'V{i}-motion.json').read_text())
 ranges={k:[min(map(float,v)),max(map(float,v))] for k,v in d['acceleration_path_mm'].items()}
 assert all(v[1]<=(2500 if k=='Travel' else 1500) for k,v in ranges.items())
 motion.append(dict(veneer=i,measured_command_acceleration_ranges_mm_s2=ranges,travel_feedrate_limit_mm_s=500,print_speed_settings_unchanged=True,conditional_machine_actions_not_simulated=True))
target=OUT/(TITLE+'.3mf');shutil.copyfile(NATIVE/'sliced.3mf',target)
assert sha(ROOT/'Letter.3mf')==validation['source_sha256']
validation.update(delivered_file=str(target),delivered_sha256=sha(target),root_Letter_unchanged=True,physical_evidence=dict(reported_failed_veneer='V1',reported_slicer_onset_layers=[692,693,694],reported_slicer_z_mm=[138.4,138.6,138.8],observations=['Photographs taken from the right side of the printer.','User reports rearward displacement across the veneer and both ends of the supporting wall.','Only one corresponding carrier-end jog is present in the audited original V1 slice at these layers.','The proposal that this was a return from an earlier shift was not confirmed by the user.'],diagnosis='A small programmed carrier-edge jog and ineffective object acceleration overrides are verified. The physical whole-part displacement remains unexplained; neither finding proves its cause.'),motion=motion,carrier_edge_checks=edge,geometry_correction=geometry)
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
shutil.copyfile(NATIVE/'carrier-edges-before-after.png',OUT/'carrier-edges-before-after.png')
org.ROOT=OUT;org.REPORT=OUT;org.TITLES=[TITLE];org.export_cad()
rows=[]
for p in validation['native_result']['sliced_plates']:
 sec=round(p['total_predication']);rows.append(f"| V{p['id']} | {p['id']} | {sec//3600}h {(sec%3600)//60}m | {sum(f['total_used_g'] for f in p['filaments']):.2f} g |")
readme=f'''# Veneer carrier-edge and acceleration candidate r9

**Status: digitally checked candidate. The reported whole-part shift is not proven resolved. No printer job was sent.**

One current candidate: `{TITLE}.3mf`, A2L/H2S-compatible saved production printer profile, three plates V1/V2/V3. Open as a project. Root `Letter.3mf` remains unchanged, including its core plates and stored slices. This candidate has not replaced the six-plate production baseline.

## Changes and limits

- V1: replace the abrupt 0.15 mm carrier end jog at layers 692–694 with a continuous taper over the adjacent 17.6 mm of the existing carrier edge. Add 1.581 mm³ of material; remove none above numerical tolerance.
- V3: the same correction at its two carrier ends near layers 6–7. Add 1.933 mm³. V2 geometry is unchanged.
- These additions stay within the existing carrier thickness, assembly Z3.2–4.4. Decorative veneer surfaces, connections, rear/web walls, openings and bed bands retain their geometry.
- Bambu ignores the saved per-object default/travel acceleration settings. This candidate applies project-level printing acceleration of 1500 mm/s² and travel acceleration of 2500 mm/s². Explicit outer-wall and top-surface acceleration also cap at 1500; initial-layer travel caps at 2500. Existing first-layer printing acceleration remains 500. All model/support extrusion and travel commands were checked after slicing.
- The exact changed project values are default 6000→1500, outer wall 5000→1500, top surface 2000→1500, travel 8000→2500, and initial-layer travel 6000→2500 mm/s². This is why the candidate isolates the veneers: those settings cannot be reliably limited to their objects inside the shared six-plate Letter project.
- Print/travel speed settings, flow, temperatures, cooling, retraction, material profile, 0.4 mm nozzle, 0.20 mm layers, four walls, five top/bottom layers, Textured PEI, gyroid and solid veneers remain unchanged. Tree supports and the shared 55° lean remain. Bed placement differs only by native serialization below 0.0001 mm.

The original V1 native path shows Y=68.190 mm at its front carrier end throughout the reported band, while the rear end changes Y=251.960→251.810 mm. The user reports a physical shift across both ends and the decorative part. The one-end mesh jog does not explain that whole-part displacement. Neither the acceleration correction nor the geometry correction establishes the physical cause. The support wall's changing finish may respond to speed/cooling/acceleration transitions; that causal link is unconfirmed.

## Verification

Native Bambu Studio 02.08.02.61 sliced all three plates with exit code 0. Saved editable geometry/settings were compared with the native output. Toolpath MD5 checksums passed; extrusion stays within the bed. Model extrusion exists at all 102 previously moved edge connections (30/29/43). No new slice warning was reported; the native project retains only the existing traditional-timelapse compatibility warning if present. These checks do not establish adhesion, restraint, bond strength, removal or appearance.

At V1 layers 691–696, the former abrupt 0.150 mm end jump is reduced to at most 0.002 mm per layer. Through Z134–143, the newly sliced decorative outside path differs from the original by at most 0.0108 mm (V1), 0.0002 mm (V2) and 0.0082 mm (V3); the original decorative geometry is retained. This path comparison includes native seam/rounding effects and does not diagnose the printed displacement.

| Veneer | Plate | Native estimated time | Material including supports |
|---|---:|---:|---:|
{chr(10).join(rows)}

Combined material: **{validation['total_mass_g']:.2f} g**, below the 1000 g requirement. All are full-size veneers; this is not a cropped test. No new physical result exists.

Source `Letter.3mf` SHA-256: `{validation['source_sha256']}`.

Candidate SHA-256: `{sha(target)}`.

The adjacent SCAD/STL files are exact mesh-based snapshots of this candidate. `validation.json` contains native estimates, settings comparisons, command-limit measurements, geometry changes and source hashes. `carrier-edges-before-after.png` plots the measured native carrier-edge paths.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(target,sha(target),flush=True)
