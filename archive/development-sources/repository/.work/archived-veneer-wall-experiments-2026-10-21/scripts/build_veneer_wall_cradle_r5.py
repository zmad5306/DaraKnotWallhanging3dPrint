"""Separate support-redesign experiment derived from the saved root Dara.3mf.

Never modifies production. Keeps the veneer and existing attachment necks;
replaces all tall fin bodies and posts with a grounded inclined sheet, rear wall and two webs.
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
OUT = ROOT / 'output/Dara-A2L-Veneer-Wall-Cradle-r5'
WORK = ROOT / '.work/veneer-wall-cradle-r5'
P = '{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
PANEL = 1.2
WEB = 1.0
REAR = 1.0
KEEP_PLANE = 4.1
PANEL_TOP = 4.4
HOLE_WIDTH=28.0
HOLE_HEIGHT=48.0
HOLE_ROOF_DEGREES=60.0
HOLE_EDGE_MARGIN=12.0
HOLE_LAND=16.0
BAND_WIDTH=4.0
BAND_HEIGHT=.6


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


def lightening_holes(profile,protected_lines=()):
    """Whole pointed openings only; keep broad borders and uncut wall joins."""
    allowed=profile.buffer(-HOLE_EDGE_MARGIN)
    for x in protected_lines:
        allowed=allowed.difference(box(x-8,-1,x+8,400))
    xmin,zmin,xmax,zmax=profile.bounds
    roof=HOLE_WIDTH/2*math.tan(math.radians(HOLE_ROOF_DEGREES))
    holes=[]
    for row,z in enumerate(np.arange(16,zmax-HOLE_HEIGHT,HOLE_HEIGHT+HOLE_LAND)):
        stagger=(row%2)*(HOLE_WIDTH+HOLE_LAND)/2
        for x in np.arange(xmin+HOLE_EDGE_MARGIN+HOLE_WIDTH/2+stagger,xmax,HOLE_WIDTH+HOLE_LAND):
            p=Polygon([(x-HOLE_WIDTH/2,z),(x+HOLE_WIDTH/2,z),
                       (x+HOLE_WIDTH/2,z+HOLE_HEIGHT-roof),(x,z+HOLE_HEIGHT),
                       (x-HOLE_WIDTH/2,z+HOLE_HEIGHT-roof)])
            if allowed.covers(p):holes.append(p)
    return holes


def make(number):
    WORK.mkdir(parents=True, exist_ok=True)
    m, settings, object_settings, cfg, root, oid = source_veneer(number)
    geometry = json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/M-geometry-validation.json').read_text())
    row = geometry['skins'][number-1]
    pose = np.array(row['assembly_to_printer'])
    body = solid(m)
    # Do not carry any of the old base rail, crossbars, center strip or feet.
    # Preserve only actual original neck stock in the bottom 1.6 mm. The new
    # front/rear/web walls themselves provide continuous modeled bed contact.
    old_base_layer=mf.Manifold.cube([330,320,1.60001])
    inverse=np.linalg.inv(pose)
    neck_boxes=[]
    for probe in row['carrier']['bond_probes_print_xyz_mm']:
        q=inverse[:3,:3]@np.asarray(probe)+inverse[:3,3]
        # Original teeth: 1.2 x 1.2 mm in assembly XY, from Z4.3 to Z9.2.
        # Intersect with production so bounding tolerances add no stock.
        neck_boxes.append(mf.Manifold.cube([1.2002,1.2002,4.9002]).translate([q[0]-.6001,q[1]-.6001,4.2999]).transform(pose[:3]))
    neck_mask=mf.Manifold.batch_boolean(neck_boxes,mf.OpType.Add)
    original_necks=body ^ neck_mask
    low_necks=original_necks ^ old_base_layer
    upper=((body ^ halfspace(pose, KEEP_PLANE))-old_base_layer)+low_necks
    veneer = body ^ halfspace(pose, 8.6)
    asm = veneer.transform(np.linalg.inv(pose)[:3])
    # A full inclined sheet grows from a continuous line on the bed. Sweep
    # the retained cap footprint downhill; do not stop at the veneer outline.
    cap_stock = upper - mf.Manifold.cube([330,320,1.6001])
    cap_footprint = cap_stock.transform(np.linalg.inv(pose)[:3]).project()
    polygons = cap_footprint.to_polygons()
    ground_y = (pose[2,3] + pose[2,2]*(PANEL_TOP-PANEL))/(-pose[2,1])
    sweep_parts=[]
    for loop in polygons:
        for a,b in zip(loop,np.roll(loop,-1,axis=0)):
            q=Polygon([a,b,[b[0],ground_y+2],[a[0],ground_y+2]])
            if q.is_valid and q.area>1e-8:sweep_parts.append(q)
    footprint = shapely.union_all(sweep_parts).buffer(.4,join_style=2)
    panel = section(footprint).extrude(PANEL).translate([0,0,PANEL_TOP-PANEL]).transform(pose[:3])
    bed = mf.Manifold.cube([330,320,325])
    panel = panel ^ bed
    pm = mesh(panel)
    # A vertical rear wall follows the upper outline of the inclined panel.
    # Two broad webs join the front and rear walls down to the bed.
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
    rear = section(profile).extrude(REAR).transform(np.array([[0,0,1,rear_x],[1,0,0,0],[0,1,0,0.]]))
    webs=[]; web_records=[]; opening_records=[]; removed_opening_volume=0.
    # Place the two webs inside the tall region. Equally spaced near the outer
    # silhouette would waste webs on low tips, leaving the tall center alone.
    cumulative=np.cumsum(heights)
    web_ys=np.interp([1/3,2/3],cumulative/cumulative[-1],ys)
    rear_holes=lightening_holes(profile,web_ys)
    if rear_holes:
        rear_removed=section(shapely.union_all(rear_holes)).extrude(REAR+.2).transform(np.array([[0,0,1,rear_x-.1],[1,0,0,0],[0,1,0,0.]]))
        removed_opening_volume+=(rear ^ rear_removed).volume()
        rear=rear-rear_removed
    for h in rear_holes:
        opening_records.append(dict(wall='rear',normal_axis=0,plane=rear_x+REAR/2,thickness=REAR,axes=[1,2],polygon_mm=list(h.exterior.coords)))
    for index,y in enumerate(web_ys):
        # Intersect the panel with a thin Y slab to get exact upper endpoints.
        strip = panel ^ mf.Manifold.cube([330,WEB,325]).translate([0,y-WEB/2,0])
        if strip.is_empty(): continue
        sm=mesh(strip)
        # The convex XZ hull extends downward to bed and rear wall, connecting
        # the panel even at disconnected strokes in the veneer silhouette.
        pts = np.vstack([sm.vertices[:,[0,2]], [rear_x,0], [sm.bounds[1,0],0]])
        region = shapely.MultiPoint(pts).convex_hull
        web = slab_xz(region,float(y),WEB)
        holes=lightening_holes(region)
        if holes:
            cutters=slab_xz(shapely.union_all(holes),float(y),WEB+.2)
            removed_opening_volume+=(web ^ cutters).volume()
            web=web-cutters
        for h in holes:
            opening_records.append(dict(wall=f'web-{index+1}',normal_axis=1,plane=float(y),thickness=WEB,axes=[0,2],polygon_mm=list(h.exterior.coords)))
        webs.append(web)
        web_records.append(dict(y_mm=float(y),xz_profile=list(region.exterior.coords)))
    bands=[];band_records=[]
    for record in web_records:
        outline=np.asarray(record['xz_profile']);xmin=float(outline[:,0].min())-.5;xmax=float(outline[:,0].max())+.5
        y=record['y_mm']
        band=mf.Manifold.cube([xmax-xmin,BAND_WIDTH,BAND_HEIGHT]).translate([xmin,y-BAND_WIDTH/2,0])
        bands.append(band)
        band_records.append(dict(x_span_mm=[xmin,xmax],center_y_mm=y,width_mm=BAND_WIDTH,height_mm=BAND_HEIGHT))
    band_stock=mf.Manifold.batch_boolean(bands,mf.OpType.Add)
    new_support = mf.Manifold.batch_boolean([panel,rear,*webs,band_stock],mf.OpType.Add)
    for name,item in [('upper',upper),('panel',panel),('rear',rear),*[(f'web{k}',w) for k,w in enumerate(webs)]]:
        assert item.status()==mf.Error.NoError,(number,name,str(item.status()))
    candidate = mf.Manifold.batch_boolean([upper,new_support],mf.OpType.Add)
    assert candidate.status()==mf.Error.NoError,(number,'union',str(candidate.status()))
    # Remove only zero-volume numerical debris, never real loose pieces.
    components=[c for c in candidate.decompose() if c.volume()>1e-7]
    assert len(components)==1, ('Disconnected components',number,[c.volume() for c in components])
    candidate=components[0]
    added_at_face=(new_support ^ halfspace(pose,8.6)).volume()
    preserved = (body ^ halfspace(pose,5.7))-old_base_layer
    original_necks_removed=abs((original_necks-candidate).volume())
    # The source and transformed neck masks have rounded coincident faces.
    # Bound both residual volume and its thickness rather than accepting any
    # large missing feature merely because its net volume is small.
    neck_difference_thickness=0.
    for part in (original_necks-candidate).decompose():
        if abs(part.volume())<=1e-8:continue
        points=mesh(part).vertices;centered=points-points.mean(axis=0)
        _,_,axes=np.linalg.svd(centered,full_matrices=False)
        neck_difference_thickness=max(neck_difference_thickness,float(np.ptp(centered@axes[-1])))
    assert original_necks_removed<1e-4 and neck_difference_thickness<.001,('Original attachment stock removed',number,original_necks_removed,neck_difference_thickness)
    # Below the former base height, permit only the new walls and original necks.
    allowed_base=(new_support+low_necks) ^ old_base_layer
    extra_base=abs(((candidate ^ old_base_layer)-allowed_base).volume())
    assert extra_base<1e-5,('Legacy base stock remains',number,extra_base)
    prior_data=np.load(ROOT/f'.work/veneer-wall-cradle-r4/V{number}-candidate.npz')
    prior=solid(trimesh.Trimesh(prior_data['vertices'],prior_data['faces'],process=False))
    old_base_removed=(prior-candidate) ^ old_base_layer
    above_base_difference=abs(((prior-candidate)-old_base_layer).volume())+abs(((candidate-prior)-old_base_layer).volume())
    assert above_base_difference<1e-5,('Change above the old base layer',number,above_base_difference)
    retained_difference=abs((((candidate ^ halfspace(pose,5.7))-old_base_layer)-preserved).volume()) + abs((preserved-candidate).volume())
    assert abs(added_at_face) < 1e-6 and abs(retained_difference) < 1e-5, (added_at_face,retained_difference)
    cm=mesh(candidate)
    np.savez_compressed(WORK/f'V{number}-candidate.npz',vertices=cm.vertices,faces=cm.faces)
    cm.export(WORK/f'V{number}-candidate.ply')
    m.export(WORK/f'V{number}-production.ply')
    mesh(new_support).export(WORK/f'V{number}-new-support.ply')
    for title,part in [('panel',panel),('rear',rear),('webs',mf.Manifold.batch_boolean(webs,mf.OpType.Add)),('upper',upper),('bands',band_stock),('bed-contact',allowed_base),('removed-base',old_base_removed)]:
        mesh(part).export(WORK/f'V{number}-{title}.ply')
    record=dict(number=number,source_plate=number+14,source_sha256=sha(SOURCE),
        source_object_id=oid,source_name=object_settings['name'],source_volume_mm3=body.volume(),
        veneer_above_rear_plane_volume_mm3=veneer.volume(),candidate_volume_mm3=candidate.volume(),
        modeled_material_g_at_saved_density=candidate.volume()*float(settings['filament_density'][2])/1000,
        source_modeled_material_g_at_saved_density=body.volume()*float(settings['filament_density'][2])/1000,
        support_panel_thickness_mm=PANEL,rear_wall_thickness_mm=REAR,web_thickness_mm=WEB,webs=web_records,
        isolated_tall_posts=0,front_panel_continuous_to_bed=True,
        old_local_base_removed_volume_mm3=old_base_removed.volume(),
        legacy_base_stock_remaining_mm3=extra_base,
        original_neck_stock_removed_mm3=original_necks_removed,
        neck_comparison_residual_max_thickness_mm=neck_difference_thickness,
        difference_from_r4_above_base_mm3=above_base_difference,
        old_base_removal_height_mm=1.60001,bed_tie_bands=band_records,band_volume_mm3=band_stock.volume(),
        lightening_opening_removed_volume_mm3=removed_opening_volume,
        opening_count=len(opening_records),openings=opening_records,
        opening_dimensions_mm=[HOLE_WIDTH,HOLE_HEIGHT],opening_roof_degrees=HOLE_ROOF_DEGREES,
        minimum_opening_edge_margin_mm=HOLE_EDGE_MARGIN,opening_grid_land_mm=HOLE_LAND,
        panel_volume_mm3=panel.volume(),rear_wall_volume_mm3=rear.volume(),
        web_volumes_mm3=[w.volume() for w in webs],upper_original_volume_mm3=upper.volume(),
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
        title=f'V{number} A2L veneer wall cradle r5 - physical trial pending'
        st={k:v for k,v in st.items() if k and v is not None and k!='name'}
        plates.append([dict(name=title,parts=[dict(mesh=cm)],settings=st,
                           transform=np.eye(4),block_front=True,
                           front_normal=np.array(record['assembly_to_printer'])[:3,2])])
    suffix='All' if len(numbers)==3 else '-'.join(f'V{i}' for i in numbers)
    filename=f'Dara-A2L-Veneer-Wall-Cradle-r5-{suffix}-Editable.3mf'
    settings.update(print_settings_id='Dara wall cradle r5 - 8% gyroid; solid veneers/carriers',
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
    path=OUT/f'Dara-A2L-Veneer-Wall-Cradle-r5-{suffix}-Editable.3mf'
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
        raise SystemExit('r5 is withdrawn. Preserve its evidence; further carrier designs require a new revision.')
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['geometry','project','slice']);parser.add_argument('--veneers',type=int,nargs='+',default=[1,2,3]);parser.add_argument('--plate',type=int,default=0);a=parser.parse_args()
    before=protected()
    if a.action=='geometry': records=[make(i) for i in a.veneers]
    elif a.action=='project': project(a.veneers)
    else: slice_project(a.veneers,a.plate)
    assert before==protected()
    save_json(WORK/'source-fingerprints.json',before)
