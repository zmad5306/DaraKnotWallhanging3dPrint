exec((__import__('pathlib').Path(__file__).parent/'check_bottom.py').read_text().split('fig,axes=')[0])
import re,math
if len(sys.argv)>1:
    W=W/'r4-check';W.mkdir(exist_ok=True)
m=meshes['Lock - quarter sheet']
fig,axes=plt.subplots(1,2,figsize=(13,6))
for ax,z in zip(axes,[.1,.3]):
    sec=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
    for p in sec.discrete:ax.plot(p[:,0],p[:,1],color='navy')
    ax.set_aspect('equal');ax.set_title(f'Model cross section at Z{z} mm');ax.set_xlim(132,206);ax.set_ylim(150,165)
fig.tight_layout();fig.savefig(W/'first-two-outlines.png',dpi=140)
g=files['Metadata/plate_1.gcode'].decode()
xyz=np.zeros(3);e=0;rel_e=False;rel_xyz=False;feature='Custom';width=.5;segments=[]
for raw in g.splitlines():
    if raw.startswith('; FEATURE: '):feature=raw.split(': ',1)[1]
    if raw.startswith('; LINE_WIDTH: '):width=float(raw.split(': ',1)[1])
    line=raw.split(';',1)[0].strip()
    if not line:continue
    cmd=line.split()[0];v={k:float(n) for k,n in re.findall(r'([XYZIJE])(-?(?:\d+\.?\d*|\.\d+))',line)}
    if cmd=='M83':rel_e=True
    elif cmd=='M82':rel_e=False
    elif cmd=='G90':rel_xyz=False
    elif cmd=='G91':rel_xyz=True
    elif cmd=='G92':
        if 'E' in v:e=v['E']
        for i,k in enumerate('XYZ'):
            if k in v:xyz[i]=v[k]
    elif cmd in ['G0','G1','G2','G3']:
        dest=np.array([xyz[i]+v.get(k,0) if rel_xyz else v.get(k,xyz[i]) for i,k in enumerate('XYZ')])
        de=v.get('E',0) if rel_e else v.get('E',e)-e
        if de>0 and feature!='Custom' and ('X' in v or 'Y' in v) and max(dest[2],xyz[2])<4.1:
            if cmd in ['G2','G3'] and ('I' in v or 'J' in v):
                c=xyz[:2]+np.array([v.get('I',0),v.get('J',0)])
                rad=np.linalg.norm(xyz[:2]-c);a=math.atan2(xyz[1]-c[1],xyz[0]-c[0]);b=math.atan2(dest[1]-c[1],dest[0]-c[0])
                da=-((a-b)%(2*math.pi)) if cmd=='G2' else ((b-a)%(2*math.pi))
                t=np.linspace(0,1,max(2,int(math.ceil(abs(da)*rad/.1))+1))
                pts=np.c_[c[0]+rad*np.cos(a+da*t),c[1]+rad*np.sin(a+da*t),xyz[2]+(dest[2]-xyz[2])*t]
            else:pts=np.array([xyz,dest])
            if np.any((pts[:,0]>133)&(pts[:,0]<205)&(pts[:,1]>148)&(pts[:,1]<180)):
                segments.append({'feature':feature,'width':width,'pts':pts.tolist()})
        xyz=dest;e=e+v.get('E',0) if rel_e else v.get('E',e)
(W/'low-paths.json').write_text(json.dumps(segments))
fig,axes=plt.subplots(1,3,figsize=(15,5))
colors={'Outer wall':'#1565c0','Inner wall':'#64b5f6','Bottom surface':'#8e24aa','Support':'#ef6c00','Support interface':'#c62828','Brim':'#aaa','Overhang wall':'#00897b'}
for ax,z in zip(axes,[.2,.4,.6]):
    for s in segments:
        p=np.array(s['pts'])
        if abs(p[0,2]-z)<.001:ax.plot(p[:,0],p[:,1],lw=.5,color=colors.get(s['feature'],'gray'))
    ax.set_aspect('equal');ax.set_title(f'Native toolpaths Z{z} mm');ax.set_xlim(132,206);ax.set_ylim(150,165)
fig.tight_layout();fig.savefig(W/'first-three-paths.png',dpi=140)
for z in [.2,.4,.6,1.0,2.0]:
    relevant=[s for s in segments if abs(s['pts'][0][2]-z)<.001]
    model=[np.array(s['pts']) for s in relevant if s['feature'] not in ['Brim','Skirt','Support','Support interface','Support transition']]
    support=[np.array(s['pts']) for s in relevant if s['feature'].startswith('Support')]
    print('LAYER',z,'model',np.concatenate(model).min(axis=0).tolist() if model else None,np.concatenate(model).max(axis=0).tolist() if model else None,'support segments',len(support))
ids=np.where((m.face_normals[:,2]<-.999)&(m.triangles_center[:,2]<1))[0]
normal=np.average(m.face_normals[ids],axis=0,weights=m.area_faces[ids]);normal/=np.linalg.norm(normal)
verts=m.vertices[np.unique(m.faces[ids])]
print('FLAT UNDERSIDE',normal.tolist(),'tilt deg',np.degrees(np.arccos(-normal[2])),'Z range',verts[:,2].min(),verts[:,2].max(),'area',m.area_faces[ids].sum())
