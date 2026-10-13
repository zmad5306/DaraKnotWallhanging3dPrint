"""Stage every regenerated normal mesh and both surface colors for clean edges."""
import json,re,shutil,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from validate_print_project import ROOT,CAD,STLS,digest,props,transform,nearest_error
from build_jointed_bambu_project import tag,P,xml,mesh_object,read_array
from add_weave_test_coupon import read_zip,write_zip,NAME
from add_blue_ribbon_edge import artwork,section,as_mesh,in_print_coordinates,coupon_shape,plot,GAP,WIDTH,BOTTOM,TOP
from refresh_curve_project import solid
from restore_weave_project import refresh_preview_cache,crop_weave,CHECKS
from export_jointed_stls import verify
from colorize_print_project import weave_modifier
from shapely.geometry import Point
from shapely import union_all,affinity,make_valid
from rebuild_clean_partitions import partition_shapes
from mesh_sections import mesh_slice,mesh_cross_section
import numpy as np
import trimesh

WORK=ROOT/'.work/edge-quality'
REVIEW=ROOT/'working/review/clean-edges'

def verify_geometry():
    cache_path=REVIEW/'geometry-verification.json'
    cache_key=lambda:dict(cad=digest(CAD),baseline=digest(WORK/'baseline.scad'),script=digest(ROOT/'scripts/refresh_clean_project.py'),
                         mesh_sections=digest(ROOT/'scripts/mesh_sections.py'),stls={p.name:digest(p) for p in STLS.glob('*.stl')})
    if cache_path.exists():
        cached=json.loads(cache_path.read_text())
        if cached.get('verified_inputs')==cache_key():
            print('Reusing complete geometry proof for identical source, meshes and audit code.',flush=True)
            return cached
    oldcad=(WORK/'baseline.scad').read_text();cad=CAD.read_text()
    strip=lambda t:re.sub(r'module (?:knot_outline|fabric_outline|photo_loop_\d+|preview_frame_\d+|frame_mask_\d+|frame_joint_domain_\d+)\(\) \{.*?\n\}', '', t,flags=re.S)
    # Outline-derived clipping polygons also change. Tested profiles, seam
    # transforms, keys, mounting features and all native CSG code stay exact.
    clean=lambda t:'\n'.join(l for l in strip(t).splitlines() if not l.startswith('// Clean frame outlines:') and not l.startswith('// Sampled chord error'))
    assert clean(oldcad)==clean(cad)
    masks,domains,partition_proof=partition_shapes(cad)
    for prefix,shapes in [('frame_mask',masks),('frame_joint_domain',domains)]:
        for i,expected in enumerate(shapes):
            actual=affinity.scale(artwork(cad,f'{prefix}_{i}'),1/.75,1/.75,origin=(0,0))
            assert actual.symmetric_difference(expected).area<.001,(prefix,i)
    old,new=[artwork(t,'knot_outline') for t in [oldcad,cad]]
    changes=[old.symmetric_difference(new)]
    partition_changes=[]
    for prefix,count in [('frame_mask',20),('frame_joint_domain',31)]:
        for i in range(count):
            a,b=[affinity.scale(artwork(t,f'{prefix}_{i}'),1/.75,1/.75,origin=(0,0)) for t in [oldcad,cad]]
            partition_changes.append(a.symmetric_difference(b))
    # Recomputed trim endpoints and the old four-decimal seam vertices can
    # change tiny strips beyond the artwork delta. The derived polygons above
    # are independently checked; include their exact differences explicitly.
    changes.extend(partition_changes)
    for module,offset in [('fabric_outline',.1125)]+[(f'photo_loop_{i}',4) for i in range(1,9)]:
        a,b=[artwork(t,module).buffer(offset,join_style=2) for t in [oldcad,cad]]
        changes.append(a.symmetric_difference(b))
    # OpenSCAD offset(delta=...) has miter joins; a circular buffer around
    # the old boundary difference does not cover the pocket's corner offsets.
    # Buffer each difference separately. Buffering their large combined
    # MultiPolygon can produce nested shells and incorrectly punch holes in
    # an allowed change (observed near F14's curved lap endpoint).
    changed=union_all(changes)
    allowed=union_all([make_valid(c.buffer(.03)) for c in changes]+[changed])
    assert allowed.is_valid
    assert changed.difference(allowed).area<1e-7
    placements=read_array(cad,'frame_placements')
    manifest=json.loads((STLS/'manifest.json').read_text());records=[];unchanged=[]
    def verify_record(r):
        name=r['part'];path=STLS/r['file']
        a,b=[trimesh.load_mesh(p) for p in [WORK/'baseline-stls'/r['file'],path]]
        sa,sb=solid(a),solid(b);delta=(sa-sb)+(sb-sa);vol=delta.volume()
        proof=dict(part=name,symmetric_difference_mm3=vol,watertight=bool(b.is_volume))
        if r['family'] not in ['frame','backer']:
            assert vol<.001 and nearest_error(a.vertices,b.vertices)<.0001,name
            shutil.copy2(WORK/'baseline-stls'/r['file'],path);r.update(verify(path));unchanged.append(name)
            proof['byte_identical_to_prior']=True
        elif r['family']=='frame':
            local=in_print_coordinates(allowed,placements[int(name[1:])-1])
            outside=(delta-section(local).extrude(30).translate([0,0,-1])).volume()
            # Coplanar regrouping in Manifold can create spurious wedges in
            # the Boolean delta. Check the actual STL triangle intersections
            # in every vertical interval where either mesh changes topology.
            zs=np.unique(np.round(np.r_[a.vertices[:,2],b.vertices[:,2]],4))
            heights=(zs[:-1]+zs[1:])/2;raw_max=0.
            for height in heights:
                da=mesh_slice(a,height);db=mesh_slice(b,height)
                unexpected=da.symmetric_difference(db,grid_size=.000001).buffer(0).difference(local,grid_size=.000001)
                raw_max=max(raw_max,unexpected.area)
                # One micron accommodates long oblique STL facets and the
                # preceding four-decimal clipping polygons. It is smaller
                # than the canonical 0.002 mm chord tolerance.
                assert unexpected.buffer(-.001).area<1e-7,(name,height,unexpected.area)
            assert np.allclose(a.bounds[:,2],b.bounds[:,2],atol=.0001)
            proof.update(boolean_delta_outside_allowed_regions_mm3=outside,
                         verification='Original STL triangle-plane contours in every distinct vertex-height interval; reject changes wider than 0.002 mm outside derived regions.',
                         cross_sections_checked=len(heights),max_roundoff_area_outside_allowed_regions_mm2=raw_max,thickness_unchanged=True)
        else:
            assert np.allclose(a.bounds[:,2],b.bounds[:,2],atol=.0001)
            proof['thickness_unchanged']=True
        records.append(proof);print(name,'solid comparison',round(vol,5),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(verify_record,manifest['parts']))
    records.sort(key=lambda record:[r['part'] for r in manifest['parts']].index(record['part']))
    unchanged.sort(key=lambda name:[r['part'] for r in manifest['parts']].index(name))
    assert len(unchanged)==11
    (STLS/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    refresh_preview_cache()
    partition_proof['source_cad_sha256']=digest(CAD)
    (REVIEW/'partition-rebuild.json').write_text(json.dumps(partition_proof,indent=2)+'\n')
    rebuild=json.loads((REVIEW/'cad-rebuild.json').read_text())
    rebuild['source_cad_sha256']=digest(CAD)
    for r in rebuild['files']:r['sha256']=digest(ROOT/r['file'])
    (REVIEW/'cad-rebuild.json').write_text(json.dumps(rebuild,indent=2)+'\n')
    proof=dict(source_cad_sha256=digest(CAD),native_feature_code_unchanged=True,outline_derived_partition_polygons_rebuilt=True,unchanged_stl_files=unchanged,
               changed_stl_files=[r['part'] for r in manifest['parts'] if r['part'] not in unchanged],parts=records)
    proof['verified_inputs']=cache_key()
    (REVIEW/'geometry-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof

def main():
    geometry=verify_geometry();coupon=crop_weave(CAD.read_text())
    source=WORK/'baseline.3mf';base=json.loads((WORK/'baseline.json').read_text());assert digest(source)==base['project_sha256']
    files=read_zip(source);root=ET.fromstring(files['3D/3dmodel.model']);config=ET.fromstring(files['Metadata/model_settings.config'])
    objects={o.get('id'):o for o in root.find(tag('resources'))}
    children={n:ET.fromstring(d) for n,d in files.items() if n.startswith('3D/Objects/') and n.endswith('.model')}
    builds={}
    for item in root.find(tag('build')):
        builds.setdefault(item.get('objectid'),transform(item.get('transform')))
    source_positions={}
    for pi,layout in enumerate(base['plate_layout']):
        for item in layout['items']:
            source_positions.setdefault(item['name'],np.array([item['xy'][0]+(pi%6)*307.2,
                                                               item['xy'][1]-(pi//6)*307.2,0.]))
    cad=CAD.read_text();placements=read_array(cad,'frame_placements');knot=artwork(cad,'knot_outline')
    fabric=artwork(cad,'fabric_outline').buffer(.1125,quad_segs=16)
    blue=(fabric.buffer(GAP+WIDTH,quad_segs=16)-fabric.buffer(GAP,quad_segs=16)).intersection(knot).simplify(.001,preserve_topology=True)
    blue_records=[];wood_records=[];meshes={}
    for obj in config.findall('object'):
        name=props(obj)['name'];path=(CHECKS if name.startswith('Test-') else STLS)/(name+'.stl')
        mesh=trimesh.load_mesh(path);meshes[name]=mesh;replacements={0:mesh}
        if re.fullmatch(r'F\d+',name) or name==NAME:
            body=solid(mesh);local=coupon_shape(blue,cad) if name==NAME else in_print_coordinates(blue,placements[int(name[1:])-1])
            expected=section(local)^mesh_cross_section(mesh,(BOTTOM+TOP)/2)
            for z in (BOTTOM+.001,TOP-.001):assert (expected-mesh_cross_section(mesh,z).offset(.0001)).area()<.02
            bm=as_mesh(expected.extrude(TOP-BOTTOM).translate([0,0,BOTTOM]));wood,proof=weave_modifier(mesh)
            replacements.update({2:wood,4:bm});wood_records.append(dict(part=name,**proof))
            blue_records.append(dict(part=name,area_mm2=expected.area(),volume_mm3=bm.volume,source_stl_sha256=digest(path),z_mm=[BOTTOM,TOP],
                                     triangles=len(bm.faces),connected_regions=len(bm.split()),printable_geometry_unchanged=False))
        comps={c.get('objectid'):c for c in objects[obj.get('id')].find(tag('components'))}
        for part in obj.findall('part'):
            slot=0 if part.get('subtype')=='normal_part' else int(props(part).get('extruder',0))
            if part.get('subtype')!='normal_part' and slot==0:continue
            if slot not in replacements:continue
            comp=comps[part.get('id')];res=children[comp.get('{'+P+'}path').lstrip('/')].find(tag('resources'))
            # Bambu recenters some objects (especially asymmetrical backers)
            # and carries that offset in the build transform. Invert the
            # entire transform chain, not just the child component transform.
            world=builds[obj.get('id')]@transform(comp.get('transform'))
            target=np.eye(4);target[:3,3]=source_positions[name]
            m=replacements[slot].copy();m.apply_transform(np.linalg.inv(world)@target)
            check=m.copy();check.apply_transform(world);check.apply_translation(-source_positions[name])
            assert np.max(np.abs(check.vertices-replacements[slot].vertices))<1e-8
            res.remove(next(o for o in res if o.get('id')==part.get('id')));mesh_object(res,part.get('id'),m)
            part.find('mesh_stat').set('face_count',str(len(m.faces)))
        print(name,'project geometry refreshed',flush=True)
    assert len(blue_records)==len(wood_records)==21
    for plate in config.findall('plate'):
        for md in list(plate.findall('metadata')):
            if md.get('key','').endswith('_file'):plate.remove(md)
    files={n:d for n,d in files.items() if not n.startswith('Metadata/') or n in ['Metadata/model_settings.config','Metadata/project_settings.config']}
    files['Metadata/model_settings.config']=xml(config)
    for n,child in children.items():files[n]=xml(child)
    output=WORK/'clean-edges.3mf';write_zip(output,files)
    manifest=json.loads((STLS/'manifest.json').read_text())
    for part in base['parts']:
        entry=next(r for r in manifest['parts'] if r['part']==part.get('part',part.get('name')))
        for k in ('triangles','bounds_mm','size_mm','volume_mm3'):
            if k in part:part[k]=entry[k]
        part['file_sha256']=entry['sha256']
    for layout in base['plate_layout']:
        for item in layout['items']:item['bounds']=(meshes[item['name']].bounds+[ *item['xy'],0]).tolist()
    for r in base['test_plate']['parts']:
        if r['name']==NAME:r.update(sha256=digest(CHECKS/(NAME+'.stl')),triangles=len(coupon.faces),source_stl_sha256=digest(STLS/'F7.stl'),dimensions_mm=coupon.extents.tolist())
    base['test_plate'].update(source_cad_sha256=digest(CAD),sliced=False,plate_layouts=base['plate_layout'][29:])
    base['weave_restoration']['surface_masks']=wood_records
    base['blue_ribbon_edge'].update(source_cad_sha256=digest(CAD),masks=blue_records,physical_geometry_unchanged=False,digital_checks_passed=False,
                                    clean_edges='working/review/clean-edges/cad-rebuild.json')
    base['clean_edges']=dict(prior_project_sha256=digest(source),source_cad_sha256=digest(CAD),boundary_loops=26,primitives=320,
                            geometry_verification='working/review/clean-edges/geometry-verification.json',physical_tested=False,
                            unchanged_stl_files=geometry['unchanged_stl_files'])
    base['curve_repair']['superseded_by']='clean_edges'
    base['project_sha256']=digest(output)
    for k in ('bambu_studio_slice','bambu_studio_round_trip','bambu_studio_slice_warnings'):base.pop(k,None)
    (WORK/'staged.json').write_text(json.dumps(base,indent=2)+'\n');plot(cad,blue,REVIEW/'assembly-color-map.png')
    print(output,flush=True)

if __name__=='__main__':main()
