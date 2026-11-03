"""New crate accessory. Reads production dimensions; never changes production."""
from pathlib import Path
import hashlib, json, re, subprocess, sys, zipfile, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'.work/python-libs'), str(ROOT/'scripts'),
                str(ROOT/'output/A2L-Poop-Bucket-r1')]
import numpy as np
import trimesh
import manifold3d as mf
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
import development_3mf as d
from build_bucket import resolve
from mesh_sections import mesh_slice
from validate_print_project import scan_gcode, transform, props, TOKEN

OUT = Path(__file__).resolve().parent
WORK = ROOT/'.work/dara-crate-clips-r1'
SOURCE = ROOT/'Dara.3mf'
DONOR = ROOT/'output/Sanding-Block-Quarter-Sheet-A1-PETG/Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'
EDIT = OUT/'Dara-Crate-Clips-A1-PETG-r1-Editable.3mf'
FINAL = OUT/'Dara-Crate-Clips-A1-PETG-r1.3mf'
TITLE = 'Dara crate clips - A1 SUNLU PETG - 8% gyroid - r1'
WIDTH, OFFSET, THICKNESS, CLEARANCE = 28., 10., 13.5, .4
OVERLAP, HOLE, WALL = 6.35, 4.7625, 4.
LIP_BOTTOM = OFFSET+THICKNESS+CLEARANCE
PROFILE = 'SUNLU PETG (Generic PETG base) @BBL A1'
LOCKED = dict(layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',
              top_shell_layers='5',bottom_shell_layers='5',sparse_infill_density='8%',
              sparse_infill_pattern='gyroid',nozzle_diameter=['0.4'],curr_bed_type='Textured PEI Plate')

def load(p):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        return {n:z.read(n) for n in z.namelist()}

def save(p,f):
    with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in f.items(): z.writestr(n,b)

def hashes():
    paths = [SOURCE,DONOR,ROOT/'AGENTS.md']
    paths += list((ROOT/'working/bambu/Dara-A1-Companion').glob('*.3mf'))
    paths += list((ROOT/'working/bambu/Dara-Photo-Frame-A2L').glob('Dara-A2L-*.3mf'))
    return {str(p):d.sha(p) for p in paths}

def cube(lo,hi):
    return mf.Manifold.cube(tuple(np.array(hi)-lo)).translate(lo)

def xz_prism(points,y0,width):
    return mf.CrossSection([points]).extrude(width).rotate((90,0,0)).translate((0,y0+width,0))

def make_clip():
    # X positive enters the knot. Z=0 is OSB contact. Y spans the 28 mm clip.
    # Nominal knot edge X=.4; lip ends at 6.75, giving exactly 6.35 overlap.
    side = [(-25,0),(10,0),(10,10),(0,10),(0,LIP_BOTTOM),
            (OVERLAP+CLEARANCE,LIP_BOTTOM),(OVERLAP+CLEARANCE,LIP_BOTTOM+3.5),
            (OVERLAP+CLEARANCE-.5,LIP_BOTTOM+4),(-3.5,LIP_BOTTOM+4),
            (-4,LIP_BOTTOM+3.5),(-4,4),(-25,4)]
    s = xz_prism(side,-14,28)
    gusset = [(-25,3.5),(-3.5,3.5),(-3.5,LIP_BOTTOM+.5)]
    for y in (-14,10):s += xz_prism(gusset,y,4)
    s -= mf.Manifold.cylinder(6,HOLE/2,HOLE/2,128).translate((-15,0,-1))
    m=d.mesh(s)
    assert m.is_volume and len(m.split())==1
    assert abs((s^cube((.4,-14,10),(30,14,23.5))).volume())<1e-7
    # A 14 mm diameter head/driver envelope remains clear above the screw seat.
    access=mf.Manifold.cylinder(40,7,7,96).translate((-15,0,4.001))
    assert abs((s^access).volume())<1e-7
    at2=mesh_slice(m,2)
    hole=next(Polygon(h) for h in at2.interiors)
    assert abs(hole.bounds[2]-hole.bounds[0]-HOLE)<1e-5
    assert abs(hole.bounds[3]-hole.bounds[1]-HOLE)<1e-5
    return m,side

