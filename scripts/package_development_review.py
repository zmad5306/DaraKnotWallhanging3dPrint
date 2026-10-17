"""Index the verified development projects and their physical test sequence."""
import json
import zipfile
from development_3mf import ROOT,OUT,sha,save_json

NAMES=[
    'M-Veneer-Seam-Coupon-A1',
    'M-Veneer-Glue-Coupon-A1',
    'Frame-Cosmetic-Comparison-A1',
    'M-Core-and-Veneer-A1',
    'Frame-Cosmetic-Candidate-A1',
    'M-Solid-Common-Orientation-A1',
]


def main():
    release='d5e57cb2cf359a46a681c052a002d991044ae35f5d5810f134c701953f97d04b'
    assert sha(ROOT/'Dara.3mf')==release,'The original release was modified'
    projects=[]
    for name in NAMES:
        report=json.loads((OUT/(name+'-native-validation.json')).read_text())
        staged=OUT/(name+'.3mf');sliced=OUT/(name+'-Sliced.3mf')
        assert sha(staged)==report['staged_sha256'],name
        assert sha(sliced)==report['native_project_sha256'],name
        for path in [staged,sliced]:
            with zipfile.ZipFile(path) as z:assert z.testzip() is None,path
        projects.append(dict(project=sliced.name,editable_source=staged.name,plate_count=report['plate_count'],
                             native_validation=name+'-native-validation.json',
                             minimum_bead_edge_clearance_mm=min(p['conservative_bed_edge_clearance_mm'] for p in report['plates']),
                             native_sha256=report['native_project_sha256']))
    report=dict(branch='codex/m-veneer-cosmetic-fit',status='Implemented and natively sliced; physical coupon confirmation pending',
      original_release_sha256=release,original_release_unchanged=True,printer='Bambu Lab A1, 256 x 256 x 256 mm',
      native_slicer='BambuStudio 02.08.02.61',total_verified_plates=sum(p['plate_count'] for p in projects),projects=projects,
      changes=dict(
        M='Six flat-printed cores with support-free planar keys and six band-free hammered veneers. Veneer seams are independent of core seams. Original rear mounting coordinates and maximum face height retained.',
        veneer='1.35–1.90 mm nominal thickness before hidden pockets; .20 mm glue space; three seating pads, one round locator and one axially relieved locator per face panel.',
        anchors='4–7 fused rear necks per full panel join a connected sacrificial bed frame. Cross braces where space allows. Tree support is additional; the necks have no slicer contact gap.',
        finish='Every veneer shares the complete 55-degree/M5 print rotation, including in-plane direction. One continuous hammer field, without band seats or cover bands.',
        frame='20 sections / 32 existing seam centerlines. Tested 18 mm lap envelope; three hidden seating stops, .20 mm adhesive relief, internal reservoirs, .80 mm secondary-pocket relief and hidden tongue-tip lead-in.',
        grain='Compensated per bed rotation. Native comparison checks white, wood and blue top-fill directions at matching heights; the white rail direction is 135 degrees in assembly.',
        jig='White-face contact pads, 4 mm clearance above the base for texture and 3 mm locating pins. M samples include matching negative face cauls.'),
      test_order=[
        dict(file='M-Veneer-Seam-Coupon-A1-Sliced.3mf',plates=['1: flat core','2: upper veneer with fused carrier','3: lower veneer with fused carrier','4: matched face caul'],purpose='Test exposed seam closure and reflection without bands; assess support cleanup and clamping.'),
        dict(file='M-Veneer-Glue-Coupon-A1-Sliced.3mf',plates=['1: two keyed core halves','2: continuous veneer with fused carrier','3: matched face caul'],purpose='Test structural core fit and whether the veneer seats flat over its joint.'),
        dict(file='Frame-Cosmetic-Comparison-A1-Sliced.3mf',plates=['1: existing .075 mm lap reference','2: refined .075 mm','3: refined .05 mm','4: refined .10 mm','5: show-face jig'],purpose='Compare face step, dry closure, surface direction and cured adhesive seam before choosing a production tolerance.')],
      assembly_instructions=[
        'Keep saved scale, orientations and object settings. Do not auto-orient veneer panels independently.',
        'Use filament slots 1 white, 2 wood tan, 3 copper silk, 4 blue. Full M parts and their fused carriers use copper; sample cauls/jig use white.',
        'Mark part identities on the back before cleanup. Cut the fused necks progressively while supporting the veneer; do not snap the carrier from the face.',
        'Trim the necks inside their recessed rear pockets, leaving no material above the surrounding underside seating plane. Keep the three seating pads and locating features clean.',
        'Assemble the structural core on a flat reference surface. Dry-fit the veneer and check all three seating contacts with gentle clamping before adding adhesive.',
        'Apply a controlled amount of the selected epoxy in the relief regions. Keep the hard stops and cosmetic closing edge free of adhesive.',
        'Use release film on the matching face caul or frame jig. Clamp only enough to seat the veneer; inspect the hammered face after cure.',
        'For the new full M, plates 1–6 are C1–C6 cores; 7–12 are V1–V6 veneers/carriers. The five original cover bands are omitted.',
        'Use the full candidate files after the coupons confirm fit, cleanup, reflection and cupping correction. These digital checks do not establish cured bond strength or invisible seams.'
      ],
      original_solid_M_alternative='The six-plate M-Solid-Common-Orientation-A1-Sliced.3mf retains original solid meshes and support paint. All pieces align with the saved M5 rotation; it does not change the original supported structural construction.',
      seam_routing='Frame seam centerlines are retained in this controlled comparison; no artwork or blue-edge feature is rerouted. Band-free M veneer seams follow the original five face divisions, with the band seats removed.',
      independent_geometry_check='Independent-geometry-checks.json',
      previews=['M-band-free-layout.png','M-veneer-carrier.png'],
      physical_confirmation_pending=True,
      source_references=['https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Support/TreeSupport.cpp'])
    save_json(OUT/'manifest.json',report)
    print(json.dumps(dict(branch=report['branch'],verified_plates=report['total_verified_plates'],projects=len(projects)),indent=2))


if __name__=='__main__':main()
