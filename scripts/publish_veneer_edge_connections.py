"""Publish only hash-validated r7 files and synchronize Letter CAD/catalog."""
import sys,json,shutil,hashlib,zipfile
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'.work/python-libs'),str(Path(__file__).parent)]
from correct_veneer_edge_connections import *
import organize_root_projects as org

def publish():
    before=json.loads((REPORT/'protected-projects-before.json').read_text())
    samplefolder=ROOT/'release/samples';samplefolder.mkdir(exist_ok=True)
    destinations={'Letter':ROOT/'Letter.3mf','ERYONE-r4':samplefolder/'Dara-A2L-Hammered-Finish-ERYONE-r4.3mf'}
    for title,dest in destinations.items():
        report=json.loads((REPORT/(title+'-native.json')).read_text())
        source=WORK/('native-'+title)/'sliced.3mf'
        assert sha(source)==report['native_sha256']
        shutil.copyfile(source,dest)
    for name,digest in before.items():
        if name!='Letter.3mf':assert sha(ROOT/name)==digest,name
    catalog=json.loads((org.REPORT/'catalog.json').read_text())
    previous=catalog['Letter'];org.TITLES=['Letter'];dump=org.dump
    def merged(path,data):
        if path.name=='catalog.json':
            catalog['Letter']={**previous,**data['Letter'],'sliced':True}
            return dump(path,catalog)
        return dump(path,data)
    org.dump=merged;org.export_cad()
    # Catalog export must not change the independent projects or their metadata.
    for title,row in catalog.items():
        assert sha(ROOT/row['project'])==row['sha256']
    gcode=json.loads((org.REPORT/'gcode-sha256.json').read_text())
    with zipfile.ZipFile(ROOT/'Letter.3mf') as z:
        codes={Path(n).stem:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.endswith('.gcode')}
    gcode['Letter']=codes;dump(org.REPORT/'gcode-sha256.json',gcode)
    native=json.loads((REPORT/'Letter-native.json').read_text())
    dump(org.REPORT/'Letter-native.json',native['slicer_result'])
    dump(REPORT/'release.json',dict(main_project='Letter.3mf',main_sha256=sha(ROOT/'Letter.3mf'),
        source_main_sha256=before['Letter.3mf'],main_native_validation='Letter-native.json',
        sample=str(destinations['ERYONE-r4'].relative_to(ROOT)).replace('\\','/'),
        sample_sha256=sha(destinations['ERYONE-r4']),sample_native_validation='ERYONE-r4-native.json',
        unchanged_other_root_projects={k:v for k,v in before.items() if k!='Letter.3mf'},physical_confirmation_pending=True))
    sample=destinations['ERYONE-r4']
    dump(samplefolder/'catalog.json',{'Dara-A2L-Hammered-Finish-ERYONE-r4':dict(file=str(sample.relative_to(ROOT)).replace('\\','/'),sha256=sha(sample),printer='Bambu Lab A2L',revision='r4',validation='release/veneer-edge-r7/ERYONE-r4-native.json')})
    print(json.dumps(json.loads((REPORT/'release.json').read_text()),indent=2))

if __name__=='__main__':publish()
