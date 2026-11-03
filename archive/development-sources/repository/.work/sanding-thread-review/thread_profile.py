exec((__import__('pathlib').Path(__file__).parent/'audit.py').read_text().split('results={}')[0])
from scipy.signal import find_peaks
def profile(mesh,axis,center,range_x):
 t=trimesh.geometry.align_vectors(axis,[1,0,0]);m=mesh.copy();m.apply_translation(-np.asarray(center));m.apply_transform(t)
 seg=trimesh.intersections.mesh_plane(m,[0,1,0],[0,0,0])
 xs=np.arange(*range_x,.01);out=[]
 for x in xs:
  valid=(seg[:,:,0].min(1)<=x)&(seg[:,:,0].max(1)>=x)&(np.abs(np.diff(seg[:,:,0],axis=1)[:,0])>1e-9)
  v=seg[valid];k=(x-v[:,0,0])/(v[:,1,0]-v[:,0,0]);z=v[:,0,2]+k*(v[:,1,2]-v[:,0,2]);out.append(z.max() if len(z) else np.nan)
 out=np.asarray(out);pk,_=find_peaks(out,prominence=.5,distance=100)
 print('PEAKS',xs[pk],out[pk], 'pitch',np.diff(xs[pk]),flush=True)
 return xs,out
rear=profile(positions['Tighteneer'],[1,0,0],rear_center,(-17.3,-1))
top=profile(positions['Screw'],top_axis,top_center,(-17,-1))
np.savez(W/'thread-profiles.npz',rear_x=rear[0],rear_r=rear[1],top_x=top[0],top_r=top[1])
