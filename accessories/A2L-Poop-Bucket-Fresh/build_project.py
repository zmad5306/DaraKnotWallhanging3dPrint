"""Package the single-color parametric bucket for A2L / SUNLU PLA+ 2.0.

The STL is exported by OpenSCAD from Bucket.scad. Geometry comparisons use
the preceding long-bucket CAD; no earlier remixed mesh is a geometry input.
Requires the repository's trimesh/manifold3d geometry dependencies and Bambu CLI.
"""
from pathlib import Path
import copy, hashlib, json, math, re, shutil, subprocess, sys, time, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REF=OUT/'reference'
WORK=ROOT/'.work/a2l-bucket-vent-clearance-build'
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
    exports=[(OUT/'history/before-vent-clearance.scad',WORK/'prior-long.stl',None),
             (OUT/'Bucket.scad',OUT/'Bucket.stl',None)]
    for source,target,mode in exports:
        if target.exists() and not force:continue
        args=[str(exe),'--hardwarnings','--export-format','binstl']
        if mode:args+=['-D',f'view_mode="{mode}"']
        args+=['-o',str(target),str(source)]
        log_path=WORK/(target.stem+'-render.log')
        with log_path.open('w',encoding='utf8') as log:
            p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        message=log_path.read_text(encoding='utf8')
        assert p.returncode==0 and not re.search(r'(?im)^\s*(ERROR|WARNING):',message),(p.returncode,message)
    # OpenSCAD 2021.01 can report a CGAL preview error yet return exit code 0.
    # F6 export alone therefore does not qualify the interactive F5 CAD path.
    preview=WORK/'cad-preview.png';record=WORK/'cad-preview-check.json'
    source=OUT/'Bucket.scad'
    if force or not preview.exists() or not record.exists() or json.loads(record.read_text())['cad_sha256']!=sha(source):
        log_path=WORK/'cad-preview.log'
        args=[str(exe),'--hardwarnings','--imgsize=1200,1000','--viewall','--autocenter',
              '--projection=o','-o',str(preview),str(source)]
        with log_path.open('w',encoding='utf8') as log:
            p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        message=log_path.read_text(encoding='utf8')
        assert p.returncode==0 and not re.search(r'(?im)^\s*(ERROR|WARNING):',message),(p.returncode,message)
        assert preview.exists() and preview.stat().st_size>0
        jsave(record,{'cad_sha256':sha(source),'preview_exit':p.returncode,'log':message,
                      'preview_png':str(preview)})

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

def validate_recess(full):
    """Check the retained blind cut, source SVG and complete wall backing."""
    from shapely.ops import unary_union
    original=trimesh.load(WORK/'prior-long.stl',force='mesh')
    before,after=solid(original),solid(full)
    svg=ET.parse(REF/'bambu-mark.svg').getroot()
    # Read the source's M/L/H/V path commands independently of the CAD polygons.
    polygons=[]
    for path in svg:
        points=[];x=y=0.;tokens=re.findall(r'[MLHVZ]|-?\d+(?:\.\d+)?',path.get('d'))
        i=0
        while i<len(tokens):
            op=tokens[i];i+=1
            if op=='Z':break
            if op in ('M','L'):x,y=map(float,tokens[i:i+2]);i+=2
            elif op=='H':x=float(tokens[i]);i+=1
            elif op=='V':y=float(tokens[i]);i+=1
            else:raise ValueError(op)
            points.append([55+(x-47)*32/122,40+(122-y)*32/122])
        polygons.append(Polygon(points))
    shape=unary_union(polygons)
    def prism(depth,y_start):
        pieces=[]
        for poly in shape.geoms:
            vertices=np.array(poly.exterior.coords[:-1])
            assert len(vertices)==4 and abs(poly.area-poly.convex_hull.area)<1e-8
            piece=trimesh.creation.extrude_triangulation(vertices,np.array([[0,1,2],[0,2,3]]),depth)
            piece.apply_transform(np.array([[1,0,0,0],[0,0,1,y_start],[0,1,0,0],[0,0,0,1.]]))
            pieces.append(piece)
        return solid(trimesh.util.concatenate(pieces))
    expected=prism(.6,0)
    residual=abs((expected ^ after).volume())
    backing_missing=abs((prism(1.4,.6)-after).volume())
    local=solid(trimesh.creation.box(bounds=[[40,-.001,39],[70,2.001,73]]))
    unchanged=vol_diff(before ^ local,after ^ local)
    assert residual<.001 and backing_missing<.001 and unchanged<.001
    return original,{'style':'recessed, single color','height_mm':32,'center_x_mm':55,
        'bottom_z_mm':40,'depth_mm':.6,'remaining_wall_mm':1.4,
        'source':'reference/bambu-mark.svg','material_remaining_in_recess_mm3':residual,
        'missing_wall_backing_mm3':backing_missing,'logo_region_difference_mm3':unchanged}


