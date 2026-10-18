"""Check every active saved veneer against its corrected, validated mesh.

Includes editable projects, native sliced projects and both production aliases.
Frozen reference solid-M projects are historical inputs, not veneer builds.
"""
import json,math,re,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from development_3mf import ROOT,OUT,read_object,props,tag,transform,sha,save_json


def veneers(path):
    with zipfile.ZipFile(path) as z:f={n:z.read(n) for n in z.namelist()}
    settings=json.loads(f['Metadata/project_settings.config']);cfg=ET.fromstring(f['Metadata/model_settings.config'])
    root=ET.fromstring(f['3D/3dmodel.model']);plates=cfg.findall('plate');cols=math.ceil(math.sqrt(len(plates)))
    area=np.array([[float(v) for v in p.split('x')] for p in settings['printable_area']]);pitch=np.ptp(area,axis=0)*1.2
    records=[]
    for pi,plate in enumerate(plates):
        for instance in plate.findall('model_instance'):
            oid=props(instance)['object_id'];obj=cfg.find(f"object[@id='{oid}']");name=props(obj).get('name','')
            if 'veneer' not in name.lower() or 'caul' in name.lower():continue
            parts,_=read_object(f,oid);normal=[p['mesh'] for p in parts if p['subtype']=='normal_part'];assert len(normal)==1
            item=root.find(tag('build')).find(f"{tag('item')}[@objectid='{oid}']")
            T=transform(item.get('transform'));T[:2,3]-=[pi%cols*pitch[0],-(pi//cols)*pitch[1]]
            v=normal[0].vertices@T[:3,:3].T+T[:3,3]
            records.append(dict(name=name,plate=pi+1,points=v,oid=oid))
    return records


def main():
    a2l=ROOT/'working/bambu/Dara-Photo-Frame-A2L';a1=ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed'
    canonical={};proofs=[]
    for family,path,plan in [('A2L',a2l/'Dara-A2L-Editable.3mf',a2l/'M-geometry-validation.json'),
                             ('A1',OUT/'M-Core-and-Veneer-A1.3mf',OUT/'M-geometry-validation.json')]:
        p=json.loads(plan.read_text());rows=veneers(path);assert len(rows)==(3 if family=='A2L' else 6)
        for row,skin in zip(rows,p['skins']):
            c=skin['carrier'];assert c['continuous_starter_shoe'] is False and c['starter_shoe_assembly_x_width_mm']==0
            assert c['cutter_access_necks_checked']==c['bonded_tooth_count']
            assert c['maximum_cutter_access_obstruction_mm3']<1e-5
            assert c['flush_trim_excess_outside_finished_veneer_mm3']<1e-5
            assert not c['tall_fins_without_diagonal_restraint']
            expected={i for i,h in enumerate(c['starter_rib_heights_mm']) if h>48}
            assert set(c['tall_starter_ribs_diagonally_restrained'])==expected
            key=(family,int(re.match(r'V(\d+)',row['name']).group(1)));canonical[key]=row['points']
            proofs.append(dict(family=family,veneer=key[1],cut_necks=c['bonded_tooth_count'],
                no_continuous_shoe=True,maximum_cutter_obstruction_mm3=c['maximum_cutter_access_obstruction_mm3'],
                flush_trim_excess_mm3=c['flush_trim_excess_outside_finished_veneer_mm3']))
    for kind in ['Glue','Seam']:
        path=OUT/f'M-Veneer-{kind}-Coupon-A1.3mf'
        for i,row in enumerate(veneers(path),1):canonical[(kind,i)]=row['points']
    combined=json.loads((OUT/'All-Development-Tests-A1.json').read_text())
    trees={k:cKDTree(v) for k,v in canonical.items()};results=[]
    targets=[ROOT/'Dara.3mf',a2l/'Dara-A2L-Complete.3mf',a2l/'Dara-A2L-Editable.3mf',
        a1/'Dara-Photo-Frame-A1-Complete.3mf']
    targets += [OUT/(stem+suffix+'.3mf') for stem in ['M-Core-and-Veneer-A1','M-Veneer-Glue-Coupon-A1','M-Veneer-Seam-Coupon-A1','All-Development-Tests-A1'] for suffix in ['', '-Sliced']]
    for path in targets:
        rows=veneers(path);assert rows,path
        checks=[]
        for i,row in enumerate(rows,1):
            delta=np.zeros(3)
            if path.name.startswith('All-Development'):
                source=next(r for r in combined['records'] if r['name']==row['name'])
                family='Glue' if 'Glue' in source['source_project'] else 'Seam'
                key=(family,source['source_plate']-1);delta[:2]=source['xy_translation_from_source_mm']
            elif 'Glue-Coupon' in path.name:key=('Glue',i)
            elif 'Seam-Coupon' in path.name:key=('Seam',i)
            else:key=('A2L' if 'A2L' in str(path) or path==ROOT/'Dara.3mf' else 'A1',int(re.match(r'V(\d+)',row['name']).group(1)))
            actual=row['points']-delta;expected=canonical[key]
            error=max(float(trees[key].query(actual)[0].max()),float(cKDTree(actual).query(expected)[0].max()))
            assert error<.001,(path,row['name'],'Stale or changed carrier mesh',error)
            checks.append(dict(name=row['name'],plate=row['plate'],corrected_geometry_maximum_error_mm=error))
        results.append(dict(project=str(path.relative_to(ROOT)),sha256=sha(path),veneers=checks))
        print(path.name,':',len(checks),'corrected veneers',flush=True)
    save_json(OUT/'All-veneer-production-audit.json',dict(production_carriers_checked=9,
        saved_veneer_instances_checked=sum(len(r['veneers']) for r in results),geometry_and_removal_checks=proofs,
        all_saved_projects_match_corrected_geometry=True,projects=results,physical_cleanup_and_bond_strength_pending=True))


if __name__=='__main__':main()
