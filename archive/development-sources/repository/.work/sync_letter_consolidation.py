import sys,json,subprocess,hashlib,zipfile
from pathlib import Path
sys.path.insert(0,'scripts')
import organize_root_projects as m
for name in ['.gitignore','README.md']:
    Path(name).write_bytes(subprocess.check_output(['git','show','MERGE_HEAD:'+name]))
p=Path('release/root-projects/catalog.json');catalog=json.loads(p.read_text())
m.TITLES=['Letter'];m.export_cad();new=json.loads(p.read_text());catalog.update(new)
catalog['Letter']['sliced']=False
m.dump(p,catalog)
g=Path('release/root-projects/gcode-sha256.json');d=json.loads(g.read_text());d['Letter']={};m.dump(g,d)
report={'project':'Letter.3mf','sha256':m.sha('Letter.3mf'),'plates':6,'stored_gcode_count':0,'status':'User-saved consolidation; slicing required.','plate_objects':[{ 'name':o['name'],'plate':o['plate']} for o in catalog['Letter']['objects']]}
m.dump(Path('release/root-projects/letter-consolidation.json'),report)
p=Path('README.md');s=p.read_text(encoding='utf-8');s=s.replace('| A2L | 7 | Five M cores','| A2L | 6 | Five M cores');start=s.index('**Letter:**');end=s.index('\n\n',start);s=s[:start]+'**Letter:** user-consolidated six-plate project: C1 on 1, C2 on 2, C3/C4/C5 on 3, and V1/V2/V3 on 4–6. The current user-saved project contains no stored toolpaths and needs slicing in Bambu Studio. Infill-first remains off. The CAD snapshot and catalog match this layout; earlier slice estimates and preservation reports describe the previous seven-plate revision.'+s[end:];s=s.replace('All **seven projects / 31 plates** contain native slices. Knot and the sanding block are byte-identical copies of their approved source projects; Letter retains its seven original slices.','The **seven projects / 30 plates** include six unsliced Letter plates. Knot and the sanding block are byte-identical copies of their approved source projects.');p.write_text(s,encoding='utf-8',newline='\n')
p=Path('release/root-projects/README.md');s=p.read_text(encoding='utf-8');s=s.replace('| Letter | 7 | 72h 20m | 1222.49 g |','| Letter | 6 | Needs slicing | Needs slicing |');s=s.replace('These are slicer estimates, not observed print times.','The Letter project is the user-saved six-plate consolidation and has no stored slices. See `letter-consolidation.json` for its current hash and layout. Previous Letter native/preservation reports and their estimates describe the prior seven-plate project. Other values are slicer estimates, not observed print times.');s=s.replace('Letter retains its existing native slices.','Letter now requires slicing after the user consolidation.');p.write_text(s,encoding='utf-8',newline='\n')
p=Path('AGENTS.md');s=p.read_text(encoding='utf-8');needle='## Printer and project identity\n';s=s.replace(needle,needle+'\n- **User consolidation, 2026-10-22:** the current `Letter.3mf` supersedes the seven-plate layout below: C1 on 1, C2 on 2, C3/C4/C5 on 3, veneers V1/V2/V3 on 4–6. Preserve the exact user-saved project. It has no stored slices and requires slicing before printing.\n');p.write_text(s,encoding='utf-8',newline='\n')
print(report)
