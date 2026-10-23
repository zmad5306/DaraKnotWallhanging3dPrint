# Historical design source retained for provenance, not a current rebuild command.
# Uses retired project paths/settings; do not regenerate current releases with it.
"""Production-outline honeycomb tracing templates, A1 / SUNLU clear PLA.

Run with .work/python-libs and scripts on PYTHONPATH. Production is read-only.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, mapping, shape
from shapely import affinity, union_all
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as PlotPath

import development_3mf as d
from develop_m_veneer import prism
from mesh_sections import mesh_slice
from validate_print_project import scan_gcode, TOKEN

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Dara.3mf'
DONOR = ROOT / 'working/bambu/Dara-A1-Companion/Dara-A1-Companion.3mf'
OUT = ROOT / 'output/Dara-Photo-Tracing-Backers-A1-r1'
WORK = ROOT / '.work/photo-tracing-backers-a1-r1'
STEM = 'Dara-Photo-Tracing-Backers-A1-r1'
EDIT = OUT / (STEM + '-Editable.3mf')
FINAL = OUT / (STEM + '.3mf')
EXE = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
HEIGHT, RIM, WEB, HEX_FLATS = 2.0, 3.0, 1.2, 18.0
PROFILE = 'SUNLU Transparent PLA @BBL A1 - Dara tracing'
TITLE = 'Dara photo tracing r1 - A1 - 8% gyroid'
MATERIAL_URL = 'https://www.sunlu.com/products/transparent-pla-filament'
LOCKED = dict(printer_model='Bambu Lab A1', nozzle_diameter=['0.4'],
              layer_height='0.2', initial_layer_print_height='0.2',
              wall_loops='4', top_shell_layers='5', bottom_shell_layers='5',
              sparse_infill_density='8%', sparse_infill_pattern='gyroid',
              curr_bed_type='Textured PEI Plate')
MACHINE_COMMANDS = ['machine_start_gcode', 'machine_end_gcode',
                    'change_filament_gcode', 'layer_change_gcode', 'time_lapse_gcode']


def read_project(path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist() if n.startswith('3D/') or n in
                ['Metadata/project_settings.config', 'Metadata/model_settings.config',
                 '[Content_Types].xml', '_rels/.rels']}


def protected():
    paths = [SOURCE, ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf',
             ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf']
    paths += list(DONOR.parent.glob('*'))
    return {str(p.relative_to(ROOT)): d.sha(p) for p in paths if p.is_file()}


def clean_settings(values):
    return {k:v for k,v in values.items() if k and v is not None and k != 'name'}


def settings(base):
    s = copy.deepcopy(base)
    s['print_settings_id'] = TITLE
    # Only slot 1 is used; the other three saved material slots are preserved.
    for key, value in dict(filament_settings_id=PROFILE, filament_vendor='SUNLU',
                           filament_density='1.23', filament_max_volumetric_speed='8',
                           nozzle_temperature='210', nozzle_temperature_initial_layer='210',
                           textured_plate_temp='60', textured_plate_temp_initial_layer='60').items():
        s[key][0] = value
    for key, value in dict(initial_layer_speed='30', initial_layer_infill_speed='50',
                           outer_wall_speed='60', inner_wall_speed='80',
                           top_surface_speed='60', internal_solid_infill_speed='80',
                           sparse_infill_speed='80', gap_infill_speed='60').items():
        s[key] = [value]
    for key,value in LOCKED.items():
        assert s[key] == value, (key,s[key])
    assert s['enable_prime_tower'] == '0'
    assert s['enable_arc_fitting'] == '0'
    return s


def honeycomb(outline):
    interior = outline.buffer(-RIM, join_style=2)
    pitch_r = (HEX_FLATS + WEB) / math.sqrt(3)
    hole_r = HEX_FLATS / math.sqrt(3)
    holes = []
    for q in range(-12,13):
        for r in range(-12,13):
            cx,cy = 1.5*pitch_r*q, math.sqrt(3)*pitch_r*(r+q/2)
            h = Polygon([(cx+hole_r*math.cos(a*math.pi/3),
                          cy+hole_r*math.sin(a*math.pi/3)) for a in range(6)])
            clipped = h.intersection(interior)
            if clipped.is_empty:
                continue
            for p in [clipped] if clipped.geom_type == 'Polygon' else clipped.geoms:
                # Omit tiny rim slivers; retain useful sight windows only.
                if p.geom_type == 'Polygon' and p.area >= 8 and not p.buffer(-1.2).is_empty:
                    holes.append(p)
    cutouts = union_all(holes)
    result = outline.difference(cutouts)
    assert result.geom_type == 'Polygon' and result.is_valid
    assert len(result.interiors) == len(holes)
    assert min(h.distance(outline.exterior) for h in holes) >= RIM-1e-5
    assert min(h.distance(k) for i,h in enumerate(holes) for k in holes[:i]) >= WEB-1e-5
    return result, holes


def patch(poly, color):
    from shapely.geometry.polygon import orient
    p = orient(poly,1)
    vertices, codes = [], []
    for ring in [p.exterior, *p.interiors]:
        xy = np.array(ring.coords)
        vertices.extend(xy)
        codes.extend([PlotPath.MOVETO]+[PlotPath.LINETO]*(len(xy)-2)+[PlotPath.CLOSEPOLY])
    return PathPatch(PlotPath(vertices,codes), facecolor=color, edgecolor='#385261', lw=.35)


def preview(records):
    fig, axes = plt.subplots(2,4,figsize=(14,7.7),facecolor='#f3f4f2')
    for ax,rec in zip(axes.flat,sorted(records,key=lambda x:x['backer'])):
        p = shape(rec['material_outline'])
        ax.add_patch(patch(p,'#bad1dc'))
        ax.set(xlim=(-68,68),ylim=(-68,68),aspect='equal')
        ax.axis('off')
        ax.set_title(f"Backer {rec['backer']}  |  {rec['open_area_percent']:.0f}% open",fontsize=12,pad=5)
    fig.suptitle('Dara photo tracing templates',fontsize=22,x=.06,ha='left',y=.98)
    fig.text(.06,.925,'2.0 mm thick  /  3.0 mm tracing rim  /  1.2 mm ribs  /  18 mm hex openings',fontsize=12)
    fig.text(.06,.025,'Exact production outside edges. Blue shows printed material; white areas are through-holes.\nGeometry preview; printed transparency is not simulated.',fontsize=10,color='#435563')
    fig.subplots_adjust(left=.035,right=.985,top=.85,bottom=.10,wspace=.09,hspace=.18)
    fig.savefig(OUT/'Preview.png',dpi=160)
    plt.close(fig)


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    WORK.mkdir(parents=True,exist_ok=True)
    before = protected()
    prod, donor = read_project(SOURCE), read_project(DONOR)
    pcfg = ET.fromstring(prod['Metadata/model_settings.config'])
    acfg = ET.fromstring(donor['Metadata/model_settings.config'])
    ar = ET.fromstring(donor['3D/3dmodel.model'])
    original = json.loads(donor['Metadata/project_settings.config'])
    chosen = settings(original)
    source_ids = {d.props(o)['name']:o.get('id') for o in pcfg.findall('object')}
    plates,records = [],[]
    for pi,plate in enumerate(acfg.findall('plate')[:2]):
        entries = []
        for ins in plate.findall('model_instance'):
            aid = d.props(ins)['object_id']
            ast = d.props(acfg.find(f"object[@id='{aid}']"))
            name = ast['name']; idx = int(name.removeprefix('Backer'))
            parts,pst = d.read_object(prod,source_ids[name])
            donor_parts,_ = d.read_object(donor,aid)
            assert len(parts) == len(donor_parts) == 1
            old = parts[0]['mesh']; same = donor_parts[0]['mesh']
            assert np.array_equal(old.vertices,same.vertices)
            outline = mesh_slice(old,float(old.bounds[:,2].mean()))
            assert outline.geom_type == 'Polygon' and len(outline.interiors) == 0
            material,holes = honeycomb(outline)
            m = d.mesh(prism(material,0,HEIGHT))
            assert m.is_volume and len(m.split()) == 1
            check = mesh_slice(m,HEIGHT/2)
            exterior = Polygon(check.exterior)
            err = exterior.boundary.hausdorff_distance(outline.boundary)
            assert err < 1e-5 and exterior.symmetric_difference(outline).area < .001
            for z in [.01,.2,1.0,1.8,1.99]:
                assert mesh_slice(m,z).symmetric_difference(material).area < .001
            T = d.transform(ar.find(d.tag('build')).find(f"{d.tag('item')}[@objectid='{aid}']").get('transform'))
            T[0,3] -= pi*307.2
            assert np.allclose(T[:3,:3],np.eye(3))
            T[2,3] = 0
            obj_name = f'Backer {idx} - honeycomb tracing - 2mm'
            objsettings = clean_settings(ast)
            partsettings = clean_settings(parts[0]['settings'])
            entry = dict(name=obj_name,parts=[dict(mesh=m,subtype='normal_part',settings=partsettings)],
                         settings=objsettings,transform=T)
            entries.append(entry)
            stl = OUT/f'Backer-{idx}-Tracing-2mm.stl'; m.export(stl)
            record = dict(backer=idx,name=obj_name,plate=pi+1,source_object_id=source_ids[name],
                          source_name=name,source_mesh_sha256=hashlib.sha256(old.vertices.tobytes()+old.faces.tobytes()).hexdigest(),
                          source_thickness_mm=float(old.extents[2]),thickness_mm=HEIGHT,
                          size_mm=m.extents.tolist(),watertight=bool(m.is_volume),connected_components=1,
                          outline_max_error_mm=err,holes=len(holes),
                          open_area_percent=100*(1-material.area/outline.area),
                          material_volume_mm3=float(m.volume),full_bed_contact_area_mm2=material.area,
                          transform=T.tolist(),material_outline=mapping(material),source_outline=mapping(outline),
                          source_object_settings=clean_settings(pst),object_settings=objsettings,
                          volume_settings=partsettings,stl_sha256=d.sha(stl))
            records.append(record)
        for i,a in enumerate(entries):
            ma=a['parts'][0]['mesh'];va=ma.vertices@a['transform'][:3,:3].T+a['transform'][:3,3]
            assert va[:,:2].min() >= 1.49 and va[:,:2].max() <= 254.51
            pa=affinity.translate(Polygon(mesh_slice(ma,1).exterior),*a['transform'][:2,3])
            for b in entries[:i]:
                pb=affinity.translate(Polygon(mesh_slice(b['parts'][0]['mesh'],1).exterior),*b['transform'][:2,3])
                assert pa.distance(pb) > 1.5
        plates.append(entries)
    # Explicit donor avoids the utility's historical fallback project.
    d.source = lambda: donor
    d.source_path = lambda: DONOR
    d.write_project(EDIT,plates,TITLE,settings_update=chosen)
    diffs = {k:dict(old=original.get(k),new=chosen.get(k),purpose=(
             'Name this separate tracing process' if k=='print_settings_id' else
             'SUNLU transparent PLA temperature, speed and material configuration'))
             for k in set(original)|set(chosen) if original.get(k)!=chosen.get(k)}
    production_settings = json.loads(prod['Metadata/project_settings.config'])
    machine_diffs = {k:dict(old=production_settings.get(k),new=original.get(k),
                          purpose='Saved A1 companion donor, for the user-requested A1 printer')
                     for k in set(production_settings)|set(original)
                     if production_settings.get(k)!=original.get(k)}
    assert protected() == before
    report = dict(source_project=str(SOURCE),source_sha256=d.sha(SOURCE),
                  settings_donor=str(DONOR),settings_donor_sha256=d.sha(DONOR),
                  editable_sha256=d.sha(EDIT),protected_before=before,
                  revision='r1',changed_geometry='Through-holes inside a 3 mm rim; thickness 1.6 to 2.0 mm',
                  unchanged_geometry='Full saved production XY outlines; no cropping or scaling',
                  placement='Saved A1 companion plates 1-2 XY positions and rotations; bottoms at Z0',
                  rim_mm=RIM,rib_mm=WEB,hex_flats_mm=HEX_FLATS,records=records,
                  material=dict(product_url='https://www.amazon.com/dp/B07ZNG4L9P',
                                manufacturer_guidance_url=MATERIAL_URL,checked_date='2026-10-22',
                                name=PROFILE,slot=1,profile_kind='Custom project profile based on saved Generic PLA A1',
                                nozzle_c=210,bed_c=60,max_flow_mm3_s=8,density_g_cm3=1.23,
                                manufacturer_guidance='200-210 C at 50-100 mm/s; bed 50-60 C',
                                calibration='Saved A1 0.98 flow ratio, 0.8 mm / 30 mm/s retraction and cooling retained; no spool calibration performed'),
                  settings_changes_from_A1_donor=diffs,
                  production_to_A1_donor_settings_changes=machine_diffs,
                  locked_settings=LOCKED,physical_validation=False)
    d.save_json(OUT/'geometry-validation.json',report)
    preview(records)
    print(json.dumps(dict(editable=str(EDIT),backers=8,plates=2,
                          open_area_range_percent=[min(x['open_area_percent'] for x in records),
                                                   max(x['open_area_percent'] for x in records)]),indent=2),flush=True)


def native():
    target=WORK/'native';target.mkdir(exist_ok=True)
    with (target/'slice.log').open('w') as log:
        result=subprocess.run([str(EXE),'--slice','0','--export-3mf','sliced.3mf',
                               '--outputdir',str(target),str(EDIT)],cwd=EXE.parent,
                              stdout=log,stderr=subprocess.STDOUT,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    print('Native slice exit:',result.returncode,flush=True)
    assert result.returncode == 0


def extrusion_segments(text):
    x=y=z=e=0.;f=0.;width=.5;relative=False;feature='Custom'
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
        if raw.startswith('; LINE_WIDTH: '):width=float(raw.split(': ',1)[1])
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd=='G92':x,y,z,e=[v.get(k,old) for k,old in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[v.get(k,old) for k,old in zip('XYZ',(x,y,z))]
            f=v.get('F',f)
            de=v.get('E',0) if relative else v.get('E',e)-e
            if de>0 and feature!='Custom' and math.hypot(nx-x,ny-y)>.001:
                assert cmd in ['G0','G1']
                yield round(nz,3),[(x,y),(nx,ny)],width,feature,f/60
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)


def validate():
    evidence=json.loads((OUT/'geometry-validation.json').read_text())
    assert d.sha(EDIT)==evidence['editable_sha256']
    native=WORK/'native'; result=json.loads((native/'result.json').read_text())
    assert result['return_code']==0,result
    path=native/'sliced.3mf'
    f=read_project(path);ef=read_project(EDIT);donor=read_project(DONOR)
    s=json.loads(f['Metadata/project_settings.config']);es=json.loads(ef['Metadata/project_settings.config'])
    ds=json.loads(donor['Metadata/project_settings.config'])
    for label,project in [('editable',ef),('sliced',f)]:
        ps=json.loads(project['Metadata/project_settings.config'])
        for key,val in LOCKED.items():assert ps[key]==val,(label,key,ps[key])
        for key in MACHINE_COMMANDS:assert ps[key]==ds[key],(label,key)
        for key in evidence['settings_changes_from_A1_donor']:assert ps[key]==es[key],(label,key,ps[key],es[key])
        cfg=ET.fromstring(project['Metadata/model_settings.config'])
        assert len(cfg.findall('plate'))==2 and len(cfg.findall('object'))==8
        for obj in cfg.findall('object'):
            for node in [obj,*obj.findall('part')]:
                overrides=d.props(node)
                for key,val in LOCKED.items():
                    if key in overrides:assert overrides[key]==val,(label,key,overrides[key])
            assert d.props(obj)['extruder']=='1'
    roundtrip=[]
    cfg=ET.fromstring(f['Metadata/model_settings.config']);root=ET.fromstring(f['3D/3dmodel.model'])
    ecfg=ET.fromstring(ef['Metadata/model_settings.config']);eroot=ET.fromstring(ef['3D/3dmodel.model'])
    for rec in evidence['records']:
        co=next(o for o in cfg.findall('object') if d.props(o)['name']==rec['name'])
        eco=next(o for o in ecfg.findall('object') if d.props(o)['name']==rec['name'])
        pts=[]
        for project,r,c in [(f,root,co),(ef,eroot,eco)]:
            parts,st=d.read_object(project,c.get('id'));assert len(parts)==1
            mesh=parts[0]['mesh'];assert mesh.is_volume and len(mesh.split())==1
            T=d.transform(r.find(d.tag('build')).find(f"{d.tag('item')}[@objectid='{c.get('id')}']").get('transform'))
            pts.append(mesh.vertices@T[:3,:3].T+T[:3,3])
        a,b=pts;err=max(cKDTree(a).query(b)[0].max(),cKDTree(b).query(a)[0].max())
        assert err<.001,(rec['name'],err)
        roundtrip.append(dict(backer=rec['backer'],max_mesh_and_pose_error_mm=float(err)))
    plate_reports=[]
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for pi in [1,2]:
            gc=z.read(f'Metadata/plate_{pi}.gcode');text=gc.decode()
            assert z.read(f'Metadata/plate_{pi}.gcode.md5').decode().strip().lower()==hashlib.md5(gc).hexdigest()
            config=dict(re.findall(r'^; ([A-Za-z0-9_]+) = (.*)$',text,re.M))
            for key,val in LOCKED.items():
                want='0.4' if key=='nozzle_diameter' else val
                assert config.get(key)==want,(pi,key,config.get(key),want)
            for key,want in [('nozzle_temperature','210'),('nozzle_temperature_initial_layer','210'),
                              ('textured_plate_temp','60'),('textured_plate_temp_initial_layer','60'),
                              ('filament_max_volumetric_speed','8')]:
                assert config[key].split(',')[0].split(';')[0]==want,(key,config[key])
            audit=scan_gcode(text)
            assert audit['conservative_bed_edge_clearance_mm']>1
            assert set(audit['model_extrusion_z_by_filament_mm'])=={'1'}
            assert np.allclose(audit['model_extrusion_z_by_filament_mm']['1'],np.arange(.2,2.01,.2))
            assert not any(audit['features'].get(k,0) for k in ['Support','Support interface','Prime tower','Brim','Bridge'])
            model=[r for r in evidence['records'] if r['plate']==pi]
            polygons=[affinity.translate(shape(r['material_outline']),*np.array(r['transform'])[:2,3]) for r in model]
            expected=union_all(polygons)
            holes=union_all([Polygon(h).buffer(-.25) for p in polygons for h in p.interiors])
            by_layer={}
            max_speed=0
            for height,line,width,feature,speed in extrusion_segments(text):
                max_speed=max(max_speed,speed)
                by_layer.setdefault(height,[]).append(LineString(line).buffer(width/2,quad_segs=3))
            assert max_speed<=100.01,max_speed
            layer_checks=[]
            for height,beads in sorted(by_layer.items()):
                covered=union_all(beads)
                intrusion=covered.intersection(holes).area
                core=expected.buffer(-.35)
                gaps=core.difference(covered)
                missing=gaps.area
                gap_parts=[gaps] if gaps.geom_type=='Polygon' else list(gaps.geoms)
                largest_gap=max((p.area for p in gap_parts),default=0)
                assert intrusion<.01,(pi,height,'closed hole',intrusion)
                # Bead envelopes contain small seam and gap-fill voids. Check
                # continuity and local coverage, rather than summing thousands
                # of tiny voids into a false missing-rib result. The first-layer
                # largest void was visually inspected at the curved rim join.
                assert missing/core.area<.01,(pi,height,'core coverage',missing/core.area)
                assert largest_gap<2 and gaps.buffer(-.4).is_empty,(pi,height,'large void',largest_gap)
                assert covered.geom_type=='MultiPolygon' and len(covered.geoms)==4
                for polygon in polygons:
                    part_core=polygon.buffer(-.35)
                    matches=[c for c in covered.geoms if c.intersection(part_core).area>part_core.area*.99]
                    assert len(matches)==1,(pi,height,'disconnected template')
                layer_checks.append(dict(z_mm=height,extrusion_into_inset_holes_mm2=intrusion,
                                         uncovered_material_core_mm2=missing,
                                         core_coverage_percent=100*(1-missing/core.area),
                                         largest_internal_void_mm2=largest_gap,
                                         all_void_inradii_below_mm=.4,
                                         connected_template_count=4))
            est=next(p for p in result['sliced_plates'] if p['id']==pi)
            assert not est.get('warning_message'),est.get('warning_message')
            plate_reports.append(dict(plate=pi,backers=[r['backer'] for r in model],
                                      seconds=est['total_predication'],weight_g=sum(fil['total_used_g'] for fil in est['filaments']),
                                      gcode_sha256=hashlib.sha256(gc).hexdigest(),gcode_md5_verified=True,
                                      maximum_model_speed_mm_s=max_speed,toolpaths=audit,layer_checks=layer_checks))
            print('Validated plate',pi,'10 layers, through-holes and web/rim coverage',flush=True)
    before=evidence['protected_before'];after=protected();assert before==after
    log=(native/'slice.log').read_text(errors='replace')
    suspicious=[line for line in log.splitlines() if re.search(r'floating|collision|outside.*bed|non.manifold',line,re.I)]
    assert not suspicious,suspicious
    shutil.copyfile(path,FINAL)
    report=dict(revision='r1',project=str(FINAL),project_sha256=d.sha(FINAL),
                editable_sha256=d.sha(EDIT),source_sha256=evidence['source_sha256'],
                printer='Bambu Lab A1 / 0.4 mm',native_return_code=0,plates=plate_reports,
                total_seconds=sum(p['seconds'] for p in plate_reports),
                total_weight_g=sum(p['weight_g'] for p in plate_reports),
                roundtrip=roundtrip,locked_settings_verified_in_editable_slice_and_gcode=LOCKED,
                toolpath_coverage_method='Nominal bead envelopes: every template connected on all 10 layers, >99% coverage of material inset by 0.35 mm, every 0.25 mm inset sight-hole free of extrusion. Small seam/gap-fill voids retained; largest first-layer rim-junction void visually inspected.',
                machine_commands_match_saved_A1=True,protected_files_unchanged=True,
                protected_after=after,slicer_result=result,physical_validation=False)
    d.save_json(OUT/'native-validation.json',report)
    lines=[STEM,'CURRENT: separate tracing templates, not a replacement for the installed backers.','',
           'Open '+FINAL.name+' AS A PROJECT in Bambu Studio; all 8 templates are sliced for the A1.',
           'Plate 1: Backers 3, 1, 5, 7. Plate 2: Backers 4, 2, 6, 8.',
           'Slot 1: load SUNLU Transparent PLA (Amazon B07ZNG4L9P). Only slot 1 is used.',
           'Custom embedded profile: '+PROFILE,
           '210 C nozzle / 60 C textured PEI bed; outer/top 60 mm/s, inner/solid 80 mm/s;',
           'first layer 30 mm/s (fill 50); volumetric limit 8 mm3/s.',
           'Manufacturer reference: '+MATERIAL_URL,
           'A1 machine commands, saved cooling, 0.98 flow ratio and 0.8 mm / 30 mm/s retraction retained.',
           'This is an uncalibrated starting profile for the selected spool, not a factory SUNLU preset.','',
           '2.0 mm thick (original backers 1.6 mm); 3.0 mm rim; 1.2 mm ribs; 18 mm hex holes.',
           'Exact saved production outside outlines; no scale, cropping, or perimeter changes.',
           'Align over the photo, hold flat, and trace the OUTSIDE edge with a fine-point pencil.',
           'Use the matching numbered original backer/3MF object to identify each template.',
           'Keep the same face/orientation when transferring the outline; do not mirror asymmetrical outlines.',
           'The open cells provide direct sightlines. Printed plastic clarity has not been established.',
           'These thicker templates are intended for tracing; installed backer clearance is not qualified.','',
           '0.4 mm nozzle; 0.20 mm initial/regular layers; 4 walls; 5 top + 5 bottom layers;',
           '8% gyroid retained. At 2 mm total thickness, the top/bottom skins meet, so the material',
           'rim and ribs print solid; visibility comes from modeled through-holes.',
           'Flat on bed, no supports/brim/prime tower. Print at 100% scale.','']
    for p in plate_reports:
        lines.append(f"Plate {p['plate']}: {p['seconds']/60:.1f} min, {p['weight_g']:.2f} g.")
    lines += [f"Total: {report['total_seconds']/60:.1f} min, {report['total_weight_g']:.2f} g.",'',
              'Verified: manifold connected meshes; exact source outlines; preserved flat orientation;',
              'full bed contact; native A1 slice; 10 printed layers; open holes and rim/rib coverage',
              'on every layer; printer bounds; no printability warnings; G-code checksums;',
              'mesh round-trip and all locked settings in editable/sliced/G-code configuration.',
              'Production root/named/editable and all A1 companion files retain their original hashes.',
              'No physical print, stiffness, flatness, trace accuracy or optical clarity test has been performed.',
              'No printer job has been sent.','',
              'Source: '+str(SOURCE),'Source SHA-256: '+evidence['source_sha256'],
              'Current sliced project SHA-256: '+report['project_sha256']]
    (OUT/'README.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    shutil.copyfile(Path(__file__),OUT/'build_photo_tracing_backers_r1.py')
    d.save_json(OUT/'SHA256SUMS.json',{p.name:d.sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256SUMS.json'})
    print(json.dumps({k:report[k] for k in ['project','project_sha256','total_seconds','total_weight_g']},indent=2),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','slice','validate','all']);args=ap.parse_args()
    if args.action in ['build','all']:build()
    if args.action in ['slice','all']:native()
    if args.action in ['validate','all']:validate()
