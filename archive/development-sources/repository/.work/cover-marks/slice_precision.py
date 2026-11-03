import json,sys,zipfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
W=ROOT/'.work/cover-marks'
label=sys.argv[1]; resolution=sys.argv[2];arc=sys.argv[3]
with zipfile.ZipFile(ROOT/'.work/cover-crown/staged.3mf') as z:
    files={k:z.read(k) for k in z.namelist()}
s=json.loads(files['Metadata/project_settings.config'])
s.update(resolution=resolution,enable_arc_fitting=arc,print_settings_id='Dara cover diagnostic '+label)
files['Metadata/project_settings.config']=json.dumps(s).encode()
target=W/(label+'.3mf')
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for k,v in files.items():z.writestr(k,v)
out=W/label;out.mkdir(exist_ok=True)
exe=Path(r'C:\Program Files\Bambu Studio\bambu-studio.exe')
with (out/'cli.log').open('w') as log:
    p=subprocess.run([str(exe),'--slice','1','--export-3mf','sliced.3mf','--outputdir',str(out),str(target)],cwd=exe.parent,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
print(label,p.returncode,flush=True)
p.check_returncode()
