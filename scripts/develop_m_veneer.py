"""Band-free hammered skin on a flat-printed structural M, development only.

Run with numpy/scipy/shapely/trimesh/manifold3d available:
  python scripts/develop_m_veneer.py build
  python scripts/develop_m_veneer.py orient

The crown, hammer pitch/depth/seed and rear mounting coordinates come from the
existing design. Core and skin use different seam schedules. All skin panels
share M5's assembly-to-printer rotation; rotating each panel to pack is forbidden.
"""
import argparse
import collections
import copy
import json
import math
import xml.etree.ElementTree as ET
import zipfile

import manifold3d as mf
import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely import affinity, union_all
from shapely.geometry import Point, LineString, Polygon, box, mapping, shape
from shapely.ops import split
import trimesh

from development_3mf import ROOT, OUT, WORK, source, source_path, save_json, solid, mesh, centered, z_rotation, common_m_rotation, write_project, sha, mesh_xml, read_object
from add_blue_ribbon_edge import artwork, section
from build_jointed_bambu_project import read_array, tag, P
from validate_print_project import transform, props

CAD = ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad'
CORE_BASE = 8.4
GLUE = .2
SEAT_Z = CORE_BASE + GLUE
BOSS_TOP = SEAT_Z + .4
POCKET_TOP = BOSS_TOP + .1
SCREW_TIP_Z = 8.7
SCREW_CLEARANCE_TOP = SCREW_TIP_Z + .4
SHOW_GAP = 0.0
SEAM_SAMPLE_GAP = 0.0
GRID = .5
GLUE_SAMPLE_WINDOW = (-290, 25, -212, 94)
SEAM_SAMPLE_WINDOW = (-290, -90, -220, -40)
SKIN_JOINTS = [
    [2, 3, [32.336138117987566, 136.58266699147163], 57.06125907870988, 70, []],
    [2, 1, [-32.336138117987566, 136.58266699147163], 122.93874092129012, 70, []],
    [4, 1, [-257, -65], 90, 130, []],
    [6, 3, [257, -65], 90, 130, []],
    [2, 5, [0, 0], 270, 96, []],
]


def axes(j):
    a = math.radians(j[3]); n = np.array([math.cos(a), math.sin(a)])
    return n, np.array([-n[1], n[0]])


def locate(g, j):
    return affinity.translate(affinity.rotate(g, j[3], origin=(0, 0)), *j[2])


def line(j, extra=20):
    n, t = axes(j); c = np.array(j[2]); h = j[4] / 2 + extra
    return LineString([c - t*h, c + t*h])


def prism(g, bottom, top):
    return section(g).extrude(top-bottom).translate([0, 0, bottom])


def crown(outline, xy):
    t = np.clip(shapely.distance(shapely.points(xy), outline.boundary) / 17.5, 0, 1)
    return 2.2 * (2*t - t*t)


def core_top(xy):
    """The structural body has one flat upper plane; only locators rise above."""
    return np.full(len(xy),CORE_BASE,dtype=float)


def skin_bottom(xy):
    """Flat veneer back: the entire convex profile belongs to its front."""
    return np.full(len(xy),SEAT_Z,dtype=float)


def screw_clearance_tools():
    # Existing screw tips reach Z8.7. A flat 8.4 mm core provides the threaded
    # passage; a shallow clearance in the cap accommodates the unchanged tips.
    screws=read_array(CAD.read_text(),'screw_mounts')
    return mf.Manifold.batch_boolean([
        mf.Manifold.cylinder(SCREW_CLEARANCE_TOP-CORE_BASE+.01,2.1,circular_segments=64).translate([*r[2],CORE_BASE-.01])
        for r in screws],mf.OpType.Add)


def screw_exclusion():
    return union_all([Point(*r[2]).buffer(4.5) for r in read_array(CAD.read_text(),'screw_mounts')])


def top_section(body):
    region=Polygon()
    for ring in body.slice(CORE_BASE-.01).to_polygons():
        region=region.symmetric_difference(Polygon(ring))
    return region


def texture(outline):
    xmin, ymin, xmax, ymax = outline.bounds
    rng = np.random.RandomState(73); centers = []
    for row in range(-2, int(np.ceil((ymax-ymin)/(9*.866)))+5):
        for col in range(-2, int(np.ceil((xmax-xmin)/9))+5):
            centers.append([(col-.5)*9 + (row % 2)*4.5 + xmin + rng.uniform(-2.52, 2.52),
                            (row-.5)*9*.866 + ymin + rng.uniform(-2.52, 2.52)])
    tree = cKDTree(centers)
    def roof(xy):
        depression = .55*(1-np.minimum(1, (tree.query(xy)[0]/4.95)**2))
        return 10.5 + np.maximum(0, crown(outline, xy)-depression)
    return roof


