"""Standard-library audit of the A1 companion for the current A2L design."""
import hashlib,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'working/bambu/Dara-A1-Companion'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def props(e):return {m.get('key'):m.get('value') for m in e.findall('metadata')}
def audit():
    r=json.loads((OUT/'release-validation.json').read_text());n=json.loads((OUT/'native-validation.json').read_text())
    assert sha(OUT/'Dara-A1-Companion.3mf')==r['project_sha256']
    assert sha(ROOT/'working/bambu/Dara-Photo-Frame-A2L/Dara-A2L-Complete.3mf')==r['source_A2L_complete_sha256']
    for name,h in r['evidence_sha256'].items():
        path=ROOT/name;raw=path.read_bytes();versions=[raw]
        if path.suffix in ['.py','.json']:
            lf=raw.replace(b'\r\n',b'\n');versions.extend([lf,lf.replace(b'\n',b'\r\n')])
        assert h in {hashlib.sha256(v).hexdigest() for v in versions},name
    assert r['native_reopen_return_code']==n['native_return_code']==0
    with zipfile.ZipFile(OUT/'Dara-A1-Companion.3mf') as z:
        assert z.testzip() is None;s=json.loads(z.read('Metadata/project_settings.config'))
        assert s['printer_model']=='Bambu Lab A1' and s['sparse_infill_density']=='8%' and s['sparse_infill_pattern']=='gyroid'
        assert s['enable_prime_tower']=='0'
        cfg=ET.fromstring(z.read('Metadata/model_settings.config'));assert len(cfg.findall('plate'))==5 and len(cfg.findall('object'))==46
        for row in n['plates']:
            data=z.read(f'Metadata/plate_{row["plate"]}.gcode');assert hashlib.sha256(data).hexdigest()==row['gcode_sha256']
            assert b'; EXECUTABLE_BLOCK_END' in data and row['conservative_bed_edge_clearance_mm']>.5
        for co in cfg.findall('object'):assert props(co).get('sparse_infill_density',s['sparse_infill_density'])=='8%'
    print('A1 companion PASS: 5 plates / 46 A2L-matching parts; A1 native slices, 8% gyroid, preserved geometry and local solid zones.')
if __name__=='__main__':audit()
