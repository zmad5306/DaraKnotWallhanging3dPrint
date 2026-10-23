"""Install validated wall-cradle plates and synchronize release evidence."""
import copy,json,shutil
from promote_veneer_wall_cradle import *
CORRECTION_GEOMETRY=None


def baseline_json(name):return json.loads((BASE/OUT.relative_to(ROOT)/name).read_text())


def install():
    proof=json.loads((WORK/'veneer-wall-promotion-validation.json').read_text())
    kept=json.loads((WORK/'veneer-wall-unchanged-plates.json').read_text())
    assert proof['project_sha256']==sha(NATIVE/'sliced.3mf')
    assert proof['editable_sha256']==sha(EDIT)
    assert proof['total_veneer_and_support_g']<1000
    reopen=json.loads((WORK/'reopen/result.json').read_text())
    assert reopen['return_code']==0
    assert json.loads((WORK/'reopen/input.json').read_text())['project_sha256']==proof['project_sha256']
    assert sha(ROOT/'Dara.3mf') in [EXPECTED_SOURCE,proof['project_sha256']]
    for name,h in kept['protected_external_file_sha256'].items():assert sha(ROOT/name)==h
    for source,target in [(EDIT,OUT/'Dara-A2L-Editable.3mf'),(NATIVE/'sliced.3mf',OUT/'Dara-A2L-Complete.3mf'),(NATIVE/'sliced.3mf',ROOT/'Dara.3mf')]:
        shutil.copyfile(source,target)
    if CORRECTION_GEOMETRY is not None:
        shutil.copyfile(BASE/OUT.relative_to(ROOT)/'veneer-wall-unchanged-plates.json',OUT/'veneer-wall-r5-unchanged-plates.json')
        shutil.copyfile(BASE/OUT.relative_to(ROOT)/'veneer-wall-promotion-validation.json',OUT/'veneer-wall-r5-promotion-validation.json')
    for name in ['veneer-wall-promotion-validation.json','veneer-wall-unchanged-plates.json','native-validation.json']:
        shutil.copyfile(WORK/name,OUT/name)
    if CORRECTION_GEOMETRY is None:
        shutil.copyfile(REVIEW/'validation.json',OUT/'veneer-wall-reviewed-r5.json')
        shutil.copyfile(REVIEW/'growth-connectivity.json',OUT/'veneer-wall-growth-connectivity.json')
        shutil.copyfile(REVIEW/'bed-base-before-after.png',OUT/'veneer-wall-base-comparison.png')
    else:
        shutil.copyfile(WORK/'end-tie-bed-preview.png',OUT/'veneer-end-tie-bed-preview.png')
    m=baseline_json('M-geometry-validation.json')
    for skin,row in zip(m['skins'],proof['plates']):
        carrier=copy.deepcopy(row['reviewed_geometry'])
        carrier.update(type='continuous_braced_wall_cradle',revision=REVISION,
            bonded_tooth_count=row['bond_toolpaths']['bond_probes_checked'],tree_supports_still_required=True,
            tooth_width_mm=skin['carrier']['tooth_width_mm'],trim_pocket_depth_mm=skin['carrier']['trim_pocket_depth_mm'],
            continuous_starter_shoe=False,starter_shoe_assembly_x_width_mm=0,
            cleanup='Remove sacrificial wall stock and original necks progressively while protecting the veneer; physical cleanup unqualified.')
        skin['carrier']=carrier
    m.update(veneer_carrier_revision=REVISION,editable_sha256=proof['editable_sha256'],
        source_preservation_basis='veneer-wall-promotion-validation.json')
    save_json(OUT/'M-geometry-validation.json',m)
    geometry=baseline_json('geometry-validation.json')
    for row in proof['plates']:
        entry=next(x for x in geometry['print_bounds'] if x['plate']==row['plate'])
        entry.update(name=row['name'],bounds_mm=row['bounds_mm'])
    geometry.update(editable_sha256=proof['editable_sha256'],veneer_carrier_revision=REVISION,
        wall_promotion_preservation_basis='veneer-wall-unchanged-plates.json',
        wall_geometry_validation='veneer-wall-promotion-validation.json')
    save_json(OUT/'geometry-validation.json',geometry)
    native=json.loads((OUT/'native-validation.json').read_text())
    native['geometry_validation_sha256']=sha(OUT/'geometry-validation.json');save_json(OUT/'native-validation.json',native)
    modifiers=baseline_json('modifier-validation.json')
    modifiers.update(editable_sha256=proof['editable_sha256'],native_project_sha256=proof['project_sha256'],
        preservation_basis='All modifier-bearing meshes, object settings and poses are unchanged; replacement veneer objects have no modifiers.')
    save_json(OUT/'modifier-validation.json',modifiers)
    for name in ['plate-plan.json','Dara-A2L-Editable.json']:
        data=baseline_json(name)
        for row in proof['plates']:
            entry=next(x for x in data['records'] if x['plate']==row['plate'])
            entry.update(name=row['name'],body_bounds_mm=row['bounds_mm'])
        data.update(editable_sha256=proof['editable_sha256'],veneer_carrier_revision=REVISION)
        if name=='Dara-A2L-Editable.json':data.update(native_slice_validated=True,native_project_sha256=proof['project_sha256'])
        save_json(OUT/name,data)
    gui=baseline_json('tower-gui-verification.json')
    ancestors=[]
    if CORRECTION_GEOMETRY is not None:
        ancestors=copy.deepcopy(gui['inherited_unchanged_plate_proofs'])
        for ancestor in ancestors:
            if ancestor['path']=='veneer-wall-unchanged-plates.json':ancestor['path']='veneer-wall-r5-unchanged-plates.json'
    gui.update(current_native_project_sha256=proof['project_sha256'],current_project_fresh_GUI_review_pending=True,
        unchanged_plate_proof_sha256=sha(OUT/'veneer-wall-unchanged-plates.json'),
        inherited_unchanged_plate_proofs=[dict(path='veneer-wall-unchanged-plates.json',sha256=sha(OUT/'veneer-wall-unchanged-plates.json'))]+ancestors,
        current_review_scope='Prior GUI observation applies to unchanged tower-bearing knot plates. Current veneer plates passed native slicing and the complete file passed native reopen. No new GUI observation or physical print is claimed.')
    save_json(OUT/'tower-gui-verification.json',gui)
    save_json(OUT/'veneer-carrier-update.json',dict(revision=REVISION,project_sha256=proof['project_sha256'],
        editable_sha256=proof['editable_sha256'],frame_and_accessory_inputs_preserved=True,
        changed_plates=[15,16,17],validation='veneer-wall-promotion-validation.json',physical_confirmation_pending=True))
    inventory=ROOT/'output/development/m-veneer-cosmetic-fit/All-veneer-production-audit.json'
    catalog=json.loads((BASE/inventory.relative_to(ROOT)).read_text())
    targets={'Dara.3mf',(OUT/'Dara-A2L-Complete.3mf').relative_to(ROOT).as_posix(),(OUT/'Dara-A2L-Editable.3mf').relative_to(ROOT).as_posix()}
    for item in catalog['projects']:
        if item['project'] in targets:
            item.update(sha256=sha(ROOT/item['project']),carrier_revision=REVISION,
                veneers=[dict(name=p['name'],plate=p['plate'],corrected_geometry_maximum_error_mm=p['maximum_mesh_error_mm']) for p in proof['plates']],
                validation_report='working/bambu/Dara-Photo-Frame-A2L/veneer-wall-promotion-validation.json')
    catalog['geometry_and_removal_checks']=[x for x in catalog['geometry_and_removal_checks'] if x['family']!='A2L']+[
        dict(family='A2L',veneer=i,revision=REVISION,cut_necks=p['bond_toolpaths']['bond_probes_checked'],
            continuous_braced_walls=True,bed_tie_bands=2,legacy_base_removed=True,physical_cleanup_pending=True)
        for i,p in enumerate(proof['plates'],1)]
    catalog['wall_cradle_promotion_basis']=dict(report='working/bambu/Dara-Photo-Frame-A2L/veneer-wall-promotion-validation.json',sha256=sha(OUT/'veneer-wall-promotion-validation.json'))
    save_json(inventory,catalog)
    print('Installed identical root/named native projects and synchronized editable source and reports.',flush=True)


