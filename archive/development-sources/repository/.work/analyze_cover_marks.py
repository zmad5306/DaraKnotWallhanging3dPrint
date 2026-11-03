import sys, json, re, math, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'output/Dara-B1-Cover-Source/scripts')]
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import prepare_hammered_bands as b
from prepare_cover_crown_test import shape
W=ROOT/'.work/cover-marks'; W.mkdir(exist_ok=True)
TOKEN=re.compile(r'([XYZEFIJ])\s*(-?(?:\d*\.\d+|\d+\.?\d*))')

def parse(text):
    xyz=np.zeros(3); e=f=0.; relative_e=relative_xyz=False
    feature='Custom'; width=.42; object_id=None; moves=[]; chain=0
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
                if de>0 and feature=='Outer wall':
                    arc=None
                    if cmd in ['G2','G3']:
                        center=xyz[:2]+[v.get('I',0),v.get('J',0)];radius=np.linalg.norm(xyz[:2]-center)
                        a0,a1=np.arctan2(*((np.array([xyz[:2],end[:2]])-center)[:,::-1].T))
                        sweep=(a1-a0)%(2*np.pi) if cmd=='G3' else -((a0-a1)%(2*np.pi))
                        length=abs(sweep)*radius;arc=(center,radius,a0,sweep)
                    moves.append(dict(start=xyz.copy(),end=end.copy(),line=line,object=object_id,speed=f/60,width=width,
                                      e_per_mm=de/length,length=length,cmd=cmd,arc=arc,chain=chain))
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

def analyze():
    release=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/cover-crown-validation.json').read_text())
    with zipfile.ZipFile(ROOT/'Dara.3mf') as z:text=z.read('Metadata/plate_31.gcode').decode()
    moves=parse(text);result=[]
    fig,axs=plt.subplots(5,3,figsize=(16,13),layout='constrained')
    for i,row in enumerate(release['geometry_checks'],1):
        t=np.array(row['build_transform']);undo=np.linalg.inv(t);region,floor,top=shape(i);joint=b.layout()[2][i-1]
        local=b.rotation(-joint[3]);local[:2,3]=-local[:2,:2]@np.array(joint[2])
        paths=[];front=[];changes=[];reversals=[];previous=None;joins=[]
        for m in moves:
            if m['object']!=i+6:continue
            points=sample(m);assembled=b.trimesh.transform_points(points,undo)
            xy=assembled[:,:2];edges=b.shapely.distance(b.shapely.points(xy),region.boundary)
            onfront=(assembled[:,2]-top(xy)>-.4)&(edges>.6)
            q=b.trimesh.transform_points(assembled,local)
            if onfront.any():
                front.append(m);paths.extend((p,m) for p in np.stack([q[:-1,:2],q[1:,:2]],axis=1)[onfront[:-1]&onfront[1:]])
                if onfront[0] and previous is not None and previous['chain']==m['chain']:
                    a,c=tangent(previous,True),tangent(m)
                    angle=float(np.degrees(np.arccos(np.clip(a@c/np.linalg.norm(a)/np.linalg.norm(c),-1,1))))
                    joins.append(dict(xy=q[0,:2].tolist(),angle_deg=angle,line=m['line']))
                    if abs(m['speed']-previous['speed'])>.1 or abs(m['width']-previous['width'])>.001:
                        changes.append(dict(xy=q[0,:2].tolist(),line=m['line'],speed_before=previous['speed'],speed_after=m['speed'],width_before=previous['width'],width_after=m['width']))
                    dx0=previous['end'][0]-previous['start'][0];dx=m['end'][0]-m['start'][0]
                    if dx0*dx<=0 and abs(dx0-dx)>1e-5:reversals.append(q[0,:2])
                previous=m
            else:previous=None
        summary=dict(name=row['name'],front_moves=len(front),speed_range=[min(m['speed'] for m in front),max(m['speed'] for m in front)],
                     width_range=[min(m['width'] for m in front),max(m['width'] for m in front)],
                     extrusion_per_mm_percentiles=np.percentile([m['e_per_mm'] for m in front],[0,1,50,99,100]).tolist(),
                     interior_changes=changes,joins=joins)
        result.append(summary)
        for j,(key,title) in enumerate([('speed','Commanded speed (mm/s)'),('e_per_mm','Filament per path mm'),('length','G-code move length (mm)')]):
            ax=axs[i-1,j];lines=[p[:,::-1] for p,m in paths];values=[m[key] for p,m in paths]
            lc=LineCollection(lines,array=np.array(values),cmap='viridis',linewidths=1);ax.add_collection(lc);ax.autoscale();ax.set_aspect('equal')
            ax.set_title(f'Band {i}: {title}');fig.colorbar(lc,ax=ax,shrink=.7)
            if changes:
                pts=np.array([c['xy'] for c in changes]);ax.scatter(pts[:,1],pts[:,0],s=7,c='red',zorder=3)
            if j==2 and reversals:
                pts=np.array(reversals);ax.scatter(pts[:,1],pts[:,0],s=7,c='magenta',zorder=3)
            if j==2 and joins:
                pts=np.array([v['xy'] for v in joins]);ax.scatter(pts[:,1],pts[:,0],s=15,facecolors='none',edgecolors='red',zorder=3)
    fig.suptitle('Production Plate 31: show-face G-code paths\nRed: interior speed/width changes; magenta: X reversals at segment joins')
    fig.savefig(W/'production-paths.png',dpi=160);plt.close(fig)
    (W/'paths.json').write_text(json.dumps(result,indent=2))
    for row in result:
        print({k:(len(v) if k in ['interior_changes','joins'] else v) for k,v in row.items()})
        print('largest joins',sorted(row['joins'],key=lambda x:-x['angle_deg'])[:3])

if __name__=='__main__':analyze()
