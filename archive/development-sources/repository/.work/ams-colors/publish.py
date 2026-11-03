"""Publish only the independently audited AMS candidate; refresh its reports."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / '.work/ams-colors'
PACKAGE = ROOT / 'working/bambu/Dara-Photo-Frame-A1-Jointed'
TESTS = ROOT / 'working/stl/Dara-Print-Checks'
candidate = STAGE / 'complete-ams.3mf'
audit = json.loads((STAGE / 'final-audit.json').read_text())
baseline = json.loads((STAGE / 'complete-ams.json').read_text())
assert audit['summary']['digital_checks_passed']
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == audit['project_sha256'] == baseline['project_sha256']

def props(el):
    return {m.get('key'): m.get('value') for m in el.findall('metadata')}

with zipfile.ZipFile(candidate) as z:
    model = ET.fromstring(z.read('Metadata/model_settings.config'))
    settings = json.loads(z.read('Metadata/project_settings.config'))
    names = {o.get('id'): props(o)['name'] for o in model.findall('object')}
    for layout, plate in zip(baseline['plate_layout'], model.findall('plate')):
        remaining = list(plate.findall('model_instance'))
        for item in layout['items']:
            inst = next(i for i in remaining if names[props(i)['object_id']] == item['name'])
            remaining.remove(inst)
            item.update({k: int(props(inst)[k]) for k in ('object_id', 'instance_id', 'identify_id')})
        assert not remaining
    thumbnail = z.read('Metadata/plate_30.png')

summary = audit['summary']
plates = audit['plates']
production = plates[:-1]
test = plates[-1]
def duration(seconds):
    return f'{seconds // 3600} h {(seconds % 3600) // 60} min'
def total_weights(rows):
    return [round(sum(p['filament_weights_g'][i] if i < len(p['filament_weights_g']) else 0 for p in rows), 2) for i in range(3)]
prod_weight = round(sum(p['weight_g'] for p in production), 2)
prod_seconds = sum(p['estimated_seconds'] for p in production)
notices = [{'plate': p['plate'], **w} for p in plates for w in p['slicer_notices']]
assert all(w['msg'] == 'not_support_traditional_timelapse' for w in notices)
assert {w['plate'] for w in notices} == set(range(21, 30))
baseline['bambu_studio_slice'] = {
    'all_plates_sliced': True, 'plate_count': 30, 'all_extrusions_within_bed': True,
    **{k: summary[k] for k in ['total_weight_g', 'total_estimated_seconds', 'minimum_edge_clearance_mm', 'extrusion_moves_checked', 'filament_weights_g']},
    'production_weight_g': prod_weight, 'production_estimated_seconds': prod_seconds,
    'production_filament_weights_g': total_weights(production),
    'validation_note': 'All 30 plates re-sliced in Bambu Studio 02.08.02.61 for white/wood/copper. Full geometry, color, quantity, and extrusion-bounds audit passed. Printer custom routines excluded from bounds checks.',
    'plates': plates}
baseline['bambu_studio_round_trip'] = {
    'normal_meshes_match_source': True, 'settings_verified': True,
    'solid_modifiers_verified': audit['solid_modifiers_verified'],
    'color_modifiers_verified': audit['color_modifiers_verified'],
    'normal_mesh_comparisons': audit['normal_mesh_comparisons']}
baseline['bambu_studio_slice_warnings'] = notices
baseline['bambu_studio_version'] = '02.08.02.61'
baseline['settings'].update({k: settings[k] for k in [
    'nozzle_temperature', 'nozzle_temperature_initial_layer', 'textured_plate_temp',
    'filament_max_volumetric_speed', 'filament_retraction_length', 'enable_prime_tower',
    'flush_into_infill', 'flush_into_support', 'flush_into_objects', 'flush_volumes_matrix']})
baseline['ams_color_workflow'].update({
    'audit': 'Passed; see final-review.json for the matching SHA256 and all 30 plate results.',
    'palette': [{'slot': i + 1, 'color': color, 'profile': profile} for i, (color, profile) in enumerate(zip(settings['filament_colour'], settings['filament_settings_id']))],
    'wood_z_mm': [8.4, 9.6], 'frame_mixed_layers': [43, 48],
    'frame_filament_changes_per_plate': 6,
    'reinforcing_glued_weave_inserts': False,
    'original_meshes_and_placements_preserved': True,
    'gui_export_note': 'Restored explicit plate links for all 32 existing Retainer build instances; IDs match the sliced G-code labels.'})
test_record = baseline['test_plate']
test_record.pop('production_gcodes_byte_identical', None)
test_record.update(slice_summary=test, sliced=True, slicer_warnings=test['slicer_notices'],
                   plate_layout=copy.deepcopy(baseline['plate_layout'][-1]),
                   current_project_sha256=audit['project_sha256'],
                   source_project_note='source_project_sha256 identifies the historical project used to generate these unchanged coupons.',
                   filament_assignment={'Test-M-Letter': 3, 'other_test_pieces': 1})
# GUI reload is recorded only after observing the published file in Bambu.
test_record.pop('bambu_reload_verified', None)

def replace(path, old, new):
    text = path.read_text()
    assert old in text, (path, old)
    path.write_text(text.replace(old, new), encoding='utf-8')

readme = PACKAGE / 'README.md'
text = readme.read_text()
start = text.index('The supplied project was sliced')
end = text.index('\n[project-validation.json]', start)
table = '\n'.join(f'| {name} | {mass:.2f} g |' for name, mass in zip(['White', 'Wood tan', 'Copper silk'], summary['filament_weights_g']))
text = text[:start] + f'''The supplied project was sliced in Bambu Studio 02.08.02.61. All 30 plates
finished. Extrusion paths, including support, brim, and prime-tower bead widths,
stay inside the 256 mm bed. The minimum checked edge clearance is
{summary['minimum_edge_clearance_mm']:.3f} mm on plate 06. Plates 21-29 carry only the slicer's
`not_support_traditional_timelapse` notices; leave timelapse off when printing
those plates. No other slice notices were recorded.

| Filament | All 30 plates, including fit tests and purge/towers |
| --- | ---: |
{table}

Production plates 1-29 total **{prod_weight:.2f} g and {duration(prod_seconds)}**.
Plate 30 adds **{test['weight_g']:.2f} g and {duration(test['estimated_seconds'])}**.
Combined: **{summary['total_weight_g']:.2f} g and {duration(summary['total_estimated_seconds'])}**.
These are slicer estimates; small rounding differences from the GUI total are
normal. The planned stock of 3.5 kg white, 1 kg wood, and 1 kg copper covers this
slice, leaving approximately {3.5-summary['filament_weights_g'][0]/1000:.3f} kg white,
{1-summary['filament_weights_g'][1]/1000:.3f} kg wood, and
{1-summary['filament_weights_g'][2]/1000:.3f} kg copper for calibration and retries.
''' + text[end:]
readme.write_text(text, encoding='utf-8')

ready = PACKAGE / 'PRINT-READINESS.md'
replace(ready, 'Bambu Lab A1, 0.4 mm nozzle, Generic PLA, textured PEI plate, 0.2 mm layers,',
        'Bambu Lab A1, 0.4 mm nozzle, white/wood Generic PLA and copper Generic PLA Silk,\ntextured PEI plate, 0.2 mm layers,')
replace(ready, 'the nine fit-test pieces. Production plates 1-29 retain their original models,\nsettings and byte-identical G-code.',
        'the nine fit-test pieces. All printable geometry, joint fits, and placements\nare unchanged. All 30 plates were re-sliced with the saved AMS colors. Match\n1 white, 2 wood, and 3 copper to the actual loaded spools in the print dialog.')
replace(ready, 'All instance placements and 82 solid modifiers were checked; each modifier\n  intersects its intended printable part.',
        'All instance placements, 82 solid modifiers, and 20 weave-color modifiers\n  were checked; each modifier intersects its intended printable part. Wood is\n  confined to layers 43-48 on every frame plate, with six changes per plate.\n  All M sections use copper; backers and hardware use white.')
replace(ready, 'including the 7,058,670\n  production moves and the added test plate, including compact',
        f'including {summary["extrusion_moves_checked"]:,}\n  moves across production and test plates, including compact')
start = ready.read_text().index('- Estimated production use remains')
text = ready.read_text()
end = text.index('- The four-page', start)
text = text[:start] + f'''- Estimated production use is **{prod_weight:,.2f} g and {duration(prod_seconds)}**.
  The included plate 30 adds **{test['weight_g']:.2f} g and {duration(test['estimated_seconds'])}**.
  All 30 plates use approximately **{summary['filament_weights_g'][0]/1000:.3f} kg white,
  {summary['filament_weights_g'][1]/1000:.3f} kg wood, and {summary['filament_weights_g'][2]/1000:.3f} kg copper**,
  including the slicer's support, brim, purge and tower estimates.
- The only slice notices concern unsupported traditional timelapse on plates
  21-29. Leave timelapse off for those single-color plates.
''' + text[end:]
text = text.replace('with five regression\ntests.', 'with six regression\ntests, including multi-filament weight accounting.')
text = text.replace("original project's slice summary has also been refreshed.", 'color project\'s slice summary has also been refreshed.')
ready.write_text(text, encoding='utf-8')

replace(TESTS / 'README.md', 'Estimated use is **160.18 g and 5 h 30 min**. Production plates 1-29 are unchanged.',
        f"Estimated use is **{test['weight_g']:.2f} g and {duration(test['estimated_seconds'])}**.\nTest-M-Letter prints in copper / Generic PLA Silk; the other eight pieces print\nin white / Generic PLA. This plate has {test['filament_changes']} filament changes. Its geometry\nand placements are unchanged; it has been re-sliced for the production palette.")
replace(TESTS / 'README.md', '3.254 kg production estimate.', f'{prod_weight/1000:.3f} kg production estimate.')

shutil.copyfile(candidate, PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf')
for path, data in [(PACKAGE / 'project-validation.json', baseline),
                   (PACKAGE / 'final-review.json', audit),
                   (TESTS / 'plate-30-manifest.json', test_record)]:
    path.write_text(json.dumps(data, indent=2) + '\n')
(PACKAGE / 'fit-test-plate.png').write_bytes(thumbnail)
print(json.dumps({'summary': summary, 'production_weight_g': prod_weight,
                  'production_seconds': prod_seconds, 'test': {k:test[k] for k in ['weight_g','estimated_seconds','filament_changes']}}, indent=2))