def height_mesh(region, bottom, top, res=GRID):
    """Conforming clipped global grid; independent panels share texture phase."""
    # Exact-contact seam intersections can otherwise leave coordinates such as
    # -5e-15 at a grid line, producing collapsed boundary triangles after joining.
    region=shapely.set_precision(region,1e-8)
    x0, y0, x1, y1 = region.bounds
    xs = np.arange(math.floor(x0/res)*res, x1, res)
    ys = np.arange(math.floor(y0/res)*res, y1, res)
    xx, yy = np.meshgrid(xs, ys)
    cells = shapely.box(xx.ravel(), yy.ravel(), xx.ravel()+res, yy.ravel()+res)
    clipped = shapely.get_parts(shapely.intersection(cells, region))
    clipped = clipped[(shapely.get_type_id(clipped) == 3) & (shapely.area(clipped) > 1e-12)]
    tris = shapely.get_parts(shapely.constrained_delaunay_triangles(clipped))
    xy0 = shapely.get_coordinates(tris).reshape(-1, 4, 2)[:, :3]
    xy, inv = np.unique(np.round(xy0.reshape(-1, 2), 9), axis=0, return_inverse=True)
    f = inv.reshape(-1, 3)
    a, b = xy[f[:, 1]]-xy[f[:, 0]], xy[f[:, 2]]-xy[f[:, 0]]
    flip = a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0] < 0
    f[flip] = f[flip, ::-1]
    edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    _, ids, counts = np.unique(np.sort(edges, axis=1), axis=0, return_index=True, return_counts=True)
    boundary = edges[ids[counts == 1]]; n = len(xy)
    low = np.full(n, bottom) if np.isscalar(bottom) else bottom(xy)
    high = np.full(n, top) if np.isscalar(top) else top(xy)
    assert np.min(high-low) > 0
    v = np.vstack([np.column_stack([xy, high]), np.column_stack([xy, low])])
    side = np.vstack([np.column_stack([boundary[:, 1], boundary[:, 0], boundary[:, 0]+n]),
                      np.column_stack([boundary[:, 1], boundary[:, 0]+n, boundary[:, 1]+n])])
    result = trimesh.Trimesh(v, np.vstack([f, f[:, ::-1]+n, side]), process=True)
    assert result.is_volume, (region.bounds, result.is_watertight, result.volume)
    return result, dict(minimum_sampled_thickness_mm=float(np.min(high-low)), vertices=n)


def partition(outline, joints):
    regions = [outline]
    for j in joints:
        regions = [q for p in regions for q in split(p, line(j, 30)).geoms]
    assert len(regions) == 6, len(regions)
    assert union_all(regions).symmetric_difference(outline).area < 1e-6
    return regions


def fit_angle(m):
    v = m.vertices
    hull = np.asarray(Polygon(v[:, :2]).convex_hull.exterior.coords)
    best = (math.inf, None)
    for a in np.arange(0, 180, .25):
        r = z_rotation(a); d = np.ptp(hull @ r[:2, :2].T, axis=0)
        if max(d) < best[0]: best = (float(max(d)), float(a))
    assert best[0] <= 252, best
    return best[1]


def rod(a, b, radius):
    a, b = np.asarray(a), np.asarray(b)
    d = b-a; length = np.linalg.norm(d)
    m = mesh(mf.Manifold.cylinder(length, radius, circular_segments=16))
    t = trimesh.geometry.align_vectors([0,0,1],d/length)
    t[:3,3] = a; m.apply_transform(t)
    return solid(m)


def carrier(m, region, outline, bottom, pose, exclusion):
    """Solid fins and repeated rear teeth; ordinary trees are supplementary."""
    from veneer_fin_carrier import fin_carrier
    return fin_carrier(m, region, bottom, pose, exclusion, height_mesh)


def seam_sample_panels(sample):
    return [sample.intersection(box(-400,-65+SEAM_SAMPLE_GAP/2,0,200)),
            sample.intersection(box(-400,-200,0,-65-SEAM_SAMPLE_GAP/2))]


def check_sample_seam(meshes):
    """Both actual veneer front edges must meet on Y=-65 with matching texture."""
    edges=[]
    for m in meshes:
        v=m.vertices
        edge=v[(abs(v[:,1]+65)<1e-7)&(v[:,2]>POCKET_TOP+.01)]
        edge=np.unique(np.round(edge[:,[0,2]],7),axis=0)
        assert len(edge)>20,('Missing front seam',len(edge))
        edges.append(edge)
    error=max(float(cKDTree(edges[0]).query(edges[1])[0].max()),
              float(cKDTree(edges[1]).query(edges[0])[0].max()))
    assert error<1e-6,('Veneer front edges do not match',error)
    collision=(solid(meshes[0])^solid(meshes[1])).volume()
    assert abs(collision)<1e-5,collision
    return dict(nominal_cosmetic_gap_mm=0,seam_assembly_y_mm=-65,
                matching_front_edge_vertices=[len(e) for e in edges],
                maximum_front_edge_mismatch_mm=error,veneer_interference_mm3=collision,
                core_glue_gap_mm=GLUE)


def profile(cad, name):
    import ast, re
    body = cad.split('module '+name+'() {', 1)[1].split('\n}', 1)[0]
    return Polygon(ast.literal_eval(re.search(r'points\s*=\s*(\[.*?\])\s*,\s*paths', body, re.S)[1]))


def xz_prism(poly, j):
    # The XZ profile is extruded along local Y, matching the frozen lap.
    raw = section(poly).extrude(j[4]+40)
    m = mesh(raw)
    t = np.array([[1,0,0,0], [0,0,1,-j[4]/2-20], [0,1,0,0], [0,0,0,1.]])
    m.apply_transform(t)
    # Axis swap flips winding; repair orientation before the solid conversion.
    if m.volume < 0: m.invert()
    a = z_rotation(j[3]); t = np.eye(4); t[:3,:3] = a; t[:2,3] = j[2]
    m.apply_transform(t)
    return solid(m)


