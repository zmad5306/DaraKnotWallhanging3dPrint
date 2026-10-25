"""Promote the user-accepted r3 solid laps to all 14 production Knot joints.

Existing mesh entries, settings and poses are immutable. New local masks use
the male lap's actual projected outline, X0..18, at both mating pieces. No
model stock is added. Native slices and adjacent mask CAD/STL are synchronized.
"""
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'.work/python-libs')]
import numpy as np
import manifold3d as mf
import shapely
from shapely.geometry import box,Point,Polygon,MultiPoint,LineString,mapping,shape
from development_3mf import solid,mesh,mesh_xml,model,tag,xml,meta,uid,P,R,IDENTITY
from develop_cosmetic_joints import cross_section
from develop_m_veneer import locate
from build_a2l_project import prism
from organize_root_projects import rows,compare,BOOKKEEPING,grid,pitch
from remove_unused_project_filaments import read,write,digest,props,ASSET,EXE
import audit_knot_rollback_joints as joints
from audit_knot_rollback_joints import paths_with_width,local
from correct_knot_reinforcement_skin import crossings
from check_a2l_towers import check_startup_tower,check_tower
from validate_print_project import scan_gcode
from build_photo_support_test import paths as all_extrusions
from revert_knot_infill_first import LOCKS

WORK=ROOT/'.work/knot-solid-laps-r1'
REPORT=ROOT/'release/knot-solid-laps-r1'
BASE=WORK/'before.3mf'
EDIT=WORK/'editable.3mf'
FINAL=WORK/'final.3mf'
SOURCE_SHA='aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46'
SAMPLE=ROOT/'output/Dara-A2L-Joint-Solid-Laps-r3/Dara-A2L-Joint-Solid-Laps-r3.3mf'
SAMPLE_SHA='6898ed006c82b81beafe6a90012c3e59d23e4124a75daf22d50db93e8a2a447c'
PLAN=ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json'
OVERRIDE={'sparse_infill_density':'100%','sparse_infill_pattern':'zig-zag'}
PREFIX='100% solid lap - J'
joints.WORK,joints.REPORT=WORK,REPORT


def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')


def sha(data):return hashlib.sha256(data).hexdigest()
def effective(s):return {k:v for k,v in s.items() if k not in BOOKKEEPING}


def protected():
    paths=[p for p in ROOT.glob('*.3mf') if p.name!='Knot.3mf']
    paths += [p for p in ROOT.glob('*.scad') if p.name!='Knot.scad']
    paths += [p for p in ROOT.glob('* STL/*.stl') if p.parent.name!='Knot STL']
    paths += list((ROOT/'release/samples').glob('*.3mf'))+[SAMPLE]
    return {p.relative_to(ROOT).as_posix():digest(p) for p in paths}


def project_polygon(body):
    result=Polygon()
    for ring in body.project().to_polygons():
        p=Polygon(ring)
        if p.is_valid and p.area>1e-10:result=result.symmetric_difference(p)
    return result


def compare_original(path):
    sa,aa=rows(BASE);sb,bb=rows(path);proof=json.loads((REPORT/'provenance.json').read_text())
    assert sa==sb and len(aa)==len(bb)==10
    results=[]
    for k,(a,b) in enumerate(zip(aa,bb)):
        assert a['name']==b['name'] and a['settings']==b['settings']
        pose_error=float(np.max(abs(a['transform']-b['transform'])));assert pose_error<.0001
        added=[r for r in proof['modifiers'] if r['object_index']==k]
        assert len(b['parts'])==len(a['parts'])+len(added)
        errors=[]
        for p,q in zip(a['parts'],b['parts']):
            assert p['subtype']==q['subtype'] and p['paint']==q['paint']
            assert effective(p['settings'])==effective(q['settings'])
            assert p['settings'].get('name')==q['settings'].get('name')
            assert np.array_equal(p['mesh'].faces,q['mesh'].faces)
            error=float(np.max(abs(p['mesh'].vertices-q['mesh'].vertices)));assert error<.0001
            errors.append(error)
        for part,expected in zip(b['parts'][len(a['parts']):],added):
            assert part['settings']['name']==expected['name'] and part['subtype']=='modifier_part'
            assert effective(part['settings'])==OVERRIDE and not part['paint']
            mask=solid(part['mesh']);target=prism(shape(expected['assembly_footprint']),0,13.5)
            error=abs((mask-target).volume())+abs((target-mask).volume());assert error<.06,(k,error)
            assert np.allclose(part['mesh'].bounds[:,2],[0,13.5],atol=.0001)
        results.append(dict(plate=k+1,original_volumes=len(a['parts']),added_modifiers=len(added),
            max_mesh_error_mm=max(errors),max_pose_error_mm=pose_error,paint_and_original_settings_preserved=True))
    return results


