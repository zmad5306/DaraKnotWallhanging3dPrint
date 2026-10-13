"""Publish the fully rebuilt project only after independent matching audits."""
import json,shutil,zipfile
from validate_print_project import ROOT,CAD,digest
from publish_blue_ribbon_edge import main as publish
from refresh_clean_project import WORK,REVIEW

def main():
    candidate=WORK/'complete.3mf';base=json.loads((WORK/'complete.json').read_text())
    integrity=json.loads((WORK/'audit.json').read_text())
    cosmetic=json.loads((REVIEW/'after/review.json').read_text())
    perimeter=json.loads((REVIEW/'perimeter-review.json').read_text())
    geometry=json.loads((REVIEW/'geometry-verification.json').read_text())
    mesh=json.loads((REVIEW/'mesh-edge-review.json').read_text())
    partition=json.loads((REVIEW/'partition-rebuild.json').read_text())
    for r in [integrity,cosmetic,perimeter]:assert r['project_sha256']==digest(candidate)
    assert perimeter['source_cad_sha256']==cosmetic['source_cad_sha256']==geometry['source_cad_sha256']==digest(CAD)
    assert mesh['source_cad_sha256']==partition['source_cad_sha256']==digest(CAD)
    assert mesh['all_passed'] and mesh['parts_checked']==34
    assert partition['maximum_mask_overlap_inside_frame_mm2']<1e-7
    assert integrity['summary']['digital_checks_passed'] and cosmetic['summary']['cosmetic_review_passed']
    assert perimeter['summary']['passed'] and perimeter['summary']['plates_checked']==20
    assert perimeter['summary']['large_arcs_covered']==perimeter['summary']['canonical_large_arcs']==56
    with zipfile.ZipFile(WORK/'baseline.3mf') as a,zipfile.ZipFile(candidate) as b:
        old,new=[json.loads(z.read('Metadata/project_settings.config')) for z in [a,b]]
    diff={k for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}
    assert not (diff-{'name','print_settings_id'}),diff
    base['clean_edges'].update(digital_checks_passed=True,cosmetic_review_passed=True,perimeter_review_passed=True,
                               all_plates_resliced=True,unchanged_slice_settings=True,
                               perimeter_review='working/review/clean-edges/perimeter-review.json')
    (WORK/'complete.json').write_text(json.dumps(base,indent=2)+'\n')
    publish(WORK,'clean_edges')
    shutil.copy2(WORK/'audit.json',REVIEW/'integrity-review.json')
    shutil.copy2(REVIEW/'assembly-color-map.png',ROOT/'working/review/blue-ribbon-edge/assembly-color-map.png')
    print('Published clean native CAD / STLs / all-plate project with matching audits.')

if __name__=='__main__':main()