def key(j, y, pocket=False):
    r = .75 + (.15 if pocket else 0)
    # Frozen rounded key spans X2.25..15.75, Y +/-1.5.
    p = box(2.25+r-(.15 if pocket else 0), -1.5+r-(.15 if pocket else 0),
            15.75-r+(.15 if pocket else 0), 1.5-r+(.15 if pocket else 0)).buffer(r, quad_segs=6)
    p = affinity.translate(p, yoff=y)
    return prism(locate(p, j), 4.94 if pocket else 4.79, 6.30 if pocket else 6.0)


def sample_project(filename, sample, panels, cores, whole, outline, core_top, skin_bottom, roof, core_settings, skin_settings):
    """Actual core geometry plus matched seating/locators and trim-away skins."""
    samples=[]
    for i,c in enumerate(cores):
        # Remove full-size seating bosses; put matched coupon bosses back below.
        q=c^prism(sample,-.01,14)^whole
        if q.volume()>1:
            assert len(q.decompose())==1, (filename, i+1, 'Crop disconnects core material')
            samples.append([i,q])
    # Preserve holes when testing ownership. A pad must be supported over its
    # entire footprint, not merely have its centre inside an outer contour.
    seat_regions=[]
    for _,q in samples:
        section_region=top_section(q)
        seat_regions.append(section_region.buffer(-2.6))
    skin_objects=[];seats=[];sample_skins=[]
    for index,region in enumerate(panels):
        v,_=height_mesh(region,skin_bottom,roof);skin=solid(v)-screw_clearance_tools()
        points=np.array([(x,y) for x in np.arange(region.bounds[0]+5,region.bounds[2]-4,3)
                         for y in np.arange(region.bounds[1]+5,region.bounds[3]-4,3)])
        good=shapely.contains(region.buffer(-4),shapely.points(points))&(shapely.distance(shapely.points(points),outline.boundary)>20)
        good &= shapely.contains(union_all(seat_regions),shapely.points(points))
        points=points[good];assert len(points)>=3,(filename,index,len(points))
        p0=points[0];p1=points[np.argmax(np.linalg.norm(points-p0,axis=1))];d=p1-p0;dd=points-p0
        p2=points[np.argmax(np.abs(d[0]*dd[:,1]-d[1]*dd[:,0]))]
        aa=math.degrees(math.atan2(d[1],d[0]));row=[]
        for k,p in enumerate([p0,p1,p2]):
            # Locate the core using real material beneath the contact, not a box.
            owner=next(item for item,safe in zip(samples,seat_regions) if safe.contains(Point(*p)))
            owner[1]+=mf.Manifold.cylinder(.25,2.5,circular_segments=32).translate([*p,SEAT_Z-.25])
            if k<2:
                owner[1]+=mf.Manifold.cylinder(.45,1.2,circular_segments=32).translate([*p,SEAT_Z-.05])
                pocket=(LineString([(-.4,0),(.4,0)]) if k else Point(0,0)).buffer(1.35,quad_segs=12)
                pocket=affinity.translate(affinity.rotate(pocket,aa,origin=(0,0)),*p)
                skin-=prism(pocket,SEAT_Z-.1,POCKET_TOP)
            row.append(p.tolist())
        excluded=union_all([Point(*p).buffer(6) for p in row]).union(screw_exclusion())
        v=mesh(skin);sample_skins.append(v);pose=centered(v,common_m_rotation(),z=2.4)
        carried,evidence=carrier(v,region,outline,skin_bottom,pose,excluded)
        skin_objects.append(dict(name=f'Veneer coupon {index+1} - fused carrier',parts=[dict(mesh=carried)],transform=np.eye(4),settings=skin_settings,block_front=True))
        seats.append(dict(panel=index+1,pads_xy_mm=row,carrier=evidence))
    objs=[]
    for n,(i,c) in enumerate(samples):
        assert len(c.decompose())==1, (filename, i+1, 'Disconnected seating feature')
        m=mesh(c);xy=(128,110) if len(samples)==1 else (75+n*103,120)
        objs.append(dict(name=f'Flat core coupon C{i+1}',parts=[dict(mesh=m)],transform=centered(m,xy=xy),settings=dict(core_settings,sparse_infill_density='8%')))
    plates=[objs]+[[obj] for obj in skin_objects]
    # The caul follows the broad crown, not the individual hammer dimples. Its
    # flat-printed contact face is used with a soft liner and release film.
    caul,_=height_mesh(sample,lambda xy:10.5+crown(outline,xy)+.15,14.8)
    flip=np.diag([1,-1,-1])
    plates.append([dict(name='Smooth crown caul - soft liner and release film',parts=[dict(mesh=caul)],transform=centered(caul,flip),settings=dict(core_settings,extruder='1',brim_width='0',enable_support='0'))])
    write_project(OUT/filename,plates,'DEVELOPMENT - '+filename.removesuffix('.3mf'))
    save_json(OUT/(filename.removesuffix('.3mf')+'-seating.json'),dict(core_body_flat_top_mm=CORE_BASE,veneer_flat_back_mm=SEAT_Z,all_convex_profile_in_veneer=True,glue_gap_mm=GLUE,caul_release_clearance_mm=.15,caul_surface='Smooth broad crown; no hammer dimples',caul_liner_required=True,panels=seats,core_parts=[i+1 for i,_ in samples],sample_bounds_mm=list(sample.bounds),core_connected_components=[len(c.decompose()) for _,c in samples],whole_pad_footprints_supported=True,physical_confirmation_pending=True))
    if len(sample_skins)==2:
        save_json(OUT/'M-zero-gap-seam-validation.json',check_sample_seam(sample_skins))