def production_dimensions(f):
    c=ET.fromstring(f['Metadata/model_settings.config'])
    byname={props(o)['name']:o.get('id') for o in c.findall('object')}
    mounts=[]
    for k in range(1,5):
        name=f'B{k} A2L wall block';parts,_=d.read_object(f,byname[name]);m=parts[0]['mesh']
        a=mesh_slice(m,9.99).area;b=mesh_slice(m,10.01).area
        assert a>4000 and b<500 and abs(m.bounds[1,2]-13)<1e-4
        mounts.append(dict(name=name,id=byname[name],body_top_mm=10,key_top_mm=13,
                           section_below_body_top_mm2=a,section_above_body_top_mm2=b))
    p,_=d.read_object(f,byname['F2 A2L knot'])
    maxima=[float(x['mesh'].bounds[1,2]) for x in p if x['subtype']=='normal_part']
    assert abs(max(maxima)-13.5)<1e-4
    return dict(wall_mounts=mounts,knot_reference='F2 A2L knot',knot_id=byname['F2 A2L knot'],
                normal_part_top_heights_mm=maxima,standoff_mm=10,knot_full_height_mm=13.5,
                note='13 mm wall-block total includes 3 mm keys inserted into knot. Fit exposed full-height edges, away from M/pins, recessed weave, joints, photos and rear hardware.')

def gusset_support(gcode,regions):
    """Check actual support interface below each new upper-gusset area at Z24."""
    x=y=z=e=0.;relative_e=False;relative_xyz=False;feature='Custom';width=.5
    beads=[]
    for raw in gcode.splitlines():
        line=raw.strip()
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        if line.startswith('; LINE_WIDTH: '):width=float(line.split(': ',1)[1])
        code=line.split(';',1)[0].strip()
        if not code:continue
        command=code.split()[0]
        if command=='M83':relative_e=True
        elif command=='M82':relative_e=False
        elif command in ('G90','G91'):relative_xyz=command=='G91'
        elif command=='G92':
            v={k:float(n) for k,n in TOKEN.findall(code)}
            x,y,z,e=v.get('X',x),v.get('Y',y),v.get('Z',z),v.get('E',e)
        elif command in ('G0','G1'):
            v={k:float(n) for k,n in TOKEN.findall(code)}
            nx,ny,nz=[old+v.get(k,0) if relative_xyz else v.get(k,old) for k,old in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative_e else v.get('E',e)-e
            if feature=='Support interface' and de>0 and abs(nz-23.8)<.001 and (nx!=x or ny!=y):
                beads.append(LineString([(x,y),(nx,ny)]).buffer(width/2))
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative_e else v.get('E',e)
    footprint=unary_union(beads);checks=[]
    for name,region in regions:
        backed=region.intersection(footprint).area
        # Interface uses .42 mm beads with .5 mm gaps: it is intentionally
        # discontinuous. Check spatial distribution, not a solid support slab.
        near=region.intersection(footprint.buffer(.75)).area/region.area
        assert backed>0 and near>.99,(name,region.area,backed,near)
        checks.append(dict(name=name,new_upper_gusset_area_mm2=region.area,
                           support_interface_at_z_mm=23.8,underside_z_mm=24,
                           interface_bead_coverage_mm2=backed,coverage_fraction=backed/region.area,
                           fraction_within_075mm_of_interface_bead=near))
    return checks

def render(m,side):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch, Rectangle
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(13,6.3),facecolor='#f4f5f6')
    ax=fig.add_subplot(121);ax.set_facecolor('#f4f5f6')
    ax.add_patch(Rectangle((-30,-5),65,5,color='#c8aa7b'))
    ax.add_patch(Patch(side,facecolor='#318091',edgecolor='#17404a'))
    ax.add_patch(Rectangle((.4,10),29.6,13.5,facecolor='#e5e3df',edgecolor='#595b62'))
    ax.text(14,16,'Knot\n13.5 mm',ha='center',va='center',fontsize=11)
    ax.text(12,-2.5,'OSB backer',ha='center',va='center',fontsize=10)
    ax.plot([-15,-15],[-3,8],color='#555',lw=3);ax.plot([-19,-11],[5,5],color='#555',lw=4)
    def dim(p,q,label,tx,ty):
        ax.annotate('',q,p,arrowprops=dict(arrowstyle='<->',color='#182b3c',lw=1.2))
        ax.text(tx,ty,label,fontsize=10,ha='center',va='center')
    dim((33,0),(33,10),'10 mm',39,5)
    dim((.4,31),(6.75,31),'6.35 mm / 1/4 in',10,35)
    ax.plot([.4,.4],[24,32],color='#999',lw=.8);ax.plot([6.75,6.75],[27.9,32],color='#999',lw=.8)
    ax.annotate('0.4 mm face clearance',xy=(5,23.7),xytext=(-25,39),fontsize=10,arrowprops=dict(arrowstyle='->'))
    ax.text(-24,-10,'Center section; gussets lie on either side of screw',fontsize=9)
    ax.set(xlim=(-30,45),ylim=(-12,44));ax.set_aspect('equal');ax.axis('off')
    ax.set_title('Installed fit',fontsize=15)
    bx=fig.add_subplot(122,projection='3d');bx.set_facecolor('#f4f5f6')
    light=np.array([-1,-.5,1]);light/=np.linalg.norm(light)
    shade=.55+.4*np.maximum(0,m.face_normals@light)
    colors=np.c_[np.array([.20,.56,.64])[None,:]*shade[:,None],np.ones(len(shade))]
    bx.add_collection3d(Poly3DCollection(m.triangles,facecolors=colors,edgecolors='none'))
    bx.set(xlim=(-27,12),ylim=(-18,18),zlim=(0,31));bx.set_box_aspect((39,36,31))
    bx.view_init(elev=28,azim=-135);bx.axis('off');bx.set_title('Two 4 mm gussets; open screw access',fontsize=14)
    fig.suptitle('Dara crate clip r1  |  A1 / SUNLU PETG  |  8 identical clips',fontsize=17)
    fig.text(.60,.05,'3/16 in (4.7625 mm) through-hole\n28 mm width; 4 mm lip and upright',fontsize=11)
    fig.tight_layout(rect=(0,.06,1,.93));fig.savefig(OUT/'clip-design.png',dpi=170);plt.close(fig)

