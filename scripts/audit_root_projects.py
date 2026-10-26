"""Read-only release audit, requiring only Python's standard library.

Hashes tie the deeper mesh/pose checks to the distributed projects, CAD and STL.
This does not slice or send anything to a printer.
"""
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def props(node):
    return {m.get('key'):m.get('value') for m in node.findall('metadata')}


def audit():
    catalog=json.loads((ROOT/'release/root-projects/catalog.json').read_text())
    expected={v['project'] for v in catalog.values()}
    sample_catalog=ROOT/'release/samples/catalog.json'
    samples=json.loads(sample_catalog.read_text()) if sample_catalog.exists() else {}
    expected_tracked=expected|{v['file'] for v in samples.values()}
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    assert {p for p in tracked if p.lower().endswith('.3mf')}==expected_tracked, 'Tracked 3MF inventory differs from the declared releases/samples.'
    for sample in samples.values():
        assert sha(ROOT/sample['file'])==sample['sha256']
        assert (ROOT/sample['validation']).is_file()
    assert {p.name for p in ROOT.glob('*.3mf')}==expected, 'Unexpected root 3MF.'
    total=0
    cleanup_sources={}
    for title,row in catalog.items():
        path=ROOT/row['project'];assert sha(path)==row['sha256'],path
        white_support_revision = None
        white_support_changed = set()
        if row.get('white_support_base_validation'):
            white_support_revision=json.loads((ROOT/row['white_support_base_validation']).read_text())
            assert title=='Knot' and white_support_revision['project_sha256']==row['sha256']
            assert white_support_revision['changed_setting']=={'support_filament':['0','1']}
            assert white_support_revision['all_other_project_settings_preserved']
            assert white_support_revision['geometry_poses_paint_object_volume_overrides_preserved']
            assert white_support_revision['all_original_3d_archive_entries_byte_identical'] and white_support_revision['all_cad_stl_unchanged']
            assert white_support_revision['fresh_native_slices'] and white_support_revision['native_reopen_verified']
            assert white_support_revision['parser_indented_tool_and_leading_decimal_extrusion_regression_passed']
            assert len(white_support_revision['plates'])==10
            white_support_changed=set(white_support_revision['changed_archive_entries'])
            for name,digest in white_support_revision['evidence_sha256'].items():
                assert sha((ROOT/row['white_support_base_validation']).parent/name)==digest,name
        labels_revision = None
        if row.get('labels_validation'):
            labels_revision=json.loads((ROOT/row['labels_validation']).read_text())
            assert title=='Knot' and labels_revision['project_sha256']==(white_support_revision['source_project_sha256'] if white_support_revision else row['sha256'])
            assert labels_revision['original_meshes_settings_support_paint_and_poses_preserved']
            assert labels_revision['all_global_settings_preserved'] and labels_revision['original_knot_stls_unchanged']
            assert labels_revision['native_reopen_verified'] and labels_revision['fresh_native_slices']
            assert len(labels_revision['labels'])==len(labels_revision['plates'])==10
            for n,label in enumerate(labels_revision['labels'],1):
                assert label['text']==f'P{n} F{n}' and label['plate']==n and label['extruder']==3
                assert label['z_mm']==[0,.2] and label['height_mm']==8
                assert label['minimum_body_edge_clearance_mm']>3 and label['minimum_joint_screw_modifier_clearance_mm']>3
            for name,digest in labels_revision['evidence_sha256'].items():
                assert sha((ROOT/row['labels_validation']).parent/name)==digest,name
            for name,digest in labels_revision['new_modifier_stls'].items():assert sha(ROOT/name)==digest,name
        lap_revision = None
        if row.get('solid_laps_validation'):
            lap_revision=json.loads((ROOT/row['solid_laps_validation']).read_text())
            assert title=='Knot' and lap_revision['project_sha256']==(labels_revision['source_project_sha256'] if labels_revision else row['sha256'])
            assert lap_revision['user_reported_solid_lap_success']
            assert lap_revision['joint_count']==14 and lap_revision['solid_lap_modifier_count']==28
            assert lap_revision['local_fill_settings']=={'sparse_infill_density':'100%','sparse_infill_pattern':'zig-zag'}
            assert lap_revision['original_meshes_settings_support_paint_and_poses_preserved']
            assert lap_revision['all_global_settings_preserved'] and lap_revision['original_knot_stls_unchanged']
            assert lap_revision['native_reopen_verified'] and lap_revision['fresh_native_slices']
            assert lap_revision['all_50_screw_modifiers_capped_at_z12_4']
            assert lap_revision['all_five_skin_layers_cross_screw_boundaries']
            assert lap_revision['all_28_lap_regions_disjoint_from_screw_bolsters']
            assert len(lap_revision['plates'])==10 and len(lap_revision['groove_support_checks'])==28
            assert len(lap_revision['removed_pad_toolpath_checks'])==42
            for name,digest in lap_revision['evidence_sha256'].items():
                assert sha((ROOT/row['solid_laps_validation']).parent/name)==digest,name
            for name,digest in lap_revision['new_modifier_stls'].items():assert sha(ROOT/name)==digest,name
            sample=ROOT/lap_revision['accepted_sample']
            if sample.exists():assert sha(sample)==lap_revision['accepted_sample_sha256']
        if row.get('joint_approval_validation'):
            approval=json.loads((ROOT/row['joint_approval_validation']).read_text())
            assert title=='Knot' and approval['project_sha256']==(lap_revision['source_project_sha256'] if lap_revision else row['sha256'])
            assert approval['user_reported_sample_joint_fit_pass']
            assert approval['production_geometry_already_matches_accepted_sample']
            assert approval['new_geometry_changes']==[]
            assert approval['production_joint_count']==14 and approval['key_count']==28
            assert approval['native_key_layer_checks']==140 and len(approval['plates'])==10
            assert all(not p['infill_first'] and p['support_type']=='normal(auto)' for p in approval['plates'])
            for name,digest in approval['evidence_sha256'].items():assert sha(ROOT/name)==digest,name
            sample=ROOT/approval['accepted_sample']
            if sample.exists():assert sha(sample)==approval['accepted_sample_sha256']
        filament_revision = None
        cleanup_revision = None
        rollback_revision = None
        normal_revision = None
        name_revision = None
        veneer_revision = None
        if row.get('veneer_correction_validation'):
            veneer_revision=json.loads((ROOT/row['veneer_correction_validation']).read_text())
            assert title=='Letter' and veneer_revision['project_sha256']==row['sha256']
            assert veneer_revision['native_reopen_verified'] and veneer_revision['fresh_native_slices']
            assert veneer_revision['all_six_spool_limits_verified'] and veneer_revision['veneer_mass_g']<1000
            assert len(veneer_revision['checks'])==6 and len(veneer_revision['objects'])==8
            assert all(r['max_mesh_pose_difference_mm']<.000001 and r['paint_and_object_volume_settings_preserved'] for r in veneer_revision['objects'])
            assert sum(r.get('connections',{}).get('bond_probes_checked',0) for r in veneer_revision['checks'])==102
            assert all(r['front_layers']==1469 and r['missing_front_layers']==0 for r in veneer_revision['full_height_continuity'])
            for name,digest in veneer_revision['evidence_sha256'].items():
                assert sha((ROOT/row['veneer_correction_validation']).parent/name)==digest,name
        if row.get('name_validation'):
            name_revision=json.loads((ROOT/row['name_validation']).read_text())
            assert title=='Letter' and name_revision['sha256']==(veneer_revision['source_sha256'] if veneer_revision else row['sha256'])
            assert name_revision['all_geometry_paint_poses_process_material_settings_and_gcode_byte_identical']
            assert name_revision['stl_geometry_bytes_unchanged']
            assert {r['name'] for r in name_revision['names']}=={'Left letter veneer','Right letter veneer','Center letter veneer'}
        if row.get('normal_supports_validation'):
            normal_revision=json.loads((ROOT/row['normal_supports_validation']).read_text())
            assert title=='Knot' and normal_revision['project_sha256']==(lap_revision['source_project_sha256'] if lap_revision else row['sha256'])
            assert normal_revision['changed_setting']=={'support_type':['tree(auto)','normal(auto)']}
            assert normal_revision['all_other_project_settings_preserved']
            assert normal_revision['geometry_poses_paint_byte_preserved']
            assert normal_revision['object_volume_overrides_preserved']
            assert normal_revision['native_reopen_verified'] and normal_revision['fresh_native_slices']
            assert len(normal_revision['removed_pad_toolpath_checks'])==42
            assert all(p['maximum_model_z_mm']==4.8 for p in normal_revision['removed_pad_toolpath_checks'])
            for key in ['joint_geometry_report','joint_toolpath_report']:
                assert sha(ROOT/normal_revision[key])==normal_revision[key+'_sha256']
        if row.get('infill_first_revert_validation'):
            rollback_revision=json.loads((ROOT/row['infill_first_revert_validation']).read_text())
            assert title=='Knot' and rollback_revision['project_sha256']==(normal_revision['source_project_sha256'] if normal_revision else row['sha256'])
            assert rollback_revision['changed_setting']=={'is_infill_first':['1','0']}
            assert rollback_revision['all_other_project_settings_preserved']
            assert rollback_revision['geometry_poses_paint_byte_preserved']
            assert rollback_revision['object_volume_overrides_preserved']
            assert rollback_revision['native_reopen_verified'] and rollback_revision['fresh_native_slices']
            assert len(rollback_revision['removed_pad_toolpath_checks'])==42
            assert all(p['maximum_model_z_mm']==4.8 for p in rollback_revision['removed_pad_toolpath_checks'])
            for key in ['joint_geometry_report','joint_toolpath_report']:
                assert sha(ROOT/rollback_revision[key])==rollback_revision[key+'_sha256']
        if row.get('filament_cleanup_validation'):
            cleanup_revision=json.loads((ROOT/row['filament_cleanup_validation']).read_text())
            assert cleanup_revision['project_sha256']==(rollback_revision['source_project_sha256'] if rollback_revision else name_revision['source_sha256'] if name_revision else row['sha256'])
            assert cleanup_revision['all_retained_material_parameters_preserved']
            assert cleanup_revision['all_process_parameters_preserved']
            assert cleanup_revision['geometry_and_poses_byte_preserved']
            assert cleanup_revision['object_volume_overrides_preserved_except_slot_indexes']
            assert cleanup_revision['native_reopen_verified'] and cleanup_revision['fresh_native_slices']
            cleanup_sources[row['project']]=cleanup_revision['source_project_sha256']
        if row.get('filament_validation'):
            revision=json.loads((ROOT/row['filament_validation']).read_text())
            filament_revision=revision['projects'][title]
            assert filament_revision['project_sha256']==(cleanup_revision['source_project_sha256'] if cleanup_revision else row['sha256'])
            assert filament_revision['all_print_parameters_preserved']
            assert filament_revision['geometry_poses_support_paint_object_volume_settings_byte_preserved']
        assert sha(ROOT/row['cad'])==row['cad_sha256'],row['cad']
        for obj in row['objects']:
            for part in obj['parts']:assert sha(ROOT/part['file'])==part['sha256'],part['file']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            names=set(z.namelist());s=json.loads(z.read('Metadata/project_settings.config'))
            if white_support_revision:
                assert s['support_filament']=='1' and s['support_interface_filament']=='0'
                for name,digest in white_support_revision['preserved_archive_entries_sha256'].items():
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
            if labels_revision:
                for name,digest in labels_revision['preserved_archive_entries_sha256'].items():
                    if name in white_support_changed:continue
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
            if lap_revision:
                for name,digest in lap_revision['preserved_archive_entries_sha256'].items():
                    if name in white_support_changed:continue
                    if labels_revision and name not in labels_revision['preserved_archive_entries_sha256']:continue
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
            if name_revision and not veneer_revision:
                for name,digest in name_revision['archive_entries_sha256'].items():
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
            if veneer_revision:
                for name,digest in veneer_revision['archive_entries_sha256'].items():
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
                for key,(_,value) in veneer_revision['project_setting_changes'].items():
                    assert s[key]==value,(title,key)
            if filament_revision:
                for key,change in filament_revision['project_setting_changes'].items():
                    expected=cleanup_revision['project_setting_changes'][key]['after'] if cleanup_revision else change['after']
                    if veneer_revision and key in veneer_revision['project_setting_changes']:
                        before,after=veneer_revision['project_setting_changes'][key]
                        assert before==expected,(title,key)
                        expected=after
                    assert s[key]==expected,(title,key)
                for name,digest in filament_revision['preserved_archive_entries_sha256'].items():
                    if name in white_support_changed:continue
                    if labels_revision and name not in labels_revision['preserved_archive_entries_sha256']:continue
                    if lap_revision and name in lap_revision['changed_archive_entries']:continue
                    if cleanup_revision and name not in cleanup_revision['preserved_archive_entries_sha256']:continue
                    if name_revision and name in name_revision['changed_archive_entries']:continue
                    if veneer_revision and name in veneer_revision['changed_archive_entries']:continue
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
            if cleanup_revision:
                for key,change in cleanup_revision['project_setting_changes'].items():
                    expected=change['after']
                    if veneer_revision and key in veneer_revision['project_setting_changes']:
                        before,after=veneer_revision['project_setting_changes'][key]
                        assert before==expected,(title,key)
                        expected=after
                    assert s[key]==expected,(title,key)
                for name,digest in cleanup_revision['preserved_archive_entries_sha256'].items():
                    if name in white_support_changed:continue
                    if labels_revision and name not in labels_revision['preserved_archive_entries_sha256']:continue
                    if lap_revision and name in lap_revision['changed_archive_entries']:continue
                    if name_revision and name in name_revision['changed_archive_entries']:continue
                    if veneer_revision and name in veneer_revision['changed_archive_entries']:continue
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
                assert s['filament_settings_id']==row['filament_settings_id']==cleanup_revision['retained_profiles']
            cfg=ET.fromstring(z.read('Metadata/model_settings.config'));info=ET.fromstring(z.read('Metadata/slice_info.config'))
            model=ET.fromstring(z.read('3D/3dmodel.model'))
            if cleanup_revision:
                slots={str(i+1) for i in range(len(s['filament_settings_id']))}
                assert {m.get('value') for m in cfg.iter('metadata') if m.get('key')=='extruder'}==slots
                assert {f.get('id') for f in info.iter('filament')}==slots
            assert s['printer_model']==row['printer']
            stencil='Stencils' in title
            locks=dict(sparse_infill_density='0%' if stencil else '8%',sparse_infill_pattern='gyroid',
                       nozzle_diameter=['0.4'],layer_height='0.2',initial_layer_print_height='0.2',
                       wall_loops='2' if stencil else '4',top_shell_layers='4' if stencil else '5',
                       bottom_shell_layers='4' if stencil else '5',curr_bed_type='Textured PEI Plate')
            for k,v in locks.items():assert s[k]==v,(title,k,s[k],v)
            if title in ['Knot','Letter']:assert s['is_infill_first']=='0'
            if rollback_revision:
                for name,digest in rollback_revision['preserved_archive_entries_sha256'].items():
                    if name in white_support_changed:continue
                    if lap_revision and name in lap_revision['changed_archive_entries']:continue
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
                assert all(m.get('key')!='is_infill_first' or m.get('value')=='0' for m in cfg.iter('metadata'))
            if normal_revision:
                assert s['support_type']=='normal(auto)' and s['support_style']=='default'
                for name,digest in normal_revision['preserved_archive_entries_sha256'].items():
                    if name in white_support_changed:continue
                    if lap_revision and name in lap_revision['changed_archive_entries']:continue
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
                assert all(props(o)['enable_support']=='1' and props(o)['support_interface_spacing']=='0.2' for o in cfg.findall('object'))
                assert all(m.get('key')!='support_type' or m.get('value')=='normal(auto)' for m in cfg.iter('metadata'))
            sliced=row.get('sliced',True)
            assert len(cfg.findall('plate'))==row['plates']
            assert len(info.findall('plate'))==(row['plates'] if sliced else 0)
            if not sliced:assert not any(n.endswith('.gcode') for n in names)
            assert len(cfg.findall('object'))==len(row['objects'])
            if lap_revision:
                laps=[p for o in cfg.findall('object') for p in o.findall('part') if props(p).get('name','').startswith('100% solid lap - J')]
                assert len(laps)==28
                for part in laps:
                    assert part.get('subtype')=='modifier_part'
                    settings=props(part)
                    assert settings['sparse_infill_density']=='100%' and settings['sparse_infill_pattern']=='zig-zag'
                    assert 'extruder' not in settings
            if labels_revision:
                label_parts=[p for o in cfg.findall('object') for p in o.findall('part') if props(p).get('name','').startswith('Blue first-layer ID - ')]
                assert len(label_parts)==10
                assert {props(p)['name'] for p in label_parts}=={f'Blue first-layer ID - P{n} F{n}' for n in range(1,11)}
                assert all(p.get('subtype')=='modifier_part' and props(p)=={'name':props(p)['name'],'extruder':'3'} for p in label_parts)
            resources={o.get('id') for o in model.find(C+'resources')}
            assert {i.get('objectid') for i in model.find(C+'build')}==resources
            for c in model.iter(C+'component'):assert c.get(P+'path').lstrip('/') in names
            if title=='Knot':
                skin=json.loads((ROOT/row['validation']).read_text())
                assert skin['project_sha256']==(filament_revision['source_project_sha256'] if filament_revision else row['sha256'])
                if skin.get('white_show_face_pattern')=='hilbertcurve':
                    assert skin['brown_blue_joint_and_pin_toolpath_geometry_preserved']
                    assert skin['screw_modifiers_preserved_at_z12_4']
                    ranges=ET.fromstring(z.read('Metadata/layer_config_ranges.xml'))
                    assert len(ranges.findall('object'))==10
                    for obj in ranges.findall('object'):
                        rr=obj.findall('range');assert len(rr)==1
                        assert (float(rr[0].get('min_z')),float(rr[0].get('max_z')))==(13,13.6)
                        assert {o.get('opt_key'):o.text for o in rr[0].findall('option')}=={
                            'layer_height':'0.2','extruder':'0','top_surface_pattern':'hilbertcurve'}
                    for obj in cfg.findall('object'):
                        for part in obj.findall('part'):
                            if props(part).get('extruder')=='4':assert props(part)['top_surface_pattern']=='monotonicline'
                            if props(part).get('extruder')=='2':assert 'top_surface_pattern' not in props(part)
                else:
                    assert skin['all_five_top_shell_layers_cross_former_modifier_boundary']
                    assert s['top_surface_pattern']=='monotonicline'
                    assert 'Metadata/layer_config_ranges.xml' not in names
                    assert all(m.get('value')!='hilbertcurve' for m in cfg.iter('metadata'))
                objects={o.get('id'):o for o in model.find(C+'resources')}
                assets={};count=0;blue_count=0
                for obj in cfg.findall('object'):
                    components={c.get('objectid'):c for c in objects[obj.get('id')].find(C+'components')}
                    for part in obj.findall('part'):
                        blue_slot='3' if cleanup_revision else '4'
                        is_label=props(part).get('name','').startswith('Blue first-layer ID - ')
                        blue=skin.get('blue_layer_count')==5 and props(part).get('extruder')==blue_slot and not is_label
                        reinforcement=props(part).get('name')=='Local solid screw reinforcement'
                        if not (blue or reinforcement or is_label):continue
                        assert part.get('subtype')=='modifier_part'
                        if reinforcement:assert props(part)['sparse_infill_density']=='100%'
                        co=components[part.get('id')];asset=co.get(P+'path').lstrip('/')
                        if asset not in assets:assets[asset]=ET.fromstring(z.read(asset))
                        mesh=assets[asset].find(C+'resources').find(f"{C}object[@id='{part.get('id')}']").find(C+'mesh')
                        t=list(map(float,co.get('transform').split()))
                        assert t[:9]==[1,0,0,0,1,0,0,0,1]
                        heights=[float(v.get('z'))+t[11] for v in mesh.find(C+'vertices')]
                        if is_label:
                            assert labels_revision and abs(min(heights))<1e-6 and abs(max(heights)-.2)<1e-6
                        elif blue:
                            assert abs(min(heights)-12.5)<1e-6 and abs(max(heights)-13.5)<1e-6
                            blue_count+=1
                        else:
                            assert abs(min(heights))<1e-6 and abs(max(heights)-12.4)<1e-6
                            count+=1
                assert count==skin['modifier_count']==50
                if skin.get('blue_layer_count')==5:assert blue_count==skin['blue_modifier_count']==10
            for i,plate in enumerate(cfg.findall('plate'),1):
                assert props(plate)['plater_id']==str(i)
                for ins in plate.findall('model_instance'):assert props(ins)['object_id'] in resources
                for k,v in props(plate).items():
                    if k.endswith('_file') and v:assert v in names,(title,k,v)
                if not sliced:continue
                name=f'Metadata/plate_{i}.gcode';data=z.read(name)
                if veneer_revision:
                    inspected=next(p for p in veneer_revision['checks'] if p['plate']==i)
                    assert hashlib.sha256(data).hexdigest()==inspected['gcode_sha256']
                    assert inspected['commands']['out_of_range_count']==0
                    assert inspected['commands']['max_travel_acceleration_mm_s2']<=2500
                    assert all(29.9999<=v['min_mm_s']<=v['max_mm_s']<=60.0001 and v['max_acceleration_mm_s2']<=1500 for v in inspected['commands']['features'].values())
                elif filament_revision:
                    filament_plate=next(p for p in filament_revision['plates'] if p['plate']==i)
                    if cleanup_revision:
                        cleanup_plate=next(p for p in cleanup_revision['plates'] if p['plate']==i)
                        assert cleanup_plate['source_gcode_sha256']==filament_plate['gcode_sha256']
                        if rollback_revision:
                            rollback_plate=next(p for p in rollback_revision['plates'] if p['plate']==i)
                            assert rollback_plate['source_gcode_sha256']==cleanup_plate['gcode_sha256']
                            if normal_revision:
                                normal_plate=next(p for p in normal_revision['plates'] if p['plate']==i)
                                assert normal_plate['source_gcode_sha256']==rollback_plate['gcode_sha256']
                                if lap_revision:
                                    lap_plate=next(p for p in lap_revision['plates'] if p['plate']==i)
                                    assert lap_plate['source_gcode_sha256']==normal_plate['gcode_sha256']
                                    if labels_revision:
                                        label_plate=next(p for p in labels_revision['plates'] if p['plate']==i)
                                        assert label_plate['source_gcode_sha256']==lap_plate['gcode_sha256']
                                        if white_support_revision:
                                            white_plate=next(p for p in white_support_revision['plates'] if p['plate']==i)
                                            assert white_plate['source_gcode_sha256']==label_plate['gcode_sha256']
                                            assert hashlib.sha256(data).hexdigest()==white_plate['gcode_sha256']
                                            assert white_plate['gcode_setting_changes']=={'support_filament':['0','1']}
                                            assert white_plate['all_support_base_white'] and white_plate['no_blue_support_extrusion']
                                            assert set(white_plate['support_after']['Support'])=={'1'}
                                            assert all('3' not in tools for tools in white_plate['support_after'].values())
                                            assert white_plate['first_layer_support_white_segments']>0 and white_plate['first_layer_blue_label_segments']>0
                                            assert white_plate['model_path_geometry_materials_widths_identical']
                                            assert white_plate['interface_transition_geometry_materials_widths_identical']
                                            assert white_plate['first_layer_support_geometry_widths_identical']
                                            assert white_plate['model_z_by_filament_mm']['3']==[.2,12.8,13.0,13.2,13.4,13.6]
                                        else:
                                            assert hashlib.sha256(data).hexdigest()==label_plate['gcode_sha256']
                                        assert label_plate['global_gcode_config_unchanged'] and label_plate['top_surface_directions_preserved']
                                        assert label_plate['upper_model_path_segments_identical']
                                        assert label_plate['label_coverage_fraction']>.96 and min(label_plate['glyph_coverage_fractions'])>.94
                                        assert label_plate['white_backing_coverage_fraction']>.98
                                        assert label_plate['model_z_by_filament_mm']['3']==[.2,12.8,13.0,13.2,13.4,13.6]
                                    else:
                                        assert hashlib.sha256(data).hexdigest()==lap_plate['gcode_sha256']
                                    assert lap_plate['global_gcode_config_unchanged'] and lap_plate['body_8_percent_gyroid_retained']
                                    assert lap_plate['top_surface_directions_preserved']
                                    assert all(min(site['crossing_segments'].values())>=5 for site in lap_plate['screw_skin_continuity'])
                                else:
                                    assert hashlib.sha256(data).hexdigest()==normal_plate['gcode_sha256']
                                assert normal_plate['gcode_setting_changes']=={'support_type':['tree(auto)','normal(auto)']}
                                assert normal_plate['support_extrusion_moves']>0 and normal_plate['support_interface_extrusion_moves']>0
                                assert normal_plate['model_z_by_filament_mm']['3']==[12.8,13.0,13.2,13.4,13.6]
                                assert normal_plate['top_surface_directions_preserved']
                                assert all(min(site['crossing_segments'].values())>=5 for site in normal_plate['screw_skin_continuity'])
                            else:
                                assert hashlib.sha256(data).hexdigest()==rollback_plate['gcode_sha256']
                            assert rollback_plate['gcode_setting_changes']=={'is_infill_first':['1','0']}
                            assert rollback_plate['model_z_by_filament_mm']['3']==[12.8,13.0,13.2,13.4,13.6]
                            expected_modifiers=sum(p['settings'].get('name')=='Local solid screw reinforcement'
                                for o in row['objects'] if o['plate']==i for p in o['parts'])
                            assert len(rollback_plate['screw_skin_continuity'])==expected_modifiers
                            assert all(min(site['crossing_segments'].values())>=5 for site in rollback_plate['screw_skin_continuity'])
                            assert rollback_plate['top_surface_directions_preserved']
                        else:
                            assert hashlib.sha256(data).hexdigest()==cleanup_plate['gcode_sha256']
                        if title=='Knot':assert cleanup_plate['model_z_by_filament_mm']['3']==[12.8,13.0,13.2,13.4,13.6]
                    else:
                        assert hashlib.sha256(data).hexdigest()==filament_plate['gcode_sha256']
                        stripped=re.sub(rb'(?m)^; filament_(?:settings_id|vendor|ids) = [^\r\n]*',b'',data)
                        assert hashlib.sha256(stripped).hexdigest()==filament_plate['nonidentity_content_sha256']
                if title=='Knot':
                    expected=next(p for p in skin['plates'] if p['plate']==i)
                    assert (filament_plate['source_gcode_sha256'] if filament_revision else hashlib.sha256(data).hexdigest())==expected['gcode_sha256']
                    if skin.get('blue_layer_count')==5:
                        assert expected['model_z_by_filament_mm']['4']==[12.8,13.0,13.2,13.4,13.6]
                assert hashlib.md5(data).hexdigest().upper()==z.read(name+'.md5').decode().strip().upper()
                config=data.decode(errors='replace')
                if white_support_revision:
                    assert re.search(r'^; support_filament = 1\s*$',config,re.M),(title,i)
                    assert re.search(r'^; support_interface_filament = 0\s*$',config,re.M),(title,i)
                if title in ['Knot','Letter']:
                    assert re.search(r'^; is_infill_first = 0\s*$',config,re.M),(title,i)
                if normal_revision:
                    assert re.search(r'^; support_type = normal\(auto\)\s*$',config,re.M),(title,i)
                for k in ['sparse_infill_density','sparse_infill_pattern','layer_height','wall_loops']:
                    assert re.search(r'^; '+k+r' = '+re.escape(locks[k])+r'\s*$',config,re.M),(title,i,k)
            for p in info.findall('plate'):
                for warning in p.findall('warning'):
                    assert warning.get('msg')=='not_support_traditional_timelapse', (title,warning.attrib)
        total+=row['plates']
        print(f'{title}: {row["plates"]} plates; project, CAD, STL and settings checks pass; '+('G-code checks pass.' if sliced else 'unsliced, slicing required.'))
    print(f'{len(catalog)} root projects / {total} plates. Slice availability and physical qualification remain as documented.')
    preset_count=0
    for folder in ('sunlu-profile-defaults-r2','sunlu-silk-copper-r1'):
        report_path=ROOT/'release'/folder/'validation.json'
        if not report_path.exists():continue
        report=json.loads(report_path.read_text())
        assert report['native_validation_passed'] and report['local_preset_installation_complete']
        for name,row in report['profiles'].items():
            assert sha(report_path.parent/'presets'/(name+'.json'))==row['after_sha256']
            assert row['native_load_verified'] and row['native_compared_option_count']==134
            preset_count+=1
        for name,digest in report['protected_projects'].items():
            # These reports describe preservation at the preset-installation
            # revision. A subsequent authorized cleanup links that exact source
            # to its current project, rather than rewriting historical evidence.
            assert cleanup_sources.get(name,sha(ROOT/name))==digest,(folder,name)
    if preset_count:print(f'{preset_count} current SUNLU preset snapshots: hashes and native loading evidence pass.')


if __name__=='__main__':audit()
