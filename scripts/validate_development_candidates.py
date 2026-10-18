"""Audit native development slices before publishing them beside the CAD.

Compare native round-trip geometry and plate-local poses, bead-inclusive bed
bounds, filament slots and finish-direction evidence. Never sends a print.
"""
import argparse
import collections
import json
import math
import shutil
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree

from development_3mf import ROOT, OUT, source, save_json, sha, tag, P, transform, props, read_object, solid
from validate_print_project import scan_gcode, TOKEN


def project_geometry(path):
    with zipfile.ZipFile(path) as z:f={n:z.read(n) for n in z.namelist()}
    cfg=ET.fromstring(f['Metadata/model_settings.config']);r=ET.fromstring(f['3D/3dmodel.model'])
    plates=cfg.findall('plate');columns=math.ceil(math.sqrt(len(plates)));result={}
    for i,plate in enumerate(plates):
        for inst in plate.findall('model_instance'):
            oid=props(inst)['object_id'];es,st=read_object(f,oid)
            t=transform(r.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']").get('transform'))
            t[:2,3]-=[i%columns*307.2,-(i//columns)*307.2]
            points=[]
            for p in es:
                if p['subtype']=='normal_part':points.append(p['mesh'].vertices@t[:3,:3].T+t[:3,3])
            result[st['name']]=np.vstack(points)
    return result


def coupon_connectivity(path):
    """A printable coupon must not conceal loose chunks in one object."""
    with zipfile.ZipFile(path) as z:files={n:z.read(n) for n in z.namelist()}
    rows=[]
    for obj in ET.fromstring(files['Metadata/model_settings.config']).findall('object'):
        parts,settings=read_object(files,obj.get('id'))
        for part in parts:
            if part['subtype']!='normal_part':continue
            components=solid(part['mesh']).decompose()
            # Re-reading rounded 3MF vertices can expose coplanar boolean sheets
            # of effectively zero volume. A real cropped-off chunk must fail.
            count=sum(abs(c.volume())>=1e-8 for c in components)
            assert count==1,(path.name,settings['name'],'Disconnected printed chunks',count)
            rows.append(dict(name=settings['name'],connected_components=count,
                             numerical_zero_volume_shells=len(components)-count,
                             excluded_absolute_volume_mm3=sum(abs(c.volume()) for c in components if abs(c.volume())<1e-8)))
    return rows


def angle_evidence(text,rotation=None):
    feature='Custom';x=y=z=e=0.;rel_e=False;rel_xyz=False;angles=[collections.Counter(),collections.Counter()]
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=='M83':rel_e=True
        elif cmd=='M82':rel_e=False
        elif cmd in ('G90','G91'):rel_xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[v.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ('G0','G1','G2','G3'):
            nx,ny,nz=[o+v.get(k,0) if rel_xyz else v.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=v.get('E',0) if rel_e else v.get('E',e)-e
            length=math.hypot(nx-x,ny-y)
            if feature=='Top surface' and de>0 and length>3 and nz>13.3 and cmd=='G1':
                side=0 if rotation is not None or (x+nx)/2<128 else 1
                yaw=rotation if rotation is not None else [17,67][side]
                a=round((math.degrees(math.atan2(ny-y,nx-x))-yaw)%180,1)
                angles[side][a]+=length
            x,y,z=nx,ny,nz;e=e+v.get('E',0) if rel_e else v.get('E',e)
    return [c.most_common(5) for c in angles]


def coupon_material_angles(text):
    """Compare matching color/height groups, including the three weave levels."""
    feature='Custom';x=y=z=e=0.;relative=False;xyz=False;tool=None;groups=collections.defaultdict(lambda:[collections.Counter(),collections.Counter()])
    for raw in text.splitlines():
        if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
        code=raw.split(';',1)[0].strip()
        if not code:continue
        cmd=code.split()[0];values={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd in ['T0','T1','T2','T3']:tool=int(cmd[1:])+1
        elif cmd=='M83':relative=True
        elif cmd=='M82':relative=False
        elif cmd in ['G90','G91']:xyz=cmd=='G91'
        elif cmd=='G92':x,y,z,e=[values.get(k,o) for k,o in zip('XYZE',(x,y,z,e))]
        elif cmd in ['G0','G1','G2','G3']:
            nx,ny,nz=[o+values.get(k,0) if xyz else values.get(k,o) for k,o in zip('XYZ',(x,y,z))]
            de=values.get('E',0) if relative else values.get('E',e)-e;length=math.hypot(nx-x,ny-y)
            if feature=='Top surface' and de>0 and length>.5 and cmd=='G1' and tool in [1,2,4]:
                side=0 if (x+nx)/2<128 else 1
                angle=(math.degrees(math.atan2(ny-y,nx-x))-[17,67][side])%180
                angle=round(angle*2)/2
                groups[(tool,round(nz,2))][side][angle]+=length
            x,y,z=nx,ny,nz;e=e+values.get('E',0) if relative else values.get('E',e)
    records=[]
    for (tool,z),cs in sorted(groups.items()):
        if min(sum(c.values()) for c in cs)<10:continue
        angles=[c.most_common(1)[0][0] for c in cs]
        delta=abs((angles[0]-angles[1]+90)%180-90)
        assert delta<1,(tool,z,angles)
        records.append(dict(filament_slot=tool,z_mm=z,dominant_assembly_angles_deg=angles,difference_deg=delta))
    assert any(r['filament_slot']==2 for r in records),'No matching wood weave evidence'
    return records


def validate(name, native):
    staged=OUT/name;export=native/'sliced.3mf'
    result=json.loads((native/'result.json').read_text());assert result['return_code']==0,result
    connectivity=None
    if name in ['M-Veneer-Glue-Coupon-A1.3mf','M-Veneer-Seam-Coupon-A1.3mf','Frame-Cosmetic-Comparison-A1.3mf']:
        connectivity=dict(editable_source=coupon_connectivity(staged),native_export=coupon_connectivity(export))
    before=project_geometry(staged);after=project_geometry(export)
    assert before.keys()==after.keys(),(before.keys(),after.keys())
    geom=[]
    for label,v in before.items():
        q=after[label]
        error=max(float(cKDTree(v).query(q)[0].max()),float(cKDTree(q).query(v)[0].max()))
        assert error<.001,(label,error)
        geom.append(dict(name=label,max_native_vertex_or_pose_error_mm=error))
    gcodes=sorted(native.glob('plate_*.gcode'),key=lambda p:int(p.stem.split('_')[-1]));rows=[]
    assert len(gcodes)==len(result['sliced_plates']),(len(gcodes),len(result['sliced_plates']))
    for p in gcodes:
        text=p.read_text();r=scan_gcode(text)
        assert r['conservative_bed_edge_clearance_mm']>.5,(p.name,r['bead_xy_bounds_mm'])
        assert '; EXECUTABLE_BLOCK_END' in text,p
        r.pop('model_extrusion_z_by_filament_mm',None)
        r.update(plate=int(p.stem.split('_')[-1]),gcode_sha256=sha(p),header=text.split('; HEADER_BLOCK_END')[0].splitlines()[2:13])
        if name=='Frame-Cosmetic-Comparison-A1.3mf' and r['plate']<=4:
            r['top_white_direction_evidence_in_assembly_deg']=angle_evidence(text)
            r['matching_surface_directions_by_color_and_height']=coupon_material_angles(text)
            dominant=[a[0][0] for a in r['top_white_direction_evidence_in_assembly_deg']]
            assert abs((dominant[0]-dominant[1]+90)%180-90)<.2,dominant
            assert all(abs(a-135)<.2 for a in dominant),dominant
        elif name=='Frame-Cosmetic-Candidate-A1.3mf':
            directions=json.loads((OUT/'Frame-full-validation.json').read_text())['directions']
            yaw=directions[r['plate']-1]['bed_rotation_deg']
            evidence=angle_evidence(text,rotation=yaw)[0]
            assert evidence and abs(evidence[0][0]-135)<.2,(r['plate'],evidence)
            r['top_surface_direction_evidence_in_assembly_deg']=evidence
        elif name=='M-Core-and-Veneer-A1.3mf' and r['plate']<=6:
            assert not any(r['features'].get(k,0) for k in ['Support','Support interface']),r
            r['core_support_material_absent']=True
        carrier=None
        if name=='M-Core-and-Veneer-A1.3mf' and r['plate']>6:
            carrier=json.loads((OUT/'M-geometry-validation.json').read_text())['skins'][r['plate']-7]['carrier']
        elif name in ['M-Veneer-Glue-Coupon-A1.3mf','M-Veneer-Seam-Coupon-A1.3mf']:
            seating=json.loads((OUT/(staged.stem+'-seating.json')).read_text())
            if 2<=r['plate']<=len(seating['panels'])+1:carrier=seating['panels'][r['plate']-2]['carrier']
        if carrier and 'bond_probes_print_xyz_mm' in carrier:
            from check_fin_toolpaths import check_fin_bonds
            r['bonded_fin_tooth_toolpath_check']=check_fin_bonds(text,carrier)
        rows.append(r)
    target=OUT/(staged.stem+'-Sliced.3mf');shutil.copyfile(export,target)
    report=dict(source_release_sha256=sha(ROOT/'Dara.3mf'),staged_sha256=sha(staged),native_project_sha256=sha(target),
                native_return_code=0,plate_count=len(gcodes),native_roundtrip_geometry=geom,plates=rows,
                physical_fit_finish_and_support_anchor_test_pending=True)
    if connectivity is not None:report['coupon_connected_components']=connectivity
    save_json(OUT/(staged.stem+'-native-validation.json'),report)
    print(json.dumps(dict(file=str(target),plates=len(rows),minimum_bed_edge_clearance_mm=min(r['conservative_bed_edge_clearance_mm'] for r in rows),max_native_error_mm=max(g['max_native_vertex_or_pose_error_mm'] for g in geom)),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('native',type=__import__('pathlib').Path);args=p.parse_args();validate(args.name,args.native)