def refresh_seam_coupon():
    """Rebuild only the matched M seam sample, keeping the smooth caul fixed."""
    assert json.loads((OUT/'M-geometry-validation.json').read_text())['core_crown_mm']==0
    outline=artwork(CAD.read_text(),'letter_outline')
    sample=box(*SEAM_SAMPLE_WINDOW).intersection(outline)
    whole=solid(height_mesh(sample,0,core_top)[0]);cores=[]
    for i in range(6):
        a=np.load(WORK/f'C{i+1}.npz')
        cores.append(solid(trimesh.Trimesh(a['vertices'],a['faces'],process=False)))
    cfg=ET.fromstring(source()['Metadata/model_settings.config'])
    base={k:v for k,v in props(cfg.find("object[@id='192']")).items() if k not in (None,'name')}
    core_settings=dict(base,enable_support='0',brim_width='1',bottom_shell_layers='5',top_shell_layers='5')
    skin_settings=dict(base,enable_support='1',brim_width='3',sparse_infill_density='100%',support_critical_regions_only='0',top_shell_layers='5')
    sample_project('M-Veneer-Seam-Coupon-A1.3mf',sample,seam_sample_panels(sample),cores,whole,
                   outline,core_top,skin_bottom,texture(outline),core_settings,skin_settings)
    print('M seam sample rebuilt: zero cosmetic gap, .20 mm glue space beneath veneer',flush=True)


def refresh_glue_coupon():
    """Rebuild all matched glue-test parts from the cached full-size cores."""
    cad=CAD.read_text();outline=artwork(cad,'letter_outline');roof=texture(outline)
    sample=box(*GLUE_SAMPLE_WINDOW).intersection(outline)
    local_whole=solid(height_mesh(sample,0,core_top)[0])
    cores=[]
    for i in range(6):
        a=np.load(WORK/f'C{i+1}.npz')
        cores.append(solid(trimesh.Trimesh(a['vertices'],a['faces'],process=False)))
    files=source();cfg=ET.fromstring(files['Metadata/model_settings.config'])
    base={k:v for k,v in props(cfg.find("object[@id='192']")).items() if k not in (None,'name')}
    core_settings=dict(base,enable_support='0',brim_width='1',bottom_shell_layers='5',top_shell_layers='5')
    skin_settings=dict(base,enable_support='1',brim_width='3',sparse_infill_density='100%',support_critical_regions_only='0',top_shell_layers='5')
    sample_project('M-Veneer-Glue-Coupon-A1.3mf',sample,[sample],cores,local_whole,outline,core_top,skin_bottom,roof,core_settings,skin_settings)
    print('Glue coupon rebuilt with continuous material below both sockets',flush=True)


def refresh_fins(include_samples=True):
    """Iterate sacrificial tooling while retaining cached artwork/core geometry."""
    plan=json.loads((OUT/'M-geometry-validation.json').read_text())
    assert plan.get('core_crown_mm')==0,'Rebuild the flat-core geometry before refreshing cached fins'
    cad=CAD.read_text();outline=artwork(cad,'letter_outline')
    path=OUT/'M-Core-and-Veneer-A1.3mf'
    staging=json.loads(path.with_suffix('.json').read_text())
    with zipfile.ZipFile(path) as z:files={n:z.read(n) for n in z.namelist()}
    plates=[]
    for row in staging['records'][:6]:
        parts,settings=read_object(files,str(row['object_id']))
        plates.append([dict(name=row['name'],parts=parts,settings=settings,
                            transform=np.array(row['assembly_to_printer']))])
    for i,row in enumerate(plan['skins']):
        data=np.load(WORK/f'V{i+1}.npz')
        m=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        region=shape(plan['skin_regions'][i]);pose=np.array(row['assembly_to_printer'])
        excluded=union_all([Point(*a['xy_mm']).buffer(7) for a in row['anchors']]).union(screw_exclusion())
        carried,evidence=carrier(m,region,outline,skin_bottom,pose,excluded)
        row['carrier']=evidence;carried.export(WORK/f'V{i+1}-with-carrier.stl')
        _,settings=read_object(files,str(staging['records'][i+6]['object_id']))
        if i in [0,2]:settings.update(tree_support_branch_angle='30',raft_first_layer_expansion='0',support_style='default',brim_width='0')
        plates.append([dict(name=f'V{i+1} band-free veneer with sacrificial fins',parts=[dict(mesh=carried)],
                            transform=np.eye(4),settings=settings,block_front=True)])
        print(f'V{i+1}: {evidence["fin_count"]} fins, {evidence["bonded_tooth_count"]} tabs, grounded starter shoe',flush=True)
    plan['project_plates']=write_project(path,plates,'DEVELOPMENT - flat M cores and fin-supported band-free veneers',
        settings_update={'bed_exclude_area':plan['native_support_guard_exclusion']})
    save_json(OUT/'M-geometry-validation.json',plan)
    if not include_samples:
        print('Full-size carriers refreshed; sample projects unchanged',flush=True)
        return
    refresh_glue_coupon()
    sample=box(*SEAM_SAMPLE_WINDOW).intersection(outline)
    local_whole=solid(height_mesh(sample,0,core_top)[0])
    cores=[]
    for i in range(6):
        a=np.load(WORK/f'C{i+1}.npz')
        cores.append(solid(trimesh.Trimesh(a['vertices'],a['faces'],process=False)))
    panels=seam_sample_panels(sample)
    with zipfile.ZipFile(OUT/'M-Veneer-Seam-Coupon-A1.3mf') as z:sample_files={n:z.read(n) for n in z.namelist()}
    _,core_settings=read_object(sample_files,'1000')
    _,skin_settings=read_object(sample_files,'1100')
    sample_project('M-Veneer-Seam-Coupon-A1.3mf',sample,panels,cores,local_whole,outline,core_top,skin_bottom,texture(outline),core_settings,skin_settings)
    print('Both M coupon projects refreshed',flush=True)


