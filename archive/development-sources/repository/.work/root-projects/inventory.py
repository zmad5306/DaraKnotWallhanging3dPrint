import json,zipfile,xml.etree.ElementTree as E,subprocess,pathlib
R=pathlib.Path.cwd()
paths={
'Knot':'working/bambu/Dara-A2L-Knot-Infill-First/Dara-A2L-Knot-Infill-First.3mf',
'Letter':'Dara.3mf',
'Small Parts':'working/bambu/Dara-A1-Companion/Dara-A1-Companion.3mf',
'Center':'output/Dara-Center-Veneer-Alignment-Jig-A1/r3/Dara-Center-Veneer-Alignment-Jig-A1-r3.3mf',
'Sides':'output/Dara-Side-Veneer-Alignment-Jigs-A1/r1/Dara-Side-Veneer-Alignment-Jigs-A1-r1.3mf',
'Crate':'output/Dara-Crate-Clips-A1-PETG-r2/Dara-Crate-Clips-A1-PETG-r2.3mf',
'Photo':'output/Dara-Photo-Tracing-Backers-A1-r1/Dara-Photo-Tracing-Backers-A1-r1.3mf',
'Sanding':'output/Sanding-Block-Quarter-Sheet-A1-PLA-r4/Sanding-Block-Quarter-Sheet-A1-PLA-r4.3mf'}
settings={}
for label,p in paths.items():
 with zipfile.ZipFile(p) as z:
  s=json.loads(z.read('Metadata/project_settings.config'));settings[label]=s
  m=E.fromstring(z.read('Metadata/model_settings.config'))
  print(label, 'plates',len(m.findall('plate')),'objects',len(m.findall('object')),'gcodes',len([n for n in z.namelist() if n.endswith('.gcode')]))
  print({k:s.get(k) for k in ['printer_model','print_settings_id','filament_type','filament_settings_id','layer_height','is_infill_first','enable_prime_tower']})
  if label in ['Center','Sides','Sanding']:
   print('global differences vs accessories:',{k:[settings['Small Parts'].get(k),s.get(k)] for k in sorted(set(s)|set(settings['Small Parts'])) if s.get(k)!=settings['Small Parts'].get(k)})
(R/'.work/root-projects/sources.json').write_text(json.dumps(paths,indent=2))
# Recover requested stencils from the known commit without changing the checkout.
files=subprocess.check_output(['git','ls-tree','-r','--name-only','3005467'],text=True).splitlines()
base=R/'.work/root-projects/stencils';base.mkdir(exist_ok=True)
for p in files:
 if 'christmas-crate-stencils/' not in p and p!='scripts/build_crate_stencils.py':continue
 b=subprocess.check_output(['git','show','3005467:'+p])
 if b.startswith(b'version https://git-lfs.github.com/spec/v1'):
  oid=b.decode().split('oid sha256:')[1].splitlines()[0]
  obj=R/'.git/lfs/objects'/oid[:2]/oid[2:4]/oid
  if not obj.exists():print('MISSING LFS',oid,p);continue
  b=obj.read_bytes()
 (base/pathlib.Path(p).name).write_bytes(b)
print('Recovered stencils:',[p.name for p in base.iterdir()])