def release():
    """Run after documentation and verifier changes, then run portable audit."""
    proof=json.loads((OUT/'veneer-wall-promotion-validation.json').read_text())
    assert sha(ROOT/'Dara.3mf')==sha(OUT/'Dara-A2L-Complete.3mf')==proof['project_sha256']
    assert sha(OUT/'Dara-A2L-Editable.3mf')==proof['editable_sha256']
    data=baseline_json('release-validation.json');native=json.loads((OUT/'native-validation.json').read_text())
    data.update(project_sha256=proof['project_sha256'],editable_sha256=proof['editable_sha256'],
        veneer_carrier_revision=REVISION,veneer_and_support_total_g=proof['total_veneer_and_support_g'],
        native_reopen_return_code=0,native_reopen_result=json.loads((WORK/'reopen/result.json').read_text()),
        GUI_verification='Prior exact-file GUI observation inherited for unchanged tower plates; current file native reopen passed; fresh GUI review pending.',
        plate_estimates=[dict(plate=p['plate'],seconds=p['seconds'],weight_g=p['weight_g']) for p in native['plates']])
    paths=[ROOT/path for path in data['evidence_sha256']]
    paths.extend(OUT/name for name in ['veneer-wall-promotion-validation.json','veneer-wall-unchanged-plates.json',
        'veneer-wall-reviewed-r5.json','veneer-wall-growth-connectivity.json','veneer-wall-base-comparison.png'])
    paths.extend(ROOT/'scripts'/name for name in ['promote_veneer_wall_cradle.py','validate_veneer_wall_promotion.py',
        'install_veneer_wall_cradle.py','check_veneer_wall_openings.py'])
    if CORRECTION_GEOMETRY is not None:
        paths.extend(OUT/name for name in ['veneer-wall-r5-unchanged-plates.json','veneer-wall-r5-promotion-validation.json','veneer-end-tie-bed-preview.png'])
        paths.append(ROOT/'scripts/correct_veneer_end_ties.py')
    data['evidence_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
    save_json(OUT/'release-validation.json',data)
    print('Release evidence synchronized:',proof['project_sha256'],flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['install','release']);args=parser.parse_args()
    {'install':install,'release':release}[args.action]()
