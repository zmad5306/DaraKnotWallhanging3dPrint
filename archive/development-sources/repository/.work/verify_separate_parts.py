from pathlib import Path
import sys
sys.path.insert(0,str(Path('.work/python-libs').resolve()))
import trimesh
for part in ['frame','M']:
    mesh=trimesh.load_mesh(f'.work/separate-{part}-check.off')
    print(part,'watertight=',mesh.is_watertight,'consistent_winding=',mesh.is_winding_consistent,'bodies=',len(mesh.split()),'z_bounds=',mesh.bounds[:,2].tolist())
