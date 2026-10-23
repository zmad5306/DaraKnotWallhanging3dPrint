# Historical design source retained for provenance, not a current rebuild command.
# Uses retired project paths/settings; do not regenerate current releases with it.
"""r2: full production photo-opening curve, cropped to 4 mm height."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import numpy as np
import manifold3d as mf
import shapely
from shapely.geometry import Polygon, Point, MultiPoint, box, mapping, shape
import development_3mf as dev
from development_3mf import solid, mesh, sha, save_json, props
from extract_production_joint_sample import source_rows, protected
from develop_cosmetic_joints import cross_section
from build_a2l_project import prism
from validate_production_split import Project, distance
from validate_print_project import scan_gcode
from check_a2l_towers import check_startup_tower
from build_photo_support_test import LOCKS, effective, paths

SOURCE=ROOT/'Dara.3mf'
NAME='Dara-A2L-Photo-Curve-Support-Test-r2'
OUT=ROOT/'output'/NAME
WORK=ROOT/'.work/photo-curve-support-test-r2'
EDIT=OUT/(NAME+'-Editable.3mf')
FINAL=OUT/(NAME+'.3mf')
TITLE='A2L full photo curve - 8% gyroid - support comparison r2'
NAMES=['LEFT A - full curve - 0.5 mm interface','RIGHT B - full curve - 0.2 mm interface']
HEIGHT=4.0
STRIP_WIDTH=14.0
END_ALLOWANCE=8.0
CENTERS=[[85.,155.],[245.,155.]]


def crop_region(body):
    # Native volume boundaries differ by micrometres. Close those gaps only in
    # this 2D crop-boundary construction; all model meshes remain exact crops.
    section=cross_section(body,2.5).buffer(.0001).buffer(-.0001)
    holes=[Polygon(h) for p in getattr(section,'geoms',[section]) for h in p.interiors]
    opening=max(holes,key=lambda p:p.area)
    assert opening.area>10000
    # End points read from the production mesh at the two tangent transitions.
    a=np.array([117.8022158369422,204.46009707450867])
    b=np.array([238.17955696582794,94.4320599809289])
    tangent=(b-a)/np.linalg.norm(b-a)
    normal=np.array([-tangent[1],tangent[0]])
    center=(a+b)/2+normal*END_ALLOWANCE
    halfplane=Polygon([center-tangent*1000,center+tangent*1000,
        center+tangent*1000-normal*1000,center-tangent*1000-normal*1000])
    region=opening.buffer(STRIP_WIDTH,quad_segs=16).intersection(halfplane)
    full_curve=opening.boundary.intersection(halfplane)
    assert full_curve.length>200 and region.buffer(1e-6).covers(full_curve)
    return region,opening,dict(crop_top_z_mm=HEIGHT,outer_cut_offset_from_photo_opening_mm=STRIP_WIDTH,
        end_transition_points_source_xy_mm=[a.tolist(),b.tolist()],
        end_cut_line_normal_xy=normal.tolist(),end_cut_line_dot_limit_mm=float(center@normal),
        straight_end_allowance_normal_to_chord_mm=END_ALLOWANCE,
        retained_photo_edge_length_mm=full_curve.length,outline_gap_closing_tolerance_mm=.0001)


def build():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    before=protected();row,settings=source_rows(['F2 A2L knot']);row=row[0]
    source_parts=[]
    for p in row['parts']:
        m=p['mesh'].copy();m.apply_transform(row['T'])
        source_parts.append((p,solid(m)))
    original=mf.Manifold.batch_boolean([m for p,m in source_parts if p['subtype']=='normal_part'],mf.OpType.Add)
    region,opening,crop_details=crop_region(original)
    save_json(OUT/'crop-boundary.geojson',mapping(region))
    crop=prism(region,0,HEIGHT)
    parts=[];records=[];bodies=[];inverse=np.linalg.inv(row['T'])
    for i,(p,s) in enumerate(source_parts):
        clipped=s^crop
        if clipped.volume()<1e-7:continue
        m=mesh(clipped);error=abs((solid(m)-clipped).volume())+abs((clipped-solid(m)).volume())
        assert error<1e-5
        if p['subtype']=='normal_part':bodies.append(clipped)
        m.apply_transform(inverse)
        parts.append(dict(mesh=m,subtype=p['subtype'],settings=p['settings']))
        records.append(dict(source_volume_index=i,subtype=p['subtype'],source_metadata=p['settings'],
            volume_mm3=clipped.volume(),boolean_roundtrip_difference_mm3=error))
    body=mf.Manifold.batch_boolean(bodies,mf.OpType.Add)
    assert abs((body-original).volume())<1e-5
    footprint=cross_section(body,.1)
    # Treat existing micrometre separations between source volumes as touching.
    assert footprint.buffer(.001).geom_type=='Polygon'
    checks=[]
    for z in [.1,2.3,2.5,3.9]:
        actual=cross_section(body,z);expected=cross_section(original,z).intersection(region)
        error=actual.symmetric_difference(expected).area
        assert error<1e-4,(z,error)
        checks.append(dict(z_mm=z,section_difference_mm2=error))
    verts=mesh(body).vertices;bounds=np.array([verts.min(axis=0),verts.max(axis=0)])
    center=bounds[:,:2].mean(axis=0);entries=[];shifts=[];hulls=[]
    for i,xy in enumerate(CENTERS):
        shift=np.r_[np.asarray(xy)-center,0.];T=row['T'].copy();T[:3,3]+=shift
        st={k:v for k,v in row['settings'].items() if k not in (None,'name')}
        if i:st['support_interface_spacing']='0.2'
        entries.append(dict(name=NAMES[i],parts=copy.deepcopy(parts),settings=st,transform=T))
        shifts.append(shift.tolist());hulls.append(MultiPoint(verts[:,:2]+shift[:2]).convex_hull)
    updates=copy.deepcopy(settings);updates.update(print_settings_id=TITLE,wipe_tower_x=['285'],wipe_tower_y=['160'])
    with zipfile.ZipFile(SOURCE) as z:files={n:z.read(n) for n in ['Metadata/project_settings.config','[Content_Types].xml']}
    dev.source=lambda:files;dev.source_path=lambda:SOURCE
    output_records=dev.write_project(EDIT,[entries],TITLE,settings_update=updates)
    with zipfile.ZipFile(EDIT) as z:assert json.loads(z.read('Metadata/project_settings.config'))==updates
    startup=check_startup_tower(updates,hulls,1,HEIGHT,1)
    differences={k:dict(before=settings.get(k),after=updates.get(k)) for k in set(settings)|set(updates) if settings.get(k)!=updates.get(k)}
    assert set(differences)=={'print_settings_id','wipe_tower_x','wipe_tower_y'}
    assert protected()==before
    report=dict(status='BUILT_AWAITING_NATIVE_SLICE',revision='r2',source_project=str(SOURCE),source_sha256=sha(SOURCE),
        source_plate=2,source_object='F2 A2L knot',source_object_id=22,source_object_settings=row['settings'],
        source_rotation=row['T'][:3,:3].tolist(),source_volume_crops=records,source_crop_definition=crop_details,
        exact_xy_crop_boundary_file='crop-boundary.geojson',crop_boundary_sha256=sha(OUT/'crop-boundary.geojson'),
        retained_source_bounds_mm=bounds.tolist(),coupon_size_mm=(bounds[1]-bounds[0]).tolist(),
        identical_geometry_both_objects=True,entire_curved_photo_edge_retained=True,
        authorized_height_crop_mm=dict(old=13.5,new=HEIGHT),model_layers_above_support=8,
        no_added_geometry=True,connected_at_source_volume_tolerance_mm=.001,
        geometry_section_checks=checks,first_layer_model_footprint_mm2=footprint.area,
        translation_only_mm=shifts,records=output_records,global_settings_differences=differences,
        changed_variable='RIGHT B support_interface_spacing 0.5 -> 0.2 mm; LEFT A remains 0.5 mm.',
        preserved_support_z_gap_mm=.2,preserved_top_interface_layers=2,
        white_only_because_crop_ends_below_color_modifiers=True,source_colors_reassigned=False,
        startup_tower_check=startup,editable_sha256=sha(EDIT),protected_before=before,
        physical_adhesion_and_removal_untested=True,printer_commands_sent=False)
    save_json(OUT/'validation.json',report)
    mesh_preview(original,body,region,report)
    print(json.dumps(dict(size=report['coupon_size_mm'],curve_mm=crop_details['retained_photo_edge_length_mm'],volumes=len(parts)),indent=2),flush=True)


def mesh_preview(original,body,region,r):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(12,6))
    for poly in getattr(cross_section(original,2.5),'geoms',[cross_section(original,2.5)]):
        ax[0].plot(*poly.exterior.xy,color='#b8c1c8',lw=1)
        for hole in poly.interiors:ax[0].plot(*hole.xy,color='#b8c1c8',lw=1)
    for poly in getattr(cross_section(body,2.5),'geoms',[cross_section(body,2.5)]):
        ax[0].fill(*poly.exterior.xy,color='#138a9e',alpha=.8)
    ax[0].set_title('Entire production curve retained (teal)')
    sec=cross_section(body,2.5)
    for i,shift in enumerate(r['translation_only_mm']):
        for poly in getattr(sec,'geoms',[sec]):
            xy=np.array(poly.exterior.coords)+np.array(shift[:2]);ax[1].fill(xy[:,0],xy[:,1],color=['#e9a640','#138a9e'][i])
        ax[1].text(CENTERS[i][0],265,['LEFT A / 0.5 mm','RIGHT B / 0.2 mm'][i],ha='center',weight='bold')
    ax[1].set_xlim(0,330);ax[1].set_ylim(0,320);ax[1].set_title('One A2L plate / both pieces 4.0 mm high')
    for a in ax:a.set_aspect('equal');a.grid(alpha=.2);a.set_xlabel('X (mm)');a.set_ylabel('Y (mm)')
    fig.tight_layout();fig.savefig(OUT/'full-curve-preview.png',dpi=150);plt.close(fig)


def slice_project():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe');native=WORK/'native';native.mkdir(parents=True,exist_ok=True)
    with (WORK/'slice.log').open('w',encoding='utf-8') as log:
        r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(native),str(EDIT)],
            cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    r.check_returncode();print((native/'result.json').read_text(),flush=True)


def contact_check(all_paths,i,r):
    shift=np.array(r['translation_only_mm'][i]);bounds=np.array(r['retained_source_bounds_mm'])+shift
    mask=box(*bounds[0,:2],*bounds[1,:2]).buffer(4)
    ps=[p for p in all_paths if mask.covers(Point(np.mean(p['segment'],axis=0)))]
    roof=[p for p in ps if p['feature']=='Support interface' and p['z']==2.2]
    walls=[p for p in ps if p['feature']=='Overhang wall' and p['z']==2.6]
    bridge=[p for p in ps if p['feature']=='Bridge' and p['z']==2.6]
    assert roof and walls and bridge
    rg=shapely.union_all([shapely.LineString(p['segment']).buffer(p['width']/2) for p in roof])
    line=shapely.union_all([shapely.LineString(p['segment']) for p in walls])
    samples=[]
    for q in getattr(line,'geoms',[line]):
        samples.extend(q.interpolate(d) for d in np.linspace(0,q.length,max(2,math.ceil(q.length/.1))))
    gaps=np.array([p.distance(rg) for p in samples])
    assert len(gaps)>1000
    bed=[p for p in ps if p['z']==.2 and p['feature'] not in ('Support','Support interface','Brim','Skirt','Prime tower')]
    assert bed
    envelope=shapely.union_all([shapely.LineString(p['segment']).buffer(p['width']/2) for p in ps])
    data=dict(name=NAMES[i],interface_spacing_mm=.5 if i==0 else .2,
        roof_extrusion_length_mm=sum(shapely.LineString(p['segment']).length for p in roof),
        roof_printed_area_mm2=rg.area,roof_top_z_mm=2.2,first_supported_model_top_z_mm=2.6,
        actual_vertical_air_gap_mm=.2,wall_length_checked_mm=line.length,wall_probe_count=len(gaps),
        max_wall_centerline_distance_to_roof_beads_mm=float(gaps.max()),
        wall_probes_within_0_5mm_percent=float(np.mean(gaps<=.5)*100),
        overhang_wall_speeds_mm_s=sorted({p['speed'] for p in walls}),bridge_speeds_mm_s=sorted({p['speed'] for p in bridge}),
        model_first_layer_extrusions=len(bed),maximum_extrusion_z_mm=max(p['z'] for p in ps))
    return data,ps,envelope


def validate():
    r=json.loads((OUT/'validation.json').read_text());assert sha(SOURCE)==r['source_sha256'] and sha(EDIT)==r['editable_sha256']
    edited=Project(EDIT);native=Project(WORK/'native/sliced.3mf');s=native.settings
    assert edited.settings==s and len(native.rows)==2 and len(native.cfg.findall('plate'))==1
    for k,v in LOCKS.items():assert s[k]==v,(k,s[k],v)
    assert s['printer_model']=='Bambu Lab A2L' and s['nozzle_diameter']==['0.4']
    errors=[]
    for i,name in enumerate(NAMES):
        a,b=edited.rows[name],native.rows[name];expected=effective(r['source_object_settings'])
        if i:expected['support_interface_spacing']='0.2'
        assert effective(a['settings'])==effective(b['settings'])==expected
        assert len(a['parts'])==len(b['parts'])==len(r['source_volume_crops'])
        for p,q,rec in zip(a['parts'],b['parts'],r['source_volume_crops']):
            assert p['subtype']==q['subtype'] and q['mesh'].is_volume
            assert effective(p['settings'])==effective(q['settings'])==effective(rec['source_metadata'])
            e={**s,**effective(b['settings']),**effective(q['settings'])}
            for k,v in LOCKS.items():
                if k=='sparse_infill_density' and rec['source_metadata'].get(k)=='100%':v='100%'
                assert e[k]==v
            assert float(e['support_interface_spacing'])==(.5 if i==0 else .2)
            av=p['mesh'].vertices@a['T'][:3,:3].T+a['T'][:3,3];bv=q['mesh'].vertices@b['T'][:3,:3].T+b['T'][:3,3]
            errors.append(distance(av,bv));assert errors[-1]<.001
    raw=native.z.read('Metadata/plate_1.gcode');g=raw.decode()
    assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    gc={line[2:].split(' = ',1)[0]:line[2:].split(' = ',1)[1] for line in g.splitlines() if line.startswith('; ') and ' = ' in line}
    for k,v in LOCKS.items():assert gc[k]==v,(k,gc.get(k),v)
    assert gc['printer_model']=='Bambu Lab A2L' and gc['nozzle_diameter']=='0.4'
    scan=scan_gcode(g);lo,hi=np.array(scan['bead_xy_bounds_mm'])
    scan['conservative_bed_edge_clearance_mm']=float(min(*lo,*(np.array([330,320])-hi)))
    assert scan['conservative_bed_edge_clearance_mm']>.5
    assert set(scan['model_extrusion_z_by_filament_mm'])=={'1'} and max(scan['model_extrusion_z_by_filament_mm']['1'])==HEIGHT
    assert not scan['features'].get('Prime tower',0)
    info=ET.fromstring(native.z.read('Metadata/slice_info.config'))
    warnings=[w.attrib for pl in info.findall('plate') for w in pl.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    all_paths=paths(g);groups=[contact_check(all_paths,i,r) for i in range(2)]
    gap=groups[0][2].distance(groups[1][2]);assert gap>3,gap
    assert groups[1][0]['roof_extrusion_length_mm']>groups[0][0]['roof_extrusion_length_mm']*1.1
    toolpath_preview(groups)
    result=json.loads((WORK/'native/result.json').read_text());assert result['return_code']==0
    plate=result['sliced_plates'][0];assert protected()==r['protected_before']
    FINAL.write_bytes((WORK/'native/sliced.3mf').read_bytes())
    for n in ['plate_1.png','top_1.png']:(OUT/('saved-'+n)).write_bytes(native.z.read('Metadata/'+n))
    r.update(status='DIGITAL_CHECKS_PASSED_PHYSICAL_SUPPORT_ADHESION_UNTESTED',current_file=str(FINAL),current_sha256=sha(FINAL),
        gcode_sha256=hashlib.sha256(raw).hexdigest(),gcode_md5_verified=True,locked_settings_gcode_checked=True,
        all_effective_object_volume_settings_checked=True,editable_and_sliced_settings_equal=True,
        maximum_native_mesh_pose_error_mm=max(errors),scan=scan,support_contact_checks=[q[0] for q in groups],
        printed_model_support_brim_separation_mm=gap,slicer_warnings=warnings,estimated_seconds=plate['total_predication'],
        estimated_grams=sum(f['total_used_g'] for f in plate['filaments']),native_result=result,
        protected_after=protected(),production_and_A1_unchanged=True,builder_sha256=sha(Path(__file__)),gui_reopen_performed=False)
    save_json(OUT/'validation.json',r)
    side=json.loads(EDIT.with_suffix('.json').read_text());side.update(native_slice_validated=True,native_project=FINAL.name,native_sha256=sha(FINAL));save_json(EDIT.with_suffix('.json'),side)
    write_readme(r)
    print(json.dumps(dict(file=str(FINAL),sha256=sha(FINAL),seconds=r['estimated_seconds'],grams=r['estimated_grams'],gap_mm=gap,
        contact=r['support_contact_checks'],warnings=warnings),indent=2),flush=True)


def toolpath_preview(groups):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    for i,(data,ps,_) in enumerate(groups):
        for role,z,color,lw in [('Support interface',2.2,'#d38a12',1.2),('Overhang wall',2.6,'#087c9c',1.0),('Bridge',2.6,'#3c95ad',.4)]:
            segs=[p['segment'] for p in ps if p['feature']==role and p['z']==z]
            axes[i].add_collection(LineCollection(segs,colors=color,linewidths=lw,label=f'{role} Z{z}'))
        axes[i].autoscale_view();axes[i].set_aspect('equal');axes[i].grid(alpha=.2)
        axes[i].set_title(NAMES[i]);axes[i].set_xlabel('Bed X (mm)');axes[i].set_ylabel('Bed Y (mm)');axes[i].legend(fontsize=7)
    fig.suptitle('Full production curve: actual support roof and first supported layer')
    fig.tight_layout();fig.savefig(OUT/'support-contact-preview.png',dpi=160);plt.close(fig)


def write_readme(r):
    t=int(r['estimated_seconds']);h,rem=divmod(t,3600);m,s=divmod(rem,60)
    text=f'''DARA A2L FULL PHOTO-CURVE SUPPORT TEST - r2
CURRENT TEST: {FINAL.name}
SHA-256: {r['current_sha256']}
Open AS A PROJECT in Bambu Studio. A2L, 0.4 mm nozzle, Textured PEI Plate.
Prepared 2026-10-22. Replaces the rejected short, full-height r1 test.
Estimate: {h} h {m} min {s} sec; {r['estimated_grams']:.2f} g combined, including supports.
One plate, two identical FULL curved photo-lip cutaways; 4.0 mm high.
LEFT A: original 0.5 mm support interface spacing.
RIGHT B: proposed 0.2 mm support interface spacing.
Only WHITE filament (slot 1) is used. Other saved filament slots/profiles remain.
No prime tower is emitted for this single-color test. No printer job was sent.

GEOMETRY AND PURPOSE
The complete curved edge is retained from one straight-edge transition to the
other, with short adjoining straight ends. Retained photo-edge length including
those ends: {r['source_crop_definition']['retained_photo_edge_length_mm']:.2f} mm.
Each footprint is approximately {r['coupon_size_mm'][0]:.2f} x {r['coupon_size_mm'][1]:.2f} mm.
The narrow cutaway reaches 14 mm outward from the photo opening: original 4 mm
lip plus approximately 10 mm of adjacent bed-contacting frame. It is an exact
intersection with production, not a new curve or scaled approximation.
Requested vertical crop: Z0..4.0 instead of the original 13.5 mm full height.
The original 2.4 mm rear recess remains. Eight model layers cover the support,
starting at Z2.6 mm, layer 13. Color modifiers begin above this crop; no recoloring.
Original pilot holes and local 100% screw reinforcement within the crop remain.

PRINT AND COMPARE
Keep placement and orientation. Watch layer 13 / Z2.6 mm for curved perimeter
lines pulling loose and straightening across the opening. Compare LEFT A and
RIGHT B. After cooling and support removal, inspect the whole curved underside
for loose strands, missing edge sections and removal effort. Keep the pieces
identified by their left/right bed position. Record the exact r2 file and printer.
This is a local support-contact experiment. Reduced height/width changes cooling,
stiffness and layer time. Physical success on the complete frame remains unknown.

SETTINGS
0.20 mm layers and initial layer; 8% gyroid; four wall loops; five top/bottom
layers; existing 100% screw zones. Thin sections may be filled by shell layers.
Two top interface layers; 0.20 mm top Z gap. Existing tree supports, brim,
temperatures, cooling, speeds and purge settings are preserved. Bridge 50 mm/s;
fully unsupported wall 10 mm/s. RIGHT B alone changes support roof spacing.
Global differences: descriptive test process name and single-plate tower arrays.

PROVENANCE AND EXACT CROP
Source: {SOURCE}
Source SHA-256: {r['source_sha256']}
Plate 2 / object 22 / F2 A2L knot.
Exact XY crop polygon: crop-boundary.geojson, SHA-256 {r['crop_boundary_sha256']}.
The polygon is the production opening's 14 mm outward offset, clipped by the
recorded end-cut half-plane. Z0..4.0. The polygon and full construction parameters
are recorded in validation.json; only the crop boundary uses a 0.0001 mm outline
gap-closing tolerance. Source model meshes themselves are not repaired or expanded.
Source-plate retained XYZ bounds: {r['retained_source_bounds_mm']}.
Translation-only placements: {r['translation_only_mm']} mm. Rotation unchanged.

CHECKS
No added model stock; native source volumes/modifiers preserved within crop;
watertight individual volumes and connected frame within 0.001 mm source-boundary
tolerance; exact production sections at four heights. Editable and sliced geometry
match within 0.001 mm. Full global/object/volume settings compared with source;
locked settings also verified in G-code. Actual bed contact, support roof, first
supported perimeter/bridge speeds, single white filament, 4 mm final height,
bed bounds and separation between model/support/brim envelopes checked.
G-code MD5 verified. The right-hand native roof is denser than the left-hand roof.
Slicer warning metadata: {r['slicer_warnings']}.
Production and A1 before/after hashes match. No GUI reopen was performed.
Digital checks do not establish physical adhesion, cleanup or production success.

FILES
{FINAL.name}: current sliced test.
{EDIT.name}: editable source for the SAME r2 test.
full-curve-preview.png: crop on the source frame and two-piece bed layout.
support-contact-preview.png: actual native roof and first-lip-layer toolpaths.
validation.json / crop-boundary.geojson / SHA256SUMS.txt: evidence and checksums.
Builder: scripts/build_photo_support_curve_test.py (build, slice, validate).
'''
    (OUT/'README.txt').write_text(text,encoding='utf-8')
    files=[FINAL,EDIT,OUT/'validation.json',OUT/'README.txt',OUT/'crop-boundary.geojson',OUT/'full-curve-preview.png',OUT/'support-contact-preview.png',OUT/'saved-plate_1.png',OUT/'saved-top_1.png']
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in files),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','slice','validate'])
    {'build':build,'slice':slice_project,'validate':validate}[p.parse_args().action]()
