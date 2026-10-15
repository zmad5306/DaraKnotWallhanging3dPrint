"""Balanced, covered joints for the hammered M, plus one reusable band test.

Preserve the original artwork and rear mounts. Repartition the M, carry the
reference keyed lap profiles to the new cuts, and add separate smooth bands.
All artifacts are candidates until the small physical band test is accepted.
"""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from prepare_hammered_m_project import (
    ROOT, P, R, IDENTITY, np, trimesh, read_array, model, mesh_object, meta,
    tag, uid, read_zip, write_zip, sha, xml, props, setmeta, transform,
    artwork, section, as_mesh, mesh_slice, boolean, rotation, texture_field,
    scan_gcode, cad_polygon, box, model_entries, support_paths,
)
from build_jointed_bambu_project import cylinder
from shapely.geometry import Point, LineString, box as rect
from shapely.ops import split
from shapely import affinity, union_all
import shapely
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RectBivariateSpline
from y_axis_orientation import choose,TRAVEL,COPPER,BAND_CENTERS,TEST_CENTERS

WORK=ROOT/'.work/hammered-bands'
REVIEW=ROOT/'working/review/hammered-bands'
SOURCE=ROOT/'Dara-Hammered-Close-Seam-Test.3mf'
CAD=ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad'
TITLE='Hammered M - balanced copper cover bands'
TARGET=ROOT/'Dara-Hammered-Bands-Candidate.3mf'
TEST=ROOT/'Dara-Hammered-Band-Test.3mf'
WIDTH=12.; SEAT_WIDTH=13.2; SEAT_DEPTH=.6; GLUE_GAP=.15; THICKNESS=1.2
TIP=.003*25.4
COMMON=rotation(55,(1,0,0))@rotation(1.5)
NUMERICAL_CLEANUP={}
PRESERVED=['Dara.3mf','Dara-Hammered-M-Candidate.3mf','Dara-Hammered-Close-Seam-Test.3mf',
 'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf']


def locate(g,pos,angle):
    return affinity.translate(affinity.rotate(g,angle,origin=(0,0)),*pos)


def layout():
    cad=CAD.read_text(); outline=artwork(cad,'letter_outline')
    # male, female, position, normal angle, local half-span. B1..B5.
    joints=[(2,3,[32.336138117987566,136.58266699147163],57.06125907870988,35),
        (2,1,[-32.336138117987566,136.58266699147163],122.93874092129012,35),
        (4,1,[-257,-65],90,65),(6,3,[257,-65],90,65),(2,5,[0,0],270,48)]
    regions=[outline]
    for male,female,pos,angle,span in joints:
        line=locate(LineString([(0,-span),(0,span)]),pos,angle)
        regions=[p for r in regions for p in split(r,line).geoms]
    refs=[[-230,110],[0,90],[230,110],[-220,-130],[0,-100],[220,-130]]
    regions=[next(r for r in regions if r.contains(Point(*p))) for p in refs]
    assert len({r.wkb for r in regions})==6
    assert outline.symmetric_difference(union_all(regions)).area<1e-7
    for male,female,pos,angle,span in joints:
        gap=locate(rect(-.0375,-span,.0375,span),pos,angle)
        for i in [male-1,female-1]:regions[i]=regions[i].difference(gap)
    return cad,outline,joints,regions


def crown(outline,xy):
    t=np.clip(shapely.distance(shapely.points(xy),outline.boundary)/17.5,0,1)
    return 2.2*(2*t-t*t)


def smooth_cover_crown(outline,region,sigma=1.5,res=.125):
    """A C2 show-face field without the nearest-edge crown's medial creases.

    Keep crown() for the existing M seats and cover undersides. Only the cover
    show face uses this filtered field. Signed distance outside the artwork
    extends the slope through the edge instead of creating an artificial lip.
    Five-sigma padding keeps the filtering boundary outside the actual cover.
    """
    pad=5*sigma+4*res
    lo=np.floor((np.array(region.bounds[:2])-pad)/res)*res
    hi=np.ceil((np.array(region.bounds[2:])+pad)/res)*res
    xs,ys=[np.arange(a,z+res/2,res) for a,z in zip(lo,hi)]
    x,y=np.meshgrid(xs,ys,indexing='ij')
    xy=np.column_stack([x.ravel(),y.ravel()]);points=shapely.points(xy)
    d=shapely.distance(points,outline.boundary)
    d=np.where(shapely.contains(outline,points),d,-d)
    t=np.minimum(d/17.5,1.)
    z=gaussian_filter((2.2*(2*t-t*t)).reshape(x.shape),sigma/res,
                      mode='nearest',truncate=5.)
    spline=RectBivariateSpline(xs,ys,z,kx=3,ky=3,s=0)
    return lambda xy:spline.ev(xy[:,0],xy[:,1])


