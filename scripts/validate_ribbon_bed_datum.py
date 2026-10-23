"""Verify precision datums and common final surface heights in native G-code."""
import argparse
import collections
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import shapely
from shapely.geometry import Point
from development_3mf import OUT,ROOT,sha,save_json,props,source,read_object,solid
from develop_cosmetic_joints import refine_pair,cross_section
from preserve_unchanged_plates import read
from validate_print_project import TOKEN


def segments(text,ids,single_object=False):
    # Single-object production plates may omit object labels. The caller must
    # establish that there is exactly one model before enabling this mode.
    if single_object:assert len(ids)==1
    model=collections.defaultdict(list);feature='Custom';current=next(iter(ids)) if single_object else None
    x=y=z=e=0.;relative=False;xyz=False;tool=None
    for line in text.splitlines():
        if line.startswith('; start printing object, unique label id: '):current=int(line.rsplit(': ',1)[1])
        elif line.startswith('; stop printing object, unique label id: '):current=None
        elif line.startswith('; FEATURE: '):feature=line.split(': ',1)[1]
        code=line.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd in ['T0','T1','T2','T3']:tool=int(cmd[1:])+1
        elif cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ['G90','G91']:xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[o+v.get(k,0) if xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if relative else v.get('E',e)-e
            if cmd in ['G1','G2','G3'] and de>0 and current in ids and feature not in ['Custom','Support','Support interface','Brim','Skirt','Prime tower']:
                if cmd=='G1':
                    if math.hypot(nx-x,ny-y)>1e-6:model[ids[current]].append((tool,feature,[[x,y,z],[nx,ny,nz]]))
                else:
                    cx,cy=x+v.get('I',0),y+v.get('J',0)
                    radius=math.hypot(x-cx,y-cy);aa=math.atan2(y-cy,x-cx);bb=math.atan2(ny-cy,nx-cx)
                    span=((bb-aa) if cmd=='G3' else (aa-bb))%(2*math.pi)
                    if span<1e-8:span=2*math.pi
                    count=max(2,math.ceil(span*radius/.15))
                    angles=aa+np.linspace(0,span,count+1)*(1 if cmd=='G3' else -1)
                    pts=np.column_stack([cx+radius*np.cos(angles),cy+radius*np.sin(angles),np.linspace(z,nz,count+1)])
                    for start,end in zip(pts[:-1],pts[1:]):model[ids[current]].append((tool,feature,[start,end]))
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if relative else v.get('E',e)
    return model


def run(native):
    files=read(native/'sliced.3mf');cfg=ET.fromstring(files['Metadata/model_settings.config']);ids={}
    for plate in cfg.findall('plate'):
        for instance in plate.findall('model_instance'):
            p=props(instance);s=props(cfg.find(f"object[@id='{p['object_id']}']"))
            if s['name'].startswith('Zero-gap refined'):ids[int(p['identify_id'])]=s['name']
    lines=segments((native/'plate_3.gcode').read_text(),ids)
    guide=json.loads((OUT/'All-Development-Tests-A1.json').read_text())
    datum=json.loads((OUT/'Frame-coupon-validation.json').read_text())['variants'][0]['bed_datum_revision']
    rows={r['name']:r for r in guide['records'] if r['plate']==3};contacts=[];heights=[]
    for name,row in rows.items():
        t=np.array(row['assembly_to_printer']);socket=name.endswith('socket')
        raw=lines[name];a=np.array([r[2] for r in raw]);tools=np.array([r[0] for r in raw])
        positions=datum['datum_feet_xy_mm']+[[9,-33.6],[9,33.6]]
        for index,p in enumerate(positions):
            target=np.array([*p,.8])@t[:3,:3].T+t[:3,3]
            # Socket feet and skirts must actually extrude on layer one; the
            # mating tongue floors must actually finish on their Z0.8 plane.
            target[2]=.2 if socket else .8
            pool=a[abs(a[:,1,2]-target[2])<.001];assert len(pool)
            delta=pool[:,1]-pool[:,0];start=pool[:,0]
            along=np.clip(np.sum((target-start)*delta,axis=1)/np.sum(delta*delta,axis=1),0,1)
            distance=float(np.linalg.norm(start+along[:,None]*delta-target,axis=1).min())
            # Circular feet may print as concentric perimeters rather than a
            # line through an arbitrary point. Require a surrounding bearing
            # footprint at this exact layer, with supports excluded.
            patch=Point(*target[:2]).buffer(1.6)
            paths=shapely.intersection(shapely.linestrings(pool[:,:,:2]),patch)
            paths=paths[~shapely.is_empty(paths)];assert len(paths),(name,p)
            bearing=shapely.union_all(paths).buffer(.15).convex_hull
            assert bearing.area>(2.5 if index<3 else .6),(name,p,bearing.area)
            assert bearing.distance(Point(*target[:2]))<.2,(name,p,'Bearing footprint displaced')
            contacts.append(dict(part=name,xy_assembly_mm=p,print_z_mm=float(target[2]),
                probe_distance_to_model_extrusion_mm=distance,bearing_span_area_mm2=float(bearing.area),support_extrusion_excluded=True))
        for slot,expected in [(1,13.6),(2,10.0),(4,13.6)]:
            selected=a[tools==slot];assert len(selected),(name,slot)
            maximum=float(selected[:,:,2].max()-t[2,3])
            assert abs(maximum-expected)<.001,(name,slot,maximum,expected)
            heights.append(dict(part=name,filament=slot,assembled_maximum_extrusion_z_mm=maximum))
    preserved=json.loads((OUT/'Zero-gap-plate-preservation.json').read_text())
    assert {r['plate'] for r in preserved['plates']}=={1,2}
    assert preserved['project_sha256']==sha(native/'sliced.3mf')
    # Retain the successful locating-key fit; only their supported ceilings
    # gained headroom. Compare actual cross sections against the prior design.
    original=source();aa,_=read_object(original,'209');bb,_=read_object(original,'213')
    prior,_=refine_pair(aa,bb,[0,1,[0,0],0,68,[-22.6530323,22.3469677]],gap=0)
    current=read(OUT/'Frame-Cosmetic-Comparison-A1.3mf')
    mask=shapely.union_all([shapely.box(1.5,y-3,17,y+3) for y in [-22.6530323,22.3469677]])
    fits=[]
    for entries,oid in zip(prior,['1000','1100']):
        before=cross_section(solid(entries[0]['mesh']),5.8).intersection(mask)
        after=cross_section(solid(read_object(current,oid)[0][0]['mesh']),5.8).intersection(mask)
        error=before.symmetric_difference(after).area
        assert error<1e-5,('Locating-key XY fit changed',oid,error)
        fits.append(float(error))
    report=dict(revision='bed-datum-ribbon-v1',project_sha256=sha(native/'sliced.3mf'),
        geometry_validation_sha256=sha(OUT/'Frame-coupon-validation.json'),
        datum_and_outer_skirt_native_checks=contacts,actual_surface_heights=heights,
        preserved_complete_plates=[1,2],nominal_visible_side_gap_mm=0,
        locating_key_fit_section_difference_mm2=fits,
        supported_bulk_is_not_a_seating_reference=True,physical_fit_flushness_and_strength_pending=True)
    save_json(OUT/'Ribbon-bed-datum-native-validation.json',report)
    print('PASS: 10 bed/floor probes; white, wood and blue finish heights match; plates 1 and 2 preserved.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('native',type=Path);run(p.parse_args().native)
