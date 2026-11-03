from pathlib import Path
import subprocess,json,sys
W=Path(__file__).resolve().parent
variant=sys.argv[1] if len(sys.argv)>1 else 'r2'
exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
inp=W/'r2-editable.3mf' if variant=='r2' else W.parents[1]/'output/Sanding-Block-Quarter-Sheet-A1-PETG/Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'
out=W/(variant+'-slice');out.mkdir(exist_ok=True)
with (W/(variant+'-slice.log')).open('w',encoding='utf8') as f:
 r=subprocess.run([str(exe),'--debug','5','--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(inp)],cwd=exe.parent,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
print('Native slicer exit',r.returncode,flush=True)
assert r.returncode==0
print((out/'result.json').read_text())
