import hashlib,json,zipfile,sys
from pathlib import Path
sys.path.insert(0,'.work/python-libs')
import numpy as np
root=Path.cwd();out=root/'.work/veneer-face-r9';src=root/'Letter.3mf'
report={'status':'UNRESOLVED: reported visible layer offset has not been identified',
 'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'reported_failure':'User reports V1 printed with an ugly line across the part, costing 12 hours and filament. Screenshot attached. Layer and exact printed file hash are not known.',
 'production_files_changed':False,'physical_result':'Reported V1 failure; no correction or subsequent print qualification.',
 'limits':'These numerical checks do not establish acceptable appearance, stability, or print quality. They do not explain or disprove the reported defect.',
 'pending':'Identify the marked layer/Z height and match the screenshot to the saved/native slice.', 'checks':[]}
with zipfile.ZipFile(src) as a,zipfile.ZipFile(out/'native-baseline/baseline.3mf') as b:
 def commands(raw):return b'\n'.join(line.split(b';',1)[0].strip() for line in raw.splitlines() if line.split(b';',1)[0].strip())
 before=commands(a.read('Metadata/plate_4.gcode'));after=commands(b.read('Metadata/plate_4.gcode'))
 report['fresh_native_v1']={'slice_result':json.loads((out/'native-baseline/result.json').read_text()),'command_stream_identical':before==after,'old_commands_sha256':hashlib.sha256(before).hexdigest(),'new_commands_sha256':hashlib.sha256(after).hexdigest(),'process_exit':3221225477,'exit_note':'Process crashed after export; result.json reports success. This is not a clean native process exit.'}
 for i in (1,2,3):
  a=np.load(out/f'V{i}-inset.npy');p=np.load(out/f'V{i}-residual.npz')['layers']
  report['checks'].append({'veneer':f'V{i}','plate':i+3,'observed_front_outer_wall_layers':len(p),'range_print_z_mm':[float(p[0,0]),float(p[-1,0])],
    'missing_0p2_layers':int(np.sum(np.diff(p[:,0])>.201)),
    'median_inset_range_mm':[float(a[:,2].min()),float(a[:,2].max())],
    'maximum_adjacent_layer_median_inset_difference_mm':float(abs(np.diff(a[:,2])).max()),
    'method':'Compare outer-wall centerlines to the saved front surface interpolated in assembly XY; solve horizontal slice-plane intersection. Slice plane uses print Z minus half the 0.2 mm layer. Interpolation uses a Delaunay triangulation of front vertices, so this is a diagnostic approximation, not an exact triangle intersection audit.'})
(out/'unresolved-findings.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('status','source_sha256','production_files_changed','checks')},indent=2))
print('Fresh native V1 command stream identical:',report['fresh_native_v1']['command_stream_identical'])
