"""Render the current three-page map from the published veneer release data."""
import json
import hashlib
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape,letter
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from shapely.geometry import shape
from shapely.ops import polylabel

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed'
OUT=ROOT/'output/pdf/Dara-Part-and-Plate-Map.pdf'
FONTS=Path(reportlab.__file__).parent/'fonts'
for name,file in [('Vera','Vera.ttf'),('VeraBold','VeraBd.ttf')]:pdfmetrics.registerFont(TTFont(name,str(FONTS/file)))


def main():
    report=json.loads((PACKAGE/'m-veneer-release-validation.json').read_text())
    assert hashlib.sha256((PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf').read_bytes()).hexdigest()==report['project_sha256']
    plan=json.loads((ROOT/'output/development/m-veneer-cosmetic-fit/M-geometry-validation.json').read_text())
    frame=json.loads((ROOT/'working/geometry/mirrored-frame-layout.json').read_text())
    rows={r['plate']:r for r in report['plate_estimates']}
    cores={f"C{i+1}":r['plate'] for i,r in enumerate(report['changed_m_plates'][:6])}
    veneers={f"V{i+1}":r['plate'] for i,r in enumerate(report['changed_m_plates'][6:])}
    c=canvas.Canvas(str(OUT),pagesize=landscape(letter));W,H=landscape(letter)
    c.setTitle('Dara part and plate map - flat core and veneer M')
    ink='#263842';muted='#536674';colors=['#c6dce7','#d7e8d2','#efdec0','#dad3e8','#edd0cc','#d3d1bd']
    def text(x,y,value,size=10,bold=False,color=ink):
        c.setFont('VeraBold' if bold else 'Vera',size);c.setFillColor(HexColor(color));c.drawString(x,y,value)
    def page(title,subtitle,num):
        text(32,H-40,title,21,True);text(32,H-59,subtitle,9.5)
        text(32,20,f'36 plates | 76 assembly pieces + 1 optional finish sample | SHA256 {report["project_sha256"][:12]}',8,color=muted)
        text(W-65,20,f'{num} / 3',8,color=muted)
    def geometry(g,cx,cy,scale,color):
        polys=[g] if g['type']=='Polygon' else [dict(type='Polygon',coordinates=p) for p in g['coordinates']]
        c.setFillColor(HexColor(color));c.setStrokeColor(HexColor('#5d6a70'));c.setLineWidth(.45)
        path=c.beginPath()
        for p in polys:
            for ring in p['coordinates']:
                for i,(x,y) in enumerate(ring):(path.moveTo if i==0 else path.lineTo)(cx+x*scale,cy+y*scale)
                path.close()
        c.drawPath(path,fill=1,stroke=1,fillMode=0)
    def label(g,cx,cy,scale,name,plate):
        p=shape(g)
        if p.geom_type!='Polygon':p=max(p.geoms,key=lambda g:g.area)
        q=polylabel(p,tolerance=1);x,y=cx+q.x*scale,cy+q.y*scale
        c.setFillColor(HexColor('#ffffff'));c.roundRect(x-23,y-10,46,25,3,fill=1,stroke=0)
        text(x-17,y+4,name,9,True);text(x-17,y-6,f'Plate {plate}',7)
    def table(entries,x,y,width):
        c.setFillColor(HexColor('#e9edef'));c.rect(x,y-19,width,19,fill=1,stroke=0)
        for xx,label in [(x+6,'Plate'),(x+45,'Part'),(x+width-83,'Hours'),(x+width-38,'g')]:text(xx,y-13,label,8,True)
        for i,(number,name) in enumerate(entries):
            yy=y-19-(i+1)*18;r=rows[number]
            for xx,value in [(x+6,f'{number:02d}'),(x+45,name),(x+width-83,f'{r["seconds"]/3600:.1f}'),(x+width-38,f'{r["weight_g"]:.0f}')]:text(xx,yy+5,value,8)
            c.setStrokeColor(HexColor('#c5cdd1'));c.setLineWidth(.4);c.line(x,yy,x+width,yy)
    page('Knot section and plate map','The existing A1 knot remains 20 sections with 32 mirrored joints. Its saved slices are preserved.',1)
    for i,g in enumerate(frame['parts']):geometry(g,254,303,.43,colors[i%len(colors)])
    for i,g in enumerate(frame['parts']):label(g,254,303,.43,f'F{i+1}',i+1)
    table([(i,f'F{i}') for i in range(1,21)],515,510,245)
    text(515,105,'White / wood tan / blue remain in their saved slots.',8.5)
    text(515,89,'Knot zero-gap refinements remain a separate test.',8.5)
    text(32,53,'Keep saved scale and rotations. Open the named A1 Complete project with its saved settings and slices.',9)
    c.showPage()
    page('Flat M core and veneer map','Use the six new cores and six matching veneers together. The original M parts and cover bands are superseded.',2)
    text(87,499,'Flat structural cores',13,True);text(485,499,'Hammered veneers',13,True)
    for i,g in enumerate([r['region'] for r in plan['cores']]):geometry(g,207,322,.43,colors[i])
    for i,g in enumerate([r['region'] for r in plan['cores']]):label(g,207,322,.43,f'C{i+1}',cores[f'C{i+1}'])
    for i,g in enumerate(plan['skin_regions']):geometry(g,583,322,.43,colors[i])
    for i,g in enumerate(plan['skin_regions']):label(g,583,322,.43,f'V{i+1}',veneers[f'V{i+1}'])
    text(32,112,'Cores: flat 8.4 mm main body. Veneers: flat backs with all crown and hammer texture on the front.',9)
    text(32,94,'Zero nominal veneer seam gap. Hidden veneer-to-core glue space: 0.20 mm. No cover bands.',9)
    text(32,76,'V1-V6 share the complete 55-degree orientation. Broad face planes run along bed Y; lean is across X.',9,True)
    text(32,58,'Do not rotate individual veneers. Moving them on the bed preserves direction; automatic reorientation does not.',8.5)
    c.showPage()
    page('M printing and remaining plates','A1 / 0.4 mm nozzle / 0.20 mm layers / textured PEI. Filaments: 1 white, 2 tan, 3 copper silk, 4 blue.',3)
    table([(p,k) for k,p in {**cores,**veneers}.items()],32,510,340)
    table([(27,'Backers 1, 3, 5, 7'),(28,'Backers 2, 4, 6, 8'),(29,'4 wall blocks + 32 retainers'),(30,'Optional finish sample')],402,510,358)
    notes=[
        'Cores: 15% gyroid, 4 walls, 5 top/bottom layers.',
        'Veneers and bonded fin carriers: 100% infill.',
        'Cut recessed necks; remove separate ribs and fins.',
        'V1/V3: remove the sacrificial perimeter guards too.',
        'Trees supplement the carriers; trim deliberately.',
        'Cradle the hammered face while cutting supports.',
        'Sand hidden rear lands flat on the granite plate.',
        'Preserve the stops, locator pockets and seam edges.',
        'Dry-fit all cores and veneers before using adhesive.',
        'Keep glue off the stops and cosmetic closing lands.',
        'Use light clamping, a soft liner and release film.',
        'Physical fit, support removal and finish need checking.',
    ]
    for i,line in enumerate(notes):text(402,369-i*17,line,9)
    text(32,217,'Six-core + six-veneer M estimate:',10,True)
    text(32,198,f'{report["m_weight_g"]:.0f} g / {report["m_seconds"]/3600:.1f} hours including supports',10)
    text(32,169,'The 8% infill trial remains in the sample project.',9)
    text(32,149,'Current samples: All-Development-Tests-A1-Sliced.3mf',8.5)
    text(32,129,'Complete project estimates include optional plate 30.',8.5)
    text(32,75,'Old copper bands on former plate 31 are removed. Plate 31 now prints veneer V1.',9,True)
    text(32,55,'Inspect the native preview before printing. This map follows the saved release plate numbers.',9)
    c.save();print(OUT)


if __name__=='__main__':main()
