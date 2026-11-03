import sys,json,numpy as np,subprocess,zipfile,shutil
sys.path.insert(0,'scripts');import organize_root_projects as o
src=json.loads((o.WORK/'sources.json').read_text());snew,merged=o.rows(o.ROOT/'Small Parts.3mf');checks=[]
for key,mapping in [('Small Parts',{1:1,2:2,3:3}),('Center',{1:4}),('Sides',{1:5})]:
 s,rows=o.rows(o.ROOT/src[key]);target=[r for r in merged if r['plate'] in mapping.values()];assert len(rows)==len(target)
 for a,b in zip(rows,target):
  assert a['name']==b['name'] and mapping[a['plate']]==b['plate']
  assert a['settings']==b['settings'];assert np.max(np.abs(a['transform']-b['transform']))<.0001
  for x,y in zip(a['parts'],b['parts']):
   assert x['subtype']==y['subtype'];assert x['paint']==y['paint'];assert np.array_equal(x['mesh'].faces,y['mesh'].faces)
   assert np.max(np.abs(x['mesh'].vertices-y['mesh'].vertices))<.0001
   assert {k:v for k,v in x['settings'].items() if k not in o.BOOKKEEPING}=={k:v for k,v in y['settings'].items() if k not in o.BOOKKEEPING}
 diff={k for k in set(s)|set(snew) if s.get(k)!=snew.get(k)};assert diff<={'print_settings_id','wipe_tower_x','wipe_tower_y'},diff
 checks.append(dict(source=key,objects=len(rows),source_plate_to_root_plate=mapping,geometry_and_paint_preserved=True,bed_poses_preserved=True,effective_settings_preserved=True,only_global_metadata_differences=sorted(diff)))
o.dump(o.REPORT/'small-parts-preservation.json',checks)
for key,row in json.loads((o.REPORT/'sources.json').read_text()).items():assert o.sha(o.ROOT/row['path'])==row['sha256'],key
checks=[]
for title in o.TITLES:
 p=o.ROOT/(title+'.scad');out=o.WORK/(title+'.csg')
 r=subprocess.run([r'C:\Program Files (x86)\OpenSCAD\openscad.exe','-o',str(out),str(p)],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert r.returncode==0 and 'ERROR' not in r.stderr,(title,r.stderr)
 checks.append(dict(file=p.name,sha256=o.sha(p),openscad_parse_return_code=r.returncode,messages=r.stderr.strip()))
o.dump(o.REPORT/'cad-validation.json',checks)
# Keep native previews for visual review without altering their pixels.
for title,plate in [('Small Parts',5),('Letter',5),('Small Parts - Crate Clips PETG',1)]:
 with zipfile.ZipFile(o.ROOT/(title+'.3mf')) as z:
  n=f'Metadata/plate_{plate}.png'
  if n in z.namelist():(o.WORK/(title+'-preview.png')).write_bytes(z.read(n))
print('Original-source preservation and all seven OpenSCAD entry files passed.')
