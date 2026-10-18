"""Show the cropped socket failure and replacement using actual mesh sections."""
import zipfile
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import Polygon,box
from shapely import get_parts
from development_3mf import OUT,read_object,solid
from develop_m_veneer import prism


def cross_section(body,z):
    result=Polygon()
    for ring in body.slice(z).to_polygons():result=result.symmetric_difference(Polygon(ring))
    return result


def main():
    with zipfile.ZipFile(OUT/'M-Veneer-Glue-Coupon-A1.3mf') as z:files={n:z.read(n) for n in z.namelist()}
    cores=[solid(read_object(files,str(i))[0][0]['mesh']) for i in [1000,1100]]
    old=[body^prism(box(-290,40,-212,94),-.01,14) for body in cores]
    assert [len(s.decompose()) for s in old]==[1,2]
    assert [len(s.decompose()) for s in cores]==[1,1]
    im=Image.new('RGB',(1400,820),'#f6f4ee');d=ImageDraw.Draw(im)
    font='/System/Library/Fonts/Supplemental/Arial.ttf'
    title=ImageFont.truetype(font,27);text=ImageFont.truetype(font,20)
    d.text((35,20),'Glue coupon: mating halves assembled',font=title,fill='#242b2d')
    d.text((35,60),'Actual mesh section at Z = 5 mm. Colors distinguish the two copper core halves.',font=text,fill='#424a4b')
    for n,(solids,label) in enumerate([(old,'Previous: crop opens socket'),(cores,'Corrected: sockets remain enclosed')]):
        ox=45+n*700
        d.rounded_rectangle((ox-20,110,ox+640,800),radius=15,fill='white')
        d.text((ox,125),label,font=title,fill='#242b2d')
        def xy(x,y):return ox+(x+290)*7,200+(94-y)*7
        for i,s in enumerate(solids):
            for p in get_parts(cross_section(s,5)):
                d.polygon([xy(x,y) for x,y in p.exterior.coords],fill=['#cc812e','#77aaba'][i],outline='#343e40',width=1)
                for ring in p.interiors:d.polygon([xy(x,y) for x,y in ring.coords],fill='white')
        px,py=xy(-279,40)
        if n==0:
            d.ellipse((px-30,py-24,px+30,py+24),outline='#c43535',width=4)
            d.text((ox,745),'Smaller half splits into two disconnected chunks.',font=text,fill='#aa2929')
        else:
            d.text((ox,745),'15 mm more depth retains the bottom socket walls.',font=text,fill='#24654d')
    im.save(OUT/'M-glue-coupon-correction.png')


if __name__=='__main__':main()
