"""One finish coupon cropped directly from the saved A2L production veneer.

Build/slice/validate never write to production or send a printer job.
"""
import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import trimesh
import manifold3d as mf
import development_3mf as dev
from development_3mf import sha, save_json, solid, mesh, tag, props
from promote_veneer_wall_cradle import selected, vertices
from validate_print_project import scan_gcode, TOKEN
from check_fin_toolpaths import check_fin_bonds
from check_a2l_towers import check_startup_tower

SOURCE = ROOT / 'Dara.3mf'
OUT = ROOT / 'output/Dara-A2L-Hammered-Finish-ERYONE-r1'
WORK = ROOT / '.work/a2l-hammered-finish-r1'
NAME = 'Dara-A2L-Hammered-Finish-ERYONE-r1'
EDIT = OUT / (NAME + '-Editable.3mf')
FINAL = OUT / (NAME + '.3mf')
TITLE = 'A2L hammered finish ERYONE copper - 8% gyroid - r1'
OBJECT = 'V1 production hammered finish crop - ERYONE copper - r1'
LO, HI = np.array([0., 67., 0.]), np.array([330., 165., 75.])
LOCKS = dict(sparse_infill_density='8%', sparse_infill_pattern='gyroid',
    layer_height='0.2', initial_layer_print_height='0.2', wall_loops='4',
    top_shell_layers='5', bottom_shell_layers='5', curr_bed_type='Textured PEI Plate')


def protected():
    paths = [SOURCE, * (ROOT/'working/bambu/Dara-Photo-Frame-A2L').glob('*.3mf'),
        * (ROOT/'working/bambu/Dara-A1-Companion').rglob('*'),
        * (ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed').glob('*.3mf')]
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths)) if p.is_file()}


