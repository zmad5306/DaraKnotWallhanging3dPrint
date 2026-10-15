"""Replace Plate 31 show faces with single circular-section crowns.

Each crown has a linear slope across its width and one unbroken circular
profile along its length. Its scale is chosen so horizontal print sections
are circles in the saved print orientation. The seating surfaces and footprint
are preserved within 0.0002 mm, and the 0.25 mm edge bevel is retained.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.work/python-libs'))
import numpy as np
import trimesh
import shapely
import manifold3d
from shapely.ops import polygonize
from scipy.interpolate import LinearNDInterpolator
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from validate_print_project import transform, props, scan_gcode
from colorize_print_project import read_mesh

C = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P = 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
ET.register_namespace('', C)
ET.register_namespace('p', P)
tag = lambda name: '{'+C+'}'+name
W = ROOT / '.work/continuous-covers'
REVIEW = ROOT / 'working/review/continuous-covers'
PRODUCTION = ROOT / 'Dara.3mf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        return {k: z.read(k) for k in z.namelist()}


def write_zip(path, files):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for k, value in files.items():
            z.writestr(k, value)


def xml(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def footprint(mesh, faces):
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    unique, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    lines = [shapely.LineString(mesh.vertices[e, :2]) for e in unique[counts == 1]]
    region = shapely.union_all(list(polygonize(lines)))
    assert region.geom_type == 'Polygon' and region.is_valid and not region.interiors
    return region


def crown(params, u, v, sin_t, cos_t):
    slope, height, radius, center = params
    d = sin_t + slope*cos_t
    q = v-center
    # Stable evaluation of sqrt(R**2-q**2)-R for large radii.
    return slope*u + height - d*q*q/(radius+np.sqrt(np.maximum(radius*radius-q*q, 1e-9)))


def ruled_roof(mesh, roof_ids, region, params, origin, u_axis, v_axis, sin_t, cos_t):
    """Use straight generators across the width, without an XY patch grid."""
    uv_region=shapely.transform(region,lambda p:(p-origin)@np.column_stack([u_axis,v_axis]))
    # Put the new envelope 10 nm inside the old cutter boundary to avoid
    # coincident-wall Boolean slivers. This is below source export precision.
    uv_region=shapely.set_precision(uv_region.buffer(-.00001),1e-9)
    core=uv_region.buffer(-.25)
    lo=np.array(uv_region.bounds[:2]);hi=np.array(uv_region.bounds[2:])
    # Uniform circular chords: <=0.0005 mm sag for radii above 250 mm.
    # Excessively short chords are nearly collinear to the native arc fitter.
    step=min(1.,np.sqrt(8*params[2]*.0004))
    ys=np.arange(np.floor(lo[1]/step)*step,np.ceil(hi[1]/step)*step+.5*step,step)
    strips=shapely.box(np.full(len(ys)-1,lo[0]-1),ys[:-1],np.full(len(ys)-1,hi[0]+1),ys[1:])
    pieces=np.concatenate([shapely.get_parts(shapely.intersection(strips,p)) for p in [core,uv_region.difference(core)]])
    pieces=pieces[shapely.get_type_id(pieces)==3]
    triangles=shapely.get_parts(shapely.constrained_delaunay_triangles(pieces))
    coords=shapely.get_coordinates(triangles).reshape(-1,4,2)[:,:3]
    uv,inv=np.unique(np.round(coords.reshape(-1,2),9),axis=0,return_inverse=True)
    faces=inv.reshape(-1,3)
    a=uv[faces[:,1]]-uv[faces[:,0]];b=uv[faces[:,2]]-uv[faces[:,0]]
    cross=a[:,0]*b[:,1]-a[:,1]*b[:,0]
    faces[cross<0]=faces[cross<0][:,::-1]
    def evaluate(points):
        edge=shapely.distance(shapely.points(points),uv_region.boundary)
        return crown(params,points[:,0],points[:,1],sin_t,cos_t)-.25*(1-np.clip(edge/.25,0,1))
    # Refine the curved bevel corners without adding a patch grid to the face.
    # Shared-edge subdivision keeps the roof conforming and watertight.
    for iteration in range(12):
        z=evaluate(uv)
        pairs=faces[:,[[0,1],[1,2],[2,0]]]
        probes=np.concatenate([uv[faces].mean(axis=1)[:,None,:],uv[pairs].mean(axis=2)],axis=1)
        linear=np.column_stack([z[faces].mean(axis=1),z[pairs].mean(axis=2)])
        error=np.abs(evaluate(probes.reshape(-1,2)).reshape(-1,4)-linear)
        bad=error.max(axis=1)>.0008
        if not bad.any():break
        edges,indices=np.unique(np.sort(pairs.reshape(-1,2),axis=1),axis=0,return_inverse=True)
        indices=indices.reshape(-1,3);marked=np.unique(indices[bad])
        midpoint=np.full(len(edges),-1,dtype=int)
        midpoint[marked]=np.arange(len(uv),len(uv)+len(marked))
        additions=[uv[edges[marked]].mean(axis=1)]
        nextid=len(uv)+len(marked);refined=[]
        for face,edgeids in zip(faces,indices):
            mids=midpoint[edgeids]
            if (mids<0).all():refined.append(face);continue
            ring=[]
            for vertex,mid in zip(face,mids):
                ring.append(vertex)
                if mid>=0:ring.append(mid)
            center=nextid;nextid+=1;additions.append(uv[face].mean(axis=0)[None,:])
            refined.extend([[ring[i],ring[(i+1)%len(ring)],center] for i in range(len(ring))])
        uv=np.concatenate([uv,*additions]);faces=np.asarray(refined)
    else:raise AssertionError('Bevel refinement failed to converge.')
    n=len(uv);xy=origin+uv@np.array([u_axis,v_axis])
    vertices=np.concatenate([np.column_stack([xy,z]),np.column_stack([xy,np.full(n,6.)])])
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    _,ix,count=np.unique(np.sort(edges,axis=1),axis=0,return_index=True,return_counts=True)
    boundary=edges[ix[count==1]]
    side=np.concatenate([np.column_stack([boundary[:,0],boundary[:,0]+n,boundary[:,1]+n]),np.column_stack([boundary[:,0],boundary[:,1]+n,boundary[:,1]])])
    faces=np.concatenate([faces,(faces+n)[:,::-1],side])
    if np.linalg.det(np.array([u_axis,v_axis]))<0:faces=faces[:,::-1]
    upper=trimesh.Trimesh(vertices,faces,process=True)
    assert upper.is_volume and upper.is_watertight
    lower=mesh.copy();lv=lower.vertices.copy();lv[roof_ids,2]=5.;lower.vertices=lv;lower.invert()
    assert lower.is_volume
    def solid(m):return manifold3d.Manifold(manifold3d.Mesh64(m.vertices,np.array(m.faces,dtype=np.uint64)))
    cut=solid(upper)-solid(lower)
    parts=sorted(cut.decompose(),key=lambda p:abs(p.volume()),reverse=True)
    # Discard only numerical boundary fragments, less than 0.0001 mm3 total.
    assert sum(abs(p.volume()) for p in parts[1:])<1e-4
    raw=parts[0].to_mesh64()
    result=trimesh.Trimesh(raw.vert_properties[:,:3],raw.tri_verts,process=False)
    assert result.is_volume and result.is_watertight and result.body_count==1
    assert result.bounds[0,2]>=mesh.bounds[0,2]-1e-6
    return result


def rebuild(mesh, pose):
    roof_faces = mesh.faces[mesh.face_normals[:, 2] > .1]
    roof_ids = np.unique(roof_faces)
    floor_ids = np.unique(mesh.faces[mesh.face_normals[:, 2] < -.1])
    assert not np.intersect1d(roof_ids, floor_ids).size
    region = footprint(mesh, roof_faces)
    xy = mesh.vertices[roof_ids, :2]
    sin_t = np.linalg.norm(pose[2, :2]); cos_t = pose[2, 2]
    u_axis = pose[2, :2]/sin_t
    v_axis = pose[1, :2]
    assert abs(pose[1, 2]) < 1e-8 and abs(np.linalg.norm(v_axis)-1) < 1e-8
    origin = (xy.min(axis=0)+xy.max(axis=0))/2
    u = (xy-origin)@u_axis; v = (xy-origin)@v_axis
    distance = shapely.distance(shapely.points(xy), region.boundary)
    bevel = .25*(1-np.clip(distance/.25, 0, 1))
    target = mesh.vertices[roof_ids, 2]+bevel
    # Sample uniformly in the face, so dense bevel/corner triangles do not
    # overwhelm the fit. The complete vertex set is checked below.
    cells = np.round(np.column_stack([u, v])/.4).astype(int)
    _, ids = np.unique(cells, axis=0, return_index=True)
    U, V, Z = u[ids], v[ids], target[ids]
    coef = np.linalg.lstsq(np.column_stack([U, np.ones(len(U)), V, V*V]), Z, rcond=None)[0]
    span = float(np.ptp(v)); limit = span*1.5
    radius0 = np.clip(-sin_t/(2*min(coef[3], -1e-6)), limit, 5000)
    center0 = np.clip(coef[2]*radius0/sin_t, -span*.5, span*.5)
    p0 = [np.clip(coef[0], -.2, .2), float(Z.mean()), radius0, center0]
    fit = least_squares(lambda p: crown(p,U,V,sin_t,cos_t)-Z, p0,
        bounds=([-.3, 6, limit, -span*.5], [.3, 20, 10000, span*.5]),
        x_scale='jac', ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=500)
    assert fit.success, fit.message
    params = fit.x
    underside = LinearNDInterpolator(mesh.vertices[floor_ids, :2], mesh.vertices[floor_ids, 2])
    floor_z = underside(xy)
    valid = np.isfinite(floor_z)
    assert valid.mean() > .98
    new_z = crown(params,u,v,sin_t,cos_t)-bevel
    # Keep at least the former nominal skin thickness through the broad face;
    # retain the quarter-mm bevel and a minimum 0.95 mm skin at its rim.
    required = 1.20-bevel
    lift = float(np.max((floor_z+required-new_z)[valid]))+.005
    params[1] += lift
    new_z = crown(params,u,v,sin_t,cos_t)-bevel
    result = mesh.copy()
    vertices = result.vertices.copy(); vertices[roof_ids,2] = new_z; result.vertices = vertices
    assert result.is_volume and result.is_watertight and result.body_count == 1
    assert np.array_equal(result.vertices[floor_ids], mesh.vertices[floor_ids])
    delta = new_z-mesh.vertices[roof_ids,2]
    if params[2]>200:
        result=ruled_roof(mesh,roof_ids,region,params,origin,u_axis,v_axis,sin_t,cos_t)
    checks = dict(parameters=params.tolist(),origin_xy=origin.tolist(),u_axis=u_axis.tolist(),v_axis=v_axis.tolist(),
        sin_t=float(sin_t),cos_t=float(cos_t),roof_vertices=len(roof_ids),floor_vertices=len(floor_ids),
        source_triangles=len(mesh.faces),triangles=len(result.faces),volume_mm3=float(result.volume),
        top_change_mm=[float(delta.min()),float(delta.max())],
        sampled_thickness_mm=[float((new_z-floor_z)[valid].min()),float((new_z-floor_z)[valid].max())],
        underside_vertices_identical=bool(params[2]<=200),underside_surface_preserved=True,
        footprint_tolerance_mm=0 if params[2]<=200 else .00002,watertight=True,bodies=1)
    return result, roof_ids, checks


def geometry():
    W.mkdir(exist_ok=True); REVIEW.mkdir(parents=True,exist_ok=True)
    baseline = W/'baseline.3mf'
    if not baseline.exists(): baseline.write_bytes(PRODUCTION.read_bytes())
    assert sha(baseline) == sha(PRODUCTION), 'Production changed after staging.'
    files = read_zip(baseline)
    root=ET.fromstring(files['3D/3dmodel.model']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    plate=next(p for p in cfg.findall('plate') if props(p).get('plater_id')=='31')
    ids={props(m)['object_id'] for m in plate.findall('model_instance')}
    rows=[]
    for item in root.find(tag('build')):
        if item.get('objectid') not in ids: continue
        obj=root.find(tag('resources')).find(tag('object')+f"[@id='{item.get('objectid')}']")
        components=list(obj.find(tag('components')));assert len(components)==1
        comp=components[0];assert np.array_equal(transform(comp.get('transform')),np.eye(4))
        path=comp.get('{'+P+'}path').lstrip('/')
        child=ET.fromstring(files[path]);meshobj=child.find(tag('resources')).find(tag('object'))
        mesh=read_mesh(meshobj);pose=transform(item.get('transform'));pose[1,3]+=1536
        changed,roof_ids,checks=rebuild(mesh,pose)
        vertices=meshobj.find(tag('mesh')).find(tag('vertices'))
        if checks['underside_vertices_identical']:
            for idx in roof_ids:vertices[idx].set('z',format(changed.vertices[idx,2],'.12g'))
        else:
            vertices.clear()
            for v in changed.vertices:ET.SubElement(vertices,tag('vertex'),**{k:format(x,'.12g') for k,x in zip('xyz',v)})
            triangles=meshobj.find(tag('mesh')).find(tag('triangles'));triangles.clear()
            front=changed.face_normals[:,2]>-.01
            enforce=(changed.face_normals@pose[:3,:3].T)[:,2]<-.1
            for idx,f in enumerate(changed.faces):
                attrs={k:str(v) for k,v in zip(['v1','v2','v3'],f)}
                if front[idx] or enforce[idx]:attrs['paint_supports']='8' if front[idx] else '4'
                ET.SubElement(triangles,tag('triangle'),**attrs)
        # Keep the production namespace declaration required by the 3MF.
        if 'xmlns:p' not in child.attrib:child.set('xmlns:p',P)
        files[path]=xml(child)
        co=cfg.find(f"object[@id='{item.get('objectid')}']")
        co.find('part').find('mesh_stat').set('face_count',str(len(changed.faces)))
        name=props(co)['name'].split(' - ')[0]
        checks.update(name=name,mesh_path=path,object_id=item.get('objectid'),build_transform=pose.tolist())
        np.savez_compressed(W/(name+'.npz'),vertices=changed.vertices,faces=changed.faces)
        rows.append(checks);print(json.dumps(checks),flush=True)
    files['Metadata/model_settings.config']=xml(cfg)
    settings=json.loads(files['Metadata/project_settings.config'])
    settings['resolution']='0.05'
    files['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
    write_zip(W/'staged.3mf',files)
    report=dict(baseline_sha256=sha(baseline),geometry=rows,settings_changed={'resolution':['0.012','0.05']},
        design='One circular-section crown per cover, linearly swept across its width; same seating surface and perimeter bevel.')
    (W/'stage.json').write_text(json.dumps(report,indent=2)+'\n')


def slice_native():
    out=W/'slice';out.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'cli.log').open('w') as log:
        p=subprocess.run([str(exe),'--slice','31','--export-3mf','sliced.3mf','--outputdir',str(out),str(W/'staged.3mf')],
            cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print('Native slice exit:',p.returncode,flush=True);p.check_returncode()


def check_geometry():
    stage=json.loads((W/'stage.json').read_text());before=read_zip(W/'baseline.3mf');rows=[]
    for r in stage['geometry']:
        original=read_mesh(ET.fromstring(before[r['mesh_path']]).find(tag('resources')).find(tag('object')))
        data=np.load(W/(r['name']+'.npz'));new=trimesh.Trimesh(data['vertices'],data['faces'],process=False)
        old_region=footprint(original,original.faces[original.face_normals[:,2]>.1])
        new_region=footprint(new,new.faces[new.face_normals[:,2]>.1])
        boundary_error=float(old_region.boundary.hausdorff_distance(new_region.boundary))
        assert boundary_error<.0001,boundary_error
        worst=0.
        for source,target in [(original,new),(new,original)]:
            st=source.triangles[source.face_normals[:,2]<-.1];tt=target.triangles[target.face_normals[:,2]<-.1]
            points=np.concatenate([np.unique(st.reshape(-1,3),axis=0),st.mean(axis=1)])
            _,near=cKDTree(tt.mean(axis=1)).query(points,k=16)
            closest=trimesh.triangles.closest_point(tt[near].reshape(-1,3,3),np.repeat(points,16,axis=0))
            dist=np.linalg.norm(closest-np.repeat(points,16,axis=0),axis=1).reshape(-1,16).min(axis=1)
            for j in np.where(dist>.00015)[0]:
                q=np.broadcast_to(points[j],(len(tt),3));dist[j]=np.linalg.norm(trimesh.triangles.closest_point(tt,q)-q,axis=1).min()
            worst=max(worst,float(dist.max()))
        assert worst<.0002,worst
        tri=new.triangles[new.face_normals[:,2]>.1]
        points=np.concatenate([tri.mean(axis=1)[:,None,:],(tri+np.roll(tri,-1,axis=1))/2],axis=1).reshape(-1,3)
        uv=points[:,:2]-r['origin_xy'];u=uv@r['u_axis'];v=uv@r['v_axis']
        edge=shapely.distance(shapely.points(points[:,:2]),new_region.boundary)
        intended=crown(r['parameters'],u,v,r['sin_t'],r['cos_t'])-.25*(1-np.clip(edge/.25,0,1))
        err=np.abs(points[:,2]-intended)
        assert err.max()<.00101,float(err.max())
        core=err[edge>.5]
        row=dict(name=r['name'],underside_max_distance_mm=worst,footprint_max_distance_mm=boundary_error,
            sampled_top_error_mm=float(err.max()),sampled_core_error_mm=float(core.max()),sample_count=len(points))
        rows.append(row);print(row,flush=True)
    (W/'geometry-checks.json').write_text(json.dumps(rows,indent=2)+'\n')


def publish():
    """Merge only the verified covers and Plate 31 slice into the full project."""
    validation=json.loads((REVIEW/'validation.json').read_text())
    stage=json.loads((W/'stage.json').read_text())
    assert sha(PRODUCTION)==stage['baseline_sha256']==validation['baseline_sha256']
    baseline=read_zip(W/'baseline.3mf');files=read_zip(W/'staged.3mf')
    native=read_zip(W/'slice/sliced.3mf')
    changed_meshes={r['mesh_path'] for r in stage['geometry']}
    allowed=changed_meshes|{'Metadata/model_settings.config','Metadata/project_settings.config'}
    assert set(files)==set(baseline)
    assert {k for k in files if files[k]!=baseline[k]}<=allowed
    previous_settings=json.loads(baseline['Metadata/project_settings.config'])
    settings=json.loads(files['Metadata/project_settings.config'])
    assert {k for k in settings if settings[k]!=previous_settings[k]}=={'resolution'}
    cfg=ET.fromstring(files['Metadata/model_settings.config'])
    oldcfg=ET.fromstring(baseline['Metadata/model_settings.config'])
    changed_ids={r['object_id'] for r in stage['geometry']}
    for obj,old in zip(cfg.findall('object'),oldcfg.findall('object')):
        if obj.get('id') not in changed_ids:assert xml(obj)==xml(old)
    assert [xml(p) for p in cfg.findall('plate')]==[xml(p) for p in oldcfg.findall('plate')]
    # Native CLI exports only the sliced meshes, with new IDs. Keep the full
    # original object/build graph and merge its matching identify_id slice.
    for key,value in native.items():
        if re.fullmatch(r'Metadata/(?:plate_31(?:_small)?|plate_no_light_31|top_31|pick_31)\.(?:png|json|gcode(?:\.md5)?)',key):
            files[key]=value
    data=files['Metadata/plate_31.gcode']
    assert hashlib.sha256(data).hexdigest()==validation['gcode_sha256']
    info=ET.fromstring(baseline['Metadata/slice_info.config'])
    replacement=ET.fromstring(native['Metadata/slice_info.config']).find('plate')
    replacement.find("metadata[@key='printer_model_id']").set('value','N2S')
    original=next(p for p in info.findall('plate') if props(p)['index']=='31')
    at=list(info).index(original);info.remove(original);info.insert(at,replacement)
    files['Metadata/slice_info.config']=xml(info)
    unchanged=[];estimates=[]
    for plate in info.findall('plate'):
        values=props(plate);n=int(values['index']);key=f'Metadata/plate_{n}.gcode'
        estimate=dict(plate=n,weight_g=float(values['weight']),seconds=int(values['prediction']))
        estimates.append(estimate)
        if n!=31:
            assert files[key]==baseline[key]
            unchanged.append(dict(plate=n,gcode_sha256=hashlib.sha256(files[key]).hexdigest()))
    target=W/'release.3mf';write_zip(target,files)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    package=ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed'
    mirror=package/'Dara-Photo-Frame-A1-Complete.3mf'
    assert sha(mirror)==stage['baseline_sha256']
    report=dict(project_sha256=sha(target),baseline_sha256=stage['baseline_sha256'],plates=32,objects=47,instances=78,
        changed_plates=[dict(plate=31,gcode_sha256=validation['gcode_sha256'],weight_g=validation['weight_g'],
            seconds=validation['seconds'],path_audit=validation['path_audit'],
            axis_limit_commands=['M201 X1000 Y1000 Z1500 E5000','M203 X150 Y150 Z30 E30'])],
        unchanged_native_plates=unchanged,geometry_checks=validation['geometry'],mesh_checks=validation['geometry_checks'],
        native_roundtrip_checks=validation['roundtrip'],surface_path_checks=validation['paths'],
        settings_changed=stage['settings_changed'],precision_settings={'enable_arc_fitting':'1','resolution':'0.05'},
        total_weight_g=round(sum(r['weight_g'] for r in estimates),2),total_seconds=sum(r['seconds'] for r in estimates),
        all_plate_estimates=estimates,physical_test_pending=True,
        scope='Five circular-section cover crowns and a native Plate 31 slice. Seating surfaces preserved within 0.0002 mm. Other 31 saved slices and all other meshes unchanged.',
        cover_finish_status=validation['finding']+' Physical print of this revision pending.',
        resolution_scope='Resolution is a global Bambu process setting, now 0.05 mm. Other saved slices retain their previously validated 0.012 mm paths; re-slicing those plates uses the new resolution.')
    PRODUCTION.write_bytes(target.read_bytes());mirror.write_bytes(target.read_bytes())
    assert sha(PRODUCTION)==sha(mirror)==report['project_sha256']
    (package/'cover-crown-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    validation['project_sha256']=report['project_sha256']
    (REVIEW/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print('Published both production copies. Plate 31:',validation['weight_g'],'g,',validation['seconds'],'seconds.')
    print('All other 31 saved slices and all other meshes are byte-identical.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['geometry','slice','check-geometry','publish']);args=p.parse_args()
    {'geometry':geometry,'slice':slice_native,'check-geometry':check_geometry,'publish':publish}[args.action]()