def envelope(evaluate,bounds,res=.5,bottom=6.6):
    """Closed height field on a global grid; returns an exact solid mesh."""
    lo=np.floor(np.array(bounds[:2])/res)*res-res
    hi=np.ceil(np.array(bounds[2:])/res)*res+res
    xs,ys=[np.arange(a,b+res/2,res) for a,b in zip(lo,hi)]
    xx,yy=np.meshgrid(xs,ys);xy=np.column_stack([xx.ravel(),yy.ravel()]);nx,ny=len(xs),len(ys)
    v=np.column_stack([xy,evaluate(xy)])
    aa=(np.arange(ny-1)[:,None]*nx+np.arange(nx-1)[None,:]).ravel()
    f=np.concatenate([np.column_stack([aa,aa+1,aa+nx+1]),np.column_stack([aa,aa+nx+1,aa+nx])])
    edge=np.array(list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+[(ny-1)*nx+i for i in range(nx-2,-1,-1)]+[j*nx for j in range(ny-2,0,-1)])
    bot=np.arange(len(v),len(v)+len(edge));nxt=np.roll(np.arange(len(bot)),-1);center=len(v)+len(bot)
    vertices=np.concatenate([v,np.column_stack([v[edge,:2],np.full(len(bot),bottom)]),[[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,bottom]]])
    f=np.concatenate([f,np.column_stack([bot,bot[nxt],edge[nxt]]),np.column_stack([bot,edge[nxt],edge]),np.column_stack([np.full(len(bot),center),bot[nxt],bot])])
    result=trimesh.Trimesh(vertices,f,process=False)
    assert result.is_volume
    return result


def prism(shape,height,z=0):return as_mesh(section(shape).extrude(height).translate([0,0,z]))


def band_envelope(region,evaluate,res=.25,bottom=6.6,bevel=.25,tolerance=.001):
    """Sample the cover AFTER cutting its footprint and bevel boundary.

    Sampling the narrow bevel on the regular grid before clipping can create
    scallops almost half a layer high. Constrain both bevel edges first, then
    refine triangles at corners where distance-to-boundary changes direction.
    The underside is still cut with the original seating envelope.
    """
    region=shapely.set_precision(region,1e-9)
    core=shapely.set_precision(region.buffer(-bevel),1e-9)
    lo=np.floor(np.array(region.bounds[:2])/res)*res
    hi=np.ceil(np.array(region.bounds[2:])/res)*res
    xs,ys=[np.arange(a,c+res/2,res) for a,c in zip(lo,hi)]
    xx,yy=np.meshgrid(xs,ys);xy=np.column_stack([xx.ravel(),yy.ravel()]);nx=len(xs)
    a=(np.arange(len(ys)-1)[:,None]*nx+np.arange(nx-1)[None,:]).ravel()
    f=np.concatenate([np.column_stack([a,a+1,a+nx+1]),np.column_stack([a,a+nx+1,a+nx])])
    grid=shapely.set_precision(shapely.polygons(xy[f]),1e-9)
    polygons=np.concatenate([shapely.get_parts(shapely.intersection(grid,part))
                             for part in [core,region.difference(core)]])
    polygons=polygons[shapely.get_type_id(polygons)==3]
    triangles=shapely.get_parts(shapely.constrained_delaunay_triangles(polygons))
    coords=shapely.get_coordinates(triangles).reshape(-1,4,2)[:,:3,:]
    xy,inv=np.unique(np.round(coords.reshape(-1,2),9),axis=0,return_inverse=True)
    f=inv.reshape(-1,3)
    u,v=xy[f[:,1]]-xy[f[:,0]],xy[f[:,2]]-xy[f[:,0]]
    f[u[:,0]*v[:,1]-u[:,1]*v[:,0]<0]=f[u[:,0]*v[:,1]-u[:,1]*v[:,0]<0][:,::-1]
    for iteration in range(12):
        z=evaluate(xy)
        # Midpoints catch an unrepresented crease even if the centroid does not.
        edgepairs=f[:,[[0,1],[1,2],[2,0]]]
        probes=np.concatenate([xy[f].mean(axis=1)[:,None,:],xy[edgepairs].mean(axis=2)],axis=1)
        linear=np.column_stack([z[f].mean(axis=1),z[edgepairs].mean(axis=2)])
        errors=np.abs(evaluate(probes.reshape(-1,2)).reshape(-1,4)-linear)
        bad=errors.max(axis=1)>tolerance
        if not bad.any():break
        edges,indices=np.unique(np.sort(edgepairs.reshape(-1,2),axis=1),axis=0,return_inverse=True)
        indices=indices.reshape(-1,3);marked=np.unique(indices[bad])
        midpoint=np.full(len(edges),-1,dtype=int)
        midpoint[marked]=np.arange(len(xy),len(xy)+len(marked))
        additions=[xy[edges[marked]].mean(axis=1)]
        nextid=len(xy)+len(marked);faces=[]
        for face,edgeids in zip(f,indices):
            mids=midpoint[edgeids]
            if (mids<0).all():faces.append(face);continue
            ring=[]
            for vertex,mid in zip(face,mids):
                ring.append(vertex)
                if mid>=0:ring.append(mid)
            center=nextid;nextid+=1;additions.append(xy[face].mean(axis=0)[None,:])
            faces.extend([[ring[i],ring[(i+1)%len(ring)],center] for i in range(len(ring))])
        xy=np.concatenate([xy,*additions]);f=np.asarray(faces)
    else:raise AssertionError('Cover bevel did not converge to the height tolerance.')
    n=len(xy);vertices=np.concatenate([np.column_stack([xy,z]),np.column_stack([xy,np.full(n,bottom)])])
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    _,ei,ec=np.unique(np.sort(edges,axis=1),axis=0,return_index=True,return_counts=True)
    boundary=edges[ei[ec==1]]
    side=np.concatenate([np.column_stack([boundary[:,0],boundary[:,0]+n,boundary[:,1]+n]),
                         np.column_stack([boundary[:,0],boundary[:,1]+n,boundary[:,1]])])
    result=trimesh.Trimesh(vertices,np.concatenate([f,(f+n)[:,::-1],side]),process=True)
    assert result.is_volume and result.is_watertight and result.body_count==1
    return result