def read_selected(path):
    with zipfile.ZipFile(path) as z:
        data = {n: z.read(n) for n in z.namelist() if n.endswith('.model') or n in (
            'Metadata/model_settings.config', 'Metadata/project_settings.config', '[Content_Types].xml')}
    return data


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    before = protected()
    files = read_selected(SOURCE)
    _, _, obj, asset, _, xml_mesh, transform = selected(files, 15)
    v = vertices(xml_mesh) @ transform[:3, :3].T + transform[:3, 3]
    triangles = list(xml_mesh.find(tag('triangles')))
    f = np.array([[int(q.get(k)) for k in ('v1', 'v2', 'v3')] for q in triangles])
    original = trimesh.Trimesh(v, f, process=False)
    body = solid(original)
    crop = body ^ mf.Manifold.cube(HI-LO).translate(LO)
    components = [q for q in crop.decompose() if q.volume() > 1e-7]
    assert len(components) == 1
    coupon = mesh(crop)
    added = abs((crop-body).volume())
    assert added < 1e-6 and coupon.is_volume and abs(coupon.bounds[0, 2]) < 1e-6
    geometry = json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())
    skin = geometry['skins'][0]
    front = np.asarray(skin['assembly_to_printer'])[:3, 2]
    actual = np.array([t.get('paint_supports') == '8' for t in triangles])
    expected = original.face_normals @ front > .01
    paint_error = float(original.area_faces[actual != expected].sum())
    # Saved float serialization changes normals on a few sub-micron slivers.
    assert paint_error < 1e-5
    settings = json.loads(files['Metadata/project_settings.config'])
    updates = copy.deepcopy(settings)
    updates['print_settings_id'] = TITLE
    updates['wipe_tower_x'] = [settings['wipe_tower_x'][14]]
    updates['wipe_tower_y'] = [settings['wipe_tower_y'][14]]
    # Identify the requested spool without changing any effective material setting.
    updates['filament_settings_id'][2] = 'ERYONE Ultra Silk Copper - production baseline @BBL A2L'
    updates['filament_vendor'][2] = 'ERYONE'
    # The shared writer otherwise falls back to a historical A1 baseline.
    dev.source = lambda: files
    dev.source_path = lambda: SOURCE
    entry = dict(name=OBJECT, parts=[dict(mesh=coupon, settings=props(obj.find('part')))],
        settings=props(obj), transform=np.eye(4), block_front=True, front_normal=front)
    dev.write_project(EDIT, [[entry]], TITLE, settings_update=updates)
    np.savez_compressed(WORK/'coupon.npz', vertices=coupon.vertices, faces=coupon.faces)
    probes = np.asarray(skin['carrier']['bond_probes_print_xyz_mm'])
    probes = probes[np.all((probes > LO+.7) & (probes < HI-.7), axis=1)]
    assert len(probes) > 5
    inverse = np.linalg.inv(np.asarray(skin['assembly_to_printer']))
    local = coupon.triangles_center @ inverse[:3, :3].T + inverse[:3, 3]
    face = (local[:, 2] > 9) & (coupon.face_normals @ front > .1)
    preview(coupon, face, local, inverse)
    diff = {k: dict(before=settings.get(k), after=updates.get(k)) for k in set(settings)|set(updates) if settings.get(k) != updates.get(k)}
    assert set(diff) == {'print_settings_id', 'wipe_tower_x', 'wipe_tower_y', 'filament_settings_id', 'filament_vendor'}
    reasons = dict(print_settings_id='Name this separate finish test and expose the locked global process.',
        wipe_tower_x='Keep source plate 15 tower coordinate as the single test plate entry.',
        wipe_tower_y='Keep source plate 15 tower coordinate as the single test plate entry.',
        filament_settings_id='Label requested ERYONE copper spool in slot 3; numeric material settings unchanged.',
        filament_vendor='Identify requested ERYONE spool in slot 3.')
    for k in diff: diff[k]['purpose'] = reasons[k]
    report = dict(status='GEOMETRY_BUILT_NOT_YET_SLICE_VALIDATED', revision='r1',
        source_project=str(SOURCE), source_sha256=sha(SOURCE), source_plate=15,
        source_object=props(obj)['name'], source_object_id=obj.get('id'),
        source_part_id=obj.find('part').get('id'), source_mesh_asset=asset,
        crop_bounds_source_plate_xyz_mm=[LO.tolist(), HI.tolist()],
        crop_is_exact_intersection=True, added_geometry_mm3=added, bed_repositioning_mm=[0,0,0],
        changed_variable='Physical filament: user-confirmed ERYONE Ultra Silk Copper PLA, Amazon ASIN B089Y6BWN3.',
        geometry_design_changes='None inside crop; planar cut faces are created at crop boundaries.',
        retained_carrier='Original inclined wall, rear wall, one connecting web, minimum-Y end band and fused necks inside crop.',
        original_shared_55_degree_rotation_preserved=True,
        sample_bounds_mm=coupon.bounds.tolist(), model_volume_mm3=crop.volume(),
        modeled_mass_g_at_saved_density=crop.volume()*float(settings['filament_density'][2])/1000,
        watertight=True, connected_components=1, minimum_z_mm=float(coupon.bounds[0,2]),
        front_surface_area_mm2=float(coupon.area_faces[face].sum()),
        support_paint_rule_verified_area_mismatch_mm2=paint_error,
        bond_probes_print_xyz_mm=probes.tolist(), source_object_overrides=props(obj),
        source_part_metadata=props(obj.find('part')), global_setting_differences=diff,
        material_profile_basis='Uncalibrated saved Generic PLA Silk numeric values; only slot-3 name/vendor changed.',
        filament_reference='https://www.amazon.com/gp/product/B089Y6BWN3/',
        manufacturer_reference='https://eryone3d.com/products/advanced-silk-pla',
        manufacturer_ranges=dict(nozzle_celsius=[190,220],bed_celsius=[55,70],print_speed_mm_s=[30,60]),
        protected_before=before, editable_sha256=sha(EDIT),
        limitations=['Finish coupon only; no mating joint is included.',
            'Crop changes height, mass, edge cooling and restraint; does not qualify a full veneer for warping or rigidity.',
            'Physical gloss, layer quality, adhesion and removal remain untested.'])
    save_json(OUT/'validation.json', report)
    assert protected() == before
    print(json.dumps({k:report[k] for k in ['sample_bounds_mm','model_volume_mm3','modeled_mass_g_at_saved_density','front_surface_area_mm2']}),flush=True)


