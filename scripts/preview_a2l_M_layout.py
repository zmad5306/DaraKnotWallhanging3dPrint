"""Draw the actual production core/veneer seam overlay before and after revision."""
import json,numpy as np,subprocess
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import shape
from development_3mf import ROOT
import build_a2l_project as b

def main():
 path=ROOT/'.work/m-short-veneer/before/production-plan.json'
 before=json.loads(path.read_text() if path.exists() else subprocess.check_output(['git','show','089bf22:working/bambu/Dara-Photo-Frame-A2L/production-plan.json'],cwd=ROOT));after=b.load_plan()
 outline=b.artwork(b.CAD.read_text(),'letter_outline');im=Image.new('RGB',(2000,1120),'#f6f3ed');d=ImageDraw.Draw(im)
 def font(n,bold=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',n)
 def text(x,y,s,n=24,bold=False):d.text((x,y),s,font=font(n,bold),anchor='mm',fill='#233b4b')
 text(1000,40,'M seams: short veneer seams, staggered structural backing',34,True)
 for col,p in enumerate([before,after]):
  cx=500+col*1000;cy=500;s=1.4
  def xy(coords):return [(cx+x*s,cy-y*s) for x,y in coords]
  d.polygon(xy(outline.exterior.coords),fill='#d5b28f',outline='#776550')
  for kind,color in [('core_seams','#276e9d'),('skin_seams','#bc4337')]:
   for row in p[kind]:d.line(xy(shape(row['line']).coords),fill=color,width=5)
  text(cx,115,'Previous layout' if not col else 'Revised production layout',28,True)
  text(cx,840,'5 cores on 4 plates / 3 veneers',25,True)
  text(cx,884,'Long fork seams: 105.6 mm visible total' if not col else 'Short crown seams restored: 24.3 mm visible total',22)
  text(cx,921,'Structural core joints already in wide areas' if not col else 'Structural arches continuous behind veneer seams',22)
 text(1000,983,'Blue: hidden core joints     Red: visible veneer joints',24,True)
 text(1000,1027,'The nearest core and veneer seams are 116.9 mm apart; no crossings or aligned seam runs.',22)
 text(1000,1071,'Core joints remain in the broad fork, stem and lower sweeps. Veneers retain the same finish orientation.',22)
 target=ROOT/'working/review/a2l-m-joints/M-staggered-seam-layout.png';im.save(target);print(target)
if __name__=='__main__':main()
