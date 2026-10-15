"""Adapt Zach's successful hammered surface to an unchanged M2/M3 joint.

Stage a separate two-piece fit sample, slice it in Studio, then audit/publish.
The production project is never changed by this script.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from build_jointed_bambu_project import ROOT, P, R, IDENTITY, np, trimesh, read_array, model, mesh_object, meta, tag, uid
from tune_silk_project import read_zip, write_zip, sha, xml, props, setmeta
from validate_print_project import scan_gcode, transform, nearest_error, TOKEN
from prepare_copper_diagnostic_test import inspect_moves
from colorize_print_project import read_mesh
from add_blue_ribbon_edge import artwork, section, as_mesh
from mesh_sections import mesh_slice
from scipy.spatial import cKDTree
import shapely
import manifold3d

WORK = ROOT / '.work/tilted-hammered-joint'
REVIEW = ROOT / 'working/review/tilted-hammered'
REFERENCE = ROOT / 'reference/hammered-success/hammered_coupon_clean.3mf'
TARGET = ROOT / 'Dara-Hammered-Joint-Test.3mf'
TITLE = 'Hammered M2-M3 joint - tilted 55 degrees'
PITCH, DEPTH, CROWN, RES = 9., .55, 2.2, .5


def rotation(angle, axis=(0, 0, 1)):
    return trimesh.transformations.rotation_matrix(math.radians(angle), axis)


def boolean(meshes, operation):
    solids=[manifold3d.Manifold(manifold3d.Mesh64(np.array(m.vertices,dtype=np.float64,copy=True,order='C').reshape(-1,3),np.array(m.faces,dtype=np.uint64,copy=True,order='C').reshape(-1,3))) for m in meshes]
    assert all(s.status()==manifold3d.Error.NoError for s in solids), [s.status() for s in solids]
    result=solids[0]
    for solid in solids[1:]:
        result=(result+solid if operation=='union' else result-solid if operation=='difference' else result^solid)
    raw=result.to_mesh64()
    return trimesh.Trimesh(raw.vert_properties,raw.tri_verts,process=False)


def texture_field(outline):
    """Same nearest-center parabola, jitter and physical scale as the sample.

    A single global field crosses section seams. The rectangular sample's
    one-axis crown is generalized using distance to the real M boundary:
    it matches a 35 mm-wide strip and caps the rise at 2.2 mm on wider strokes.
    Relief is clamped to zero at edges to retain the entire structural body.
    """
    xmin, ymin, xmax, ymax = outline.bounds
    rng = np.random.RandomState(73)
    centers = []
    for row in range(-2, int(np.ceil((ymax-ymin)/(PITCH*.866)))+5):
        for col in range(-2, int(np.ceil((xmax-xmin)/PITCH))+5):
            centers.append([(col-.5)*PITCH+(row%2)*PITCH/2+xmin+rng.uniform(-PITCH*.28, PITCH*.28),
                            (row-.5)*PITCH*.866+ymin+rng.uniform(-PITCH*.28, PITCH*.28)])
    tree = cKDTree(centers)

    def evaluate(xy):
        edge = shapely.distance(shapely.points(xy), outline.boundary)
        t = np.clip(edge/17.5, 0, 1)
        crown = CROWN*(2*t-t*t)
        distance = tree.query(xy)[0]
        depression = DEPTH*(1-np.minimum(1, (distance/(PITCH*.55))**2))
        return np.maximum(0, crown-depression)
    return evaluate


def height_slab(evaluate, to_world):
    xs, ys = np.arange(-12, 30.001, RES), np.arange(-17, 13.001, RES)
    xx, yy = np.meshgrid(xs, ys)
    xy = np.column_stack([xx.ravel(), yy.ravel()])
    world = trimesh.transform_points(np.column_stack([xy, np.zeros(len(xy))]), to_world)
    zz = 10.5 + evaluate(world[:, :2])
    n, ny = len(xs), len(ys)
    vertices = np.column_stack([xy, zz]).tolist()
    faces = []
    for j in range(ny-1):
        for i in range(n-1):
            a = j*n+i
            faces.extend([[a, a+1, a+n+1], [a, a+n+1, a+n]])
    boundary = list(range(n)) + [j*n+n-1 for j in range(1, ny)] + [(ny-1)*n+i for i in range(n-2, -1, -1)] + [j*n for j in range(ny-2, 0, -1)]
    bottom = []
    for i in boundary:
        bottom.append(len(vertices)); vertices.append([*vertices[i][:2], 10.4])
    center = len(vertices); vertices.append([9, -2, 10.4])
    for j, v in enumerate(boundary):
        k = (j+1) % len(boundary)
        faces.extend([[bottom[j], bottom[k], boundary[k]], [bottom[j], boundary[k], v], [center, bottom[k], bottom[j]]])
    mesh = trimesh.Trimesh(vertices, faces, process=True)
    assert mesh.is_volume and mesh.body_count == 1
    return mesh


def stage():
    WORK.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    source = read_zip(REFERENCE)
    source_root = ET.fromstring(source['3D/3dmodel.model'])
    saved = transform(source_root.find(tag('build')).find(tag('item')).get('transform'))
    r = np.eye(4); r[:3, :3] = saved[:3, :3]
    assert abs(math.degrees(math.acos(r[2, 2]))-55) < 1e-5
    assert np.allclose(r[:3, :3].T @ r[:3, :3], np.eye(3), atol=1e-8)
    cad = (ROOT / 'working/Dara-Photo-Frame-A1-Jointed.scad').read_text()
    placements = read_array(cad, 'M_placements')
    joint = read_array(cad, 'M_joints')[0]
    local = rotation(-joint[3]); local[:3, 3] = -local[:3, :3] @ [*joint[2], 0]
    to_world = np.linalg.inv(local)
    evaluate = texture_field(artwork(cad, 'letter_outline'))
    slab = height_slab(evaluate, to_world)
    crop = trimesh.creation.box([42, 30, 30]); crop.apply_translation([9, -2, 10])
    bodies, before, checks = [], [], []
    for i in joint[:2]:
        original = trimesh.load_mesh(ROOT / f'working/stl/Dara-Photo-Frame-A1-Jointed/M{i+1}.stl')
        p = placements[i]
        original.apply_translation([*p[1], -p[3]])
        original.apply_transform(rotation(-p[0]))
        original.apply_transform(local)
        base = boolean([original, crop], 'intersection')
        top = mesh_slice(base, 10.49)
        prism = as_mesh(section(top).extrude(3).translate([0, 0, 10.4]))
        cap = boolean([slab, prism], 'intersection')
        textured = boolean([base, cap], 'union')
        assert textured.is_volume and textured.body_count == 1, (i, textured.is_watertight, textured.is_winding_consistent, textured.body_count, textured.volume)
        removed = boolean([base, textured], 'difference')
        added = boolean([textured, base], 'difference')
        assert abs(removed.volume) < .001
        lower = trimesh.creation.box([100, 100, 20.9998])
        preserved_added = boolean([added, lower], 'intersection')
        # Boolean evaluation can leave negligible numerical slivers.
        assert abs(preserved_added.volume) < 1e-5, (added.bounds, preserved_added.volume)
        errors = {str(z):mesh_slice(base,z).symmetric_difference(mesh_slice(textured,z)).area for z in [.1, 1., 3.25, 4.8, 4.95, 6.05, 8.7, 10.49]}
        assert max(errors.values()) < 1e-5, errors
        before.append(base); bodies.append(textured)
        textured.export(WORK / f'M{i+1}-joint-assembled.stl')
        checks.append(dict(part=f'M{i+1}', watertight=True, components=1, removed_original_material_mm3=float(removed.volume),
                           section_difference_mm2=errors, numerical_added_volume_below_face_mm3=float(preserved_added.volume),
                           bounds_in_joint_coordinates_mm=textured.bounds.tolist(), volume_mm3=float(textured.volume)))
    collision = boolean(bodies, 'intersection')
    assert abs(collision.volume) < .001
    # Both pieces share this one source slab, rather than independently seeded
    # or recentered crowns. Geometry cropping retains the existing seam gap.
    settings = json.loads(source['Metadata/project_settings.config'])
    settings.update(print_settings_id=TITLE, print_sequence='by layer', enable_prime_tower='0',
                    wall_loops='4', sparse_infill_pattern='gyroid', sparse_infill_density='15%')
    assert settings['enable_support'] == '1' and settings['support_type'] == 'tree(auto)'
    settings['enable_prime_tower'] = '0'
    files = {k:source[k] for k in ['[Content_Types].xml', '_rels/.rels']}
    root = model(); del root.attrib['xmlns:p']
    for key,value in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title',TITLE)]:
        ET.SubElement(root,tag('metadata'),name=key).text=value
    res = ET.SubElement(root,tag('resources')); build = ET.SubElement(root,tag('build'),attrib={'{'+P+'}UUID':uid()})
    config = ET.Element('config'); relations = ET.Element('Relationships',xmlns=R)
    centers = [(98,128),(158,128)]
    for k,(body,center) in enumerate(zip(bodies,centers),1):
        name=f'M{joint[k-1]+1} - actual joint crop'
        obj_id=k*1000; path=f'3D/Objects/Joint-{k}.model'
        child=model();mesh_object(ET.SubElement(child,tag('resources')),obj_id+1,body)
        files[path]=xml(child)
        obj=ET.SubElement(res,tag('object'),id=str(obj_id),type='model',attrib={'{'+P+'}UUID':uid()})
        ET.SubElement(ET.SubElement(obj,tag('components')),tag('component'),objectid=str(obj_id+1),transform=IDENTITY,
                      attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
        positioned=body.copy(); positioned.apply_transform(r)
        t=r.copy();t[:2,3]=np.array(center)-positioned.bounds.mean(axis=0)[:2];t[2,3]=-positioned.bounds[0,2]
        ET.SubElement(build,tag('item'),objectid=str(obj_id),printable='1',transform=' '.join(f'{x:.10g}' for x in t[:3,:].T.ravel()),attrib={'{'+P+'}UUID':uid()})
        c=ET.SubElement(config,'object',id=str(obj_id));meta(c,'name',name);meta(c,'extruder',1)
        part=ET.SubElement(c,'part',id=str(obj_id+1),subtype='normal_part');meta(part,'name',name)
        ET.SubElement(part,'mesh_stat',face_count=str(len(body.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        ET.SubElement(relations,'Relationship',Target='/'+path,Id=f'rel-{k}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        checks[k-1]['build_transform']=t.tolist()
    plate=ET.SubElement(config,'plate')
    for key,value in [('plater_id',1),('plater_name',TITLE),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 1 1 1'),('filament_volume_maps','0 0 0 0')]:meta(plate,key,value)
    for k in [1,2]:
        instance=ET.SubElement(plate,'model_instance')
        for key,value in [('object_id',k*1000),('instance_id',0),('identify_id',100+k)]:meta(instance,key,value)
    files.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(relations),
                  'Metadata/model_settings.config':xml(config),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
    write_zip(WORK/'staged.3mf',files)
    manifest=dict(source_sha256=sha(REFERENCE),preserved={name:sha(ROOT/name) for name in ['Dara.3mf','working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']},
                  source_rotation=r.tolist(),face_angle_degrees=55,joint=joint,crop_mm=[[-12,-17],[30,13]],
                  texture=dict(pitch_mm=PITCH,depth_mm=DEPTH,crown_maximum_rise_mm=CROWN,mesh_spacing_mm=RES,seed=73),
                  geometry_checks=checks,assembled_intersection_mm3=float(collision.volume),
                  limitations=['Joint fit, locator fit and support removal require physical inspection.',
                               'Pattern uses the successful formula at the same physical scale, extended continuously over the M.',
                               'Crown follows the actual M outline, with relief clamped at zero to preserve the original body.',
                               'This fit sample retains the successful saved process except four structural walls and 15% gyroid.'])
    (WORK/'manifest.json').write_text(json.dumps(manifest,indent=2))
    render(bodies)
    print(json.dumps(dict(staged=str(WORK/'staged.3mf'),checks=checks),indent=2))


def render(bodies):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(10,5),facecolor='#f4f1eb')
    for k,explode in enumerate([False,True]):
        ax=fig.add_subplot(1,2,k+1,projection='3d',facecolor='#f4f1eb')
        for i,body in enumerate(bodies):
            m=body.copy()
            if explode:m.apply_translation([(-6 if i==0 else 6),0,0])
            light=np.array([-.4,-.6,.7]); light/=np.linalg.norm(light)
            camera=np.array([math.cos(math.radians(45))*math.cos(math.radians(-60)),math.cos(math.radians(45))*math.sin(math.radians(-60)),math.sin(math.radians(45))])
            visible=m.face_normals@camera>1e-8
            shade=.5+.5*np.maximum(m.face_normals[visible]@light,0)
            colors=np.array([.82,.40,.16])[None,:]*shade[:,None]
            ax.add_collection3d(Poly3DCollection(m.triangles[visible],facecolors=colors,edgecolors='none',antialiaseds=False))
        ax.set_xlim(-19,37);ax.set_ylim(-20,16);ax.set_zlim(0,15);ax.set_box_aspect((56,36,15));ax.view_init(45,-60);ax.set_axis_off()
        ax.set_title('Assembled seam' if not explode else 'Separated: existing keyed lap',fontsize=12)
    fig.suptitle('Actual M2 / M3 geometry with a continuous hammered face',fontsize=15)
    fig.text(.5,.035,'42 x 30 mm assembly crop | original 10.5 mm body | up to 2.2 mm added relief\nGeometry preview; copper sheen is not simulated.',ha='center',fontsize=10)
    fig.subplots_adjust(left=0,right=1,top=.88,bottom=.13,wspace=0)
    fig.savefig(REVIEW/'joint-geometry.png',dpi=150);plt.close(fig)


def render_toolpaths(gcode, manifest):
    """Show real exported outer-wall and support moves, including fitted arcs."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    records,pauses=inspect_moves(gcode,[dict(label='plate',xy=[128,128])],(100,100))
    assert not pauses
    lines=gcode.splitlines();groups={k:[] for k in ['face','body','support']}
    inverses=[np.linalg.inv(np.array(c['build_transform'])) for c in manifest['geometry_checks']]
    support_back=[]
    for move in records['plate']:
        if move['feature'] not in ['Outer wall','Overhang wall','Top surface','Support','Support interface','Brim']:continue
        xy=np.array([move['start'],move['end']]);z=move['z']
        if move['command'] in ['G2','G3']:
            v={k:float(n) for k,n in TOKEN.findall(lines[move['line']])}
            center=xy[0]+[v.get('I',0),v.get('J',0)]
            radius=np.linalg.norm(xy[0]-center)
            a,b=[math.atan2(p[1]-center[1],p[0]-center[0]) for p in xy]
            ccw=move['command']=='G3';span=((b-a) if ccw else (a-b))%(2*math.pi)
            angles=np.linspace(a,a+(span if ccw else -span),max(3,math.ceil(radius*span/.15)))
            xy=center+radius*np.column_stack([np.cos(angles),np.sin(angles)])
        xyz=np.column_stack([xy,np.full(len(xy),z)])
        obj=0 if xy[:,0].mean()<128 else 1
        local=trimesh.transform_points(xyz,inverses[obj])
        kind='support' if move['feature'] in ['Support','Support interface','Brim'] else 'face' if local[:,2].mean()>10.25 else 'body'
        groups[kind].extend(np.stack([xyz[:-1],xyz[1:]],axis=1))
        if move['feature'].startswith('Support'):support_back.extend(local[:,2])
    # Existing support settings produce only a low foot on this crop, away
    # from the decorative surface. This is not a support audit of full parts.
    assert max(support_back)<10
    fig=plt.figure(figsize=(10,6),facecolor='#f4f1eb');ax=fig.add_subplot(111,projection='3d',facecolor='#f4f1eb')
    for kind,color,width in [('support','#77858e',.65),('body','#93603f',.35),('face','#ce662b',.65)]:
        ax.add_collection3d(Line3DCollection(groups[kind],colors=color,linewidths=width))
    ax.set_xlim(80,178);ax.set_ylim(90,165);ax.set_zlim(0,35);ax.set_box_aspect((98,75,35));ax.view_init(30,-35);ax.set_axis_off()
    fig.suptitle('Exported Bambu toolpaths: two real joint halves at 55 degrees',fontsize=14)
    fig.text(.5,.055,'Copper: decorative face and body  |  Gray: supports and brim\n0.2 mm layers, 4 walls, 15% gyroid. Actual paths; not a sheen prediction.',ha='center',fontsize=10)
    fig.subplots_adjust(left=0,right=1,top=.9,bottom=.12)
    fig.savefig(REVIEW/'joint-toolpaths.png',dpi=160);plt.close(fig)
    return dict(support_maximum_local_depth_axis_mm=float(max(support_back)),decorative_face_starts_at_local_z_mm=10.5)


