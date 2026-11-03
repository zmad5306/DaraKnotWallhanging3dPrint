"""Separate support-redesign experiment derived from the saved root Dara.3mf.

Never modifies production. Keeps the veneer and existing attachment necks;
replaces the tall fin bodies with an inclined panel, rear wall and two webs.
All new carrier geometry remains solid under the original process settings.
"""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import manifold3d as mf
import trimesh
import shapely
from shapely.geometry import Polygon, box, LineString
from development_3mf import solid, mesh, sha, save_json, tag, transform, props, xml, write_project
from add_blue_ribbon_edge import section
from veneer_trim_carrier import slab_xz

SOURCE = ROOT / 'Dara.3mf'
OUT = ROOT / 'output/Dara-A2L-Veneer-Wall-Cradle-r2'
WORK = ROOT / '.work/veneer-wall-cradle-r2'
P = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
PANEL = 1.2
WEB = 1.2
KEEP_PLANE = 4.1
PANEL_TOP = 4.4


def protected():
    paths = [SOURCE, ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf',
             ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Editable.3mf']
    paths += sorted((ROOT/'working/bambu/Dara-A1-Companion').glob('*'))
    return {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}


def source_veneer(number):
    """Only parse the selected production mesh; retain its triangle attributes."""
    with zipfile.ZipFile(SOURCE) as z:
        cfg = ET.fromstring(z.read('Metadata/model_settings.config'))
        root = ET.fromstring(z.read('3D/3dmodel.model'))
        st = json.loads(z.read('Metadata/project_settings.config'))
        objcfg = next(o for o in cfg.findall('object') if props(o).get('name','').startswith(f'V{number} A2L'))
        oid = objcfg.get('id')
        top = root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
        co = list(top.find(tag('components')))[0]
        child = ET.fromstring(z.read(co.get(P+'path').lstrip('/')))
        body = child.find(tag('resources')).find(f"{tag('object')}[@id='{co.get('objectid')}']").find(tag('mesh'))
        vertices = np.array([[float(v.get(k)) for k in ('x','y','z')] for v in body.find(tag('vertices'))])
        faces = np.array([[int(f.get(k)) for k in ('v1','v2','v3')] for f in body.find(tag('triangles'))])
        m = trimesh.Trimesh(vertices, faces, process=False)
        T = transform(root.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']").get('transform'))
        pi = number + 13
        T[:2,3] -= [pi%5*396, -(pi//5)*384]
        m.apply_transform(T @ transform(co.get('transform')))
        return m, st, props(objcfg), cfg, root, oid


def halfspace(pose, bottom):
    return mf.Manifold.cube([2000,2000,1500]).translate([-1000,-1000,bottom]).transform(pose[:3])


def make(number):
    WORK.mkdir(parents=True, exist_ok=True)
    m, settings, object_settings, cfg, root, oid = source_veneer(number)
    geometry = json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())
    row = geometry['skins'][number-1]
    pose = np.array(row['assembly_to_printer'])
    body = solid(m)
    upper = body ^ halfspace(pose, KEEP_PLANE)
    veneer = body ^ halfspace(pose, 8.6)
    asm = veneer.transform(np.linalg.inv(pose)[:3])
    footprint = asm.project()
    panel = footprint.extrude(PANEL).translate([0,0,PANEL_TOP-PANEL]).transform(pose[:3])
    bed = mf.Manifold.cube([330,320,325])
    panel = panel ^ bed
    # Retain the existing ground ring, all starter feet and their first 1.6 mm.
    base = body ^ mf.Manifold.cube([330,320,1.6])
    pm = mesh(panel)
    # A vertical rear wall follows the upper outline of the inclined panel.
    # The backmost edge meets it directly; each intermediate web joins both.
    coords = pm.vertices
    y0,y1 = coords[:,1].min(), coords[:,1].max()
    rear_x = float(coords[:,0].min())
    # Projection onto YZ followed by a vertical sweep to the bed.
    yz = shapely.union_all(shapely.polygons(coords[pm.faces][:,:,[1,2]]))
    ys = sorted(set([float(y0),float(y1)] + list(np.arange(y0,y1,1.0))))
    heights = []
    for y in ys:
        cut = yz.intersection(LineString([(y,-1),(y,326)]))
        heights.append(float(cut.bounds[3]) if not cut.is_empty else 0.0)
    profile = Polygon([(y0,0),*zip(ys,heights),(y1,0)]).buffer(0)
    # Extrude the YZ profile in X (use a right-handed cyclic transform).
    rear = section(profile).extrude(PANEL).transform(np.array([[0,0,1,rear_x],[1,0,0,0],[0,1,0,0.]]))
    webs=[]; web_records=[]
    # Place the two webs inside the tall region. Equally spaced near the outer
    # silhouette would waste webs on low tips, leaving the tall center alone.
    cumulative=np.cumsum(heights)
    web_ys=np.interp([1/3,2/3],cumulative/cumulative[-1],ys)
    for y in web_ys:
        # Intersect the panel with a thin Y slab to get exact upper endpoints.
        strip = panel ^ mf.Manifold.cube([330,WEB,325]).translate([0,y-WEB/2,0])
        if strip.is_empty(): continue
        sm=mesh(strip)
        # The convex XZ hull extends downward to bed and rear wall, connecting
        # the panel even at disconnected strokes in the veneer silhouette.
        pts = np.vstack([sm.vertices[:,[0,2]], [rear_x,0], [sm.bounds[1,0],0]])
        region = shapely.MultiPoint(pts).convex_hull
        web = slab_xz(region,float(y),WEB)
        webs.append(web)
        web_records.append(dict(y_mm=float(y),xz_profile=list(region.exterior.coords)))
    new_support = mf.Manifold.batch_boolean([panel,rear,*webs],mf.OpType.Add)
    # Preserve positive bed ties from the ACTUAL production mesh, including
    # starter ribs at the rising edge. Feet alone are not an anchor for a
    # veneer that first appears higher up the print.
    carrier=row['carrier'];normal=pose[:3,2]
    boxes=[];tie_records=[];stiffeners=[];stiffener_records=[]
    starter_count=carrier['starter_rib_count']
    for index,probe in enumerate(carrier['bond_probes_print_xyz_mm'][-starter_count:]):
        center=np.array(probe)-normal*2.25
        # Source starter ribs span 1.2 mm in the assembly X direction, which
        # projects to 1.2*cos(55 deg) in print X. A tiny bounding tolerance
        # captures the saved float32 serialization; all retained stock is
        # intersected with production, so this does not enlarge those ribs.
        half=.6*np.cos(np.radians(55))+.0001
        lo=[float(center[0]-half),float(center[1]-.8001),0.]
        hi=[float(center[0]+half),float(center[1]+.8001),325.]
        boxes.append(mf.Manifold.cube(np.subtract(hi,lo)).translate(lo))
        tie_records.append(dict(kind='original_starter_rib',bounds_mm=[lo,hi]))
        if carrier['starter_rib_heights_mm'][index]>48:
            # Keep the original fused neck and rib; thicken its tall free
            # standing lower section to a 2.4 mm square until it meets the
            # backing panel. No added stock reaches the veneer/neck region.
            pillar=mf.Manifold.cube([2.4,2.4,325]).translate([center[0]-1.2,center[1]-1.2,0])
            pillar=pillar-halfspace(pose,KEEP_PLANE+.01)
            stiffeners.append(pillar)
            stiffener_records.append(dict(starter_index=index,center_xy_mm=center[:2].tolist(),
                original_starter_height_mm=carrier['starter_rib_heights_mm'][index],
                strengthened_lower_cross_section_mm=[2.4,2.4]))
    for fin in carrier['fins']:
        xmin,_,xmax,_=fin['fin_xz_bounds_mm'];y=fin['print_y_mm']
        # Preserve each original fin's two vertical end posts and all saved
        # upper fin stock. Together they retain a direct frame down to bed;
        # the continuous wall braces the former fins across their thin axis.
        for xlo,xhi in [(xmin-.0001,min(xmax,xmin+1.6)+.0001),
                        (max(xmin,xmax-1.6)-.0001,xmax+.0001)]:
            lo=[xlo,y-.8001,0.];hi=[xhi,y+.8001,325.]
            boxes.append(mf.Manifold.cube(np.subtract(hi,lo)).translate(lo))
            tie_records.append(dict(kind='original_fin_end_post',bounds_mm=[lo,hi]))
    retained_ties=body ^ mf.Manifold.batch_boolean(boxes,mf.OpType.Add)
    # Upper source stock is already preserved. Keep a 0.01 mm overlap into it
    # without introducing duplicate coincident booleans on the veneer faces.
    retained_ties=retained_ties-halfspace(pose,KEEP_PLANE+.01)
    if stiffeners:
        new_support=new_support+mf.Manifold.batch_boolean(stiffeners,mf.OpType.Add)
    candidate = mf.Manifold.batch_boolean([upper,base,new_support,retained_ties],mf.OpType.Add)
    # Remove only zero-volume numerical debris, never real loose pieces.
    components=[c for c in candidate.decompose() if c.volume()>1e-7]
    assert len(components)==1, ('Disconnected components',number,[c.volume() for c in components])
    candidate=components[0]
    added_at_face=(new_support ^ halfspace(pose,8.6)).volume()
    preserved = body ^ halfspace(pose,5.7)
    retained_difference=((candidate ^ halfspace(pose,5.7))-preserved).volume() + (preserved-candidate).volume()
    assert added_at_face < 1e-6 and retained_difference < 1e-5, (added_at_face,retained_difference)
    cm=mesh(candidate)
    np.savez_compressed(WORK/f'V{number}-candidate.npz',vertices=cm.vertices,faces=cm.faces)
    cm.export(WORK/f'V{number}-candidate.ply')
    m.export(WORK/f'V{number}-production.ply')
    mesh(new_support+retained_ties).export(WORK/f'V{number}-new-support.ply')
    mesh(retained_ties).export(WORK/f'V{number}-retained-bed-ties.ply')
    record=dict(number=number,source_plate=number+14,source_sha256=sha(SOURCE),
        source_object_id=oid,source_name=object_settings['name'],source_volume_mm3=body.volume(),
        veneer_above_rear_plane_volume_mm3=veneer.volume(),candidate_volume_mm3=candidate.volume(),
        modeled_material_g_at_saved_density=candidate.volume()*float(settings['filament_density'][2])/1000,
        source_modeled_material_g_at_saved_density=body.volume()*float(settings['filament_density'][2])/1000,
        support_panel_thickness_mm=PANEL,web_thickness_mm=WEB,webs=web_records,
        direct_bed_ties=tie_records,original_starter_ribs_retained=starter_count,
        original_fin_rows_with_end_posts_retained=len(carrier['fins']),
        tall_starter_stiffeners=stiffener_records,
        web_position_method='one-third and two-thirds of cumulative rear-wall height integral',
        source_carrier_clip_assembly_z_mm=KEEP_PLANE,retained_geometry_above_assembly_z_mm=5.7,backing_panel_top_assembly_z_mm=PANEL_TOP,
        backing_panel_minimum_nominal_rear_gap_mm=8.6-PANEL_TOP,
        minimum_bounds_mm=cm.bounds[0].tolist(),maximum_bounds_mm=cm.bounds[1].tolist(),
        preserved_upper_geometry_difference_mm3=retained_difference,new_support_above_veneer_rear_plane_mm3=added_at_face,
        connected_components=len(components),assembly_to_printer=pose.tolist(),
        bond_probes_print_xyz_mm=row['carrier']['bond_probes_print_xyz_mm'],
        geometry_only_not_slice_estimate=True,physical_confirmation_pending=True)
    save_json(WORK/f'V{number}-geometry.json',record)
    print(json.dumps({k:record[k] for k in ['number','source_modeled_material_g_at_saved_density','modeled_material_g_at_saved_density','preserved_upper_geometry_difference_mm3','connected_components']}),flush=True)
    return record


def project(numbers):
    OUT.mkdir(parents=True, exist_ok=True)
    plates=[]
    for number in numbers:
        record=json.loads((WORK/f'V{number}-geometry.json').read_text())
        _,settings,st,*_=source_veneer(number)
        arrays=np.load(WORK/f'V{number}-candidate.npz')
        cm=trimesh.Trimesh(arrays['vertices'],arrays['faces'],process=False)
        title=f'V{number} A2L veneer wall cradle r2 - physical trial pending'
        st={k:v for k,v in st.items() if k and v is not None and k!='name'}
        plates.append([dict(name=title,parts=[dict(mesh=cm)],settings=st,
                           transform=np.eye(4),block_front=True,
                           front_normal=np.array(record['assembly_to_printer'])[:3,2])])
    suffix='All' if len(numbers)==3 else '-'.join(f'V{i}' for i in numbers)
    filename=f'Dara-A2L-Veneer-Wall-Cradle-r2-{suffix}-Editable.3mf'
    settings.update(print_settings_id='Dara wall cradle r2 - 8% gyroid; solid veneers/carriers',
                    wipe_tower_x=[settings['wipe_tower_x'][i+13] for i in numbers],
                    wipe_tower_y=[settings['wipe_tower_y'][i+13] for i in numbers])
    path=OUT/filename
    write_project(path,plates,settings['print_settings_id'],settings_update=settings)
    side=json.loads(path.with_suffix('.json').read_text())
    side.update(source_project=str(SOURCE.relative_to(ROOT)),source_sha256=sha(SOURCE),
                source_plates=[i+14 for i in numbers],geometry_crop=None,
                support_only_redesign=True,physical_confirmation_pending=True)
    save_json(path.with_suffix('.json'),side)
    print('Created',path,flush=True)


def slice_project(numbers, plate=0):
    suffix='All' if len(numbers)==3 else '-'.join(f'V{i}' for i in numbers)
    path=OUT/f'Dara-A2L-Veneer-Wall-Cradle-r2-{suffix}-Editable.3mf'
    folder=WORK/(suffix if not plate else f'{suffix}-plate-{plate}');folder.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (folder/'cli.log').open('w') as log:
        result=subprocess.run([str(exe),'--slice',str(plate),'--export-3mf','sliced.3mf',
                               '--outputdir',str(folder),str(path)],cwd=exe.parent,
                               stdout=log,stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    print('Slicer exit',result.returncode,flush=True)
    if (folder/'result.json').exists():
        data=json.loads((folder/'result.json').read_text())
        print(json.dumps(data)[:4500],flush=True)
    result.check_returncode()


if __name__=='__main__':
    if (OUT/'WITHDRAWN.txt').exists():
        raise SystemExit('r2 is withdrawn. Preserve its evidence; further carrier designs require a new revision.')
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['geometry','project','slice']);parser.add_argument('--veneers',type=int,nargs='+',default=[1,2,3]);parser.add_argument('--plate',type=int,default=0);a=parser.parse_args()
    before=protected()
    if a.action=='geometry': records=[make(i) for i in a.veneers]
    elif a.action=='project': project(a.veneers)
    else: slice_project(a.veneers,a.plate)
    assert before==protected()
    save_json(WORK/'source-fingerprints.json',before)
