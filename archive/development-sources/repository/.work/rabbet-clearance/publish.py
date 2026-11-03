import sys, json, shutil, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from validate_print_project import digest
W = ROOT/'.work/rabbet-clearance'
P = ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed'
C = ROOT/'working/stl/Dara-Print-Checks'
a = json.loads((W/'audit.json').read_text())
b = json.loads((W/'complete.json').read_text())
old = json.loads((W/'baseline.json').read_text())
geometry = json.loads((ROOT/'working/review/rabbet-clearance/geometry-verification.json').read_text())
s = a['summary']
assert s['digital_checks_passed'] and s['plates'] == 31
assert a['project_sha256'] == b['project_sha256'] == digest(W/'complete.3mf')
assert geometry['all_passed'] and geometry['source_sha256'] == a['source_sha256']
prod = a['plates'][:29]
def wt(rows): return round(sum(x['weight_g'] for x in rows), 2)
def sec(rows): return sum(x['estimated_seconds'] for x in rows)
def duration(n): return f'{n//3600} h {(n%3600)//60} min'
b['test_plate']['sliced'] = True
b['bambu_studio_slice'] = dict(all_plates_sliced=True, plate_count=31, all_extrusions_within_bed=True,
    total_weight_g=s['total_weight_g'], total_estimated_seconds=s['total_estimated_seconds'],
    minimum_edge_clearance_mm=s['minimum_edge_clearance_mm'], extrusion_moves_checked=s['extrusion_moves_checked'],
    filament_weights_g=s['filament_weights_g'], production_weight_g=wt(prod), production_estimated_seconds=sec(prod),
    production_filament_weights_g=[round(sum(p['filament_weights_g'][i] if i<len(p['filament_weights_g']) else 0 for p in prod),2) for i in range(3)],
    validation_note='2.4 mm rabbets re-sliced; separate material tests and restored weave preserved; independent audit passed.', plates=a['plates'])
b['bambu_studio_round_trip'] = dict(normal_meshes_match_source=True, settings_verified=True,
    solid_modifiers_verified=a['solid_modifiers_verified'], color_modifiers_verified=a['color_modifiers_verified'],
    comparisons=a['normal_mesh_comparisons'])
b['bambu_studio_slice_warnings'] = [{'plate': p['plate'], **n} for p in a['plates'] for n in p.get('slicer_notices',[])]
b['ams_color_workflow'].update(audit='Passed; matching project SHA256 and all 31 plates in final-review.json.',
    palette=[dict(slot=i+1,color=c,profile=p) for i,c,p in zip(range(3),['#FFFFFF','#C2AB84','#B87333'],['Generic PLA @BBL A1','Generic PLA @BBL A1','Generic PLA Silk @BBL A1'])],
    wood_z_mm=[8.4,9.9], frame_mixed_layers=[43,50], frame_filament_changes_per_plate=8,
    production_placements_preserved=True,
    gui_export_note='Explicit links restored for all 32 existing Retainer build instances; IDs match G-code labels.')
b['weave_restoration']['physical_test_status'] = 'Earlier hardware/lap tests printed per user. User reports insufficient photo clearance in the former 2.0 mm rabbet. Revised 2.4 mm rabbet, restored weave and copper tests await physical checks.'
b['rabbet_revision'].update(digital_geometry_checks_passed=True, physical_fit_verified=False,
    revised_photo_fit_stl='working/stl/Dara-Print-Checks/Test-Photo-Frame.stl')
