"""Historical r1 audit, withdrawn for testing the wrong screw feature.

These checks did not identify the requested photo-retainer bolster. Do not use
them to qualify a current sample; r2 has explicit photo-anchor/bore checks.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'scripts')]
import numpy as np
import manifold3d as mf
import shapely
from shapely.geometry import box,Point,LineString,MultiPoint
from organize_root_projects import rows,BOOKKEEPING
from development_3mf import solid,mesh
from develop_m_veneer import locate
from develop_cosmetic_joints import cross_section
from build_a2l_project import prism
from audit_knot_rollback_joints import vertical_hits,local,paths_with_width,key_paths
from correct_knot_reinforcement_skin import crossings
from remove_unused_project_filaments import read,digest,dump,props,EXE
from revert_knot_infill_first import protected,LOCKS
from build_photo_support_test import paths as extrusions
from check_a2l_towers import check_tower,check_startup_tower
from validate_print_project import scan_gcode

OUT=ROOT/'output/Dara-A2L-Joint-Screw-Bolster-r1'
SAMPLE=OUT/'Dara-A2L-Joint-Screw-Bolster-r1.3mf'
SOURCE=ROOT/'Knot.3mf'
SHA='8229ed33c45aae2a29ce10df0b178d7ef1ad225bcc8f1cd8c61d9ece846d7a15'
SOURCE_SHA='aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46'
WORK=ROOT/'.work/joint-screw-bolster-r1/reaudit'

def hashes():return {**protected(),'Knot.3mf':digest(SOURCE),'delivered_sample':digest(SAMPLE)}
def eff(s):return {k:v for k,v in s.items() if k not in BOOKKEEPING}
def commands(t):return '\n'.join(l.split(';')[0].rstrip() for l in t.splitlines() if l.split(';')[0].strip())
def cfg(t):return dict(re.findall(r'^; ([A-Za-z_0-9]+) = (.*)$',t,re.M))

def static():
    before=hashes();assert before['delivered_sample']==SHA and before['Knot.3mf']==SOURCE_SHA
    ss,source=rows(SOURCE);s,objects=rows(SAMPLE);assert len(objects)==2
    j=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())['frame_joints'][1]
    assert j[:2]==[2,0]
    region=locate(box(-18,-32,44,48),j);crop=prism(region,-.01,20)
    bodies=[];volume_checks=[];bolsters=[];hulls=[]
    for obj,oi in zip(objects,[2,0]):
        original=source[oi]
        assert np.max(abs(obj['transform'][:3,:3]-original['transform'][:3,:3]))<1e-6
        assert eff(obj['settings'])==eff(original['settings'])
        expected=[]
        for p in original['parts']:
            clipped=solid(p['mesh'])^crop
            if clipped.volume()>1e-7:expected.append((p,clipped))
        assert len(expected)==len(obj['parts'])
        actual=[]
        for q,(p,clipped) in zip(obj['parts'],expected):
            assert q['subtype']==p['subtype'] and eff(q['settings'])==eff(p['settings'])
            assert q['paint']==p['paint']==[]
            m=q['mesh'];assert m.is_volume and m.is_watertight
            got=solid(m);extra=abs((got-clipped).volume());missing=abs((clipped-got).volume())
            # Native serialization rounds coordinates to microns. Volume error
            # is bounded relative to surface area, then every overlap component
            # is checked separately below for assembled interference.
            tolerance=m.area*.000005
            assert extra+missing<tolerance,(obj['name'],extra,missing,tolerance)
            volume_checks.append(dict(object=obj['name'],volume=q['settings']['name'],
                extra_mm3=extra,missing_mm3=missing,tolerance_mm3=tolerance))
            if q['subtype']=='normal_part':actual.append(got)
            if q['settings'].get('name')=='Local solid screw reinforcement':
                assert abs(solid(p['mesh']).volume()-clipped.volume())<1e-5
                assert q['settings']['sparse_infill_density']=='100%'
                assert np.allclose(m.bounds[:,2],[0,12.4],atol=1e-5)
                center=m.bounds[:,:2].mean(axis=0);radius=np.ptp(m.bounds[:,0])/2
                assert region.boundary.distance(Point(center))-radius>5
                bolsters.append(dict(center_mm=center.tolist(),radius_mm=float(radius),z_mm=[0,12.4]))
        body=mf.Manifold.batch_boolean(actual,mf.OpType.Add);bodies.append(body)
        assert len(body.decompose())==1
        vertices=mesh(body).vertices@obj['transform'][:3,:3].T+obj['transform'][:3,3]
        assert abs(vertices[:,2].min())<.001
        hulls.append(MultiPoint(vertices[:,:2]).convex_hull)
    assert len(bolsters)==1 and hulls[0].distance(hulls[1])>8
    intersection=bodies[0]^bodies[1];slivers=[]
    angle=math.radians(j[3]);n=np.array([math.cos(angle),math.sin(angle)]);t=np.array([-n[1],n[0]])
    for component in intersection.decompose():
        v=component.to_mesh64().vert_properties[:,:3]
        if not len(v):continue
        localv=np.column_stack(((v[:,:2]-j[2])@np.column_stack((n,t)),v[:,2]))
        thickness=float(np.ptp(localv,axis=0).min());assert thickness<.0001
        slivers.append(thickness)
    probes=[]
    for key,y in enumerate(j[5],1):
        for z in [5.1,5.3,5.5,5.7,5.9]:
            a,b=[local(cross_section(body,z),j) for body in bodies]
            for x in [3.5,9,14.5]:
                line=LineString([(x,y-3.5),(x,y+3.5)])
                male=a.intersection(line);cavity=line.difference(b)
                if cavity.geom_type=='MultiLineString':cavity=next(g for g in cavity.geoms if g.distance(Point(x,y))<.0001)
                kw=male.bounds[3]-male.bounds[1];gw=cavity.bounds[3]-cavity.bounds[1]
                assert abs(kw-3)<.001 and gw-kw>.29
                probes.append(dict(key=key,x_mm=x,z_mm=z,key_width_mm=kw,groove_width_mm=gw))
        xy=np.array(j[2])+9*n+y*t
        a,b=[vertical_hits(mesh(body),xy) for body in bodies]
        assert abs(max(a)-6)<.001 and abs(min(z for z in b if z>4.8)-6.3)<.001
    differences={k:[ss.get(k),s.get(k)] for k in set(ss)|set(s) if ss.get(k)!=s.get(k)}
    assert set(differences)=={'print_settings_id','wipe_tower_x','wipe_tower_y'}
    locks={**LOCKS,'support_type':'normal(auto)','nozzle_diameter':['0.4']}
    for o in objects:
        assert o['settings']['enable_support']=='1' and o['settings']['support_interface_spacing']=='0.2'
        for p in o['parts']:
            e={**s,**eff(o['settings']),**eff(p['settings'])}
            for k,v in locks.items():
                if k=='sparse_infill_density' and p['settings'].get('name')=='Local solid screw reinforcement':v='100%'
                assert e[k]==v
    assert s['printer_model']=='Bambu Lab A2L'
    # Also recheck the main project: all 50 capped modifiers, all ten supports.
    mainbolsters=0
    for o in source:
        assert o['settings']['enable_support']=='1' and o['settings']['support_interface_spacing']=='0.2'
        for p in o['parts']:
            if p['settings'].get('name')=='Local solid screw reinforcement':
                assert p['settings']['sparse_infill_density']=='100%'
                assert np.allclose(p['mesh'].bounds[:,2],[0,12.4],atol=1e-5);mainbolsters+=1
    assert mainbolsters==50 and ss['is_infill_first']=='0' and ss['support_type']=='normal(auto)'
    assert hashes()==before
    dump(WORK/'geometry-settings.json',dict(sample_sha256=SHA,source_sha256=SOURCE_SHA,
        geometry_pass=True,settings_pass=True,volumes=volume_checks,complete_bolster=bolsters,
        assembled_overlap_mm3=abs(intersection.volume()),overlap_sliver_thickness_mm=slivers,
        key_probes=probes,global_differences=differences,all_effective_settings_preserved=True,
        all_50_production_bolsters_capped=True,protected_before=before))
    print('PASS: exact delivered crop, complete assembly clearance, all overrides, and all 50 production bolster caps.',flush=True)

def native():
    assert digest(SAMPLE)==SHA
    WORK.mkdir(parents=True,exist_ok=True)
    for attempt in range(3):
        with (WORK/f'slice-{attempt+1}.log').open('w') as log:
            p=subprocess.run([str(EXE),'--slice','0','--export-3mf','fresh.3mf','--outputdir',str(WORK),str(SAMPLE)],
                cwd=EXE.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        if p.returncode!=3221225477:break
    p.check_returncode();result=json.loads((WORK/'result.json').read_text());assert result['return_code']==0
    assert digest(SAMPLE)==SHA
    print('PASS: fresh native slice from delivered file.',flush=True)

def toolpaths():
    a=read(SAMPLE);b=read(WORK/'fresh.3mf')
    text=a['Metadata/plate_1.gcode'].decode();fresh=b['Metadata/plate_1.gcode'].decode()
    assert cfg(text)==cfg(fresh)
    s,objects=rows(SAMPLE);fs,fo=rows(WORK/'fresh.3mf');assert s==fs
    errors=[]
    for o,q in zip(objects,fo):
        assert eff(o['settings'])==eff(q['settings']) and np.allclose(o['transform'],q['transform'],atol=1e-6)
        for p,r in zip(o['parts'],q['parts']):
            assert eff(p['settings'])==eff(r['settings']) and np.array_equal(p['mesh'].faces,r['mesh'].faces)
            error=float(np.max(abs(p['mesh'].vertices-r['mesh'].vertices)));assert error<1e-5
            errors.append(error)
    source=json.loads((WORK/'geometry-settings.json').read_text())
    source['production_skin_reference']=production_skin(source['complete_bolster'][0])
    delivered=check_paths(a,s,objects,source)
    resliced=check_paths(b,fs,fo,source)
    for old,new in zip(delivered['key_toolpaths'],resliced['key_toolpaths']):
        assert abs(old['minimum_commanded_clearance_mm']-new['minimum_commanded_clearance_mm'])<.002
    assert delivered['local_groove_support_probes']==resliced['local_groove_support_probes']
    before=json.loads((OUT/'native-result.json').read_text())['sliced_plates'][0]
    after=json.loads((WORK/'result.json').read_text())['sliced_plates'][0]
    grams_delta=sum(f['total_used_g'] for f in after['filaments'])-sum(f['total_used_g'] for f in before['filaments'])
    seconds_delta=after['total_predication']-before['total_predication']
    assert abs(grams_delta)<.02 and abs(seconds_delta)<1
    assert hashes()==source['protected_before']
    report=dict(status='THREE_PASS_DIGITAL_AUDIT_PASSED_PHYSICAL_RESULT_PENDING',sample_sha256=SHA,
        source_sha256=SOURCE_SHA,geometry_and_settings=source,
        printer_commands_identical_after_fresh_slice=commands(text)==commands(fresh),
        fresh_slice_comparison=dict(configuration_identical=True,max_serialized_vertex_delta_mm=max(errors),
            estimated_grams_delta=grams_delta,estimated_seconds_delta=seconds_delta,
            explanation='Reslicing saved native meshes changes low-order coordinates/extrusion and some fill segmentation. Both command streams were separately checked; byte identity is not claimed.'),
        delivered_toolpath_audit=delivered,fresh_toolpath_audit=resliced,
        delivered_sample_unchanged=True,production_files_unchanged=True,printer_job_sent=False)
    dump(OUT/'three-pass-audit.json',report)
    print('PASS: both stored and fresh slices independently pass key, six groove backing, five skin layer, color, bed/tower and warning checks.',flush=True)

def production_skin(bolster):
    _,objects=rows(SOURCE);o=objects[0]
    ps=paths_with_width(read(SOURCE)['Metadata/plate_1.gcode'].decode(),o['transform'])
    roi=Point(bolster['center_mm']).buffer(bolster['radius_mm']+2)
    body=mf.Manifold.batch_boolean([solid(p['mesh']) for p in o['parts'] if p['subtype']=='normal_part'],mf.OpType.Add)
    result=[]
    for z in [12.8,13.,13.2,13.4,13.6]:
        selected=[p for p in ps if abs(p[2][1,2]-z)<.001 and LineString(p[2][:,:2]).distance(roi)<1]
        env=shapely.union_all([LineString(p[2][:,:2]).buffer(p[3]/2,quad_segs=8) for p in selected])
        section=cross_section(body,min(z-.1,13.499)).intersection(roi)
        result.append(dict(z_mm=z,coverage_fraction=env.intersection(section).area/section.area,
            features=sorted(set(p[1] for p in selected))))
    return result

def check_paths(a,s,objects,source):
    text=a['Metadata/plate_1.gcode'].decode()
    assert hashlib.md5(a['Metadata/plate_1.gcode']).hexdigest()==a['Metadata/plate_1.gcode.md5'].decode().strip().lower()
    j=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A2L/production-plan.json').read_text())['frame_joints'][1]
    mc=ET.fromstring(a['Metadata/model_settings.config']);labels={props(i)['object_id']:int(props(i)['identify_id']) for i in mc.find('plate').findall('model_instance')}
    ps=[paths_with_width(text,o['transform'],labels[str(o['id'])]) for o in objects]
    checks=[]
    for ki,y in enumerate(j[5],1):
        for z in [5.2,5.4,5.6,5.8,6.0]:
            male,order=key_paths(ps[0],j,y,z);female,_=key_paths(ps[1],j,y,z)
            gap=male.distance(female);overlap=male.intersection(female).area
            assert gap>.05 and overlap<1e-6
            assert order['wall_before_fill'] in (True,None)
            checks.append(dict(key=ki,z_mm=z,minimum_commanded_clearance_mm=gap,overlap_mm2=overlap,order=order))
    bolster=source['complete_bolster'][0];c=np.array(bolster['center_mm']);radius=bolster['radius_mm']
    skin=crossings(ps[1],c,radius);assert len(skin)==5 and min(skin.values())>=5
    roi=Point(c).buffer(radius+2);body=solid(next(p['mesh'] for p in objects[1]['parts'] if p['subtype']=='normal_part'))
    coverage=[]
    for z in [12.8,13.,13.2,13.4,13.6]:
        paths=[p for p in ps[1] if abs(p[2][1,2]-z)<.001 and LineString(p[2][:,:2]).distance(roi)<1]
        assert paths and not any(p[1]=='Sparse infill' for p in paths)
        envelope=shapely.union_all([LineString(p[2][:,:2]).buffer(p[3]/2,quad_segs=8) for p in paths])
        section=cross_section(body,min(z-.1,13.499)).intersection(roi)
        fraction=envelope.intersection(section).area/section.area
        baseline=next(p for p in source['production_skin_reference'] if p['z_mm']==z)
        # The first shell layer is a bridge over the infill. Its spaced bridge
        # lines also occur in production; compare them to that actual baseline.
        # The remaining four layers must have at least 98% commanded coverage.
        assert fraction>(.90 if z==12.8 else .98),(z,fraction)
        assert abs(fraction-baseline['coverage_fraction'])<.005
        if z==12.8:assert 'Bridge' in baseline['features'] and any(p[1]=='Bridge' for p in paths)
        coverage.append(dict(z_mm=z,commanded_skin_coverage_fraction=fraction,
            production_coverage_fraction=baseline['coverage_fraction'],sparse_infill_present=False))
    emitted=extrusions(text);angle=math.radians(j[3]);normal=np.array([math.cos(angle),math.sin(angle)]);tangent=np.array([-normal[1],normal[0]])
    support=[]
    # Probe three positions along each groove instead of just its centre.
    for ki,y in enumerate(j[5],1):
        for x in [4,9,14]:
            xy=np.array(j[2])+x*normal+y*tangent;tr=objects[1]['transform'];bed=(np.array([*xy,0])@tr[:3,:3].T+tr[:3,3])[:2]
            interfaces=[p for p in emitted if p['feature']=='Support interface' and LineString(p['segment']).intersects(Point(bed).buffer(.7))]
            roof=max(p['z'] for p in interfaces)
            first=min(p[2][1,2] for p in ps[1] if LineString(p[2][:,:2]).intersects(Point(xy).buffer(.7)))
            gap=float(first-.2-roof);assert abs(gap-.2)<.001
            support.append(dict(key=ki,x_mm=x,support_top_mm=roof,first_model_layer_top_mm=float(first),air_gap_mm=gap))
    scan=scan_gcode(text);hulls=[]
    for o,paths in zip(objects,ps):
        assert any(abs(p[2][1,2]-.2)<.001 for p in paths)
        v=np.concatenate([p['mesh'].vertices for p in o['parts'] if p['subtype']=='normal_part'])@o['transform'][:3,:3].T+o['transform'][:3,3]
        hulls.append(MultiPoint(v[:,:2]).convex_hull)
    tower=check_tower(text,hulls,[0,0,330,320]);tower.pop('actual_tower_convex_envelope')
    startup=check_startup_tower(s,hulls,3,16.6,1)
    lo,hi=np.array(scan['bead_xy_bounds_mm']);clearance=float(min(*lo,*(np.array([330,320])-hi)));assert clearance>.5
    assert scan['model_extrusion_z_by_filament_mm']['3']==[12.8,13,13.2,13.4,13.6]
    warnings=[w.attrib for w in ET.fromstring(a['Metadata/slice_info.config']).iter('warning')];assert not warnings
    return dict(command_stream_sha256=hashlib.sha256(commands(text).encode()).hexdigest(),key_toolpaths=checks,
        screw_skin_crossings=skin,screw_skin_coverage=coverage,local_groove_support_probes=support,
        bed_clearance_mm=clearance,tower=tower,startup_tower=startup,warnings=warnings,
        printer_job_sent=False)

if __name__=='__main__':
    raise RuntimeError('r1 is withdrawn: M through-hole reinforcement was the wrong feature. Use the r2 photo-retainer validation.')
