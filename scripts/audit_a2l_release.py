"""Portable standard-library audit of the published A2L project and evidence."""
import hashlib,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def valid_hash(p,expected):
 raw=Path(p).read_bytes()
 if Path(p).suffix in ['.py','.scad','.json','.md','.txt']:
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
 proofs=gui.get('inherited_unchanged_plate_proofs',[dict(path='veneer-unchanged-plates.json',sha256=gui['unchanged_plate_proof_sha256'])])
 expected=project_sha
 for proof in proofs:
  path=OUT/proof['path'];kept=json.loads(path.read_text());assert valid_hash(path,proof['sha256'])
  assert kept['project_sha256']==expected
  assert set(range(1,11))<=set(p['plate'] for p in kept['plates'])
  assert all(p['geometry_settings_and_poses_unchanged'] and p['gcode_byte_identical'] for p in kept['plates'])
  expected=kept['baseline_project_sha256']
 assert expected==gui['GUI_tested_file_sha256']
 update=json.loads((OUT/'veneer-carrier-update.json').read_text())
 assert update.get('frame_and_accessory_inputs_preserved') or (update['all_other_zip_entries_byte_identical_to_previous_editable'] and update['saved_poses_materials_and_other_geometry_preserved'])
 assert all(not p['startup_prime_tower_check']['intersects_model'] for p in native['plates'])
 assert all(p['startup_prime_tower_check']['estimated_footprint_area_mm2']==0 for p in native['plates'][10:])
 return 'Prior GUI tower result retained: tower plates unchanged; fresh visual review pending'

def verify_carriers(carriers):
 assert len(carriers)==3
 for row in carriers:
  c=row['carrier']
  if c.get('revision','').startswith('wall-cradle-'):
   assert c['front_panel_continuous_to_bed'] and c['isolated_tall_posts']==0
   assert c['legacy_base_stock_remaining_mm3']<1e-5
   assert len(c['bed_tie_bands'])==2
   assert all(b['width_mm']==4 and b['height_mm']==.6 for b in c['bed_tie_bands'])
   assert c['physical_confirmation_pending']
   if c['revision']=='wall-cradle-r6-end-ties':
    assert c['band_location']=='two open ends, flush outer edges'
    assert c['difference_above_band_height_mm3']<1e-4
    assert c['protected_wall_and_neck_removed_mm3']<1e-4
    assert c['difference_outside_band_masks_mm3']<1e-4
    assert [b['outer_edge_y_mm'] for b in c['bed_tie_bands']]==c['source_wall_y_extent_mm']
    assert all(min(b['front_and_rear_overlap_mm3'])>1 for b in c['end_wall_contacts'])
  else:
   assert c['continuous_starter_shoe'] is False and c['starter_shoe_assembly_x_width_mm']==0
   assert c['cutter_access_necks_checked']==c['bonded_tooth_count']
   assert c['maximum_cutter_access_obstruction_mm3']<1e-5
   assert c['flush_trim_excess_outside_finished_veneer_mm3']<1e-5


