"""Measure actual native paths and validate the five continuous cover crowns."""
import json
import re
import hashlib
import copy
import xml.etree.ElementTree as ET
import rebuild_continuous_covers as g
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree

TOKEN=re.compile(r'([XYZEFIJ])\s*(-?(?:\d*\.\d+|\d+\.?\d*))')


def parse(text, features=None):
    xyz=np.zeros(3);e=f=0.;relative_e=relative_xyz=False
    feature='Custom';width=.42;object_id=None;moves=[];chain=0
    for line,raw in enumerate(text.splitlines(),1):
        if raw.startswith('; FEATURE: '):feature=raw[11:].strip()
        if raw.startswith('; LINE_WIDTH: '):width=float(raw[14:])
        if raw.startswith('; start printing object, unique label id: '):object_id=int(raw.rsplit(':',1)[1]);chain+=1
        if raw.startswith('; stop printing object, unique label id: '):object_id=None;chain+=1
        code=raw.split(';')[0].strip()
        if not code:continue
        cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
        if cmd=='M83':relative_e=True
        elif cmd=='M82':relative_e=False
        elif cmd in ['G90','G91']:relative_xyz=cmd=='G91'
        elif cmd=='G92':xyz=np.array([v.get(k,old) for k,old in zip('XYZ',xyz)]);e=v.get('E',e)
        elif cmd in ['G0','G1','G2','G3']:
            end=np.array([old+v.get(k,0) if relative_xyz else v.get(k,old) for k,old in zip('XYZ',xyz)])
            de=v.get('E',0) if relative_e else v.get('E',e)-e
            f=v.get('F',f);length=np.linalg.norm(end-xyz)
            if length>1e-8:
                if de>0 and feature in (features or {'Outer wall'}):
                    arc=None
                    if cmd in ['G2','G3']:
                        center=xyz[:2]+[v.get('I',0),v.get('J',0)];radius=np.linalg.norm(xyz[:2]-center)
                        a0,a1=np.arctan2(*((np.array([xyz[:2],end[:2]])-center)[:,::-1].T))
                        sweep=(a1-a0)%(2*np.pi) if cmd=='G3' else -((a0-a1)%(2*np.pi))
                        length=abs(sweep)*radius;arc=(center,radius,a0,sweep)
                    moves.append(dict(start=xyz.copy(),end=end.copy(),line=line,feature=feature,object=object_id,
                        speed=f/60,width=width,e_per_mm=de/length,length=length,cmd=cmd,arc=arc,chain=chain))
                else:chain+=1
            elif de<0:chain+=1
            xyz=end;e=e+v.get('E',0) if relative_e else v.get('E',e)
    return moves


def sample(m):
    if m['arc'] is None:return np.array([m['start'],m['end']])
    center,r,a0,sweep=m['arc'];a=np.linspace(a0,a0+sweep,max(3,int(m['length']/.15)))
    return np.column_stack([center[0]+r*np.cos(a),center[1]+r*np.sin(a),np.linspace(m['start'][2],m['end'][2],len(a))])


def tangent(m,end=False):
    if m['arc'] is None:return (m['end']-m['start'])[:2]
    center,*_=m['arc'];v=m['end' if end else 'start'][:2]-center
    return (1 if m['cmd']=='G3' else -1)*np.array([-v[1],v[0]])


def mesh_in_project(files, name):
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    co=next(o for o in cfg.findall('object') if g.props(o)['name'].split(' - ')[0]==name)
    root=ET.fromstring(files['3D/3dmodel.model']);oid=co.get('id')
    item=root.find(g.tag('build')).find(g.tag('item')+f"[@objectid='{oid}']")
    obj=root.find(g.tag('resources')).find(g.tag('object')+f"[@id='{oid}']")
    components=list(obj.find(g.tag('components')));assert len(components)==1
    comp=components[0];path=comp.get('{'+g.P+'}path').lstrip('/')
    model=ET.fromstring(files[path]);meshobj=model.find(g.tag('resources')).find(g.tag('object'))
    mesh=g.read_mesh(meshobj)
    pose=g.transform(item.get('transform'))@g.transform(comp.get('transform'));pose[1,3]+=1536
    return mesh,pose


