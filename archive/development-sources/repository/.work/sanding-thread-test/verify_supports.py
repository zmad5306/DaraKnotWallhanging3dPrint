"""Use the established arc-aware thread-envelope audit at translated test poses."""
from pathlib import Path
import json
W=Path(__file__).resolve().parent
source=W.parent/'sanding-thread-review/verify_supports.py'
text=source.read_text()
# Use the existing verified axes and original placement for coordinate mapping.
# Geometry itself is sourced only from saved r2 by build_test.py.
text=text.replace("for variant in ['r1','r2']:","for variant in ['t1']:")
text=text.replace("W/(variant+'-slice/sliced.3mf')","TEST_W/'slice/sliced.3mf'")
text=text.replace("t=printposes[oid];a=(points-t[:3,3])", "t=printposes[oid];a=(points-SHIFTS[oid]-t[:3,3])")
text=text.replace("W/(variant+'-'+name+'-support.npy')","TEST_W/(variant+'-'+name+'-support.npy')")
text=text.replace("W/'r2-support-check.json'","TEST_W/'support-check.json'")
records=json.loads((W/'build.json').read_text())['parts']
ids={'Base':2,'Screw':8,'Tighteneer':4,'Nut':6}
shifts={ids[r['source_part']]:r['source_to_test_translation_mm'] for r in records}
exec(compile(text,str(source),'exec'),{'__file__':str(source),'TEST_W':W,'SHIFTS':shifts})
