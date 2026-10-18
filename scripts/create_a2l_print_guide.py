"""Printable maps and production checklist for the 20-plate A2L release."""
import json,math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape,letter
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from shapely.geometry import shape
from shapely.ops import polylabel
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
for name,file in [('Vera','Vera.ttf'),('VeraBold','VeraBd.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path(reportlab.__file__).parent/'fonts'/file)))

def main():
 p=json.loads((OUT/'production-plan.json').read_text());proof=json.loads((OUT/'native-validation.json').read_text());release=json.loads((OUT/'release-validation.json').read_text());est={r['plate']:r for r in release['plate_estimates']}
 target=ROOT/'output/pdf/Dara-A2L-Print-Guide.pdf';c=canvas.Canvas(str(target),pagesize=landscape(letter));W,H=landscape(letter);ink='#263842';colors=['#c6dce7','#d7e8d2','#efdec0','#dad3e8','#edd0cc','#d3d1bd']
 def text(x,y,s,size=10,bold=False):c.setFont('VeraBold' if bold else 'Vera',size);c.setFillColor(HexColor(ink));c.drawString(x,y,s)
 def page(title,sub,num):
  text(30,H-38,title,21,True);text(30,H-56,sub,9)
  text(30,20,f'A2L / 0.4 mm / 0.20 mm | 8% gyroid bodies; solid veneers | SHA {release["project_sha256"][:12]}',8);text(W-65,20,f'{num} / 3',8)
 def geo(g,cx,cy,s,color):
  g=shape(g) if isinstance(g,dict) else g;pp=[g] if g.geom_type=='Polygon' else list(g.geoms);path=c.beginPath()
  for q in pp:
   for ring in [q.exterior,*q.interiors]:
    for i,(x,y) in enumerate(ring.coords):(path.moveTo if i==0 else path.lineTo)(cx+x*s,cy+y*s)
    path.close()
  c.setFillColor(HexColor(color));c.setStrokeColor(HexColor('#667782'));c.setLineWidth(.5);c.drawPath(path,fill=1,stroke=1,fillMode=0)
 def label(g,cx,cy,s,name,plate):
  g=shape(g);q=polylabel(g,tolerance=1);x=cx+q.x*s;y=cy+q.y*s
  c.setFillColor(HexColor('#ffffff'));c.roundRect(x-22,y-11,44,25,3,fill=1,stroke=0);text(x-17,y+3,name,9,True);text(x-17,y-7,f'Plate {plate}',7)
 def table(rows,x,y,width):
  for xx,v in [(x,'Plate / contents'),(x+width-90,'Hours'),(x+width-42,'g')]:text(xx,y,v,9,True)
  for i,(pi,name) in enumerate(rows):
   yy=y-21*(i+1);r=est[pi];text(x,yy,f'{pi:02}  {name}',9);text(x+width-90,yy,f'{r["seconds"]/3600:.1f}',9);text(x+width-42,yy,f'{r["weight_g"]:.0f}',9)
 page('A2L knot: part and joint map','10 freshly partitioned knot sections. 14 joints: six fully hidden, two partly covered, six fully exposed.',1)
 for i,g in enumerate(p['parts']):geo(g,255,307,.45,colors[i%6])
 for i,row in enumerate(p['band_free_M_visibility']):
  j=p['frame_joints'][i];a=math.radians(j[3]);t=(-math.sin(a),math.cos(a));x,y=j[2];h=j[4]/2;c.setStrokeColor(HexColor('#278062' if row['fully_hidden'] else '#b64132'));c.setLineWidth(1.3);c.line(255+(x-h*t[0])*.45,307+(y-h*t[1])*.45,255+(x+h*t[0])*.45,307+(y+h*t[1])*.45)
 for i,g in enumerate(p['parts']):label(g,255,307,.45,f'F{i+1}',i+1)
 table([(i,f'F{i} knot') for i in range(1,11)],515,495,240)
 text(515,245,'Green: concealed behind the band-free M.',8.5);text(515,226,'Red: seam has a visible portion.',8.5)
 text(32,73,'Glue order: '+' > '.join('F'+str(i) for i in p['frame_assembly_order']),10,True)
 text(32,53,'Keep saved rotations. Knot fill directions compensate for each bed rotation; cosmetic edges have zero nominal gap.',8.5);c.showPage()
 page('A2L M: four flat cores, three veneers','All convex crown and hammer texture is in the flat-backed veneer. No seam-cover bands.',2)
 text(87,493,'Flat cores / plates 11-14',13,True);text(483,493,'Veneers / plates 15-17',13,True)
 for i,g in enumerate(p['core_regions']):geo(g,210,320,.43,colors[i]);label(g,210,320,.43,f'C{i+1}',i+11)
 for i,g in enumerate(p['skin_regions']):geo(g,582,320,.43,colors[i]);label(g,582,320,.43,f'V{i+1}',i+15)
 text(32,116,'Cores: constant 8.4 mm main body. Veneer backs: Z8.6. Hidden glue space: 0.20 mm.',9)
 text(32,97,'Two veneer seams total about 24 mm in front projection; their actual front edges match at zero nominal gap.',9)
 text(32,78,'All three veneers share the complete 55-degree lean and in-plane direction. Show planes run along bed Y.',9,True)
 text(32,58,'Do not rotate individual veneers. Clip bonded fins, tabs, starter shoes and perimeter guards; sand hidden backs flat.',8.5);c.showPage()
 page('Production checklist','Print one demanding knot joint and one core / veneer first. Physical fit, silk restraint and finish need confirmation.',3)
 rows=[(i,f'C{i-10} flat core') for i in range(11,15)]+[(i,f'V{i-14} veneer + carrier') for i in range(15,18)]+[(18,'Backers 1, 3, 5, 7'),(19,'Backers 2, 4, 6, 8'),(20,'4 wall blocks + 32 retainers')]
 table(rows,32,505,350)
 checks=['Open the 3MF as a project; verify the A2L profile.','Verify slots: white / tan / copper silk / blue.','Inspect plate preview before each first print.','Print a full joint pair; check fit and 8% stiffness.','Print one full veneer; inspect restraint / cupping.','Trim fins progressively; cradle the hammered face.','Sand rear lands flat; preserve locators and edges.','Dry-fit the four cores on a flat reference.','Dry-fit veneers; inspect both seams in grazing light.','Check matching M pins, screws and screw tips.','Glue in hidden relief; keep stops and edges dry.','Confirm photos, backers, retainers and wall blocks.']
 for i,s in enumerate(checks):
  y=493-i*27;c.setStrokeColor(HexColor(ink));c.rect(416,y-2,8,8,stroke=1,fill=0);text(434,y,s,8.2)
 text(32,245,'Print tracking: mark each plate when complete',11,True)
 for pi in range(1,21):
  col=(pi-1)%10;row=(pi-1)//10;x=37+col*34;y=213-row*28;c.rect(x,y,10,10,stroke=1,fill=0);text(x+13,y+1,str(pi),8)
 text(32,120,f'All 20 plates: {sum(r["seconds"] for r in est.values())/3600:.1f} hours / {sum(r["weight_g"] for r in est.values()):.0f} g including support and purge.',9,True)
 text(32,96,'Filament lot / adhesive: _______________________________________________________________',9)
 text(32,70,'Fit, reflection, cleanup notes: __________________________________________________________',9)
 text(32,45,'___________________________________________________________________________________',9);c.save();print(target)
if __name__=='__main__':main()
