"""Package the fresh parametric bucket and front logo for A2L / SUNLU PLA+ 2.0.

The STL and logo are exported by OpenSCAD from Bucket.scad. Geometry comparisons
use the accepted-r3.scad reference; no earlier remixed mesh is a geometry input.
Requires the repository's trimesh/manifold3d geometry dependencies and Bambu CLI.
"""
from pathlib import Path
import copy, hashlib, json, re, shutil, subprocess, sys, time, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REF=OUT/'reference'
WORK=ROOT/'.work/a2l-bucket-fresh-release'
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from development_3mf import solid, mesh, mesh_xml
from build_jointed_bambu_project import C,P,R,IDENTITY,tag,xml,model,meta
from validate_print_project import scan_gcode, transform

FINAL=OUT/'A2L-Poop-Bucket-SUNLU-PLA-Plus-2.0.3mf'
PROFILE='SUNLU PLA+ 2.0 @Bambu Lab A2L 0.4 nozzle (project)'
COLORS=['#555555','#00CC00']
TITLE='A2L poop bucket - gray body / green Bambu mark - SUNLU PLA+ 2.0'
PLACEMENT=np.array([101.,32.7,0.])

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def jsave(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def package(p):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        return {n:z.read(n) for n in z.namelist()}
def save(p,files):
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
        for n,d in files.items():z.writestr(n,d)
def vol_diff(a,b):return abs((a-b).volume())+abs((b-a).volume())
def mesh_error(a,b):
    return float(max(cKDTree(a.vertices).query(b.vertices)[0].max(),cKDTree(b.vertices).query(a.vertices)[0].max()))
def native(src,directory,export=False):
    directory.mkdir(parents=True,exist_ok=True)
    exe=Path('C:/Program Files/Bambu Studio/bambu-studio.exe')
    args=[str(exe),'--debug','5','--slice','1']
    if export:args+=['--export-3mf','sliced.3mf']
    args+=['--outputdir',str(directory),str(src)]
    codes=[]
    for i in range(3):
        with (directory/f'native-{i+1}.log').open('w',encoding='utf8') as f:
            p=subprocess.run(args,cwd=exe.parent,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        codes.append(p.returncode)
        if p.returncode==0:break
        if p.returncode!=3221225477:break
        time.sleep(1)
    assert p.returncode==0,(codes,str(directory))
    result=json.loads((directory/'result.json').read_text())
    assert result['return_code']==0 and len(result['sliced_plates'])==1
    assert result['sliced_plates'][0]['warning_message']==''
    result['native_launch_exit_codes']=codes
    return result

def render_inputs(force=False):
    """Recreate missing CAD inputs without needing historical local outputs."""
    exe=Path('C:/Program Files (x86)/OpenSCAD/openscad.exe')
    exports=[(REF/'accepted-r3.scad',WORK/'accepted-r3.stl',None),
             (OUT/'Bucket.scad',OUT/'Bucket.stl','SingleColor'),
             (OUT/'Bucket.scad',OUT/'Green-Logo.stl','GreenLogo')]
    for source,target,mode in exports:
        if target.exists() and not force:continue
        args=[str(exe),'--hardwarnings','--export-format','binstl']
        if mode:args+=['-D',f'view_mode="{mode}"']
        args+=['-o',str(target),str(source)]
        with (WORK/(target.stem+'-render.log')).open('w') as log:
            p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        assert p.returncode==0

def configuration():
    source=json.loads((REF/'a2l-settings-source.json').read_text())
    cfg=copy.deepcopy(source)
    plus=json.loads((REF/'SUNLU-PLA-Plus-2-source.json').read_text())
    a2l=json.loads((REF/'SUNLU-A2L-machine-source.json').read_text())
    profile=copy.deepcopy(plus)
    # Retain A2L-specific start/flush/cooling/retraction behavior. Material flow,
    # density, speed and temperature values come from the installed SUNLU preset.
    machine_keys=['filament_start_gcode','filament_flush_temp_fast','pre_start_fan_time',
                  'overhang_fan_threshold','eng_plate_temp','eng_plate_temp_initial_layer',
                  'filament_long_retractions_when_cut','filament_retraction_distances_when_cut']
    for k in machine_keys:profile[k]=a2l[k]
    profile.update(name=PROFILE,filament_settings_id=[PROFILE],filament_id='GFSNL04',
                   compatible_printers=['Bambu Lab A2L 0.4 nozzle'],default_filament_colour=[''],
                   filament_notes='Project adaptation of installed SUNLU PLA+ 2.0 settings to the saved A2L machine behavior. Gray and green use identical parameters; no new calibration is implied.')
    for k in ['filament_flow_ratio','impact_strength_z','filament_dev_chamber_drying_time']:
        profile[k]=[format(float(v),'g') for v in profile[k]]
    jsave(REF/'SUNLU-PLA-Plus-2-A2L-project.json',profile)
    # Expand the single-color template's per-filament values, including newer
    # fields absent from the older user preset. No machine/process arrays expand.
    for k,v in list(cfg.items()):
        if k.startswith('filament_') and isinstance(v,list) and len(v)==1:cfg[k]=v*2
    excluded={'name','inherits','from','version','filament_id','compatible_printers',
              'compatible_printers_condition','compatible_prints','compatible_prints_condition'}
    for k,v in profile.items():
        if k in excluded:continue
        cfg[k]=v*2 if isinstance(v,list) else v
    cfg.update(filament_colour=COLORS,filament_multi_colour=COLORS,
               filament_colour_type=['1','1'],filament_ids=['GFSNL04','GFSNL04'],
               filament_map=['1','1'],filament_nozzle_map=['0','0'],filament_volume_map=['0','0'],
               filament_diameter_map=['0.4','0.4'],filament_settings_id=[PROFILE,PROFILE],
               print_settings_id='Fresh A2L bucket - 0.20 mm - 8% gyroid - tree supports',
               layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',
               top_shell_layers='5',bottom_shell_layers='5',sparse_infill_density='8%',
               sparse_infill_pattern='gyroid',enable_support='1',support_type='tree(auto)',
               support_style='default',enable_prime_tower='1',wipe_tower_x=['25'],wipe_tower_y=['235'],
               flush_volumes_matrix=['0','280','280','0'],flush_volumes_vector=['140']*4,
               filament_map_2=['1'],inherits_group=['','','',''],different_settings_to_system=['','','',''])
    locked_keys=['printer_model','printer_settings_id','printer_variant','nozzle_diameter',
                 'printable_area','printable_height','layer_height','initial_layer_print_height',
                 'wall_loops','top_shell_layers','bottom_shell_layers','sparse_infill_density',
                 'sparse_infill_pattern','curr_bed_type','enable_support','support_type','support_style',
                 'enable_prime_tower','brim_type','filament_colour','filament_ids','filament_settings_id',
                 'nozzle_temperature','nozzle_temperature_initial_layer','textured_plate_temp',
                 'textured_plate_temp_initial_layer','filament_flow_ratio','filament_max_volumetric_speed']
    locked={k:cfg[k] for k in locked_keys}
    changes={k:{'source':source.get(k),'saved':v} for k,v in cfg.items() if source.get(k)!=v}
    return cfg,locked,changes,machine_keys

def make_project(body,logo,cfg):
    child=model();res=ET.SubElement(child,tag('resources'))
    mesh_xml(res,1,body);mesh_xml(res,2,logo)
    root=ET.Element(tag('model'),unit='millimeter',requiredextensions='p',attrib={'{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    for k,v in [('Application','BambuStudio-02.09.01.70'),('BambuStudio:3mfVersion','1'),
                ('Title',TITLE),('Description','Fresh parametric A2L purge bucket with triangular front, full-height back, sloped pillar wall, catch chute and green Bambu mark.')]:
        ET.SubElement(root,tag('metadata'),name=k).text=v
    rr=ET.SubElement(root,tag('resources'));obj=ET.SubElement(rr,tag('object'),id='3',type='model')
    comps=ET.SubElement(obj,tag('components'))
    for oid in (1,2):ET.SubElement(comps,tag('component'),objectid=str(oid),transform=IDENTITY,attrib={'{'+P+'}path':'/3D/Objects/object_1.model'})
    pose='1 0 0 0 1 0 0 0 1 '+' '.join(map(str,PLACEMENT))
    ET.SubElement(ET.SubElement(root,tag('build')),tag('item'),objectid='3',transform=pose,printable='1')
    settings=ET.Element('config');o=ET.SubElement(settings,'object',id='3')
    meta(o,'name','A2L poop bucket');meta(o,'extruder','1')
    for oid,name,tm in [(1,'Gray bucket body',body),(2,'Green Bambu front logo',logo)]:
        part=ET.SubElement(o,'part',id=str(oid),subtype='normal_part')
        meta(part,'name',name);meta(part,'extruder',oid)
        meta(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        ET.SubElement(part,'mesh_stat',face_count=str(len(tm.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
    plate=ET.SubElement(settings,'plate')
    for k,v in [('plater_id',1),('plater_name','A2L bucket - gray and green PLA+ 2.0'),('locked','false'),
                ('filament_map_mode','Auto For Flush'),('filament_maps','1 1'),('filament_volume_maps','0 0')]:meta(plate,k,v)
    inst=ET.SubElement(plate,'model_instance')
    for k,v in [('object_id',3),('instance_id',0),('identify_id',100)]:meta(inst,k,v)
    assemble=ET.SubElement(settings,'assemble')
    ET.SubElement(assemble,'assemble_item',object_id='3',instance_id='0',transform=pose,offset='0 0 0')
    rels=ET.Element('Relationships',xmlns=R);crels=ET.Element('Relationships',xmlns=R)
    rt='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
    ET.SubElement(rels,'Relationship',Target='/3D/3dmodel.model',Id='rel-1',Type=rt)
    ET.SubElement(crels,'Relationship',Target='/3D/Objects/object_1.model',Id='rel-2',Type=rt)
    types=ET.Element('Types',xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
    for ext,typ in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('model','application/vnd.ms-package.3dmanufacturing-3dmodel+xml'),('config','application/octet-stream')]:
        ET.SubElement(types,'Default',Extension=ext,ContentType=typ)
    return {'[Content_Types].xml':xml(types),'_rels/.rels':xml(rels),'3D/_rels/3dmodel.model.rels':xml(crels),
            '3D/3dmodel.model':xml(root),'3D/Objects/object_1.model':xml(child),
            'Metadata/model_settings.config':xml(settings),'Metadata/project_settings.config':json.dumps(cfg,indent=2).encode()}

def saved_parts(files):
    root=ET.fromstring(files['3D/3dmodel.model'])
    item=root.find(tag('build')+'/'+tag('item'))
    assembly=root.find(tag('resources')+'/'+tag('object'))
    result=[]
    for co in assembly.findall(tag('components')+'/'+tag('component')):
        child=ET.fromstring(files[co.get('{'+P+'}path').lstrip('/')])
        o=child.find(tag('resources')+'/'+tag('object')+f"[@id='{co.get('objectid')}']")
        v=np.array([[float(e.get(k)) for k in ('x','y','z')] for e in o.findall('.//'+tag('vertex'))])
        f=np.array([[int(e.get(k)) for k in ('v1','v2','v3')] for e in o.findall('.//'+tag('triangle'))])
        t=transform(item.get('transform'))@transform(co.get('transform'))
        result.append(trimesh.Trimesh(v@t[:3,:3].T+t[:3,3],f,process=True))
    return result

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    if not (WORK/'protected-before.json').exists():
        protected=list(ROOT.glob('*.3mf'))+list((ROOT/'accessories/A2L-Poop-Bucket').glob('*.3mf'))
        protected += [ROOT/'accessories/A2L-Poop-Bucket/Bucket.scad',ROOT/'accessories/A2L-Poop-Bucket/Bucket.stl']
        jsave(WORK/'protected-before.json',{rel(p):sha(p) for p in protected})
    before=json.loads((WORK/'protected-before.json').read_text())
    render_inputs('--render' in sys.argv)
    # R3 is freshly exportable from its archived parametric source.
    accepted=trimesh.load(WORK/'accepted-r3.stl',force='mesh')
    full=trimesh.load(OUT/'Bucket.stl',force='mesh')
    logo=trimesh.load(OUT/'Green-Logo.stl',force='mesh')
    a,l,f=map(solid,[accepted,logo,full])
    assert accepted.is_volume and full.is_volume and len(full.split())==1
    assert len(logo.split())==4 and logo.is_volume
    assert vol_diff(a+l,f)<0.02
    assert (a-f).volume()<0.01, 'Body material was removed beyond the color split'
    body=mesh(a-l)
    body.export(OUT/'Gray-Body.stl')
    overlap=(solid(body)^l).volume()
    assert abs(overlap)<0.001
    assert vol_diff(solid(body)+l,f)<0.02
    cfg,locked,changes,machine_keys=configuration()
    files=make_project(body,logo,cfg);editable=WORK/'editable.3mf';save(editable,files)
    print('Fresh body and logo verified. Checking A2L with gray / green SUNLU PLA+ 2.0.',flush=True)
    if '--verify-existing' in sys.argv:
        result=json.loads((WORK/'slice/result.json').read_text())
        assert result['return_code']==0
    else:result=native(editable,WORK/'slice',True)
    candidate=WORK/'slice/sliced.3mf';sliced=package(candidate)
    settings=json.loads(sliced['Metadata/project_settings.config'])
    assert settings==cfg, 'Native export changed configuration'
    for k,v in locked.items():assert settings[k]==v,(k,settings[k],v)
    expected=saved_parts(files);saved=saved_parts(sliced)
    assert len(saved)==2
    errors=[mesh_error(e,s) for e,s in zip(expected,saved)]
    assert max(errors)<0.0001 and all(s.is_volume for s in saved)
    object_cfg=ET.fromstring(sliced['Metadata/model_settings.config'])
    parts=object_cfg.findall('object/part')
    assert len(parts)==2
    assignments=[{m.get('key'):m.get('value') for m in p.findall('metadata')}.get('extruder') for p in parts]
    assert assignments==['1','2'],assignments
    gc=sliced['Metadata/plate_1.gcode'].decode()
    gcfg=dict(re.findall(r'^; (\w+) = (.*)$',gc,re.M))
    for k in ['layer_height','initial_layer_print_height','wall_loops','top_shell_layers','bottom_shell_layers',
              'sparse_infill_density','sparse_infill_pattern','curr_bed_type','enable_support','support_type','support_style']:
        assert gcfg[k]==locked[k],(k,gcfg.get(k),locked[k])
    assert PROFILE in gcfg['filament_settings_id']
    assert re.search(r'^\s*M(?:140|190) S65\b',gc,re.M)
    assert re.search(r'^\s*M(?:104|109) S220\b',gc,re.M)
    checksum=hashlib.md5(sliced['Metadata/plate_1.gcode']).hexdigest()
    assert sliced['Metadata/plate_1.gcode.md5'].decode().strip().lower()==checksum
    audit=scan_gcode(gc)
    low,high=audit['bead_xy_bounds_mm']
    audit['bed_size_mm']=[330,320]
    audit['conservative_bed_edge_clearance_mm']=min(*low,330-high[0],320-high[1])
    assert audit['conservative_bed_edge_clearance_mm']>3
    assert audit['features'].get('Support',0)>0
    assert result['sliced_plates'][0]['times']['support_tree_generate_time']>0
    assert result['sliced_plates'][0]['times']['support_normal_generate_time']==0
    assert audit['features'].get('Prime tower',0)>0
    zs=audit['model_extrusion_z_by_filament_mm']
    assert set(zs)=={'1','2'} and min(zs['2'])>=40 and max(zs['2'])<=72.001
    assert len(zs['2'])>=150
    info=ET.fromstring(sliced['Metadata/slice_info.config'])
    warnings=[e.attrib for e in info.findall('plate/warning')]
    assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
    for element in info.findall('plate/filament'):assert element.get('tray_info_idx')=='GFSNL04'
    shutil.copyfile(candidate,FINAL)
    if 'Metadata/plate_1.png' in sliced:(OUT/'native-preview.png').write_bytes(sliced['Metadata/plate_1.png'])
    print('Native two-color slice passed. Reopening saved production project.',flush=True)
    reopened=native(FINAL,WORK/'reopened')
    after={p:sha(ROOT/p) for p in before};assert before==after
    report={'date':'2026-11-09','revision':'fresh-r4','project':rel(FINAL),'sha256':sha(FINAL),
            'geometry':{'accepted_r3_scad_sha256':sha(REF/'accepted-r3.scad'),
              'accepted_r3_stl_sha256':sha(WORK/'accepted-r3.stl'),
              'full_mesh_watertight':bool(full.is_watertight),'full_mesh_body_count':len(full.split()),
              'bounds_mm':full.bounds.tolist(),'gray_mesh_watertight':bool(body.is_watertight),
              'green_logo_components':4,'logo_height_mm':32,'logo_inset_mm':0.8,'logo_relief_mm':0.4,
              'unchanged_r3_plus_logo_difference_mm3':vol_diff(a+l,f),
              'color_part_overlap_mm3':float(overlap),'saved_part_vertex_error_mm':errors,
              'nominal_fit_mm':{'front_reach':41.275,'rear_return':15.621,'pillar_gap':49.6568,
                'inside_radius':15.08125,'convex_tip_radius':12.7},'placement_mm':PLACEMENT.tolist()},
            'locked_settings':locked,'source_settings_changes':changes,
            'a2l_specific_material_fields_retained':machine_keys,
            'native_slice':result,'native_reopen':reopened,'gcode_md5':checksum,
            'gcode_audit':audit,'slice_warnings':warnings,
            'protected_before':before,'protected_after':after,
            'physical_status':'Design approved; full bucket fit, motion clearance, color quality and support removal have not been physically observed.'}
    jsave(OUT/'validation.json',report)
    print(json.dumps({'project':str(FINAL),'estimate':result['sliced_plates'][0],
                     'bed_clearance_mm':audit['conservative_bed_edge_clearance_mm'],'mesh_errors_mm':errors},indent=2),flush=True)

if __name__=='__main__':main()