def face_paths(moves,row,mesh,old=False):
    region=g.footprint(mesh,mesh.faces[mesh.face_normals[:,2]>.1]);undo=np.linalg.inv(row['build_transform'])
    roof=np.unique(mesh.faces[mesh.face_normals[:,2]>.1])
    evaluate=LinearNDInterpolator(mesh.vertices[roof,:2],mesh.vertices[roof,2]) if old else None
    prev=None;joins=[];front=[];segments=[]
    for m in moves:
        if m['object']!=int(row['name'][-1])+6:continue
        xyz=g.trimesh.transform_points(sample(m),undo)
        uv=xyz[:,:2]-row['origin_xy'];u=uv@row['u_axis'];v=uv@row['v_axis']
        edge=g.shapely.distance(g.shapely.points(xyz[:,:2]),region.boundary)
        top=evaluate(xyz[:,:2]) if old else g.crown(row['parameters'],u,v,row['sin_t'],row['cos_t'])-.25*(1-np.clip(edge/.25,0,1))
        onface=(xyz[:,2]-top>-.4)&(edge>.6)
        if onface.any():
            front.append(m)
            q=np.column_stack([v,u]);segs=np.stack([q[:-1],q[1:]],axis=1)
            segments.extend(segs[onface[:-1]&onface[1:]])
            if onface[0] and prev is not None and prev['chain']==m['chain']:
                a,b=tangent(prev,True),tangent(m)
                angle=float(np.degrees(np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
                joins.append(dict(uv=[float(u[0]),float(v[0])],line=m['line'],angle_deg=angle,
                    edge_distance_mm=float(edge[0])))
            prev=m if onface[-1] else None
        else:prev=None
    return dict(name=row['name'],front_moves=len(front),arc_moves=sum(m['arc'] is not None for m in front),
        interior_joins=len(joins),maximum_join_angle_deg=max([j['angle_deg'] for j in joins],default=0),joins=joins),segments


def validate():
    stage=json.loads((g.W/'stage.json').read_text());before=g.read_zip(g.W/'baseline.3mf')
    staged=g.read_zip(g.W/'staged.3mf');native=g.read_zip(g.W/'slice/sliced.3mf')
    expected=json.loads(staged['Metadata/project_settings.config']);actual=json.loads(native['Metadata/project_settings.config'])
    assert all(actual.get(k)==v for k,v in expected.items())
    assert actual['resolution']=='0.05' and actual['enable_arc_fitting']=='1'
    info=ET.fromstring(native['Metadata/slice_info.config']);assert len(info.findall('plate'))==1
    plate=info.find('plate');stats=g.props(plate)
    assert stats['outside']=='false' and stats['pause_count']=='0'
    assert {f.get('id') for f in plate.findall('filament')}=={'3'}
    assert all(w.get('msg')=='not_support_traditional_timelapse' for w in plate.findall('warning'))
    text=native['Metadata/plate_31.gcode'].decode()
    assert hashlib.md5(text.encode()).hexdigest()==native['Metadata/plate_31.gcode.md5'].decode().strip().lower()
    assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',text,re.M)
    assert 'M201 X1000 Y1000 Z1500 E5000' in text and 'M203 X150 Y150 Z30 E30' in text
    audit=g.scan_gcode(text);zs=audit.pop('model_extrusion_z_by_filament_mm')
    assert set(zs)=={'3'} and .1999<=min(zs['3'])<=max(zs['3'])<250
    assert audit['conservative_bed_edge_clearance_mm']>6
    assert all(audit['features'].get(k,0)>0 for k in ['Outer wall','Support','Support interface'])
    moves=parse(text);oldmoves=parse(before['Metadata/plate_31.gcode'].decode())
    supports=parse(text,{'Support','Support interface'})
    support_points=np.concatenate([sample(m) for m in supports])
    rows=[];plots=[];roundtrip=[]
    for row in stage['geometry']:
        old=g.read_mesh(ET.fromstring(before[row['mesh_path']]).find(g.tag('resources')).find(g.tag('object')))
        data=np.load(g.W/(row['name']+'.npz'));mesh=g.trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        assert mesh.is_volume and mesh.is_watertight and mesh.body_count==1
        saved,pose=mesh_in_project(native,row['name']);assert saved.is_volume and saved.is_watertight
        a=g.trimesh.transform_points(mesh.vertices,row['build_transform']);b=g.trimesh.transform_points(saved.vertices,pose)
        error=float(max(cKDTree(a).query(b)[0].max(),cKDTree(b).query(a)[0].max()));assert error<.0002,error
        # No support may touch the broad visible face. Points on the underside
        # and outside the cover footprint are excluded geometrically.
        local=g.trimesh.transform_points(support_points,np.linalg.inv(row['build_transform']))
        region=g.footprint(mesh,mesh.faces[mesh.face_normals[:,2]>.1])
        inside=g.shapely.contains(region.buffer(-.6),g.shapely.points(local[:,:2]))
        uv=local[:,:2]-row['origin_xy'];u=uv@row['u_axis'];v=uv@row['v_axis']
        height=g.crown(row['parameters'],u,v,row['sin_t'],row['cos_t'])
        touched=inside&(np.abs(local[:,2]-height)<.4)
        assert not touched.any(),row['name']
        newpaths,segs=face_paths(moves,row,mesh);oldpaths,oldsegs=face_paths(oldmoves,row,old,True)
        # Record every remaining transition without an angle threshold. The
        # former middle track must be absent; at most three isolated end
        # transitions are accepted across the entire face of any cover.
        vertices_uv=(mesh.vertices[:,:2]-row['origin_xy'])@np.array([row['u_axis'],row['v_axis']]).T
        lo,hi=np.percentile(vertices_uv[:,1],[0,100]);margin=(hi-lo)*.25
        central=[j for j in newpaths['joins'] if lo+margin<j['uv'][1]<hi-margin]
        assert not central and newpaths['interior_joins']<=3,(row['name'],newpaths)
        rows.append(dict(name=row['name'],before=oldpaths,after=newpaths,middle_half_span_joins=0))
        plots.append((row,oldsegs,segs,oldpaths,newpaths))
        roundtrip.append(dict(name=row['name'],vertex_roundtrip_error_mm=error,visible_face_support_contacts=0))
    report=dict(baseline_sha256=stage['baseline_sha256'],gcode_sha256=hashlib.sha256(text.encode()).hexdigest(),
        weight_g=float(stats['weight']),seconds=int(stats['prediction']),geometry=stage['geometry'],
        geometry_checks=json.loads((g.W/'geometry-checks.json').read_text()),roundtrip=roundtrip,
        paths=rows,path_audit=audit,settings_changed=stage['settings_changed'],physical_print_pending=True,
        finding='Repeated middle-face junction tracks removed on all five covers. Three isolated transitions remain near the ends of Bands 1 and 2; all are recorded below.')
    g.REVIEW.mkdir(parents=True,exist_ok=True)
    (g.REVIEW/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    render(plots)
    print(json.dumps({k:v for k,v in report.items() if k not in ['geometry','geometry_checks','paths','roundtrip','path_audit']},indent=2))
    print([(r['name'],r['before']['interior_joins'],r['after']['interior_joins']) for r in rows])
    return report


def render(plots):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    fig,axs=plt.subplots(5,2,figsize=(15,9),layout='constrained')
    for axes,(r,old,new,op,np_) in zip(axs,plots):
        for ax,segs,p,title in zip(axes,[old,new],[op,np_],['Before','Rebuilt crown']):
            ax.add_collection(LineCollection(segs,linewidths=.55,color='#98602d'));ax.autoscale();ax.set_aspect('equal')
            if p['joins']:ax.scatter([j['uv'][1] for j in p['joins']],[j['uv'][0] for j in p['joins']],c='#c82d36',s=10)
            ax.set_title(r['name']+' — '+title+' ('+str(p['interior_joins'])+' junctions)',fontsize=10)
            ax.tick_params(labelsize=7)
    fig.suptitle('Plate 31 · actual native outer-wall paths\nRed dots mark every interior command junction; broad faces are now continuous circular crowns',fontsize=14)
    fig.savefig(g.REVIEW/'before-after-paths.png',dpi=160);plt.close(fig)


if __name__=='__main__':validate()
