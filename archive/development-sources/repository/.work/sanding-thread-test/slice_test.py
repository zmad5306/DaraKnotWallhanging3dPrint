from pathlib import Path
import subprocess,json
W=Path(__file__).resolve().parent
exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
out=W/'slice';out.mkdir(exist_ok=True)
with (W/'slice.log').open('w',encoding='utf8') as f:
 r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(W/'test-editable.3mf')],
  cwd=exe.parent,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
print('Exit',r.returncode,flush=True);assert r.returncode==0
d=json.loads((out/'result.json').read_text());print(json.dumps(d,indent=2))