def slice_project():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe');out=WORK/'slice';out.mkdir(exist_ok=True)
    with (WORK/'slice.log').open('w',encoding='utf-8') as log:
        r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/'staged.3mf')],
                         cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print(json.dumps(dict(return_code=r.returncode,log=str(WORK/'slice.log'))));r.check_returncode()


def publish():
    manifest=json.loads((WORK/'manifest.json').read_text())
    for name,digest in manifest['preserved'].items():assert sha(ROOT/name)==digest
    files=read_zip(WORK/'slice/sliced.3mf');cfg=ET.fromstring(files['Metadata/model_settings.config'])
    assert len(cfg.findall('object'))==2 and len(cfg.findall('plate'))==1
    settings=json.loads(files['Metadata/project_settings.config'])
    for k,v in dict(layer_height='.2',wall_loops='4',sparse_infill_pattern='gyroid',sparse_infill_density='15%',support_type='tree(auto)',support_on_build_plate_only='1',enable_support='1',ironing_type='no ironing').items():
        actual=settings[k];assert (float(actual)==float(v) if k=='layer_height' else actual==v),(k,actual)
    assert float(settings['filament_flow_ratio'][0])==.98
    # Compare the saved geometry in bed coordinates against the staged meshes;
    # Studio is allowed to recenter but not rescale or otherwise alter them.
    def placed(data):
        root=ET.fromstring(data['3D/3dmodel.model']);result=[]
        for item in root.find(tag('build')):
            obj=root.find(tag('resources')).find(f"{tag('object')}[@id='{item.get('objectid')}']")
            comp=obj.find(tag('components')).find(tag('component'))
            child=ET.fromstring(data[comp.get('{'+P+'}path').lstrip('/')])
            m=read_mesh(child.find(tag('resources')).find(f"{tag('object')}[@id='{comp.get('objectid')}']"))
            m.apply_transform(transform(item.get('transform'))@transform(comp.get('transform')));result.append(m)
        return sorted(result,key=lambda m:m.centroid[0])
    reference=placed(read_zip(WORK/'staged.3mf'));actual=placed(files)
    for a,b in zip(reference,actual):
        assert nearest_error(a.vertices,b.vertices)<1e-4 and nearest_error(b.vertices,a.vertices)<1e-4
        assert np.max(np.abs(a.bounds-b.bounds))<1e-4
    info=ET.fromstring(files['Metadata/slice_info.config']);plate=info.find('plate');setmeta(plate,'printer_model_id','N2S')
    for entry in list(plate.findall('metadata')):
        if entry.get('key')=='first_layer_time':
            n=float(entry.get('value'))
            if not math.isfinite(n) or not 0<=n<=float(props(plate)['prediction']):plate.remove(entry)
    files['Metadata/slice_info.config']=xml(info)
    audit=scan_gcode(files['Metadata/plate_1.gcode'].decode())
    assert audit['conservative_bed_edge_clearance_mm']>60
    assert audit['features'].get('Sparse infill',0)>0
    assert audit['features'].get('Support',0)>0
    assert set(audit['model_extrusion_z_by_filament_mm'])=={'1'}
    assert max(audit['model_extrusion_z_by_filament_mm']['1'])<40
    assert not audit['features'].get('Ironing',0)
    result=json.loads((WORK/'slice/result.json').read_text());assert result['return_code']==0
    support_check=render_toolpaths(files['Metadata/plate_1.gcode'].decode(),manifest)
    write_zip(TARGET,files)
    manifest.update(project=TARGET.name,project_sha256=sha(TARGET),toolpath_audit=audit,support_face_check=support_check,slice_metadata=props(plate),slicer_result=result)
    (REVIEW/'joint-test-validation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (REVIEW/'slicer-plate.png').write_bytes(files['Metadata/plate_1.png'])
    print(json.dumps(dict(project=str(TARGET),slice_metadata=props(plate),audit=audit),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['stage','slice','publish'])
    {'stage':stage,'slice':slice_project,'publish':publish}[parser.parse_args().command]()
