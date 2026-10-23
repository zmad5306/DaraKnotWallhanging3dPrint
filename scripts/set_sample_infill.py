"""Apply the 8% body-infill trial to existing editable sample projects only.

This settings-only update avoids rebuilding geometry. Run before combining and
native slicing; sliced exports and their validation reports must be refreshed.
The sample generators also set these overrides for clean builds.
"""
import json
import xml.etree.ElementTree as ET
import zipfile
from development_3mf import OUT,props

TARGETS={
    'M-Veneer-Glue-Coupon-A1':2,
    'M-Veneer-Seam-Coupon-A1':1,
    'Frame-Cosmetic-Comparison-A1':2,
}


def verify_sample_infill(path,expected):
    with zipfile.ZipFile(path) as z:
        base=json.loads(z.read('Metadata/project_settings.config'))
        cfg=ET.fromstring(z.read('Metadata/model_settings.config'))
    bodies=[]
    for obj in cfg.findall('object'):
        st=props(obj);label=st.get('name','')
        if label.startswith(('Flat core coupon C','M glue core C','M seam core C')) or label.endswith((' tongue',' socket')):
            effective={**base,**st}
            assert effective['sparse_infill_density']=='8%',(path,label,effective['sparse_infill_density'])
            assert effective['sparse_infill_pattern']=='gyroid',(path,label)
            assert effective['wall_loops']=='4',(path,label)
            bodies.append(label)
        if 'veneer' in label.lower() and 'caul' not in label.lower():
            assert st.get('sparse_infill_density',base['sparse_infill_density'])=='100%',(path,label)
    assert len(bodies)==expected,(path,bodies)
    return dict(body_count=len(bodies),density='8%',pattern='gyroid',wall_loops=4,verified_in_project=str(path.name))


def main():
    for name,count in TARGETS.items():
        path=OUT/(name+'.3mf')
        with zipfile.ZipFile(path) as z:
            entries=z.infolist();files={e.filename:z.read(e) for e in entries}
        key='Metadata/model_settings.config';cfg=ET.fromstring(files[key]);changed=[]
        for obj in cfg.findall('object'):
            label=props(obj).get('name','')
            if not (label.startswith('Flat core coupon C') or label.endswith((' tongue',' socket'))):
                continue
            density=obj.find("metadata[@key='sparse_infill_density']")
            if density is None:density=ET.SubElement(obj,'metadata',key='sparse_infill_density')
            density.set('value','8%');changed.append(label)
        assert len(changed)==count,(name,changed)
        files[key]=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
        temporary=path.with_suffix('.tmp')
        with zipfile.ZipFile(temporary,'w') as z:
            for entry in entries:z.writestr(entry,files[entry.filename])
        with zipfile.ZipFile(path) as before,zipfile.ZipFile(temporary) as after:
            assert all(before.read(e)==after.read(e) for e in before.namelist() if e!=key)
        temporary.replace(path)
        verify_sample_infill(path,count)
        print(name,': 8% gyroid on',', '.join(changed),flush=True)


if __name__=='__main__':main()
