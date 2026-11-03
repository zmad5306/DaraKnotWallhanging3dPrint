"""Stage only white Hilbert work; retain existing stencil changes unstaged."""
import json
import re
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
def git(*args,**kw): return subprocess.check_output(['git',*args],cwd=root,**kw)
assert not git('diff','--cached','--name-only').strip()
paths=['Knot.3mf','scripts/apply_knot_white_hilbert.py','scripts/audit_root_projects.py',
       'release/root-projects/Knot-native.json']
paths+=['release/knot-white-hilbert-r1/'+p for p in
        ['README.md','provenance.json','validation.json','native-result.json','white-blue-before-after.png']]
git('add','--',*paths)
shared=['AGENTS.md','release/root-projects/README.md','release/root-projects/catalog.json','release/root-projects/gcode-sha256.json']
for path in shared:
    head=git('show','HEAD:'+path).decode();work=(root/path).read_text(encoding='utf-8')
    if path.endswith('.json'):
        a,b=json.loads(head),json.loads(work);a['Knot']=b['Knot'];staged=json.dumps(a,indent=2)+'\n'
    elif path=='AGENTS.md':
        start=work.index('- **Approved white knot Hilbert finish,')
        end=work.index('- **Approved knot screw-skin correction,',start)
        marker='## Printer and project identity\n\n'
        assert head.count(marker)==1 and 'Approved white knot Hilbert finish' not in head
        staged=head.replace(marker,marker+work[start:end],1)
    else:
        row=re.search(r'^\| Knot \|.*$',work,re.M)[0]
        staged,count=re.subn(r'^\| Knot \|.*$',lambda _:row,head,flags=re.M);assert count==1
        para=re.search(r'^Knot now uses.*$',work,re.M)[0]
        staged,count=re.subn(r'^Knot now includes.*$',lambda _:para,staged,flags=re.M);assert count==1
    oid=git('hash-object','-w','--stdin',input=staged.encode()).decode().strip()
    git('update-index','--cacheinfo','100644',oid,path)
names=git('diff','--cached','--name-only').decode().splitlines()
assert set(names)==set(paths+shared)
for path in shared[2:]:
    a,b=[json.loads(git('show',ref+':'+path)) for ref in ['HEAD','']]
    assert {k:v for k,v in a.items() if k!='Knot'}=={k:v for k,v in b.items() if k!='Knot'}
assert 'Approved stencil speed revision' not in git('show',':AGENTS.md').decode()
print('Staged',len(names),'Hilbert-only paths. Existing stencil work remains unstaged.')
