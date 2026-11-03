import sys,json,math,re
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import prepare_hammered_bands as b
from validate_print_project import TOKEN
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
WORK=b.ROOT/'.work/band-repair';r=json.loads((b.ROOT/'working/review/y-stable-dara/test-validation.json').read_text());row=next(r for r in r['orientation'] if r['name']=='B1');t=b.np.array(row['build_transform']);t[:2,3]+=[-68,18]
_,outline,joints,_=b.layout();j=joints[0];u=b.rotation(-j[3]);u[:2,3]=-u[:2,:2]@b.np.array(j[2])
def examine(file):
 text=b.read_zip(file)['Metadata/plate_1.gcode'].decode();x=y=z=e=0.;rel=False;xyzrel=False;feature='Custom';last=None;paths=[];jumps=[];arc_count=0;extruding=False
 for i,raw in enumerate(text.splitlines()):
  if raw.startswith('; FEATURE: '):feature=raw[11:].strip()
  code=raw.split(';',1)[0].strip()
  if not code:continue
  cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
  if cmd=='M83':rel=True
  elif cmd=='M82':rel=False
  elif cmd in ['G90','G91']:xyzrel=cmd=='G91'
  elif cmd=='G92':x,y,z,e=[v.get(k,old) for k,old in zip('XYZE',(x,y,z,e))]
  elif cmd in ['G0','G1','G2','G3']:
   nx,ny,nz=[old+v.get(k,0) if xyzrel else v.get(k,old) for k,old in zip('XYZ',(x,y,z))];de=v.get('E',0) if rel else v.get('E',e)-e;length=math.dist([x,y,z],[nx,ny,nz]);p=b.np.array([[x,y,z],[nx,ny,nz]])
   if length>.00001:
    if de>0 and feature=='Outer wall':
     if cmd in ['G2','G3']:
      center=b.np.array([x+v.get('I',0),y+v.get('J',0)]);radii=p[:,:2]-center;sign=1 if cmd=='G3' else -1
      d0=sign*b.np.array([-radii[0,1],radii[0,0],0]);d1=sign*b.np.array([-radii[1,1],radii[1,0],0]);radius=b.np.linalg.norm(radii[0]);a0,a1=b.np.arctan2(radii[:,1],radii[:,0]);delta=(a1-a0)%(2*math.pi) if sign>0 else -((a0-a1)%(2*math.pi));angles=b.np.linspace(a0,a0+delta,max(2,int(abs(delta)*radius/.06)+1));sample=b.np.column_stack([center[0]+radius*b.np.cos(angles),center[1]+radius*b.np.sin(angles),b.np.linspace(z,nz,len(angles))]);arc_count+=1
     else:
      d0=d1=p[1]-p[0];sample=p
     local=b.trimesh.transform_points(p,b.np.linalg.inv(t));roof=10.5+b.crown(outline,local[:,:2])-.6+.15+1.2;local=b.trimesh.transform_points(local,u)
     onfront=min(local[:,2]-roof)>-.4
     if onfront:
      sp=b.trimesh.transform_points(b.trimesh.transform_points(sample,b.np.linalg.inv(t)),u);paths.extend(b.np.stack([sp[:-1],sp[1:]],axis=1).tolist())
      if last is not None and last['onfront'] and b.np.linalg.norm(p[0]-last['end'])<.00001 and abs(local[0,0])<4.8 and -16<local[0,1]<12:
       angle=math.degrees(math.acos(b.np.clip(b.np.dot(d0,last['dir'])/(b.np.linalg.norm(d0)*b.np.linalg.norm(last['dir'])),-1,1)));jumps.append(dict(angle=angle,xy=local[0,:2].tolist(),line=i+1,cmd=cmd))
     last=dict(dir=d1,end=p[1],onfront=onfront)
    else:last=None
   elif de<0:last=None
   x,y,z=nx,ny,nz;e=e+v.get('E',0) if rel else v.get('E',e)
 return paths,jumps,arc_count
fig,axes=plt.subplots(1,3,figsize=(12,13));reports={}
for ax,label in zip(axes,['control','no-arcs','fine']):
 paths,jumps,arcs=examine(WORK/label/'sliced.3mf');reports[label]=dict(arcs=arcs,jumps=jumps)
 vals=[q['angle'] for q in jumps];print(label,'arcs',arcs,'tangent jumps',len(jumps),'max',max(vals),'p50/95',b.np.percentile(vals,[50,95]),'gt1',sum(v>1 for v in vals),flush=True)
 ax.add_collection(LineCollection(b.np.array(paths)[:,:,:2],linewidths=.5,colors='#9a673b'));xy=b.np.array([q['xy'] for q in jumps]);sc=ax.scatter(xy[:,0],xy[:,1],c=vals,s=9,vmin=0,vmax=2,cmap='inferno',zorder=3);ax.autoscale();ax.set_aspect('equal');ax.set_title(label+' direction changes');fig.colorbar(sc,ax=ax)
fig.tight_layout();fig.savefig(WORK/'tangents.png',dpi=150);(WORK/'tangent-report.json').write_text(json.dumps(reports,indent=2))
