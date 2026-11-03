import sys, json, shutil, zipfile, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_print_project import digest
W = ROOT / '.work/weave-restore'
P = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
C = ROOT / 'working/stl/Dara-Print-Checks'
a = json.loads((W/'audit-v2.json').read_text())
b = json.loads((W/'complete-v2.json').read_text())
s = a['summary']
assert s['digital_checks_passed'] and s['plates'] == 31
assert a['project_sha256'] == b['project_sha256'] == digest(W/'complete-v2.3mf')
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
    validation_note='Current relief and separate tests re-sliced; independent audit passed.', plates=a['plates'])
b['bambu_studio_round_trip'] = dict(normal_meshes_match_source=True, settings_verified=True,
    solid_modifiers_verified=a['solid_modifiers_verified'], color_modifiers_verified=a['color_modifiers_verified'],
    comparisons=a['normal_mesh_comparisons'])
b['bambu_studio_slice_warnings'] = [{'plate': p['plate'], **n} for p in a['plates'] for n in p.get('slicer_notices',[])]
b['ams_color_workflow'].update(audit='Passed; matching project SHA256 and all 31 plates in final-review.json.',
    palette=[dict(slot=i+1,color=c,profile=p) for i,c,p in zip(range(3),['#FFFFFF','#C2AB84','#B87333'],['Generic PLA @BBL A1','Generic PLA @BBL A1','Generic PLA Silk @BBL A1'])],
    wood_z_mm=[8.4,9.9], frame_mixed_layers=[43,50], frame_filament_changes_per_plate=8,
    production_placements_preserved=True,
    gui_export_note='Explicit links restored for all 32 existing Retainer build instances; IDs match G-code labels.')
