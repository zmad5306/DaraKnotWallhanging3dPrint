exec((__import__('pathlib').Path(__file__).parent/'audit.py').read_text().split('results={}')[0])
results={}
for name,moving,fixed,axis,center,phase in [('rear',parts['Nut'],parts['Tighteneer'],np.array([1.,0,0]),rear_center,202.5),('top',parts['Screw'],parts['Base'],top_axis,top_center,157.5)]:
 dirs=[]
 for sign in [-1,1]:
  series=[]
  for angle in range(-180,181,30):
   v=(rotate_about(moving,phase+angle,axis,center).translate(axis*sign*2*angle/360)^fixed).volume()
   series.append([angle,v])
  dirs.append(dict(sign=sign,collisions=series))
  print(name,'sign',sign,'max',max(v[1] for v in series),flush=True)
 results[name]=dirs
(W/'motion.json').write_text(json.dumps(results,indent=2))
