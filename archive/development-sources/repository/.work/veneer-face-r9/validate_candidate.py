import sys,json,pickle,hashlib,zipfile,copy
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path[:0]=['.work/python-libs','scripts']
import numpy as np
from validate_production_split import Project
from development_3mf import sha
from check_veneer_layer_overlap import parse
from check_fin_toolpaths import check_fin_bonds
from validate_print_project import scan_gcode
import organize_root_projects as org
ROOT=Path.cwd();WORK=ROOT/'.work/veneer-face-r9';out=WORK/'native-veneers-r9';native=out/'sliced.3mf';editable=WORK/'Letter-veneers-r9-editable.3mf';source=WORK/'Letter-before.3mf'
assert sha(ROOT/'Letter.3mf')==sha(source)
native_compare=org.compare(editable,native)
p=Project(native);old=Project(source);ed=Project(editable)
expected=json.loads((WORK/'candidate-settings.json').read_text())['changed_settings']
settings_changes={k:[old.settings.get(k),ed.settings.get(k)] for k in set(old.settings)|set(ed.settings) if old.settings.get(k)!=ed.settings.get(k)}
assert set(settings_changes)==set(expected)|{'wipe_tower_x','wipe_tower_y'}
assert all(settings_changes[k]==v for k,v in expected.items())
locks=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',nozzle_diameter=['0.4'],layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',curr_bed_type='Textured PEI Plate',is_infill_first='0',support_type='tree(auto)')
for k,v in locks.items():assert p.settings[k]==v,(k,p.settings[k],v)
assert p.settings['printer_model']=='Bambu Lab A2L'
checks=[];geom=json.loads((ROOT/'release/veneer-nub-cleanup-r8/Letter-geometry.json').read_text());info=ET.fromstring(p.z.read('Metadata/slice_info.config'))
warnings=[w.attrib for plate in info.findall('plate') for w in plate.findall('warning')]
assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
for i in (1,2,3):
 name=next(n for n in p.rows if n.startswith(f'V{i} '));row=p.rows[name];before=old.rows[name]
 assert row['settings']==before['settings'];assert np.max(abs(row['T']-before['T']))<.0001
 eff={**p.settings,**row['settings'],**row['parts'][0]['settings']}
 assert eff['sparse_infill_density']=='100%' and eff['enable_support']=='1' and eff['extruder']=='1'
 raw=p.z.read(f'Metadata/plate_{i}.gcode');text=raw.decode();(out/f'V{i}.gcode').write_bytes(raw)
 assert hashlib.md5(raw).hexdigest().upper()==p.z.read(f'Metadata/plate_{i}.gcode.md5').decode().strip().upper()
 c={line[2:].split(' = ',1)[0]:line[2:].split(' = ',1)[1] for line in text.splitlines() if line.startswith('; ') and ' = ' in line}
 for k,v in locks.items():assert c[k]==(v[0] if isinstance(v,list) else v)
 for k,(_,v) in expected.items():assert c[k]==v[0],(k,c[k])
 geometry=next(g for g in geom['objects'] if g['name']==name);pose=np.array(geometry['pose']);probes=np.array([g['new_probe_assembly_xyz_mm'] for g in geometry['connections']]);probes=probes@pose[:3,:3].T+pose[:3,3]
 bonds=check_fin_bonds(text,dict(bond_probes_print_xyz_mm=probes.tolist()))
 scan=scan_gcode(text);bounds=np.array(scan['bead_xy_bounds_mm']);assert np.all(bounds[0]>0) and np.all(bounds[1]<[330,320])
 mod,sup=parse(text);(out/f'V{i}-parsed.pkl').write_bytes(pickle.dumps((mod,sup)))
 checks.append(dict(veneer=i,plate=i,gcode_sha256=hashlib.sha256(raw).hexdigest(),md5_verified=True,bed_bounds_mm=bounds.tolist(),connections=bonds,model_layers=len(mod),support_layers=len(sup),saved_rotation_and_position_preserved=True))
 print('validated geometry/settings/bonds V',i,flush=True)
result=json.loads((out/'result.json').read_text());assert result['return_code']==0
mass=sum(f['total_used_g'] for plate in result['sliced_plates'] for f in plate['filaments']);assert mass<1000
report=dict(status='DIGITAL_CANDIDATE; physical whole-part shift not proven resolved',source=str(source),source_sha256=sha(source),native_sha256=sha(native),native_process_exits=json.loads((out/'process-exits.json').read_text()),native_comparison=native_compare,settings_changes=settings_changes,checks=checks,warnings=warnings,total_mass_g=mass,native_result=result)
(out/'validation.json').write_text(json.dumps(report,indent=2))
print('mass',mass,flush=True)
