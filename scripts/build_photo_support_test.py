# Historical design source retained for provenance, not a current rebuild command.
# Uses retired project paths/settings; do not regenerate current releases with it.
"""Production F2 photo-lip support-spacing comparison; no production writes."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import manifold3d as mf
import shapely
from shapely.geometry import box, MultiPoint, Point
import development_3mf as dev
from development_3mf import solid, mesh, sha, save_json, props
from extract_production_joint_sample import source_rows, protected
from develop_cosmetic_joints import cross_section
from validate_production_split import Project, distance
from validate_print_project import scan_gcode
from check_a2l_towers import check_startup_tower, check_tower

SOURCE = ROOT / 'Dara.3mf'
NAME = 'Dara-A2L-Photo-Lip-Support-Test-r1'
OUT = ROOT / 'output' / NAME
WORK = ROOT / '.work/photo-support-test-r1'
EDIT = OUT / (NAME + '-Editable.3mf')
FINAL = OUT / (NAME + '.3mf')
TITLE = 'A2L photo lip support comparison - 8% gyroid - r1'
NAMES = ['LEFT A - production 0.5 mm interface', 'RIGHT B - test 0.2 mm interface']
LO = np.array([95., 130., 0.])
HI = np.array([160., 220., 17.])
CENTERS = [[100., 100.], [205., 100.]]
LOCKS = dict(sparse_infill_density='8%', sparse_infill_pattern='gyroid',
    layer_height='0.2', initial_layer_print_height='0.2', wall_loops='4',
    top_shell_layers='5', bottom_shell_layers='5', curr_bed_type='Textured PEI Plate')
BOOKKEEPING = {'name', 'matrix', 'source_file', 'source_object_id', 'source_volume_id',
    'source_offset_x', 'source_offset_y', 'source_offset_z', None, 'null'}


def effective(st):
    return {k: v for k, v in st.items() if k not in BOOKKEEPING}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    before = protected()
    rows, settings = source_rows(['F2 A2L knot'])
    row = rows[0]
    crop = mf.Manifold.cube(HI-LO).translate(LO)
    inverse = np.linalg.inv(row['T'])
    parts, records, bodies, originals = [], [], [], []
    for i, p in enumerate(row['parts']):
        m = p['mesh'].copy()
        m.apply_transform(row['T'])
        original = solid(m)
        clipped = original ^ crop
        if p['subtype'] == 'normal_part': originals.append(original)
        if clipped.volume() < 1e-7: continue
        m = mesh(clipped)
        delta = abs((solid(m)-clipped).volume()) + abs((clipped-solid(m)).volume())
        assert delta < 1e-6
        if p['subtype'] == 'normal_part': bodies.append(clipped)
        m.apply_transform(inverse)
        parts.append(dict(mesh=m, subtype=p['subtype'], settings=p['settings']))
        records.append(dict(source_volume_index=i, subtype=p['subtype'],
            source_metadata=p['settings'], crop_volume_mm3=clipped.volume(),
            boolean_roundtrip_difference_mm3=delta))
    body = mf.Manifold.batch_boolean(bodies, mf.OpType.Add)
    original = mf.Manifold.batch_boolean(originals, mf.OpType.Add)
    assert len([q for q in body.decompose() if q.volume() > 1e-6]) == 1
    assert abs((body-original).volume()) < 1e-6
    footprint = cross_section(body, .1)
    assert footprint.area > 1000
    # Straight crop planes bound a continuous production rail; no lap joint is included.
    checks = []
    for z in [.1, 2.3, 2.5, 8.3, 9.0, 13.4]:
        section = cross_section(body, z)
        expected = cross_section(original, z).intersection(box(*LO[:2], *HI[:2]))
        error = section.symmetric_difference(expected).area
        assert error < 1e-5
        checks.append(dict(z_mm=z, section_symmetric_difference_mm2=error))
    vertices = mesh(body).vertices
    bounds = np.array([vertices.min(axis=0), vertices.max(axis=0)])
    center = bounds[:, :2].mean(axis=0)
    entries, hulls, shifts = [], [], []
    for k, xy in enumerate(CENTERS):
        shift = np.r_[np.asarray(xy)-center, 0.]
        T = row['T'].copy()
        T[:3, 3] += shift
        st = {a: b for a, b in row['settings'].items() if a not in (None, 'name')}
        if k == 1: st['support_interface_spacing'] = '0.2'
        entries.append(dict(name=NAMES[k], parts=copy.deepcopy(parts), settings=st, transform=T))
        hulls.append(MultiPoint(vertices[:, :2]+shift[:2]).convex_hull)
        shifts.append(shift.tolist())
    updates = copy.deepcopy(settings)
    updates.update(print_settings_id=TITLE, wipe_tower_x=['285'], wipe_tower_y=['160'])
    with zipfile.ZipFile(SOURCE) as z:
        source_files = {n: z.read(n) for n in ['Metadata/project_settings.config', '[Content_Types].xml']}
    dev.source = lambda: source_files
    dev.source_path = lambda: SOURCE
    output_records = dev.write_project(EDIT, [entries], TITLE, settings_update=updates)
    startup = check_startup_tower(updates, hulls, 3, 13.6, 1)
    differences = {k: dict(before=settings.get(k), after=updates.get(k))
        for k in set(settings)|set(updates) if settings.get(k) != updates.get(k)}
    assert set(differences) == {'print_settings_id', 'wipe_tower_x', 'wipe_tower_y'}
    assert protected() == before
    report = dict(status='BUILT_AWAITING_NATIVE_SLICE', revision='r1', source_project=str(SOURCE),
        source_sha256=sha(SOURCE), source_plate=2, source_object='F2 A2L knot', source_object_id=22,
        source_crop_xyz_mm=[LO.tolist(), HI.tolist()], retained_source_bounds_mm=bounds.tolist(),
        coupon_size_mm=(bounds[1]-bounds[0]).tolist(), source_rotation=row['T'][:3, :3].tolist(),
        source_object_settings=row['settings'], source_volume_crops=records,
        identical_cropped_geometry_both_objects=True, original_full_height_preserved=True,
        model_connected=True, crop_only_no_added_stock=True, crop_section_checks=checks,
        first_layer_model_footprint_mm2=footprint.area, translation_only_mm=shifts,
        global_settings_differences=differences, records=output_records,
        changed_variable='RIGHT B support_interface_spacing 0.5 -> 0.2 mm; LEFT A retains 0.5 mm.',
        source_support_top_z_distance_mm=.2, source_support_interface_layers=2,
        startup_tower_check=startup, editable_sha256=sha(EDIT), protected_before=before,
        physical_adhesion_and_removal_untested=True, printer_commands_sent=False)
    save_json(OUT/'validation.json', report)
    print(json.dumps(dict(size_mm=report['coupon_size_mm'], volumes=len(parts),
        source_crop=report['source_crop_xyz_mm'], editable=str(EDIT)), indent=2), flush=True)


def slice_project():
    exe = Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    native = WORK/'native'
    native.mkdir(parents=True, exist_ok=True)
    with (WORK/'slice.log').open('w', encoding='utf-8') as log:
        r = subprocess.run([str(exe), '--slice', '1', '--export-3mf', 'sliced.3mf',
            '--outputdir', str(native), str(EDIT)], cwd=exe.parent, stdout=log,
            stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    r.check_returncode()
    print((native/'result.json').read_text(), flush=True)


def paths(text):
    feature='Custom'; x=y=z=e=feed=0.; width=.5; rel=False; xyz=False; tool=None
    result=[]
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '): feature=raw.split(': ',1)[1]
        if raw.startswith('; LINE_WIDTH: '): width=float(raw.split(': ',1)[1])
        code=raw.split(';',1)[0].strip()
        if not code: continue
        cmd=code.split()[0]
        v={k:float(n) for k,n in re.findall(r'([XYZEF])([+-]?(?:\d+(?:\.\d*)?|\.\d+))',code)}
        if cmd in ['T0','T1','T2','T3']: tool=int(cmd[1:])+1
        elif cmd=='M83': rel=True
        elif cmd=='M82': rel=False
        elif cmd in ('G90','G91'): xyz=cmd=='G91'
        elif cmd=='G92': x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ('G0','G1','G2','G3'):
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if rel else v.get('E',e)-e
            feed=v.get('F',feed)
            if de>0 and math.hypot(nx-x,ny-y)>1e-6 and feature!='Custom':
                assert cmd=='G1', 'Do not approximate arcs as chords'
                result.append(dict(z=round(nz,4), feature=feature, width=width, speed=feed/60,
                    tool=tool, segment=[[x,y],[nx,ny]]))
            x,y,z=nx,ny,nz; e=e+v.get('E',0) if rel else v.get('E',e)
    return result


def support_check(all_paths, index, report):
    shift=np.array(report['translation_only_mm'][index])
    bounds=np.array(report['retained_source_bounds_mm'])+shift
    mask=box(*bounds[0,:2],*bounds[1,:2]).buffer(4)
    ps=[p for p in all_paths if mask.covers(Point(np.mean(p['segment'],axis=0)))]
    roof=[p for p in ps if p['feature']=='Support interface' and abs(p['z']-2.2)<.001]
    walls=[p for p in ps if p['feature']=='Overhang wall' and abs(p['z']-2.6)<.001]
    bridges=[p for p in ps if p['feature']=='Bridge' and abs(p['z']-2.6)<.001]
    assert roof and walls and bridges
    roof_geom=shapely.union_all([shapely.LineString(p['segment']).buffer(p['width']/2) for p in roof])
    lines=shapely.union_all([shapely.LineString(p['segment']) for p in walls])
    # Inspect every supported wall, excluding 3 mm next to artificial crop ends.
    roi=box(*(bounds[0,:2]+3),*(bounds[1,:2]-3))
    line=lines.intersection(roi)
    samples=[]
    for seg in getattr(line,'geoms',[line]):
        if seg.length<1e-7: continue
        samples.extend(seg.interpolate(d) for d in np.linspace(0,seg.length,max(2,math.ceil(seg.length/.1))))
    gaps=np.array([p.distance(roof_geom) for p in samples])
    assert len(gaps)>100
    bed=[p for p in ps if p['z']==.2 and p['feature'] not in ('Support','Support interface','Brim','Prime tower','Skirt')]
    assert bed
    slots={str(t):max(p['z'] for p in ps if p['tool']==t and p['feature'] not in ('Support','Support interface','Brim','Prime tower','Skirt')) for t in (1,2,4)}
    assert slots=={'1':13.6,'2':10.,'4':13.6}, slots
    data=dict(name=NAMES[index], interface_spacing_mm=.5 if index==0 else .2,
        roof_top_z_mm=2.2, first_model_layer_top_z_mm=2.6, model_layer_thickness_mm=.2,
        actual_vertical_air_gap_mm=.2, roof_extrusion_length_mm=sum(shapely.LineString(p['segment']).length for p in roof),
        roof_printed_area_mm2=roof_geom.area, supported_wall_length_checked_mm=line.length,
        wall_probe_count=len(gaps), max_wall_centerline_distance_from_roof_beads_mm=float(gaps.max()),
        median_wall_centerline_distance_from_roof_beads_mm=float(np.median(gaps)),
        percentage_wall_probes_within_0_25mm=float(np.mean(gaps<=.25)*100),
        percentage_wall_probes_within_0_5mm=float(np.mean(gaps<=.5)*100),
        overhang_wall_speeds_mm_s=sorted({p['speed'] for p in walls}),
        bridge_speeds_mm_s=sorted({p['speed'] for p in bridges}),
        model_first_layer_extrusions=len(bed), maximum_model_z_by_filament_mm=slots)
    return data, ps, roof_geom


def preview(groups, report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig,axes=plt.subplots(1,2,figsize=(12,8))
    for i,(data,ps,roof) in enumerate(groups):
        ax=axes[i]
        for role,z,col,lw in [('Support interface',2.2,'#d38a12',1.5),('Overhang wall',2.6,'#087c9c',1.5),('Bridge',2.6,'#3c95ad',.45)]:
            segs=[p['segment'] for p in ps if p['feature']==role and p['z']==z]
            ax.add_collection(LineCollection(segs,colors=col,linewidths=lw,label=f'{role} at Z{z}'))
        ax.autoscale_view();ax.set_aspect('equal');ax.grid(alpha=.2)
        ax.set_title(f'{"LEFT A / control" if i==0 else "RIGHT B / proposed"}\n{data["interface_spacing_mm"]:.1f} mm top interface spacing')
        ax.set_xlabel('Bed X (mm)');ax.set_ylabel('Bed Y (mm)');ax.legend(fontsize=8,loc='upper right')
    fig.suptitle('Actual native toolpaths: support roof beneath first photo-lip layer',fontsize=14)
    fig.tight_layout();fig.savefig(OUT/'support-contact-preview.png',dpi=160);plt.close(fig)


def validate():
    report=json.loads((OUT/'validation.json').read_text())
    assert sha(SOURCE)==report['source_sha256'] and sha(EDIT)==report['editable_sha256']
    edited=Project(EDIT);native=Project(WORK/'native/sliced.3mf')
    assert edited.settings==native.settings
    assert len(native.rows)==2 and len(native.cfg.findall('plate'))==1
    s=native.settings
    for k,v in LOCKS.items(): assert s[k]==v,(k,s[k],v)
    assert s['printer_model']=='Bambu Lab A2L' and s['nozzle_diameter']==['0.4']
    errors=[];hulls=[]
    for i,name in enumerate(NAMES):
        a,b=edited.rows[name],native.rows[name]
        assert effective(a['settings'])==effective(b['settings'])
        expected=effective(report['source_object_settings'])
        if i: expected['support_interface_spacing']='0.2'
        assert effective(b['settings'])==expected
        assert len(a['parts'])==len(b['parts'])==len(report['source_volume_crops'])
        for p,q,rec in zip(a['parts'],b['parts'],report['source_volume_crops']):
            assert p['subtype']==q['subtype'] and q['mesh'].is_volume
            assert effective(p['settings'])==effective(q['settings'])==effective(rec['source_metadata'])
            e={**s,**effective(b['settings']),**effective(q['settings'])}
            for k,v in LOCKS.items():
                if k=='sparse_infill_density' and rec['source_metadata'].get(k)=='100%':v='100%'
                assert e[k]==v,(name,k,e[k],v)
            assert float(e['support_interface_spacing'])==(.5 if i==0 else .2)
            va=p['mesh'].vertices@a['T'][:3,:3].T+a['T'][:3,3]
            vb=q['mesh'].vertices@b['T'][:3,:3].T+b['T'][:3,3]
            errors.append(distance(va,vb));assert errors[-1]<.001
            if q['subtype']=='normal_part': hulls.append(MultiPoint(vb[:,:2]).convex_hull)
    raw=native.z.read('Metadata/plate_1.gcode');g=raw.decode()
    assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    gc={line[2:].split(' = ',1)[0]:line[2:].split(' = ',1)[1] for line in g.splitlines() if line.startswith('; ') and ' = ' in line}
    for k,v in LOCKS.items():assert gc[k]==v,(k,gc.get(k),v)
    assert gc['printer_model']=='Bambu Lab A2L' and gc['nozzle_diameter']=='0.4'
    assert gc['support_interface_spacing']=='0.5' # RIGHT B overrides are validated above and in actual paths.
    scan=scan_gcode(g);lo,hi=np.array(scan['bead_xy_bounds_mm'])
    scan['conservative_bed_edge_clearance_mm']=float(min(*lo,*(np.array([330,320])-hi)))
    assert scan['conservative_bed_edge_clearance_mm']>.5
    assert scan['features'].get('Sparse infill',0)>0
    tower=check_tower(g,hulls,[282,157,318,197])
    info=ET.fromstring(native.z.read('Metadata/slice_info.config'))
    warnings=[w.attrib for pl in info.findall('plate') for w in pl.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    all_paths=paths(g)
    groups=[support_check(all_paths,i,report) for i in range(2)]
    # A denser roof must actually be emitted, not merely written to an override.
    assert groups[1][0]['roof_extrusion_length_mm']>groups[0][0]['roof_extrusion_length_mm']*1.1
    preview(groups,report)
    result=json.loads((WORK/'native/result.json').read_text())
    assert result['return_code']==0
    plate=result['sliced_plates'][0]
    assert protected()==report['protected_before']
    FINAL.write_bytes((WORK/'native/sliced.3mf').read_bytes())
    for n in ('plate_1.png','top_1.png'):
        (OUT/('saved-'+n)).write_bytes(native.z.read('Metadata/'+n))
    report.update(status='DIGITAL_CHECKS_PASSED_PHYSICAL_SUPPORT_ADHESION_UNTESTED',
        current_file=str(FINAL),current_sha256=sha(FINAL),gcode_sha256=hashlib.sha256(raw).hexdigest(),
        gcode_md5_verified=True,global_settings_editable_equals_sliced=True,
        full_effective_object_and_volume_settings_checked=True,locked_settings_in_gcode_checked=True,
        max_native_mesh_pose_error_mm=max(errors),scan=scan,tower=tower,
        support_contact_checks=[q[0] for q in groups],slicer_warnings=warnings,
        estimated_seconds=plate['total_predication'],estimated_grams=sum(f['total_used_g'] for f in plate['filaments']),
        native_result=result,protected_after=protected(),production_and_A1_unchanged=True,
        builder_sha256=sha(Path(__file__)),native_gui_reopen_performed=False)
    save_json(OUT/'validation.json',report)
    side=json.loads(EDIT.with_suffix('.json').read_text())
    side.update(native_slice_validated=True,native_project=FINAL.name,native_sha256=sha(FINAL))
    save_json(EDIT.with_suffix('.json'),side)
    write_readme(report)
    print(json.dumps(dict(file=str(FINAL),sha256=sha(FINAL),seconds=report['estimated_seconds'],
        grams=report['estimated_grams'],support_checks=report['support_contact_checks'],warnings=warnings),indent=2),flush=True)


def write_readme(r):
    seconds=int(r['estimated_seconds']);h,rem=divmod(seconds,3600);m,sec=divmod(rem,60)
    text=f'''DARA A2L PHOTO-LIP SUPPORT COMPARISON - r1
Prepared 2026-10-22. Physical support adhesion and removal remain untested.

CURRENT PRINT PROJECT: {FINAL.name}
SHA-256: {r['current_sha256']}
Open AS A PROJECT in Bambu Studio. Printer: Bambu Lab A2L, 0.4 mm nozzle.
One plate, two identical production crops. Keep the saved orientation/placement.
LEFT A: saved 0.5 mm top interface spacing (control).
RIGHT B: 0.2 mm top interface spacing (the only experimental process change).
The object names and support-contact-preview.png identify them without added labels.
Estimate: {h} h {m} min {sec} sec; {r['estimated_grams']:.2f} g total including supports and purge tower.
Filament slots retained: 1 white, 2 wood tan, 3 copper silk, 4 Azurite blue.
This crop uses white, wood tan and blue; copper is unused. No printer job was sent.

WHAT TO OBSERVE
Watch the first model layer above the photo-lip support at Z2.6 mm (layer 13).
Look for curved perimeter lines staying in place instead of pulling straight
across the opening. Compare LEFT A with RIGHT B at that layer and after completion.
Let the plate cool, remove supports, and compare the supported underside for loose
strands, missing edge sections and support removal effort. Record the exact r1
filename, printer and any locally changed settings with the result.
The control deliberately repeats the saved spacing involved in the reported issue.
Passing a small crop does not qualify the whole frame: crop size changes layer time,
cooling, stiffness and support layout. Both pieces preserve the original full height.

UNCHANGED SETTINGS
0.20 mm layers and first layer; 8% gyroid structural infill; four walls;
five top and bottom layers; Textured PEI Plate; existing local screw zones 100%.
Two top interface layers; 0.20 mm top Z gap; original tree-support type and style.
Bridge speed 50 mm/s, fully unsupported wall speed 10 mm/s; all other speed,
temperature, cooling, material, brim and purge settings remain the source baseline.
Actual emitted roof and first-lip-layer checks are recorded in validation.json.
The right-hand override changes SUPPORT roof spacing, not the model's 8% gyroid.

SOURCE AND CROP
Source: {SOURCE}
Source SHA-256: {r['source_sha256']}
Source plate 2, object 22 (F2 A2L knot).
Exact crop in source plate coordinates: X95..160, Y130..220, Z0..17 mm.
Retained model size: 65 x 90 x 13.5 mm per crop; no vertical shortening.
All intersecting color and screw-reinforcement modifiers are cropped with the body.
The actual production curvature, 4 mm photo lip, 2.4 mm rear recess, pilot hole,
full thickness, colors, material boundaries and print rotation are retained.
Translation-only placements: {r['translation_only_mm']} mm relative to source plate.
Prime tower repositioned to X285, Y160 for clearance; purge settings unchanged.
Global changes are only the test process name and single-plate tower coordinate arrays.
RIGHT B alone overrides support_interface_spacing from 0.5 to 0.2 mm.
No joint design is included or evaluated. Straight cut faces are artificial crop ends.

VALIDATION
Exact Boolean crop with no added geometry; connected watertight body; original
cross-sections checked at six heights; both crops have identical model/modifier meshes.
Full effective settings compared against production at global, object and volume
levels; editable/sliced settings agree; locked settings checked in G-code.
Native round-trip mesh/pose error below 0.001 mm; actual model bed-contact extrusion,
support-roof paths, first supported wall/bridge speeds, show-face colors/heights,
printable bounds, prime-tower clearance and stored G-code MD5 checked.
The actual right-hand roof is denser than the left. Exact contact distances and
coverage percentages are in validation.json; the preview plots actual native paths.
Slicer warning metadata checked: only traditional-timelapse compatibility notices
are allowed. A GUI reopen is not part of this validation. Physical adhesion is unknown.
Protected production and A1 files have matching before/after SHA-256 hashes.

FILES
{FINAL.name}: current sliced comparison plate to open.
{EDIT.name}: matching editable source for the same r1 plate.
validation.json: provenance, differences, hashes and native checks.
support-contact-preview.png: roof and first supported layer toolpaths.
saved-plate_1.png / saved-top_1.png: native slicer previews.
SHA256SUMS.txt: checksums of supplied files.
Builder: scripts/build_photo_support_test.py (build, slice, validate).
'''
    (OUT/'README.txt').write_text(text,encoding='utf-8')
    items=[FINAL,EDIT,OUT/'validation.json',OUT/'README.txt',OUT/'support-contact-preview.png',OUT/'saved-plate_1.png',OUT/'saved-top_1.png']
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in items),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','slice','validate'])
    {'build':build,'slice':slice_project,'validate':validate}[p.parse_args().action]()
