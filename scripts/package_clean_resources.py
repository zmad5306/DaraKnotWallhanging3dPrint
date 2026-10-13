"""Bundle the matching current resources after publication and PDF refresh."""
import json,shutil,zipfile
from pathlib import Path
from validate_print_project import ROOT,PACKAGE,CAD,STLS,digest

NAME='Dara-Clean-Curves-2026-10-13'
DEST=Path(r'C:\Users\Zach\Nextcloud\3D prints\Dara-Solid-Joint-Backs-v26')/NAME

def main():
    audit=json.loads((PACKAGE/'final-review.json').read_text())
    base=json.loads((PACKAGE/'project-validation.json').read_text())
    project=PACKAGE/'Dara-Photo-Frame-A1-Complete.3mf'
    assert audit['summary']['digital_checks_passed'] and base['clean_edges']['perimeter_review_passed']
    assert digest(project)==audit['project_sha256']==base['project_sha256']
    assert digest(CAD)==audit['source_sha256']
    layout=json.loads((ROOT/'.work/part-layout-map/layout-data.json').read_text())
    assert layout['project_sha256']==digest(project)
    files=[CAD,ROOT/'working/Dara-Photo-Frame.scad',ROOT/'working/Dara-Clean-Artwork.scad',ROOT/'working/Dara-Clean-Artwork.svg',ROOT/'working/geometry/clean-frame-primitives.json',ROOT/'output/pdf/Dara-Part-and-Plate-Map.pdf',ROOT/'working/review/curve-artifacts/review.json']
    files += list(STLS.glob('*.stl'))+[STLS/'manifest.json',STLS/'README.md']
    files += [p for p in PACKAGE.iterdir() if p.is_file()]
    files += [p for p in (ROOT/'working/review/clean-edges').rglob('*') if p.is_file() and p.name!='delivery.json']
    files += [ROOT/'working/review/blue-ribbon-edge'/n for n in ['assembly-color-map.png','design.json']]
    files += list((ROOT/'scripts').glob('*.py'))
    checks=ROOT/'working/stl/Dara-Print-Checks'
    files += [checks/n for n in ['Test-Weave-Full-Width.stl','Test-M-Letter.stl','plate-30-manifest.json','plate-31-manifest.json']]
    DEST.mkdir(parents=True,exist_ok=True)
    for source in files:
        dest=DEST/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        assert digest(dest)==digest(source)
    # A distinct filename at the bundle root prevents confusion with prior opens.
    shutil.copy2(project,DEST/(NAME+'.3mf'))
    (DEST/'START-HERE.md').write_text(f'''# Dara clean curves - 2026-10-13

Open **{NAME}.3mf** in Bambu Studio. This is the fully rebuilt and sliced
31-plate project. The copy under working/bambu is byte-identical.

- Production CAD: working/Dara-Photo-Frame-A1-Jointed.scad (self-contained).
- Continuous artwork reference: working/Dara-Clean-Artwork.scad and .svg.
- All 39 production STL files: working/stl/Dara-Photo-Frame-A1-Jointed.
- Current material test STLs: working/stl/Dara-Print-Checks; plates 30 and 31.
- Four-page assembly/plate map: output/pdf/Dara-Part-and-Plate-Map.pdf.
- Measurements and saved toolpath images: working/review/clean-edges/README.md.
- Hardware and assembly order: working/bambu/Dara-Photo-Frame-A1-Jointed/PRINT-READINESS.md.
- Canonical geometry and rebuilding/audit scripts: working/geometry and scripts.

working/Dara-Photo-Frame.scad is the earlier continuous feature model with
synchronized clean artwork. It has the earlier sliding-retainer design; use
the A1-Jointed CAD for the production screw-tab hardware and current clearance.

There are 70 production pieces on plates 1-29, plus two separate material tests.
Use the 3MF to retain color assignments, modifiers, settings and saved slices.
STLs carry geometry only. Slot order is white, wood tan, copper silk, Azurite blue.

The full frame outline, partition trimming, blue edges, photo openings/backers,
native preview meshes and all plate slices have been rebuilt together.
Plate 30 remains the physical surface/color test; no physical print result is
claimed by the digital audits. No printer job was sent.

Project SHA-256: {digest(project)}
CAD SHA-256: {digest(CAD)}

SHA256-MANIFEST.json records every delivered file. Historical traced references,
superseded projects and old hardware coupons are not part of this clean bundle.
''',encoding='utf-8')
    (DEST/'working/stl/Dara-Print-Checks/README.md').write_text('''# Current material tests

Use plate 30 in the complete 3MF for the white/wood/blue weave and edge sample.
Use plate 31 for the copper M sample. Source hashes and slice estimates are in
the two plate manifests. The STL files alone do not contain color settings.
The earlier hardware coupons remain in the historical repository, outside this bundle.
''')
    entries=[dict(file=p.relative_to(DEST).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json']
    manifest=dict(bundle=NAME,project_sha256=digest(project),cad_sha256=digest(CAD),files=entries)
    (DEST/'SHA256-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=DEST.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(DEST.rglob('*')):
            if p.is_file():z.write(p,NAME+'/'+p.relative_to(DEST).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        import hashlib
        for r in entries:assert hashlib.sha256(z.read(NAME+'/'+r['file'])).hexdigest()==r['sha256']
    record=dict(folder=str(DEST),archive=str(archive),archive_sha256=digest(archive),files=len(entries)+1,project_sha256=digest(project),cad_sha256=digest(CAD))
    (ROOT/'working/review/clean-edges/delivery.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
