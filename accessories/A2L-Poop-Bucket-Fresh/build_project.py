"""Package the fresh parametric bucket and front logo for A2L / SUNLU PLA+ 2.0.

The STL and logo are exported by OpenSCAD from Bucket.scad. Geometry comparisons
use the accepted-r3.scad reference; no earlier remixed mesh is a geometry input.
Requires the repository's trimesh/manifold3d geometry dependencies and Bambu CLI.
"""
from pathlib import Path
import copy, hashlib, json, math, re, shutil, subprocess, sys, time, zipfile
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
from validate_print_project import scan_gcode, transform, TOKEN
from shapely.geometry import Polygon, LineString
from shapely.affinity import translate
from mesh_sections import mesh_slice

FINAL=OUT/'A2L-Poop-Bucket-SUNLU-PLA-Plus-2.0.3mf'
PROFILE='SUNLU PLA+ 2.0 @Bambu Lab A2L 0.4 nozzle'
COLORS=['#555555','#00CC00']
TITLE='A2L Poop Bucket'
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
    """Use the current saved process/material values, including user purge edits."""
    cfg=json.loads((REF/'current-project-settings.json').read_text())
    locked_keys=['printer_model','printer_settings_id','printer_variant','nozzle_diameter',
                 'printable_area','printable_height','layer_height','initial_layer_print_height',
                 'wall_loops','top_shell_layers','bottom_shell_layers','sparse_infill_density',
                 'sparse_infill_pattern','curr_bed_type','enable_support','support_type','support_style','support_on_build_plate_only',
                 'enable_prime_tower','brim_type','filament_colour','filament_ids','filament_settings_id',
                 'nozzle_temperature','nozzle_temperature_initial_layer','textured_plate_temp',
                 'textured_plate_temp_initial_layer','filament_flow_ratio','filament_max_volumetric_speed']
    locked={k:cfg[k] for k in locked_keys}
    assert cfg['support_on_build_plate_only']=='1'
    assert cfg['filament_settings_id']==[PROFILE,PROFILE]
    machine_keys=['filament_start_gcode','filament_flush_temp_fast','pre_start_fan_time',
                  'overhang_fan_threshold','eng_plate_temp','eng_plate_temp_initial_layer',
                  'filament_long_retractions_when_cut','filament_retraction_distances_when_cut']
    return cfg,locked,{},machine_keys


