from pathlib import Path
import json, zipfile, xml.etree.ElementTree as ET
W=Path(__file__).resolve().parent
p=W.parents[1]/'output/Sanding-Block-Quarter-Sheet-A1-PETG/Sanding-Block-Quarter-Sheet-A1-PETG-r1.3mf'
with zipfile.ZipFile(p) as z: files={n:z.read(n) for n in z.namelist()}
s=json.loads(files['Metadata/project_settings.config'])
s.update(enable_support='1',support_type='normal(auto)',support_style='snug',support_threshold_angle='30',
         support_on_build_plate_only='0')
cfg=ET.fromstring(files['Metadata/model_settings.config'])
for o in cfg.findall('object'):
    for e in list(o.findall('metadata')):
        if e.get('key') in ('enable_support','support_type','support_threshold_angle','support_on_build_plate_only'):
            o.remove(e)
files['Metadata/project_settings.config']=json.dumps(s,indent=2).encode()
files['Metadata/model_settings.config']=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
    for n,v in files.items():z.writestr(n,v)
