"""Draw the actual production core/veneer seam overlay before and after revision."""
import json,numpy as np,subprocess
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import shape
from development_3mf import ROOT
import build_a2l_project as b

def main():
 path=ROOT/'.work/m-joint-relayout/before/working/bambu/Dara-Photo-Frame-A2L/production-plan.json'
 before=json.loads(path.read_text() if path.exists() else subprocess.check_output(['git','show','9d9eda7:working/bambu/Dara-Photo-Frame-A2L/production-plan.json'],cwd=ROOT));after=b.load_plan()
 outline=b.artwork(b.CAD.read_text(),'letter_outline');im=Image.new('RGB',(2000,1120),'#f6f3ed');d=ImageDraw.Draw(im)
 def font(n,bold=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',n)
 def text(x,y,s,n=24,bold=False):d.text((x,y),s,font=font(n,bold),anchor='mm',fill='#233b4b')
 text(1000,40,'M seams: continuous narrow arches and staggered backing',34,True)
 for col,p in enumerate([before,after]):
  cx=500+col*1000;cy=500;s=1.4
  def xy(coords):return [(cx+x*s,cy-y*s) for x,y in coords]
  d.polygon(xy(outline.exterior.coords),fill='#d5b28f',outline='#776550')
  for kind,color in [('core_seams','#276e9d'),('skin_seams','#bc4337')]:
   for row in p[kind]:d.line(xy(shape(row['line']).coords),fill=color,width=5)
  text(cx,115,'Previous layout' if not col else 'Revised production layout',28,True)
  text(cx,840,'4 cores / 3 veneers' if not col else '5 cores on 4 plates / 3 veneers',25,True)
  text(cx,884,'12 mm crown seams; one narrow core key surround' if not col else 'Both veneer seams moved to the wide fork',22)
  text(cx,921,'Minimal visible length drove poor seam placement' if not col else 'Narrow arch crowns remain continuous in both layers',22)
 text(1000,983,'Blue: hidden core joints     Red: visible veneer joints',24,True)
 text(1000,1027,'No aligned seam runs. One isolated crossing in the fork is about 46 degrees; the layers bridge each other.',22)
 text(1000,1071,'The longer face seams total 105.6 mm. Core key heads have at least 10 mm of surrounding artwork.',22)
 target=ROOT/'working/review/a2l-m-joints/M-staggered-seam-layout.png';im.save(target);print(target)
if __name__=='__main__':main()
