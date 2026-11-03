import sys,time,json
from pathlib import Path
sys.path.insert(0,'scripts')
import prepare_hammered_bands as b
np=b.np;sh=b.shapely

def conforming_envelope(region,evaluate,res=.25,bottom=6.6,bevel=.25):
    # Planar grid is cut at both exact edges of the bevel BEFORE height evaluation.
    core=sh.set_precision(region.buffer(-bevel),1e-9);region=sh.set_precision(region,1e-9)
    rim=region.difference(core)
    lo=np.floor(np.array(region.bounds[:2])/res)*res;hi=np.ceil(np.array(region.bounds[2:])/res)*res
    xs,ys=[np.arange(a,c+res/2,res) for a,c in zip(lo,hi)]
    xx,yy=np.meshgrid(xs,ys);xy=np.column_stack([xx.ravel(),yy.ravel()]);nx=len(xs);ny=len(ys)
    aa=(np.arange(ny-1)[:,None]*nx+np.arange(nx-1)[None,:]).ravel()
    ff=np.concatenate([np.column_stack([aa,aa+1,aa+nx+1]),np.column_stack([aa,aa+nx+1,aa+nx])])
    grid=sh.set_precision(sh.polygons(xy[ff]),1e-9)
    polys=np.concatenate([sh.get_parts(sh.intersection(grid,core)),sh.get_parts(sh.intersection(grid,rim))])
    polys=polys[sh.get_type_id(polys)==3];tris=sh.get_parts(sh.constrained_delaunay_triangles(polys));coords=sh.get_coordinates(tris).reshape(-1,4,2)[:,:3,:]
    pts,inv=np.unique(np.round(coords.reshape(-1,2),9),axis=0,return_inverse=True);f=inv.reshape(-1,3)
    # Ensure consistent upward winding.
    cross=np.cross(pts[f[:,1]]-pts[f[:,0]],pts[f[:,2]]-pts[f[:,0]]);f[cross<0]=f[cross<0][:,::-1]
    v=np.column_stack([pts,evaluate(pts)]);n=len(v);vb=np.column_stack([pts,np.full(n,bottom)])
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);_,ei,ec=np.unique(np.sort(edges,axis=1),axis=0,return_index=True,return_counts=True);boundary=edges[ei[ec==1]]
    side=np.concatenate([np.column_stack([boundary[:,0],boundary[:,0]+n,boundary[:,1]+n]),np.column_stack([boundary[:,0],boundary[:,1]+n,boundary[:,1]])])
    faces=np.concatenate([f,(f+n)[:,::-1],side]);m=b.trimesh.Trimesh(np.concatenate([v,vb]),faces,process=True)
    assert m.is_volume and m.is_watertight,(m.is_watertight,m.body_count)
    return m

if __name__=='__main__':
 _,outline,joints,_=b.layout();results=[]
 for idx,j in enumerate(joints,1):
  region=b.locate(b.rect(-6,-j[4],6,j[4]),j[2],j[3]).intersection(outline.buffer(-.15))
  def floor(xy):return 10.5+b.crown(outline,xy)-.6+.15
  def top(xy):return floor(xy)+1.2-.25*(1-np.clip(sh.distance(sh.points(xy),region.boundary)/.25,0,1))
  upper=conforming_envelope(region,top);band=b.boolean([upper,b.envelope(floor,region.bounds,.25)],'difference')
  assert band.is_volume and band.body_count==1
  np.savez_compressed(f'.work/cover-render/B{idx}-edge.npz',vertices=band.vertices,faces=band.faces)
  sel=band.face_normals[:,2]>.01;p=band.triangles_center[sel];err=p[:,2]-top(p[:,:2]);row=dict(name=f'B{idx}',faces=len(band.faces),volume=float(band.volume),max_top_error=float(abs(err).max()),oldvolume=float(b.load_mesh(f'B{idx}').volume));results.append(row);print(row,flush=True)
 Path('.work/cover-render/edge-geometry.json').write_text(json.dumps(results,indent=2))
