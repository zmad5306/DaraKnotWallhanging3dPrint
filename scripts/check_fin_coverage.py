"""Audit actual generated fin contacts on a finer rear-area grid; draw V1 map."""
import json
import hashlib
import math
import numpy as np
import shapely
from PIL import Image,ImageDraw,ImageFont
from scipy.spatial import cKDTree
from shapely.geometry import Point,box,shape
from shapely import union_all
from development_3mf import ROOT,OUT,WORK,save_json,sha
from develop_m_veneer import screw_exclusion
import plan_veneer_fins as coverage


def draw(g,old,new,xy,old_d,new_d):
    im=Image.new('RGB',(1760,1050),'#f5f2ec');d=ImageDraw.Draw(im)
    def font(n,b=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',n)
    def text(x,y,s,n=24,b=False):d.text((x,y),s,font=font(n,b),fill='#263d4c',anchor='mm')
    text(880,42,'V1 rear support coverage — actual fin contacts',32,True)
    x0,y0,x1,y1=g.bounds;s=2.2
    for k,(rows,dist,title) in enumerate([(old,old_d,f'Previous: {len(old)} fins'),(new,new_d,f'Revised: {len(new)} fins')]):
        cx=440+880*k;cy=490
        def pixel(x,y):return (cx+(x-(x0+x1)/2)*s,cy-(y-(y0+y1)/2)*s)
        for p,r in zip(xy,dist):
            # Same absolute distance scale in both panels.
            color='#b5d5cd' if r<=10 else '#e3ce8d' if r<=20 else '#d9846d'
            xx,yy=pixel(*p);d.rectangle([xx-1,yy-1,xx+1,yy+1],fill=color)
        d.line([pixel(*p) for p in g.exterior.coords],fill='#475b64',width=2)
        for row in rows:
            c=row['contacts'];d.line([pixel(c[:,0].min(),c[0,1]),pixel(c[:,0].max(),c[0,1])],fill='#263d4c',width=3)
            for p in c:
                x,y=pixel(*p);d.ellipse((x-2,y-2,x+2,y+2),fill='#a13c33')
        text(cx,145,title,27,True)
        text(cx,822,f'Max rear distance to a bond: {dist.max():.1f} mm',23)
    text(880,893,'Green: within 10 mm     Gold: 10–20 mm     Red: over 20 mm',23)
    text(880,931,'Dark lines: fin contact lanes. Red dots: bonded tabs. Both maps use the same scale.',22)
    text(880,979,'Rear-area geometry check; physical stiffness and silk bonding still require confirmation.',22)
    im.save(OUT/'M-fin-coverage-before-after.png')


def main():
    plan=json.loads((OUT/'M-geometry-validation.json').read_text())
    baseline=ROOT/'working/review/m-fin-density/baseline-fin-contacts.json'
    before=json.loads(baseline.read_text())
    assert hashlib.sha256(json.dumps(plan['skin_regions'],sort_keys=True).encode()).hexdigest()==before['skin_regions_sha256']
    coverage.SAMPLE=.75
    reports=[]
    for i,skin in enumerate(plan['skins']):
        g=shape(plan['skin_regions'][i]);x0,y0,_,y1=g.bounds
        excluded=union_all([Point(*a['xy_mm']).buffer(7) for a in skin['anchors']]).union(screw_exclusion())
        starter=g.intersection(box(x0-1,y0-1,x0+4,y1+1)).difference(excluded)
        xy,w,allow=coverage.area_samples(g)
        sd=shapely.distance(shapely.points(xy),starter)
        rows=[dict(contacts=np.array(r['contacts_xy_mm'])) for r in skin['carrier']['fins']]
        old=[dict(contacts=np.array(r['contacts_xy_mm'])) for r in before['veneers'][i]['fins']]
        measured=coverage.coverage(rows,xy,w,allow,sd)
        original=coverage.coverage(old,xy,w,allow,sd)
        limits=skin['carrier']['area_coverage']['trial_geometric_limits']
        assert measured['area_outside_distance_limit_mm2']==0,(i,measured)
        assert measured['maximum_area_per_bond_mm2']<=limits['maximum_rear_area_per_bond_mm2'],i
        assert measured['maximum_tributary_width_mm']<=limits['maximum_tributary_width_mm'],i
        assert len(rows)==skin['carrier']['fin_count']
        assert not skin['carrier']['tall_fins_without_diagonal_restraint']
        reports.append(dict(veneer=skin['name'],baseline=original,revised=measured,limits=limits,
            trial_geometric_checks_pass=True,physical_rigidity_not_established=True))
        if i==0:
            a=np.minimum(cKDTree(np.concatenate([r['contacts'] for r in old])).query(xy)[0],sd)
            b=np.minimum(cKDTree(np.concatenate([r['contacts'] for r in rows])).query(xy)[0],sd)
            draw(g,old,rows,xy,a,b)
    report=dict(geometry_plan_sha256=sha(OUT/'M-geometry-validation.json'),
        baseline_contacts_sha256=sha(baseline),baseline_commit=before['source_commit'],
        finer_sampling_than_planner=True,validation_grid_mm=.75,
        original_fins=sum(r['baseline']['fin_count'] for r in reports),
        revised_fins=sum(r['revised']['fin_count'] for r in reports),
        veneers=reports,
        limits_basis='At most twice each original panel average rear area per tab and average tributary width; additional local distance guard.',
        scope='Sampled rear geometric coverage and balanced support area. Not FEA or measured print stiffness.',
        physical_confirmation_pending=True)
    save_json(OUT/'M-fin-coverage-validation.json',report)
    print(json.dumps(dict(original_fins=report['original_fins'],revised_fins=report['revised_fins'],
        all_finer_grid_checks_pass=True)))


if __name__=='__main__':main()
