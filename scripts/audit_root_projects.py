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
        if row.get('joint_approval_validation'):
            approval=json.loads((ROOT/row['joint_approval_validation']).read_text())
            assert title=='Knot' and approval['project_sha256']==row['sha256']
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
        if row.get('normal_supports_validation'):
            normal_revision=json.loads((ROOT/row['normal_supports_validation']).read_text())
            assert title=='Knot' and normal_revision['project_sha256']==row['sha256']
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
            assert cleanup_revision['project_sha256']==(rollback_revision['source_project_sha256'] if rollback_revision else row['sha256'])
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
            if filament_revision:
                for key,change in filament_revision['project_setting_changes'].items():
                    expected=cleanup_revision['project_setting_changes'][key]['after'] if cleanup_revision else change['after']
                    assert s[key]==expected,(title,key)
                for name,digest in filament_revision['preserved_archive_entries_sha256'].items():
                    if cleanup_revision and name not in cleanup_revision['preserved_archive_entries_sha256']:continue
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
            if cleanup_revision:
                for key,change in cleanup_revision['project_setting_changes'].items():
                    assert s[key]==change['after'],(title,key)
                for name,digest in cleanup_revision['preserved_archive_entries_sha256'].items():
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
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
                assert all(m.get('key')!='is_infill_first' or m.get('value')=='0' for m in cfg.iter('metadata'))
            if normal_revision:
                assert s['support_type']=='normal(auto)' and s['support_style']=='default'
                for name,digest in normal_revision['preserved_archive_entries_sha256'].items():
                    assert hashlib.sha256(z.read(name)).hexdigest()==digest,(title,name)
                assert all(props(o)['enable_support']=='1' and props(o)['support_interface_spacing']=='0.2' for o in cfg.findall('object'))
                assert all(m.get('key')!='support_type' or m.get('value')=='normal(auto)' for m in cfg.iter('metadata'))
            sliced=row.get('sliced',True)
            assert len(cfg.findall('plate'))==row['plates']
            assert len(info.findall('plate'))==(row['plates'] if sliced else 0)
            if not sliced:assert not any(n.endswith('.gcode') for n in names)
            assert len(cfg.findall('object'))==len(row['objects'])
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
                        blue=skin.get('blue_layer_count')==5 and props(part).get('extruder')==blue_slot
                        reinforcement=props(part).get('name')=='Local solid screw reinforcement'
                        if not (blue or reinforcement):continue
                        assert part.get('subtype')=='modifier_part'
                        if reinforcement:assert props(part)['sparse_infill_density']=='100%'
                        co=components[part.get('id')];asset=co.get(P+'path').lstrip('/')
                        if asset not in assets:assets[asset]=ET.fromstring(z.read(asset))
                        mesh=assets[asset].find(C+'resources').find(f"{C}object[@id='{part.get('id')}']").find(C+'mesh')
                        t=list(map(float,co.get('transform').split()))
                        assert t[:9]==[1,0,0,0,1,0,0,0,1]
                        heights=[float(v.get('z'))+t[11] for v in mesh.find(C+'vertices')]
                        if blue:
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
                if filament_revision:
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
