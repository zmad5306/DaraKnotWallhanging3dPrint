"""Copy A1-sized parts of the coordinated A2L design into an A1 print project.

Meshes and matching hardware are taken from the current A2L release, not the
historical A1 design. Only flat part poses and the printer profiles change.
"""
import argparse,copy,json,math,shutil,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,box
from shapely import affinity
from development_3mf import ROOT,sha,save_json,read_object,write_project,centered,z_rotation,tag,transform,props
from build_a2l_project import resolved_profile,PROFILE
from validate_print_project import scan_gcode

OUT=ROOT/'working/bambu/Dara-A1-Companion'
SOURCE=ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf'
A2L=ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf'
EDIT=OUT/'Dara-A1-Companion-Editable.3mf'
FINAL=OUT/'Dara-A1-Companion.3mf'
SOURCE_PLATES=[18,19,20]


def files(path):
    with zipfile.ZipFile(path) as z:return {n:z.read(n) for n in z.namelist()}


def a1_settings():
    old=files(ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf')
    s=json.loads(old['Metadata/project_settings.config'])
    s.update(resolved_profile('machine','Bambu Lab A1 0.4 nozzle'))
    s.update(resolved_profile('process','0.20mm Standard @BBL A1'))
    names=['Generic PLA @BBL A1','Generic PLA @BBL A1','Generic PLA Silk @BBL A1','Generic PLA @BBL A1']
    fil=[resolved_profile('filament',name) for name in names]
    for key in set().union(*(f.keys() for f in fil)):
        values=[f.get(key) for f in fil]
        if all(isinstance(v,list) and len(v)==1 for v in values):s[key]=[v[0] for v in values]
    s.update(printer_settings_id='Bambu Lab A1 0.4 nozzle',printer_model='Bambu Lab A1',printer_variant='0.4',
        print_compatible_printers=['Bambu Lab A1 0.4 nozzle'],print_settings_id='Dara A1 companion - 8% gyroid',
        filament_settings_id=names,filament_colour=['#FFFFFF','#C2AB84','#B87333','#295D8A'],
        layer_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',sparse_infill_density='8%',
        sparse_infill_pattern='gyroid',print_sequence='by layer',enable_prime_tower='0',enable_arc_fitting='0',
        curr_bed_type='Textured PEI Plate',support_type='tree(auto)',support_style='default',enable_support='0',
        raft_first_layer_expansion='0',wipe_tower_x=['10']*3,wipe_tower_y=['10']*3)
    s['textured_plate_temp']=['65','65','55','65'];s['textured_plate_temp_initial_layer']=s['textured_plate_temp']
    s['filament_max_volumetric_speed']=['12','12','7.5','7.5']
    assert s['printable_area']==['0x0','256x0','256x256','0x256'] and s['printable_height']=='256'
    return s


def build():
    OUT.mkdir(parents=True,exist_ok=True);src=files(SOURCE);cfg=ET.fromstring(src['Metadata/model_settings.config'])
    byname={props(co)['name']:co.get('id') for co in cfg.findall('object')};plates=[];mapping=[]
    def entry(name,xy,yaw=0):
        parts,st=read_object(src,byname[name]);st={k:v for k,v in st.items() if k not in [None,'name']}
        st.update(sparse_infill_density='8%',sparse_infill_pattern='gyroid',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5')
        return dict(name=name.replace('A2L','A1 companion'),parts=parts,settings=st,transform=centered(parts[0]['mesh'],z_rotation(yaw),xy=xy))
    for group in [[3,1,5,7],[4,2,6,8]]:
        objects=[]
        for corner,k in enumerate(group):
            e=entry(f'Backer{k}',(128,128));m=e['parts'][0]['mesh'];low,high=m.bounds[:,:2]
            T=np.eye(4);T[2,3]=-m.bounds[0,2]
            T[:2,3]=[256-1.5-high[0] if corner&1 else 1.5-low[0],256-1.5-high[1] if corner&2 else 1.5-low[1]]
            e['transform']=T;e['settings'].update(brim_width='0',enable_support='0');objects.append(e)
        plates.append(objects)
    hardware=[]
    for k in range(1,5):
        e=entry(f'B{k} A2L wall block',(84,55+48*(k-1)));e['settings'].update(brim_width='1',enable_support='1',support_on_build_plate_only='0');hardware.append(e)
    for k in range(1,33):
        j=k-1;e=entry(f'R{k} photo retainer',(179+26*(j%3),48+16*(j//3)));e['settings'].update(brim_width='0',enable_support='0');hardware.append(e)
    plates.append(hardware)
    for pi,objects in enumerate(plates):
        footprints=[]
        for e in objects:
            m=e['parts'][0]['mesh'];T=e['transform'];v=m.vertices@T[:3,:3].T+T[:3,3]
            assert m.is_volume and np.all(v.min(axis=0)>=[1.49,1.49,-.001]) and np.all(v.max(axis=0)<=[254.51,254.51,256]),(e['name'],v.min(axis=0),v.max(axis=0))
            # A conservative projected hull check includes brim allowance;
            # these grouped plates use sparse packing, without interlocking.
            g=Polygon(v[:,:2]).convex_hull;footprints.append(g)
            mapping.append(dict(name=e['name'],A1_plate=pi+1,A2L_plate=SOURCE_PLATES[pi],source_name=e['name'].replace('A1 companion','A2L'),
                source_object_id=byname[e['name'].replace('A1 companion','A2L')],source_part_count=len(e['parts'])))
        gap=1.5 if pi<2 else 4
        for i,g in enumerate(footprints):
            for q in footprints[:i]:assert g.distance(q)>=gap-.01,(pi+1,g.distance(q))
    records=write_project(EDIT,plates,'Dara A1 companion - A2L matching backers and hardware',settings_update=a1_settings())
    assert len(records)==44 and len(plates)==3
    save_json(OUT/'companion-plan.json',dict(source_A2L_editable_sha256=sha(SOURCE),source_A2L_complete_sha256=sha(A2L),editable_sha256=sha(EDIT),
        plates=3,pieces=44,source_A2L_plates=SOURCE_PLATES,records=records,mapping=mapping,
        printing_assignment=dict(A1='All three companion plates',A2L='Original complete project plates 1-17, including every M core and veneer',skip_A2L_plates=SOURCE_PLATES),
        layer_height_mm=.2,body_infill='8% gyroid',filament_slots=dict(white=1,copper_silk=3),prime_tower_disabled=True))
    print('Built three A1 plates / 44 matching A2L-design parts',flush=True)


def geometry(path):
    f=files(path);cfg=ET.fromstring(f['Metadata/model_settings.config']);root=ET.fromstring(f['3D/3dmodel.model']);out={};plates=cfg.findall('plate');cols=math.ceil(math.sqrt(len(plates)))
    for pi,plate in enumerate(plates):
        for inst in plate.findall('model_instance'):
            oid=props(inst)['object_id'];parts,st=read_object(f,oid);it=root.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']");T=transform(it.get('transform'));T[:2,3]-=[pi%cols*307.2,-(pi//cols)*307.2]
            points=np.concatenate([p['mesh'].vertices@T[:3,:3].T+T[:3,3] for p in parts])
            out[st['name']]=dict(parts=parts,settings=st,points=points,T=T,plate=pi+1)
    return f,out


def validate(native):
    result=json.loads((native/'result.json').read_text());assert result['return_code']==0,result
    plan=json.loads((OUT/'companion-plan.json').read_text());assert sha(EDIT)==plan['editable_sha256'] and sha(A2L)==plan['source_A2L_complete_sha256']
    sf,src=geometry(EDIT);nf,dst=geometry(native/'sliced.3mf');source=files(SOURCE);roundtrip=[];preserved=[]
    assert src.keys()==dst.keys() and len(src)==44
    for row in plan['mapping']:
        name=row['name'];parts,st=read_object(source,row['source_object_id']);actual=src[name]['parts'];assert len(parts)==len(actual)
        errors=[]
        for old,new in zip(parts,actual):
            assert old['subtype']==new['subtype']
            a,b=old['mesh'].vertices,new['mesh'].vertices
            error=max(cKDTree(a).query(b)[0].max(),cKDTree(b).query(a)[0].max());assert error<.00001,(name,error);errors.append(float(error))
        preserved.append(dict(name=name,max_source_geometry_error_mm=max(errors),all_model_and_modifier_meshes_checked=True))
        a,b=src[name]['points'],dst[name]['points'];error=max(cKDTree(a).query(b)[0].max(),cKDTree(b).query(a)[0].max());assert error<.001,(name,error)
        roundtrip.append(dict(name=name,max_native_geometry_or_pose_error_mm=float(error)))
        assert src[name]['settings']['sparse_infill_density']=='8%'
        for part in src[name]['parts'][1:]:
            if part['settings'].get('sparse_infill_density'):assert part['settings']['sparse_infill_density']=='100%'
    settings=json.loads(nf['Metadata/project_settings.config']);assert settings['printer_model']=='Bambu Lab A1'
    assert settings['enable_prime_tower']=='0' and settings['sparse_infill_density']=='8%'
    machine=resolved_profile('machine','Bambu Lab A1 0.4 nozzle')
    command_keys=['machine_start_gcode','machine_end_gcode','change_filament_gcode','layer_change_gcode','time_lapse_gcode']
    for key in command_keys:assert settings[key]==machine[key],key
    gcodes=sorted(native.glob('plate_*.gcode'),key=lambda p:int(p.stem.split('_')[-1]));assert len(gcodes)==3;rows=[]
    for pi,file in enumerate(gcodes,1):
        text=file.read_text();r=scan_gcode(text);assert r['conservative_bed_edge_clearance_mm']>.5,(pi,r['bead_xy_bounds_mm'])
        assert '; EXECUTABLE_BLOCK_END' in text and '; printer_model = Bambu Lab A1' in text
        assert not r['features'].get('Prime tower',0)
        if pi!=3:assert not any(r['features'].get(k,0) for k in ['Support','Support interface'])
        model_slots=set(r['model_extrusion_z_by_filament_mm']);assert model_slots==({'1'} if pi<=3 else {'3'}),(pi,model_slots)
        estimate=next(e for e in result['sliced_plates'] if e['id']==pi)
        r.update(plate=pi,gcode_sha256=sha(file),seconds=estimate['total_predication'],weight_g=sum(f['total_used_g'] for f in estimate['filaments']))
        rows.append(r);print('A1 plate',pi,'passed:',round(r['conservative_bed_edge_clearance_mm'],3),'mm bed clearance',flush=True)
    save_json(OUT/'native-validation.json',dict(source_A2L_complete_sha256=sha(A2L),source_A2L_editable_sha256=sha(SOURCE),editable_sha256=sha(EDIT),native_sha256=sha(native/'sliced.3mf'),
        native_return_code=0,plates=rows,source_geometry_preservation=preserved,native_roundtrip=roundtrip,
        printer_command_profiles_verified=command_keys,slicer_result=result,physical_confirmation_pending=True))


def publish(native,reopen):
    r=json.loads((OUT/'native-validation.json').read_text());info=json.loads((reopen/'result.json').read_text())
    assert info['return_code']==r['native_return_code']==0 and sha(native/'sliced.3mf')==r['native_sha256'] and sha(EDIT)==r['editable_sha256']
    assert (reopen/'result.json').stat().st_mtime>=(native/'sliced.3mf').stat().st_mtime
    shutil.copyfile(native/'sliced.3mf',FINAL)
    evidence=[EDIT,OUT/'companion-plan.json',OUT/'native-validation.json',ROOT/'scripts/build_a1_companion.py',ROOT/'scripts/audit_a1_companion.py']
    save_json(OUT/'release-validation.json',dict(project_sha256=sha(FINAL),editable_sha256=sha(EDIT),source_A2L_complete_sha256=sha(A2L),pieces=44,plates=3,
        native_reopen_return_code=0,evidence_sha256={str(p.relative_to(ROOT)):sha(p) for p in evidence},
        plate_estimates=[dict(plate=p['plate'],seconds=p['seconds'],weight_g=p['weight_g']) for p in r['plates']],physical_confirmation_pending=True))
    print(FINAL,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','validate','publish']);p.add_argument('native',nargs='?',type=Path);p.add_argument('reopen',nargs='?',type=Path);a=p.parse_args()
    if a.action=='build':build()
    elif a.action=='validate':validate(a.native)
    else:publish(a.native,a.reopen)