def verify_M_layout():
 plan=json.loads((OUT/'production-plan.json').read_text())
 if not plan.get('M_layout_revision'):return
 proof=json.loads((OUT/'M-joint-layout-validation.json').read_text())
 assert proof['revision']==plan['M_layout_revision']=='short-veneer-staggered-cores-v2'
 assert valid_hash(OUT/'production-plan.json',proof['production_plan_sha256'])
 assert valid_hash(ROOT/'working/review/a2l-m-joints/staggered-layout.json',plan['M_layout_specification_sha256'])
 assert valid_hash(ROOT/'working/review/a2l-m-joints/evaluation.json',plan['M_study_sha256'])
 assert len(plan['core_regions'])==5 and plan['core_plate_groups']==[[1],[2],[3],[4,5]]
 assert proof['narrow_structural_arches_have_no_seams'] and proof['minimum_key_head_wall_mm']>=10
 assert proof['key_heads_clear_of_veneer_seams_mm']>=8 and proof['minimum_core_joint_separation_mm']>=18
 assert proof['minimum_cross_layer_seam_separation_mm']>=20
 assert all(c['aligned_length_mm']<1e-6 and c['distance_mm']>=20 for c in proof['cross_layer_seam_checks'])
 assert sum(s['length_mm'] for s in plan['skin_seams'])<24.3


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
 verify_carriers(carriers)
 for plate in n['plates'][:10]:
  tower=plate['prime_tower_clearance']
  assert tower['studio_model_convex_hull_clearance_mm']>8
  assert tower['actual_tower_to_other_extrusion_clearance_mm']>3
 assert all(p['startup_prime_tower_check']['intersects_model'] is False for p in n['plates'])
 assert all(p['startup_prime_tower_check']['estimated_footprint_area_mm2']==0 for p in n['plates'][10:])
 assert n['native_project_sha256']==r['project_sha256']
 assert r['native_reopen_return_code']==0
 verify_gui_evidence(r['project_sha256'],n)
 verify_M_layout()
 wall=None
 if r.get('veneer_carrier_revision','').startswith('wall-cradle-'):
  wall=json.loads((OUT/'veneer-wall-unchanged-plates.json').read_text())
  proof=json.loads((OUT/'veneer-wall-promotion-validation.json').read_text())
  assert wall['project_sha256']==proof['project_sha256']==r['project_sha256']
  assert wall['editable_sha256']==proof['editable_sha256']==r['editable_sha256']
  assert wall['changed_plates']==[15,16,17]
  assert {p['plate'] for p in wall['plates']}==set(range(1,21))-{15,16,17}
  assert sum(p['weight_g'] for p in proof['plates'])==proof['total_veneer_and_support_g']<1000
  assert sum(p['bond_toolpaths']['bond_probes_checked'] for p in proof['plates'])==721
  assert all(p['band_toolpaths']['bond_probes_checked']>0 and p['opening_toolpaths']['support_segments_inside_openings']==0 for p in proof['plates'])
  with zipfile.ZipFile(ROOT/'Dara.3mf') as archive:
   for plate in wall['plates']:
    assert plate['geometry_settings_and_poses_unchanged'] and plate['gcode_byte_identical']
    for name,h in plate['preserved_assets_sha256'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==h,name
  for path,h in wall['protected_external_file_sha256'].items():assert valid_hash(ROOT/path,h),path
 if r.get('joint_revision')=='lower-lap-pads-removed-v1':
  pad=json.loads((OUT/'joint-pad-removal-validation.json').read_text())
  kept=json.loads((OUT/'joint-pad-unchanged-plates.json').read_text())
  predecessor=wall
  if r.get('veneer_carrier_revision')=='wall-cradle-r6-end-ties':
   predecessor=json.loads((OUT/'veneer-wall-r5-unchanged-plates.json').read_text())
   assert predecessor['project_sha256']==wall['baseline_project_sha256']
   assert predecessor['editable_sha256']==wall['baseline_editable_sha256']
   assert predecessor['changed_plates']==wall['changed_plates']
  assert pad['project_sha256']==kept['project_sha256']==(predecessor['baseline_project_sha256'] if predecessor else r['project_sha256'])
  assert pad['editable_sha256']==(predecessor['baseline_editable_sha256'] if predecessor else r['editable_sha256'])
  assert pad['removed_pads']==42 and pad['joints']==14
  assert len(pad['native_pad_toolpaths'])==42
  assert all(abs(p['maximum_model_extrusion_z_mm']-4.8)<.001 for p in pad['native_pad_toolpaths'])
  assert {p['plate'] for p in kept['plates']}==set(range(11,21))
  for path,h in kept['protected_external_file_sha256'].items():assert valid_hash(ROOT/path,h),path
  with zipfile.ZipFile(ROOT/'Dara.3mf') as protected_archive:
   for plate in kept['plates']:
    if wall and plate['plate'] in wall['changed_plates']:continue
    assert plate['geometry_settings_and_poses_unchanged'] and plate['gcode_byte_identical']
    for name,h in plate['preserved_assets_sha256'].items():assert hashlib.sha256(protected_archive.read(name)).hexdigest()==h,name
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
