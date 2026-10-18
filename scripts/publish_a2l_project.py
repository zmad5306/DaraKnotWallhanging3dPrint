"""Publish only after geometry, native toolpaths and a native reopen pass."""
import argparse,json,shutil
from pathlib import Path
from build_a2l_project import ROOT,OUT,EDIT,FINAL,sha,save,PROFILE,settings

def publish(native,reopen):
 m=json.loads((OUT/'modifier-validation.json').read_text())
 n=json.loads((OUT/'native-validation.json').read_text());g=json.loads((OUT/'geometry-validation.json').read_text());r=json.loads((reopen/'result.json').read_text())
 assert n['native_return_code']==r['return_code']==0
 gui=json.loads((OUT/'tower-gui-verification.json').read_text())
 assert gui['prime_tower_collision_warning_absent_after_fresh_GUI_open']
 assert gui['GUI_tested_file_sha256']==sha(native/'sliced.3mf')
 assert all(p['prime_tower_clearance']['actual_tower_to_other_extrusion_clearance_mm']>3 for p in n['plates'][:10])
 assert sha(EDIT)==n['editable_sha256']==g['editable_sha256']
 assert m['editable_sha256']==sha(EDIT)
 assert sha(native/'sliced.3mf')==n['native_project_sha256']==m['native_project_sha256']
 assert (reopen/'result.json').stat().st_mtime>=(native/'sliced.3mf').stat().st_mtime
 for p in [FINAL,ROOT/'Dara.3mf']:shutil.copyfile(native/'sliced.3mf',p)
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
 evidence += [ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad',ROOT/'working/review/a2l-hidden-joints/lean-candidate.json',ROOT/'working/review/a2l-m-joints/evaluation.json',EDIT]
 if (ROOT/'output/pdf/Dara-A2L-Print-Guide.pdf').exists():evidence.append(ROOT/'output/pdf/Dara-A2L-Print-Guide.pdf')
 report=dict(project_sha256=sha(FINAL),editable_sha256=sha(EDIT),native_reopen_return_code=r['return_code'],native_reopen_result=r,
    plates=20,assembly_pieces=61,printer='Bambu Lab A2L 0.4 nozzle',structural_infill='8% gyroid',veneer_infill='100%',
    plate_estimates=[dict(plate=p['plate'],seconds=p['seconds'],weight_g=p['weight_g']) for p in n['plates']],
    evidence_sha256={str(p.relative_to(ROOT)):sha(p) for p in evidence},physical_confirmation_pending=True,
    retained_A1_complete_sha256=sha(ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf'),
    sample_project_sha256=sha(ROOT/'output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf'))
 save(OUT/'release-validation.json',report)
 print('Published root and named A2L project:',report['project_sha256'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('native',type=Path);p.add_argument('reopen',type=Path);a=p.parse_args();publish(a.native,a.reopen)
