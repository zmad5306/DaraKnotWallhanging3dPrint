"""Native slice and checks for the saved r7 perimeter correction; no printing."""
import sys,json,subprocess,hashlib,shutil
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'.work/python-libs'),str(Path(__file__).parent)]
from correct_veneer_edge_connections import *
from validate_print_project import scan_gcode
from check_fin_toolpaths import check_fin_bonds
from check_a2l_towers import check_startup_tower
from shapely.geometry import MultiPoint
from organize_root_projects import compare
EXE=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
LOCKS=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',nozzle_diameter=['0.4'],
 layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',
 bottom_shell_layers='5',curr_bed_type='Textured PEI Plate',is_infill_first='0')
TARGETS={'Letter':WORK/'Letter-corrected.3mf','ERYONE-r4':SAMPLE_OUT/'Dara-A2L-Hammered-Finish-ERYONE-r4-Editable.3mf'}

def slice_one(title):
    out=WORK/('native-'+title);out.mkdir(exist_ok=True)
    for attempt in range(3):
        with (out/f'slice-{attempt+1}.log').open('w') as log:
            process=subprocess.run([str(EXE),'--slice','0','--export-3mf','sliced.3mf',
                '--outputdir',str(out),str(TARGETS[title])],cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
        if process.returncode!=3221225477:break
    assert process.returncode==0,(process.returncode,str(out/'slice.log'))
    print(title,(out/'result.json').read_text(),flush=True)

def validate(title):
    folder=WORK/('native-'+title);native=folder/'sliced.3mf';source=TARGETS[title]
    comparison=compare(source,native)
    p=Project(native);s=p.settings
    for k,v in LOCKS.items():assert s[k]==v,(title,k,s[k],v)
    assert s['printer_model']=='Bambu Lab A2L'
    geometry=json.loads((REPORT/(title+'-geometry.json')).read_text())
    checks=[];warnings=[]
    info=ET.fromstring(p.z.read('Metadata/slice_info.config'))
    for plate in info.findall('plate'):
        warnings.extend([w.attrib for w in plate.findall('warning')])
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    for row in geometry['objects']:
        number=row['plate'];raw=p.z.read(f'Metadata/plate_{number}.gcode');text=raw.decode()
        assert hashlib.md5(raw).hexdigest().upper()==p.z.read(f'Metadata/plate_{number}.gcode.md5').decode().strip().upper()
        config={line[2:].split(' = ',1)[0]:line[2:].split(' = ',1)[1] for line in text.splitlines() if line.startswith('; ') and ' = ' in line}
        for k,v in LOCKS.items():
            if k=='nozzle_diameter':v=v[0]
            assert config[k]==v,(k,config.get(k),v)
        r=p.rows[row['name']];part=r['parts'][0]
        effective={**s,**r['settings'],**part['settings']}
        assert effective['sparse_infill_density']=='100%' and effective['sparse_infill_pattern']=='gyroid'
        assert effective['enable_support']=='1' and effective['support_type']=='tree(auto)' and effective['extruder']=='3'
        pose=np.array(row['pose']);probes=np.array([c['new_probe_assembly_xyz_mm'] for c in row['connections']])
        probes=probes@pose[:3,:3].T+pose[:3,3]
        bonds=check_fin_bonds(text,dict(bond_probes_print_xyz_mm=probes.tolist()))
        scan=scan_gcode(text);bounds=np.array(scan['bead_xy_bounds_mm'])
        margin=min(bounds[0].min(),*(np.array([330,320])-bounds[1]))
        assert margin>.5
        m=part['mesh'].copy();m.apply_transform(r['T'])
        tower=check_startup_tower(s,[MultiPoint(m.vertices[:,:2]).convex_hull],1,float(m.bounds[1,2]),number)
        checks.append(dict(plate=number,gcode_sha256=hashlib.sha256(raw).hexdigest(),md5_verified=True,
            new_connections_model_toolpaths=bonds,conservative_bed_clearance_mm=float(margin),tower=tower))
    result=json.loads((folder/'result.json').read_text());assert result['return_code']==0
    veneer_mass=sum(f['total_used_g'] for plate in result['sliced_plates']
        if title!='Letter' or plate['id']>=4 for f in plate['filaments'])
    if title=='Letter':assert veneer_mass<1000
    core_bounds=[]
    if title=='Letter':
        for number in (1,2,3):
            bounds=np.array(scan_gcode(p.z.read(f'Metadata/plate_{number}.gcode').decode())['bead_xy_bounds_mm'])
            assert np.all(bounds[0]>0) and np.all(bounds[1]<[330,320])
            core_bounds.append(dict(plate=number,bead_xy_bounds_mm=bounds.tolist()))
    (REPORT/(title+'-native.json')).write_text(json.dumps(dict(source_sha256=sha(source),native_sha256=sha(native),
        preservation=comparison,warnings=warnings,plates=checks,slicer_result=result,
        veneer_and_support_material_g=veneer_mass,core_toolpath_bounds=core_bounds,
        physical_validation_pending=True),indent=2)+'\n')
    print(title,'validated',flush=True)

if __name__=='__main__':
    action,title=sys.argv[1:]
    {'slice':slice_one,'validate':validate}[action](title)