def make_project(body,logo,cfg):
    child=model();res=ET.SubElement(child,tag('resources'))
    mesh_xml(res,1,body);mesh_xml(res,2,logo)
    root=ET.Element(tag('model'),unit='millimeter',requiredextensions='p',attrib={'{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    for k,v in [('Application','BambuStudio-02.09.01.70'),('BambuStudio:3mfVersion','1'),
                ('Title',TITLE),('Description','A2L poop bucket with triangular front, full-height back, sloped pillar wall, catch chute and green Bambu logo.')]:
        ET.SubElement(root,tag('metadata'),name=k).text=v
    rr=ET.SubElement(root,tag('resources'));obj=ET.SubElement(rr,tag('object'),id='3',type='model')
    comps=ET.SubElement(obj,tag('components'))
    for oid in (1,2):ET.SubElement(comps,tag('component'),objectid=str(oid),transform=IDENTITY,attrib={'{'+P+'}path':'/3D/Objects/object_1.model'})
    pose='1 0 0 0 1 0 0 0 1 '+' '.join(map(str,PLACEMENT))
    ET.SubElement(ET.SubElement(root,tag('build')),tag('item'),objectid='3',transform=pose,printable='1')
    settings=ET.Element('config');o=ET.SubElement(settings,'object',id='3')
    meta(o,'name','A2L Poop Bucket');meta(o,'extruder','1')
    for oid,name,tm in [(1,'Gray Body',body),(2,'Green Logo',logo)]:
        part=ET.SubElement(o,'part',id=str(oid),subtype='normal_part')
        meta(part,'name',name);meta(part,'extruder',oid)
        meta(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        ET.SubElement(part,'mesh_stat',face_count=str(len(tm.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
    plate=ET.SubElement(settings,'plate')
    for k,v in [('plater_id',1),('plater_name','A2L Poop Bucket'),('locked','false'),
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

def cavity():
    m=trimesh.load(OUT/'Bucket.stl',force='mesh')
    section=mesh_slice(m,10)
    assert section.geom_type=='Polygon' and len(section.interiors)==1
    return translate(Polygon(section.interiors[0]),xoff=101,yoff=32.7)

def support_audit(gc):
    interior=cavity();cached={};feature='Custom';width=.5;x=y=z=e=0.
    relative_e=False;relative_xyz=False;count=inside=0;bounds=[np.full(3,np.inf),np.full(3,-np.inf)];examples=[]
    for raw in gc.splitlines():
        line=raw.strip()
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        elif line.startswith('; LINE_WIDTH: '):width=float(line.split(': ',1)[1])
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0]
        if cmd=='M83':relative_e=True
        elif cmd=='M82':relative_e=False
        elif cmd in ['G90','G91']:relative_xyz=cmd=='G91'
        elif cmd=='G92':
            v={k:float(n) for k,n in TOKEN.findall(code)};x,y,z,e=v.get('X',x),v.get('Y',y),v.get('Z',z),v.get('E',e)
        elif cmd in ['G0','G1','G2','G3']:
            v={k:float(n) for k,n in TOKEN.findall(code)}
            nx,ny,nz=[old+v.get(k,0) if relative_xyz else v.get(k,old) for k,old in zip('XYZ',[x,y,z])]
            de=v.get('E',0) if relative_e else v.get('E',e)-e
            if de>0 and feature in ['Support','Support interface','Support transition'] and any(k in v for k in ['X','Y','I','J']):
                count+=1;points=[(x,y),(nx,ny)]
                if cmd in ['G2','G3']:
                    cx,cy=x+v.get('I',0),y+v.get('J',0);rad=math.hypot(x-cx,y-cy)
                    a,b=math.atan2(y-cy,x-cx),math.atan2(ny-cy,nx-cx);sgn=1 if cmd=='G3' else -1
                    span=((b-a)*sgn)%(2*math.pi);n=max(2,math.ceil(rad*span/.1))
                    points=[(cx+rad*math.cos(a+sgn*span*i/n),cy+rad*math.sin(a+sgn*span*i/n)) for i in range(n+1)]
                radius=round(width/2,5)
                if radius not in cached:cached[radius]=interior.buffer(radius-.001)
                shape=cached[radius]
                if nz>1.98 and LineString(points).intersects(shape):
                    inside+=1
                    for px,py in points:
                        bounds[0]=np.minimum(bounds[0],[px,py,nz]);bounds[1]=np.maximum(bounds[1],[px,py,nz])
                    if len(examples)<5:examples.append({'feature':feature,'start':[x,y,z],'end':[nx,ny,nz],'width':width})
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative_e else v.get('E',e)
    return {'support_extrusions_checked':count,'support_extrusions_intersecting_collection_cavity':inside,
        'interior_support_bounds_mm':[v.tolist() for v in bounds] if inside else None,'examples':examples,
        'check':'Every support/interface/transition extrusion above the floor; bead half-width included; arcs sampled at <=0.1 mm.'}

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
    # The accepted shell loses only the inward chute shelf. Fit and outer reach stay fixed.
    removed=(a+l)-f
    assert (f-(a+l)).volume()<0.02
    allowed=trimesh.creation.box(bounds=[[103.9999,7.9999,54.3999],[108.0001,189.3433,58.0001]])
    assert abs((removed-solid(allowed)).volume())<0.02, 'Material removed outside the chute shelf'
    assert abs(removed.volume()-1450.75)<0.1
    body=mesh(f-l)
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
              'sparse_infill_density','sparse_infill_pattern','curr_bed_type','enable_support','support_type','support_style','support_on_build_plate_only']:
        assert gcfg[k]==locked[k],(k,gcfg.get(k),locked[k])
    assert PROFILE in gcfg['filament_settings_id']
    assert re.search(r'^\s*M(?:140|190) S65\b',gc,re.M)
    assert re.search(r'^\s*M(?:104|109) S220\b',gc,re.M)
    checksum=hashlib.md5(sliced['Metadata/plate_1.gcode']).hexdigest()
    assert sliced['Metadata/plate_1.gcode.md5'].decode().strip().lower()==checksum
    interior_supports=support_audit(gc)
    assert interior_supports['support_extrusions_intersecting_collection_cavity']==0
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
    reopened_supports=support_audit((WORK/'reopened/plate_1.gcode').read_text())
    assert reopened_supports['support_extrusions_intersecting_collection_cavity']==0
    after={p:sha(ROOT/p) for p in before};assert before==after
    report={'date':'2026-11-09','revision':'fresh-r5','project':rel(FINAL),'sha256':sha(FINAL),
            'geometry':{'accepted_r3_scad_sha256':sha(REF/'accepted-r3.scad'),
              'accepted_r3_stl_sha256':sha(WORK/'accepted-r3.stl'),
              'full_mesh_watertight':bool(full.is_watertight),'full_mesh_body_count':len(full.split()),
              'bounds_mm':full.bounds.tolist(),'gray_mesh_watertight':bool(body.is_watertight),
              'green_logo_components':4,'logo_height_mm':32,'logo_inset_mm':0.8,'logo_relief_mm':0.4,
              'removed_inward_shelf_volume_mm3':removed.volume(),
              'color_part_overlap_mm3':float(overlap),'saved_part_vertex_error_mm':errors,
              'nominal_fit_mm':{'front_reach':41.275,'rear_return':15.621,'pillar_gap':49.6568,
                'inside_radius':15.08125,'convex_tip_radius':12.7},'placement_mm':PLACEMENT.tolist()},
            'locked_settings':locked,'source_settings_changes':changes,
            'a2l_specific_material_fields_retained':machine_keys,
            'native_slice':result,'native_reopen':reopened,'gcode_md5':checksum,
            'gcode_audit':audit,'slice_warnings':warnings,
            'support_audit':interior_supports,'reopen_support_audit':reopened_supports,
            'protected_before':before,'protected_after':after,
            'physical_status':'Design approved; full bucket fit, motion clearance, color quality and support removal have not been physically observed.'}
    jsave(OUT/'validation.json',report)
    print(json.dumps({'project':str(FINAL),'estimate':result['sliced_plates'][0],
                     'bed_clearance_mm':audit['conservative_bed_edge_clearance_mm'],'mesh_errors_mm':errors},indent=2),flush=True)

if __name__=='__main__':main()