def refresh_cauls():
    """Replace only the two white sample cauls, retaining every printable part."""
    from build_jointed_bambu_project import model,xml
    cad=CAD.read_text();outline=artwork(cad,'letter_outline')
    title='Smooth crown caul - soft liner and release film'
    for name,window in [('M-Veneer-Glue-Coupon-A1',GLUE_SAMPLE_WINDOW),('M-Veneer-Seam-Coupon-A1',SEAM_SAMPLE_WINDOW)]:
        path=OUT/(name+'.3mf')
        with zipfile.ZipFile(path) as z:files={n:z.read(n) for n in z.namelist()}
        cfg=ET.fromstring(files['Metadata/model_settings.config']);root=ET.fromstring(files['3D/3dmodel.model'])
        obj=next(o for o in cfg.findall('object') if 'caul' in props(o).get('name','').lower());oid=obj.get('id')
        normal=obj.find("part[@subtype='normal_part']");pid=normal.get('id')
        resource=root.find(tag('resources')).find(f"{tag('object')}[@id='{oid}']")
        co=resource.find(tag('components')).find(f"{tag('component')}[@objectid='{pid}']")
        child_path=co.get('{'+P+'}path').lstrip('/')
        sample=box(*window).intersection(outline)
        caul,_=height_mesh(sample,lambda xy:10.5+crown(outline,xy)+.15,14.8)
        curved=caul.vertices[caul.vertices[:,2]<14.8-1e-8]
        error=float(np.abs(curved[:,2]-(10.5+crown(outline,curved[:,:2])+.15)).max())
        assert error<1e-7,error
        child=model();mesh_xml(ET.SubElement(child,tag('resources')),pid,caul)
        preserved={n:sha_bytes(v) for n,v in files.items() if n.startswith('3D/Objects/') and n!=child_path}
        files[child_path]=xml(child)
        for element in [obj,normal]:
            for md in element.findall('metadata'):
                if md.get('key')=='name':md.set('value',title)
        normal.find('mesh_stat').set('face_count',str(len(caul.faces)))
        plate=cfg.findall('plate')[-1]
        for md in plate.findall('metadata'):
            if md.get('key')=='plater_name':md.set('value',f'{len(cfg.findall("plate"))} - {title}')
        files['Metadata/model_settings.config']=xml(cfg)
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for n,v in files.items():z.writestr(n,v)
        assert all(sha_bytes(files[n])==h for n,h in preserved.items())
        staging=OUT/(name+'.json');report=json.loads(staging.read_text())
        row=report['records'][-1];row['name']=title
        t=np.array(row['assembly_to_printer']);v=caul.vertices@t[:3,:3].T+t[:3,3]
        row['body_bounds_mm']=[v.min(axis=0).tolist(),v.max(axis=0).tolist()]
        save_json(staging,report)
        seating=OUT/(name+'-seating.json');report=json.loads(seating.read_text())
        report.update(caul_surface='Smooth broad crown; no hammer dimples',caul_liner_required=True,
                      caul_surface_error_mm=error,other_object_meshes_byte_identical=True)
        save_json(seating,report)
        print(name+': smooth white caul; cores and veneers unchanged',flush=True)


def sha_bytes(value):
    import hashlib
    return hashlib.sha256(value).hexdigest()