def preview(m, face, local, inverse):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), facecolor='white')
    # Exact mesh triangles, viewed normal to the decorative face.
    local_v = m.vertices @ inverse[:3,:3].T + inverse[:3,3]
    polys = local_v[m.faces[face]][:, :, :2]
    normals = m.face_normals[face] @ inverse[:3,:3].T
    light = np.array([-.5, -.6, 1.]); light /= np.linalg.norm(light)
    brightness = .25 + .75*np.maximum(0, normals @ light)
    colors = brightness[:,None]*np.array([.9,.52,.25])[None,:]
    axes[0].add_collection(PolyCollection(polys, facecolors=colors, edgecolors='none', antialiased=False))
    axes[0].autoscale_view(); axes[0].set_aspect('equal')
    axes[0].set_title('Actual cropped hammered surface')
    axes[0].set_xlabel('Production assembly X (mm)'); axes[0].set_ylabel('Production assembly Y (mm)')
    axes[1].add_collection(PolyCollection(m.triangles[:,:,[0,2]],facecolors='#b87333',edgecolors='none',alpha=.13))
    axes[1].autoscale_view();axes[1].set_aspect('equal');axes[1].axhline(0,color='#34495e')
    axes[1].set_xlabel('Bed X (mm)');axes[1].set_ylabel('Height (mm)');axes[1].set_title('Side view: retained production carrier')
    fig.suptitle('A2L hammered finish / ERYONE copper / r1',fontsize=16)
    fig.tight_layout();fig.savefig(OUT/'mesh-preview.png',dpi=160);plt.close(fig)


def slice_project():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    folder=WORK/'native';folder.mkdir(parents=True,exist_ok=True)
    with (WORK/'slice.log').open('w',encoding='utf-8') as log:
        r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(folder),str(EDIT)],
            cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    r.check_returncode()
    print((folder/'result.json').read_text(),flush=True)


def inspect_native(text):
    feature='Custom';x=y=z=e=speed=accel=0.;rel=False;xyz=False
    speeds=collections.defaultdict(list);accelerations=collections.defaultdict(set)
    nozzle=set();bed=set();fans=collections.defaultdict(set);layers=collections.defaultdict(list)
    for line in text.splitlines():
        if line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in re.findall(r'([XYZEFISP])([+-]?(?:\d+(?:\.\d*)?|\.\d+))',code)}
        if cmd in ('M104','M109') and 'S' in v:nozzle.add(v['S'])
        if cmd in ('M140','M190') and 'S' in v:bed.add(v['S'])
        if cmd=='M106' and 'S' in v:fans[str(int(v.get('P',1)))].add(v['S'])
        if cmd=='M204':accel=v.get('S',v.get('P',accel))
        if cmd=='M83':rel=True
        elif cmd=='M82':rel=False
        elif cmd in ('G90','G91'):xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ('G0','G1','G2','G3'):
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if rel else v.get('E',e)-e;speed=v.get('F',speed)
            if de>0 and math.hypot(nx-x,ny-y)>.001 and feature!='Custom':
                assert cmd=='G1'
                speeds[feature].append(speed/60);accelerations[feature].add(accel)
                if round(nz,3) in (.2,10,30,60):layers[round(nz,3)].append(([[x,y],[nx,ny]],feature))
                # Saved overhang speeds are absolute; some exceed nominal 40.
                if feature=='Outer wall':assert speed/60<=50.001
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if rel else v.get('E',e)
    assert nozzle=={0.,140.,220.} and bed=={0.,55.}
    assert not any('sparse' in k.lower() for k in speeds)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig,axes=plt.subplots(2,2,figsize=(12,7),facecolor='white')
    for ax,height in zip(axes.ravel(),(.2,10,30,60)):
        for support,color in [(True,'#3e92b8'),(False,'#ab612d')]:
            lines=[line for line,kind in layers[height] if ('Support' in kind)==support]
            if lines:ax.add_collection(LineCollection(lines,colors=color,linewidths=.55))
        ax.set_xlim(50,276);ax.set_ylim(63,175);ax.set_aspect('equal');ax.set_title(f'Z {height:.1f} mm')
        ax.set_xlabel('Bed X (mm)');ax.set_ylabel('Bed Y (mm)')
    fig.suptitle('Actual native A2L toolpaths / copper = model, blue = supports',fontsize=14)
    fig.tight_layout();fig.savefig(OUT/'toolpath-preview.png',dpi=150);plt.close(fig)
    return dict(actual_feature_speed_ranges_mm_s={k:[min(v),max(v)] for k,v in speeds.items()},
        actual_feature_accelerations_mm_s2={k:sorted(v) for k,v in accelerations.items()},
        nozzle_commands_celsius=sorted(nozzle),bed_commands_celsius=sorted(bed),
        fan_commands_pwm_0_255={k:sorted(v) for k,v in fans.items()},
        outer_wall_configured_speed_mm_s=40.,actual_outer_wall_maximum_mm_s=50.,
        speed_note='Saved first-layer/overhang rules can emit 50 mm/s despite the nominal 40 mm/s outer-wall setting.',
        first_layer_outer_wall_speed_mm_s=50.,no_sparse_toolpaths_in_solid_veneer=True)


