"""Render an actual cut through the generated flat core and shaped cap meshes."""
import numpy as np
import trimesh
import shapely
from shapely.geometry import Polygon,box
from PIL import Image,ImageDraw,ImageFont
from development_3mf import OUT,WORK,solid


def section(name,y):
    a=np.load(WORK/(name+'.npz'));m=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
    t=np.eye(4);t[:3,:3]=[[1,0,0],[0,0,1],[0,-1,0]];m.apply_transform(t)
    p=Polygon()
    for ring in solid(m).slice(-y).to_polygons():p=p.symmetric_difference(Polygon(ring))
    return p.intersection(box(-320,-.1,-170,15))


def main():
    core,cap=[section(n,75) for n in ['C1','V1']]
    assert not core.is_empty and not cap.is_empty
    bounds=core.union(cap).bounds;sx=850/(bounds[2]-bounds[0]);sz=20
    def pt(x,z):return 150+(x-bounds[0])*sx,430-z*sz
    im=Image.new('RGB',(1200,650),'#f7f4ee');d=ImageDraw.Draw(im)
    f='/System/Library/Fonts/Supplemental/Arial.ttf';font=lambda n:ImageFont.truetype(f,n)
    d.text((600,28),'Flat structural core / shaped veneer',font=font(32),anchor='mt',fill='#243c4b')
    d.text((600,76),'Actual generated meshes, cut through the left sweep at Y = 75 mm',font=font(21),anchor='mt',fill='#425a64')
    for geometry,color in [(core,'#a8b8bf'),(cap,'#b77848')]:
        for p in shapely.get_parts(geometry):
            if p.geom_type!='Polygon':continue
            d.polygon([pt(x,z) for x,z in p.exterior.coords],fill=color,outline='#34464d',width=2)
            for hole in p.interiors:d.polygon([pt(x,z) for x,z in hole.coords],fill='#f7f4ee',outline='#34464d')
    d.text((600,477),'8.4 mm flat core  +  0.2 mm glue space  +  flat-backed veneer',font=font(24),anchor='mm',fill='#243c4b')
    d.text((600,523),'All convex shaping and hammer texture belong to the veneer.',font=font(23),anchor='mm',fill='#243c4b')
    d.text((600,566),'Veneer: 1.9-4.1 mm before hidden recesses. Finished front profile retained.',font=font(20),anchor='mm',fill='#425a64')
    d.text((600,608),'Vertical scale enlarged for clarity; local seating features are outside this section.',font=font(18),anchor='mm',fill='#586e76')
    im.save(OUT/'M-flat-core-section.png')


if __name__=='__main__':main()
