"""Package the single-color parametric bucket for A2L / SUNLU PLA+ 2.0.

The STL is exported by OpenSCAD from Bucket.scad. Geometry comparisons
use the accepted-r3.scad reference; no earlier remixed mesh is a geometry input.
Requires the repository's trimesh/manifold3d geometry dependencies and Bambu CLI.
"""
from pathlib import Path
import copy, hashlib, json, math, re, shutil, subprocess, sys, time, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REF=OUT/'reference'
WORK=ROOT/'.work/a2l-bucket-single-build'
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
COLORS=['#555555']
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
             (OUT/'Bucket.scad',OUT/'Bucket.stl',None)]
    for source,target,mode in exports:
        if target.exists() and not force:continue
        args=[str(exe),'--hardwarnings','--export-format','binstl']
        if mode:args+=['-D',f'view_mode="{mode}"']
        args+=['-o',str(target),str(source)]
        with (WORK/(target.stem+'-render.log')).open('w') as log:
            p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        assert p.returncode==0

def make_project(body,cfg):
    child=model();res=ET.SubElement(child,tag('resources'))
    mesh_xml(res,1,body)
    root=ET.Element(tag('model'),unit='millimeter',requiredextensions='p',attrib={'{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    for k,v in [('Application','BambuStudio-02.09.01.70'),('BambuStudio:3mfVersion','1'),
                ('Title',TITLE),('Description','A2L poop bucket with triangular front, full-height back, sloped pillar wall, catch chute.')]:
        ET.SubElement(root,tag('metadata'),name=k).text=v
    rr=ET.SubElement(root,tag('resources'));obj=ET.SubElement(rr,tag('object'),id='3',type='model')
    comps=ET.SubElement(obj,tag('components'))
    for oid in (1,):ET.SubElement(comps,tag('component'),objectid=str(oid),transform=IDENTITY,attrib={'{'+P+'}path':'/3D/Objects/object_1.model'})
    pose='1 0 0 0 1 0 0 0 1 '+' '.join(map(str,PLACEMENT))
    ET.SubElement(ET.SubElement(root,tag('build')),tag('item'),objectid='3',transform=pose,printable='1')
    settings=ET.Element('config');o=ET.SubElement(settings,'object',id='3')
    meta(o,'name','A2L Poop Bucket');meta(o,'extruder','1')
    for oid,name,tm in [(1,'Bucket',body)]:
        part=ET.SubElement(o,'part',id=str(oid),subtype='normal_part')
        meta(part,'name',name);meta(part,'extruder',oid)
        meta(part,'matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')
        ET.SubElement(part,'mesh_stat',face_count=str(len(tm.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
    plate=ET.SubElement(settings,'plate')
    for k,v in [('plater_id',1),('plater_name','A2L Poop Bucket'),('locked','false'),
                ('filament_map_mode','Auto For Flush'),('filament_maps','1'),('filament_volume_maps','0')]:meta(plate,k,v)
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

def validate_geometry(full):
    from shapely.geometry import box
    assert full.is_volume and len(full.split())==1
    assert np.max(np.abs(full.bounds-np.array([[0,0,0],[132.296,255,160.804]])))<.0001
    accepted=trimesh.load(WORK/'accepted-r3.stl',force='mesh')
    a,b=solid(accepted),solid(full)
    domain=solid(trimesh.creation.box(bounds=[[103.999,7.999,54.39],[132.297,189.344,66.01]]))
    outside_change=abs(((a-b)-domain).volume())+abs(((b-a)-domain).volume())
    assert outside_change<.03, outside_change
    profile=Polygon(full.section(plane_origin=[0,100,0],plane_normal=[0,1,0]).discrete[0][:,[0,2]])
    local=profile.intersection(box(108,55,133,67))
    expected=Polygon([[108,55],[110,55],[110,58.026],[110.268,58.326],
                      [132.296,62.348],[131.896,64.016],[108.304,59.546],[108,59.194]])
    profile_error=local.symmetric_difference(expected).area
    assert profile_error<.001, profile_error
    return {'closed_single_body':True,'bounds_mm':full.bounds.tolist(),
            'outside_chute_change_from_accepted_body_mm3':outside_change,
            'reference_dimension_section_error_mm2':profile_error,
            'logo_present':False,'front_surface_y_mm':0,
            'pillar_fit_unchanged':True,'body_size_unchanged':True,
            'chute_wall_height_mm':58.026,'chute_tip_top_mm':64.016,
            'chute_tip_bottom_mm':62.348,'chute_reach_mm':22.296}

def build_project(cfg, destination, run_dir):
    protected=list(ROOT.glob('*.3mf'))+list((ROOT/'accessories/A2L-Poop-Bucket').glob('*.3mf'))
    protected += [ROOT/'accessories/A2L-Poop-Bucket/Bucket.scad',ROOT/'accessories/A2L-Poop-Bucket/Bucket.stl']
    protected_before={rel(p):sha(p) for p in protected}
    body=trimesh.load(OUT/'Bucket.stl',force='mesh')
    geometry=validate_geometry(body)
    assert len(cfg['filament_settings_id'])==1 and len(cfg['filament_colour'])==1
    assert cfg['enable_prime_tower']=='0'
    locks={'layer_height':'0.2','initial_layer_print_height':'0.2','wall_loops':'4',
           'top_shell_layers':'5','bottom_shell_layers':'5','sparse_infill_density':'8%',
           'sparse_infill_pattern':'gyroid','support_type':'tree(auto)','support_style':'default',
           'support_on_build_plate_only':'1','curr_bed_type':'Textured PEI Plate','enable_prime_tower':'0'}
    for k,v in locks.items():assert cfg[k]==v,(k,cfg[k])
    run_dir.mkdir(parents=True,exist_ok=True)
    files=make_project(body,cfg)
    editable=run_dir/'editable.3mf';save(editable,files)
    sliced_result=native(editable,run_dir/'slice',True)
    sliced=package(run_dir/'slice/sliced.3mf')
    settings=json.loads(sliced['Metadata/project_settings.config'])
    assert settings==cfg, {k:[cfg.get(k),settings.get(k)] for k in cfg.keys()|settings.keys() if cfg.get(k)!=settings.get(k)}
    parts=saved_parts(sliced);assert len(parts)==1 and parts[0].is_volume
    placed=body.copy();placed.apply_translation(PLACEMENT)
    mesh_difference=mesh_error(placed,parts[0]);assert mesh_difference<.0001
    config=ET.fromstring(sliced['Metadata/model_settings.config'])
    assert len(config.findall('object/part'))==1
    assert config.find("plate/metadata[@key='plater_name']").get('value')=='A2L Poop Bucket'
    gc=sliced['Metadata/plate_1.gcode'].decode()
    gcfg=dict(re.findall(r'^; (\w+) = (.*)$',gc,re.M))
    for k,v in locks.items():assert gcfg[k]==v,(k,gcfg.get(k))
    sa=support_audit(gc);assert sa['support_extrusions_intersecting_collection_cavity']==0,sa
    audit=scan_gcode(gc)
    assert set(audit['model_extrusion_z_by_filament_mm'])=={'1'}
    assert audit['features'].get('Prime tower',0)==0
    plate=sliced_result['sliced_plates'][0]
    assert plate['filament_change_times']==0
    assert len(plate['filaments'])==1
    assert plate['times']['support_tree_generate_time']>0 and plate['times']['support_normal_generate_time']==0
    lo,hi=audit['bead_xy_bounds_mm'];clearance=min(*lo,330-hi[0],320-hi[1]);assert clearance>3
    checksum=hashlib.md5(sliced['Metadata/plate_1.gcode']).hexdigest()
    assert sliced['Metadata/plate_1.gcode.md5'].decode().strip().lower()==checksum
    warnings=[w.attrib for w in ET.fromstring(sliced['Metadata/slice_info.config']).findall('plate/warning')]
    assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
    shutil.copyfile(run_dir/'slice/sliced.3mf',destination)
    print(destination.name,'sliced;',round(plate['total_predication']/60),'minutes; no interior supports or color changes',flush=True)
    reopen=native(destination,run_dir/'reopen',True)
    opened=package(run_dir/'reopen/sliced.3mf')
    assert json.loads(opened['Metadata/project_settings.config'])==settings
    assert max(mesh_error(a,b) for a,b in zip(parts,saved_parts(opened)))<.0001
    rsa=support_audit(opened['Metadata/plate_1.gcode'].decode())
    assert rsa['support_extrusions_intersecting_collection_cavity']==0
    assert reopen['sliced_plates'][0]['filament_change_times']==0
    protected_after={rel(p):sha(p) for p in protected}
    assert protected_before==protected_after
    locked=dict(locks)
    for k in ['printer_model','printer_settings_id','nozzle_diameter','filament_settings_id','filament_colour',
              'filament_flow_ratio','filament_max_volumetric_speed','nozzle_temperature','textured_plate_temp']:
        locked[k]=cfg[k]
    report={'date':'2026-11-10','revision':'single-color-reference-chute','project':str(destination),
            'sha256':sha(destination),'geometry':geometry,'saved_part_vertex_error_mm':mesh_difference,
            'saved_settings':settings,'native_slice':sliced_result,'native_reopen':reopen,
            'support_audit':sa,'reopen_support_audit':rsa,'bed_edge_clearance_mm':clearance,
            'gcode_md5':checksum,'color_changes':0,'prime_tower_extrusions':0,
            'locked_settings':locked,'protected_before':protected_before,'protected_after':protected_after,
            'physical_status':'User reports the reference bucket fits. Current wall/chute dimensions match that reference; a physical print of this single-color bucket has not been observed.'}
    jsave(run_dir/'validation.json',report)
    print(destination.name,'native reopen passed',flush=True)
    return report

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    render_inputs('--render' in sys.argv)
    cfg=json.loads((REF/'current-project-settings.json').read_text())
    report=build_project(cfg,FINAL,WORK/'production')
    report['project']=rel(FINAL)
    jsave(OUT/'validation.json',report)
    (OUT/'native-preview.png').write_bytes(package(FINAL)['Metadata/plate_1.png'])

if __name__=='__main__':main()