def save_mesh(name,mesh):
    if mesh.body_count!=1:
        components=mesh.split(only_watertight=False)
        valid=[c for c in components if abs(c.volume)>1e-7]
        discarded=[c for c in components if abs(c.volume)<=1e-7]
        assert len(valid)==1,(name,[(c.volume,c.bounds.tolist()) for c in components])
        NUMERICAL_CLEANUP[name]=dict(components=len(discarded),absolute_volume_mm3=float(sum(abs(c.volume) for c in discarded)))
        mesh=valid[0]
    assert mesh.is_volume and mesh.is_watertight and mesh.body_count==1,(name,mesh.is_watertight,mesh.body_count)
    np.savez_compressed(WORK/(name+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
    return mesh


def load_mesh(name):
    a=np.load(WORK/(name+'.npz'))
    return trimesh.Trimesh(a['vertices'],a['faces'],process=False)


def original_parts(cad):
    originals=[]
    for i,p in enumerate(read_array(cad,'M_placements')):
        m=trimesh.load_mesh(ROOT/f'working/stl/Dara-Photo-Frame-A1-Jointed/M{i+1}.stl')
        m.apply_translation([*p[1],-p[3]]);m.apply_transform(rotation(-p[0]));originals.append(m)
    return originals


def mount_cutters(cad):
    """Extract original bores, including the slot/chamfer tessellation."""
    originals=original_parts(cad);cutters=[]
    for kind,key,diam,height in [('screw','screw_mounts',5,8.8),('locator','dowel_mounts',7,3.5)]:
        for idx,h in enumerate(read_array(cad,key)):
            region=cylinder(h[2],diam,height)
            void=boolean([region,originals[h[0]]],'difference')
            assert 40<abs(void.volume)<90,(kind,idx,void.volume)
            cutters.append((kind,h[2],void,region,originals[h[0]]))
    return cutters


def shoulder(cad,j,socket,outline):
    male,female,pos,angle,span=j
    poly=cad_polygon(cad,'tested_socket_void_xz' if socket else 'tested_tongue_xz')
    if not socket:poly=poly.intersection(rect(-2,-1,18-TIP,8))
    m=prism(poly,2*span)
    m.apply_transform(np.array([[1,0,0,0],[0,0,1,-span],[0,1,0,0],[0,0,0,1.]]))
    # Find positions for two complete keys, allowing 3.3 mm-wide pockets.
    local=affinity.rotate(affinity.translate(outline,-pos[0],-pos[1]),-angle,origin=(0,0))
    ranges=[]
    for x in np.linspace(2.1,15.9,15):
        cross=local.intersection(LineString([(x,-span),(x,span)]))
        assert cross.geom_type=='LineString'
        ranges.append((cross.bounds[1],cross.bounds[3]))
    ymin=max(r[0] for r in ranges)+2.;ymax=min(r[1] for r in ranges)-2.
    assert ymax-ymin>10
    ys=[ymin+(ymax-ymin)/3,ymin+2*(ymax-ymin)/3]
    key=cad_polygon(cad,'tested_key_pocket' if socket else 'tested_key')
    if not socket:key=key.intersection(rect(-1,-4,15.75-TIP,4))
    parts=[m]+[prism(affinity.translate(key,0,y),1.36 if socket else 1.21,4.94 if socket else 4.79) for y in ys]
    tool=boolean(parts,'union');t=rotation(angle);t[:2,3]=pos;tool.apply_transform(t)
    # Socket cutters intentionally extend through the outer contour. Clipping
    # a subtractive cutter to the exact same tessellation creates coincident
    # side faces; keeping the excess outside the body avoids that ambiguity.
    if not socket:tool=boolean([tool,prism(outline,7,-.1)],'intersection')
    return tool,ys


def best_transform(mesh):
    # Always put the face plane along the A1 bed's Y motion. Fit the part by
    # rolling within that plane, never by yawing its weak direction into Y.
    t,extent,in_plane=choose(mesh)
    return t,extent,90.


def geometry():
    WORK.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
    cad,outline,joints,regions=layout();field=texture_field(outline)
    seats=[locate(rect(-SEAT_WIDTH/2,-j[4],SEAT_WIDTH/2,j[4]),j[2],j[3]).intersection(outline) for j in joints]
    def roof(xy):return 10.5+field(xy)
    # Cut the seat boundaries with exact planar sides. Encoding a sharp seat
    # step in the half-mm height grid would leave stair-stepped ledges.
    seat_cutters=[boolean([prism(seat,6,9),envelope(lambda xy:10.5+crown(outline,xy)-SEAT_DEPTH,seat.bounds)],'difference') for seat in seats]
    holes=mount_cutters(cad);tools=[];jointrows=[]
    for idx,j in enumerate(joints,1):
        tongue,ys=shoulder(cad,j,False,outline);socket,_=shoulder(cad,j,True,outline)
        tools.append((tongue,socket))
        jointrows.append(dict(band=f'B{idx}',male=f'M{j[0]}',female=f'M{j[1]}',xy_mm=j[2],normal_angle_deg=j[3],key_y_mm=ys))
    bodies=[];rows=[]
    for n,region in enumerate(regions,1):
        lower=prism(region,6.7)
        upper=boolean([envelope(roof,region.bounds),prism(region,8,6.6)],'intersection')
        body=boolean([lower,upper],'union')
        for seat,cutter in zip(seats,seat_cutters):
            if region.intersects(seat):body=boolean([body,cutter],'difference')
        for j,(tongue,socket) in zip(joints,tools):
            if j[0]==n:body=boolean([body,tongue],'union')
            if j[1]==n:body=boolean([body,socket],'difference')
        for kind,xy,void,_,_ in holes:
            if region.buffer(20).contains(Point(*xy)):body=boolean([body,void],'difference')
        body=save_mesh(f'M{n}',body);bodies.append(body)
        t,extent,yaw=best_transform(body)
        row=dict(name=f'M{n}',watertight=True,components=1,triangles=len(body.faces),volume_mm3=float(body.volume),
            bounds_mm=body.bounds.tolist(),build_transform=t.tolist(),print_extent_mm=extent,yaw_deg=yaw)
        rows.append(row);print(json.dumps(row),flush=True)
    bands=[]
    for idx,(j,seat) in enumerate(zip(joints,seats),1):
        region=locate(rect(-WIDTH/2,-j[4],WIDTH/2,j[4]),j[2],j[3]).intersection(outline.buffer(-.15))
        def bottom(xy):return 10.5+crown(outline,xy)-SEAT_DEPTH+GLUE_GAP
        show_crown=smooth_cover_crown(outline,region)
        def top(xy):
            edge=shapely.distance(shapely.points(xy),region.boundary)
            return 10.5+show_crown(xy)-SEAT_DEPTH+GLUE_GAP+THICKNESS-.25*(1-np.clip(edge/.25,0,1))
        upper=band_envelope(region,top)
        band=boolean([upper,envelope(bottom,region.bounds,.25)],'difference')
        band=save_mesh(f'B{idx}',band);bands.append(band)
        t,extent,yaw=best_transform(band)
        rows.append(dict(name=f'B{idx}',watertight=True,components=1,triangles=len(band.faces),volume_mm3=float(band.volume),
            bounds_mm=band.bounds.tolist(),build_transform=t.tolist(),print_extent_mm=extent,yaw_deg=yaw))
        print('B'+str(idx),'band',band.volume,extent,flush=True)
    # Check the actual solids, rather than nominal parameters alone.
    overlaps=[]
    for i,a in enumerate(bodies+bands):
        for k,b in enumerate((bodies+bands)[:i]):
            if np.any(a.bounds[1]<b.bounds[0]) or np.any(b.bounds[1]<a.bounds[0]):continue
            volume=abs(boolean([a,b],'intersection').volume)
            assert volume<.001,(i,k,volume)
            overlaps.append([i,k,float(volume)])
    mountrows=[]
    for kind,xy,void,region,original in holes:
        near=[b for b in bodies if np.all(b.bounds[1,:2]>region.bounds[0,:2]) and np.all(b.bounds[0,:2]<region.bounds[1,:2])]
        before=boolean([original,region],'intersection')
        after=boolean([boolean(near,'union'),region],'intersection')
        error=abs(boolean([before,after],'difference').volume)+abs(boolean([after,before],'difference').volume)
        assert error<.001,(kind,xy,error)
        mountrows.append(dict(kind=kind,xy_mm=xy,difference_mm3=float(error)))
    report=dict(parts=rows,joints=jointrows,mounts=mountrows,collision_checks=overlaps,numerical_cleanup=NUMERICAL_CLEANUP,
        dimensions_mm=dict(band_width=WIDTH,seat_width=SEAT_WIDTH,seat_recess=SEAT_DEPTH,band_thickness=THICKNESS,
            glue_gap=GLUE_GAP,nominal_face_gap=.075,body=10.5,hammer_crown_max=2.2,band_max_front_z=13.45),
        physical_band_test_pending=True,source_cad_sha256=sha(CAD),preserved={p:sha(ROOT/p) for p in PRESERVED})
    (WORK/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    (REVIEW/'geometry-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    render(bodies,bands)


def render(bodies,bands):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig,ax=plt.subplots(figsize=(12,8),facecolor='#f3efe7');ax.set_facecolor('#f3efe7')
    light=np.array([-.45,-.65,.65]);light/=np.linalg.norm(light)
    for i,m in enumerate(bodies+bands):
        visible=(m.face_normals[:,2]>.15)&(m.triangles[:,:,2].min(axis=1)>9.89)
        shade=.4+.6*np.maximum(m.face_normals[visible]@light,0)
        color=np.array([.89,.49,.23] if i<6 else [.98,.65,.36])[None,:]*shade[:,None]
        ax.add_collection(PolyCollection(m.triangles[visible,:,:2],facecolors=color,edgecolors='none',antialiaseds=False))
    ax.set(xlim=(-310,310),ylim=(-190,190),aspect='equal');ax.axis('off')
    fig.suptitle('Hammered M with five separate smooth copper bands',fontsize=17)
    fig.text(.5,.035,'Actual candidate geometry | 12 mm bands | original artwork and all 22 mounting features\nOuter pair moved together to clear rear mounts. Shading illustrates shape, not predicted silk sheen.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.09,1,.94));fig.savefig(REVIEW/'assembled-bands.png',dpi=160);plt.close(fig)


def add_object(files,resources,build,config,relations,name,body,t,oid,holes,mods):
    path=f'3D/Objects/{name}.model';child=model();cr=ET.SubElement(child,tag('resources'))
    mesh_object(cr,oid+1,body)
    tri=cr.find(tag('object')).find(tag('mesh')).find(tag('triangles'))
    centers=body.triangles_center;normal=body.face_normals@t[:3,:3].T
    hole_mask=np.zeros(len(body.faces),bool)
    for kind,xy,*_ in holes:
        hole_mask|=(np.linalg.norm(centers[:,:2]-xy,axis=1)<(1.75 if kind=='screw' else 3.05))&(centers[:,2]<(8.71 if kind=='screw' else 3.4))
    # Bands: protect the outward surface and edges, support the inner seat.
    # Bodies: also block side facets sharing an upper vertex. Some long side
    # triangles extend below the seat; enforcing those lets Studio expand an
    # interface over the decorative edge even though the face itself is blocked.
    front=(body.face_normals[:,2]>-.01) if name.startswith('B') else (body.triangles[:,:,2].max(axis=1)>9.89)
    enforce=(normal[:,2]<-.1)&~front&~hole_mask;block=front|hole_mask
    for i in np.where(enforce|block)[0]:tri[i].set('paint_supports','8' if block[i] else '4')
    obj=ET.SubElement(resources,tag('object'),id=str(oid),type='model',attrib={'{'+P+'}UUID':uid()})
    comps=ET.SubElement(obj,tag('components'));cfg=ET.SubElement(config,'object',id=str(oid))
    meta(cfg,'name',name+' - covered joint candidate');meta(cfg,'extruder',1)
    for key,value in COPPER.items():meta(cfg,key,value)
    for k,(label,m) in enumerate([(name,body)]+mods,1):
        if k>1:mesh_object(cr,oid+k,m)
        ET.SubElement(comps,tag('component'),objectid=str(oid+k),transform=IDENTITY,attrib={'{'+P+'}path':'/'+path,'{'+P+'}UUID':uid()})
        pc=ET.SubElement(cfg,'part',id=str(oid+k),subtype='normal_part' if k==1 else 'modifier_part');meta(pc,'name',label)
        if k==1:ET.SubElement(pc,'mesh_stat',face_count=str(len(m.faces)),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        else:
            meta(pc,'sparse_infill_density','100%');meta(pc,'sparse_infill_pattern','cubic')
            assert boolean([body,m],'intersection').volume>1
    ET.SubElement(build,tag('item'),objectid=str(oid),printable='1',transform=' '.join(f'{v:.12g}' for v in t[:3,:].T.ravel()),attrib={'{'+P+'}UUID':uid()})
    ET.SubElement(relations,'Relationship',Target='/'+path,Id='rel-'+name,Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
    files[path]=xml(child)
    return dict(name=name,support_enforced_facets=int(enforce.sum()),support_blocked_facets=int(block.sum()),
        build_transform=t.tolist(),reinforcement_count=len(mods))


def centered(mesh,t,xy):
    r=t.copy();r[:3,3]=0;placed=mesh.copy();placed.apply_transform(r)
    r[:2,3]=np.array(xy)-placed.bounds.mean(axis=0)[:2];r[2,3]=-placed.bounds[0,2]
    return r


def stage(test=False):
    report=json.loads((WORK/'manifest.json').read_text());cad,outline,joints,regions=layout()
    source=read_zip(SOURCE);settings=json.loads(source['Metadata/project_settings.config'])
    settings.update(print_settings_id=TITLE,print_sequence='by layer',enable_prime_tower='0')
    settings.update(TRAVEL)
    assert settings['enable_support']=='1' and settings['support_type']=='tree(auto)'
    files={k:source[k] for k in ['[Content_Types].xml','_rels/.rels']}
    root=model();del root.attrib['xmlns:p']
    for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title',TITLE+(' - small B1 test' if test else ''))]:
        ET.SubElement(root,tag('metadata'),name=k).text=v
    resources=ET.SubElement(root,tag('resources'));build=ET.SubElement(root,tag('build'),attrib={'{'+P+'}UUID':uid()})
    config=ET.Element('config');relations=ET.Element('Relationships',xmlns=R)
    holes=mount_cutters(cad);rows={r['name']:r for r in report['parts']}
    plates=[];bodies={}
    if test:
        j=joints[0];crop=prism(locate(rect(-10,-35,27,35),j[2],j[3]),20,-1)
        for n in [2,3]:
            body=boolean([load_mesh(f'M{n}'),crop],'intersection')
            bodies[f'T{n}']=save_mesh(f'T{n}',body)
        bodies['B1']=load_mesh('B1')
        centers=TEST_CENTERS
        records=[]
        for name,xy in zip(['T2','T3','B1'],centers):
            parent=name.replace('T','M')
            t=centered(bodies[name],best_transform(load_mesh(parent))[0],xy);records.append((name,bodies[name],t))
        plates.append(('B1 band and actual joint crop',records))
    else:
        for n in range(1,7):
            name=f'M{n}';body=load_mesh(name);bodies[name]=body
            plates.append((name+' - hammered with band seats',[(name,body,best_transform(body)[0])]))
        records=[]
        for i,xy in enumerate(BAND_CENTERS,1):
            name=f'B{i}';body=load_mesh(name);bodies[name]=body
            records.append((name,body,centered(body,best_transform(body)[0],xy)))
        plates.append(('B1-B5 smooth copper bands',records))
    objectrows=[];oid=1000
    for n,(title,objects) in enumerate(plates,1):
        plate=ET.SubElement(config,'plate')
        for k,v in [('plater_id',n),('plater_name',title),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 1 1 1'),('filament_volume_maps','0 0 0 0')]:meta(plate,k,v)
        for name,body,t in objects:
            mods=[]
            if name.startswith('M'):
                for idx,(_,xy,void,region,_) in enumerate(holes):
                    if holes[idx][0]!='screw':continue
                    if np.any(body.bounds[1,:2]<region.bounds[0,:2]) or np.any(body.bounds[0,:2]>region.bounds[1,:2]):continue
                    if boolean([body,region],'intersection').volume>1:
                        mods.append((f'Screw reinforcement {idx+1}',cylinder(xy,14,10.5)))
            t=t.copy();t[:2,3]+=[((n-1)%3)*307.2,-((n-1)//3)*307.2]
            row=add_object(files,resources,build,config,relations,name,body,t,oid,holes if not name.startswith('B') else [],mods)
            row['plate']=n;objectrows.append(row)
            inst=ET.SubElement(plate,'model_instance')
            for k,v in [('object_id',oid),('instance_id',0),('identify_id',oid//1000)]:meta(inst,k,v)
            oid+=1000
    config[:]=config.findall('object')+config.findall('plate')
    files.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(relations),
        'Metadata/model_settings.config':xml(config),'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()})
    suffix='test' if test else 'full'
    write_zip(WORK/(suffix+'-staged.3mf'),files)
    (WORK/(suffix+'-stage.json')).write_text(json.dumps(dict(objects=objectrows,plate_count=len(plates)),indent=2))
    if test:render_test(bodies)
    print(suffix,'staged',len(plates),'plates',len(objectrows),'objects',flush=True)


def render_test(bodies):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    j=layout()[2][0];inv=rotation(-j[3]);inv[:2,3]=-inv[:2,:2]@j[2]
    fig=plt.figure(figsize=(11,5),facecolor='#f3efe7')
    for p,exploded in enumerate([False,True],1):
        ax=fig.add_subplot(1,2,p,projection='3d',facecolor='#f3efe7')
        for name,m in bodies.items():
            m=m.copy();m.apply_transform(inv)
            if exploded:m.apply_translation([(-5 if name=='T2' else 5 if name=='T3' else 0),0,8 if name=='B1' else 0])
            camera=np.array([.35,-.6,.7]);vis=m.face_normals@camera>0
            light=np.array([-.4,-.5,.75]);shade=.4+.6*np.maximum(m.face_normals[vis]@light,0)
            colors=np.array([.89,.49,.23] if name!='B1' else [.98,.65,.36])[None,:]*shade[:,None]
            ax.add_collection3d(Poly3DCollection(m.triangles[vis],facecolors=colors,edgecolors='none',antialiaseds=False))
        ax.set(xlim=(-17,34),ylim=(-30,30),zlim=(0,24));ax.set_box_aspect((51,60,24));ax.view_init(42,-60);ax.set_axis_off()
        ax.set_title('Assembled cover band' if not exploded else 'Separate band and recessed seats',fontsize=12)
    fig.suptitle('Small test from the actual B1 crown joint',fontsize=16)
    fig.text(.5,.03,'Full-size joint and band geometry | body cropped to 37 mm along the stroke\nBand bridges the seam with a nominal 0.15 mm glue allowance. Appearance and fit need the physical test.',ha='center',fontsize=10)
    fig.subplots_adjust(left=0,right=1,top=.88,bottom=.15,wspace=0);fig.savefig(REVIEW/'band-test.png',dpi=160);plt.close(fig)


def slice_project(test=False):
    suffix='test' if test else 'full';out=WORK/(suffix+'-slice');out.mkdir(exist_ok=True)
    exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
    with (out/'console.log').open('w') as log:
        r=subprocess.run([str(exe),'--slice','0','--export-3mf','sliced.3mf','--outputdir',str(out),str(WORK/(suffix+'-staged.3mf'))],
            cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print(suffix,'slice exit',r.returncode,flush=True)
    assert r.returncode==0,(out/'console.log').read_text()[-6000:]


def publish(test=False):
    suffix='test' if test else 'full';out=WORK/(suffix+'-slice')
    source=read_zip(WORK/(suffix+'-staged.3mf'));files=read_zip(out/'sliced.3mf')
    staged=json.loads((WORK/(suffix+'-stage.json')).read_text())
    manifest=json.loads((WORK/'manifest.json').read_text());result=json.loads((out/'result.json').read_text())
    assert result['return_code']==0 and len(result['sliced_plates'])==staged['plate_count']
    settings=json.loads(files['Metadata/project_settings.config'])
    assert settings==json.loads(source['Metadata/project_settings.config'])
    before,after=model_entries(source),model_entries(files)
    assert before.keys()==after.keys()
    roundtrip=[]
    for name,a in before.items():
        b=after[name];assert len(a)==len(b)
        for pa,pb in zip(a,b):
            ma,mb=pa['mesh'],pb['mesh']
            error=max(cKDTree(ma.vertices).query(mb.vertices)[0].max(),cKDTree(mb.vertices).query(ma.vertices)[0].max())
            assert error<.0001,(name,error)
            assert pa['config'].get('subtype')==pb['config'].get('subtype')
            for state in [4,8]:
                assert (pa['paint']==state).sum()==(pb['paint']==state).sum()
                aa=ma.area_faces[pa['paint']==state].sum();bb=mb.area_faces[pb['paint']==state].sum()
                assert abs(aa-bb)<max(.001,aa*1e-6)
            if pa['config'].get('subtype')=='modifier_part':
                for k in ['sparse_infill_density','sparse_infill_pattern']:assert props(pa['config'])[k]==props(pb['config'])[k]
            roundtrip.append(dict(name=name,subtype=pa['config'].get('subtype'),maximum_vertex_error_mm=float(error)))
    info=ET.fromstring(files['Metadata/slice_info.config']);cfg=ET.fromstring(files['Metadata/model_settings.config'])
    assert len(info.findall('plate'))==len(cfg.findall('plate'))==staged['plate_count']
    audits=[];plotpaths=[];cad,outline,joints,regions=layout()
    for n,plate in enumerate(info.findall('plate'),1):
        assert int(props(plate)['index'])==n
        setmeta(plate,'printer_model_id','N2S')
        for md in list(plate.findall('metadata')):
            if md.get('key')=='first_layer_time':
                value=float(md.get('value'))
                if not math.isfinite(value) or not 0<=value<=float(props(plate)['prediction']):plate.remove(md)
        warnings=[dict(w.attrib) for w in plate.findall('warning')]
        assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
        assert props(plate)['outside']=='false'
        gcode=files[f'Metadata/plate_{n}.gcode'].decode();audit=scan_gcode(gcode)
        assert audit['conservative_bed_edge_clearance_mm']>=1.5,(n,audit)
        assert set(audit['model_extrusion_z_by_filament_mm'])=={'1'}
        zs=audit.pop('model_extrusion_z_by_filament_mm')['1']
        assert max(zs)<250 and min(zs)>=.1999
        audit['model_z_range_mm']=[min(zs),max(zs)]
        assert not audit['features'].get('Ironing',0)
        if test or n<=6:assert audit['features'].get('Sparse infill',0)>0
        for f in ['Support','Support interface']:assert audit['features'].get(f,0)>0
        assert not re.search(r'^\s*(?:M400\s+U1|M0(?:\s|$)|M1(?:\s|$)|M25(?:\s|$))',gcode,re.M)
        paths,volumes=support_paths(gcode);centers=paths['Support interface'].mean(axis=1)
        facechecks=[]
        for row in staged['objects']:
            if row['plate']!=n:continue
            name=row['name'];t=np.array(row['build_transform']);shift=np.array([((n-1)%3)*307.2,-((n-1)//3)*307.2])
            t[:2,3]-=shift;mesh=load_mesh(name);placed=mesh.copy();placed.apply_transform(t)
            near=np.all(centers>=placed.bounds[0]-2,axis=1)&np.all(centers<=placed.bounds[1]+2,axis=1)
            local=trimesh.transform_points(centers[near],np.linalg.inv(t))
            if name.startswith('B'):
                j=joints[int(name[1:])-1]
                footprint=locate(rect(-WIDTH/2,-j[4],WIDTH/2,j[4]),j[2],j[3]).intersection(outline.buffer(-.15))
            else:footprint=mesh_slice(mesh,9)
            interior=shapely.contains(footprint.buffer(-.6),shapely.points(local[:,:2]))
            floor=10.5+crown(outline,local[interior,:2])-SEAT_DEPTH+GLUE_GAP
            delta=float(np.max(local[interior,2]-floor)) if interior.any() else None
            if name.startswith('B'):
                assert delta is not None and delta<.12,(name,delta)
            else:
                assert delta is None or delta<-2,(name,delta)
            facechecks.append(dict(name=name,interior_interface_points=int(interior.sum()),maximum_interface_z_minus_band_underside_mm=delta))
        audit.update(plate=n,metadata=props(plate),warnings=warnings,support_face_checks=facechecks,feature_extrusion_volume_mm3=volumes)
        audits.append(audit);plotpaths.append({k:v[::max(1,len(v)//16000)] for k,v in paths.items()})
        print(suffix,n,'weight',props(plate)['weight'],'time',props(plate)['prediction'],'clearance',audit['conservative_bed_edge_clearance_mm'],flush=True)
    files['Metadata/slice_info.config']=xml(info)
    target=TEST if test else TARGET;write_zip(target,files)
    for p,h in manifest['preserved'].items():assert sha(ROOT/p)==h
    report=dict(project=target.name,sha256=sha(target),roundtrip=roundtrip,plates=audits,
        total_weight_g=sum(float(a['metadata']['weight']) for a in audits),total_time_s=sum(int(a['metadata']['prediction']) for a in audits),
        physical_band_test_pending=True,preserved=manifest['preserved'],settings_equal_to_staged=True,slicer_result=result)
    (REVIEW/(suffix+'-validation.json')).write_text(json.dumps(report,indent=2)+'\n')
    render_paths(plotpaths,audits,suffix)
    if test:(REVIEW/'test-slicer-plate.png').write_bytes(files['Metadata/plate_1.png'])
    print(json.dumps({k:report[k] for k in ['project','sha256','total_weight_g','total_time_s']},indent=2))


def render_paths(paths,audits,suffix):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    count=len(paths);cols=1 if count==1 else 3;rows=math.ceil(count/cols)
    fig=plt.figure(figsize=(10,6) if count==1 else (15,14),facecolor='#f3efe7')
    for n,(groups,audit) in enumerate(zip(paths,audits),1):
        ax=fig.add_subplot(rows,cols,n,projection='3d',facecolor='#f3efe7')
        for key,color,lw in [('Outer wall','#b9692e',.4),('Support','#969ca3',.25),('Support interface','#2c7788',.55)]:
            ax.add_collection3d(Line3DCollection(groups[key],colors=color,linewidths=lw))
        if count==1:
            ax.set(xlim=(30,220),ylim=(70,200),zlim=(0,65));ax.set_box_aspect((190,130,65))
        else:
            ax.set(xlim=(0,256),ylim=(0,256),zlim=(0,256));ax.set_box_aspect((256,256,256))
        ax.view_init(25,-60);ax.set_xlabel('X');ax.set_ylabel('Y');ax.set_zlabel('Z');ax.tick_params(labelsize=7)
        label='Small band test' if count==1 else f'Plate {n}: '+(f'M{n}' if n<=6 else 'bands B1-B5')
        ax.set_title(label+f' | {float(audit["metadata"]["weight"]):.1f} g',fontsize=11)
    fig.suptitle('Native Bambu toolpaths - copper bands and hammered parts',fontsize=16)
    fig.text(.5,.035,'Copper: outer walls | gray: tree supports | teal: interfaces\nActual exported paths, sampled for clarity. Supports touch band undersides; check removal on the small test.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.09,1,.95));fig.savefig(REVIEW/(suffix+'-supports.png'),dpi=140);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['geometry','stage','slice','publish']);parser.add_argument('--test',action='store_true')
    args=parser.parse_args()
    if args.action=='geometry':geometry()
    else:{'stage':stage,'slice':slice_project,'publish':publish}[args.action](args.test)