def build():
    OUT.mkdir(exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    before=hashes();production=load(SOURCE);ref=production_dimensions(production)
    donor=load(DONOR);old=json.loads(donor['Metadata/project_settings.config']);cfg=dict(old)
    cfg.update(resolve('machine','Bambu Lab A1 0.4 nozzle'))
    cfg.update(resolve('filament','Generic PETG @BBL A1'))
    cfg.update(LOCKED)
    cfg.update(print_settings_id=TITLE,printer_model='Bambu Lab A1',printer_variant='0.4',
               printer_settings_id='Bambu Lab A1 0.4 nozzle',print_compatible_printers=['Bambu Lab A1 0.4 nozzle'],
               filament_settings_id=[PROFILE],filament_ids=['GFG99'],filament_vendor=['SUNLU'],filament_colour=['#FFFFFF'],
               default_filament_profile=['Generic PETG @BBL A1'],
               inherits_group=['','Generic PETG @BBL A1','Bambu Lab A1 0.4 nozzle'],
               enable_support='1',support_type='normal(auto)',support_style='snug',
               support_on_build_plate_only='0',support_filament='1',support_interface_filament='1',
               support_top_z_distance='0.2',support_bottom_z_distance='0.2',
               brim_type='no_brim',brim_width='0',enable_prime_tower='0',enable_arc_fitting='0',
               print_sequence='by layer')
    # All local part settings are new; no source accessory geometry or overrides copied.
    m,side=make_clip();m.export(OUT/'Dara-Crate-Clip-r1.stl')
    rotation=np.array([[1,0,0],[0,0,-1],[0,1,0]])
    entries=[]
    for i in range(8):
        t=d.centered(m,rotation,xy=(53+50*(i%4),94+68*(i//4)))
        entries.append(dict(name=f'Crate clip {i+1} - 10mm spacer - 1-4in lip',
                            parts=[dict(mesh=m,settings=dict(extruder='1'))],
                            transform=t,settings=dict(extruder='1')))
    d.source=lambda:donor;d.source_path=lambda:DONOR
    records=d.write_project(EDIT,[entries],TITLE,settings_update=cfg)
    # This project contains one material and one plate.
    f=load(EDIT);c=ET.fromstring(f['Metadata/model_settings.config'])
    c.find("plate/metadata[@key='filament_maps']").set('value','1')
    c.find("plate/metadata[@key='filament_volume_maps']").set('value','0')
    f['Metadata/model_settings.config']=ET.tostring(c,encoding='utf-8',xml_declaration=True);save(EDIT,f)
    render(m,side)
    report=dict(revision='r1',source=str(SOURCE),source_sha256=d.sha(SOURCE),production_reference=ref,
        settings_donor=str(DONOR),settings_donor_sha256=d.sha(DONOR),protected_before=before,
        requested_changes='New separate PETG crate clips; no production geometry or settings altered.',
        dimensions_mm=dict(standoff=OFFSET,knot_thickness=THICKNESS,face_clearance=CLEARANCE,
                           lateral_clearance=CLEARANCE,overlap=OVERLAP,screw_hole=HOLE,width=WIDTH,
                           gusset_thickness=4,lip_thickness=4,screw_flange_thickness=4,
                           under_knot_tongue_reach=9.6,overall=m.extents.tolist()),
        screw_head_access_diameter_mm=14,nominal_knot_collision_mm3=0,
        quantity=8,geometry=dict(watertight=True,components=1,volume_mm3=m.volume),
        orientation='Side down: print layer planes span the C profile; automatic snug supports beneath upper gusset and other detected overhangs.',
        material=dict(name='SUNLU standard PETG',profile=PROFILE,base='Generic PETG @BBL A1',
                      nozzle_c=255,bed_c=80,max_volumetric_mm3_s=8,spool_calibrated=False,
                      source_url='https://www.sunlu.com/products/petg-3d-printing-filament',
                      manufacturer_nozzle_guidance='240-260 C; standard PETG, not matte or CF'),
        settings_changes_from_petg_donor={k:dict(before=old.get(k),after=cfg.get(k),purpose=(
            'Clip support/removal configuration' if k.startswith(('support_','brim_')) else
            'Official A1 / Generic PETG profile and identity for separate SUNLU PETG accessory'))
            for k in sorted(set(old)|set(cfg)) if old.get(k)!=cfg.get(k)},
        locked_settings=LOCKED,records=records,editable_sha256=d.sha(EDIT),
        physical_fit_verified=False,shipping_load_tested=False,print_job_sent=False)
    d.save_json(OUT/'validation.json',report)
    assert hashes()==before
    sliced=WORK/'slice';sliced.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (WORK/'slice.log').open('w',encoding='utf8') as log:
        r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(sliced),str(EDIT)],
                         cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    assert r.returncode==0,(WORK/'slice.log').read_text(errors='replace')[-3000:]
    print('Slice complete',flush=True)

def validate():
    report=json.loads((OUT/'validation.json').read_text())
    original=load(EDIT);f=load(WORK/'slice/sliced.3mf')
    result=json.loads((WORK/'slice/result.json').read_text());p=result['sliced_plates'][0]
    assert result['return_code']==0 and p['warning_message']=='',result
    expected={**LOCKED,'printer_model':'Bambu Lab A1','printer_settings_id':'Bambu Lab A1 0.4 nozzle',
              'filament_type':['PETG'],'filament_settings_id':[PROFILE],'nozzle_temperature':['255'],
              'nozzle_temperature_initial_layer':['255'],'textured_plate_temp':['80'],
              'textured_plate_temp_initial_layer':['80'],'filament_max_volumetric_speed':['8'],
              'enable_support':'1','support_type':'normal(auto)','support_style':'snug','enable_prime_tower':'0'}
    machine=resolve('machine','Bambu Lab A1 0.4 nozzle')
    checks=[];footprints=[];gusset_regions=[]
    for package in (original,f):
        cfg=json.loads(package['Metadata/project_settings.config'])
        for k,v in expected.items(): assert cfg[k]==v,(k,cfg[k],v)
        for k in ['machine_start_gcode','machine_end_gcode','change_filament_gcode','layer_change_gcode','time_lapse_gcode']:
            assert cfg[k]==machine[k],k
        c=ET.fromstring(package['Metadata/model_settings.config'])
        assert len(c.findall('object'))==8 and len(c.findall('plate'))==1
        for obj in c.findall('object'):
            assert len(obj.findall('part'))==1
            for node in [obj]+obj.findall('part'):
                for k,v in props(node).items():
                    if k in expected:assert v==expected[k],(k,v)
    root=ET.fromstring(f['3D/3dmodel.model'])
    original_ids={props(o)['name']:o.get('id') for o in ET.fromstring(original['Metadata/model_settings.config']).findall('object')}
    for it in root.find(d.tag('build')):
        oid=it.get('objectid');parts,st=d.read_object(f,oid);a,_=d.read_object(original,original_ids[st['name']])
        ma=a[0]['mesh'];m=parts[0]['mesh']
        # Native export centers local mesh coordinates, compensating in the pose.
        ma.apply_translation(m.bounds.mean(axis=0)-ma.bounds.mean(axis=0))
        err=max(cKDTree(ma.vertices).query(m.vertices)[0].max(),cKDTree(m.vertices).query(ma.vertices)[0].max())
        assert err<1e-4 and m.is_volume and len(m.split())==1
        m.apply_transform(transform(it.get('transform')))
        assert min(np.max(np.abs(m.bounds-np.array(r['body_bounds_mm']))) for r in report['records'])<1e-4
        gusset_regions.append((st['name'],mesh_slice(m,24.1).difference(mesh_slice(m,23.9))))
        assert abs(m.bounds[0,2])<1e-4 and np.all(m.bounds[0,:2]>5) and np.all(m.bounds[1,:]<251)
        contact=mesh_slice(m,.1);assert contact.area>300
        footprint=Polygon(m.vertices[:,:2]).convex_hull
        for other in footprints:assert footprint.distance(other)>14
        footprints.append(footprint)
        checks.append(dict(name=st['name'],mesh_roundtrip_error_mm=float(err),bounds_mm=m.bounds.tolist(),
                           bed_contact_area_mm2=contact.area,watertight=True,components=1))
    g=f['Metadata/plate_1.gcode'].decode();gc=dict(re.findall(r'^; (\w+) = (.*)$',g,re.M))
    for k,v in expected.items():
        if k=='filament_settings_id':continue
        assert gc.get(k)==(v[0] if isinstance(v,list) else v),(k,gc.get(k),v)
    digest=hashlib.md5(f['Metadata/plate_1.gcode']).hexdigest()
    assert f['Metadata/plate_1.gcode.md5'].decode().strip().lower()==digest
    audit=scan_gcode(g)
    local_support=gusset_support(g,gusset_regions)
    assert audit['features'].get('Support',0)>0 and audit['features'].get('Support interface',0)>0
    assert audit['features'].get('Sparse infill',0)>0 and 'Prime tower' not in audit['features']
    assert audit['conservative_bed_edge_clearance_mm']>10
    assert list(audit['model_extrusion_z_by_filament_mm'])==['1']
    # Support transition is omitted from the model-layer classification.
    modelaudit=scan_gcode(g.replace('; FEATURE: Support transition','; FEATURE: Support'))
    zs=modelaudit['model_extrusion_z_by_filament_mm']['1']
    assert len(zs)==140 and max(abs(z/.2-round(z/.2)) for z in zs)<.001
    info=ET.fromstring(f['Metadata/slice_info.config'])
    warnings=[e.attrib for e in info.findall('plate/warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    modelid=json.loads(Path(r'C:\Program Files\Bambu Studio\resources\profiles\BBL\machine\Bambu Lab A1.json').read_text())['model_id']
    info.find("plate/metadata[@key='printer_model_id']").set('value',modelid)
    f['Metadata/slice_info.config']=ET.tostring(info,encoding='utf-8',xml_declaration=True)
    save(FINAL,f)
    (OUT/'native-plate-preview.png').write_bytes(f['Metadata/plate_1.png'])
    after=hashes();assert after==report['protected_before']
    report.update(current_file=FINAL.name,current_sha256=d.sha(FINAL),native_slice_validated=True,
                  mesh_validation=checks,effective_settings=expected,gcode_md5=digest,
                  native_result=result,native_warnings=warnings,toolpath_validation=audit,
                  per_clip_upper_gusset_support=local_support,
                  model_layers=140,protected_after=after,printer_model_id=modelid,
                  estimated_seconds=p['total_predication'],estimated_petg_g=p['filaments'][0]['total_used_g'])
    d.save_json(OUT/'validation.json',report)
    minutes=round(p['total_predication']/60)
    (OUT/'README.txt').write_text(f'''Dara crate clips - A1 SUNLU PETG - r1

CURRENT PROJECT: {FINAL.name}
SHA-256: {d.sha(FINAL)}
Eight identical clips on one plate; includes native A1 toolpaths.
Open as a PROJECT in Bambu Studio to retain its configuration.
Editable companion and single-clip STL are geometry sources for this same r1.

FIT
10.00 mm spacer matches the saved B1-B4 wall-block bodies.
Wall-block keys add 3 mm but insert into the knot, so are not part of the offset.
Fits a 13.50 mm full-height knot edge; 0.40 mm top and side clearance.
Top lip overlaps the nominal knot edge by 6.35 mm (1/4 inch).
28 mm wide; 4 mm lip, upright, screw flange and each of two gussets.
3/16 inch (4.7625 mm) cylindrical screw hole; flat pan-head seat.
14 mm diameter clear head/driver envelope, 4 mm printed stock beneath head.
No countersink. Choose screw length for the actual OSB thickness and engagement.

USE
Remove supports from the upper gusset and any hole support; check the hole is clear.
Slip the lower tongue beneath an exposed full-height knot edge, with the upper
lip over its face. Keep 0.4 mm between the clip upright and knot edge.
Place opposing clips around the perimeter, keeping the existing wall mounts flat
on the same OSB. Avoid recessed weave, joints, M parts/pins, photo tabs and screws.
Check the lip has its full overlap and that curved edges fit the 28 mm clip width.
Snug the screw to the OSB; the clip captures the knot without compressing its face.
The screw seats on the 4 mm flange; gussets brace the upright on both sides.
No padding thickness is included in the 0.4 mm clearance.

PRINT
Bambu Lab A1 / 0.4 mm nozzle / Textured PEI Plate / SUNLU standard PETG.
Generic PETG A1 base: 255 C nozzle, 80 C bed, 8 mm3/s volumetric limit.
SUNLU standard PETG guidance: https://www.sunlu.com/products/petg-3d-printing-filament
This is a base profile, not a calibration of the user's spool.
0.20 mm first and later layers; 4 walls; 5 top and bottom layers; 8% gyroid.
White slot 1 display color; use the actual PETG spool. No prime tower.
Clips print side-down, with automatic snug PETG supports for the upper gussets.
Estimate including supports: {minutes//60} h {minutes%60} min / {report['estimated_petg_g']:.2f} g.

VALIDATION
Production source: {SOURCE}
Source SHA-256: {report['source_sha256']}
Measured saved production wall bodies/key tops and F2 full-height edge.
New clip is one closed connected solid; nominal edge has no mesh interference.
Screw hole, head/driver access and exact spacer/lip dimensions checked.
Native Bambu slice passed without printability warnings; support/interface
extrusion, 140 model layers, bed bounds, spacing and G-code checksum checked.
Actual interface beads at Z23.8 back each upper gusset starting at Z24.0.
Locked settings and all object/volume overrides checked in editable and sliced
3MF, plus G-code. Saved mesh matches source within 0.0001 mm.
Production, named complete/editable projects and A1 companion hashes unchanged.
Physical fit, support removal, surface marking and shipping-load resistance
remain untested. Dry-fit a clip before using the set to secure the artwork.
No print job was sent. See validation.json and clip-design.png.
''',encoding='utf8')
    d.save_json(OUT/'SHA256SUMS.json',{p.name:d.sha(p) for p in [FINAL,EDIT,OUT/'Dara-Crate-Clip-r1.stl',OUT/'build_clips.py']})
    print(json.dumps(dict(file=str(FINAL),sha256=d.sha(FINAL),minutes=minutes,grams=report['estimated_petg_g'],warnings=warnings),indent=2))

if __name__=='__main__':
    if '--validate' not in sys.argv:build()
    validate()
