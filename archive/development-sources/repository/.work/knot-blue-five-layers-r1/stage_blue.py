"""Stage the blue-depth revision without including existing stencil work."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
def git(*args,**kw):return subprocess.check_output(['git',*args],cwd=root,**kw)
assert not git('diff','--cached','--name-only').strip()
report=json.loads((root/'release/knot-blue-five-layers-r1/validation.json').read_text())
assert hashlib.sha256((root/'Knot.3mf').read_bytes()).hexdigest()==report['project_sha256']
catalog=json.loads((root/'release/root-projects/catalog.json').read_text())
blue=[p['file'] for o in catalog['Knot']['objects'] for p in o['parts'] if p['settings'].get('extruder')=='4']
assert len(blue)==10
paths=['Knot.3mf','scripts/deepen_knot_blue_trim.py','scripts/audit_root_projects.py',
       'release/root-projects/Knot-native.json','release/knot-reinforcement-skin-r1/README.md',
       'release/knot-white-hilbert-removal-r2/README.md']+blue
paths+=['release/knot-blue-five-layers-r1/'+n for n in ['README.md','provenance.json','geometry.json','validation.json','native-result.json']]
shared=['AGENTS.md','release/root-projects/README.md','release/root-projects/catalog.json','release/root-projects/gcode-sha256.json']
git('add','--',*paths)
for path in shared:
    head=git('show','HEAD:'+path).decode();work=(root/path).read_text(encoding='utf-8')
    if path.endswith('.json'):
        a,b=json.loads(head),json.loads(work);a['Knot']=b['Knot'];staged=json.dumps(a,indent=2)+'\n'
    elif path=='AGENTS.md':
        start=work.index('- **Approved deeper blue knot trim,')
        end=work.index('- **Approved knot screw-skin correction,',start)
        hstart=head.index('- **Approved removal of white knot Hilbert finish,')
        hend=head.index('- **Approved knot screw-skin correction,',hstart)
        staged=head[:hstart]+work[start:end]+head[hend:]
    else:
        row=re.search(r'^\| Knot \|.*$',work,re.M)[0]
        staged,count=re.subn(r'^\| Knot \|.*$',lambda _:row,head,flags=re.M);assert count==1
        para=re.search(r'^Knot retains.*$',work,re.M)[0]
        staged,count=re.subn(r'^Knot has returned.*$',lambda _:para,staged,flags=re.M);assert count==1
    oid=git('hash-object','-w','--stdin',input=staged.encode()).decode().strip()
    git('update-index','--cacheinfo','100644',oid,path)
names=git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0')
assert set(names)==set(paths+shared),(set(names)-set(paths+shared),set(paths+shared)-set(names))
for path in shared[2:]:
    a,b=[json.loads(git('show',ref+':'+path)) for ref in ['HEAD','']]
    assert {k:v for k,v in a.items() if k!='Knot'}=={k:v for k,v in b.items() if k!='Knot'}
assert 'Approved stencil speed revision' not in git('show',':AGENTS.md').decode()
print('Staged',len(names),'blue-depth paths only. Unrelated stencil work remains unstaged.')
