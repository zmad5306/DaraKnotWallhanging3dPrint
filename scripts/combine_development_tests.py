"""Pack the current 11 test parts onto three A1 plates without reorienting them.

Retain mesh XML exactly, including color modifiers and support paint. Renumber
resource IDs uniquely for Bambu, and change names, XY placement and plate/tower XY.
"""
import copy
import hashlib
import json
import math
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from development_3mf import ROOT,OUT,source_path,save_json,sha,read_object,tag,P,R,transform,props
from build_jointed_bambu_project import model,xml,uid,meta

NAME='All-Development-Tests-A1'
SOURCES=['M-Veneer-Glue-Coupon-A1','M-Veneer-Seam-Coupon-A1','Frame-Cosmetic-Comparison-A1']
# source index, original object id, clear identity, desired plate-local XY centre
LAYOUT=[
 ('White fixtures',[(0,1300,'Glue-test smooth caul',(62,64)),(1,1300,'Seam-test smooth caul',(62,164)),(2,1800,'Ribbon show-face jig',(180,118))]),
 ('Copper M tests',[(0,1000,'M glue core C1',(56,48)),(0,1100,'M glue core C4',(56,128)),(1,1000,'M seam core C4',(56,208)),
                    (0,1200,'M glue veneer - fins and cut tabs',(184,55)),(1,1100,'M seam upper veneer - fins and cut tabs',(184,135)),(1,1200,'M seam lower veneer - fins and cut tabs',(184,215))]),
 ('Zero-gap ribbon test',[(2,1000,'Zero-gap refined tongue',(44,45)),(2,1100,'Zero-gap refined socket',(121.5,45))])]