def build():
    source=ROOT/'Knot.3mf';assert digest(source)==SOURCE_SHA and digest(SAMPLE)==SAMPLE_SHA
    WORK.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    if not BASE.exists():shutil.copyfile(source,BASE)
    assert digest(BASE)==SOURCE_SHA
    settings,objects=rows(BASE);original=read(BASE);files=dict(original)
    cfg=ET.fromstring(files['Metadata/model_settings.config']);root=ET.fromstring(files['3D/3dmodel.model'])
    rels=ET.fromstring(files['3D/_rels/3dmodel.model.rels'])
    bodies=[mf.Manifold.batch_boolean([solid(p['mesh']) for p in o['parts'] if p['subtype']=='normal_part'],mf.OpType.Add) for o in objects]
    outlines=[project_polygon(b) for b in bodies]
    plan=json.loads(PLAN.read_text());records=[];features=[]
    for ji,j in enumerate(plan['frame_joints'],1):
        envelope=locate(box(0,-j[4]/2-20,18,j[4]/2+20),j)
        # The historical extrusion width is j[4]+40. Limit it further to the
        # actual tongue silhouette, excluding unrelated full-height stock in
        # the female object's nearby outline. The accepted crop lies inside it.
        exact_footprint=envelope.intersection(outlines[j[0]])
        # Collapse sub-micron projection slivers only in the new settings mask.
        # Native STL/3MF roundtrips otherwise create degenerate mask triangles;
        # all existing printable geometry remains byte-identical.
        footprint=exact_footprint.simplify(.00005,preserve_topology=True).intersection(envelope)
        mask_outline_error=exact_footprint.hausdorff_distance(footprint)
        assert mask_outline_error<.0001
        assert footprint.is_valid and footprint.area>1000
        high=cross_section(bodies[j[0]],8).intersection(footprint).area
        assert high<.01,(ji,'Mask would reach full-height male body',high)
        for z in [.1,1,2.5,4,4.6,5.1,5.9]:
            intended=cross_section(bodies[j[0]],z).intersection(envelope)
            assert intended.difference(footprint.buffer(.0001)).area<.001
        if ji==3:
            sample_settings,sample_objects=rows(SAMPLE)
            crop=locate(box(-14,-38,66,38),j)
            for o in sample_objects:
                ps=[p for p in o['parts'] if p['settings'].get('name','').startswith('100% solid')]
                assert len(ps)==1 and effective(ps[0]['settings'])==OVERRIDE
                actual=cross_section(solid(ps[0]['mesh']),2.5)
                assert footprint.intersection(crop).symmetric_difference(actual).area<.01
        m=mesh(prism(footprint,0,13.5))
        features.append(dict(joint=ji,male_plate=j[0]+1,female_plate=j[1]+1,
            actual_lap_outline_area_mm2=footprint.area,local_bounds=list(local(footprint,j).bounds),
            mask_outline_tolerance_mm=mask_outline_error,
            unrelated_male_stock_area_mm2=high,geometry_source='Existing male lap projected from unchanged production triangles'))
        for side,oi in enumerate(j[:2]):
            obj=cfg.find(f"object[@id='{objects[oi]['id']}']");pid=10000+len(records)
            name=f'{PREFIX}{ji} - '+('LOWER' if side==0 else 'UPPER')
            path=f'3D/Objects/solid_lap_j{ji}_{side}.model'
            child=model();res=ET.SubElement(child,tag('resources'));mesh_xml(res,pid,m);files[path]=xml(child)
            top=root.find(tag('resources')).find(f"{tag('object')}[@id='{obj.get('id')}']")
            ET.SubElement(top.find(tag('components')),tag('component'),objectid=str(pid),transform=IDENTITY,
                attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
            part=ET.SubElement(obj,'part',id=str(pid),subtype='modifier_part')
            meta(part,'name',name)
            for key,value in OVERRIDE.items():meta(part,key,value)
            ET.SubElement(part,'mesh_stat',face_count=str(len(m.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
            ET.SubElement(rels,'{'+R+'}Relationship',Target='/'+path,Id=f'rel-solid-lap-{ji}-{side}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
            distances=[]
            for p in objects[oi]['parts']:
                if p['settings'].get('name')=='Local solid screw reinforcement':
                    b=p['mesh'].bounds;c=b[:,:2].mean(axis=0);radius=np.ptp(b[:,0])/2
                    overlap=Point(c).buffer(radius).intersection(footprint).area
                    assert overlap<.001,(ji,oi,'Lap intersects capped screw bolster',overlap)
                    distances.append(Point(c).buffer(radius).distance(footprint))
            records.append(dict(joint=ji,object_index=oi,plate=oi+1,side=['lower','upper'][side],name=name,
                assembly_footprint=mapping(footprint),volume_z_mm=[0,13.5],settings=OVERRIDE,
                minimum_screw_bolster_clearance_mm=min(distances)))
    assert len(records)==28
    for name in list(files):
        if ASSET.fullmatch(name) or name in ('Metadata/slice_info.config','Metadata/filament_sequence.json'):del files[name]
    for p in cfg.findall('plate'):
        for md in list(p.findall('metadata')):
            if md.get('key') in ('gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file'):p.remove(md)
    files['3D/3dmodel.model']=xml(root);files['Metadata/model_settings.config']=xml(cfg)
    files['3D/_rels/3dmodel.model.rels']=xml(rels)
    for name in [n for n in files if n.endswith('.rels')]:
        clean=ET.Element('Relationships',xmlns=R)
        for rel in ET.fromstring(files[name]):
            if rel.get('TargetMode')=='External' or rel.get('Target').lstrip('/') in files:ET.SubElement(clean,'Relationship',rel.attrib)
        files[name]=xml(clean)
    assert all(files[n]==v for n,v in original.items() if n.startswith('3D/Objects/'))
    assert files['Metadata/project_settings.config']==original['Metadata/project_settings.config']
    write(EDIT,files,BASE)
    catalog=json.loads((ROOT/'release/root-projects/catalog.json').read_text())
    proof=dict(source_project_sha256=SOURCE_SHA,editable_sha256=digest(EDIT),accepted_sample=str(SAMPLE.relative_to(ROOT)),
        accepted_sample_sha256=SAMPLE_SHA,user_report='Solids work wonderfully',
        user_authorization='Propagate this pattern into the main knot project commit and push.',
        actual_printed_hash_and_printer_independently_observed=False,
        source_catalog_entry=catalog['Knot'],protected_before=protected(),
        original_knot_stl_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in (ROOT/'Knot STL').glob('*.stl')},
        original_cad_sha256=digest(ROOT/'Knot.scad'),source_plan_sha256=digest(PLAN),
        modifiers=records,joints=features,project_settings_changed=False,
        accepted_r3_overlap_geometry_and_fill_settings_matched=True)
    dump(REPORT/'provenance.json',proof)
    dump(REPORT/'editable-preservation.json',compare_original(EDIT))
    print('Built 28 solid lap modifiers across all 14 joints; original meshes/settings/poses untouched.',flush=True)


def native(reopen=False):
    folder=WORK/('reopen' if reopen else 'native');folder.mkdir(exist_ok=True)
    args=['--info','--export-3mf','reopened.3mf'] if reopen else ['--slice','0','--export-3mf','sliced.3mf']
    for attempt in range(3):
        with (folder/f'run-{attempt+1}.log').open('w') as log:
            p=subprocess.run([str(EXE),*args,'--outputdir',str(folder),str(FINAL if reopen else EDIT)],cwd=EXE.parent,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if p.returncode!=3221225477:break
    p.check_returncode();result=json.loads((folder/'result.json').read_text());assert result['return_code']==0
    if not reopen:assert [p['id'] for p in result['sliced_plates']]==list(range(1,11))
    print('Native reopen passed.' if reopen else 'All ten solid-lap plates sliced natively.',flush=True)


def assemble_final():
    edited=read(EDIT);sliced=read(WORK/'native/sliced.3mf')
    assert json.loads(edited['Metadata/project_settings.config'])==json.loads(sliced['Metadata/project_settings.config'])
    original_check=compare_original(WORK/'native/sliced.3mf')
    native_check=compare(EDIT,WORK/'native/sliced.3mf');assert not native_check['settings_changes']
    cfg=ET.fromstring(edited['Metadata/model_settings.config']);nc=ET.fromstring(sliced['Metadata/model_settings.config'])
    for a,b in zip(cfg.findall('plate'),nc.findall('plate')):
        for md in list(a.findall('metadata')):a.remove(md)
        for md in b.findall('metadata'):a.insert(0,copy.deepcopy(md))
        ai=a.find('model_instance');bi=b.find('model_instance')
        for md in ai.findall('metadata'):
            if md.get('key')=='identify_id':md.set('value',props(bi)['identify_id'])
    final=dict(edited);final['Metadata/model_settings.config']=xml(cfg)
    for name,data in sliced.items():
        if ASSET.fullmatch(name) or name in ('Metadata/slice_info.config','Metadata/filament_sequence.json'):final[name]=data
    write(FINAL,final,BASE)
    compare_original(FINAL);compare(EDIT,FINAL)
    return original_check,native_check


def angles(paths):
    groups=collections.defaultdict(collections.Counter)
    for slot,feature,ends,width in paths:
        d=ends[1]-ends[0];length=float(np.linalg.norm(d[:2]))
        if feature=='Top surface' and length>.5:
            angle=round((math.degrees(math.atan2(d[1],d[0]))%180)*2)/2
            groups[slot,round(float(ends[1,2]),2)][angle]+=length
    return {k:v.most_common(1)[0][0] for k,v in groups.items() if sum(v.values())>10}


def check_fill(body,paths,footprint,joint,plate,side):
    grouped=collections.defaultdict(list)
    for p in paths:
        if p[2][1,2]<=13.61:grouped[round(float(p[2][1,2]),3)].append(p)
    checks=[]
    local_body=body^prism(footprint.buffer(.01),-.01,13.61)
    for z,ps in sorted(grouped.items()):
        roi=cross_section(local_body,z-.1).intersection(footprint).buffer(-.6)
        if roi.area<1:continue
        lines=shapely.linestrings(np.array([p[2][:,:2] for p in ps]))
        # Include beads whose centerlines lie outside the measurement region:
        # their swept widths can still cover its edges. A centerline-only
        # filter falsely reported uncovered strips on the unchanged key tops.
        hits=shapely.distance(lines,roi)<=np.array([p[3]/2+.00001 for p in ps])
        selected=[(p,ln) for p,ln,hit in zip(ps,lines,hits) if hit];assert selected
        bands=shapely.union_all([ln.buffer(p[3]/2,quad_segs=6) for p,ln in selected])
        fraction=bands.intersection(roi).area/roi.area
        # Normal bridge spacing is intentionally preserved over supports.
        bridges=[ln.buffer(p[3]/2,quad_segs=6) for p,ln in selected if p[1]=='Bridge']
        bridge_fraction=shapely.union_all(bridges).intersection(roi).area/roi.area if bridges else 0
        assert fraction>(.84 if bridge_fraction>.1 else .975),(joint,plate,z,fraction,bridge_fraction)
        checks.append(dict(joint=joint,plate=plate,side=side,z_mm=z,interior_area_mm2=roi.area,
            commanded_coverage_fraction=fraction,bridge_coverage_fraction=bridge_fraction,
            features=sorted({p[1] for p,ln in selected})))
    assert len(checks)>15,(joint,plate,len(checks))
    return checks


def investigate_coverage_edge(body,paths,oldpaths,footprint):
    roi=cross_section(body,5.9).intersection(footprint).buffer(-.6)
    results=[];sets=[]
    for label,source in [('source',oldpaths),('solid_laps',paths)]:
        ps=[p for p in source if abs(p[2][1,2]-6)<.001]
        lines=shapely.linestrings(np.array([p[2][:,:2] for p in ps]));widths=np.array([p[3] for p in ps])
        fractions={}
        for method,selected in [('centerlines_only',shapely.intersects(lines,roi)),
                                ('full_bead_widths',shapely.distance(lines,roi)<=widths/2+.00001)]:
            bands=shapely.union_all([ln.buffer(w/2,quad_segs=6) for ln,w,hit in zip(lines,widths,selected) if hit])
            fractions[method]=bands.intersection(roi).area/roi.area
            if method=='full_bead_widths':
                segments=sorted((int(p[0]),p[1],round(p[3],6),tuple(sorted(tuple(np.round(q,6)) for q in p[2]))) for p,hit in zip(ps,selected) if hit)
                sets.append(sha(repr(segments).encode()))
        assert fractions['full_bead_widths']>.98
        results.append(dict(slice=label,coverage=fractions))
    assert abs(results[0]['coverage']['centerlines_only']-results[1]['coverage']['centerlines_only'])<1e-7
    dump(REPORT/'coverage-edge-investigation.json',dict(plate=5,joint=5,layer_z_mm=6,
        finding='A centerline-only ROI filter omitted bead edges. The full swept-width calculation resolves the apparent gap without any print-artifact change.',
        measurements=results,source_and_new_selected_segment_sets_identical=sets[0]==sets[1],segment_set_sha256=sets))


def validate():
    proof=json.loads((REPORT/'provenance.json').read_text())
    assert digest(BASE)==SOURCE_SHA and digest(EDIT)==proof['editable_sha256']
    assert protected()==proof['protected_before']
    original_check,native_check=assemble_final()
    geometry=joints.geometry(FINAL)
    settings,objects=rows(FINAL);files=read(FINAL);old=read(BASE)
    locks={**LOCKS,'support_type':'normal(auto)','nozzle_diameter':['0.4']}
    for key,value in locks.items():assert settings[key]==value
    allpaths={};keypaths={};lap_checks=[];records=[];padchecks=[];supportchecks=[]
    plan=json.loads(PLAN.read_text());frame=json.loads((PLAN.parent/'frame-geometry-validation.json').read_text())
    info=ET.fromstring(files['Metadata/slice_info.config']);result=json.loads((WORK/'native/result.json').read_text())
    bolster_count=blue_count=0
    for oi,obj in enumerate(objects):
        number=obj['plate'];name=f'Metadata/plate_{number}.gcode';raw=files[name];text=raw.decode()
        assert raw!=old[name] and hashlib.md5(raw).hexdigest()==files[name+'.md5'].decode().strip().lower()
        config=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',text,re.M))
        oldconfig=dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',old[name].decode(),re.M))
        assert config==oldconfig,(number,{k:[oldconfig.get(k),v] for k,v in config.items() if oldconfig.get(k)!=v})
        assert obj['settings']['enable_support']=='1' and obj['settings']['support_interface_spacing']=='0.2'
        for part in obj['parts']:
            e={**settings,**effective(obj['settings']),**effective(part['settings'])};expected=dict(locks)
            if part['settings'].get('name')=='Local solid screw reinforcement':
                expected['sparse_infill_density']='100%';bolster_count+=1
                assert np.allclose(part['mesh'].bounds[:,2],[0,12.4],atol=.00001)
            if part['settings'].get('name','').startswith(PREFIX):expected.update(OVERRIDE)
            for key,value in expected.items():assert e[key]==value,(number,key,e[key])
            if part['settings'].get('extruder')=='3':
                assert np.allclose(part['mesh'].bounds[:,2],[12.5,13.5],atol=.00001);blue_count+=1
        scan=scan_gcode(text);lo,hi=np.array(scan['bead_xy_bounds_mm']);clearance=float(min(*lo,*(np.array([330,320])-hi)))
        assert clearance>.5 and scan['features'].get('Support',0)>0 and scan['features'].get('Support interface',0)>0
        assert scan['model_extrusion_z_by_filament_mm']['3']==[12.8,13,13.2,13.4,13.6]
        tr=obj['transform'];hulls=[MultiPoint((p['mesh'].vertices@tr[:3,:3].T+tr[:3,3])[:,:2]).convex_hull for p in obj['parts'] if p['subtype']=='normal_part']
        top=max(max(z) for z in scan['model_extrusion_z_by_filament_mm'].values())
        startup=check_startup_tower(settings,hulls,3,top,number);tower=check_tower(text,hulls,[0,0,330,320]);tower.pop('actual_tower_convex_envelope')
        paths=paths_with_width(text,tr);oldpaths=paths_with_width(old[name].decode(),tr)
        before_angles,after_angles=angles(oldpaths),angles(paths)
        assert before_angles.keys()==after_angles.keys()
        assert all(abs((v-after_angles[k]+90)%180-90)<=.5 for k,v in before_angles.items()),(number,before_angles,after_angles)
        keypaths[number]=[p for p in paths if 5.19<=p[2][1,2]<=6.01]
        body=mf.Manifold.batch_boolean([solid(p['mesh']) for p in obj['parts'] if p['subtype']=='normal_part'],mf.OpType.Add)
        localmods=[m for m in proof['modifiers'] if m['object_index']==oi]
        for mod in localmods:lap_checks+=check_fill(body,paths,shape(mod['assembly_footprint']),mod['joint'],number,mod['side'])
        if oi==4:
            mod=next(m for m in localmods if m['joint']==5 and m['side']=='lower')
            investigate_coverage_edge(body,paths,oldpaths,shape(mod['assembly_footprint']))
        union=shapely.union_all([shape(m['assembly_footprint']) for m in localmods])
        sparse=[p for p in paths if p[1]=='Sparse infill']
        assert sparse and any(LineString(p[2][:,:2]).distance(union)>2 for p in sparse),'Missing sparse body infill'
        # Original material regions must still select the same extruders,
        # including where the new settings modifiers cross colored stock.
        colorchecks=0
        for part in obj['parts']:
            slot=part['settings'].get('extruder')
            if slot not in ('2','3'):continue
            col=solid(part['mesh'])
            for z in sorted({round(float(p[2][1,2]),3) for p in paths if p[0]==int(slot)}):
                area=cross_section(col,z-.1).buffer(-.5)
                if area.is_empty:continue
                pool=[p for p in paths if abs(p[2][1,2]-z)<.001]
                points=shapely.points(np.array([p[2][:,:2].mean(axis=0) for p in pool]));inside=shapely.contains(area,points)
                for p,hit in zip(pool,inside):
                    if hit:assert p[0]==int(slot);colorchecks+=1
        assert colorchecks>0
        # All 42 removed lower-lap pad sites remain at Z4.8 in real paths.
        a=np.array([p[2] for p in paths]);starts=a[:,0,:2];deltas=a[:,1,:2]-starts;lengths=(deltas*deltas).sum(axis=1)
        for j,pr in zip(plan['frame_joints'],frame['joints']):
            if j[0]!=oi:continue
            for xy in pr['seating_pads_xy']:
                frac=np.clip(((np.array(xy)-starts)*deltas).sum(axis=1)/lengths,0,1)
                near=np.linalg.norm(starts+frac[:,None]*deltas-xy,axis=1)<.65
                height=float(a[near,:,2].max());assert abs(height-4.8)<.001
                padchecks.append(dict(joint=pr['joint'],plate=number,xy_mm=xy,max_z_mm=height))
        shell=[p for p in paths if 12.79<=p[2][1,2]<=13.61];skin=[]
        for part in obj['parts']:
            if part['settings'].get('name')!='Local solid screw reinforcement':continue
            b=part['mesh'].bounds;c=b[:,:2].mean(axis=0);radius=float(np.ptp(b[:,0])/2)
            counts=crossings(shell,c,radius);assert min(counts.values())>=5,(number,c,counts)
            skin.append(dict(center_mm=c.tolist(),radius_mm=radius,z_cap_mm=12.4,crossing_segments=counts))
        emitted=[p for p in all_extrusions(text) if p['feature']=='Support interface']
        support_lines=shapely.linestrings(np.array([p['segment'] for p in emitted]))
        support_z=np.array([p['z'] for p in emitted])
        model_lines=shapely.linestrings(a[:,:,:2]);model_z=a[:,1,2]
        for ji,j in enumerate(plan['frame_joints'],1):
            if j[1]!=oi:continue
            angle=math.radians(j[3]);n=np.array([math.cos(angle),math.sin(angle)]);t=np.array([-n[1],n[0]])
            for ki,y in enumerate(j[5],1):
                xy=np.array(j[2])+9*n+y*t;bed=(np.array([*xy,0])@tr[:3,:3].T+tr[:3,3])[:2]
                near=shapely.distance(support_lines,Point(bed))<.6
                assert near.any()
                supporttop=float(support_z[near].max())
                first=float(model_z[shapely.distance(model_lines,Point(xy))<.6].min())
                gap=first-.2-supporttop;assert abs(gap-.2)<.001,(ji,ki,gap)
                supportchecks.append(dict(joint=ji,key=ki,plate=number,interface_z_mm=supporttop,first_model_z_mm=float(first),gap_mm=float(gap)))
        pi=next(p for p in info.findall('plate') if props(p)['index']==str(number));warnings=[w.attrib for w in pi.findall('warning')]
        assert all(w.get('msg')=='not_support_traditional_timelapse' for w in warnings),warnings
        est=next(p for p in result['sliced_plates'] if p['id']==number)
        records.append(dict(plate=number,source_gcode_sha256=sha(old[name]),gcode_sha256=sha(raw),md5_verified=True,
            global_gcode_config_unchanged=True,model_z_by_filament_mm=scan['model_extrusion_z_by_filament_mm'],
            bed_clearance_mm=clearance,startup_tower=startup,tower=tower,warnings=warnings,
            top_surface_directions_preserved=True,screw_skin_continuity=skin,color_segments_checked=colorchecks,
            solid_lap_modifiers=len(localmods),body_8_percent_gyroid_retained=True,
            seconds=est['total_predication'],grams=sum(f['total_used_g'] for f in est['filaments'])))
        dump(WORK/'validation-progress.json',records)
        print(f'F{number}: solid laps, sparse body, colors, screw skins, supports, clearances and settings checked.',flush=True)
    assert bolster_count==50 and blue_count==10 and len(padchecks)==42 and len(supportchecks)==28
    jointpaths=joints.toolpaths(keypaths)
    dump(REPORT/'lap-toolpaths.json',dict(checks=lap_checks,modifiers_checked=28,
        minimum_commanded_coverage_fraction=min(r['commanded_coverage_fraction'] for r in lap_checks),
        note='Swept commanded line-width coverage; preserved bridge spacing is checked separately. Does not measure deposited plastic.'))
    native(True);reopen=compare(FINAL,WORK/'reopen/reopened.3mf');assert not reopen['settings_changes']
    compare_original(WORK/'reopen/reopened.3mf')
    assert protected()==proof['protected_before']
    changed=[n for n in set(old)|set(files) if old.get(n)!=files.get(n)]
    unchanged={n:sha(v) for n,v in old.items() if files.get(n)==v}
    assert all(n in unchanged for n in old if n.startswith('3D/Objects/'))
    report=dict(project='Knot.3mf',project_sha256=digest(FINAL),source_project_sha256=SOURCE_SHA,
        accepted_sample=str(SAMPLE.relative_to(ROOT)),accepted_sample_sha256=SAMPLE_SHA,
        user_reported_solid_lap_success=True,actual_printed_hash_printer_independently_observed=False,
        joint_count=14,solid_lap_modifier_count=28,local_fill_settings=OVERRIDE,
        original_meshes_settings_support_paint_and_poses_preserved=True,original_object_checks=original_check,
        all_global_settings_preserved=True,preserved_archive_entries_sha256=unchanged,changed_archive_entries=changed,
        native_roundtrip=native_check,native_reopen=reopen,native_reopen_verified=True,fresh_native_slices=True,
        native_reopen_scope='Editable geometry/settings roundtrip. CLI --info export omits G-code caches; the delivered final retains all ten freshly sliced and independently checked G-codes.',
        plates=records,removed_pad_toolpath_checks=padchecks,groove_support_checks=supportchecks,
        minimum_commanded_key_clearance_mm=jointpaths['minimum_commanded_clearance_mm'],
        all_50_screw_modifiers_capped_at_z12_4=True,all_five_skin_layers_cross_screw_boundaries=True,
        all_28_lap_regions_disjoint_from_screw_bolsters=True,blue_layers=5,
        total_seconds=sum(p['seconds'] for p in records),total_grams=sum(p['grams'] for p in records),
        evidence_sha256={n:digest(REPORT/n) for n in ['provenance.json','editable-preservation.json','joint-geometry.json','joint-toolpaths.json','lap-toolpaths.json','coverage-edge-investigation.json']},
        protected_after=protected(),printer_job_sent=False,full_size_physical_qualification_pending=True)
    dump(REPORT/'validation.json',report)
    shutil.copyfile(WORK/'native/result.json',REPORT/'native-result.json');shutil.copyfile(WORK/'reopen/result.json',REPORT/'native-reopen.json')
    print('All ten production plates passed; ready to publish the validated project.',flush=True)


def publish():
    proof=json.loads((REPORT/'provenance.json').read_text());report=json.loads((REPORT/'validation.json').read_text())
    assert digest(FINAL)==report['project_sha256'] and digest(ROOT/'Knot.3mf')==SOURCE_SHA
    assert protected()==proof['protected_before']
    catpath=ROOT/'release/root-projects/catalog.json';catalog=json.loads(catpath.read_text())
    assert catalog['Knot']==proof['source_catalog_entry']
    st,objects=rows(FINAL);entry=catalog['Knot'];cad=ROOT/'Knot.scad'
    assert digest(cad)==proof['original_cad_sha256']
    lines=[cad.read_text().rstrip(),'','// Approved 100% rectilinear lap modifiers; original model geometry retained.']
    new_stls={}
    for oi,(obj,catalog_obj) in enumerate(zip(objects,entry['objects'])):
        original_count=len(catalog_obj['parts'])
        for part in obj['parts'][original_count:]:
            name=part['settings']['name'];ji=int(re.search(r'J(\d+)',name)[1])
            path=ROOT/'Knot STL'/f'J{ji:02d}-solid-lap-modifier.stl'
            data=part['mesh'].export(file_type='stl')
            if path.exists():assert path.read_bytes()==data
            else:path.write_bytes(data)
            new_stls[path.relative_to(ROOT).as_posix()]=digest(path)
            offset=grid(oi,10,pitch(st));rel=path.relative_to(ROOT).as_posix()
            lines += [f'// Plate {oi+1}: {name}',f'if ((plate == 0 || plate == {oi+1}) && show_modifiers)',
                f' translate(plate == 0 ? {json.dumps([float(offset[0]),float(offset[1]),0])} : [0,0,0])',
                f'  multmatrix({json.dumps(obj["transform"].tolist())})',f'   color("#FF9900") import("{rel}", convexity=20);','']
            catalog_obj['parts'].append(dict(file=rel,sha256=digest(path),subtype=part['subtype'],settings=part['settings'],
                faces=len(part['mesh'].faces),bounds=part['mesh'].bounds.tolist()))
    cad.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8',newline='\n')
    assert len(new_stls)==14
    entry.update(sha256=report['project_sha256'],cad_sha256=digest(cad),
        unique_stl=len({p['file'] for o in entry['objects'] for p in o['parts']}),
        solid_laps_validation='release/knot-solid-laps-r1/validation.json')
    report['new_modifier_stls']=new_stls;report['cad_sha256']=digest(cad)
    report['original_knot_stls_unchanged']=all(digest(ROOT/n)==h for n,h in proof['original_knot_stl_hashes'].items())
    assert report['original_knot_stls_unchanged']
    dump(REPORT/'validation.json',report)
    staged=WORK/'publish.3mf';shutil.copyfile(FINAL,staged);staged.replace(ROOT/'Knot.3mf')
    dump(catpath,catalog)
    hp=ROOT/'release/root-projects/gcode-sha256.json';hashes=json.loads(hp.read_text())
    hashes['Knot']={f"plate_{p['plate']}":p['gcode_sha256'] for p in report['plates']};dump(hp,hashes)
    shutil.copyfile(REPORT/'native-result.json',ROOT/'release/root-projects/Knot-native.json')
    assert protected()==proof['protected_before']
    print('Published root Knot.3mf, adjacent modifier STL/CAD and release catalog.',flush=True)


def guide():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    _,objects=rows(FINAL)
    proof=json.loads((REPORT/'provenance.json').read_text())
    fig,ax=plt.subplots(figsize=(10,10))
    for obj in objects:
        body=mf.Manifold.batch_boolean([solid(p['mesh']) for p in obj['parts'] if p['subtype']=='normal_part'],mf.OpType.Add)
        outline=cross_section(body,7.5)
        for p in getattr(outline,'geoms',[outline]):
            if p.is_empty:continue
            ax.fill(*p.exterior.xy,color='#e5e9ed',ec='#83919c',lw=.4)
            for h in p.interiors:ax.fill(*h.xy,color='white')
    for mod in proof['modifiers']:
        if mod['side']!='lower':continue
        region=shape(mod['assembly_footprint'])
        for p in getattr(region,'geoms',[region]):
            if p.is_empty:continue
            ax.fill(*p.exterior.xy,color='#efa94c',ec='#a05b10',lw=.7)
            for h in p.interiors:ax.fill(*h.xy,color='white')
        c=region.centroid
        ax.text(c.x,c.y,f"J{mod['joint']}",ha='center',va='center',fontsize=9,
            bbox={'boxstyle':'round,pad=.15','facecolor':'white','alpha':.9,'edgecolor':'none'})
    for obj in objects:
        for p in obj['parts']:
            if p['settings'].get('name')!='Local solid screw reinforcement':continue
            b=p['mesh'].bounds;c=b[:,:2].mean(axis=0);r=np.ptp(b[:,0])/2
            ax.add_patch(plt.Circle(c,r,fill=False,color='#bd4646',lw=.7))
    ax.set_aspect('equal');ax.axis('off')
    fig.suptitle('Knot — solid overlaps at all 14 joints',fontsize=18)
    fig.text(.5,.045,'Orange: 100% rectilinear in both mating halves at each marked joint.\nRed rings: original capped screw-bolster footprints; no overlap with the solid laps.',ha='center',fontsize=11)
    fig.tight_layout(rect=[0,.08,1,.96]);fig.savefig(REPORT/'solid-laps-map.png',dpi=160);plt.close(fig)


def document():
    r=json.loads((REPORT/'validation.json').read_text())
    assert digest(ROOT/'Knot.3mf')==r['project_sha256']
    def duration(seconds):
        minutes=round(seconds/60)
        return f'{minutes//60}h {minutes%60:02d}m'
    table='\n'.join(f"| F{p['plate']} | {duration(p['seconds'])} | {p['grams']:.2f} g |" for p in r['plates'])
    text=f'''# Knot solid laps — October 25, 2026

Current production file: **root `Knot.3mf`**, Bambu Lab A2L, ten plates F1–F10.

The user reported **"Solids work wonderfully"** after the supplied r3 solid-lap sample and requested promotion, commit and push. Both halves of **all 14 overlapping joints** now use the accepted **100% rectilinear** fill. Bambu serializes Rectilinear as `zig-zag`. Each new modifier covers joint-local X0–18 mm and Z0–13.5 across the actual lower lap's projected outline; the matching upper half receives the same footprint. This extends the successful sample across the full joint width without changing any printable geometry. The projection masks simplify only sub-micron edges (maximum allowed outline error 0.0001 mm); no original mesh is simplified or regenerated.

The source has 28 new local settings modifiers. All original embedded body, color and screw-modifier mesh files remain **byte-identical**. The new masks add no printed stock and do not fill the key clearances, glue recesses, holes or removed pads.

## Preserved settings and reinforcement

Surrounding bodies remain **8% gyroid**. Infill-first stays **off**; supports stay **normal(auto)** with the same paint, build-plate-only activation, 0.20 mm interface spacing and 0.20 mm top gap. Nozzle 0.4 mm, layers 0.20 mm, four walls, five top/bottom layers, textured PEI, materials, temperatures, speeds, cooling, brims, poses and finish directions remain unchanged.

All **50 screw reinforcement modifiers end at Z12.4**, preserving their original 100% infill and pattern beneath the five top layers. None of the new lap masks overlaps any screw-bolster footprint. Five blue layers remain. Letter, all other root projects, their CAD/STL and the approved ERYONE sample remain byte-identical.

## Verification

- Compared every original volume, support-paint record, pose and effective setting before and after the change and after native reopen.
- Fresh native slices on all ten plates; complete G-code configurations remain identical to their source configurations, with valid checksums.
- Checked actual dense fill throughout all 28 lap regions and retained sparse fill outside them. The inherited spacing of bridge layers over supports is preserved. Commanded line-width coverage is recorded in `lap-toolpaths.json`.
- Checked all 14 joints / 28 keys geometrically and **140** key/groove layer pairs in actual native paths. Minimum commanded key clearance: **{r['minimum_commanded_key_clearance_mm']:.4f} mm**.
- Verified all 42 removed lower-lap pad sites, support backing and 0.20 mm gaps at all 28 grooves, color assignments, surface directions, all 50 bolster caps and five-layer continuity, plus bed/tower clearance including supports.
- Reopened the final project natively and synchronized 14 new shared modifier STLs, 28 CAD references and the release catalog. All pre-existing Knot STLs remain unchanged.

The physical sample result is user-reported. The actual printed hash/printer were not independently observed. Full-size fit, clamping performance and surface finish for this promoted revision remain unconfirmed. No print job was sent.

## Native estimates

| Piece | Time | Material |
| --- | ---: | ---: |
{table}
| **Total** | **{duration(r['total_seconds'])}** | **{r['total_grams']:.2f} g** |

These are slicer estimates, including supports and purge structures.

## Files and evidence

- Production SHA-256: `{r['project_sha256']}`
- Source production SHA-256: `{SOURCE_SHA}` (preceding committed Knot revision).
- Accepted sample: `Dara-A2L-Joint-Solid-Laps-r3.3mf`, SHA-256 `{SAMPLE_SHA}`.
- `provenance.json` records the user's result/authorization, exact source, masks and protected files.
- `validation.json`, `joint-geometry.json`, `joint-toolpaths.json` and `lap-toolpaths.json` record current checks.
- `native-result.json` and `native-reopen.json` record native completion.

Earlier rollback, normal-support and r2 approval reports retain their historical hashes. Run `python scripts/audit_root_projects.py` to audit the current release and its source chain. The accepted sample evidence lives in `output/Dara-A2L-Joint-Solid-Laps-r3/`; the repository's existing production-only 3MF inventory is preserved.
'''
    (REPORT/'README.md').write_text(text,encoding='utf-8',newline='\n')
    p=ROOT/'README.md';text=p.read_text(encoding='utf-8')
    text=text.replace('Full-size F1–F10, normal supports, infill-first off','Full-size F1–F10, solid laps, normal supports, infill-first off')
    paragraph='''**Knot:** all 14 joints now have **100% rectilinear fill in both overlapping lap halves**, promoted from the r3 test after the user reported "Solids work wonderfully." Surrounding bodies remain **8% gyroid**; **normal supports and infill-first off** remain. All ten plates are freshly sliced and natively reopened. Original joint geometry, color boundaries, poses, support settings, all 50 Z12.4 screw-bolster caps and five top layers are preserved. See the [solid-lap production checks](release/knot-solid-laps-r1/README.md). The user-reported sample success does not independently qualify full-size performance. The [earlier r2 joint approval](release/knot-joint-approval-r1/README.md), [normal-support change](release/knot-normal-supports-r1/README.md) and [infill-first rollback](release/knot-infill-first-revert-r1/README.md) remain historical records.'''
    text,n=re.subn(r'^\*\*Knot:\*\*[^\n]+',lambda _:paragraph,text,flags=re.M);assert n==1
    p.write_text(text,encoding='utf-8',newline='\n')
    p=ROOT/'release/root-projects/README.md';text=p.read_text(encoding='utf-8')
    text=re.sub(r'^\| Knot \|[^\n]+',f"| Knot | 10 | {duration(r['total_seconds'])} | {r['total_grams']:.2f} g |",text,flags=re.M)
    note='''**October 25 solid Knot laps:** the main `Knot.3mf` now contains the accepted **100% rectilinear fill in both halves of all 14 joints**, with 28 local modifiers and ten fresh native slices. Surrounding bodies stay 8% gyroid; original geometry, normal supports, infill-first off, all 50 Z12.4 screw caps and five top layers remain. Native reopening, current geometry/toolpaths and adjacent CAD/STL are verified in [knot-solid-laps-r1](../knot-solid-laps-r1/README.md). The user reported "Solids work wonderfully" for r3; full-size performance remains unconfirmed. Earlier Knot records below describe source revisions, not current container/toolpath hashes.

'''
    if note not in text:text=text.replace('**October 25 main Letter correction:**',note+'**October 25 main Letter correction:**',1)
    text=text.replace('The accepted J3 F2/F3 test is a direct crop of this exact root `Knot.3mf`.','The accepted J3 F2/F3 test was a direct crop of the preceding root `Knot.3mf` revision.')
    text=text.replace('Its geometry/settings are already present across the existing production design; ten current native slices retain','Its geometry/settings were already present across that production design; those ten native slices retained')
    text=text.replace('Current root `Knot.3mf` uses **normal(auto)** supports','The preceding root `Knot.3mf` revision introduced **normal(auto)** supports')
    p.write_text(text,encoding='utf-8',newline='\n')
    p=SAMPLE.parent/'README.md';text=p.read_text(encoding='utf-8')
    marker='## User-reported result — October 25, 2026'
    if marker not in text:
        note=f'''{marker}

The user reported **"Solids work wonderfully"** and requested propagation, commit and push. This is user-reported success for the supplied r3 sample, SHA-256 `{SAMPLE_SHA}`; the actual printed hash/printer were not independently observed. Its solid-lap settings are now promoted to the main `Knot.3mf`; see `release/knot-solid-laps-r1/`. Full-size performance and bolster appearance are not independently established by this statement. The preparation notes below describe the sample's creation before promotion; their digital checks remain historical evidence.

'''
        first,rest=text.split('\n',1);text=first+'\n\n'+note+rest.lstrip()
        p.write_text(text,encoding='utf-8',newline='\n')
    print('Updated production documentation and recorded the r3 physical report.',flush=True)


if __name__=='__main__':
    action=sys.argv[1]
    if action=='slice':native()
    else:globals()[action]()
