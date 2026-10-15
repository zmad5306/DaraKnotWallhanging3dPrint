"""Narrow the visible hammered seam, preserving Zach's saved support painting.

The upper edge of each part extends 0.025 mm into the existing 0.075 mm gap.
The extension tapers to zero at Z=6.7, above the hidden shoulder and keys.
Also trim 0.003 inches from the free ends of the lower shelf and both keys,
keeping the mating shoulder unchanged. The actual contact is unconfirmed.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from prepare_tilted_hammered_joint import (
    ROOT, P, np, trimesh, tag, read_zip, write_zip, sha, xml, props,
    setmeta, transform, read_mesh, mesh_slice, boolean, scan_gcode,
)
from shapely.geometry import LineString
import manifold3d

SOURCE = ROOT / 'Dara-Hammered-Joint-Test.3mf'
TARGET = ROOT / 'Dara-Hammered-Close-Seam-Test.3mf'
WORK = ROOT / '.work/hammered-close-seam'
REVIEW = ROOT / 'working/review/hammered-close-seam'
TITLE = 'Hammered joint - 0.025 mm face gap'
START_Z, FULL_Z, EXTENSION, BAND = 6.7, 10.5, .025, .5
SHELF_SHORTENING = .003*25.4
SHELF_END = 18.-SHELF_SHORTENING
KEY_END = 15.75-SHELF_SHORTENING


def mesh_entries(files):
    root = ET.fromstring(files['3D/3dmodel.model'])
    config = ET.fromstring(files['Metadata/model_settings.config'])
    for item in root.find(tag('build')):
        obj = root.find(tag('resources')).find(f"{tag('object')}[@id='{item.get('objectid')}']")
        comp = obj.find(tag('components')).find(tag('component'))
        path = comp.get('{'+P+'}path').lstrip('/')
        child = ET.fromstring(files[path])
        obj = child.find(tag('resources')).find(f"{tag('object')}[@id='{comp.get('objectid')}']")
        cfg = config.find(f"object[@id='{item.get('objectid')}']")
        part = props(cfg.find('part'))
        offset = np.array([float(part['source_offset_'+a]) for a in 'xyz'])
        yield dict(name=props(cfg)['name'], path=path, child=child, obj=obj,
                   offset=offset, config=cfg, item=item,
                   placed=transform(item.get('transform')) @ transform(comp.get('transform')))


def split_plane(vertices, faces, attributes, axis, value):
    """Subdivide triangles without changing geometry or uniform support paint."""
    cache = {}
    out_faces, out_attrs = [], []

    def point(a, b):
        da, db = vertices[a][axis]-value, vertices[b][axis]-value
        if abs(da) < 1e-10:
            return a
        if abs(db) < 1e-10:
            return b
        key = tuple(sorted((a, b)))
        if key not in cache:
            p = vertices[a]+(vertices[b]-vertices[a])*da/(da-db)
            p[axis] = value
            cache[key] = len(vertices)
            vertices.append(p)
        return cache[key]

    def clip(poly, side):
        result = []
        for a, b in zip(poly, poly[1:]+poly[:1]):
            ina = side*(vertices[a][axis]-value) >= -1e-10
            inb = side*(vertices[b][axis]-value) >= -1e-10
            if ina:
                result.append(a)
            if ina != inb:
                result.append(point(a,b))
        clean = []
        for i in result:
            if not clean or i != clean[-1]:
                clean.append(i)
        if len(clean)>1 and clean[0]==clean[-1]:
            clean.pop()
        return clean

    for face, attr in zip(faces, attributes):
        distances = [vertices[i][axis]-value for i in face]
        if min(distances)<-1e-10 and max(distances)>1e-10:
            polygons = [clip(face,side) for side in [-1,1]]
        else:
            polygons = [face]
        for poly in polygons:
            for j in range(1,len(poly)-1):
                tri = [poly[0],poly[j],poly[j+1]]
                # Keep very thin source facets: dropping them opens the shared
                # seam topology in Studio's serialized mesh.
                if len(set(tri))==3:
                    out_faces.append(tri)
                    out_attrs.append(attr.copy())
    return vertices,out_faces,out_attrs


def tip_cutters():
    cutters=[]
    for lower,upper in [([SHELF_END,-50,-1],[20,50,6.3]),
                        ([KEY_END,-50,4.8],[16,50,6.3])]:
        box=trimesh.creation.box(np.subtract(upper,lower))
        box.apply_translation((np.array(upper)+lower)/2)
        cutters.append(box)
    return cutters


def trim_hidden_tips(vertices,faces,attributes):
    """Propagate each source triangle's support paint through the tip cuts."""
    def solid(v,f,start):
        mesh=manifold3d.Mesh64(np.array(v,dtype=np.float64,copy=True,order='C'),
              np.array(f,dtype=np.uint64,copy=True,order='C'),
              face_id=np.arange(start,start+len(f),dtype=np.uint64))
        result=manifold3d.Manifold(mesh)
        assert result.status()==manifold3d.Error.NoError
        return result
    body=solid(vertices,faces,0)
    for i,cutter in enumerate(tip_cutters()):
        body=body-solid(cutter.vertices,cutter.faces,len(faces)+i*100)
    raw=body.to_mesh64()
    # IDs survive splitting, so the remaining user-painted regions retain
    # their exact labels. New vertical end faces do not need support paint.
    attrs=[attributes[int(i)].copy() if i<len(attributes) else {} for i in raw.face_id]
    return [v.copy() for v in raw.vert_properties],raw.tri_verts.tolist(),attrs


