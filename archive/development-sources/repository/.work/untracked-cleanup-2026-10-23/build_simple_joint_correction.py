"""Separate, unqualified correction to the physically failed J4 coupon.

One broad tongue, an open-bottom mortise, and continuous outer side walls.
Both original backs locate against a shared flat assembly surface. No pads,
keys, feet, rear offsets, or changes to production/M/A1 files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import shapely
from shapely.geometry import box, Polygon, MultiPoint, LineString
from development_3mf import solid, mesh, centered, write_project, sha, save_json, props
from develop_cosmetic_joints import cross_section
from build_a2l_project import prism
from build_a2l_flush_joint_test import protected
from validate_production_split import Project, distance
from validate_ribbon_bed_datum import segments
from validate_print_project import scan_gcode
from check_a2l_towers import check_tower, check_startup_tower

OLD = ROOT / 'working/bambu/Dara-A2L-Flush-Joint-Test'
OUT = ROOT / 'working/bambu/Dara-A2L-Simple-Joint-Draft'
WORK = ROOT / '.work/a2l-simple-joint-correction'
EDIT = OUT / 'Dara-A2L-Simple-Joint-Draft-Editable.3mf'
FINAL = OUT / 'Dara-A2L-Simple-Joint-Draft.3mf'
HEIGHT = 4.8
XY_GAP = .3
ROOF = 5.2
LENGTH = 18.


def draw(parts, before):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch
    fig = plt.figure(figsize=(13, 8))
    for i, (body, title) in enumerate(zip(parts, ['One flat tongue', 'Plain mortise; solid side walls'])):
        ax = fig.add_subplot(2, 2, i + 1)
        for z,col in [(6.0,'#ddd8cd'),(.1,'#438fa3' if i==0 else '#d6ac65')]:
            section=cross_section(body,z)
            polygons=[section] if section.geom_type=='Polygon' else section.geoms
            for p in polygons:
                ax.add_patch(Patch(np.array(p.exterior.coords),facecolor=col,edgecolor='#333333',lw=.7))
                for ring in p.interiors:
                    ax.add_patch(Patch(np.array(ring.coords),facecolor='white',edgecolor='#333333',lw=.7))
        ax.set(xlim=(-25,43),ylim=(-35,35),xlabel='Along joint (mm)',ylabel='Across ribbon (mm)',title=title+' (rear view)')
        ax.set_aspect('equal');ax.grid(alpha=.15)
        ax.text(9,0,'Flat tongue\n4.8 mm thick' if i==0 else 'Open mortise\nroof at 5.2 mm',ha='center',va='center')
    for i, (pair,title) in enumerate([(before,'Failed test: side openings and small keys'),
                                      (parts,'Draft: 0.3 mm sides/end; 0.4 mm roof clearance')]):
        ax=fig.add_subplot(2,2,i+3)
        for body,col in zip(pair,['#438fa3','#d6ac65']):
            # Rotate so the mid-width XZ section is a horizontal slice.
            section=cross_section(body.rotate([90,0,0]),0)
            polygons=[section] if section.geom_type=='Polygon' else section.geoms
            for p in polygons:
                ax.add_patch(Patch(np.array(p.exterior.coords)*[1,-1],facecolor=col,edgecolor='#333333',lw=.5))
                for ring in p.interiors:
                    ax.add_patch(Patch(np.array(ring.coords)*[1,-1],facecolor='white',edgecolor='#333333',lw=.5))
        ax.set(xlim=(-8,25),ylim=(-.5,14),xlabel='Along joint (mm)',ylabel='Height (mm)',title=title)
        ax.set_aspect('equal');ax.grid(alpha=.15)
    fig.suptitle('J4 correction — CAD review only; physical fit and reported color defect unresolved')
    fig.tight_layout();fig.savefig(OUT/'joint-design.png',dpi=160);plt.close(fig)


def build():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    fingerprints=protected()
    source=Project(OLD/'Dara-A2L-Flush-Joint-Test-Editable.3mf')
    rows=list(source.rows.values())
    # The old coupon included a 1 mm flare at its cut ends. Crop to the
    # actual straight ribbon span so the test has no scalloped side steps.
    half_span=67.3035/2
    edge_crop=prism(box(-100,-half_span,100,half_span),-.1,20)
    for row in rows:
        for part in row['parts']:
            part['mesh']=mesh(solid(part['mesh']) ^ edge_crop)
    a,b=[solid(r['parts'][0]['mesh']) for r in rows]
    before=[a,b]
    footprint=cross_section(a+b,8.1)
    # This crop's narrowest outside width is the original 67.3035 mm ribbon.
    # Retain 3 mm nominal edge allowance before enlarging the mortise .3 mm.
    half_width=67.3035/2-3
    tongue=box(-1+1,-half_width+1,LENGTH-1,half_width-1).buffer(1,quad_segs=16)
    tongue=tongue.intersection(box(-.5,-50,LENGTH+.1,50))
    # Open the mortise beyond the cosmetic seam; its entry cannot pinch there.
    mortise=tongue.buffer(XY_GAP,quad_segs=16).union(box(-1,-half_width-XY_GAP,1,half_width+XY_GAP))
    left=prism(box(-100,-100,0,100),-.1,20)
    root=prism(footprint.intersection(box(-.6,-100,0,100)),0,8)
    a=(a ^ left)+root+prism(tongue,0,HEIGHT)
    rebuild=prism(box(0,-100,18.6,100),-.1,8)
    b=(b-rebuild)+prism(footprint.intersection(box(0,-100,18.6,100)),0,8)
    b-=prism(mortise,-.01,ROOF)
    bodies=[a,b]
    upper=prism(box(-100,-100,100,100),8.001,20)
    for old,new in zip(before,bodies):
        assert ((old ^ upper)-new).volume()<1e-5 and ((new ^ upper)-old).volume()<1e-5
        assert len([q for q in new.decompose() if q.volume()>1e-7])==1
        assert abs(new.bounding_box()[2])<1e-7
    assert (a^b).volume()<1e-6
    assert abs((a ^ prism(box(.1,-50,18.1,50),HEIGHT+.001,7.999)).volume())<1e-6
    # The outside edge remains solid through the formerly open clearance band.
    sides=footprint.difference(footprint.buffer(-1)).intersection(box(.05,-100,17.9,100))
    missing=(prism(sides,0,8)-(a+b)).volume()
    assert missing<1e-6,missing
    layer_checks=[]
    for name,body in zip(['Tongue','Mortise'],bodies):
        previous=cross_section(body,.1)
        for z in np.arange(.3,13.51,.2):
            current=cross_section(body,float(z))
            polygons=[current] if current.geom_type=='Polygon' else list(current.geoms)
            for p in polygons:
                if p.is_empty or p.area<1e-10:continue
                assert p.intersection(previous).area>1e-7,(name,z,'new detached layer island')
            previous=current
        layer_checks.append(dict(part=name,new_disconnected_layer_islands=0,section_step_mm=.2,
                                 limitation='Checks component starts, not support coverage or physical overhang quality.'))
    lap=cross_section(a,4.7).intersection(box(.5,-50,18.1,50))
    socket=cross_section(b,4.7)
    gap=lap.distance(socket)
    assert abs(gap-XY_GAP)<.002,gap
    # A tolerance budget, not a claim about measured printed dimensions.
    tolerance_overlap=lap.buffer(.1).intersection(socket.buffer(.1)).area
    assert tolerance_overlap<1e-7
    entries=[];hulls=[]
    for i,(body,row) in enumerate(zip(bodies,rows)):
        m=mesh(body)
        T=centered(m,xy=[100+110*i,100])
        parts=[dict(mesh=m)]+[dict(mesh=p['mesh'].copy(),subtype=p['subtype'],settings=p['settings']) for p in row['parts'][1:]]
        settings={k:v for k,v in row['settings'].items() if k and k!='name'}
        entries.append(dict(name=['Simple tongue - flat back','Plain mortise - flat back'][i],parts=parts,transform=T,settings=settings))
        hulls.append(MultiPoint((m.vertices@T[:3,:3].T+T[:3,3])[:,:2]).convex_hull)
    title='A2L simple J4 joint - unqualified draft'
    settings=dict(source.settings,print_settings_id=title)
    records=write_project(EDIT,[entries],title,settings_update=settings)
    startup=check_startup_tower(settings,hulls,3,13.6,1)
    draw(bodies,before)
    assert protected()==fingerprints
    save_json(OUT/'geometry-validation.json',dict(status='CAD_DRAFT_PHYSICAL_FIT_UNVERIFIED',
        source_sha256=sha(OLD/'Dara-A2L-Flush-Joint-Test-Editable.3mf'),editable_sha256=sha(EDIT),
        tongue_length_mm=LENGTH,tongue_width_mm=2*half_width,tongue_height_mm=HEIGHT,
        mortise_width_mm=2*(half_width+XY_GAP),mortise_end_mm=LENGTH+XY_GAP,mortise_roof_mm=ROOF,
        measured_minimum_lateral_gap_mm=gap,nominal_roof_gap_mm=ROOF-HEIGHT,
        minimum_outer_wall_width_mm=2.7,missing_outer_wall_volume_mm3=missing,
        keys=0,pads=0,feet=0,extra_spacers=0,nominal_interference_mm3=(a^b).volume(),
        overlap_after_point_one_mm_expansion_of_each_mating_boundary_mm2=tolerance_overlap,
        assembly_reference='Both bed-printed backs held against the same flat surface during fit and adhesive cure.',
        self_registering_vertical_stop=False,layer_component_checks=layer_checks,
        cropped_show_geometry_above_z8_preserved=True,color_modifiers_preserved_inside_crop=True,
        coupon_side_crop_y_mm=[-half_span,half_span],removed_old_coupon_end_flare_mm=1,
        physical_white_in_brown_cause='Unresolved; first scan found no white toolpath centers inside intended fabric.',
        protected_project_sha256=fingerprints,records=records,startup_tower=startup))
    print('Built separate plain-joint draft; no production changes.',flush=True)


def slice_plate():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (WORK/'cli.log').open('w') as log:
        r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(WORK),str(EDIT)],
                         cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    r.check_returncode();print('Draft sliced locally.',flush=True)


def validate():
    import xml.etree.ElementTree as ET
    src=Project(EDIT);p=Project(WORK/'sliced.3mf')
    record=json.loads((OUT/'geometry-validation.json').read_text())
    assert src.settings==p.settings
    errors=[];hulls=[]
    for name,row in p.rows.items():
        old=src.rows[name]
        assert {k for k in row['settings'] if k}=={k for k in old['settings'] if k}
        for key,value in old['settings'].items():
            if key=='infill_direction':assert float(row['settings'][key])==float(value)
            else:assert row['settings'][key]==value,(name,key)
        assert len(row['parts'])==len(old['parts'])
        for a,b in zip(row['parts'],old['parts']):
            assert a['subtype']==b['subtype']
            assert a['settings'].get('extruder')==b['settings'].get('extruder')
            va=a['mesh'].vertices@row['T'][:3,:3].T+row['T'][:3,3]
            vb=b['mesh'].vertices@old['T'][:3,:3].T+old['T'][:3,3]
            errors.append(distance(va,vb));assert errors[-1]<.001
            if a['subtype']=='normal_part':hulls.append(MultiPoint(va[:,:2]).convex_hull)
    raw=p.z.read('Metadata/plate_1.gcode');text=raw.decode()
    assert hashlib.md5(raw).hexdigest()==p.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    scan=scan_gcode(text);lo,hi=np.array(scan['bead_xy_bounds_mm'])
    margin=float(min(*lo,*(np.array([330,320])-hi)));assert margin>.5
    scan['conservative_bed_edge_clearance_mm']=margin
    assert set(scan['model_extrusion_z_by_filament_mm'])=={'1','2','4'}
    tower=check_tower(text.replace('; LINE_WIDTH: ','; WIDTH: '),hulls,[282,157,318,197])
    ids={int(props(i)['identify_id']):props(p.configs[props(i)['object_id']])['name'] for pl in p.cfg.findall('plate') for i in pl.findall('model_instance')}
    paths=segments(text,ids);color_checks=[];roof_checks=[]
    for name,rows in paths.items():
        a=np.array([r[2] for r in rows]);a-=src.rows[name]['T'][:3,3]
        slots=np.array([r[0] for r in rows]);features=np.array([r[1] for r in rows]);mid=a.mean(axis=1)
        m=src.rows[name]['parts'][0]['mesh']
        fabric=shapely.union_all([Polygon(t[:,:2]) for t,n in zip(m.triangles,m.face_normals) if n[2]>.999 and 8.9<t[:,2].mean()<10])
        # Test complete path interiors, densely enough to catch color crossings.
        fabric=fabric.buffer(-.05)
        bad=0;sampled=0
        for line,slot in zip(a,slots):
            if slot!=1 or line[1,2]<8.6:continue
            count=max(2,int(np.ceil(np.linalg.norm(line[1]-line[0])/.1))+1)
            q=np.linspace(line[0],line[1],count)
            sampled+=len(q);bad+=int(shapely.contains_xy(fabric,q[:,0],q[:,1]).sum())
        assert bad==0,(name,bad)
        heights={str(slot):float(a[slots==slot,:,2].max()) for slot in [1,2,4]}
        assert heights=={'1':13.6,'2':10.0,'4':13.6}
        color_checks.append(dict(part=name,white_path_samples_checked=sampled,white_path_samples_inside_fabric=bad,
                                 maximum_z_by_filament_mm=heights,physical_color_cause_resolved=False))
        region=(mid[:,0]>2)&(mid[:,0]<16)&(abs(mid[:,1])<25)
        z=float(a[region,:,2].max() if name.startswith('Simple') else a[region,:,2].min())
        assert abs(z-(4.8 if name.startswith('Simple') else 5.4))<.001,(name,z)
        roof_checks.append(dict(part=name,actual_model_z_mm=z,role='tongue top' if name.startswith('Simple') else 'first roof extrusion'))
    info=ET.fromstring(p.z.read('Metadata/slice_info.config'))
    warnings=[w.attrib for pl in info.findall('plate') for w in pl.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    assert scan['features'].get('Support interface',0)>0
    # Compare actual nominal bead envelopes after reassembling the toolpaths.
    # This includes slicer perimeter offsets; it cannot measure plastic shrink,
    # flow error, support residue or the user's physical mortise.
    from check_veneer_layer_overlap import parse
    model,_=parse(text)
    offsets=[row['T'][:2,3] for row in src.rows.values()]
    bead_checks=[]
    for z,rows in sorted(model.items()):
        if z>HEIGHT+.001:continue
        beads=[[],[]]
        for x,y,X,Y,width,feature in rows:
            index=0 if (x+X)/2<160 else 1
            line=LineString(np.array([[x,y],[X,Y]])-offsets[index])
            if line.intersects(box(.5,-32,19,32)):
                beads[index].append(line.buffer(width/2,cap_style='round'))
        aa,bb=[shapely.union_all(items) for items in beads]
        aa=aa.intersection(box(.5,-32,18.5,32))
        clearance=float(aa.distance(bb));overlap=float(aa.intersection(bb).area)
        assert clearance>.28 and overlap<1e-8,(z,clearance,overlap)
        bead_checks.append(dict(layer_z_mm=z,minimum_xy_clearance_mm=clearance,overlap_mm2=overlap))
    assert protected()==record['protected_project_sha256']
    FINAL.write_bytes((WORK/'sliced.3mf').read_bytes())
    save_json(OUT/'native-validation.json',dict(status='SLICED_DRAFT_NOT_PHYSICALLY_QUALIFIED',
        project_sha256=sha(FINAL),editable_sha256=sha(EDIT),builder_sha256=sha(Path(__file__)),
        geometry_validation_sha256=sha(OUT/'geometry-validation.json'),maximum_pose_error_mm=max(errors),
        scan=scan,tower=tower,color_checks=color_checks,lap_roof_checks=roof_checks,slicer_metadata_warnings=warnings,
        assembled_nominal_bead_clearance_checks=bead_checks,
        GUI_warning_check_performed=False,physical_fit_flushness_color_and_strength_unverified=True,
        production_and_A1_preserved=True,printer_commands_sent=False))
    side=json.loads(EDIT.with_suffix('.json').read_text());side.update(status='SLICED_DRAFT_NOT_PHYSICALLY_QUALIFIED',
        native_slice_validated=True,native_project=FINAL.name,native_sha256=sha(FINAL));save_json(EDIT.with_suffix('.json'),side)
    result=json.loads((WORK/'result.json').read_text());print(json.dumps(result.get('sliced_plates',[]),indent=2),flush=True)
    print('Saved separate draft; physical outcome and reported color defect remain unresolved.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','slice','validate'])
    {'build':build,'slice':slice_plate,'validate':validate}[parser.parse_args().action]()
