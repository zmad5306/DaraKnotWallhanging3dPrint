"""Stage this correction while retaining the pre-existing stencil work unstaged."""
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]


def git(*args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=root, **kwargs)


assert not git('diff', '--cached', '--name-only').strip(), 'Unexpected staged work.'
catalog = json.loads((root / 'release/root-projects/catalog.json').read_text())
paths = ['Knot.3mf', 'scripts/correct_knot_reinforcement_skin.py',
         'scripts/audit_root_projects.py', 'release/root-projects/Knot-native.json']
paths += sorted({p['file'] for o in catalog['Knot']['objects'] for p in o['parts']
                 if p['settings'].get('sparse_infill_density') == '100%'})
paths += ['release/knot-reinforcement-skin-r1/' + p for p in
          ['README.md', 'provenance.json', 'geometry.json', 'validation.json',
           'native-result.json', 'top-surface-before-after.png']]
git('add', '--', *paths)
shared = ['AGENTS.md', 'release/root-projects/README.md',
          'release/root-projects/catalog.json', 'release/root-projects/gcode-sha256.json']
for path in shared:
    head = git('show', 'HEAD:' + path).decode('utf-8')
    work = (root / path).read_text(encoding='utf-8')
    if path.endswith('.json'):
        a, b = json.loads(head), json.loads(work)
        a['Knot'] = b['Knot']
        staged = json.dumps(a, indent=2) + '\n'
    elif path == 'AGENTS.md':
        start = work.index('- **Approved knot screw-skin correction,')
        end = work.index('\n- **Approved stencil speed revision,', start)
        block = work[start:end].strip() + '\n\n'
        marker = '## Printer and project identity\n\n'
        assert head.count(marker) == 1 and 'Approved knot screw-skin correction' not in head
        staged = head.replace(marker, marker + block, 1)
    else:
        row = re.search(r'^\| Knot \|.*$', work, re.M)[0]
        staged, count = re.subn(r'^\| Knot \|.*$', lambda _: row, head, flags=re.M)
        assert count == 1
        paragraph = re.search(r'^Knot now includes.*$', work, re.M)[0]
        staged, count = re.subn(r'^Knot and Sanding Block.*$', lambda _: paragraph, staged, flags=re.M)
        assert count == 1
    oid = git('hash-object', '-w', '--stdin', input=staged.encode()).decode().strip()
    git('update-index', '--cacheinfo', '100644', oid, path)
names = git('diff', '--cached', '--name-only').decode().splitlines()
assert set(names) == set(paths + shared), names
for path in ['release/root-projects/catalog.json', 'release/root-projects/gcode-sha256.json']:
    a, b = [json.loads(git('show', ref + ':' + path)) for ref in ['HEAD', '']]
    assert {k:v for k,v in a.items() if k != 'Knot'} == {k:v for k,v in b.items() if k != 'Knot'}
assert 'Approved stencil speed revision' not in git('show', ':AGENTS.md').decode()
print(f'Staged {len(names)} knot-only paths; existing stencil changes remain unstaged.')
