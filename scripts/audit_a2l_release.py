"""Portable standard-library audit of the published A2L project and evidence."""
import hashlib,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'working/bambu/Dara-Photo-Frame-A2L'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def valid_hash(p,expected):
 raw=Path(p).read_bytes()
 if Path(p).suffix in ['.py','.scad','.json']:
  lf=raw.replace(b'\r\n',b'\n');return expected in {hashlib.sha256(b).hexdigest() for b in [raw,lf,lf.replace(b'\n',b'\r\n')]}
 return hashlib.sha256(raw).hexdigest()==expected
def props(e):return {m.get('key'):m.get('value') for m in e.findall('metadata')}
def audit():
 r=json.loads((OUT/'release-validation.json').read_text());n=json.loads((OUT/'native-validation.json').read_text())
 for p in [ROOT/'Dara.3mf',OUT/'Dara-A2L-Complete.3mf']:assert sha(p)==r['project_sha256'],p
 for path,h in r['evidence_sha256'].items():assert valid_hash(ROOT/path,h),path
 assert sha(ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/Dara-Photo-Frame-A1-Complete.3mf')==r['retained_A1_complete_sha256']
 assert sha(ROOT/'output/development/m-veneer-cosmetic-fit/All-Development-Tests-A1-Sliced.3mf')==r['sample_project_sha256']
 assert n['native_return_code']==0 and len(n['plates'])==20
 assert n['native_project_sha256']==r['project_sha256']
 assert r['native_reopen_return_code']==0
 with zipfile.ZipFile(ROOT/'Dara.3mf') as z:
  assert z.testzip() is None
  settings=json.loads(z.read('Metadata/project_settings.config'));assert settings['printer_model']=='Bambu Lab A2L'
  assert settings['sparse_infill_density']=='8%' and settings['sparse_infill_pattern']=='gyroid'
  cfg=ET.fromstring(z.read('Metadata/model_settings.config'));assert len(cfg.findall('plate'))==20
  for co in cfg.findall('object'):
   s=props(co)
   if s.get('name','').startswith('V'):assert s['sparse_infill_density']=='100%'
  for row in n['plates']:
   name=f'Metadata/plate_{row["plate"]}.gcode';data=z.read(name);assert hashlib.sha256(data).hexdigest()==row['gcode_sha256'],name
   assert b'; EXECUTABLE_BLOCK_END' in data
   md5=name+'.md5'
   if md5 in z.namelist():assert z.read(md5).decode().strip().lower()==hashlib.md5(data).hexdigest()
 print('A2L PASS: identical main/alias, 20 native slices, 8% structural / solid veneers, source/evidence hashes, native reopen.')
if __name__=='__main__':audit()
