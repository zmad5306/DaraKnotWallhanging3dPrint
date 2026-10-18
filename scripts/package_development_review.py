"""Index the verified development projects and their physical test sequence."""
import json
import zipfile
from development_3mf import ROOT,OUT,source_path,sha,save_json

NAMES=[
    'All-Development-Tests-A1',
    'M-Veneer-Seam-Coupon-A1',
    'M-Veneer-Glue-Coupon-A1',
    'Frame-Cosmetic-Comparison-A1',
    'M-Core-and-Veneer-A1',
    'Frame-Cosmetic-Candidate-A1',
    'M-Solid-Common-Orientation-A1',
]


def main():
    release='d5e57cb2cf359a46a681c052a002d991044ae35f5d5810f134c701953f97d04b'
    assert sha(source_path())==release,'The archived source release was modified'
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
      original_release_sha256=release,original_release_unchanged=True,original_release_file=str(source_path().relative_to(ROOT)),
      main_project='Dara.3mf',main_project_sha256=sha(ROOT/'Dara.3mf'),printer='Bambu Lab A1, 256 x 256 x 256 mm',
      native_slicer='BambuStudio 02.08.02.61',total_verified_plates=sum(p['plate_count'] for p in projects),projects=projects,
      changes=dict(
        M='Six constant-thickness 8.4 mm cores with planar front and back faces, support-free keys, and local seating/registration features. Six flat-backed band-free veneers contain the entire convex profile and hammer texture. Original mounting coordinates and finished front profile retained.',
        veneer='1.90-4.10 mm nominal thickness before hidden pockets; flat back at Z8.6, .20 mm planar glue space; three seating pads, one round locator and one axially relieved locator per face panel.',
        anchors='Full M carriers retain their old starter shoes and are on hold after failed removal. Revised A1 samples use area-allocated fins, separate grounded starter ribs, 1.2 mm cut necks, .40 mm rear recesses and 3 mm cutter access. Trees supplement the bonded tooling.',
        finish='Every veneer shares the complete 55-degree/M5 print rotation, including in-plane direction. One continuous hammer field, without band seats or cover bands.',
        frame='20 sections / 32 existing seam centerlines. Tested 18 mm lap envelope; three hidden seating stops, .20 mm adhesive relief, internal reservoirs, .80 mm secondary-pocket relief and hidden tongue-tip lead-in.',
        grain='Compensated per bed rotation. Native comparison checks white, wood and blue top-fill directions at matching heights; the white rail direction is 135 degrees in assembly.',
        jig='White-face contact pads, 4 mm clearance above the base for texture and 3 mm locating pins. M samples include smooth crown cauls, without hammer dimples, for use with a soft liner and release film.'),
      test_order=[
        dict(file='All-Development-Tests-A1-Sliced.3mf',plates=['1: both white cauls and ribbon jig (3 parts)',
             '2: all copper cores and fin-supported veneers (6 parts)',
             '3: one refined zero-gap ribbon pair (2 parts)'],
             purpose='All 11 current test parts in one project, three plates. Plates 1 and 3 retain their exact prior toolpaths; only copper M test plate 2 changes.')],
      combined_test_plate_map='All-Development-Tests-A1-plates.png',
      combined_test_guide='All-Development-Tests-A1.json',
      sample_infill_trial=dict(body_density='8%',pattern='gyroid',parts='Three M structural coupons and two ribbon test parts',
        retained='Four walls, solid skins, 100% veneers/carriers, prior fixture settings and any local solid modifiers',
        full_size_candidates='Remain at 15% pending physical rigidity and weight comparison'),
      ribbon_zero_gap_revision=dict(visible_edge_gap_mm=0,pairs=1,additional_hidden_adhesive_recess_mm=.2,
        nominal_hidden_glue_clearance_mm=.4,cosmetic_closure_from_z_mm=8,
        retained='18 mm lap, seating stops, secondary-pocket relief, hidden squeeze-out reservoir, 8% gyroid and matched surface direction',
        supersedes='Previous A-D visible-gap comparisons. Full-size frame candidate retains its earlier .075 mm seam pending this test.',
        unchanged_plates_proof='Zero-gap-plate-preservation.json'),
      m_seam_zero_gap_revision=dict(visible_edge_gap_mm=0,veneer_to_core_glue_gap_mm=.2,
        geometry_validation='M-zero-gap-seam-validation.json',
        change='Both seam veneers and their matched core seating are regenerated; smooth caul and plate 1 remain unchanged.',
        full_size_veneers='Zero nominal cosmetic gap is now integrated into the main project; physical confirmation remains pending.'),
      flat_core_revision=dict(core_body_thickness_mm=8.4,core_crown_mm=0,veneer_flat_back_z_mm=8.6,
        all_convex_shaping_in_veneer=True,nominal_veneer_thickness_mm=[1.9,4.1],
        finished_front_and_mount_positions_preserved=True,
        mounting='Existing screw tips pass through the flat core into shallow hidden clearance pockets in the veneer.',
        replace='Earlier crowned-core M test parts are superseded. Use the corrected cores and veneers together.'),
      glue_coupon_correction=dict(reason='The previous crop opened one socket and disconnected a chunk of the smaller core half.',
        change='Extended the sample 15 mm below the old crop, retaining continuous material around both sockets; regenerated matching seating features, veneer and caul.',
        replace='Use all three plates from the updated glue-coupon project together. Earlier glue-coupon parts are superseded.',
        verification='All 11 printed test parts have one connected material body in both editable and native exported meshes. Numerical zero-volume boolean sheets are excluded from component counts.'),
      fin_support_revision=dict(priority='One-off artwork: restraint and surface quality take priority over material use and removal time.',
        coupon_revision='clean-trim-coupon-v1',
        coupon_geometry_and_access='M-clean-trim-carrier-validation.json',
        regression_and_negative_control='M-clean-trim-regression-validation.json',
        production_hold='Full-size A1 carriers and A2L veneer plates 15-17 retain the failed continuous shoe. Confirm revised sample removal before production tooling is updated.',
        full_size_area_revision='M-fin-coverage-validation.json; fins are placed by rear-area coverage rather than removing alternate rows. Counts are allowed above the half-population target where coverage requires it.',
        trial_dimensions=True,physical_confirmation_pending=True,
        verification='All 70 revised coupon necks have clear cutter windows and native model extrusion. Simulated flush trimming leaves no material outside the finished cap. Earliest-layer geometry stays within 2.4 mm of grounded starter contacts; show faces and zero-gap seams are retained. The failed shoe is checked as a negative control. Physical removal and silk bond strength remain pending.',
        test_first='Use the combined project: white fixtures first, then the copper M tests and ribbon comparisons. Full veneers remain candidates pending rigidity, silk bonding, removal, fit and finish results.'),
      assembly_instructions=[
        'Keep saved scale, orientations and object settings. Do not auto-orient veneer panels independently.',
        'Use filament slots 1 white, 2 wood tan, 3 copper silk, 4 blue. Full M parts and their fused carriers use copper; sample cauls/jig use white.',
        'Mark tongue/socket on the ribbon backs before cleanup. Cradle the M face in the lined caul. Cut each narrow neck flush with rear lands through its pocket; remove fins and separate starter ribs progressively. The revised coupons have no continuous starter shoe.',
        'Scrape or sand the hidden tab remnants inside their .40 mm recessed rear pockets, leaving no material above the surrounding underside seating plane. Preserve the hammered face, cosmetic seam edges, seating pads and locating features.',
        'Assemble the structural core on a flat reference surface. Dry-fit the veneer and check all three seating contacts with gentle clamping before adding adhesive.',
        'Apply a controlled amount of the selected epoxy in the relief regions. Keep the hard stops and cosmetic closing edge free of adhesive.',
        'The white M caul is a removable clamp pad, not part of the artwork. Add a soft liner and release film to its smooth crown face. Use release film on the frame jig. Clamp only enough to seat the veneer; inspect the hammered face after cure.',
        'For the new full M, plates 1–6 are C1–C6 cores; 7–12 are V1–V6 veneers/carriers. The five original cover bands are omitted.',
        'Use the full candidate files after the coupons confirm fit, cleanup, reflection and cupping correction. These digital checks do not establish cured bond strength or invisible seams.'
      ],
      original_solid_M_alternative='The six-plate M-Solid-Common-Orientation-A1-Sliced.3mf retains original solid meshes and support paint. All pieces align with the saved M5 rotation; it does not change the original supported structural construction.',
      seam_routing='Frame seam centerlines are retained in this controlled comparison; no artwork or blue-edge feature is rerouted. Band-free M veneer seams follow the original five face divisions, with the band seats removed.',
      independent_geometry_check='Independent-geometry-checks.json',
      previews=['M-flat-core-section.png','All-Development-Tests-A1-plates.png','M-band-free-layout.png','M-veneer-carrier.png','M-veneer-fin-test.png','M-glue-coupon-correction.png'],
      physical_confirmation_pending=True,
      source_references=['https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Support/TreeSupport.cpp',
                         'https://weblog.masukomi.org/2024/03/11/manual-support-fins-for-3d-printing/',
                         'https://github.com/Gluhy/finSTL'])
    save_json(OUT/'manifest.json',report)
    print(json.dumps(dict(branch=report['branch'],verified_plates=report['total_verified_plates'],projects=len(projects)),indent=2))


if __name__=='__main__':main()
