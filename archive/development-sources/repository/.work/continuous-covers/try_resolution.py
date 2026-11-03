import json,zipfile,subprocess
from pathlib import Path
W=Path(__file__).resolve().parent
exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
with zipfile.ZipFile(W/'slice/sliced.3mf') as z: base={k:z.read(k) for k in z.namelist()}
for value in [.05]:
    name='r'+str(value);out=W/name;out.mkdir(exist_ok=True)
    files=base.copy();settings=json.loads(files['Metadata/project_settings.config'])
    settings['resolution']=str(value);files['Metadata/project_settings.config']=json.dumps(settings).encode()
    src=W/(name+'.3mf')
    with zipfile.ZipFile(src,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in files.items():z.writestr(k,v)
    with (out/'cli.log').open('w') as f:
        p=subprocess.run([str(exe),'--slice','31','--export-3mf','sliced.3mf','--outputdir',str(out),str(src)],cwd=exe.parent,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print(name,p.returncode,flush=True);p.check_returncode()
    with (out/'paths.log').open('w') as f:
        subprocess.run(['python',str(W/'check_paths.py'),name],cwd=W.parents[1],stdout=f,stderr=subprocess.STDOUT,check=True)
    print([{k:v for k,v in r.items() if k!='joins'} for r in json.loads((W/(name+'-paths.json')).read_text())],flush=True)