def validate():
    from validate_production_split import Project, distance
    from shapely.geometry import MultiPoint
    report=json.loads((OUT/'validation.json').read_text())
    assert sha(SOURCE)==report['source_sha256'] and sha(EDIT)==report['editable_sha256']
    edited=Project(EDIT);native=Project(WORK/'native/sliced.3mf')
    assert edited.settings==native.settings
    assert len(native.rows)==len(native.cfg.findall('plate'))==1
    s=native.settings
    for k,value in LOCKS.items():assert s[k]==value,(k,s.get(k),value)
    assert s['nozzle_diameter']==['0.4'] and s['printer_model']=='Bambu Lab A2L'
    a,b=edited.rows[OBJECT],native.rows[OBJECT]
    assert {k:v for k,v in a['settings'].items() if k}=={k:v for k,v in b['settings'].items() if k}
    assert len(a['parts'])==len(b['parts'])==1
    old={k:v for k,v in report['source_object_overrides'].items() if k not in ('name','null',None)}
    new={k:v for k,v in b['settings'].items() if k not in ('name',None)}
    assert old==new,(old,new)
    # Source/import bookkeeping differs; all effective volume overrides must match.
    ignore={'name','matrix','source_file','source_object_id','source_volume_id','source_offset_x','source_offset_y','source_offset_z'}
    before={k:v for k,v in report['source_part_metadata'].items() if k not in ignore}
    after={k:v for k,v in b['parts'][0]['settings'].items() if k not in ignore}
    assert before==after
    effective={**s,**b['settings'],**after}
    assert effective['sparse_infill_density']=='100%' and effective['sparse_infill_pattern']=='gyroid'
    assert effective['enable_support']=='1' and effective['support_type']=='tree(auto)' and effective['extruder']=='3'
    for k,value in LOCKS.items():
        if k!='sparse_infill_density':assert effective[k]==value
    av=a['parts'][0]['mesh'].vertices@a['T'][:3,:3].T+a['T'][:3,3]
    bv=b['parts'][0]['mesh'].vertices@b['T'][:3,:3].T+b['T'][:3,3]
    error=distance(av,bv);assert error<.001
    raw=native.z.read('Metadata/plate_1.gcode');text=raw.decode()
    assert hashlib.md5(raw).hexdigest()==native.z.read('Metadata/plate_1.gcode.md5').decode().strip().lower()
    config={}
    for line in text.splitlines():
        if line.startswith('; ') and ' = ' in line:
            k,v=line[2:].split(' = ',1);config[k]=v
    for k,value in LOCKS.items():assert config[k]==value,(k,config.get(k))
    assert config['nozzle_diameter']=='0.4' and config['printer_model']=='Bambu Lab A2L'
    for k in ['filament_settings_id','nozzle_temperature','nozzle_temperature_initial_layer','textured_plate_temp','textured_plate_temp_initial_layer','filament_flow_ratio','filament_max_volumetric_speed']:
        assert config[k].replace('"','') in (';'.join(s[k]),','.join(s[k])),(k,config[k],s[k])
    scan=scan_gcode(text)
    lo,hi=np.array(scan['bead_xy_bounds_mm']);margin=float(min(*lo,*(np.array([330,320])-hi)))
    # The legacy scanner's default is a 256 mm A1 bed. Override for actual A2L.
    scan['conservative_bed_edge_clearance_mm']=margin
    assert margin>.5 and set(scan['model_extrusion_z_by_filament_mm'])=={'3'}
    assert max(scan['model_extrusion_z_by_filament_mm']['3'])<=75.001
    info=ET.fromstring(native.z.read('Metadata/slice_info.config'))
    warnings=[w.attrib for p in info.findall('plate') for w in p.findall('warning')]
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
    bonds=check_fin_bonds(text,report)
    base_probes=dict(bond_probes_print_xyz_mm=[[x,69.9796234048,.2] for x in (56.7,100.,160.,220.,263.6)])
    base=check_fin_bonds(text,base_probes)
    actual=inspect_native(text)
    tower=check_startup_tower(s,[MultiPoint(bv[:,:2]).convex_hull],1,75,1)
    result=json.loads((WORK/'native/result.json').read_text());assert result['return_code']==0
    assert len(result['sliced_plates'])==1
    assert protected()==report['protected_before']
    FINAL.write_bytes((WORK/'native/sliced.3mf').read_bytes())
    report.update(status='DIGITAL_CHECKS_PASSED_PHYSICAL_FINISH_UNTESTED',current_file=str(FINAL),
        current_sha256=sha(FINAL),native_mesh_pose_max_error_mm=error,global_settings_editable_equals_sliced=True,
        all_source_object_and_effective_volume_overrides_preserved=True,gcode_locked_settings_verified=True,
        gcode_sha256=hashlib.sha256(raw).hexdigest(),gcode_md5_verified=True,scan=scan,
        extrusion_bed_edge_clearance_mm=margin,slicer_warnings=warnings,bond_toolpath_check=bonds,
        retained_end_band_first_layer_toolpath_check=base,actual_native_commands=actual,
        startup_tower_check=tower,native_result=result,protected_after=protected(),
        production_and_A1_files_unchanged=True,builder_sha256=sha(Path(__file__)))
    save_json(OUT/'validation.json',report)
    side=json.loads(EDIT.with_suffix('.json').read_text());side.update(native_slice_validated=True,
        native_project=FINAL.name,native_sha256=sha(FINAL),physical_confirmation_pending=True)
    save_json(EDIT.with_suffix('.json'),side)
    write_instructions(report)
    print(json.dumps(dict(file=str(FINAL),sha256=sha(FINAL),warnings=warnings,bonds=bonds,
        estimate=result['sliced_plates']),indent=2),flush=True)