def main():
    inputs=[]
    for name in SOURCES:
        path=OUT/(name+'.3mf')
        with zipfile.ZipFile(path) as z:f={n:z.read(n) for n in z.namelist()}
        inputs.append(dict(name=name,files=f,root=ET.fromstring(f['3D/3dmodel.model']),cfg=ET.fromstring(f['Metadata/model_settings.config']),
                           staging=json.loads(path.with_suffix('.json').read_text()),sha256=sha(path)))
    base=inputs[0]['files'];settings=json.loads(base['Metadata/project_settings.config'])
    for inp in inputs[1:]:
        other=json.loads(inp['files']['Metadata/project_settings.config'])
        assert {k:v for k,v in settings.items() if k!='print_settings_id'}=={k:v for k,v in other.items() if k!='print_settings_id'}
    settings.update(print_settings_id='All current development tests - A1',print_sequence='by layer',
                    wipe_tower_x=['196']*3,wipe_tower_y=['192']*3)
    out={'[Content_Types].xml':base['[Content_Types].xml'],'_rels/.rels':base['_rels/.rels'],
         'Metadata/project_settings.config':json.dumps(settings,indent=2).encode()}
    root=model();del root.attrib['xmlns:p']
    resources=ET.SubElement(root,tag('resources'));build=ET.SubElement(root,tag('build'),attrib={'{'+P+'}UUID':uid()})
    for k,v in [('Application','BambuStudio-02.08.02.61'),('BambuStudio:3mfVersion','1'),('Title','All development tests - 3 A1 plates'),
                ('Description','11 parts: white fixtures, copper M tests, one zero-gap ribbon pair. Saved finish orientations retained.')]:
        ET.SubElement(root,tag('metadata'),name=k).text=v
    cfg=ET.Element('config');rels=ET.Element('Relationships',xmlns=R)
    records=[];seen=set();columns=2
    for pi,(title,items) in enumerate(LAYOUT):
        plate=ET.SubElement(cfg,'plate')
        for k,v in [('plater_id',pi+1),('plater_name',f'{pi+1} - {title}'),('locked','false'),('filament_map_mode','Auto For Flush'),('filament_maps','1 1 1 1'),('filament_volume_maps','0 0 0 0')]:meta(plate,k,v)
        for si,old_oid,label,xy in items:
            inp=inputs[si];oid=10000+len(records)*100;old_oid=str(old_oid)
            assert (si,old_oid) not in seen;seen.add((si,old_oid))
            old_record=next(r for r in inp['staging']['records'] if str(r['object_id'])==old_oid)
            local=np.array(old_record['assembly_to_printer']);low,high=np.array(old_record['body_bounds_mm'])
            delta=np.array(xy)-(low[:2]+high[:2])/2
            local[:2,3]+=delta
            top=copy.deepcopy(inp['root'].find(tag('resources')).find(f"{tag('object')}[@id='{old_oid}']"));top.set('id',str(oid))
            child_hashes={};part_ids={}
            obj=copy.deepcopy(inp['cfg'].find(f"object[@id='{old_oid}']"));obj.set('id',str(oid))
            for j,co in enumerate(top.find(tag('components')),1):
                old=co.get('{'+P+'}path').lstrip('/');new=f'3D/Objects/source-{si}-{old_oid}.model'
                old_pid=co.get('objectid');new_pid=str(oid+j);part_ids[old_pid]=new_pid
                child=ET.fromstring(out.get(new,inp['files'][old]))
                resource=child.find(tag('resources')).find(f"{tag('object')}[@id='{old_pid}']")
                before=ET.tostring(resource.find(tag('mesh')))
                resource.set('id',new_pid)
                out[new]=xml(child);co.set('{'+P+'}path','/'+new);co.set('objectid',new_pid)
                child_hashes[new_pid]=hashlib.sha256(before).hexdigest()
                assert ET.tostring(resource.find(tag('mesh')))==before
                obj.find(f"part[@id='{old_pid}']").set('id',new_pid)
            resources.append(top)
            ET.SubElement(rels,'Relationship',Target='/'+new,Id=f'rel-{oid}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
            for md in obj.findall('metadata'):
                if md.get('key')=='name':md.set('value',label)
            cfg.append(obj)
            t=local.copy();t[:2,3]+=[pi%columns*307.2,-(pi//columns)*307.2]
            ET.SubElement(build,tag('item'),objectid=str(oid),printable='1',transform=' '.join(format(float(x),'.12g') for x in t[:3].T.reshape(-1)),attrib={'{'+P+'}UUID':uid()})
            inst=ET.SubElement(plate,'model_instance')
            for k,v in [('object_id',oid),('instance_id',0),('identify_id',oid)]:meta(inst,k,v)
            bounds=np.array([low,high]);bounds[:,:2]+=delta
            records.append(dict(name=label,plate=pi+1,object_id=oid,source_project=inp['name']+'.3mf',source_object_id=int(old_oid),
                source_name=old_record['name'],source_plate=old_record['plate'],assembly_to_printer=local.tolist(),body_bounds_mm=bounds.tolist(),
                xy_translation_from_source_mm=delta.tolist(),rotation_and_z_unchanged=True,
                mesh_blocks_byte_identical=child_hashes,part_id_mapping=part_ids))
    assert len(records)==11
    expected=sum(len(i['staging']['records']) for i in inputs);assert len(seen)==expected==11
    out.update({'3D/3dmodel.model':xml(root),'3D/_rels/3dmodel.model.rels':xml(rels),'Metadata/model_settings.config':xml(cfg)})
    path=OUT/(NAME+'.3mf')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in out.items():z.writestr(n,v)
    guide=dict(title='All current development tests',plate_count=3,part_count=11,previous_plate_count=12,
        sources=[dict(file=i['name']+'.3mf',sha256=i['sha256']) for i in inputs],records=records,
        plates=[dict(plate=i+1,name=title,parts=len(items)) for i,(title,items) in enumerate(LAYOUT)],
        filament_slots={'1':'white','2':'wood tan','3':'copper silk','4':'Azurite blue'},
        ribbon_tower_reserved_rectangle_mm=[165,174,250,252],
        ribbon_test=dict(visible_edge_gap_mm=0,pairs=1,additional_adhesive_recess_mm=.2,
            nominal_hidden_glue_clearance_mm=.8,revision='bed-datum-ribbon-v1',
            socket_hidden_back_recess_mm=.8,
            detail='Straight 68 mm coupon sides. Three bed-printed socket feet seat on upward-printed tongue pocket floors at assembly Z0.8. Supported bulk clears to Z5.4; zero-gap show edge above Z8.'),
        m_seam_test=dict(visible_edge_gap_mm=0,veneer_to_core_glue_gap_mm=.2,
            geometry_validation='M-zero-gap-seam-validation.json',full_size_veneers='Zero nominal gap in the current A2L design; production carriers remain on hold pending revised coupon removal'),
        instructions=['Keep saved orientations, scale and filament assignments; open as a project.',
            'Plate 1: white cauls and jig. Use soft liner plus release film on the smooth M cauls.',
            'Plate 2: all six copper test parts. Revised carriers have separate starter ribs, 1.2 mm cut necks and 3 mm rear access; no continuous starter shoe.',
            'Plate 3: one refined zero-gap ribbon pair. Mark tongue/socket on the backs before removing them.',
            'Plate 3 revision: remove supports from the recessed socket underside, foot sides and key pockets. Keep foot bottoms and tongue pocket floors clean. Dry-seat all three feet; inspect the white surface in grazing light before gluing.',
            'Cradle the veneers in lined cauls. Cut each neck flush with the rear lands through its shallow pocket; remove fins and starter ribs progressively, then sand the back flat. Preserve seam edges and locating pockets.',
            'This carrier revision is coupon-only. A2L veneer plates 15-17 remain on hold pending successful physical removal.',
            'Physical fit, silk bonding and finish still require these prints.'],
        source_release_sha256=sha(source_path()),native_slice_validated=False)
    save_json(path.with_suffix('.json'),guide)
    preview(guide,inputs)
    print(f'{path}: 11 parts on 3 plates; source mesh/color/support XML preserved',flush=True)


def preview(guide,inputs):
    im=Image.new('RGB',(1600,650),'#f5f2ec');d=ImageDraw.Draw(im)
    ft='/System/Library/Fonts/Supplemental/Arial.ttf';font=lambda n:ImageFont.truetype(ft,n)
    d.text((800,20),'All development tests — 11 parts, 3 A1 plates',font=font(28),anchor='mt',fill='#243c4b')
    palette={1:'#c8c5ba',2:'#b77542',3:'#6a9bad'}
    for pi,p in enumerate(guide['plates']):
        ox=40+pi*530;oy=110;scale=1.72
        d.text((ox,75),f"{pi+1}. {p['name']}",font=font(22),fill='#243c4b')
        d.rectangle((ox,oy,ox+256*scale,oy+256*scale),fill='white',outline='#aaaaaa',width=2)
        for row in guide['records']:
            if row['plate']!=pi+1:continue
            low,high=np.array(row['body_bounds_mm'])
            x0,y0=ox+low[0]*scale,oy+(256-high[1])*scale;x1,y1=ox+high[0]*scale,oy+(256-low[1])*scale
            d.rounded_rectangle((x0,y0,x1,y1),radius=4,fill=palette[pi+1],outline='#34444a')
            label=row['name'].replace(' - fins and cut tabs','').replace('smooth caul','caul').replace('Ribbon show-face jig','Ribbon jig')
            if pi==2:label='Zero gap '+('T' if 'tongue' in row['name'] else 'S')
            elif pi==1:label=label.replace('M glue','Glue').replace('M seam','Seam').replace('veneer','skin')
            words=label.split();lines=[];line=''
            for word in words:
                q=(line+' '+word).strip()
                if len(q)>13 and line:lines.append(line);line=word
                else:line=q
            lines.append(line)
            d.multiline_text(((x0+x1)/2,(y0+y1)/2),'\n'.join(lines),font=font(16),anchor='mm',align='center',fill='#142b37')
        if pi==2:
            a,b,c,e=guide['ribbon_tower_reserved_rectangle_mm']
            rect=(ox+a*scale,oy+(256-e)*scale,ox+c*scale,oy+(256-b)*scale)
            d.rectangle(rect,outline='#815b37',width=2)
            d.text(((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),'Purge tower',font=font(17),anchor='mm',fill='#815b37')
    d.text((800,590),'Plate map shows part bounding boxes; orientations and finish directions are retained.',font=font(20),anchor='mm',fill='#435d69')
    d.text((800,625),'Ribbon plate: one zero-gap pair. T = tongue, S = socket; glue clearance is underneath.',font=font(20),anchor='mm',fill='#435d69')
    im.save(OUT/(NAME+'-plates.png'))


if __name__=='__main__':main()
