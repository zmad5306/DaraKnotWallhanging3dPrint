from pathlib import Path
import zipfile,json,hashlib,subprocess,shutil
root=Path.cwd(); work=root/'.work/stencil-speed-r1'; source=root/'Small Parts - Crate Stencils.3mf'
assert not (work/'before.3mf').exists(), 'Snapshot exists; do not overwrite'
shutil.copyfile(source,work/'before.3mf')
protected={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.3mf') if p!=source}
(work/'protected.json').write_text(json.dumps(protected,indent=2))
changes={'initial_layer_infill_speed':(['105'],['50']),'internal_solid_infill_speed':(['250'],['80']),'top_surface_speed':(['200'],['80'])}
with zipfile.ZipFile(source) as z, zipfile.ZipFile(work/'input.3mf','w',zipfile.ZIP_DEFLATED) as out:
 for n in z.namelist():
  data=z.read(n)
  if n=='Metadata/project_settings.config':
   d=json.loads(data)
   for k,(old,new) in changes.items():
    assert d[k]==old,(k,d[k]);d[k]=new
   data=json.dumps(d,indent=2).encode()
  out.writestr(n,data)
exe=Path(r'C:/Program Files/Bambu Studio/bambu-studio.exe')
with (work/'slice.log').open('w') as log:
 p=subprocess.run([str(exe),'--slice','0','--export-3mf','sliced.3mf','--outputdir',str(work/'native'),str(work/'input.3mf')],cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
print('Native slice return code:',p.returncode)
p.check_returncode()
print((work/'native/result.json').read_text())
