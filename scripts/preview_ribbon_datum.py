"""True mesh sections of the revised ribbon coupon, in assembly coordinates."""
import zipfile
import shapely
from PIL import Image,ImageDraw,ImageFont
from development_3mf import OUT,read_object,solid
from develop_cosmetic_joints import cross_section


def main():
    with zipfile.ZipFile(OUT/'Frame-Cosmetic-Comparison-A1.3mf') as z:files={n:z.read(n) for n in z.namelist()}
    bodies=[solid(read_object(files,oid)[0][0]['mesh']) for oid in ['1000','1100']]
    im=Image.new('RGB',(1500,680),'#f5f2ec');d=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
    d.text((750,25),'Ribbon joint revision — actual mesh sections',font=font(28),anchor='mt',fill='#263d4c')
    for index,(y,title) in enumerate([(1,'Through a datum foot'),(33.6,'Through the outside wall')]):
        ox=48+index*750;oy=480;s=21
        pixel=lambda coords:[(ox+(x+8)*s,oy+z*s) for x,z in coords]
        d.text((ox+320,85),title,font=font(23),anchor='mm',fill='#263d4c')
        for body,color in zip(bodies,['#8aaabd','#be8558']):
            profile=cross_section(body.rotate([90,0,0]),y)
            profile=profile.intersection(shapely.box(-8,-14.5,24,.5))
            for poly in shapely.get_parts(profile):
                if poly.geom_type!='Polygon':continue
                d.polygon(pixel(poly.exterior.coords),fill=color,outline='#334b58')
                for hole in poly.interiors:d.polygon(pixel(hole.coords),fill='#f5f2ec',outline='#334b58')
        for z,label in [(13.6,'White rail datum: Z13.6'),(.8,'Bed-printed datum / pocket floor')]:
            yy=oy-z*s
            d.line((ox,yy,ox+672,yy),fill='#687d85',width=1)
            d.text((ox+8,yy-8),label,font=font(15),anchor='ls',fill='#263d4c')
        caption='Feet locate on flat printed floors; supported bulk has 0.8 mm clearance.' if index==0 else 'Outer skirt covers the relief; no groove through the visible side wall.'
        d.text((ox+330,530),caption,font=font(17),anchor='mm',fill='#334b58')
    d.text((750,590),'Blue: tongue   Copper: receiving lap   Both print in the saved white / tan / blue materials.',font=font(20),anchor='mm',fill='#334b58')
    d.text((750,633),'Receiver back is recessed 0.8 mm. Preserve its saved Z placement and in-plane direction. Physical confirmation pending.',font=font(18),anchor='mm',fill='#526572')
    im.save(OUT/'Ribbon-bed-datum-v1-sections.png')


if __name__=='__main__':main()