def write_instructions(r):
    instructions = f'''DARA A2L HAMMERED FINISH - ERYONE ULTRA SILK COPPER - r1
Prepared 2026-10-22. Physical finish remains untested.

CURRENT PRINT PROJECT: {FINAL.name}
SHA-256: {r['current_sha256']}
Open AS A PROJECT in Bambu Studio to retain the saved configuration and slice.
Printer: Bambu Lab A2L, 0.4 mm nozzle, Textured PEI Plate.
Filament: ERYONE Ultra Silk Copper PLA, 1.75 mm, assigned to project slot 3.
Other project slots retain white / wood tan / Azurite blue; only copper is used.
Slicer estimate: 3 h 16 min 43 sec (about 3 h 17 min), 45.31 g including carrier
and native tree supports; 15.19 m filament, no filament changes. The estimate
does not predict your actual calibration overhead or physical result.

WHAT THIS TEST MEASURES
An unchanged crop of the actual production hammered face, printed with the
saved complete 55-degree orientation and a cropped portion of its bonded
wall carrier. The test variable is the requested physical copper filament.
Inspect dimple definition, metallic sheen, layer lines and ringing in grazing
light. Record the exact r1 filename, printer, spool and any calibration choices
with the result. Gloss, adhesion, removal and full-size warping remain unknown.
This small crop cannot qualify a full veneer or any mating joint.

SAVED SETTINGS
Layer / first layer: 0.20 / 0.20 mm; four wall loops; five top / bottom layers.
The veneer and its carrier retain their existing 100% solid setting. Sparse
infill has no effect here; the global 8% gyroid baseline is simply retained.
Nozzle: 220 C all printing layers. Textured PEI bed: 55 C all layers.
Slot-3 maximum volumetric speed: 7.5 mm3/s; flow ratio: 0.98.
Outer wall: nominal 40 mm/s. Actual outer-wall moves span 10-50 mm/s because
of the saved first-layer and overhang rules. Outer-wall acceleration in the
G-code is 5000 mm/s2 (500 mm/s2 on the first layer).
Inner wall setting remains 80 mm/s. Classic wall generator is preserved.
Part-cooling profile: 60-80%, with the existing 100% overhang-fan override;
first-layer cooling remains off. Actual emitted part-fan values include 65-76%
and 100%. Auxiliary/exhaust channels P2/P3 are only commanded off in this slice,
even though the saved generic material contains an auxiliary-fan value of 70%.
Tree supports and all saved support, brim, seam, purge and numeric filament
settings remain unchanged. The slot-3 profile name/vendor identifies ERYONE;
it is the production numeric baseline, not a calibrated manufacturer preset.

ERYONE lists 190-220 C nozzle, 55-70 C bed and 30-60 mm/s printing speed:
https://eryone3d.com/products/advanced-silk-pla
User-confirmed product: https://www.amazon.com/gp/product/B089Y6BWN3/
The broad speed recommendation does not describe all feature-specific moves
in the saved production profile. This is a physical evaluation of that profile.

GEMINI ADVICE REVIEW
The saved 7.5 mm3/s flow limit and nominal 40 mm/s outer-wall speed are lower
than the suggested 10-12 mm3/s and 50-60 mm/s. Outer acceleration already
falls within the suggested range. Temperature is already 220 C. Bed and
cooling remain the production baseline, so the first result is comparable.
Infill suggestions do not affect this solid veneer. No change to wall count,
wall generator or cooling was made merely from the supplied advice.
An automatic flow calibration is a printer launch choice; no printer session
or launch setting has been changed by preparation of this project.

PRINT AND INSPECT
Keep the saved orientation, carrier and supports. Map project slot 3 to the
actual copper spool in the print dialog. No print has been sent.
Let the plate cool before removal. Support the decorative face with a soft
lined caul and cut the fused necks individually; do not pull the carrier off
by bending the thin veneer. Check the finish before sanding or coating it.
Capture photographs under consistent lighting and note any changed settings.

SOURCE AND CROP
Source: {SOURCE}
Source SHA-256: {r['source_sha256']}
Source plate 15; object 273, part 272:
V1 A2L hammered veneer and wall cradle r6 end ties.
Source-plate coordinates, millimetres: X 0..330, Y 67..165, Z 0..75.
Actual retained bounds: X 56.191410104..268.655731,
Y 67.9796234048..165, Z 0..75. No translation or rotation was added.
The crop retains the minimum-Y end band, a connecting web, inclined backing,
rear wall and 28 complete original fused-neck probe locations. The opposite
end band and other neighboring geometry fall outside the crop. Nothing is
added within it. New planar crop faces are not production appearance surfaces.
Cropping changes height, mass, edge cooling and restraint, independently of
the material being evaluated. Sample footprint is about 212.5 x 97.0 mm,
75 mm high. Decorative face area is approximately 2295 mm2.

CHECKS PERFORMED
Exact Boolean crop, no added stock, watertight single connected volume, Z0
bed contact; source orientation and effective object/volume settings retained.
Global settings compared in full: only test name, slot-3 name/vendor and the
one-plate tower-coordinate arrays differ. All effective process values match.
Editable and native-sliced project settings match. Locked settings and material
values verified in G-code configuration. Actual native paths contain no sparse
infill and use only filament 3. Printing nozzle/bed commands are 220/55 C;
the saved startup routine also uses a 140 C nozzle preheat and shutdown uses 0.
All 28 retained neck probes have model extrusion within 0.099 mm; five probes
across the retained bed band have first-layer model extrusion. Model/support
extrusion is within the A2L bed, with a minimum 56.191 mm bead-edge clearance.
No single-color prime tower is emitted. Geometry matches the editable project
within 0.001 mm after native serialization. G-code MD5 checksum passed.
Only the two native traditional-timelapse compatibility notices remain; there
are no floating-region or collision warnings. Hashes of 11 protected A2L/A1
production files were unchanged. These are digital checks, not a physical pass.

FILES
{FINAL.name}: the current sliced test to open.
{EDIT.name}: matching editable source for the SAME r1 test.
validation.json: exact settings differences, hashes and native toolpath evidence.
mesh-preview.png / toolpath-preview.png: actual mesh and sampled native layers.
SHA256SUMS.txt: hashes of the current project, editable source and evidence.
Builder: scripts/build_a2l_hammered_finish_test.py (build, slice, validate).
Root Dara.3mf and every production plate remain unchanged.
'''
    (OUT/'README.txt').write_text(instructions,encoding='utf-8')
    paths=[FINAL,EDIT,OUT/'validation.json',OUT/'README.txt',OUT/'mesh-preview.png',OUT/'toolpath-preview.png']
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in paths),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','slice','validate'])
    {'build':build,'slice':slice_project,'validate':validate}[parser.parse_args().action]()
