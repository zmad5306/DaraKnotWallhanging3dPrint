"""Promote the accepted R8 interface to the original full bucket, for A1/SUNLU.

Inputs are exact mesh/settings snapshots in reference/. No download or older
sample builder is required. Run with the repository's geometry dependencies.
"""
from pathlib import Path
import copy, hashlib, json, re, subprocess, sys, time, zipfile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import trimesh
import manifold3d as mf
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from shapely.affinity import translate
from development_3mf import solid,mesh,mesh_xml
from build_jointed_bambu_project import P,R,IDENTITY,tag,xml,model
from validate_print_project import scan_gcode,transform

OUT=Path(__file__).resolve().parent
REF=OUT/'reference'
WORK=ROOT/'.work/a2l-bucket-production-r9'
FINAL=OUT/'A2L-Poop-Bucket-A1-SUNLU-PLA.3mf'
EDIT=WORK/'editable.3mf'
TITLE='A2L poop bucket - A1 SUNLU PLA Basic - 8% gyroid - r9'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def package(p):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        return {n:z.read(n) for n in z.namelist()}
def save(p,files):
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
        for n,d in files.items():z.writestr(n,d)
def cross(p):
    return mf.CrossSection([np.asarray(p.exterior.coords)[:-1]]+
                          [np.asarray(r.coords)[:-1] for r in p.interiors],mf.FillRule.EvenOdd)
def cube(lo,hi):return mf.Manifold.cube(tuple(np.array(hi)-lo)).translate(lo)
def section(s,z=.8):
    paths=s.slice(z).to_polygons();assert len(paths)==1
    p=Polygon(paths[0]);assert p.is_valid and not p.interiors
    return p
def right(p,y):return p.intersection(LineString([(-1,y),(200,y)])).bounds[2]
def volume_diff(a,b):return abs((a-b).volume())+abs((b-a).volume())
def saved_mesh(files):
    r=ET.fromstring(files['3D/3dmodel.model']);it=r.find(tag('build')+'/'+tag('item'))
    co=r.find(tag('resources')).find(tag('object')).find(tag('components')+'/'+tag('component'))
    child=ET.fromstring(files[co.get('{'+P+'}path').lstrip('/')]);o=child.find(tag('resources')).find(tag('object'))
    v=np.array([[float(e.get(k)) for k in ('x','y','z')] for e in o.findall('.//'+tag('vertex'))])
    f=np.array([[int(e.get(k)) for k in ('v1','v2','v3')] for e in o.findall('.//'+tag('triangle'))])
    t=transform(it.get('transform'))@transform(co.get('transform'))
    return trimesh.Trimesh(v@t[:3,:3].T+t[:3,3],f,process=False)
