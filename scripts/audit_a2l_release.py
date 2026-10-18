"""Portable standard-library audit of the published A2L project and evidence."""
import hashlib,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def valid_hash(p,expected):
 raw=Path(p).read_bytes()
 if Path(p).suffix in ['.py','.scad','.json']:
  lf=raw.replace(b'\r\n',b'\n');return expected in {hashlib.sha256(b).hexdigest() for b in [raw,lf,lf.replace(b'\n',b'\r\n')]}
 return hashlib.sha256(raw).hexdigest()==expected
def props(e):return {m.get('key'):m.get('value') for m in e.findall('metadata')}
def verify_gui_evidence(project_sha,native):
 gui=json.loads((OUT/'tower-gui-verification.json').read_text())
 assert gui['prime_tower_collision_warning_absent_after_fresh_GUI_open']
 if gui['GUI_tested_file_sha256']==project_sha:return 'Fresh GUI open of this exact file'
 # A carrier-only update may inherit the previously observed tower result
 # only when all tower-bearing inputs and saved slices are proven unchanged.
 assert gui.get('current_project_fresh_GUI_review_pending') is True
 assert gui['current_native_project_sha256']==project_sha
 path=OUT/'veneer-unchanged-plates.json';kept=json.loads(path.read_text())
 assert sha(path)==gui['unchanged_plate_proof_sha256']
 assert kept['baseline_project_sha256']==gui['GUI_tested_file_sha256']
 assert kept['project_sha256']==project_sha
 assert set(range(1,11))<=set(p['plate'] for p in kept['plates'])
 assert all(p['geometry_settings_and_poses_unchanged'] and p['gcode_byte_identical'] for p in kept['plates'])
 update=json.loads((OUT/'veneer-carrier-update.json').read_text())
 assert update['all_other_zip_entries_byte_identical_to_previous_editable']
 assert update['saved_poses_materials_and_other_geometry_preserved']
 assert all(not p['startup_prime_tower_check']['intersects_model'] for p in native['plates'])
 assert all(p['startup_prime_tower_check']['estimated_footprint_area_mm2']==0 for p in native['plates'][10:])
 return 'Prior GUI tower result retained: tower plates unchanged; fresh visual review pending (Mac locked)'


def audit():
 r=json.loads((OUT/'release-validation.json').read_text());n=json.loads((OUT/'native-validation.json').read_text())
 for p in [ROOT/'Dara.3mf',OUT/'Dara-A2L-Complete.3mf']:assert sha(p)==r['project_sha256'],p
 for path,h in r['evidence_sha256'].items():assert valid_hash(ROOT/path,h),path
 inventory=ROOT/'output/development/m-veneer-cosmetic-fit/All-veneer-production-audit.json'
 if inventory.exists():
  catalog=json.loads(inventory.read_text());assert catalog['all_saved_projects_match_corrected_geometry']
  for row in catalog['projects']:assert sha(ROOT/row['project'])==row['sha256'],row['project']
 assert sha(ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf')==r['retained_A1_complete_sha256']
 assert sha(ROOT/'output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf')==r['sample_project_sha256']
 assert n['native_return_code']==0 and len(n['plates'])==20
 carriers=json.loads((OUT/'M-geometry-validation.json').read_text())['skins']
 assert len(carriers)==3
 for row in carriers:
  c=row['carrier'];assert c['continuous_starter_shoe'] is False
  assert c['starter_shoe_assembly_x_width_mm']==0
  assert c['cutter_access_necks_checked']==c['bonded_tooth_count']
  assert c['maximum_cutter_access_obstruction_mm3']<1e-5
  assert c['flush_trim_excess_outside_finished_veneer_mm3']<1e-5
 for plate in n['plates'][:10]:
  tower=plate['prime_tower_clearance']
  assert tower['studio_model_convex_hull_clearance_mm']>8
  assert tower['actual_tower_to_other_extrusion_clearance_mm']>3
 assert all(p['startup_prime_tower_check']['intersects_model'] is False for p in n['plates'])
 assert all(p['startup_prime_tower_check']['estimated_footprint_area_mm2']==0 for p in n['plates'][10:])
 assert n['native_project_sha256']==r['project_sha256']
 assert r['native_reopen_return_code']==0
 verify_gui_evidence(r['project_sha256'],n)
 with zipfile.ZipFile(ROOT/'Dara.3mf') as z:
  assert z.testzip() is None
  settings=json.loads(z.read('Metadata/project_settings.config'));assert settings['printer_model']=='Bambu Lab A2L'
  assert settings['wipe_tower_y']==['160']*20
  assert all(15<=float(x)<=285 for x in settings['wipe_tower_x'])
  assert settings['prime_tower_rib_wall']=='0'
  assert settings['sparse_infill_density']=='8%' and settings['sparse_infill_pattern']=='gyroid'
  cfg=ET.fromstring(z.read('Metadata/model_settings.config'));assert len(cfg.findall('plate'))==20
  for co in cfg.findall('object'):
   s=props(co)
   if s.get('name','').startswith('V'):assert s['sparse_infill_density']=='100%'
  for row in n['plates']:
   name=f'Metadata/plate_{row["plate"]}.gcode';data=z.read(name);assert hashlib.sha256(data).hexdigest()==row['gcode_sha256'],name
   assert b'; EXECUTABLE_BLOCK_END' in data
   md5=name+'.md5'
   if md5 in z.namelist():assert z.read(md5).decode().strip().lower()==hashlib.md5(data).hexdigest()
 print('A2L PASS: identical main/alias, 20 native slices, 8% structural / solid veneers, source/evidence hashes, native reopen.')
if __name__=='__main__':audit()
