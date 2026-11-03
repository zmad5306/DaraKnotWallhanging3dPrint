from pathlib import Path
import json
p=Path('working/bambu/Dara-Photo-Frame-A1-Jointed')
for name in ['final-review.json','project-validation.json']:
 f=p/name
 text=f.read_text(encoding='utf-8')
 assert '"current_report": "hammered-integration-validation.json"' in text
 f.write_text(text.replace('"current_report": "hammered-integration-validation.json"','"current_report": "cover-crown-validation.json"'),encoding='utf-8')
f=p/'cover-crown-validation.json'
r=json.loads(f.read_text())
r['cover_finish_status']='Unresolved; investigation deferred at user request on 2026-10-15. The geometric corrections are not a confirmed cure for the printed surface scar.'
f.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