def stage():
    WORK.mkdir(parents=True,exist_ok=True)
    REVIEW.mkdir(parents=True,exist_ok=True)
    baseline = WORK/'user-supported-baseline.3mf'
    if not baseline.exists():
        baseline.write_bytes(SOURCE.read_bytes())
    assert sha(SOURCE)==sha(baseline), 'Saved source changed; review before rebuilding.'
    files = read_zip(baseline)
    settings = files['Metadata/project_settings.config']
    report = dict(source_sha256=sha(baseline), source=SOURCE.name,
                  extension_per_edge_mm=EXTENSION, target_face_gap_mm=.025,
                  lower_shelf_shortening_mm=SHELF_SHORTENING,
                  lower_shelf_shortening_inches=.003,
                  keys_same_end_shortening_mm=SHELF_SHORTENING,
                  cosmetic_extension_unchanged_below_z_mm=START_Z, full_extension_above_z_mm=FULL_Z,
                  settings_preserved_exactly=True, geometry=[],
                  preserved={p:sha(ROOT/p) for p in [SOURCE.name,'Dara.3mf',
                      'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']})
    meshes = []
    config = ET.fromstring(files['Metadata/model_settings.config'])
    for entry in mesh_entries(files):
        obj, offset = entry['obj'],entry['offset']
        original = read_mesh(obj)
        original.apply_translation(offset)
        attrs = [{k:v for k,v in t.attrib.items() if k not in ['v1','v2','v3']}
                 for t in obj.find(tag('mesh')).find(tag('triangles'))]
        # Whole-face paint can be inherited by each subdivided triangle.
        assert all(a.get('paint_supports') in [None,'4'] for a in attrs)
        original_painted_area = float(sum(original.area_faces[i] for i,a in enumerate(attrs) if a.get('paint_supports')))
        vertices = [v.copy() for v in original.vertices]
        faces = original.faces.tolist()
        sign = 1 if entry['name'].startswith('M2') else -1
        if sign==1:
            vertices,faces,attrs=trim_hidden_tips(vertices,faces,attrs)
        mechanical=trimesh.Trimesh(vertices,faces,process=False)
        assert mechanical.is_volume and mechanical.is_watertight
        removed_tip=boolean([original,mechanical],'difference')
        assert abs(boolean([mechanical,original],'difference').volume)<1e-6
        if sign==1:
            assert abs(mechanical.bounds[1,0]-SHELF_END)<1e-7
            outside=boolean([removed_tip,boolean(tip_cutters(),'union')],'difference')
            assert abs(outside.volume)<1e-6
            key_section=mesh_slice(mechanical,5.9)
            keys=[p for p in key_section.geoms if p.bounds[0]>2]
            assert len(keys)==2 and all(abs(p.bounds[2]-KEY_END)<1e-7 for p in keys)
        retained_paint_area=float(sum(mechanical.area_faces[i] for i,a in enumerate(attrs) if a.get('paint_supports')))
        for axis,value in [(2,START_Z),(2,FULL_Z),(0,-sign*(.0375+BAND))]:
            vertices,faces,attrs = split_plane(vertices,faces,attrs,axis,value)
        v = np.asarray(vertices)
        subdivided = trimesh.Trimesh(v.copy(),faces,process=False)
        assert subdivided.is_volume and subdivided.is_watertight
        paint_mask = np.array([bool(a.get('paint_supports')) for a in attrs])
        painted_area = float(subdivided.area_faces[paint_mask].sum())
        assert abs(retained_paint_area-painted_area)<1e-6
        weight = np.clip((v[:,2]-START_Z)/(FULL_Z-START_Z),0,1)
        weight *= np.clip(1-(np.abs(v[:,0])-.0375)/BAND,0,1)
        v[:,0] += sign*EXTENSION*weight
        updated = trimesh.Trimesh(v,faces,process=False)
        assert updated.is_volume and updated.is_watertight and updated.body_count==1
        lower_box = trimesh.creation.box([100,100,START_Z+1])
        lower_box.apply_translation([0,0,(START_Z-1)/2])
        old_lower = boolean([mechanical,lower_box],'intersection')
        new_lower = boolean([updated,lower_box],'intersection')
        removed = abs(boolean([old_lower,new_lower],'difference').volume)
        added = abs(boolean([new_lower,old_lower],'difference').volume)
        assert removed+added<1e-6, (removed,added)
        differences = {str(z):float(mesh_slice(mechanical,z).symmetric_difference(mesh_slice(updated,z)).area)
                       for z in [.1,1,3.25,4.8,4.95,5.6,6.05,6.5,6.69]}
        assert max(differences.values())<1e-7, differences
        meshes.append(updated)
        updated.export(WORK/(entry['name'].split(' - ')[0]+'.stl'))
        mesh_xml = obj.find(tag('mesh'))
        verts_xml = mesh_xml.find(tag('vertices'));verts_xml.clear()
        for xyz in v-offset:
            ET.SubElement(verts_xml,tag('vertex'),dict(zip('xyz',[f'{n:.12g}' for n in xyz])))
        triangles = mesh_xml.find(tag('triangles'));triangles.clear()
        for face,attr in zip(faces,attrs):
            ET.SubElement(triangles,tag('triangle'),dict(v1=str(face[0]),v2=str(face[1]),v3=str(face[2]),**attr))
        files[entry['path']] = xml(entry['child'])
        co = config.find(f"object[@id='{entry['config'].get('id')}']")
        co.find('metadata[@face_count]').set('face_count',str(len(faces)))
        co.find('part/mesh_stat').set('face_count',str(len(faces)))
        setmeta(co,'name',entry['name']+' - close seam')
        setmeta(co.find('part'),'name',entry['name']+' - close seam')
        report['geometry'].append(dict(name=entry['name'],triangles=len(faces),
            painted_triangles=int(paint_mask.sum()),original_painted_area_mm2=original_painted_area,
            retained_painted_area_after_tip_trim_mm2=retained_paint_area,
            preserved_painted_area_before_extension_mm2=painted_area,
            tip_material_removed_mm3=float(abs(removed_tip.volume)),
            lower_removed_mm3=removed,lower_added_mm3=added,lower_section_differences_mm2=differences,
            max_vertex_displacement_mm=float((EXTENSION*weight).max()),
            build_transform=entry['placed'].tolist()))
    collision = abs(boolean(meshes,'intersection').volume)
    assert collision<1e-7
    gaps=[]
    for z in [10.5,11,11.5,12]:
        for y in [-15,-10,-5,0,5,10]:
            segments=[mesh_slice(m,z).intersection(LineString([(-.3,y),(.3,y)])) for m in meshes]
            if all(not s.is_empty for s in segments):
                gap=float(segments[1].bounds[0]-segments[0].bounds[2])
                # Exclude dimple/crown sections where the face is below this Z.
                if gap<.04:
                    gaps.append(gap)
    assert len(gaps)>10 and all(abs(g-.025)<.0001 for g in gaps),gaps
    report.update(face_gap_range_mm=[min(gaps),max(gaps)],face_gap_checks=len(gaps),assembled_intersection_mm3=collision)
    plate=config.find('plate');setmeta(plate,'plater_name',TITLE)
    for md in list(plate.findall('metadata')):
        if md.get('key','').endswith('_file'):
            plate.remove(md)
    files['Metadata/model_settings.config']=xml(config)
    root=ET.fromstring(files['3D/3dmodel.model'])
    for md in root.findall(tag('metadata')):
        if md.get('name')=='Title':md.text=TITLE
    files['3D/3dmodel.model']=xml(root)
    for name in list(files):
        if name.startswith('Metadata/') and (name.endswith(('.gcode','.md5','.png','.jpg')) or name=='Metadata/plate_1.json'):
            del files[name]
    files['Metadata/slice_info.config']=b'<?xml version="1.0" encoding="UTF-8"?><config/>'
    assert files['Metadata/project_settings.config']==settings
    write_zip(WORK/'staged.3mf',files)
    (WORK/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


def slice_project():
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    out=WORK/'slice';out.mkdir(exist_ok=True)
    with (WORK/'slice.log').open('w',encoding='utf-8') as log:
        result=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/'staged.3mf')],
            cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print(json.dumps(dict(return_code=result.returncode,log=str(WORK/'slice.log'))))
    result.check_returncode()


