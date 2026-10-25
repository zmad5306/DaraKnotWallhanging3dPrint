"""Promote the approved veneer corrections into the main six-plate Letter project.

All six plates are resliced because process and filament limits are shared.
No printer job is sent. Actions are build, slice, validate, reopen, publish.
"""
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'.work/python-libs'), str(ROOT/'scripts')]
import numpy as np
import organize_root_projects as org
from validate_production_split import Project
from validate_print_project import scan_gcode
from check_fin_toolpaths import check_fin_bonds
from set_veneer_eryone_spool_limits import audit_commands

WORK = ROOT/'.work/letter-veneer-promotion'
REPORT = ROOT/'release/letter-veneer-correction'
SOURCE = ROOT/'Letter.3mf'
CANDIDATE = ROOT/'output/Letter Veneers/Letter Veneers.3mf'
NAMES = ['Left letter veneer', 'Right letter veneer', 'Center letter veneer']
EXE = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')


def dump(path, data):
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8', newline='\n')


def build():
    WORK.mkdir(exist_ok=True);REPORT.mkdir(exist_ok=True)
    assert org.sha(SOURCE) == '75b14a311d5a92ad5cfd6fd4ff1a8228a19ed2e027a04b67b02439fd74905ecd'
    assert org.sha(CANDIDATE) == '6bcfc5bbc39382607d28d6a840f66e96b66051d22ca4df30ca41900f99c468f1'
    shutil.copyfile(SOURCE, WORK/'before.3mf')
    files = org.read(SOURCE);cf = org.read(CANDIDATE)
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    model = ET.fromstring(files['3D/3dmodel.model'])
    ccfg = ET.fromstring(cf['Metadata/model_settings.config'])
    cmodel = ET.fromstring(cf['3D/3dmodel.model'])
    settings = json.loads(files['Metadata/project_settings.config'])
    wanted = json.loads(cf['Metadata/project_settings.config'])
    changes = {k:[settings.get(k),v] for k,v in wanted.items() if settings.get(k)!=v and k not in ('wipe_tower_x','wipe_tower_y')}
    assert len(changes) == 23, changes
    for k,(_,v) in changes.items():settings[k] = v
    for i,name in enumerate(NAMES):
        old = next(o for o in cfg.findall('object') if org.props(o)['name']==name)
        src = next(o for o in ccfg.findall('object') if org.props(o)['name']==name)
        oid = old.get('id');sid = src.get('id');part_id = old.find('part').get('id')
        new = copy.deepcopy(src);new.set('id', oid);new.find('part').set('id',part_id)
        index = list(cfg).index(old);cfg.remove(old);cfg.insert(index,new)
        target = model.find(org.tag('resources')).find(f"{org.tag('object')}[@id='{oid}']")
        src_obj = cmodel.find(org.tag('resources')).find(f"{org.tag('object')}[@id='{sid}']")
        co = copy.deepcopy(src_obj.find(org.tag('components'))[0])
        src_asset = co.get('{'+org.P+'}path').lstrip('/')
        asset = f'3D/Objects/letter_veneer_{i+1}.model'
        child = ET.fromstring(cf[src_asset])
        child.find(org.tag('resources'))[0].set('id',part_id)
        co.set('objectid',part_id);co.set('{'+org.P+'}path','/'+asset)
        target.find(org.tag('components')).clear();target.find(org.tag('components')).append(co)
        files[asset] = org.xml(child)
        src_item = cmodel.find(org.tag('build')).find(f"{org.tag('item')}[@objectid='{sid}']")
        pose = org.transform(src_item.get('transform'))
        pose[:2,3] += org.grid(i+3,6,org.pitch(settings))-org.grid(i,3,org.pitch(settings))
        item = model.find(org.tag('build')).find(f"{org.tag('item')}[@objectid='{oid}']")
        item.set('transform',org.matrix_text(pose))
        assembly = cfg.find('assemble')
        if assembly is not None:
            for a in assembly:
                if a.get('object_id')==oid:a.set('transform',org.matrix_text(pose))
    assets = {c.get('{'+org.P+'}path').lstrip('/') for c in model.iter(org.tag('component'))}
    for n in list(files):
        if (n.startswith('3D/Objects/') and n not in assets) or org.ASSET.fullmatch(n) or n in ['Metadata/slice_info.config','Metadata/filament_sequence.json']:
            del files[n]
    for plate in cfg.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key') in ['gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file']:plate.remove(md)
    rels = ET.Element('Relationships',xmlns=org.R)
    for i,n in enumerate(sorted(assets)):
        ET.SubElement(rels,'Relationship',Target='/'+n,Id=f'rel-{i}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    files['3D/_rels/3dmodel.model.rels'] = org.xml(rels)
    files['Metadata/model_settings.config'] = org.xml(cfg)
    files['Metadata/project_settings.config'] = json.dumps(settings,indent=2).encode()
    files['3D/3dmodel.model'] = org.xml(model)
    org.clean_relations(files);org.write(WORK/'editable.3mf',files)
    # Check each actual volume in printer coordinates, and every material/paint record.
    _,old = org.rows(SOURCE);_,new = org.rows(WORK/'editable.3mf');_,candidate = org.rows(CANDIDATE)
    expected = {r['name']:r for r in old if r['plate']<=3}|{r['name']:r for r in candidate}
    preservation=[]
    for row in new:
        e = expected[row['name']]
        assert row['settings']==e['settings']
        assert len(row['parts'])==len(e['parts'])
        maximum=0
        for a,b in zip(row['parts'],e['parts']):
            assert a['settings']==b['settings'] and a['paint']==b['paint'] and a['subtype']==b['subtype']
            assert np.array_equal(a['mesh'].faces,b['mesh'].faces)
            av=a['mesh'].vertices@row['transform'][:3,:3].T+row['transform'][:3,3]
            bv=b['mesh'].vertices@e['transform'][:3,:3].T+e['transform'][:3,3]
            err=float(np.max(abs(av-bv)));assert err<.000001,err
            maximum=max(maximum,err)
        preservation.append(dict(name=row['name'],plate=row['plate'],source='original core' if row['plate']<=3 else 'approved veneer candidate',max_mesh_pose_difference_mm=maximum,paint_and_object_volume_settings_preserved=True))
    dump(WORK/'build.json',dict(source_sha256=org.sha(SOURCE),candidate_sha256=org.sha(CANDIDATE),
        editable_sha256=org.sha(WORK/'editable.3mf'),project_setting_changes=changes,objects=preservation,
        protected_projects={p.name:org.sha(p) for p in ROOT.glob('*.3mf') if p.name!='Letter.3mf'}))
    print('Prepared six plates with exact core/candidate geometry and 23 shared setting changes.',flush=True)


def native(action):
    folder = WORK/('native' if action=='slice' else 'reopen');folder.mkdir(exist_ok=True)
    src = WORK/('editable.3mf' if action=='slice' else 'native/sliced.3mf')
    args = [str(EXE)]+(['--slice','0'] if action=='slice' else [])+['--export-3mf','sliced.3mf','--outputdir',str(folder),str(src)]
    with (folder/'native.log').open('w') as log:
        r=subprocess.run(args,cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    dump(folder/'process.json',dict(exit=r.returncode))
    print(action,'exit',r.returncode,flush=True);assert r.returncode==0


def validate():
    native=WORK/'native/sliced.3mf';files=org.read(native)
    preservation=org.compare(WORK/'editable.3mf',native)
    build=json.loads((WORK/'build.json').read_text());p=Project(native)
    geom=json.loads((ROOT/'release/veneer-nub-cleanup-r8/Letter-geometry.json').read_text())
    checks=[]
    locks=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',nozzle_diameter=['0.4'],layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',curr_bed_type='Textured PEI Plate',is_infill_first='0',support_type='tree(auto)')
    for k,v in locks.items():assert p.settings[k]==v,(k,p.settings[k])
    for i in range(1,7):
        raw=files[f'Metadata/plate_{i}.gcode'];text=raw.decode()
        assert hashlib.md5(raw).hexdigest().upper()==files[f'Metadata/plate_{i}.gcode.md5'].decode().strip().upper()
        commands=audit_commands(text);assert commands['out_of_range_count']==0,commands['out_of_range_examples']
        assert commands['max_travel_acceleration_mm_s2']<=2500
        c={l[2:].split(' = ',1)[0]:l[2:].split(' = ',1)[1] for l in text.splitlines() if l.startswith('; ') and ' = ' in l}
        for k,v in locks.items():assert c[k]==(v[0] if isinstance(v,list) else v),(k,c[k])
        for k,(_,v) in build['project_setting_changes'].items():assert c[k]==v[0],(i,k,c.get(k),v)
        bounds=np.array(scan_gcode(text)['bead_xy_bounds_mm']);assert np.all(bounds[0]>0) and np.all(bounds[1]<[330,320])
        rec=dict(plate=i,gcode_sha256=hashlib.sha256(raw).hexdigest(),commands=commands,bead_bounds_mm=bounds.tolist())
        if i>=4:
            name=NAMES[i-4];row=p.rows[name];eff={**p.settings,**row['settings'],**row['parts'][0]['settings']}
            assert eff['sparse_infill_density']=='100%' and eff['enable_support']=='1' and eff['extruder']=='1'
            g=next(x for x in geom['objects'] if x['name'].startswith(f'V{i-3} '));pose=np.array(g['pose']);probes=np.array([c['new_probe_assembly_xyz_mm'] for c in g['connections']]);probes=probes@pose[:3,:3].T+pose[:3,3]
            rec['connections']=check_fin_bonds(text,dict(bond_probes_print_xyz_mm=probes.tolist()));rec['name']=name
        checks.append(rec)
        print('Plate',i,'native commands, spool limits, acceleration and bounds passed.',flush=True)
    result=json.loads((WORK/'native/result.json').read_text());assert result['return_code']==0 and len(result['sliced_plates'])==6
    mass=sum(f['total_used_g'] for plate in result['sliced_plates'] if plate['id']>=4 for f in plate['filaments']);assert mass<1000
    info=ET.fromstring(files['Metadata/slice_info.config']);warnings=[w.attrib for plate in info.findall('plate') for w in plate.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' and w.get('error_code') in ('10018003','1000C003') for w in warnings)
    for name,digest in build['protected_projects'].items():assert org.sha(ROOT/name)==digest
    dump(WORK/'validation.json',dict(**build,project_sha256=org.sha(native),native_preservation=preservation,checks=checks,
        fresh_native_slices=True,all_six_spool_limits_verified=True,veneer_mass_g=mass,warnings=warnings,native_result=result,
        physical_qualification=False,physical_shift_cause='Unresolved; corrected geometry/process has no physical result.'))


def publish():
    report=json.loads((WORK/'validation.json').read_text());native=WORK/'native/sliced.3mf'
    assert org.sha(native)==report['project_sha256']
    assert json.loads((WORK/'reopen/process.json').read_text())['exit']==0
    report['native_reopen_comparison']=org.compare(native,WORK/'reopen/sliced.3mf');report['native_reopen_verified']=True
    continuity=json.loads((WORK/'continuity/continuity.json').read_text())
    assert continuity['source_sha256']==report['project_sha256']
    assert [c['plate'] for c in continuity['checks']]==[4,5,6]
    assert all(c['front_layers']==1469 and c['missing_front_layers']==0 and c['maximum_adjacent_median_change_mm']<.01 for c in continuity['checks'])
    report['full_height_continuity']=continuity['checks']
    candidate_report=json.loads((CANDIDATE.parent/'validation.json').read_text())
    report['assembly_to_printer_by_plate']=candidate_report['assembly_to_printer_by_plate']
    report['physical_observation']=candidate_report['physical_observation']
    report['geometry_correction']=json.loads((ROOT/'output/Dara-A2L-Veneers-Carrier-Motion-r9/validation.json').read_text())['geometry_correction']
    assert org.sha(SOURCE)==report['source_sha256']
    for name,digest in report['protected_projects'].items():assert org.sha(ROOT/name)==digest
    shutil.copyfile(native,SOURCE)
    files=org.read(SOURCE);report['archive_entries_sha256']={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}
    before=org.read(WORK/'before.3mf')
    report['changed_archive_entries']=[n for n in set(files)|set(before) if files.get(n)!=before.get(n)]
    old_catalog=json.loads((ROOT/'release/root-projects/catalog.json').read_text())
    org.REPORT=WORK/'cad';org.REPORT.mkdir(exist_ok=True);org.TITLES=['Letter'];org.export_cad()
    row=json.loads((org.REPORT/'catalog.json').read_text())['Letter']
    old_catalog['Letter'].update(row)
    old_catalog['Letter']['veneer_correction_validation']='release/letter-veneer-correction/validation.json'
    dump(ROOT/'release/root-projects/catalog.json',old_catalog)
    hashes=json.loads((ROOT/'release/root-projects/gcode-sha256.json').read_text())
    hashes['Letter']={f'plate_{i}':hashlib.sha256(files[f'Metadata/plate_{i}.gcode']).hexdigest() for i in range(1,7)}
    dump(ROOT/'release/root-projects/gcode-sha256.json',hashes)
    dump(ROOT/'release/root-projects/Letter-native.json',report['native_result'])
    for name in ['continuity.json','all-veneer-continuity.png','transition-inspection.json','carrier-end-transitions.png']:
        shutil.copyfile(WORK/'continuity'/name,REPORT/name)
    continuity['source']='Letter.3mf'
    continuity['perimeter_closure_follow_up']='transition-inspection.json'
    dump(REPORT/'continuity.json',continuity)
    report['continuity_report']='release/letter-veneer-correction/continuity.json'
    report['transition_inspection']='release/letter-veneer-correction/transition-inspection.json'
    report['evidence_sha256']={name:org.sha(REPORT/name) for name in
        ['continuity.json','all-veneer-continuity.png','transition-inspection.json','carrier-end-transitions.png']}
    dump(REPORT/'validation.json',report)
    print('Published main Letter.3mf',report['project_sha256'],flush=True)


if __name__=='__main__':
    action=sys.argv[1]
    if action=='build':build()
    elif action in ['slice','reopen']:native(action)
    elif action=='validate':validate()
    elif action=='publish':publish()
    else:raise ValueError(action)
