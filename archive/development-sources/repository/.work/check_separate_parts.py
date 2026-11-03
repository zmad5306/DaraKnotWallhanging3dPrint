import subprocess,concurrent.futures
exe=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
def run(mode):
    p=subprocess.run([exe,'--hardwarnings','-D',f'view_mode="{mode}"','--camera=0,0,0,0,0,0,3000','-o',f'.work/separate-{mode}-check.off','working/Dara-Photo-Frame.scad'],capture_output=True,text=True)
    print(mode,p.returncode,p.stderr,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,['M','frame']))
