from pathlib import Path
import sys
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import trimesh
m=trimesh.load_mesh('.work/print-M-check.off')
print('M watertight:',m.is_watertight,'winding consistent:',m.is_winding_consistent,'bodies:',len(m.split()),'Z:',m.bounds[:,2].tolist())
