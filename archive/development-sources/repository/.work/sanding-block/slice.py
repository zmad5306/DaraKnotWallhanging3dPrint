import subprocess
from pathlib import Path
exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
w=Path(__file__).resolve().parent
out=w/'slice-clean';out.mkdir(exist_ok=True)
p=w.parents[1]/'output/Sanding-Block-Quarter-Sheet-A1-PETG/Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'
with (w/'slice.log').open('w',encoding='utf8') as f:
    r=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(p)],
                     cwd=exe.parent,stdout=f,stderr=subprocess.STDOUT,
                     creationflags=subprocess.CREATE_NO_WINDOW)
print('Native slicer exit',r.returncode)
assert r.returncode==0, 'Slice did not complete; do not use older result files.'
print((out/'result.json').read_text() if (out/'result.json').exists() else 'No result.json')
print((w/'slice.log').read_text(encoding='utf8',errors='replace')[-4000:])