def support_preview(files):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection,Poly3DCollection
    from prepare_copper_diagnostic_test import inspect_moves
    from validate_print_project import TOKEN
    gcode=files['Metadata/plate_1.gcode'].decode();lines=gcode.splitlines()
    moves,pauses=inspect_moves(gcode,[dict(label='plate',xy=[128,128])],(100,100))
    assert not pauses
    groups={'Support':[],'Support interface':[]}
    ranges={name:[] for name in groups}
    for move in moves['plate']:
        if move['feature'] not in groups:continue
        xy=np.array([move['start'],move['end']])
        if move['command'] in ['G2','G3']:
            values={k:float(n) for k,n in TOKEN.findall(lines[move['line']])}
            center=xy[0]+[values.get('I',0),values.get('J',0)]
            radius=float(np.linalg.norm(xy[0]-center))
            a,b=[math.atan2(p[1]-center[1],p[0]-center[0]) for p in xy]
            ccw=move['command']=='G3';span=((b-a) if ccw else (a-b))%(2*math.pi)
            if np.linalg.norm(xy[0]-xy[1])<1e-8:span=2*math.pi
            angles=np.linspace(a,a+(span if ccw else -span),max(3,math.ceil(radius*span/.2)))
            xy=center+radius*np.column_stack([np.cos(angles),np.sin(angles)])
        xyz=np.column_stack([xy,np.full(len(xy),move['z'])])
        groups[move['feature']].extend(np.stack([xyz[:-1],xyz[1:]],axis=1))
        ranges[move['feature']].append(move['z'])
    assert all(ranges.values()) and max(ranges['Support interface'])>20
    fig=plt.figure(figsize=(12,6),facecolor='#f4f1eb')
    for k,angle in enumerate([-60,120],1):
        ax=fig.add_subplot(1,2,k,projection='3d',facecolor='#f4f1eb')
        for entry in mesh_entries(files):
            m=read_mesh(entry['obj']);m.apply_transform(entry['placed'])
            light=np.maximum(0,m.face_normals@np.array([-.4,-.4,.82]))
            rgb=np.array([.8,.38,.16])*(.55+.45*light[:,None])
            ax.add_collection3d(Poly3DCollection(m.triangles,facecolors=rgb,edgecolors='none',linewidth=0))
        for name,color in [('Support','#667680'),('Support interface','#406c8e')]:
            ax.add_collection3d(Line3DCollection(groups[name],colors=color,linewidths=.35))
        ax.set_xlim(78,185);ax.set_ylim(100,160);ax.set_zlim(0,35)
        ax.set_box_aspect((107,60,35));ax.view_init(20,angle);ax.set_axis_off()
    fig.suptitle('Close-seam joint test: saved geometry and exported support paths',fontsize=14)
    fig.text(.5,.06,'Copper: actual part geometry | Gray/blue: generated trees and support interfaces\nUser-painted support regions retained. Geometry preview does not simulate silk reflections.',ha='center',fontsize=10)
    fig.subplots_adjust(left=0,right=1,top=.93,bottom=.1,wspace=0)
    fig.savefig(REVIEW/'supports.png',dpi=160);plt.close(fig)
    return {name:dict(min_z_mm=min(z),max_z_mm=max(z),extrusion_moves=len(z)) for name,z in ranges.items()}


