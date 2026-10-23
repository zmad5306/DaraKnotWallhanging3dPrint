"""Extend blue color modifiers downward by 0.40 mm; retain the finished face."""
import argparse
import collections
import copy
import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'.work/python-libs'), str(ROOT/'scripts')]
import numpy as np
import trimesh
from organize_root_projects import rows, compare, dump, sha, ASSET, clean_relations
from development_3mf import props, tag, transform, P
from colorize_print_project import read_mesh
from promote_veneer_wall_cradle import read, write
import correct_knot_reinforcement_skin as skin

WORK = ROOT/'.work/knot-blue-five-layers-r1'
REPORT = ROOT/'release/knot-blue-five-layers-r1'
BASE = WORK/'Knot-before.3mf'
EDIT = WORK/'Knot-editable.3mf'
FINAL = WORK/'Knot-final.3mf'
NATIVE = WORK/'native'
SOURCE_SHA = '8a76b70a1c1430d74a16ec06c9689827d33f3902afb1d7de90e4436072c251c3'


def protected():
    cat=json.loads((ROOT/'release/root-projects/catalog.json').read_text())
    blue={p['file'] for o in cat['Knot']['objects'] for p in o['parts'] if p['settings'].get('extruder')=='4'}
    paths=[p for p in ROOT.glob('*.3mf') if p.name!='Knot.3mf']
    paths+=list(ROOT.glob('*.scad'))+list(ROOT.glob('* STL/*.stl'))+list((ROOT/'release/samples').glob('*.3mf'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths if p.relative_to(ROOT).as_posix() not in blue}


def extend_bottom(mesh):
    """Add vertical side faces below the old bottom; preserve the original sides.

    F1 has intermediate Z vertices at existing body intersections. Stretching
    its bottom vertices would distort those faces, so extrude the bottom cap.
    """
    vertices=mesh.vertices.copy();faces=mesh.faces.copy();z=vertices[:,2]
    bottom=np.all(abs(z[faces]-z.min())<1e-8,axis=1)
    cap=faces[bottom];assert len(cap) and mesh.is_volume
    # Preserve the source cap's tiny coplanar triangulation slivers as well.
    assert np.dot(mesh.area_faces[bottom],mesh.face_normals[bottom,2])<0
    oriented=np.concatenate([cap[:,[0,1]],cap[:,[1,2]],cap[:,[2,0]]])
    counts=collections.Counter(tuple(sorted(e)) for e in oriented)
    edges=[(int(a),int(b)) for a,b in oriented if counts[tuple(sorted((a,b)))]==1]
    boundary=sorted({i for e in edges for i in e})
    mapping={i:len(vertices)+n for n,i in enumerate(boundary)}
    lower=vertices[boundary].copy();lower[:,2]-=.4
    for i in set(cap.flatten())-set(boundary):vertices[i,2]-=.4
    newcap=np.array([[mapping.get(int(i),int(i)) for i in f] for f in cap])
    side=np.array([f for a,b in edges for f in [(a,b,mapping[b]),(a,mapping[b],mapping[a])]])
    result=trimesh.Trimesh(np.vstack([vertices,lower]),np.vstack([faces[~bottom],newcap,side]),process=False)
    assert result.is_watertight and result.is_volume
    assert len(np.unique(result.faces))==len(result.vertices)
    assert np.array_equal(result.triangles[:sum(~bottom)],mesh.triangles[~bottom])
    assert abs(result.bounds[0,2]-(mesh.bounds[0,2]-.4))<1e-8
    return result


def build():
    assert sha(ROOT/'Knot.3mf')==SOURCE_SHA
    WORK.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    if not BASE.exists():
        shutil.copyfile(ROOT/'Knot.3mf',BASE)
        for name in ['AGENTS.md','release/root-projects/catalog.json','release/root-projects/gcode-sha256.json','release/root-projects/README.md']:
            target=WORK/'initial'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    assert sha(BASE)==SOURCE_SHA
    files=read(BASE);cfg=ET.fromstring(files['Metadata/model_settings.config']);model=ET.fromstring(files['3D/3dmodel.model'])
    changes=[]
    for obj in cfg.findall('object'):
        parent=model.find(tag('resources')).find(f"{tag('object')}[@id='{obj.get('id')}']")
        components={c.get('objectid'):c for c in parent.find(tag('components'))}
        blue=[p for p in obj.findall('part') if props(p).get('extruder')=='4'];assert len(blue)==1
        part=blue[0];assert part.get('subtype')=='modifier_part'
        co=components[part.get('id')];t=transform(co.get('transform'));assert np.array_equal(t[:3,:3],np.eye(3))
        asset=co.get('{'+P+'}path').lstrip('/');tree=ET.fromstring(files[asset])
        node=tree.find(tag('resources')).find(f"{tag('object')}[@id='{part.get('id')}']")
        mesh=read_mesh(node);old_bounds=mesh.bounds+t[:3,3]
        assert np.allclose(old_bounds[:,2],[12.9,13.5],atol=1e-6)
        assert all(len(f.attrib)==3 for f in node.find(tag('mesh')).find(tag('triangles')))
        new=extend_bottom(mesh)
        vertex_xml=''.join('<vertex x="%.12g" y="%.12g" z="%.12g"/>'%tuple(v) for v in new.vertices)
        face_xml=''.join('<triangle v1="%d" v2="%d" v3="%d"/>'%tuple(f) for f in new.faces)
        text=files[asset].decode();pattern=rf'(<object\b[^>]*\bid="{part.get("id")}"[^>]*>)(.*?)(</object>)'
        hit=re.search(pattern,text,re.S);assert hit
        body,count=re.subn(r'<mesh>.*?</mesh>',f'<mesh><vertices>{vertex_xml}</vertices><triangles>{face_xml}</triangles></mesh>',hit[2],flags=re.S);assert count==1
        files[asset]=(text[:hit.start(2)]+body+text[hit.end(2):]).encode()
        changes.append(dict(object=props(obj)['name'],asset=asset,volume_id=part.get('id'),old_z_mm=old_bounds[:,2].tolist(),new_z_mm=(new.bounds+t[:3,3])[:,2].tolist(),original_nonbottom_faces_preserved=True))
    assert len(changes)==10
    for name in list(files):
        if ASSET.fullmatch(name) or name in ['Metadata/slice_info.config','Metadata/filament_sequence.json']:del files[name]
    for plate in cfg.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key','').endswith('_file'):plate.remove(md)
    files['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
    clean_relations(files);write(EDIT,files)
    dump(REPORT/'provenance.json',dict(source='Knot.3mf',source_sha256=SOURCE_SHA,editable_sha256=sha(EDIT),changes=changes,protected_before=protected(),process_changes={},blue_depth_mm=[.6,1.0],blue_layers=[3,5],visible_xy_or_surface_height_changes=False))
    print('Extended ten blue modifiers downward by 0.40 mm; original side/top faces and all other meshes preserved.',flush=True)


def native(info=False):
    skin.WORK,skin.NATIVE,skin.FINAL,skin.EDIT=WORK,NATIVE,FINAL,EDIT
    skin.native(info)


def preserved_wall_coverage(before,after):
    """Check unchanged perimeters despite native seam placement/segmentation."""
    import shapely
    def collect(paths):
        groups=collections.defaultdict(collections.Counter)
        for slot,feature,ends in paths:
            if feature not in ['Outer wall','Inner wall']:continue
            z=ends[1][2]
            keep=slot==2 or (slot==1 and (z<12.59 or z>13.59)) or (slot==4 and z>13.19)
            if not keep:continue
            a,b=[tuple(round(v,3) for v in p[:2]) for p in ends]
            groups[(slot,round(z,3),feature)][(min(a,b),max(a,b))]+=1
        return groups
    a,b=collect(before),collect(after);assert a.keys()==b.keys();changes=[]
    for key in sorted(a):
        left,right=a[key]-b[key],b[key]-a[key]
        if not left and not right:continue
        distances=[]
        for delta,target in [(left,b[key]),(right,a[key])]:
            if not delta:continue
            # Compare against the complete corresponding wall, including
            # unchanged segments that can cover a moved segment endpoint.
            line=shapely.multilinestrings(np.array(list(delta)))
            samples=shapely.get_coordinates(shapely.segmentize(line,.01))
            other=shapely.multilinestrings(np.array(list(target)))
            distances.append(float(shapely.distance(shapely.points(samples),other).max()))
        # Distance to a fixed path is 1-Lipschitz. Half the sample interval
        # bounds an unsampled maximum anywhere along these straight segments.
        bound=max(distances,default=0)+.005
        assert bound<.05,(key,bound)
        changes.append(dict(filament_slot=key[0],z_mm=key[1],feature=key[2],old_changed_segments=sum(left.values()),new_changed_segments=sum(right.values()),max_centerline_difference_upper_bound_mm=bound))
    return changes


def validate():
    from mesh_sections import mesh_slice
    from validate_ribbon_bed_datum import segments
    from apply_knot_white_hilbert import path_signature
    from validate_print_project import scan_gcode
    from check_a2l_towers import check_startup_tower,check_tower
    from shapely.geometry import MultiPoint
    import shapely
    proof=json.loads((REPORT/'provenance.json').read_text());assert sha(BASE)==SOURCE_SHA and sha(EDIT)==proof['editable_sha256']
    assert protected()==proof['protected_before']
    old,edited,sliced=read(BASE),read(EDIT),read(NATIVE/'sliced.3mf')
    settings,oldrows=rows(BASE);s,newrows=rows(EDIT);assert s==settings
    assert old['3D/3dmodel.model']==edited['3D/3dmodel.model']
    assert old['Metadata/project_settings.config']==edited['Metadata/project_settings.config']
    cfg=ET.fromstring(old['Metadata/model_settings.config']);ecfg=ET.fromstring(edited['Metadata/model_settings.config'])
    assert [ET.tostring(o) for o in cfg.findall('object')]==[ET.tostring(o) for o in ecfg.findall('object')]
    for asset in {c['asset'] for c in proof['changes']}:
        pattern=r'<object\b[^>]*\bid="(\d+)"[^>]*>.*?</object>'
        a,b=[{m[1]:m[0] for m in re.finditer(pattern,f[asset].decode(),re.S)} for f in [old,edited]]
        blue={c['volume_id'] for c in proof['changes'] if c['asset']==asset}
        assert a.keys()==b.keys() and all(a[i]==b[i] for i in a.keys()-blue)
    locks=dict(sparse_infill_density='8%',sparse_infill_pattern='gyroid',layer_height='0.2',initial_layer_print_height='0.2',wall_loops='4',top_shell_layers='5',bottom_shell_layers='5',curr_bed_type='Textured PEI Plate',is_infill_first='1',support_top_z_distance='0.2',top_surface_pattern='monotonicline',top_surface_line_width='0.42')
    for k,v in locks.items():assert settings[k]==v
    assert settings['printer_model']=='Bambu Lab A2L' and settings['nozzle_diameter']==['0.4']
    assert 'Metadata/layer_config_ranges.xml' not in edited
    roundtrip=compare(EDIT,NATIVE/'sliced.3mf');assert not roundtrip['settings_changes']
    geometry=[]
    for a,b in zip(oldrows,newrows):
        assert a['settings']==b['settings'] and np.array_equal(a['transform'],b['transform'])
        for x,y in zip(a['parts'],b['parts']):
            assert x['settings']==y['settings'] and x['paint']==y['paint'] and x['subtype']==y['subtype']
            if x['settings'].get('extruder')!='4':
                assert np.array_equal(x['mesh'].vertices,y['mesh'].vertices) and np.array_equal(x['mesh'].faces,y['mesh'].faces)
                continue
            expected=extend_bottom(x['mesh']);assert np.array_equal(expected.faces,y['mesh'].faces)
            assert np.max(abs(expected.vertices-y['mesh'].vertices))<1e-8
            checks={}
            for z in [12.91,13.0,13.1,13.2,13.3,13.4,13.49]:
                error=mesh_slice(x['mesh'],z).symmetric_difference(mesh_slice(y['mesh'],z)).area
                assert error<1e-5
                checks[str(z)]=float(error)
            low=mesh_slice(x['mesh'],12.90001)
            for z in [12.51,12.6,12.7,12.8,12.89]:
                error=low.symmetric_difference(mesh_slice(y['mesh'],z)).area;assert error<.0001
            geometry.append(dict(plate=a['plate'],blue_bounds_mm=y['mesh'].bounds.tolist(),original_section_difference_mm2=checks,watertight=y['mesh'].is_watertight))
    dump(REPORT/'geometry.json',dict(blue_modifiers=geometry,all_other_meshes_byte_identical=True,all_settings_poses_and_support_paint_unchanged=True,native_roundtrip=roundtrip))
    sites=json.loads((ROOT/'release/knot-reinforcement-skin-r1/geometry.json').read_text())['modifiers']
    results=json.loads((NATIVE/'result.json').read_text());info=ET.fromstring(sliced['Metadata/slice_info.config'])
    records=[]
    for obj in newrows:
        n=obj['plate'];name=f'Metadata/plate_{n}.gcode';raw=sliced[name];text=raw.decode();oldtext=old[name].decode()
        assert hashlib.md5(raw).hexdigest().upper()==sliced[name+'.md5'].decode().strip().upper()
        gc=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.M))
        for k,v in locks.items():assert gc[k]==v
        assert gc['nozzle_diameter']=='0.4' and '; EXECUTABLE_BLOCK_END' in text
        scan=scan_gcode(text);assert scan['model_extrusion_z_by_filament_mm']['4']==[12.8,13.0,13.2,13.4,13.6]
        ps=segments(text,{1:'knot'},single_object=True)['knot'];prior=segments(oldtext,{1:'knot'},single_object=True)['knot']
        preserved={}
        wall_features=['Outer wall','Inner wall']
        for label,pred in [('brown_fill',lambda s,f,p:s==2 and f not in wall_features),('white_lower_infill',lambda s,f,p:s==1 and p[1][2]<12.59 and f not in wall_features),('white_and_blue_show_face_fill',lambda s,f,p:s in [1,4] and abs(p[1][2]-13.6)<.001 and f not in wall_features),('above_show_face_fill',lambda s,f,p:p[1][2]>13.61 and f not in wall_features)]:
            a,b=path_signature(prior,pred),path_signature(ps,pred);assert a==b,(n,label,a,b);preserved[label]=b
        seam_changes=preserved_wall_coverage(prior,ps)
        interface_fill={label:path_signature(paths,lambda s,f,p:s==1 and abs(p[1][2]-12.6)<.001) for label,paths in [('before',prior),('after',ps)]}
        t=obj['transform'];blue=next(p['mesh'].copy() for p in obj['parts'] if p['settings'].get('extruder')=='4');blue.apply_transform(t)
        blue_paths=[]
        for z in [12.8,13.0,13.2,13.4,13.6]:
            lines=np.array([p[2] for p in ps if p[0]==4 and abs(p[2][1][2]-z)<.001])[:,:,:2];assert len(lines)
            # The slicer quantizes the nominal 13.5 mm cap. Sample just inside
            # the mesh when that mid-plane coincides with its rounded top.
            region=mesh_slice(blue,min(z-.1,blue.bounds[1,2]-.00001))
            shapes=shapely.linestrings(lines)
            outside=float(shapely.length(shapely.difference(shapes,region.buffer(.03))).sum());assert outside<.01,(n,z,outside)
            blue_paths.append(dict(z_mm=z,segments=len(lines),centerline_outside_modifier_mm=outside))
        shell=[p for p in ps if 12.79<=p[2][1][2]<=13.61];continuity=[]
        for site in [p for p in sites if p['plate']==n]:
            center=(np.array([*site['xy_assembly_mm'],0])@t[:3,:3].T+t[:3,3])[:2]
            cross=skin.crossings(shell,center,site['radius_mm']);assert min(cross.values())>=5,(n,site['volume'],cross)
            continuity.append(dict(volume=site['volume'],cross_boundary_extrusion_segments=cross))
        lo,hi=np.array(scan['bead_xy_bounds_mm']);clearance=float(min(*lo,*(np.array([330,320])-hi)));assert clearance>.5
        hulls=[MultiPoint((p['mesh'].vertices@t[:3,:3].T+t[:3,3])[:,:2]).convex_hull for p in obj['parts'] if p['subtype']=='normal_part']
        top=max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values());startup=check_startup_tower(settings,hulls,3,top,n)
        tower=check_tower(text,hulls,[0,0,330,320]);tower.pop('actual_tower_convex_envelope')
        pi=next(p for p in info.findall('plate') if props(p)['index']==str(n));warnings=[w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings)
        estimate=next(p for p in results['sliced_plates'] if p['id']==n)
        records.append(dict(plate=n,gcode_sha256=hashlib.sha256(raw).hexdigest(),gcode_md5_verified=True,blue_layers=blue_paths,unchanged_extrusion_signatures=preserved,native_wall_seam_changes=seam_changes,white_z12_6_native_interface_fill=interface_fill,shell_continuity=continuity,model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],bed_clearance_mm=clearance,startup_tower=startup,tower=tower,warnings=warnings,seconds=estimate['total_predication'],grams=sum(f['total_used_g'] for f in estimate['filaments'])))
        dump(WORK/'progress.json',records);print(f'Plate {n}: five blue layers, unchanged show face/brown and continuous screw skin verified.',flush=True)
    final=dict(old)
    for asset in {c['asset'] for c in proof['changes']}:final[asset]=edited[asset]
    nc=ET.fromstring(sliced['Metadata/model_settings.config'])
    for x,y in zip(cfg.findall('plate'),nc.findall('plate')):
        for md in list(x.findall('metadata')):x.remove(md)
        for md in y.findall('metadata'):x.insert(0,copy.deepcopy(md))
        for md in x.find('model_instance').findall('metadata'):
            if md.get('key')=='identify_id':md.set('value',props(y.find('model_instance'))['identify_id'])
    final['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
    for name,data in sliced.items():
        if ASSET.fullmatch(name) or name in ['Metadata/slice_info.config','Metadata/filament_sequence.json']:final[name]=data
    write(FINAL,final);compare(EDIT,FINAL);native(True);assert protected()==proof['protected_before']
    dump(REPORT/'validation.json',dict(project='Knot.3mf',project_sha256=sha(FINAL),source_sha256=SOURCE_SHA,editable_sha256=sha(EDIT),native_project_sha256=sha(NATIVE/'sliced.3mf'),blue_layer_count=5,blue_depth_mm=1.0,blue_modifier_count=10,modifier_count=50,screw_modifiers_preserved_at_z12_4=True,all_five_top_shell_layers_cross_former_modifier_boundary=True,all_process_settings_and_poses_unchanged=True,white_show_face_and_brown_fill_paths_unchanged=True,preserved_wall_centerline_coverage_tolerance_mm=.05,plates=records,total_seconds=sum(r['seconds'] for r in records),total_grams=sum(r['grams'] for r in records),native_roundtrip=roundtrip,native_reopen=json.loads((WORK/'reopen/result.json').read_text()),protected_after=protected(),physical_sanding_and_finish_confirmation_pending=True,printer_job_sent=False))
    shutil.copyfile(NATIVE/'result.json',REPORT/'native-result.json');print('Validation passed.',flush=True)


def publish():
    report=json.loads((REPORT/'validation.json').read_text())
    assert sha(FINAL)==report['project_sha256'] and sha(ROOT/'Knot.3mf')==SOURCE_SHA
    assert protected()==report['protected_after']
    path=ROOT/'release/root-projects/catalog.json';cat=json.loads(path.read_text());entry=cat['Knot'];assert entry['sha256']==SOURCE_SHA
    _,objects=rows(FINAL)
    for rec,obj in zip(entry['objects'],objects):
        assert rec['name']==obj['name']
        for saved,part in zip(rec['parts'],obj['parts']):
            if part['settings'].get('extruder')!='4':assert sha(ROOT/saved['file'])==saved['sha256'];continue
            data=part['mesh'].export(file_type='stl');(ROOT/saved['file']).write_bytes(data)
            saved.update(sha256=hashlib.sha256(data).hexdigest(),bounds=part['mesh'].bounds.tolist(),faces=len(part['mesh'].faces))
    shutil.copyfile(FINAL,ROOT/'Knot.3mf');entry.update(sha256=sha(FINAL),validation='release/knot-blue-five-layers-r1/validation.json');dump(path,cat)
    path=ROOT/'release/root-projects/gcode-sha256.json';hashes=json.loads(path.read_text());hashes['Knot']={f"plate_{r['plate']}":r['gcode_sha256'] for r in report['plates']};dump(path,hashes)
    shutil.copyfile(REPORT/'native-result.json',ROOT/'release/root-projects/Knot-native.json')
    assert protected()==report['protected_after'];print('Published Knot and ten blue modifier STLs; CAD references retained.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build','slice','validate','publish']);args=parser.parse_args()
    if args.action=='slice':native()
    else:globals()[args.action]()
