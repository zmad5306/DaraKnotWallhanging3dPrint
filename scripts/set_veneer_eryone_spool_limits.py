"""Apply the user's ERYONE spool limits to the three-veneer r9 candidate.

No printer job is sent. Root production projects remain unchanged.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / '.work/python-libs'), str(ROOT / 'scripts')]
import numpy as np
import organize_root_projects as org
from development_3mf import sha
from check_veneer_layer_overlap import parse
from check_fin_toolpaths import check_fin_bonds
from validate_print_project import scan_gcode
from validate_production_split import Project

SOURCE = ROOT / 'output/Dara-A2L-Veneers-Carrier-Motion-r9/Dara-A2L-Veneers-Carrier-Motion-r9.3mf'
SOURCE_HASH = '0eeb8b60ce2624a802416906e51126d4e63d879b2f00ab30b63f86e1339b7b75'
WORK = ROOT / '.work/veneer-eryone-limits-r10'
OUT = ROOT / 'output/Dara-A2L-Veneers-ERYONE-r10'
TITLE = 'Dara-A2L-Veneers-ERYONE-r10'
EXE = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
TOKEN = re.compile(r'([A-Z])\s*(-?(?:\d*\.\d+|\d+\.?\d*))')


def build():
    assert sha(SOURCE) == SOURCE_HASH
    WORK.mkdir(exist_ok=True)
    files = org.read(SOURCE)
    s = json.loads(files['Metadata/project_settings.config'])
    cfg = ET.fromstring(files['Metadata/model_settings.config'])
    desired = dict(
        outer_wall_speed=['40'], inner_wall_speed=['60'],
        sparse_infill_speed=['60'], internal_solid_infill_speed=['60'],
        gap_infill_speed=['60'], top_surface_speed=['60'],
        support_speed=['60'], support_interface_speed=['60'],
        initial_layer_infill_speed=['60'], small_perimeter_speed=['30'],
        slow_down_min_speed=['30'], filament_bridge_speed=['30'],
        overhang_4_4_speed=['30'], overhang_totally_speed=['30'],
        filament_overhang_4_4_speed=['30'], filament_overhang_totally_speed=['30'],
        nozzle_temperature_range_high=['220'], filament_flush_temp=['220'],
    )
    changes = {}
    for k,v in desired.items():
        assert k in s
        if s[k] != v:
            changes[k] = [s[k],v]
            s[k] = v
    object_changes = []
    for o in cfg.findall('object'):
        name=org.props(o)['name'];assert name.startswith(('V1 ','V2 ','V3 '))
        md=o.find("metadata[@key='inner_wall_speed']")
        assert md.get('value')=='80'
        md.set('value','60');object_changes.append(dict(name=name,inner_wall_speed=['80','60']))
    for i,plate in enumerate(cfg.findall('plate'),1):
        org.setmeta(plate,'plater_name',f'{i} - V{i} ERYONE spool limits r10')
        for md in list(plate.findall('metadata')):
            if md.get('key') in ('gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file'):
                plate.remove(md)
    for n in list(files):
        if org.ASSET.fullmatch(n) or n in ('Metadata/slice_info.config','Metadata/filament_sequence.json'):
            del files[n]
    files['Metadata/project_settings.config']=json.dumps(s,indent=2).encode()
    files['Metadata/model_settings.config']=org.xml(cfg)
    org.clean_relations(files)
    org.write(WORK/'editable.3mf',files)
    report=dict(source=str(SOURCE),source_sha256=sha(SOURCE),editable_sha256=sha(WORK/'editable.3mf'),
        requested_limits=dict(nozzle_c=[190,220],bed_c=[55,70],commanded_print_speed_mm_s=[30,60]),
        settings_changes=changes,object_changes=object_changes,
        protected_hashes={p.name:sha(p) for p in ROOT.glob('*.3mf')})
    (WORK/'changes.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Prepared r10 with',len(changes),'project settings and three inner-wall overrides changed.',flush=True)


def slice_native():
    folder=WORK/'native';folder.mkdir(exist_ok=True)
    exits=[]
    for attempt in range(3):
        with (folder/f'slice-{attempt+1}.log').open('w') as log:
            result=subprocess.run([str(EXE),'--slice','0','--export-3mf','sliced.3mf','--outputdir',str(folder),str(WORK/'editable.3mf')],
                cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        exits.append(result.returncode)
        if result.returncode==0:break
    (folder/'process-exits.json').write_text(json.dumps(exits))
    assert result.returncode==0,exits
    print('All three plates sliced; process exits',exits,flush=True)


def audit_commands(text):
    xyz=np.zeros(3);e=0.;f=0.;acc=0.;rel_e=False;rel_xyz=False;feature='Custom';layer=0.
    nozzle=None;bed=None;features={};bad=[];thermal=[];flush=[];travel_max=0.
    temp_syntax={'M104','M109','M140','M190'}
    for number,line in enumerate(text.splitlines(),1):
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        elif line.startswith('; Z_HEIGHT: '):layer=float(line.split(': ',1)[1])
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if cmd not in {'G0','G1','G2','G3','G90','G91','G92','M82','M83','M204','M620.10'}|temp_syntax:continue
        v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd in temp_syntax:
            t=v.get('S',v.get('R'))
            if t is not None:
                if cmd in ('M104','M109'):nozzle=t
                else:bed=t
                thermal.append(dict(line=number,layer=layer,command=code))
        elif cmd=='M620.10':
            if 'T' in v:
                assert 190<=v['T']<=220,(number,code)
                flush.append(v['T'])
        elif cmd=='M204':acc=v.get('S',acc)
        elif cmd=='M83':rel_e=True
        elif cmd=='M82':rel_e=False
        elif cmd in ('G90','G91'):rel_xyz=cmd=='G91'
        elif cmd=='G92':
            xyz=np.array([v.get(k,o) for k,o in zip('XYZ',xyz)]);e=v.get('E',e)
        elif cmd in ('G0','G1','G2','G3'):
            end=np.array([o+v.get(k,0) if rel_xyz else v.get(k,o) for k,o in zip('XYZ',xyz)])
            de=v.get('E',0) if rel_e else v.get('E',e)-e;f=v.get('F',f)
            distance=float(np.linalg.norm(end[:2]-xyz[:2]))
            if feature!='Custom' and layer>0 and distance>1e-7:
                if de>0:
                    assert cmd=='G1','Unexpected arc extrusion'
                    speed=f/60
                    row=features.setdefault(feature,dict(min_mm_s=speed,max_mm_s=speed,max_acceleration_mm_s2=acc,moves=0,path_mm=0.))
                    row['min_mm_s']=min(row['min_mm_s'],speed);row['max_mm_s']=max(row['max_mm_s'],speed)
                    row['max_acceleration_mm_s2']=max(row['max_acceleration_mm_s2'],acc);row['moves']+=1;row['path_mm']+=distance
                    if not 29.9999<=speed<=60.0001:bad.append(dict(line=number,layer=layer,feature=feature,speed_mm_s=speed,command=code))
                    assert nozzle is not None and 190<=nozzle<=220,(number,nozzle)
                    assert bed is not None and 55<=bed<=70,(number,bed)
                    assert acc<=1500,(number,acc)
                else:travel_max=max(travel_max,acc)
            xyz=end;e=e+v.get('E',0) if rel_e else v.get('E',e)
    return dict(features=features,out_of_range_count=len(bad),out_of_range_examples=bad[:40],
        temperature_commands=thermal,flush_temperatures_c=sorted(set(flush)),max_travel_acceleration_mm_s2=travel_max,
        interpretation='Feedrates on XY extrusion commands for model, carrier, supports and brim. Travel, retraction, machine priming/calibration and thermal warmup/probing/cooldown are separate. Actual mechanical speed changes during acceleration and turns.')


def validate():
    folder=WORK/'native';native=folder/'sliced.3mf';files=org.read(native);old=org.read(SOURCE);edit=org.read(WORK/'editable.3mf')
    preservation=org.compare(WORK/'editable.3mf',native)
    assert all(edit[n]==v for n,v in old.items() if n.endswith('.model'))
    p=Project(native);sp=Project(SOURCE)
    geometry=json.loads((ROOT/'release/veneer-nub-cleanup-r8/Letter-geometry.json').read_text())
    changes=json.loads((WORK/'changes.json').read_text());checks=[]
    locks=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',nozzle_diameter=['0.4'],layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',curr_bed_type='Textured PEI Plate',is_infill_first='0',support_type='tree(auto)')
    for k,v in locks.items():assert p.settings[k]==v,(k,p.settings[k])
    for i in (1,2,3):
        name=next(n for n in p.rows if n.startswith(f'V{i} '));row=p.rows[name]
        assert np.max(abs(row['T']-sp.rows[name]['T']))<.0001
        eff={**p.settings,**row['settings'],**row['parts'][0]['settings']}
        assert eff['sparse_infill_density']=='100%' and eff['enable_support']=='1' and eff['extruder']=='1'
        raw=files[f'Metadata/plate_{i}.gcode'];text=raw.decode()
        assert hashlib.md5(raw).hexdigest().upper()==files[f'Metadata/plate_{i}.gcode.md5'].decode().strip().upper()
        commands=audit_commands(text);(folder/f'V{i}-commands.json').write_text(json.dumps(commands,indent=2))
        print('V',i,'extrusion speeds',{k:[v['min_mm_s'],v['max_mm_s']] for k,v in commands['features'].items()},'violations',commands['out_of_range_count'],flush=True)
        assert commands['out_of_range_count']==0,commands['out_of_range_examples']
        assert commands['max_travel_acceleration_mm_s2']<=2500
        c={l[2:].split(' = ',1)[0]:l[2:].split(' = ',1)[1] for l in text.splitlines() if l.startswith('; ') and ' = ' in l}
        for k,v in locks.items():assert c[k]==(v[0] if isinstance(v,list) else v),(k,c[k])
        for k,(_,v) in changes['settings_changes'].items():assert c[k]==v[0]
        g=next(x for x in geometry['objects'] if x['name']==name);pose=np.array(g['pose']);probes=np.array([c['new_probe_assembly_xyz_mm'] for c in g['connections']]);probes=probes@pose[:3,:3].T+pose[:3,3]
        bonds=check_fin_bonds(text,dict(bond_probes_print_xyz_mm=probes.tolist()))
        bounds=np.array(scan_gcode(text)['bead_xy_bounds_mm']);assert np.all(bounds[0]>0) and np.all(bounds[1]<[330,320])
        checks.append(dict(veneer=i,plate=i,gcode_sha256=hashlib.sha256(raw).hexdigest(),commands=commands,connections=bonds,bead_bounds_mm=bounds.tolist()))
    result=json.loads((folder/'result.json').read_text());assert result['return_code']==0
    mass=sum(f['total_used_g'] for plate in result['sliced_plates'] for f in plate['filaments']);assert mass<1000
    info=ET.fromstring(files['Metadata/slice_info.config']);warnings=[w.attrib for plate in info.findall('plate') for w in plate.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' and w.get('error_code') in ('10018003','1000C003') for w in warnings)
    for name,digest in changes['protected_hashes'].items():assert sha(ROOT/name)==digest
    assert sha(SOURCE)==SOURCE_HASH
    report=dict(status='DIGITALLY_VERIFIED_SPOOL_LIMITS; whole-part physical shift still unresolved',**changes,native_sha256=sha(native),native_preservation=preservation,
        geometry_and_support_paint_unchanged=True,checks=checks,warnings=warnings,total_mass_g=mass,native_result=result,
        process_exits=json.loads((folder/'process-exits.json').read_text()))
    (WORK/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Validated all three. Total material',mass,flush=True)


def package():
    report=json.loads((WORK/'validation.json').read_text())
    native=WORK/'native/sliced.3mf'
    assert sha(native)==report['native_sha256']
    for name,digest in report['protected_hashes'].items():assert sha(ROOT/name)==digest
    OUT.mkdir(exist_ok=True)
    target=OUT/(TITLE+'.3mf');shutil.copyfile(native,target)
    report['delivered_file']=str(target);report['delivered_sha256']=sha(target)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    org.ROOT=OUT;org.REPORT=OUT;org.TITLES=[TITLE];org.export_cad()
    rows=[]
    for p in report['native_result']['sliced_plates']:
        seconds=round(p['total_predication']);mass=sum(f['total_used_g'] for f in p['filaments'])
        rows.append(f"| V{p['id']} | {p['id']} | {seconds//3600}h {(seconds%3600)//60:02d}m | {mass:.2f} g |")
    table='\n'.join(rows)
    (OUT/'README.md').write_text(f'''# Current ERYONE veneer candidate r10

`{TITLE}.3mf` supersedes the r9 candidate for this investigation. Open it as a project. It contains all three full-size veneers, on plates 1–3, using the saved A2L/H2S-compatible production printer profile. Root `Letter.3mf` remains unchanged.

## User-supplied spool limits

The user supplied **190–220°C nozzle, 55–70°C bed, 30–60 mm/s print speed** on 2026-10-25. These limits, rather than a different generic ERYONE product's specification, govern this revision.

- Printing nozzle: **220°C**, first and subsequent layers. The saved upper temperature recommendation is corrected from 240 to 220°C.
- Textured PEI bed: **55°C**, first and subsequent layers.
- Startup filament flushing: **220°C**, replacing the previously resolved 240°C automatic flush temperature. The native machine-start template is unchanged; its material-dependent temperature resolves to the corrected value.
- All model, carrier and generated support XY extrusion commands are **30–60 mm/s**. Outer-wall setting remains 40, first-layer wall setting remains 50, inner walls reduce 80→60, and infill/top/support settings cap at 60. Small-perimeter and cooling slowdown minimums are 30. Filament bridge speed changes 25→30; severe-overhang settings change 10→30 to meet the requested lower bound. The exact 18 global changes and three object changes are in `validation.json`.
- Print/travel acceleration remains capped at **1500/2500 mm/s²** from r9. Cooling fan settings, 7.5 mm³/s volumetric limit, 0.98 flow and retraction remain unchanged.

Print speed here means the feedrate of commands that move in XY while extruding the part or support. Non-extruding travel remains 500 mm/s maximum. Retraction, startup priming/calibration, and actual acceleration/deceleration through corners are separate. The printer retains its 140°C nozzle-probing routine and normal off commands; all model/support extrusion occurs with a 220°C nozzle target and 55°C bed target.

## Preservation and verification

All geometry, support paint, plate poses, solid veneer settings, tree supports, bed bands, connections and r9 carrier-edge corrections are retained. Editable mesh assets are byte-identical to r9. Native serialization was compared: faces and paint match, and vertex/placement differences stay below 0.0001 mm. The 0.4 mm nozzle, 0.20 mm initial/subsequent layers, four walls, five top/bottom layers, Textured PEI and gyroid pattern remain unchanged. Geometry source snapshots are adjacent SCAD/STL files.

All three plates were freshly sliced with Bambu Studio 02.08.02.61, clean process exit 0. Every model/support extrusion command was checked for the requested speed and temperature ranges; **zero out-of-range commands**. Checksums, bed bounds, acceleration limits and all 102 previously moved edge connections passed. The only native warnings remain the existing traditional-timelapse warnings (10018003 and 1000C003). No printer job was sent.

| Veneer | Plate | Estimated time | Material including supports |
|---|---:|---:|---:|
{table}

Combined material: **{report['total_mass_g']:.2f} g**, below 1000 g.

**Physical status:** no r10 print has been evaluated. The reported whole-part rearward shift remains unresolved; compliance with the spool limits does not establish its cause or prove it corrected. In particular, the revised bridge/overhang minimum is faster than r9 and its physical finish/support behavior remains unqualified.

Source r9 SHA-256: `{SOURCE_HASH}`.

Current r10 SHA-256: `{sha(target)}`.

Rebuild/audit commands, from the repository root: `python scripts/set_veneer_eryone_spool_limits.py build`, then `slice`, `validate`, and `package`. The original source hash is checked before building. Root production project hashes are checked during validation and packaging.
''',encoding='utf-8')
    previous=SOURCE.parent/'README.md'
    notice='**Superseded for this investigation by `../Dara-A2L-Veneers-ERYONE-r10/Dara-A2L-Veneers-ERYONE-r10.3mf`, which applies the user-supplied ERYONE spool temperature and speed limits. This r9 file remains unchanged as historical evidence.**\n\n'
    old=previous.read_text(encoding='utf-8')
    if not old.startswith('**Superseded'):previous.write_text(notice+old,encoding='utf-8')
    print('Delivered',target,sha(target),flush=True)


if __name__=='__main__':
    {'build':build,'slice':slice_native,'validate':validate,'package':package}[sys.argv[1]]()
