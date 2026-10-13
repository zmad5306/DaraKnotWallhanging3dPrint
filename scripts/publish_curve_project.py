"""Publish only the matching native rebuild, all-plate slice and cosmetic audit."""
import json
import shutil
import zipfile

from repair_curve_artifacts import WORK, REVIEW
from validate_print_project import ROOT, CAD, digest
from publish_blue_ribbon_edge import main as publish


def main():
    candidate = WORK/'complete.3mf'
    base = json.loads((WORK/'complete.json').read_text())
    geometry = json.loads((REVIEW/'geometry-verification.json').read_text())
    cosmetic = json.loads((REVIEW/'after/review.json').read_text())
    audit = json.loads((WORK/'audit.json').read_text())
    assert cosmetic['project_sha256'] == audit['project_sha256'] == digest(candidate)
    assert cosmetic['source_cad_sha256'] == geometry['source_cad_sha256'] == digest(CAD)
    assert cosmetic['summary']['cosmetic_review_passed']
    assert cosmetic['summary']['unique_curve_findings'] == 0
    assert audit['summary']['digital_checks_passed']
    assert len(geometry['unchanged_stl_files']) == 32
    with zipfile.ZipFile(WORK/'baseline.3mf') as a, zipfile.ZipFile(candidate) as b:
        old, new = [json.loads(z.read('Metadata/project_settings.config')) for z in (a, b)]
        different = {k:[old.get(k), new.get(k)] for k in old.keys() | new.keys() if old.get(k) != new.get(k)}
    # File/project names are harmless; every slicing setting must survive.
    allowed = {'name', 'print_settings_id'}
    assert not (different.keys()-allowed), different
    base['curve_repair'].update(digital_checks_passed=True, cosmetic_review_passed=True,
                               all_plates_resliced=True, physical_tested=False,
                               cosmetic_review='working/review/curve-repair/after/review.json',
                               unchanged_slice_settings=True)
    (WORK/'complete.json').write_text(json.dumps(base, indent=2)+'\n')
    publish(WORK, 'curve_repair')
    shutil.copy2(WORK/'audit.json', REVIEW/'integrity-review.json')
    shutil.copy2(REVIEW/'assembly-color-map.png', ROOT/'working/review/blue-ribbon-edge/assembly-color-map.png')
    print('Published the independently verified curve repair.')


if __name__ == '__main__':
    main()
