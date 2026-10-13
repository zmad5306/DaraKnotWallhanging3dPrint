"""Publish the audited blue-edge candidate and matching production records."""
import json
import shutil
import zipfile

from validate_print_project import ROOT, PACKAGE, digest


def main(work=None, revision_key='blue_ribbon_edge'):
    work = work or ROOT / '.work/blue-ribbon-edge'
    project = PACKAGE / 'Dara-Photo-Frame-A1-Complete.3mf'
    candidate = work / 'complete.3mf'
    audit = json.loads((work / 'audit.json').read_text())
    base = json.loads((work / 'complete.json').read_text())
    summary = audit['summary']
    assert summary['digital_checks_passed'] and summary['plates'] == 31
    assert audit['project_sha256'] == base['project_sha256'] == digest(candidate)
    assert digest(project) in (base[revision_key]['prior_project_sha256'], digest(candidate))
    assert len(audit['color_modifiers_verified']) == 42
    production = audit['plates'][:29]
    colors = base['settings']['filament_colour']
    base['test_plate']['sliced'] = True
    base['test_plate']['color_modifier_count'] = 2
    for part in base['test_plate']['parts']:
        if part['plate'] == 30:
            part['blue_color_modifier'] = dict(filament=4, z_mm=[12.9, 13.5], width_mm=1.5, flush=True)
    base['bambu_studio_slice'] = dict(
        all_plates_sliced=True, plate_count=31, all_extrusions_within_bed=True,
        **{k: summary[k] for k in ('total_weight_g', 'total_estimated_seconds', 'minimum_edge_clearance_mm',
                                   'extrusion_moves_checked', 'filament_weights_g')},
        production_weight_g=round(sum(p['weight_g'] for p in production), 2),
        production_estimated_seconds=sum(p['estimated_seconds'] for p in production),
        production_filament_weights_g=[round(sum(p['filament_weights_g'][i] if i < len(p['filament_weights_g']) else 0
                                                 for p in production), 2) for i in range(len(colors))],
        validation_note=({'curve_repair':'Locally repaired source curves; ', 'clean_edges':'Complete tangent line/arc artwork rebuild; '}.get(revision_key,'Flush Azurite ribbon edging; '))+
                        'independent geometry, color-height and toolpath audit passed.',
        plates=audit['plates'])
    base['bambu_studio_round_trip'] = dict(normal_meshes_match_source=True, settings_verified=True,
        solid_modifiers_verified=audit['solid_modifiers_verified'], color_modifiers_verified=audit['color_modifiers_verified'],
        comparisons=audit['normal_mesh_comparisons'])
    base['bambu_studio_slice_warnings'] = [{'plate': p['plate'], **n} for p in audit['plates'] for n in p.get('slicer_notices', [])]
    base['ams_color_workflow'].update(
        audit='Passed; matching project SHA256 and all 31 plates in final-review.json.',
        palette=[dict(slot=i+1, color=c, profile=base['settings']['filament_settings_id'][i]) for i, c in enumerate(colors)],
        wood_z_mm=[8.4, 9.9], frame_mixed_layers=[43, 50], blue_mixed_layers=[66, 68],
        blue_toolpath_z_mm=[13.2, 13.4, 13.6],
        frame_filament_changes_by_plate={str(p['plate']): p['filament_changes'] for p in production[:20]},
        production_placements_preserved=True,
        gui_export_note='Explicit links restored for all 32 existing Retainer build instances; IDs match G-code labels.')
    base['blue_ribbon_edge'].update(digital_checks_passed=True, physical_tested=False,
        sample_plate=30, sliced_blue_layers=[66, 68], sliced_blue_z_mm=[13.2, 13.4, 13.6])
    shutil.copy2(candidate, project)
    (PACKAGE / 'project-validation.json').write_text(json.dumps(base, indent=2) + '\n')
    (PACKAGE / 'final-review.json').write_text(json.dumps(audit, indent=2) + '\n')
    (ROOT / 'working/review/blue-ribbon-edge/design.json').write_text(json.dumps(base['blue_ribbon_edge'], indent=2) + '\n')
    checks = ROOT / 'working/stl/Dara-Print-Checks'
    for number in (30, 31):
        record = dict(plate=number, pieces=1, source_cad_sha256=audit['source_sha256'], project_sha256=audit['project_sha256'],
                      parts=[p for p in base['test_plate']['parts'] if p['plate'] == number],
                      plate_layout=base['plate_layout'][number-1], sliced=True, audit=audit['plates'][number-1])
        (checks / f'plate-{number}-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    with zipfile.ZipFile(candidate) as archive:
        for number, filename in ((30, 'fit-test-plate.png'), (31, 'copper-test-plate.png')):
            (PACKAGE / filename).write_bytes(archive.read(f'Metadata/plate_{number}.png'))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