def top_height(mesh,x,y):
    tri=mesh.triangles
    ax,ay=tri[:,0,0],tri[:,0,1]
    bx,by=tri[:,1,0],tri[:,1,1]
    cx,cy=tri[:,2,0],tri[:,2,1]
    denom=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
    good=np.abs(denom)>1e-10
    denom=np.where(good,denom,1)
    u=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/denom
    v=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/denom
    w=1-u-v
    inside=good & (u>=-1e-5) & (v>=-1e-5) & (w>=-1e-5)
    assert inside.any(),(x,y)
    return float((u*tri[:,0,2]+v*tri[:,1,2]+w*tri[:,2,2])[inside].max())


FORWARD_LIMIT=6*25.4
VENT_MARGIN=1.0
FORWARD_REACH=FORWARD_LIMIT-VENT_MARGIN
BODY_LENGTH=FORWARD_REACH+49.6568+12
SHORTENING=255-BODY_LENGTH


def validate_shortening(before_mesh,full):
    from shapely.geometry import box
    before,after=solid(before_mesh),solid(full)
    def cube(lo,hi):return solid(trimesh.creation.box(bounds=[lo,hi]))
    # Independent construction: remove a straight middle length and rejoin.
    # Retain the complete front end and translate the remainder as one solid.
    front=cube([-1,-1,-1],[134,8,162])
    rear=cube([-1,8+SHORTENING,-1],[134,256,162])
    expected=(before ^ front)+(before ^ rear).translate([0,-SHORTENING,0])
    expected_difference=vol_diff(expected,after)
    front_difference=vol_diff(before ^ front,after ^ front)
    rear_domain=cube([-1,193.3432-.001,-1],[134,256,162])
    rear_difference=vol_diff(before ^ rear_domain,after.translate([0,SHORTENING,0]) ^ rear_domain)
    # Translating float32 STL coordinates accumulates small surface-volume noise.
    # Bound it with independent section distances/areas across the full height.
    section_checks=[]
    for z in [1,10,40,58,63.7,65.5,100,150]:
        base=mesh_slice(before_mesh,z);actual=mesh_slice(full,z)
        expect=base.intersection(box(-1,-1,134,8)).union(
            translate(base.intersection(box(-1,8+SHORTENING,134,256)),yoff=-SHORTENING))
        distance=expect.hausdorff_distance(actual)
        area=expect.symmetric_difference(actual).area
        assert distance<.0002 and area<.003,(z,distance,area)
        section_checks.append({'z_mm':z,'max_distance_mm':distance,'difference_area_mm2':area})
    assert expected_difference<.5,expected_difference
    assert front_difference<.01,front_difference
    assert rear_difference<.5,rear_difference
    prior_outline=mesh_slice(before_mesh,10)
    outline=mesh_slice(full,10)
    prior_pillar=prior_outline.intersection(box(-1,192.5,134,256))
    aligned_pillar=translate(outline,yoff=SHORTENING).intersection(box(-1,192.5,134,256))
    pillar_distance=prior_pillar.hausdorff_distance(aligned_pillar)
    pillar_area=prior_pillar.symmetric_difference(aligned_pillar).area
    assert pillar_distance<.00005 and pillar_area<.005,(pillar_distance,pillar_area)
    # Measure the actual straight pillar-front contact face from the STL outline.
    points=np.asarray(outline.exterior.coords);segments=[]
    for a,b in zip(points[:-1],points[1:]):
        if (80<a[1]<190 and 80<b[1]<190 and min(a[0],b[0])>80
            and max(a[0],b[0])<=110.0001 and abs(a[1]-b[1])<.00001 and abs(a[0]-b[0])>.1):
            segments.append((a+b)/2)
    assert segments
    planes=np.array(segments)[:,1]
    assert np.ptp(planes)<.0001,planes
    pillar_front=float(planes.mean());frontmost=float(full.bounds[0,1])
    reach=pillar_front-frontmost
    assert abs(reach-FORWARD_REACH)<.0001 and FORWARD_LIMIT-reach>=.9999,(reach,FORWARD_LIMIT)
    return {'limit_mm':FORWARD_LIMIT,'limit_in':6,'target_margin_mm':VENT_MARGIN,
        'stl_pillar_front_y_mm':pillar_front,'stl_frontmost_y_mm':frontmost,
        'measured_forward_reach_mm':reach,'measured_forward_reach_in':reach/25.4,
        'measured_margin_mm':FORWARD_LIMIT-reach,'previous_forward_reach_mm':193.3432,
        'body_length_mm':BODY_LENGTH,'previous_body_length_mm':255,'shortening_mm':SHORTENING,
        'independent_shortening_difference_mm3':expected_difference,
        'front_end_difference_mm3':front_difference,'aligned_rear_difference_mm3':rear_difference,
        'aligned_pillar_outline_distance_mm':pillar_distance,'aligned_pillar_outline_difference_mm2':pillar_area,
        'independent_section_comparisons':section_checks,
        'all_geometry_within_forward_limit':True}


