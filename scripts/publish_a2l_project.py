"""Publish only after geometry, native toolpaths and a native reopen pass."""
import argparse,json,shutil
from pathlib import Path
from build_a2l_project import ROOT,OUT,EDIT,FINAL,sha,save,PROFILE,settings

def publish(native,reopen):
 m=json.loads((OUT/'modifier-validation.json').read_text())
 n=json.loads((OUT/'native-validation.json').read_text());g=json.loads((OUT/'geometry-validation.json').read_text());r=json.loads((reopen/'result.json').read_text())
 assert n['native_return_code']==r['return_code']==0
 from audit_a2l_release import verify_gui_evidence,verify_M_layout
 verify_M_layout()
 gui_status=verify_gui_evidence(sha(native/'sliced.3mf'),n)
 assert all(p['prime_tower_clearance']['actual_tower_to_other_extrusion_clearance_mm']>3 for p in n['plates'][:10])
 assert sha(EDIT)==n['editable_sha256']==g['editable_sha256']
 assert m['editable_sha256']==sha(EDIT)
 assert sha(native/'sliced.3mf')==n['native_project_sha256']==m['native_project_sha256']
 carriers=json.loads((OUT/'M-geometry-validation.json').read_text())['skins']
 assert len(carriers)==3
 for row in carriers:
  c=row['carrier'];assert c['continuous_starter_shoe'] is False and c['starter_shoe_assembly_x_width_mm']==0
  assert c['cutter_access_necks_checked']==c['bonded_tooth_count']
  assert c['maximum_cutter_access_obstruction_mm3']<1e-5 and c['flush_trim_excess_outside_finished_veneer_mm3']<1e-5
 assert (reopen/'result.json').stat().st_mtime>=(native/'sliced.3mf').stat().st_mtime
 for p in [FINAL,ROOT/'Dara.3mf']:
  if not p.exists() or sha(p)!=n['native_project_sha256']:shutil.copyfile(native/'sliced.3mf',p)
 profiles={}
 for kind in ['machine','process','filament']:
  for p in (PROFILE/kind).glob('*A2L*.json'):
   if kind=='machine' and ('0.4 nozzle' not in p.name and p.stem!='Bambu Lab A2L'):continue
   if kind=='process' and p.stem!='0.20mm Standard @BBL A2L':continue
   if kind=='filament' and p.stem not in ['Generic PLA @BBL A2L','Generic PLA Silk @BBL A2L']:continue
   profiles[f'{kind}/{p.name}']=sha(p)
 save(OUT/'profile-provenance.json',dict(installed_profile_sha256=profiles,printer='Bambu Lab A2L 0.4 nozzle',
   flattened_settings_embedded_in_editable_and_native_projects=True,A1_machine_commands_replaced=True))
 evidence=[OUT/x for x in ['production-plan.json','plate-plan.json','frame-geometry-validation.json','M-geometry-validation.json','geometry-validation.json','native-validation.json','profile-provenance.json','modifier-validation.json','tower-placement.json','tower-fix-preservation.json','tower-gui-verification.json','tower-GUI-position-reset.json','knot-volume-toolpath-comparison.json']]
 evidence += [ROOT/'scripts'/x for x in ['build_a2l_project.py','validate_a2l_project.py','publish_a2l_project.py','development_3mf.py','develop_m_veneer.py','develop_cosmetic_joints.py','veneer_fin_carrier.py','plan_veneer_fins.py','check_fin_toolpaths.py','audit_a2l_release.py','create_a2l_print_guide.py','audit_dara_release.py','check_a2l_towers.py','check_knot_volume_partitions.py']]
 evidence += [ROOT/'scripts'/x for x in ['veneer_trim_carrier.py','refresh_production_veneers.py','audit_all_veneers.py']]
 evidence += [OUT/'tower-baseline-carrier-preservation.json',OUT/'veneer-carrier-update.json',OUT/'veneer-unchanged-plates.json',OUT/'M-joint-layout-validation.json',ROOT/'working/review/a2l-m-joints/staggered-layout.json',ROOT/'scripts/repartition_a2l_M.py',ROOT/'scripts/preview_a2l_M_layout.py',ROOT/'working/review/a2l-m-joints/M-staggered-seam-layout.png']
 inventory=ROOT/'output/development/m-veneer-cosmetic-fit/All-veneer-production-audit.json'
 if inventory.exists():
  audit=json.loads(inventory.read_text());assert audit['all_saved_projects_match_corrected_geometry']
  assert next(row['sha256'] for row in audit['projects'] if row['project']=='Dara.3mf')==sha(native/'sliced.3mf')
  evidence.append(inventory)
 evidence += [ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad',ROOT/'working/review/a2l-hidden-joints/lean-candidate.json',ROOT/'working/review/a2l-m-joints/evaluation.json',EDIT]
 pad_path=OUT/'joint-pad-removal-validation.json'
 if pad_path.exists():
  pads=json.loads(pad_path.read_text())
  assert pads['project_sha256']==sha(native/'sliced.3mf') and pads['editable_sha256']==sha(EDIT)
  assert pads['removed_pads']==42 and len(pads['native_pad_toolpaths'])==42
  evidence += [pad_path,OUT/'joint-pad-unchanged-plates.json',ROOT/'scripts/remove_a2l_joint_pads.py',ROOT/'scripts/validate_a2l_pad_removal.py',ROOT/'scripts/validate_ribbon_bed_datum.py']
 if (ROOT/'output/pdf/Dara-A2L-Print-Guide.pdf').exists():evidence.append(ROOT/'output/pdf/Dara-A2L-Print-Guide.pdf')
 report=dict(project_sha256=sha(FINAL),editable_sha256=sha(EDIT),native_reopen_return_code=r['return_code'],native_reopen_result=r,
    GUI_verification=gui_status,plates=20,assembly_pieces=len(n['native_roundtrip']),printer='Bambu Lab A2L 0.4 nozzle',structural_infill='8% gyroid',veneer_infill='100%',
    plate_estimates=[dict(plate=p['plate'],seconds=p['seconds'],weight_g=p['weight_g']) for p in n['plates']],
    evidence_sha256={str(p.relative_to(ROOT)):sha(p) for p in evidence},physical_confirmation_pending=True,
    retained_A1_complete_sha256=sha(ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf'),
    sample_project_sha256=sha(ROOT/'output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf'))
 if pad_path.exists():
  report.update(joint_revision=pads['revision'],physical_joint_result=pads['physical_report'],
                physical_test_printer_context=pads['physical_printer_context'],physical_A2L_production_print_not_yet_reported=True)
 save(OUT/'release-validation.json',report)
 print('Published root and named A2L project:',report['project_sha256'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('native',type=Path);p.add_argument('reopen',type=Path);a=p.parse_args();publish(a.native,a.reopen)
