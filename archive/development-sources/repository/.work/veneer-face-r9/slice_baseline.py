import os,subprocess
exe=r'C:\Program Files\Bambu Studio\bambu-studio.exe'
p=subprocess.run([exe,'--slice','4','--export-3mf','baseline.3mf','--outputdir',os.path.abspath('.work/veneer-face-r9/native-baseline'),os.path.abspath('Letter.3mf')],cwd=os.path.dirname(exe),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
print(p.returncode,p.stdout[:5000])
