import subprocess, time, json, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
exe=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
scad=root/'reference/Dara-Clean-Reference.scad'
mode=sys.argv[1]
base=[exe,'--hardwarnings']
if mode not in ('front','angle','back'):
    base.append('--camera=0,0,0,0,0,0,3000')
if mode in ('front','angle','back'):
    view={'front':'0,0,0,0,0,0,3000','angle':'0,0,0,32,0,25,3000','back':'0,0,0,0,180,0,3000'}[mode]
    output=root/'reference'/f'Dara-Clean-Reference-{mode}.png'
    args=['--preview','--imgsize=1800,1800','--camera='+view,'--autocenter','--viewall',
          '--projection=o','--colorscheme=Tomorrow','-o',str(output)]
elif mode=='svg':
    output=root/'reference/Dara-Clean-Reference-drawing.svg'
    args=['-D','view_mode="drawing"','-o',str(output)]
elif mode=='mesh':
    output=root/'.work/reference-render.stl'
    args=['--export-format=binstl','-o',str(output)]
elif mode=='bare':
    output=root/'.work/reference-bare.stl'
    args=['-D','show_fabric=false','--export-format=binstl','-o',str(output)]
else:raise ValueError(mode)
start=time.monotonic()
p=subprocess.run(base+args+[str(scad)],capture_output=True,text=True,timeout=900)
failed = p.returncode != 0 or 'ERROR:' in p.stderr or 'WARNING:' in p.stderr
report={'mode':mode,'returncode':p.returncode,'passed':not failed,'seconds':round(time.monotonic()-start,2),
        'command':base+args+[str(scad)],'stdout':p.stdout,'stderr':p.stderr,
        'output_exists':output.exists(),'bytes':output.stat().st_size if output.exists() else 0}
(root/'.work'/f'render-{mode}.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
sys.exit(1 if failed else 0)
