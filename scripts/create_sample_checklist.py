"""Create the two-page Letter checklist for the current three-plate test pack."""
import json
import math
import re
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR=Path(reportlab.__file__).parent/'fonts'
pdfmetrics.registerFont(TTFont('DaraSans',str(FONT_DIR/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('DaraSans-Bold',str(FONT_DIR/'VeraBd.ttf')))

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'output/development/m-veneer-cosmetic-fit'
TARGET=ROOT/'output/pdf/Dara-Sample-Production-Checklist.pdf'
PROJECT='All-Development-Tests-A1'
INK=colors.HexColor('#202020');GRAY=colors.HexColor('#666666');RULE=colors.HexColor('#a6a6a6');PALE=colors.HexColor('#f0f0f0')
W,H=letter;L=36;R=576


def text(c,x,y,s,size=10,bold=False,color=INK):
    c.setFillColor(color);c.setFont('DaraSans-Bold' if bold else 'DaraSans',size);c.drawString(x,y,s)


def line(c,x,y,x2,y2,color=RULE):
    c.setStrokeColor(color);c.setLineWidth(.5);c.line(x,y,x2,y2)


def check(c,x,y,label='',size=9.5):
    c.setStrokeColor(INK);c.setLineWidth(.65);c.rect(x,y-1,9,9,stroke=1,fill=0)
    if label:text(c,x+15,y,label,size)


def blank(c,x,y,label,end):
    text(c,x,y,label,9.5);start=x+c.stringWidth(label,'DaraSans',9.5)+5
    line(c,start,y-2,end,y-2)


def footer(c,page,sha):
    line(c,L,32,R,32)
    text(c,L,19,f'Test project SHA256: {sha[:12]} | Print at 100% on US Letter',8,color=GRAY)
    c.setFont('DaraSans',8);c.setFillColor(GRAY);c.drawRightString(R,19,f'{page} / 2')


def header(c,kicker,title,subtitle):
    text(c,L,755,kicker.upper(),9,True,GRAY)
    text(c,L,730,title,20,True)
    text(c,L,712,subtitle,9.5)
    line(c,L,702,R,702)


def estimate(row):
    h=row['header'];s=next(x for x in h if 'total estimated time:' in x).split('total estimated time: ')[1]
    seconds=sum(int(n)*m for n,u in re.findall(r'(\d+)([hms])',s) for m in [{'h':3600,'m':60,'s':1}[u]])
    minutes=round(seconds/60);weight=sum(map(float,next(x for x in h if 'total filament weight [g]' in x).split(' : ')[1].split(',')))
    return f'{minutes//60}h {minutes%60:02d}m',weight


def production_table(c,y,title,est,weight,labels):
    text(c,L,y,title,11,True)
    text(c,L,y-15,f'Estimate: {est} / {weight:.0f} g',9,color=GRAY)
    blank(c,258,y-15,'Started:',394);blank(c,414,y-15,'Finished:',R)
    top=y-24;cols=[L,356,411,466,521,R]
    c.setFillColor(PALE);c.rect(L,top-19,R-L,19,stroke=0,fill=1)
    heads=['Sample / fixture','Printed','Cleaned','Ready','Redo']
    for i,h in enumerate(heads):
        if i==0:text(c,cols[i]+6,top-13,h,8.5,True)
        else:
            c.setFont('DaraSans-Bold',8.5);c.setFillColor(INK);c.drawCentredString((cols[i]+cols[i+1])/2,top-13,h)
    line(c,L,top,R,top)
    rh=19
    for i,label in enumerate(labels):
        yy=top-19-i*rh;text(c,L+6,yy-13,label,9.5)
        for k in range(1,5):check(c,(cols[k]+cols[k+1])/2-4.5,yy-13)
        line(c,L,yy-rh,R,yy-rh)
    bottom=top-19-len(labels)*rh
    for x in cols:line(c,x,top,x,bottom)
    return bottom-22


def test_panel(c,x,top,width,title,items):
    c.setStrokeColor(RULE);c.setLineWidth(.5);c.rect(x,top-149,width,149,stroke=1,fill=0)
    text(c,x+10,top-18,title,10.5,True)
    for i,s in enumerate(items):check(c,x+10,top-40-i*18,s,9)
    text(c,x+10,top-101,'Result:',9)
    for xx,label in [(x+52,'Good'),(x+111,'Adjust'),(x+180,'Redo')]:check(c,xx,top-101,label,8.5)
    blank(c,x+10,top-123,'Notes:',x+width-10);line(c,x+10,top-140,x+width-10,top-140)


def main():
    guide=json.loads((SOURCE/(PROJECT+'.json')).read_text());report=json.loads((SOURCE/(PROJECT+'-native-validation.json')).read_text())
    assert guide['part_count']==17 and guide['plate_count']==3 and guide['native_slice_validated']
    estimates=[estimate(r) for r in report['plates']]
    labels=[['Glue-test smooth caul','Seam-test smooth caul','Ribbon show-face jig'],
            ['Glue test: core C1','Glue test: core C4','Seam test: core C4',
             'Glue test: continuous veneer + fin carrier','Seam test: upper veneer + fin carrier','Seam test: lower veneer + fin carrier'],
            ['A - existing 0.075 mm: tongue','A - existing 0.075 mm: socket','B - refined 0.075 mm: tongue','B - refined 0.075 mm: socket',
             'C - refined 0.050 mm: tongue','C - refined 0.050 mm: socket','D - refined 0.100 mm: tongue','D - refined 0.100 mm: socket']]
    assert sum(map(len,labels))==17
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(TARGET),pagesize=letter,pageCompression=1)
    c.setTitle('Dara Sample Production Checklist');c.setAuthor('Dara knot project')
    c.setSubject('17 test parts on 3 A1 plates; production, cleanup, fit and finish tracking')
    header(c,'Dara knot / development samples','Sample production checklist','3 A1 plates | 17 parts | About 20h 22m and 305 g total')
    blank(c,L,684,'Name / initials:',267);blank(c,285,684,'Run / date:',R)
    text(c,L,666,'Project: '+PROJECT+'-Sliced.3mf',9)
    text(c,L,649,'Filament slots: 1 white / 2 wood tan / 3 copper silk / 4 Azurite blue',9.5)
    check(c,L,631,'Opened as a project; saved scale, rotations and settings retained.',9)
    text(c,L,615,'Ready = cleaned and usable. Mark Redo when a replacement is needed.',9,color=GRAY)
    y=593
    for i,(title,items) in enumerate(zip(['PLATE 1 - WHITE FIXTURES (3 parts)','PLATE 2 - COPPER M TESTS (6 parts)','PLATE 3 - RIBBON COMPARISONS (8 parts)'],labels)):
        y=production_table(c,y,title,*estimates[i],items)
    text(c,L,76,'Before lifting ribbon parts: mark A-D and tongue/socket on their backs.',9,True)
    blank(c,L,58,'Reprints / print issues:',R)
    footer(c,1,report['native_project_sha256']);c.showPage()
    header(c,'Dara knot / development samples','Fit, finish & decision log','Complete dry-fit checks before glue. Use the matching smooth caul for each M sample.')
    blank(c,L,684,'Name / initials:',267);blank(c,285,684,'Run / date:',R)
    text(c,L,660,'VENEER SUPPORT AND CLEANUP',11,True)
    checks=['Fins and starter shoes stayed attached; veneer was stable during printing.',
            'No unacceptable cupping, chatter marks, cracks or visible-face damage.',
            'Face cradled in a soft-lined caul while fins, tabs and starter shoe were cut away.',
            'Rear remnants trimmed into 0.40 mm recesses; seating pads and locators clean.']
    for i,s in enumerate(checks):check(c,L,642-i*17,s,9.5)
    test_panel(c,L,575,264,'GLUE TEST - CONTINUOUS VENEER',[
        'Core halves seat on a flat reference.', 'Veneer contacts all 3 seating stops.','Seats with light pressure; no rocking.'])
    test_panel(c,312,575,264,'SEAM TEST - TWO VENEERS',[
        'Upper/lower veneers dry-fit on core.','Faces level; seam edges undamaged.','Reflection matches in grazing light.'])
    text(c,L,408,'ADHESIVE / CURE RECORD (if bonded)',11,True)
    blank(c,L,390,'Product:',290);blank(c,308,390,'Mix / batch:',R)
    blank(c,L,372,'Applied:',207);blank(c,224,372,'Full cure due:',398);blank(c,415,372,'Checked:',R)
    check(c,L,354,'Dry fits complete before glue.',9)
    check(c,290,354,'Cured per adhesive instructions.',9)
    blank(c,L,336,'Clamp / liner notes:',R)
    text(c,L,312,'RIBBON COMPARISON RESULTS',11,True)
    text(c,L,296,'Write G = good, A = adjust, R = reprint. Recheck finish and closure after cure, if bonded.',9,color=GRAY)
    cols=[L,184,274,364,454,R];top=283;hh=23;rh=27
    c.setFillColor(PALE);c.rect(L,top-hh,R-L,hh,stroke=0,fill=1)
    for i,s in enumerate(['Variant / nominal gap','Dry closure','Face step','Reflection','After cure']):
        c.setFont('DaraSans-Bold',8.5);c.setFillColor(INK);c.drawCentredString((cols[i]+cols[i+1])/2,top-15,s)
    line(c,L,top,R,top)
    for i,label in enumerate(['A - existing / 0.075 mm','B - refined / 0.075 mm','C - refined / 0.050 mm','D - refined / 0.100 mm']):
        yy=top-hh-i*rh;text(c,L+7,yy-17,label,9.5);line(c,L,yy-rh,R,yy-rh)
    bottom=top-hh-4*rh
    for x in cols:line(c,x,top,x,bottom)
    blank(c,L,133,'Preferred ribbon variant:',237);blank(c,254,133,'Gap (mm):',R)
    text(c,L,113,'M veneer result:',9.5)
    check(c,130,113,'Keep',9);check(c,196,113,'Revise',9);check(c,270,113,'Reprint',9)
    blank(c,359,113,'Parts:',R)
    text(c,L,92,'Observations / next changes:',9.5)
    for yy in [76,58,40]:line(c,L,yy,R,yy)
    footer(c,2,report['native_project_sha256']);c.save()
    print(TARGET)


if __name__=='__main__':main()
