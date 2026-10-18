"""Engineering previews drawn from generated meshes, not illustrative mockups."""
import json
import math
import zipfile
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape
from development_3mf import ROOT, OUT, WORK, read_object
from develop_m_veneer import axes, crown, skin_bottom
from add_blue_ribbon_edge import artwork

FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
plan=json.loads((OUT/'M-geometry-validation.json').read_text())
cad=(ROOT/'working/Dara-Photo-Frame-A1-Jointed.scad').read_text();outline=artwork(cad,'letter_outline')


def layout():
    im=Image.new('RGB',(2000,1060),'#f5f2ec');d=ImageDraw.Draw(im)
    def pix(points,cx):return [(cx+float(x)*1.35,560-float(y)*1.35) for x,y in points]
    d.text((1000,34),'Band-free M — development candidate',font=font(34,True),anchor='mt',fill='#263d4c')
    d.text((500,130),'Hammered veneer',font=font(27,True),anchor='mt',fill='#263d4c')
    d.text((1500,130),'Independent core and face seams',font=font(27,True),anchor='mt',fill='#263d4c')
    light=np.array([-.3,-.4,1.]);light/=np.linalg.norm(light)
    for i in range(1,7):
        a=np.load(WORK/f'V{i}.npz');m=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
        faces=m.faces[m.face_normals[:,2]>.1];norm=m.face_normals[m.face_normals[:,2]>.1]
        pixels=np.column_stack([500+m.vertices[:,0]*1.35,560-m.vertices[:,1]*1.35])
        lum=np.clip(norm@light,0,1)
        for f,l in zip(faces,lum):
            color=tuple(int(c*(.65+.40*l)) for c in (183,119,75))
            d.polygon([tuple(v) for v in pixels[f]],fill=color)
    palette=['#98b3c5','#d2b690','#a7bea1','#c5acb7','#b2aac9','#d0bf8f']
    for i,row in enumerate(plan['cores']):
        p=shape(row['region']);d.polygon(pix(p.exterior.coords,1500),fill=palette[i])
        d.line(pix(p.exterior.coords,1500),fill='#f5f2ec',width=1)
        pt=p.representative_point();d.text(pix([pt.coords[0]],1500)[0],row['name'],font=font(23,True),anchor='mm',fill='#233b49')
    def seam(j,cx,color,width,dashed=False):
        from shapely.geometry import LineString
        n,t=axes(j);c=np.array(j[2]);h=j[4]/2+20
        cut=LineString([c-t*h,c+t*h]).intersection(outline)
        for segment in ([cut] if cut.geom_type=='LineString' else cut.geoms):
            if segment.geom_type!='LineString':continue
            if not dashed:d.line(pix(segment.coords,cx),fill=color,width=width)
            else:
                for x in np.arange(0,segment.length,6):
                    d.line(pix([segment.interpolate(x).coords[0],segment.interpolate(min(x+3,segment.length)).coords[0]],cx),fill=color,width=width)
    for j in plan['core_joints']:seam(j,1500,'#185c86',3,True)
    for j in plan['skin_joints']:seam(j,1500,'#a53631',3)
    d.text((500,880),'One global hammer field; no cover bands.',font=font(24),anchor='mm',fill='#334b58')
    d.text((1500,875),'Red: veneer seams     Blue dashed: core seams',font=font(23),anchor='mm',fill='#334b58')
    d.text((1000,952),'Nominal veneer gap: 0.075 mm. Seam lines at right are enlarged for review.',font=font(23),anchor='mm',fill='#526572')
    d.text((1000,996),'CAD appearance is not proof of optical matching or physical joint closure.',font=font(22),anchor='mm',fill='#526572')
    im.save(OUT/'M-band-free-layout.png')


def draw_carrier(m,t,c,title,path):
    # Read an angle from the rear so fins and repeated teeth are visible.
    view=np.array([-1,-1,.65]);view/=np.linalg.norm(view)
    u=np.array([1,-1,0.])/math.sqrt(2);v=np.cross(view,u)
    points=m.vertices@np.column_stack([u,v]);low=points.min(axis=0);high=points.max(axis=0)
    scale=min(980/(high-low)[0],740/(high-low)[1]);center=(low+high)/2
    pixels=(points-center)*[scale,-scale]+[600,495]
    depth=m.triangles_center@view;order=np.argsort(depth)
    t=np.array(t);R=t[:3,:3]
    ac=(m.triangles_center-t[:3,3])@R
    floor=skin_bottom(ac[:,:2])
    is_skin=ac[:,2]>floor-.12
    light=np.array([-.5,-.5,1.]);light/=np.linalg.norm(light)
    lum=np.clip(np.abs(m.face_normals@light),0,1)
    im=Image.new('RGB',(1200,1040),'#f5f2ec');d=ImageDraw.Draw(im)
    for i in order:
        color=np.array([181,117,74] if is_skin[i] else [96,117,129])*(.60+.42*lum[i])
        d.polygon([tuple(p) for p in pixels[m.faces[i]]],fill=tuple(color.astype(int)))
    d.text((600,26),title,font=font(29,True),anchor='mt',fill='#263d4c')
    d.text((600,904),f"{c['fin_count']} solid fins; {c['bonded_tooth_count']} tabs; {c['cross_braces']} cross ties; bonded starter shoe.",font=font(23),anchor='mm',fill='#334b58')
    d.text((600,948),'Carrier shaded gray for clarity; the complete part prints in copper silk.',font=font(22),anchor='mm',fill='#526572')
    d.text((600,988),'Cut the tabs individually. Trim inside rear pockets; trees remain additional support.',font=font(21),anchor='mm',fill='#526572')
    im.save(path)


def carrier():
    m=trimesh.load_mesh(WORK/'V1-with-carrier.stl',process=False)
    row=plan['skins'][0]
    draw_carrier(m,row['assembly_to_printer'],row['carrier'],'V1 veneer with sacrificial fins — rear view',OUT/'M-veneer-carrier.png')


def coupon_carrier():
    with zipfile.ZipFile(OUT/'M-Veneer-Glue-Coupon-A1.3mf') as z:files={n:z.read(n) for n in z.namelist()}
    m=read_object(files,'1200')[0][0]['mesh']
    c=json.loads((OUT/'M-Veneer-Glue-Coupon-A1-seating.json').read_text())['panels'][0]['carrier']
    draw_carrier(m,c['assembly_to_printer'],c,'Glue-test veneer with sacrificial fins — rear view',OUT/'M-veneer-fin-test.png')


if __name__=='__main__':layout();carrier();coupon_carrier()