shutil.copy2(W/'complete.3mf', P/'Dara-Photo-Frame-A1-Complete.3mf')
(P/'project-validation.json').write_text(json.dumps(b,indent=2)+'\n')
(P/'final-review.json').write_text(json.dumps(a,indent=2)+'\n')
for plate in (30,31):
    report = dict(plate=plate, pieces=1, source_cad_sha256=a['source_sha256'], project_sha256=a['project_sha256'],
        parts=[p for p in b['test_plate']['parts'] if p['plate']==plate],
        plate_layout=b['plate_layout'][plate-1], sliced=True, audit=a['plates'][plate-1])
    (C/f'plate-{plate}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
with zipfile.ZipFile(W/'complete.3mf') as z:
    for n in (30,31):
        (P/('fit-test-plate.png' if n==30 else 'copper-test-plate.png')).write_bytes(z.read(f'Metadata/plate_{n}.png'))

# Refresh previously documented estimates to the values in the new audit.
previous = old['bambu_studio_slice']
replacements = {
    f"{previous['extrusion_moves_checked']:,}": f"{s['extrusion_moves_checked']:,}",
    f"{previous['minimum_edge_clearance_mm']:.3f}": f"{s['minimum_edge_clearance_mm']:.3f}",
    f"{previous['production_weight_g']:,.2f}": f"{wt(prod):,.2f}",
    duration(previous['production_estimated_seconds']): duration(sec(prod)),
    f"{previous['total_weight_g']:,.2f}": f"{s['total_weight_g']:,.2f}",
    duration(previous['total_estimated_seconds']): duration(s['total_estimated_seconds']),
}
for was, now in zip(previous['filament_weights_g'], s['filament_weights_g']):
    replacements[f'{was:.2f} g'] = f'{now:.2f} g'
for was, now in zip(previous['plates'][29:], a['plates'][29:]):
    replacements[f"{was['weight_g']:.2f} g; {duration(was['estimated_seconds'])}"] = f"{now['weight_g']:.2f} g; {duration(now['estimated_seconds'])}"
    replacements[f"{was['weight_g']:.2f} g and {duration(was['estimated_seconds'])}"] = f"{now['weight_g']:.2f} g and {duration(now['estimated_seconds'])}"
for path in (P/'README.md', P/'PRINT-READINESS.md', C/'README.md'):
    text = path.read_text()
    for was, now in replacements.items(): text = text.replace(was, now)
    path.write_text(text)

path=P/'README.md'
text=path.read_text()
text=text.replace('## Restored weave', '''## Photo rabbet clearance

All photo rabbets are now **2.4 mm deep**, increased from 2.0 mm after the printed backer left insufficient room for the photo. The backer remains **1.6 mm** thick, leaving **0.8 mm total for the photo and surface clearance**: the original 0.4 mm photo allowance plus 0.4 mm to accommodate supported-surface roughness.

The native CAD, preview cache, F1-F20 STLs, and sliced project use the deeper recess. [Geometry verification](../../review/rabbet-clearance/geometry-verification.json) checks every frame section and confirms that the revision only removes material in the 2.0-2.4 mm rabbet depth band. The restored weave, joints, screws, tabs, and other parts retain their geometry. The [optional photo-frame coupon](../../stl/Dara-Print-Checks/Test-Photo-Frame.stl) is updated separately; plates 30 and 31 retain only their material tests. The new physical fit has not yet been checked.

## Restored weave''')
text=text.replace('Frame joints, rails, hardware interfaces, and production plate placements retain their dimensions.', 'Frame joints, hardware interfaces, and production plate placements retain their dimensions. The rear photo rabbet has the additional clearance described above.')
text=text.replace('Only the crossing relief was added to the frame bodies, within numerical tolerances.', 'Those reports describe the preceding weave-only revision; the separate rabbet report above records this subsequent clearance change.')
start=text.index('The initial generation scripts')
end=text.index('To audit the published artifacts', start)
text=text[:start]+'''Save the preceding 31-plate project, its validation report, and original production STLs under `.work/rabbet-clearance/` as `baseline.3mf`, `baseline.json`, and `original-stls/`. Export the revised native CAD, then stage and compare:

```powershell
python scripts/export_jointed_stls.py
python scripts/refresh_rabbet_project.py
python scripts/check_rabbet_clearance.py
```

The staging script refreshes the embedded preview cache, affected model meshes, and photo-fit STL. Open `.work/rabbet-clearance/deeper-rabbet.3mf` in Bambu Studio, **Slice all**, **Save Project As** `.work/rabbet-clearance/models.3mf`, and **Export all sliced file** to `.work/rabbet-clearance/models.gcode.3mf` from the same project. Combine and audit before publishing:

```powershell
python scripts/combine_ams_slices.py --models .work/rabbet-clearance/models.3mf --slices .work/rabbet-clearance/models.gcode.3mf --baseline .work/rabbet-clearance/staged.json --output .work/rabbet-clearance/complete.3mf
python scripts/validate_print_project.py --project .work/rabbet-clearance/complete.3mf --baseline .work/rabbet-clearance/complete.json --report .work/rabbet-clearance/audit.json
```

'''+text[end:]
path.write_text(text)

path=P/'PRINT-READINESS.md'
text=path.read_text()
text=text.replace('The user has already printed the earlier hardware and lap tests; their fit results have not been reported. This revision restores the weave crossing relief and separates the remaining material tests.', 'The user has printed the earlier hardware and lap tests and reports that the backer left insufficient photo room, possibly due to support roughness. This revision deepens the rabbet from **2.0 to 2.4 mm**. With the existing 1.6 mm backer, 0.8 mm remains for the photo and surface clearance. Physical fit of this revision is still unverified.')
text=text.replace('No need to reprint the removed hardware coupons for this cleanup.', 'The optional standalone [photo-frame fit coupon](../../stl/Dara-Print-Checks/Test-Photo-Frame.stl) also has the deeper recess; the material test plates remain unchanged in purpose.')
start=text.index('The native frame geometry has')
end=text.index('## Saved-file checks',start)
text=text[:start]+'''The alternating 0.3 mm weave crossing pads are preserved. The [rabbet comparison](../../review/rabbet-clearance/geometry-verification.json) verifies all 20 frame sections: only the recess depth changes, with geometry outside Z=2.0-2.4 mm unchanged within numerical tolerance. The M, backer, wall-block and retainer STL files are byte-identical to the preceding revision. Production placements and saved material settings are retained.

'''+text[end:]
path.write_text(text)

path=C/'README.md'
text=path.read_text().replace('Earlier fit-sample exports and their [manifest](manifest.json) retain their original source hash. They are not part of the current 31-plate layout. The user reports these tests were already printed; fit results are not recorded here.', 'The user reports insufficient photo room with the former 2.0 mm recess, possibly due to support roughness. [Test-Photo-Frame.stl](Test-Photo-Frame.stl) and [Photo-Fit-Sample.stl](Photo-Fit-Sample.stl) now use a **2.4 mm rabbet**, leaving 0.8 mm beyond the existing 1.6 mm backer. The backer and tab samples retain their dimensions. The revised physical fit is unverified. Other archived coupons retain their earlier geometry; the [manifest](manifest.json) records per-file source hashes. These fit coupons are not added to the current 31-plate layout.')
path.write_text(text)

path=ROOT/'working/stl/Dara-Photo-Frame-A1-Jointed/README.md'
text=path.read_text().replace('hardware interfaces retain their dimensions; M and accessory STLs are unchanged.', 'hardware interfaces retain their dimensions; M and accessory STLs are unchanged.\nPhoto rabbets are now 2.4 mm deep, leaving 0.8 mm for a photo and surface\nclearance beyond the existing 1.6 mm backer. This adds 0.4 mm to accommodate\nthe reported clearance issue and possible support roughness.')
path.write_text(text)

path=ROOT/'README.md'
text=path.read_text().replace('test pieces; their results have not been recorded here.', 'test pieces and reported insufficient photo clearance. The jointed model now\nhas 2.4 mm deep rabbets, giving the 1.6 mm backer 0.8 mm of photo and surface\nclearance. The extra 0.4 mm addresses the reported fit issue; the revised\nphysical fit has not yet been checked.')
path.write_text(text)
print(json.dumps(s,indent=2))