def validate_wall_transitions(full):
    start=65.12+1.696*(69.59-65.12)/(21.896+1.696)
    checks=[]
    def check(name,x,y,expected):
        actual=top_height(full,x,y)
        assert abs(actual-expected)<.0002,(name,x,y,actual,expected)
        checks.append({'location':name,'xy_mm':[float(x),float(y)],'top_mm':actual,'expected_mm':expected})
    for x in [20,55,90,104]:
        check('front slope',x,1,160.804+(start-160.804)*(x-8)/102)
    for y in [6.1,7,7.999,FORWARD_REACH-3.999,FORWARD_REACH-3,FORWARD_REACH-1,FORWARD_REACH-.001]:
        check('connecting wall',109,y,start)
    outline=np.asarray(mesh_slice(full,10).exterior.coords)
    rear=outline[(outline[:,1]>FORWARD_REACH+.0001)&(outline[:,1]<BODY_LENGTH-2.03)&(outline[:,0]>8.02)]
    assert len(rear)>20
    for x,y in rear[::max(1,len(rear)//24)]:
        check('rear slope',x,y,start+(160.804-start)*(y-FORWARD_REACH)/(BODY_LENGTH-2.02-FORWARD_REACH))
    for y in [7.999,FORWARD_REACH-3.999,FORWARD_REACH-.8]:
        for x in np.linspace(108.001,109.999,9):check('lip connection',x,y,start)
    return {'adjoining_wall_start_mm':start,'adjoining_wall_start_in':start/25.4,
        'height_checks':checks,'front_and_rear_connections_reach_lip_top':True}


def validate_geometry(full):
    from shapely.geometry import box
    assert full.is_volume and len(full.split())==1
    assert np.max(np.abs(full.bounds-np.array([[0,0,0],[132.296,BODY_LENGTH,160.804]])))<.0001
    original,logo=validate_recess(full)
    shortening=validate_shortening(original,full)
    transitions=validate_wall_transitions(full)
    profile=Polygon(full.section(plane_origin=[0,100,0],plane_normal=[0,1,0]).discrete[0][:,[0,2]])
    local=profile.intersection(box(108,55,133,71))
    expected=Polygon([[108,55],[110,55],[110,63.6],[110.268,63.9],
                      [132.296,67.922],[131.896,69.59],[108.304,65.12],[108,64.768]])
    profile_error=local.symmetric_difference(expected).area
    assert profile_error<.001, profile_error
    # Check the entire external underside, including the root transition.
    mask=(full.face_normals[:,2]<-.01)&(full.triangles_center[:,0]>110.00001)
    mask &= (full.triangles_center[:,1]>7.999)&(full.triangles_center[:,1]<FORWARD_REACH-3.999)
    assert mask.any()
    underside_min=float(full.triangles[mask,:,2].min())
    clearance=underside_min-2.464*25.4
    assert clearance>=1.0,clearance
    return {'closed_single_body':True,'bounds_mm':full.bounds.tolist(),
            'wall_transitions':transitions,'vent_clearance':shortening,
            'reference_dimension_section_error_mm2':profile_error,
            'logo_present':True,'logo':logo,'front_surface_y_mm':0,
            'pillar_fit_unchanged':True,'body_width_and_height_unchanged':True,'body_length_mm':BODY_LENGTH,
            'chute_wall_height_mm':63.6,'chute_tip_top_mm':69.59,
            'chute_tip_bottom_mm':67.922,'chute_reach_mm':22.296,
            'user_housing_height_in':2.464,'user_housing_height_mm':2.464*25.4,
            'minimum_chute_underside_height_mm':underside_min,'minimum_vertical_clearance_mm':clearance,
            'chute_vertical_offset_mm':5.574,'wall_height_in':63.6/25.4,'tip_top_height_in':69.59/25.4}

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
    report={'date':'2026-11-10','revision':'vent-clearance','project':str(destination),
            'sha256':sha(destination),'geometry':geometry,'saved_part_vertex_error_mm':mesh_difference,
            'saved_settings':settings,'native_slice':sliced_result,'native_reopen':reopen,
            'support_audit':sa,'reopen_support_audit':rsa,'bed_edge_clearance_mm':clearance,
            'gcode_md5':checksum,'color_changes':0,'prime_tower_extrusions':0,
            'locked_settings':locked,'protected_before':protected_before,'protected_after':protected_after,
            'physical_status':'User requires at most 6 inches from pillar front to bucket front. Shortened forward reach to 151.4 mm, leaving 1 mm nominal margin. Pillar/rear shape, chute section, raised wall transitions and recessed logo retained. Physical printing and vent clearance remain unobserved.'}
    jsave(run_dir/'validation.json',report)
    print(destination.name,'native reopen passed',flush=True)
    return report

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    render_inputs('--render' in sys.argv)
    cfg=json.loads((REF/'current-project-settings.json').read_text())
    report=build_project(cfg,FINAL,WORK/'production')
    report['project']=rel(FINAL)
    report['cad_preview_check']=json.loads((WORK/'cad-preview-check.json').read_text())
    jsave(OUT/'validation.json',report)
    (OUT/'native-preview.png').write_bytes(package(FINAL)['Metadata/plate_1.png'])

if __name__=='__main__':main()

