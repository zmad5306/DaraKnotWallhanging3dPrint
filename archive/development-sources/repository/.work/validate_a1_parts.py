from pathlib import Path
import subprocess,concurrent.futures,json,time,sys,hashlib,re,ast
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import numpy as np,trimesh
CAD=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
OUT=Path('.work/a1-validation');OUT.mkdir(exist_ok=True)
source=CAD.read_text();source_hash=hashlib.sha256(CAD.read_bytes()).hexdigest()
placements={family:ast.literal_eval(re.search('^'+family+r'_placements = (.*?);',source,re.M).group(1))for family in ['frame','M']}
jobs=[]
for family,count in [('frame',30),('M',6)]:
    jobs += [(f'{family[0].upper()}{i+1}',family,i,['view_mode="section"',f'part_family="{family}"',f'section_index={i+1}'])for i in range(count)]
jobs += [(f'B{i+1}','backer',i,['view_mode="backer"',f'backer_index={i+1}'])for i in range(8)]
jobs += [('tab','retainer',0,['view_mode="retainer"']),('washer','washer',0,['view_mode="washer"']),('fit-sample','fit_sample',0,['view_mode="fit_sample"'])]
def run(job):
    name,family,i,defs=job;start=time.monotonic();path=OUT/(name+'.stl')
    args=[EXE,'--hardwarnings','--camera=0,0,0,0,0,0,700','--export-format=binstl','-o',str(path)]
    for d in defs:args+=['-D',d]
    p=subprocess.run(args+[str(CAD)],capture_output=True,text=True,timeout=600)
    result={'part':name,'family':family,'index':i,'seconds':round(time.monotonic()-start,1),'returncode':p.returncode,'stderr':p.stderr}
    (OUT/(name+'-log.json')).write_text(json.dumps(result,indent=2))
    assert p.returncode==0 and 'ERROR:'not in p.stderr and 'WARNING:'not in p.stderr,(name,p.stderr)
    mesh=trimesh.load_mesh(path)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,(name,'invalid geometry')
    parts=len(mesh.split());assert parts==(3 if family=='fit_sample' else 1),(name,'disconnected',parts)
    lo,hi=mesh.bounds;size=mesh.extents
    edge=min(*(lo[:2]+128),*(128-hi[:2]))
    size_ok=max(size[:2])<=246 and size[2]<=256
    placement_ok=edge>=5 and abs(lo[2])<1e-5 and hi[2]<=256
    result.update({'bounds_mm':mesh.bounds.tolist(),'size_mm':size.tolist(),'edge_margin_mm':float(edge),'size_ok':bool(size_ok),'placement_ok':bool(placement_ok),'volume_mm3':mesh.volume,'components':parts})
    if family in placements:
        pl=placements[family][i];result['rotation_deg']=pl[0]
        mesh.apply_translation([*pl[1],-pl[3]])
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-pl[0]),[0,0,1]))
        result['assembly_size_mm']=mesh.extents.tolist()
    print(name, 'PASS'if size_ok and placement_ok else 'NEEDS UPDATE', np.round(size,3), 'edge',round(edge,3),flush=True)
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(run,jobs))
report={'source_sha256':source_hash,'date':'2026-10-12','bed_mm':[256,256,256],'reserved_edge_mm':5,'source':'https://bambulab.com/en/a1/tech-specs','parts':results,'all_pass':all(r['size_ok'] and r['placement_ok']for r in results)}
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
print('ALL PASS:',report['all_pass'],'checked',len(results),'distinct part shapes',flush=True)