def native(src,directory,export=False):
    directory.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    args=[str(exe),'--debug','5','--slice','1']
    if export:args+=['--export-3mf','sliced.3mf']
    args+=['--outputdir',str(directory),str(src)]
    codes=[]
    for i in range(3):
        with (directory/f'native-{i+1}.log').open('w',encoding='utf8') as log:
            r=subprocess.run(args,cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        codes.append(r.returncode)
        if r.returncode==0:break
        if r.returncode!=3221225477:break
        time.sleep(1)
    assert r.returncode==0,(codes,str(directory))
    data=json.loads((directory/'result.json').read_text());assert data['return_code']==0
    assert len(data['sliced_plates'])==1 and data['sliced_plates'][0]['warning_message']==''
    data['native_launch_exit_codes']=codes
    return data


def main():
    WORK.mkdir(parents=True,exist_ok=True)
    protected=list(ROOT.glob('*.3mf'))
    for pattern in ['A2L-Pillar-*/*.3mf','A2L-Poop-*/*.3mf']:
        protected+=list((ROOT/'output').glob(pattern))
    before={rel(p):sha(p) for p in protected}
    doc=json.loads((REF/'source-template.json').read_text())
    for key in ['source','fit']:
        path=ROOT/doc[key+'_path']
        if path.exists():assert sha(path)==doc[key+'_sha256']
    preset=json.loads((REF/'SUNLU-PLA-Basic-A1.json').read_text())
    assert sha(REF/'SUNLU-PLA-Basic-A1.json')==doc['preset_sha256']
    raw=np.load(REF/'source-r4-mesh.npz');original=trimesh.Trimesh(raw['vertices'],raw['faces'],process=False)
    raw=np.load(REF/'accepted-r8-mesh.npz');fit=trimesh.Trimesh(raw['vertices'],raw['faces'],process=False)
    old=solid(original);old_floor=section(old);fit_poly=section(solid(fit))
    d=doc['fit_metadata']['nominal_r7_interface_mm']
    # Register the actual R8 contour by its front tip and front shoulder. The
    # rear outer wall belongs to the full bucket; keep its original location.
    front_y=179.33200120180845
    registration=[right(old_floor,170)-right(fit_poly,5),front_y-d['front_shoulder_y']]
    template=translate(fit_poly,xoff=registration[0],yoff=registration[1])
    rear_y=original.bounds[1,1];front_x=right(old_floor,170)
    rear_x=right(template,registration[1]+75);side_x=right(template,registration[1]+40)
    assert abs(front_x-side_x-41.275)<1e-4 and abs(rear_x-side_x-15.621)<1e-4
    rear_margin=rear_y-template.bounds[3];assert abs(rear_margin-3.175)<1e-4
    patch=unary_union([template,box(32,160,template.bounds[0],rear_y),
                      box(32,160,front_x,template.bounds[1]),
                      box(32,template.bounds[3],rear_x,rear_y)])
    patch_xy=box(32,160,150,rear_y+1)
    floor=old_floor.difference(patch_xy).union(patch)
    assert floor.geom_type=='Polygon' and floor.is_valid
    outer=cross(floor);inner=cross(floor.buffer(-2,join_style='mitre'))
    replacement=outer.extrude(1.98)+(outer-inner).extrude(58)
    domain=cube((32,160,-1),(150,rear_y+1,200))
    lip_domain=cube((88,160,57.9),(150,176.33201,100))
    revised=(old-domain)+(replacement^domain)+(old^lip_domain)
    raw_revised=revised;revised=revised.simplify(.00001)
    cleanup=volume_diff(raw_revised,revised);assert cleanup<.02,cleanup
    tm=mesh(revised);assert tm.is_volume and len(revised.decompose())==1
    assert np.allclose(tm.bounds,original.bounds,atol=1e-4)
    preservation=volume_diff(revised-domain,old-domain)
    lip_error=volume_diff(revised^lip_domain,old^lip_domain)
    front_domain=cube((-1,-1,-1),(150,159.99,200))
    front_error=volume_diff(revised^front_domain,old^front_domain)
    assert max(preservation,lip_error,front_error)<.05
    actual_floor=section(revised)
    crop=box(template.bounds[0],template.bounds[1],front_x,template.bounds[3])
    fit_error=actual_floor.intersection(crop).symmetric_difference(template).area
    assert fit_error<.002,fit_error
    wall_checks={}
    for z in [5.,30.,57.]:
        a=revised.slice(z)^cross(patch_xy);w=replacement.slice(z)^cross(patch_xy)
        wall_checks[str(z)]=abs((a-w).area())+abs((w-a).area())
        assert wall_checks[str(z)]<.002
    # Binary STL uses float32 coordinates; remove redundant microscopic faces
    # before export so those coordinates do not collapse into open edges.
    stl_body=revised.simplify(.0001)
    stl_cleanup=volume_diff(revised,stl_body);assert stl_cleanup<.01
    mesh(stl_body).export(OUT/'Bucket.stl')
    assert trimesh.load(OUT/'Bucket.stl',force='mesh').is_volume
    # Full material assignment, not a name-only substitution. Preserve the
    # single white slot; the preset's empty default color is not a color change.
    baseline=doc['base_settings'];cfg=copy.deepcopy(baseline);cfg['print_settings_id']=TITLE
    meta={'name','from','version','inherits','filament_id','compatible_printers',
          'compatible_printers_condition','compatible_prints','compatible_prints_condition',
          'default_filament_colour','filament_notes'}
    applied=[]
    for k,v in preset.items():
        if k not in meta and k in cfg:cfg[k]=copy.deepcopy(v);applied.append(k)
    cfg['filament_settings_id']=[preset['name']];cfg['filament_ids']=[preset['filament_id']]
    cfg['filament_vendor']=preset['filament_vendor'];cfg['inherits_group'][1]=preset.get('inherits','')
    cfg.update(support_type='tree(auto)',support_style='default')
    cfg_diff={k:[baseline.get(k),cfg.get(k)] for k in baseline.keys()|cfg.keys() if baseline.get(k)!=cfg.get(k)}
    assert set(cfg_diff)<=set(applied)|{'print_settings_id','filament_ids','inherits_group','support_type','support_style'}
    locked={'printer_model':'Bambu Lab A1','printer_settings_id':'Bambu Lab A1 0.4 nozzle',
            'nozzle_diameter':['0.4'],'layer_height':'0.2','initial_layer_print_height':'0.2',
            'wall_loops':'4','top_shell_layers':'5','bottom_shell_layers':'5',
            'sparse_infill_density':'8%','sparse_infill_pattern':'gyroid','curr_bed_type':'Textured PEI Plate',
            'enable_support':'1','support_type':'tree(auto)','support_style':'default',
            'brim_type':'auto_brim','enable_prime_tower':'0','filament_colour':['#FFFFFF'],
            'filament_settings_id':[preset['name']],'filament_ids':[preset['filament_id']],
            'nozzle_temperature':['220'],'nozzle_temperature_initial_layer':['220'],
            'textured_plate_temp':['65'],'textured_plate_temp_initial_layer':['65'],
            'filament_max_volumetric_speed':['12'],'filament_flow_ratio':['0.98']}
    for k,v in locked.items():assert cfg[k]==v,(k,cfg[k],v)
    root=ET.fromstring(doc['root_model']);co=root.find('.//'+tag('component'))
    path=co.get('{'+P+'}path').lstrip('/');co.set('transform',IDENTITY)
    child=model();res=ET.SubElement(child,tag('resources'));mesh_xml(res,int(co.get('objectid')),tm)
    for e in list(root.findall(tag('metadata'))):
        k=e.get('name','')
        if k in ['Title','ProfileTitle']:e.text=TITLE
        elif k=='Description':e.text='Full A2L bucket with accepted R8 pillar interface. Print on A1 with saved SUNLU PLA Basic. Original exterior, handle, lip and catch wall retained.'
        elif 'thumbnail' in k.lower() or k in ['DesignerCover','ProfileCover']:root.remove(e)
    t=np.eye(4);t[:3,3]=doc['placement_mm']
    root.find(tag('build')+'/'+tag('item')).set('transform',' '.join(format(float(x),'.12g') for x in t[:3].T.reshape(-1)))
    settings=ET.fromstring(doc['object_settings'])
    for obj in settings.findall('object')+settings.findall('object/part'):
        for e in list(obj.findall('metadata')):
            k=e.get('key','')
            if k=='name':e.set('value','A2L poop bucket - accepted R8 fit - SUNLU PLA Basic')
            elif k.startswith('source_'):obj.remove(e)
            elif e.get('face_count') is not None:e.set('face_count',str(len(tm.faces)))
        for e in obj.findall('mesh_stat'):e.set('face_count',str(len(tm.faces)))
    for e in list(settings.find('plate').findall('metadata')):
        k=e.get('key')
        if k=='plater_name':e.set('value','A2L bucket - PRINT ON A1 - SUNLU PLA Basic')
        elif k in ['gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file']:settings.find('plate').remove(e)
    rels=ET.Element('Relationships',xmlns=R);child_rels=ET.Element('Relationships',xmlns=R)
    rt='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'
    ET.SubElement(rels,'Relationship',Target='/3D/3dmodel.model',Id='rel-1',Type=rt)
    ET.SubElement(child_rels,'Relationship',Target='/'+path,Id='rel-2',Type=rt)
    files={'[Content_Types].xml':doc['content_types'].encode(),'_rels/.rels':xml(rels),
           '3D/_rels/3dmodel.model.rels':xml(child_rels),'3D/3dmodel.model':xml(root),path:xml(child),
           'Metadata/model_settings.config':xml(settings),'Metadata/project_settings.config':json.dumps(cfg,indent=2).encode()}
    save(EDIT,files)
    print('Accepted R8 interface matches full bucket floor/wall; SUNLU profile applied. Slicing A1.',flush=True)
    result=native(EDIT,WORK/'slice',True);sliced=package(WORK/'slice/sliced.3mf')
    for data in [files,sliced]:
        saved=json.loads(data['Metadata/project_settings.config']);assert saved==cfg
        for k,v in locked.items():assert saved[k]==v
        overrides=ET.fromstring(data['Metadata/model_settings.config'])
        assert len(overrides.findall('object'))==1 and len(overrides.findall('plate'))==1
        for obj in overrides.findall('object')+overrides.findall('object/part'):
            for e in obj.findall('metadata'):
                k=e.get('key')
                if k in cfg and k!='name':
                    v=cfg[k];assert e.get('value')==(v[0] if isinstance(v,list) else v)
    a,c=saved_mesh(files),saved_mesh(sliced)
    error=max(cKDTree(a.vertices).query(c.vertices)[0].max(),cKDTree(c.vertices).query(a.vertices)[0].max())
    assert error<1e-4 and c.is_volume and len(c.split())==1
    assert np.allclose(c.bounds,original.bounds+np.asarray(doc['placement_mm']),atol=1e-4)
    gc=sliced['Metadata/plate_1.gcode'].decode();get_cfg=lambda s:dict(re.findall(r'^; (\w+) = (.*)$',s,re.M))
    gcfg=get_cfg(gc)
    for k,v in locked.items():
        if k not in ['filament_settings_id']:
            assert gcfg.get(k)==(v[0] if isinstance(v,list) else v),(k,gcfg.get(k),v)
    assert preset['name'] in gcfg['filament_settings_id']
    assert re.search(r'^M(?:140|190) S65\b',gc,re.M)
    assert re.search(r'^M(?:104|109) S220\b',gc,re.M)
    checksum=hashlib.md5(sliced['Metadata/plate_1.gcode']).hexdigest()
    assert sliced['Metadata/plate_1.gcode.md5'].decode().strip().lower()==checksum
    audit=scan_gcode(gc.replace('; FEATURE: Support transition','; FEATURE: Support'))
    assert audit['conservative_bed_edge_clearance_mm']>4.5
    assert audit['features'].get('Support',0)>0 and audit['features'].get('Support interface',0)>0
    assert audit['features'].get('Sparse infill',0)>0 and 'Prime tower' not in audit['features']
    zs=audit['model_extrusion_z_by_filament_mm'];assert list(zs)==['1'] and len(zs['1'])==754
    info=ET.fromstring(sliced['Metadata/slice_info.config']);warnings=[e.attrib for e in info.findall('plate/warning')]
    assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
    filament=info.find('plate/filament');assert filament.get('tray_info_idx')==preset['filament_id']
    FINAL.write_bytes((WORK/'slice/sliced.3mf').read_bytes())
    reopen=native(FINAL,WORK/'reopened');assert get_cfg((WORK/'reopened/plate_1.gcode').read_text())==gcfg
    after={rel(p):sha(p) for p in protected};assert before==after
    estimate=result['sliced_plates'][0]
    report=dict(revision='r10',project=rel(FINAL),sha256=sha(FINAL),printer='Bambu Lab A1',plates=1,
                source_project=doc['source_path'],source_sha256=doc['source_sha256'],
                accepted_sample=doc['fit_path'],accepted_sample_sha256=doc['fit_sha256'],
                user_approval='2026-11-07: that is it, update the project, set it for my sunlu pla basic, commit and push.',
                physical_status='User approved the R8 design and requested promotion. A successful physical R8 print/fit was not explicitly stated; full-height bucket has not been physically confirmed.',
                interface=doc['fit_metadata'],registration_xy_mm=registration,
                retained_outer_back_margin_mm=rear_margin,
                retained_outer_back_note='The original full-bucket back wall remains in place, 3.175 mm behind the flat sample edge. All fitted inner contours and the convex tip arc match R8 exactly.',
                floor_match_error_mm2=fit_error,wall_match_errors_mm2=wall_checks,
                outside_changed_domain_error_mm3=preservation,front_handle_error_mm3=front_error,lip_error_mm3=lip_error,
                mesh_cleanup_error_mm3=cleanup,changed_domain_mm=[[32,160,-1],[150,rear_y+1,200]],
                overall_dimensions_mm=tm.extents.tolist(),floor_thickness_mm=1.98,wall_thickness_mm=2,low_rim_height_mm=58,
                native_mesh_roundtrip_error_mm=float(error),placed_bounds_mm=c.bounds.tolist(),
                preset_source=doc['preset_source_path'],preset_sha256=doc['preset_sha256'],
                filament_settings_differences={k:v for k,v in cfg_diff.items() if k not in ['support_type','support_style']},
                support_settings_differences={k:v for k,v in cfg_diff.items() if k in ['support_type','support_style']},
                applied_preset_keys=applied,locked_settings=locked,
                native_slice=result,native_reopen=reopen,gcode_md5=checksum,toolpath_audit=audit,warnings=warnings,
                estimated_seconds=estimate['total_predication'],estimated_pla_g=estimate['filaments'][0]['total_used_g'],
                protected_before=before,protected_after=after,
                reference_sha256={p.name:sha(p) for p in REF.iterdir() if p.is_file()},
                stl_sha256=sha(OUT/'Bucket.stl'),stl_cleanup_tolerance_mm=.0001,
                stl_cleanup_difference_mm3=stl_cleanup,print_job_sent=False)
    (OUT/'native-preview.png').write_bytes(sliced['Metadata/plate_1.png'])
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    # This is deliberately a mesh snapshot, matching the repository convention.
    (OUT/'Bucket.scad').write_text('// Full-bucket mesh snapshot; redundant tessellation cleaned within 0.0001 mm.\n// Print using the adjacent 3MF, which retains the native mesh and settings.\nimport("Bucket.stl", convexity=20);\n',encoding='utf8')
    render_preview(actual_floor,template,report)
    print(json.dumps({k:report[k] for k in ['project','sha256','estimated_seconds','estimated_pla_g','filament_settings_differences']},indent=2))


def render_preview(floor,template,report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,(ax,detail)=plt.subplots(1,2,figsize=(12,7),facecolor='#f5f7f8')
    ax.imshow(plt.imread(OUT/'native-preview.png'));ax.axis('off');ax.set_title('Full bucket · native Bambu preview')
    p=floor.intersection(box(34,160,98,248));x,y=p.exterior.xy
    detail.fill(x,y,color='#d5e6e9',edgecolor='#19596b',lw=1.5)
    inner=floor.buffer(-2,join_style='mitre').intersection(box(34,160,98,248))
    if inner.geom_type=='Polygon':
        x,y=inner.exterior.xy;detail.fill(x,y,color='#f5f7f8')
    x,y=template.exterior.xy;detail.plot(x,y,'--',color='#c47b32',lw=1.3,label='Accepted R8 sample')
    detail.set_aspect('equal');detail.axis('off');detail.set_title('Exact fitted contour · full 58 mm rim height')
    detail.legend(loc='lower left',bbox_to_anchor=(0,-.06),frameon=False)
    fig.suptitle('A2L poop bucket · approved R8 outline · print on A1',fontsize=21,weight='bold',y=.97)
    minutes=round(report['estimated_seconds']/60)
    fig.text(.5,.05,f'SUNLU PLA Basic · 220°C nozzle / 65°C bed · {minutes//60} h {minutes%60} min · {report["estimated_pla_g"]:.1f} g\n'
             '19/32 inch inside curves · 1/2 inch convex rear tip · narrowed pillar spacing',ha='center',fontsize=11)
    fig.tight_layout(rect=(0,.11,1,.93));fig.savefig(OUT/'preview.png',dpi=160);plt.close(fig)


if __name__=='__main__':main()