def build(include_samples=True):
    WORK.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    original_hash = sha(source_path()); cad = CAD.read_text()
    outline = artwork(cad, 'letter_outline'); roof = texture(outline)
    core_joints = copy.deepcopy(read_array(cad, 'M_joints'))
    # Move the two otherwise coincident/nearby core joints away from skin seams.
    for index in [0, 4]:
        n, _ = axes(core_joints[index]); core_joints[index][2] = (np.array(core_joints[index][2])+12*n).tolist()
    core_regions = partition(outline, core_joints)
    # Match stable names to source flat M masks by maximum overlap.
    from scipy.optimize import linear_sum_assignment
    old_regions = [artwork(cad, f'M_mask_{i}') for i in range(6)]
    # M_mask coordinates are finished millimetres already (not artwork units).
    old_regions = [affinity.scale(p, 1/.75, 1/.75, origin=(0,0)) for p in old_regions]
    ii, jj = linear_sum_assignment([[-p.intersection(q).area for q in old_regions] for p in core_regions])
    named = {int(j): core_regions[int(i)] for i, j in zip(ii, jj)}
    skin_regions0 = partition(outline, SKIN_JOINTS)
    refs = [(-230,110), (0,90), (230,110), (-220,-130), (0,-100), (220,-130)]
    skin_regions = [next(p for p in skin_regions0 if p.contains(Point(*q))) for q in refs]
    if SHOW_GAP>0:
        cuts = union_all([locate(box(-SHOW_GAP/2,-j[4]/2-30,SHOW_GAP/2,j[4]/2+30), j) for j in SKIN_JOINTS])
        skin_regions = [p.difference(cuts) for p in skin_regions]
    whole = prism(outline,0,CORE_BASE); cores = []; skins = []; reports = []
    # Full-thickness planar keys eliminate supported socket roofs in the core.
    # The separate frame refinement retains its frozen 18 mm lap profile.
    planar_tabs=[]
    for j in core_joints:
        tabs=[]
        for y in j[5]:
            neck=box(-.5,y-3.5,12,y+3.5)
            head=Point(12.0,y).buffer(6.0,quad_segs=12)
            tabs.append(neck.union(head))
        # Retain a continuous outside wall around each female key; a head near
        # the stroke boundary must not cut a loose sliver from the core.
        planar_tabs.append(locate(union_all(tabs),j).intersection(outline.buffer(-3)))
    screws = read_array(cad, 'screw_mounts'); pins = read_array(cad, 'dowel_mounts')
    hardware = []
    for _, _, xy in screws:
        hardware.append(mf.Manifold.cylinder(8.72, 3.175/2, circular_segments=64).translate([*xy,-.02]))
    for _, _, xy, secondary, angle in pins:
        p = box(-.4 if secondary else 0, 0, .4 if secondary else 0, 0).buffer(2.1, quad_segs=16) if secondary else Point(0,0).buffer(2.1, quad_segs=16)
        p = affinity.translate(affinity.rotate(p,angle,origin=(0,0)),*xy)
        hardware.append(prism(p,-.02,3.3))
        mouth = Point(*xy).buffer(2.4,quad_segs=16)
        hardware.append(prism(mouth,-.02,.3))
    tools = mf.Manifold.batch_boolean(hardware, mf.OpType.Add)
    for i in range(6):
        region = named[i]
        # Gap only at the seam, preserving the actual external silhouette.
        gapcuts = union_all([locate(box(-.0375,-j[4]/2-20,.0375,j[4]/2+20),j) for j in core_joints if i in j[:2]])
        footprint = region.difference(gapcuts)
        for j,tabs in zip(core_joints,planar_tabs):
            if j[0] == i:
                footprint=footprint.union(tabs)
            elif j[1] == i:
                footprint=footprint.difference(tabs.buffer(.15,quad_segs=8))
        body = whole ^ prism(footprint,-.01,14)
        body -= tools
        assert len(body.decompose())==1,(i,[(p.volume(),p.bounding_box()) for p in body.decompose()])
        cores.append(body)
        print('Core',i+1,'built',flush=True)
    # Three seating pads per skin, plus a round and a slotted registration pair.
    anchors = []; hole_points = [Point(*r[2]) for r in screws+pins]
    seat_regions=[top_section(c).buffer(-2.6) for c in cores]
    core_seams = union_all([line(j) for j in core_joints])
    for i, region in enumerate(skin_regions):
        v, stats = height_mesh(region,skin_bottom,roof); skin = solid(v)-screw_clearance_tools()
        safe = region.buffer(-5).difference(core_seams.buffer(8))
        for pt in hole_points: safe = safe.difference(pt.buffer(6))
        grid = np.array([(x,y) for x in np.arange(region.bounds[0],region.bounds[2],4)
                         for y in np.arange(region.bounds[1],region.bounds[3],4)])
        good = shapely.contains(safe,shapely.points(grid)) & (shapely.distance(shapely.points(grid),outline.boundary)>20)
        good &= shapely.contains(union_all(seat_regions),shapely.points(grid))
        candidates = grid[good]; assert len(candidates)>=3,(i,len(candidates))
        p0 = candidates[np.argmin(np.linalg.norm(candidates-np.array(region.centroid.coords[0]),axis=1))]
        p1 = candidates[np.argmax(np.linalg.norm(candidates-p0,axis=1))]
        direction=p1-p0;delta=candidates-p0
        p2 = candidates[np.argmax(np.abs(direction[0]*delta[:,1]-direction[1]*delta[:,0]))]
        angle = math.degrees(math.atan2(*(p1-p0)[::-1]))
        row = []
        for k, p in enumerate([p0,p1,p2]):
            owner = next(j for j,r in enumerate(seat_regions) if r.contains(Point(*p)))
            cores[owner] += mf.Manifold.cylinder(.25,2.5,circular_segments=40).translate([*p,SEAT_Z-.25])
            if k<2:
                cores[owner] += mf.Manifold.cylinder(.45,1.2,circular_segments=40).translate([*p,SEAT_Z-.05])
                pocket = Point(0,0).buffer(1.35,quad_segs=12)
                if k==1: pocket=LineString([(-.4,0),(.4,0)]).buffer(1.35,quad_segs=12)
                pocket=affinity.translate(affinity.rotate(pocket,angle,origin=(0,0)),*p)
                skin -= prism(pocket,SEAT_Z-.1,POCKET_TOP)
            row.append(dict(xy_mm=p.tolist(),core=owner+1,role=['primary_round','secondary_axial_slot','seat_only'][k]))
        anchors.append(row); skins.append(skin)
        reports.append(dict(name=f'V{i+1}',**stats,nominal_minimum_thickness_before_pockets_mm=1.9,
                            flat_back_z_mm=SEAT_Z,minimum_roof_over_locator_pocket_mm=1.4,anchors=row))
        print('Veneer',i+1,'built',flush=True)
    # Collision and actual hardware cover checks are geometric, not load ratings.
    core_collision = sum((cores[i]^cores[j]).volume() for i in range(6) for j in range(i))
    skin_collision = sum((skins[i]^skins[j]).volume() for i in range(6) for j in range(i))
    skin_core_collision = sum((v^c).volume() for v in skins for c in cores)
    assert max(core_collision,skin_collision,skin_core_collision)<.001,(core_collision,skin_collision,skin_core_collision)
    cover = []
    for _,_,xy in screws:
        aa=np.linspace(0,2*np.pi,129);q=np.array(xy)+2.1*np.column_stack([np.cos(aa),np.sin(aa)])
        cover.append(float(roof(q).min()-SCREW_CLEARANCE_TOP))
    assert min(cover)>1.0,cover
    tip_clearance=screw_clearance_tools()
    assert sum((v^tip_clearance).volume() for v in skins)<1e-5,'Veneer blocks the existing screw tips'
    files=source(); cfg=ET.fromstring(files['Metadata/model_settings.config']); base=props(cfg.find("object[@id='192']"));base={k:v for k,v in base.items() if k not in (None,'name')}
    core_settings=dict(base,enable_support='0',brim_width='1',bottom_shell_layers='5',top_shell_layers='5')
    skin_settings=dict(base,enable_support='1',brim_width='3',sparse_infill_density='100%',support_critical_regions_only='0',top_shell_layers='5')
    plates=[];core_records=[]
    for i,c in enumerate(cores):
        assert len(c.decompose())==1,(i,'Disconnected core seating feature')
        m=mesh(c);a=fit_angle(m);t=centered(m,z_rotation(a));m.export(WORK/f'C{i+1}.stl');np.savez_compressed(WORK/f'C{i+1}.npz',vertices=m.vertices,faces=m.faces)
        mods=[]
        for n,r in enumerate(screws):
            if named[i].contains(Point(*r[2])):
                mod=mesh(mf.Manifold.cylinder(11,7,circular_segments=48).translate([*r[2],0]))
                mods.append(dict(mesh=mod,subtype='modifier_part',settings=dict(name=f'Screw reinforcement {n+1}',sparse_infill_density='100%')))
        plates.append([dict(name=f'C{i+1} flat structural core',parts=[dict(mesh=m)]+mods,transform=t,settings=dict(core_settings,infill_direction=str((45+a)%180)))])
        core_records.append(dict(name=f'C{i+1}',region=mapping(named[i]),print_rotation_deg=a))
    for i,v in enumerate(skins):
        # The two tall panels need room for actual native tree/brim envelopes,
        # which are asymmetric even though their body silhouettes are mirrored.
        y_center=130 if i==0 else (126 if i==2 else 128)
        m=mesh(v);t=centered(m,common_m_rotation(),z=2.4,xy=(128,y_center));m.export(WORK/f'V{i+1}.stl');np.savez_compressed(WORK/f'V{i+1}.npz',vertices=m.vertices,faces=m.faces)
        assert np.all(np.ptp(m.vertices@t[:3,:3].T,axis=0)<[250,250,253.6])
        excluded=union_all([Point(*a['xy_mm']).buffer(7) for a in anchors[i]]).union(screw_exclusion())
        carried,carrier_report=carrier(m,skin_regions[i],outline,skin_bottom,t,excluded)
        reports[i]['carrier']=carrier_report;reports[i]['assembly_to_printer']=t.tolist()
        carried.export(WORK/f'V{i+1}-with-carrier.stl')
        # Bambu's raft_first_layer_expansion also controls tree-foot expansion
        # without a raft. -1 auto-expands tall trees to the physical bed edge.
        full_settings=dict(skin_settings,brim_width='0',tree_support_branch_angle='30',raft_first_layer_expansion='0',support_style='default') if i in [0,2] else skin_settings
        plates.append([dict(name=f'V{i+1} band-free veneer with fused trim-away carrier',parts=[dict(mesh=carried)],transform=np.eye(4),settings=full_settings,block_front=True)])
    # Keep the main project's original usable bed. Control auxiliary tree feet
    # per object rather than imposing an exclusion on the unrelated knot plates.
    support_guard=[]
    records=write_project(OUT/'M-Core-and-Veneer-A1.3mf',plates,'DEVELOPMENT - flat M cores and common-orientation band-free veneers',settings_update={'bed_exclude_area':support_guard})
    # Independent tests: straighten a continuous skin over a core joint, then
    # close an exposed skin seam over an uninterrupted core. Both use real pads.
    if include_samples:
        sample=box(*GLUE_SAMPLE_WINDOW).intersection(outline)
        sample_project('M-Veneer-Glue-Coupon-A1.3mf',sample,[sample],cores,whole,outline,core_top,skin_bottom,roof,core_settings,skin_settings)
        sample=box(*SEAM_SAMPLE_WINDOW).intersection(outline)
        panels=seam_sample_panels(sample)
        sample_project('M-Veneer-Seam-Coupon-A1.3mf',sample,panels,cores,whole,outline,core_top,skin_bottom,roof,core_settings,skin_settings)
    report=dict(status='Geometry verified; native slicing and physical confirmation tracked separately',source_sha256=original_hash,
                core_base_mm=CORE_BASE,core_crown_mm=0,core_main_top_z_mm=CORE_BASE,veneer_flat_back_z_mm=SEAT_Z,
                entire_convex_profile_in_veneer=True,veneer_crown_mm=2.2,glue_gap_mm=GLUE,nominal_skin_thickness_mm=[1.9,4.1],
                hammer=dict(pitch_mm=9,depth_mm=.55,seed=73),maximum_finished_height_mm=12.7,
                cosmetic_gap_mm=SHOW_GAP,cover_bands=0,core_joint_type='18 mm deep full-thickness planar mushroom keys; support-free mating walls',core_joints=core_joints,skin_joints=SKIN_JOINTS,
                cores=core_records,skins=reports,skin_regions=[mapping(p) for p in skin_regions],
                minimum_roof_over_screw_clearance_mm=min(cover),existing_screw_tip_z_mm=SCREW_TIP_Z,
                screw_clearance_top_z_mm=SCREW_CLEARANCE_TOP,rear_mount_positions_preserved=True,
                core_overlap_mm3=core_collision,skin_overlap_mm3=skin_collision,
                native_support_guard_exclusion=support_guard,
                skin_core_interference_mm3=skin_core_collision,project_plates=records,
                limitations=['Skin closing gap and clamping behaviour require the physical coupon.',
                             'Three pads define seating; keep adhesive off them and the front seam lands.',
                             'All skins use the same rotation. Common face normal alone is insufficient.',
                             'No claim of invisible seams or mechanical load rating.',
                             'Core seam centers are offset; long seam segments can still meet a skin seam locally.'])
    save_json(OUT/'M-geometry-validation.json',report)
    assert sha(source_path())==original_hash
    print('M core / veneer projects written',flush=True)


