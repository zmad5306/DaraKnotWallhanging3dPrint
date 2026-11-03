from design_sections import *
import manifold3d as md, trimesh

DATA=json.loads(Path('.work/jointed-data.json').read_text())
if len(sys.argv)>1:DATA={sys.argv[1]:DATA[sys.argv[1]]}
PROFILES={k:shape(g)for k,g in json.loads(Path('.work/joint-profiles.json').read_text()).items()}

def cs(g):
    contours=[]
    for p in geoms(g):
        p=orient(p,1)
        contours += [np.array(p.exterior.coords)[:-1],*[np.array(r.coords)[:-1]for r in p.interiors]]
    return md.CrossSection(contours,md.FillRule.Positive)
def extr(g,height,z=0):return cs(g).extrude(height).translate([0,0,z])
def mesh_solid(path):
    m=trimesh.load_mesh(path)
    s=md.Manifold(md.Mesh64(np.array(m.vertices),np.array(m.faces,dtype=np.uint64)))
    assert s.status()==md.Error.NoError and s.volume()>0
    return s
def joint_tool(j,socket=False):
    width=j['span']+44
    profile=extr(PROFILES['void' if socket else 'male'],width,-width/2).rotate([90,0,0])
    for y in j['keys']:
        profile+=extr(PROFILES['pocket' if socket else 'key'],1.36 if socket else 1.21,4.94 if socket else 4.79).translate([0,y,0])
    return profile.rotate([0,0,j['angle']]).translate([*j['centre'],0]) ^ extr(shape(j['domain']),7,-.1)
def tm(s):
    m=s.to_mesh64();return trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=False)

report={};fig,axs=plt.subplots(1,2,figsize=(16,9))
for ax,(name,d) in zip(axs,DATA.items()):
    raw=mesh_solid('.work/jointed-original-'+name+'.off')
    ts=[joint_tool(j)for j in d['joints']];vs=[joint_tool(j,True)for j in d['joints']]
    parts=[];entries=[]
    for i,p in enumerate(d['parts']):
        mask=extr(shape(d['masks'][i]),35,-5)
        for j,t in zip(d['joints'],ts):
            if j['male']==i:mask+=t
        part=raw ^ mask
        for j,v in zip(d['joints'],vs):
            if j['female']==i:part-=v
        m=tm(part)
        assert part.status()==md.Error.NoError
        assert len(part.decompose())==1,(name,i,'disconnected',[(s.volume())for s in part.decompose()])
        assert m.is_watertight and m.is_winding_consistent and m.volume>0,(name,i,'invalid mesh')
        pl=d['placements'][i]
        pm=tm(part.rotate([0,0,pl['angle']]))
        assert max(pm.extents[:2])<246,(name,i,pm.extents)
        expected_z=-3.2 if name=='frame' and shape(p).intersects(unary_union(TRACKS)) else 0
        assert abs(m.bounds[0,2]-expected_z)<1e-5,(name,i,'wrong print origin',m.bounds)
        entries.append({'section':i+1,'size_mm':pm.extents.tolist(),'volume_mm3':part.volume(),'watertight':True,'connected':True})
        parts.append(part)
        draw(ax,shape(p),plt.cm.tab20(i%20));c=shape(p).representative_point();ax.text(c.x,c.y,f'{name[0]}{i+1}',ha='center',fontsize=8)
    interference=[]
    for i,p in enumerate(parts):
        for k,q in enumerate(parts[i+1:],i+1):
            volume=(p^q).volume()
            assert volume<1e-5,(name,'interference',i,k,volume)
    all_parts=md.Manifold.batch_boolean(parts,md.OpType.Add)
    print(name,'assembly bodies',len(all_parts.decompose()),'sum volume',sum(p.volume()for p in parts),'union volume',all_parts.volume(),flush=True)
    added=(all_parts-raw).volume(); assert added<1e-5,(name,'outline changed',added)
    # Every removed voxel must be inside an intentional seam or lap pocket.
    zones=[]
    for j in d['joints']:
        g=shape(j['domain']).union(shape(j['line']).buffer(.1))
        zones.append(extr(g.buffer(.001),35,-5))
        ax.plot(*shape(j['line']).xy,color='red',lw=.8)
    zone=md.Manifold.batch_boolean(zones,md.OpType.Add)
    accidental=(raw-all_parts)-zone
    assert accidental.volume()<.01,(name,'unintended removal',accidental.volume())
    if name=='frame':
        for idx,track in enumerate(TRACKS):
            vol=(extr(track,3.201,-3.2)^(raw-all_parts)).volume()
            assert vol<1e-5,('track modified',idx,vol)
    else:
        exported=mesh_solid('.work/jointed-M.off')
        mismatch=(exported-all_parts).volume()+(all_parts-exported).volume()
        print('SCAD mismatch',mismatch,'exported components',len(exported.decompose()),flush=True)
        assert mismatch<20,(name,'SCAD and independent construction mismatch',mismatch)
    # Assemble sockets downward only; reject an overlap cycle.
    incoming={i:set()for i in range(len(parts))}
    for j in d['joints']:incoming[j['female']].add(j['male'])
    order=[]
    while len(order)<len(parts):
        ready=next((i for i,v in incoming.items()if i not in order and v.issubset(order)),None)
        assert ready is not None,'Assembly cycle'
        order.append(ready)
    report[name]={'sections':entries,'joint_count':len(d['joints']),'assembly_order':[i+1 for i in order],'interference_mm3':0,'unintended_removed_mm3':accidental.volume(),'gap_volume_mm3':(raw-all_parts).volume(),'max_xy_mm':max(max(e['size_mm'][:2])for e in entries)}
    ax.set_aspect('equal');ax.autoscale();ax.set_title(name);ax.grid(alpha=.15)
    print(name,len(parts),'closed connected solids; no interference; max XY',report[name]['max_xy_mm'],'order',report[name]['assembly_order'],flush=True)
fig.tight_layout();fig.savefig('.work/jointed-verified-plan.png',dpi=125)
Path('.work/jointed-verification.json').write_text(json.dumps(report,indent=2))
