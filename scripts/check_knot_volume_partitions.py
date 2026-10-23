"""Compare model extrusion before/after a same-material volume partition.

Usage: python check_knot_volume_partitions.py BEFORE.3mf NATIVE_DIR OUTPUT.json
The source project is the previous distributed release, with identical part
geometry, rotations, infill and cosmetic settings. Tower/support changes are
excluded. Extra internal partition walls would increase outer-wall extrusion.
"""
import sys,re,json,zipfile,hashlib,collections
from pathlib import Path
skip={'Custom','Support','Support interface','Prime tower','Brim','Skirt'}
E=re.compile(r'E([+-]?(?:\d+(?:\.\d*)?|\.\d+))')
def stats(text):
 feature='Custom';s=collections.Counter()
 for line in text.splitlines():
  if line.startswith('; FEATURE: '):feature=line[11:]
  elif line.startswith('G1 ') and feature not in skip and ('X' in line or 'Y' in line):
   e=E.search(line)
   if e and float(e[1])>0:s[feature]+=float(e[1])
 return s
def main(before,native,out):
 rows=[]
 with zipfile.ZipFile(before) as old:
  for pi in range(1,11):
   a=old.read(f'Metadata/plate_{pi}.gcode');b=(native/f'plate_{pi}.gcode').read_bytes();aa,bb=stats(a.decode()),stats(b.decode())
   delta=(sum(bb.values())/sum(aa.values())-1)*100;outer=(bb['Outer wall']/aa['Outer wall']-1)*100
   assert abs(delta)<1 and abs(outer)<1,(pi,delta,outer)
   rows.append(dict(plate=pi,before_gcode_sha256=hashlib.sha256(a).hexdigest(),after_gcode_sha256=hashlib.sha256(b).hexdigest(),
    model_extrusion_change_percent=delta,outer_wall_extrusion_change_percent=outer))
 r=dict(previous_project_sha256=hashlib.sha256(before.read_bytes()).hexdigest(),maximum_absolute_model_extrusion_change_percent=max(abs(x['model_extrusion_change_percent']) for x in rows),
   maximum_absolute_outer_wall_extrusion_change_percent=max(abs(x['outer_wall_extrusion_change_percent']) for x in rows),plates=rows,
   limitation='Compares extrusion amount; combined with exact solid-union and cosmetic-edge geometry checks. Physical seam tests remain required.')
 out.write_text(json.dumps(r,indent=2)+'\n');print('All ten model / outer-wall extrusion comparisons passed',flush=True)
if __name__=='__main__':main(*(Path(x) for x in sys.argv[1:]))
