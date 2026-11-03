from pathlib import Path
import re,json
paths=[Path('README.md'),Path('working/bambu/Dara-Photo-Frame-A1-Jointed/README.md'),Path('working/bambu/Dara-Photo-Frame-A1-Jointed/PRINT-READINESS.md')]
bad=[]
for p in paths:
 for s in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if '://' in s or s.startswith('#'):continue
  link=s.split('#')[0]
  if not (p.parent/link).exists():bad.append([str(p),s])
print('Missing local links:',json.dumps(bad));assert not bad
print('Documentation links pass')