def orient():
    """Fix all six original solid M poses without altering their mesh/paint bytes."""
    files=source(); poses=json.loads((ROOT/'working/geometry/hammered-M-assembly-poses.json').read_text())
    root=ET.fromstring(files['3D/3dmodel.model']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    for md in root.findall(tag('metadata')):
        if md.get('name')=='Title':md.text='M solid - six common-orientation A1 plates'
        elif md.get('name')=='Description':md.text='Original solid M meshes and support painting; all six orientations aligned to saved M5.'
    resources=root.find(tag('resources'));build=root.find(tag('build'))
    ids={p['object_id'] for p in poses.values()};needed=set();records=[]
    for o in list(resources):
        if o.get('id') not in ids:resources.remove(o)
    for b in list(build):
        if b.get('objectid') not in ids:build.remove(b)
    for q in list(cfg):
        if q.tag=='object' and q.get('id') in ids:continue
        if q.tag=='plate' and props(q).get('plater_id') in [str(i) for i in range(21,27)]:continue
        cfg.remove(q)
    for i,(name,p) in enumerate(sorted(poses.items())):
        obj=resources.find(f"{tag('object')}[@id='{p['object_id']}']")
        co=next(c for c in obj.find(tag('components')) if c.get('objectid')==p['part_id'])
        child=ET.fromstring(files[p['path']]);from colorize_print_project import read_mesh
        m=read_mesh(child.find(tag('resources')).find(f"{tag('object')}[@id='{p['part_id']}']"));m.apply_transform(np.array(p['assembly_from_mesh']))
        t=centered(m,common_m_rotation(),z=2.4); b=t@np.array(p['assembly_from_mesh'])@np.linalg.inv(transform(co.get('transform')))
        b[:2,3]+=[i%3*307.2,-(i//3)*307.2]
        build.find(f"{tag('item')}[@objectid='{p['object_id']}']").set('transform',' '.join(format(float(x),'.12g') for x in b[:3].T.reshape(-1)))
        plate=next(q for q in cfg.findall('plate') if props(q).get('plater_id')==str(i+21))
        for md in list(plate.findall('metadata')):
            if md.get('key','').endswith('_file'):plate.remove(md)
            elif md.get('key')=='plater_id':md.set('value',str(i+1))
            elif md.get('key')=='plater_name':md.set('value',f'{i+1} - {name} - common orientation with M5')
        needed.update(c.get('{'+P+'}path').lstrip('/') for c in obj.find(tag('components')))
        records.append(dict(name=name,plate=i+1,assembly_to_printer=t.tolist(),assembled_layer_direction_deg=90,source_mesh_and_support_paint_unchanged=True))
    ET.register_namespace('',tag('model')[1:].split('}')[0]);ET.register_namespace('p',P)
    rels=ET.Element('Relationships',xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
    for i,path in enumerate(sorted(needed)):
        ET.SubElement(rels,'Relationship',Target='/'+path,Id=f'rel-{i}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    keep={n:files[n] for n in ['[Content_Types].xml','_rels/.rels','Metadata/project_settings.config',*needed]}
    keep.update({'3D/3dmodel.model':ET.tostring(root,encoding='utf-8',xml_declaration=True),'Metadata/model_settings.config':ET.tostring(cfg,encoding='utf-8',xml_declaration=True),'3D/_rels/3dmodel.model.rels':ET.tostring(rels,encoding='utf-8',xml_declaration=True)})
    OUT.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUT/'M-Solid-Common-Orientation-A1.3mf','w',zipfile.ZIP_DEFLATED) as z:
        for n,v in keep.items():z.writestr(n,v)
    save_json(OUT/'M-solid-orientation.json',dict(source_sha256=sha(source_path()),records=records,native_slice_validated=False,physical_finish_matching_pending=True))
    print('Original solid M - all six aligned to M5',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','full','orient','cauls','glue-coupon','seam-coupon','fins','full-fins']);args=ap.parse_args()
    {'build':build,'full':lambda:build(include_samples=False),'orient':orient,'cauls':refresh_cauls,'glue-coupon':refresh_glue_coupon,'seam-coupon':refresh_seam_coupon,'fins':refresh_fins,'full-fins':lambda:refresh_fins(include_samples=False)}[args.action]()
