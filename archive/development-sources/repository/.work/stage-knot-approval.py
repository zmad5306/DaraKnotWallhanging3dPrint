import hashlib,json,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def git(*args,**kwargs):return subprocess.check_output(['git',*args],cwd=root,**kwargs)
resume=sys.argv[1:]==['--resume']
if not resume:assert not git('diff','--cached','--name-only').strip(),'Existing staged work must be preserved.'
assert git('rev-parse','HEAD').strip()==git('rev-parse','origin/main').strip()
paths=['.gitattributes','Knot.3mf','README.md','release/root-projects/Knot-native.json',
 'release/root-projects/README.md','release/root-projects/catalog.json','release/root-projects/gcode-sha256.json',
 'scripts/audit_root_projects.py','scripts/validate_print_project.py',
 'working/bambu/Dara-A2L-Knot-Infill-First/README.md']
paths+=['scripts/'+n for n in ['audit_joint_screw_bolster_sample.py','audit_knot_rollback_joints.py',
 'build_joint_photo_retainer_sample.py','build_joint_screw_bolster_sample.py','record_knot_joint_approval.py',
 'revert_knot_infill_first.py','set_knot_normal_supports.py']]
folders=['release/knot-infill-first-revert-r1','release/knot-normal-supports-r1','release/knot-joint-approval-r1',
 'output/Dara-A2L-Joint-Photo-Retainer-Bolster-r2','output/Dara-A2L-Joint-Screw-Bolster-r1']
for folder in folders:
 paths += [p.relative_to(root).as_posix() for p in (root/folder).iterdir() if p.suffix.lower() in ('.json','.md','.png')]
assert all((root/p).is_file() for p in paths)
if resume:
 existing=set(git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0'))
 assert existing==set(paths)|{'AGENTS.md'},'Unexpected staged changes; preserve them.'
head=git('show','HEAD:AGENTS.md').decode('utf-8');work=(root/'AGENTS.md').read_text(encoding='utf-8')
workhash=hashlib.sha256((root/'AGENTS.md').read_bytes()).hexdigest()
# Build the index copy from HEAD and only this chat's agreed Knot additions.
# The unrelated ERYONE paragraph stays intact and unstaged in the working file.
start=work.index('- **Accepted knot joint sample and production publication, 2026-10-25:**')
end=work.index('- **Approved unused filament removal, 2026-10-23:**',start)
block=work[start:end]
assert 'ERYONE spool limits' not in block
staged=head.replace('## Printer and project identity\n\n','## Printer and project identity\n\n'+block,1)
old='  unchanged. In this separate project only, `is_infill_first = 1` replaces 0;\n  each knot object\'s `support_interface_spacing = 0.2` replaces inherited 0.5.\n'
new='  unchanged. At that revision, `is_infill_first = 1` replaced 0; the October 24\n  rollback above supersedes this setting for the current root Knot project.\n  Each knot object\'s `support_interface_spacing = 0.2` replaced inherited 0.5\n  and remains in effect.\n'
assert old in staged;staged=staged.replace(old,new,1)
physical=re.search(r'- \*\*Physical update, 2026-10-24:\*\*.*?(?=- `working/bambu/Dara-A2L-Flush-Joint-Test/`)',work,re.S).group(0)
needle='- `working/bambu/Dara-A2L-Flush-Joint-Test/`';assert needle in staged
staged=staged.replace(needle,physical+needle,1)
(root/'.work/AGENTS-knot-staged.md').write_text(staged,encoding='utf-8',newline='\n')
git('add','--',*paths)
git('add','--renormalize','--',*[p for p in paths if p.endswith('.json') and any(p.startswith(f+'/') for f in folders)])
oid=git('hash-object','-w','--path=AGENTS.md','--stdin',input=staged.encode()).decode().strip()
git('update-index','--cacheinfo','100644,'+oid+',AGENTS.md')
assert hashlib.sha256((root/'AGENTS.md').read_bytes()).hexdigest()==workhash
assert git('show',':AGENTS.md').decode()==staged
actual=set(git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0'))
assert actual==set(paths)|{'AGENTS.md'},actual-(set(paths)|{'AGENTS.md'})
assert not any('Veneers-' in p or 'veneer_eryone' in p for p in actual)
pointer=git('show',':Knot.3mf').decode();assert 'oid sha256:aefab9b242945a149fdc18900c694c556eb7ad5d8d5d5f7fbc4451280730ae46' in pointer
report=json.loads((root/'release/knot-joint-approval-r1/validation.json').read_text())
for name,digest in report['evidence_sha256'].items():assert hashlib.sha256(git('show',':'+name)).hexdigest()==digest,name
(root/'.work/knot-approved-staged-paths.json').write_text(json.dumps(sorted(actual),indent=2))
print(f'Staged {len(actual)} Knot files; unrelated ERYONE instructions/work preserved unstaged. LFS pointer and indexed evidence hashes verified.')
