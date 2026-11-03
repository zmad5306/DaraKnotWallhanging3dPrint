from repartition_search import *

def mesh(v):
    ps=[]
    for row in range(4):
        for col in range(4):
            pg=Polygon([v[row,col],v[row,col+1],v[row+1,col+1],v[row+1,col]])
            if not pg.is_valid:return None
            gg=geoms(FRAME.intersection(pg))
            if len(gg)!=1:return None
            ps.append(gg[0])
    return ps

def vertices(p):
    v=np.zeros((5,5,2))
    for r,y in enumerate([-600,-p[0],0,p[0],600]):
        for c,x in enumerate([-600,-p[0],0,p[0],600]):v[r,c]=[x,y]
    for r in [0,4]:v[r,1,0]=-p[1];v[r,3,0]=p[1]
    for c in [0,4]:v[1,c,1]=-p[1];v[3,c,1]=p[1]
    return v

if __name__=='__main__':
    best=None
    for t in range(165,196,5):
        for u in range(180,601,10):
            v=vertices([t,u]);ps=mesh(v)
            if ps is None:continue
            sizes=[fast_fit(p)[0] for p in ps];score=max(sizes)
            if best is None or score<best[0]:best=(score,t,u,sizes)
    print(best)
    v=vertices(best[1:3]);ps=mesh(v)
    fig,ax=plt.subplots(figsize=(10,10))
    for i,p in enumerate(ps):draw(ax,p,plt.get_cmap('tab20')(i));ax.text(*p.representative_point().coords[0],str(i+1))
    ax.autoscale();ax.set_aspect('equal');fig.savefig(OUT/'mesh-test.png',dpi=100)
    (OUT/'mesh-test.json').write_text(json.dumps({'vertices':v.tolist(),'parts':[mapping(p)for p in ps]}))
