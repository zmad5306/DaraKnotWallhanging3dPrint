from pathlib import Path
import subprocess,json,re,hashlib

CAD=Path('working/Dara-Photo-Frame-A1-Jointed.scad')
OUT=Path('.work/photo-retainers')
EXE=r'C:\Program Files (x86)\OpenSCAD\openscad.exe'
s=CAD.read_text()
assert s.count('sectioned_model();')==1
probe=OUT/'cache-probe.scad'
probe.write_text(s.replace('sectioned_model();',
    'echo(frame_cache=cached_shape_matches("frame"), M_cache=cached_shape_matches("M"), pilot_depth=photo_pilot_depth);'))
cases=[('default',[],True,True,10.7),
       ('pilot-tuning',['photo_pilot_diameter=3.3'],False,True,10.7),
       ('thickness-tuning',['photo_retainer_thickness=2.5'],False,True,11.2),
       ('tab-hole-tuning',['photo_clearance_diameter=4.2'],True,True,10.7),
       ('plain-fabric',['fabric_style="plain"'],False,False,10.7)]
results=[]
for name,defs,frame,letter,depth in cases:
    args=[EXE,'--hardwarnings','--camera=0,0,0,0,0,0,700','-o',str(OUT/'probe.csg')]
    for d in defs:args+=['-D',d]
    p=subprocess.run(args+[str(probe)],capture_output=True,text=True,timeout=30)
    expected=f'ECHO: frame_cache = {str(frame).lower()}, M_cache = {str(letter).lower()}, pilot_depth = {depth}'
    assert p.returncode==0 and expected in p.stderr and 'ERROR:'not in p.stderr and 'WARNING:'not in p.stderr,(name,p.stderr)
    results.append({'case':name,'expected_frame_cache':frame,'expected_M_cache':letter,'pilot_depth_mm':depth,'passed':True})
    print(name,'PASS',flush=True)

report=json.loads((OUT/'verification.json').read_text())
report['cache_parameter_checks']=results
report['preview_renders']=json.loads((OUT/'preview-checks.json').read_text())
assert len(report['preview_renders'])==9 and all(r['ok']for r in report['preview_renders'])
report['source_sha256']=hashlib.sha256(CAD.read_bytes()).hexdigest()
report['review_date']='2026-10-12'
report['CAD_scope']='Photo-retainer revision only; no slicer or production-project changes.'
Path('working/review/photo-retainers/verification.json').write_text(json.dumps(report,indent=2))
print('Final report saved. Max frame XY span:',max(max(r['size_mm'][:2])for r in report['parts']))
print('Minimum open-tab gap:',min(r['open_backer_clearance_mm']for r in report['tabs']))
print('Maximum preview/native difference:',max(r['difference_mm3']for r in report['preview_cache']['native_comparisons']))
