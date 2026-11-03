import sys,re,json,math
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
TOKEN=re.compile(r'([A-Z])\s*(-?(?:\d*\.\d+|\d+\.?\d*))')
for i in (1,2,3):
 p=[0.,0.,0.];e=0.;relE=False;relXYZ=False;f=0.;acc=0.;feat='Custom';layer=0.;width=.4
 motions=[];events=[];stats=defaultdict(Counter);speeds=defaultdict(Counter);target=[]
 source=ROOT/f'V{i}.gcode'
 if not source.exists():source=ROOT/f'plate_{i}.gcode'
 for lineno,line in enumerate(source.read_text().splitlines(),1):
  if line.startswith('; Z_HEIGHT: '):layer=float(line.split(': ')[1])
  elif line.startswith('; FEATURE: '):feat=line.split(': ')[1]
  elif line.startswith('; LINE_WIDTH: '):width=float(line.split(': ')[1])
  code=line.split(';')[0].strip()
  if not code:continue
  cmd=code.split()[0];v={k:float(n) for k,n in TOKEN.findall(code)}
  if cmd=='M83':relE=True
  elif cmd=='M82':relE=False
  elif cmd in ('G90','G91'):relXYZ=cmd=='G91'
  elif cmd=='G92':
   p=[v.get(k,old) for k,old in zip('XYZ',p)];e=v.get('E',e)
  elif cmd=='M204':acc=v.get('S',acc)
  if 1<layer<296 and cmd not in ('G0','G1','G2','G3','M204','M73','G92','M106','M991'):
   events.append([layer,lineno,code])
  if cmd=='G92' and any(k in v for k in 'XYZ'):
   events.append([layer,lineno,code])
  if cmd not in ('G0','G1','G2','G3'):continue
  end=[old+v.get(k,0) if relXYZ else v.get(k,old) for k,old in zip('XYZ',p)]
  de=v.get('E',0) if relE else v.get('E',e)-e;f=v.get('F',f)
  dist=math.dist(p[:2],end[:2]);extrude=de>0 and dist>1e-7
  typ=feat if extrude else 'Travel'
  if dist>1e-7 and layer>0 and feat!='Custom':
   stats[typ][acc]+=dist;speeds[typ][f/60]+=dist
   if 134<=layer<=143:
    motions.append(dict(line=lineno,layer=layer,cmd=cmd,start=p.copy(),end=end.copy(),extrude=extrude,feature=feat,speed=f/60,acc=acc,width=width,dist=dist))
  if 138.0<=layer<=139.0 and (cmd!='G1' or not extrude):target.append([layer,lineno,code])
  p=end;e=e+v.get('E',0) if relE else v.get('E',e)
 report=dict(veneer=i,acceleration_path_mm={k:dict(v) for k,v in stats.items()},speed_path_mm={k:dict(v) for k,v in speeds.items()},unusual_commands=events,region_motions=motions,target_nonextrusion=target)
 (ROOT/f'V{i}-motion.json').write_text(json.dumps(report,indent=2))
 print('V',i,'acceleration ranges',{k:[min(v),max(v)] for k,v in stats.items()})
 print('events count',len(events))
 near=[m for m in motions if 138.2<=m['layer']<=138.8]
 print('target acceleration',dict(Counter((m['feature'] if m['extrude'] else 'Travel',m['acc']) for m in near)))
 print('travel max',max(m['speed'] for m in near if not m['extrude']))