def publish():
    manifest=json.loads((WORK/'manifest.json').read_text())
    for path,digest in manifest['preserved'].items():assert sha(ROOT/path)==digest
    staged=read_zip(WORK/'staged.3mf');files=read_zip(WORK/'slice/sliced.3mf')
    settings=json.loads(files['Metadata/project_settings.config'])
    expected=json.loads(staged['Metadata/project_settings.config'])
    differences={k:[expected.get(k),settings.get(k)] for k in set(expected)|set(settings) if expected.get(k)!=settings.get(k)}
    # CLI adds bookkeeping fields to a project saved by the GUI.
    assert all(k in ['different_settings_to_system','filament_map_2','inherits_group']
               and expected.get(k) is None for k in differences),differences
    manifest['slicer_added_bookkeeping']=differences
    from validate_print_project import nearest_error
    for before,after in zip(mesh_entries(staged),mesh_entries(files)):
        a,b=read_mesh(before['obj']),read_mesh(after['obj'])
        a.apply_transform(before['placed']);b.apply_transform(after['placed'])
        assert nearest_error(a.vertices,b.vertices)<1e-4 and nearest_error(b.vertices,a.vertices)<1e-4
        def paint_area(entry):
            mesh=read_mesh(entry['obj'])
            mask=[bool(t.get('paint_supports')) for t in entry['obj'].find(tag('mesh')).find(tag('triangles'))]
            return float(mesh.area_faces[mask].sum())
        assert abs(paint_area(before)-paint_area(after))<1e-4
    gcode=files['Metadata/plate_1.gcode'].decode();audit=scan_gcode(gcode)
    assert audit['conservative_bed_edge_clearance_mm']>50
    assert audit['features'].get('Sparse infill',0)>0 and audit['features'].get('Support',0)>0
    assert set(audit['model_extrusion_z_by_filament_mm'])=={'1'}
    assert not audit['features'].get('Ironing',0)
    info=ET.fromstring(files['Metadata/slice_info.config']);plate=info.find('plate');setmeta(plate,'printer_model_id','N2S')
    for md in list(plate.findall('metadata')):
        if md.get('key')=='first_layer_time':
            t=float(md.get('value'))
            if not math.isfinite(t) or not 0<=t<=float(props(plate)['prediction']):plate.remove(md)
    files['Metadata/slice_info.config']=xml(info)
    result=json.loads((WORK/'slice/result.json').read_text());assert result['return_code']==0
    write_zip(TARGET,files)
    manifest.update(project=TARGET.name,project_sha256=sha(TARGET),audit=audit,slice_metadata=props(plate),slicer_result=result,
                    support_toolpath_ranges=support_preview(files))
    (REVIEW/'validation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(project=str(TARGET),slice_metadata=props(plate),support_toolpath_ranges=manifest['support_toolpath_ranges']),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['stage','slice','publish'])
    {'stage':stage,'slice':slice_project,'publish':publish}[parser.parse_args().command]()