b['weave_restoration']['geometry_verification'] = 'working/review/weave-restoration/geometry-verification.json'
b['weave_restoration']['physical_test_status'] = 'Earlier hardware/lap tests already printed per user; results not reported. Restored weave and separate copper tests are pending.'
shutil.copy2(W/'complete-v2.3mf', P/'Dara-Photo-Frame-A1-Complete.3mf')
(P/'project-validation.json').write_text(json.dumps(b,indent=2)+'\n')
(P/'final-review.json').write_text(json.dumps(a,indent=2)+'\n')
for plate in (30,31):
    report = dict(plate=plate, pieces=1, source_cad_sha256=a['source_sha256'], project_sha256=a['project_sha256'],
        parts=[p for p in b['test_plate']['parts'] if p['plate']==plate],
        plate_layout=b['plate_layout'][plate-1], sliced=True, audit=a['plates'][plate-1])
    (C/f'plate-{plate}-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
with zipfile.ZipFile(W/'complete-v2.3mf') as z:
    for n in (30,31):
        filename=f'Metadata/plate_{n}.png'
        assert filename in z.namelist(), filename
        (P/('fit-test-plate.png' if n==30 else 'copper-test-plate.png')).write_bytes(z.read(filename))
white, wood, copper=s['filament_weights_g']
t30,t31=a['plates'][29:]
(P/'README.md').write_text(f'''# Complete A1 print project

[Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf) contains 70 production pieces on plates 1-29 and two separate material tests on plates 30-31: **72 pieces on 31 plates**. The previously printed hardware and lap coupons have been removed from the project; their STL files remain available.

The project includes editable models, local infill and color modifiers, thumbnails, and sliced toolpaths. Use Git LFS to retrieve it after cloning. If Bambu Studio asks to regenerate Preview when opening the editable file, use **Slice all** with its saved settings.

| Plates | Contents |
| --- | --- |
| 01-20 | F1-F20, one frame section per plate |
| 21-26 | M1-M6, one copper letter section per plate |
| 27 | Backer1, Backer3, Backer5, Backer7 |
| 28 | Backer2, Backer4, Backer6, Backer8 |
| 29 | B1-B4 and 32 retainers |
| 30 | One short white/wood weave sample |
| 31 | One copper Test-M-Letter sample |

The [four-page part and plate map](../../../output/pdf/Dara-Part-and-Plate-Map.pdf) still describes the unchanged production assignments. See the [test guide](../../stl/Dara-Print-Checks/README.md) for the two material tests.

## Restored weave

F1-F20 and the short F7 sample now include the older alternating crossing detail: **3.3 x 1.5 mm crossing pads raised 0.3 mm above the 0.6 mm thread grid**, on a 6 mm pitch. Adjacent crossings alternate direction. The native CAD, embedded preview meshes, STL exports, and sliced project agree. Frame joints, rails, hardware interfaces, and production plate placements retain their dimensions.

Wood modifiers follow the recessed backing, threads, and raised crossings at Z=8.4-9.9 mm. They no longer fill the relief with a flat prism in model view. Wood prints in place on layers **43-50**, with **eight filament changes** per frame or weave-test plate. Keep these modifiers when editing; plain STL files do not retain color assignments.

[Geometry comparison](../../review/weave-restoration/texture-comparison.png) and [geometry verification](../../review/weave-restoration/geometry-verification.json) document the restoration. Only the crossing relief was added to the frame bodies, within numerical tolerances.

## Saved print settings

- Bambu Lab A1, 0.4 mm nozzle, textured PEI plate, 0.2 mm layers, four walls, 15% gyroid.
- Filament 1: white `#FFFFFF`, Generic PLA; filament 2: wood tan `#C2AB84`, ordinary Generic PLA; filament 3: copper `#B87333`, Generic PLA Silk.
- Match those colors to the actual AMS Lite spools in the print dialog.
- Nozzle 220 C. White/wood plates use a 65 C bed; copper plates, including plate 31, use 55 C throughout printing.
- Copper outer walls and top surfaces run at 40 mm/s. Copper maximum volumetric speed is 7.5 mm3/s; white/wood use 12 mm3/s.
- 74 local 100% infill modifiers: 73 production screw/keyhole zones and the copper test screw zone. Lap tongues and roots use the normal body settings.
- Original rear-down orientations and 100% scale are retained. Backers print four per plate, by layer, without supports or brim. Tight frame/M plates retain their 1 mm brim and zero extra support-base expansion.
- Prime towers remain clear of the pieces. Flushing into objects, infill, and supports is disabled.

All 31 plates finished slicing in Bambu Studio 02.08.02.61. The independent audit checked {s['extrusion_moves_checked']:,} extrusion moves including bead widths, brims, support, and towers. Minimum bed-edge clearance is **{s['minimum_edge_clearance_mm']:.3f} mm**. The only slicer notices concern unsupported traditional timelapse on the single-color plates; leave timelapse off for those plates.

| Material | All 31 plates, including support and purge/towers |
| --- | ---: |
| White | {white:.2f} g |
| Wood tan | {wood:.2f} g |
| Copper silk | {copper:.2f} g |

Production plates 1-29: **{wt(prod):,.2f} g; {duration(sec(prod))}**. Plate 30: **{t30['weight_g']:.2f} g; {duration(t30['estimated_seconds'])}**. Plate 31: **{t31['weight_g']:.2f} g; {duration(t31['estimated_seconds'])}**. Total: **{s['total_weight_g']:,.2f} g; {duration(s['total_estimated_seconds'])}**. These are slicer estimates.

[project-validation.json](project-validation.json) records the final hash, source hashes, quantities, plate positions, settings, and slice estimates. [final-review.json](final-review.json) independently verifies the geometry, 74 reinforcement modifiers, 21 wood modifiers, filament assignments, and saved toolpaths. All 41 normal meshes match their source STLs within 0.0001 mm. [PRINT-READINESS.md](PRINT-READINESS.md) retains the hardware and assembly guide.

## Rebuilding and checking

The initial generation scripts build the production project and historical hardware-test workflow. For this revision, export native CAD with `scripts/export_jointed_stls.py`, then stage from the preceding ten-test AMS project and its matching report:

```powershell
python scripts/restore_weave_project.py --source path/to/prior-project.3mf --baseline path/to/prior-project-validation.json --refresh-preview-cache
```

This writes `.work/weave-restore/restored.3mf` and `staged.json`. Open the candidate in Bambu Studio, **Slice all**, **Save Project As** an editable models file, and **Export all sliced file** from the same unchanged project. Combine and audit before publishing:

```powershell
python scripts/combine_ams_slices.py --models path/to/models.3mf --slices path/to/models.gcode.3mf --baseline .work/weave-restore/staged.json --output .work/weave-restore/complete.3mf
python scripts/validate_print_project.py --project .work/weave-restore/complete.3mf --baseline .work/weave-restore/complete.json --report .work/weave-restore/audit.json
```

To audit the published artifacts without changing the project:

```powershell
python -m unittest discover -s scripts -p test_validate_print_project.py
python scripts/validate_print_project.py
```
''')
old=(P/'PRINT-READINESS.md').read_text()
assembly=old[old.index('## Assembly supplies and order'):]
(P/'PRINT-READINESS.md').write_text(f'''# Print review - 2026-10-12

**The revised project passes the digital audit.** The user has already printed the earlier hardware and lap tests; their fit results have not been reported. This revision restores the weave crossing relief and separates the remaining material tests.

Use [Dara-Photo-Frame-A1-Complete.3mf](Dara-Photo-Frame-A1-Complete.3mf). Plate **30** contains only the **68.45 x 24 x 13.5 mm** white/wood sample from F7. Plate **31** contains only **Test-M-Letter**, with the copper Generic PLA Silk profile and 55 C bed. No need to reprint the removed hardware coupons for this cleanup.

The native frame geometry has alternating 0.3 mm raised crossing pads. Joints, rails, screws, locators, wall keys, and production placements retain their dimensions. A comparison against the previous meshes verifies that the crossing relief is the only geometric addition, within 0.02 mm3 boolean tolerance per check. The M and accessory STL files are byte-identical to the previous files.

## Saved-file checks

- All 39 production STLs and two test meshes are valid solids; the current CAD hash and STL hashes match their manifests.
- All 70 production pieces were checked in their assembled positions, including lap order and mating interfaces.
- All 41 normal meshes in the 3MF match their source geometry within 0.0001 mm. The 74 reinforcement modifiers and 21 wood modifiers were checked.
- Wood occupies layers 43-50 on the frame and short test, with eight color changes per plate. Plate 31 uses copper only, with no filament changes and a 55 C bed throughout printing; plate 30 uses a 65 C bed.
- All 31 saved toolpaths pass the extrusion-bounds audit: {s['extrusion_moves_checked']:,} checked moves and {s['minimum_edge_clearance_mm']:.3f} mm minimum bed-edge clearance. Printer purge/wipe/parking routines are outside that model-path check.
- Estimated production use: {wt(prod):,.2f} g and {duration(sec(prod))}. Weave test: {t30['weight_g']:.2f} g and {duration(t30['estimated_seconds'])}. Copper test: {t31['weight_g']:.2f} g and {duration(t31['estimated_seconds'])}.

The matching report is [final-review.json](final-review.json). Inspect the weave sample for crossing detail, white/wood boundaries, and surface finish. The separate copper sample checks the silk finish using the same settings as the M plates. The digital review does not record physical print results for these revised samples.

'''+assembly)
(C/'README.md').write_text(f'''# Separate weave and copper tests

Open the [complete Bambu project](../../bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf). The previously printed hardware/lap coupons have been removed from the plate layout. Their standalone STL files are retained here.

| Plate | Piece | Materials and settings | Estimate |
| --- | --- | --- | --- |
| 30 | Test-Weave-Full-Width | White/wood Generic PLA; 65 C bed | {t30['weight_g']:.2f} g; {duration(t30['estimated_seconds'])} |
| 31 | Test-M-Letter | Copper Generic PLA Silk; 55 C bed | {t31['weight_g']:.2f} g; {duration(t31['estimated_seconds'])} |

Both use the A1, 0.4 mm nozzle, 0.2 mm layers, four walls, and 15% gyroid. Copper retains its local solid screw zone, silk flow/retraction settings, and 40 mm/s outer-wall/top-surface speeds. It prints with zero filament changes on its own plate.

The weave coupon is **68.45 mm wide x 24 mm long x 13.5 mm high**, cropped from the restored F7 mesh. Both white side rails remain intact; only the short ends are cut. The recessed backing and raised threads include the alternating **3.3 x 1.5 x 0.3 mm crossing pads**. Wood is assigned at Z=8.4-9.9 mm, layers 43-50, with eight color changes. Inspect the actual texture and white/wood boundary in Preview's Filament view and on the printed sample.

![Short weave test on plate 30](../../bambu/Dara-Photo-Frame-A1-Jointed/fit-test-plate.png)

![Copper test on plate 31](../../bambu/Dara-Photo-Frame-A1-Jointed/copper-test-plate.png)

The model thumbnails use the base color for filament modifiers; sliced Filament Preview shows the final wood assignment. [Plate 30 manifest](plate-30-manifest.json) and [plate 31 manifest](plate-31-manifest.json) record source hashes, placements, and audited slice results. The standalone [weave STL](Test-Weave-Full-Width.stl) has no color settings; use the complete 3MF for the two-color test.

## Previously printed fit coupons

The photo, B1 wall-block/socket, M interface pair, and F7/F4 lap pair remain as standalone STL files for reference. Earlier fit-sample exports and their [manifest](manifest.json) retain their original source hash. They are not part of the current 31-plate layout. The user reports these tests were already printed; fit results are not recorded here.

Test-M-Letter on plate 31 remains the original crop of M5, including its screw stack and locating holes. For any repeated fit check, use its retained Test-M-Frame mate, a selected #6-19 x 1/2-inch plastic thread-forming screw, and a 10 mm OD x 4 mm ID x 1 mm washer. The outside cropped edges are sample boundaries, not mating features.
''')
stlread=ROOT/'working/stl/Dara-Photo-Frame-A1-Jointed/README.md'
text=stlread.read_text()
needle='These are binary STL files in **millimetres**.'
text=text.replace(needle, needle+' The frame exports include restored alternating\n3.3 x 1.5 mm crossing pads, 0.3 mm above the thread grid. The joints and\nhardware interfaces retain their dimensions; M and accessory STLs are unchanged.')
stlread.write_text(text)
print(json.dumps(s,indent=2))
