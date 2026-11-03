import json,subprocess,shutil
from pathlib import Path
p=Path('outputs/Dara-Solid-Joint-Backs-v26').resolve();w=Path('work/slicer').resolve();d=json.loads((p/'project-data.json').read_text());exe='C:/Program Files/Bambu Studio/bambu-studio.exe'
sets=[('01-Knot', [r for r in d['parts'] if '/knot/' in r['file']],False),('02-Manuscript-M',[r for r in d['parts'] if '/letter/' in r['file']],False),('03-Dowels-and-Screw-Mounts',[r for r in d['parts'] if '/hardware/' in r['file'] and not r['part'].startswith('OPTIONAL')],True),('00-Test-First',[r for r in d['parts'] if '/test-first/' in r['file']]+[dict(r,quantity=1) for r in d['parts'] if r['part'] in ['SPLICE_50x18','M_LOCATING_DOWEL']],False)]
sets=[item for item in sets if item[0]!='00-Test-First']
reports=[];out=p/'Bambu-Studio/Grouped-Projects';out.mkdir(exist_ok=True)
for name,parts,solid in sets:
 dest=w/('v26-batch-'+name);dest.mkdir(exist_ok=True)
 profile='process-light-solid.json' if solid else 'process-v26.json'
 cmd=[exe,'--datadir',str(dest/'app-data'),'--load-settings',str(w/'machine.json')+';'+str(w/profile),'--load-filaments',str(w/'filament.json'),'--arrange','1','--orient','0','--slice','0','--clone-objects',','.join(str(r['quantity']) for r in parts),'--export-3mf',name+'.3mf','--outputdir',str(dest)]+[str(p/r['file']) for r in parts]
 if name=='01-Knot':
  i=cmd.index('--slice');del cmd[i:i+2]
 with (dest/'cli.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=600,creationflags=0x08000000)
 report=json.loads((dest/'result.json').read_text()) if (dest/'result.json').exists() else {'return_code':r.returncode,'error_string':'Missing result'}
 count=sum(len(v.get('objects',[])) for v in report.get('sliced_plates',[]));expected=sum(r['quantity'] for r in parts)
 report.update({'project_name':name,'expected_objects':expected,'actual_objects':count,'success':report.get('return_code')==0 and count==expected,'parts':[{'part':r['part'],'copies':r['quantity']} for r in parts]})
 if report['success']:shutil.copy2(dest/(name+'.3mf'),out/(name+'.3mf'))
 reports.append(report);print(name,report['success'],'plates',len(report.get('sliced_plates',[])),'objects',count,expected,flush=True)
 (p/'grouped-project-validation.json').write_text(json.dumps(reports,indent=2))
