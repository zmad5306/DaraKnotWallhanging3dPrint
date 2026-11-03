"""Package the validated r4 review candidate without changing production."""
import json
from pathlib import Path
import shutil
import zipfile

from build_veneer_wall_cradle_r4 import ROOT, OUT, WORK, protected
from development_3mf import sha, save_json


def main():
    assert not (OUT/'WITHDRAWN.txt').exists()
    report=json.loads((OUT/'validation.json').read_text())
    assert report['native_total_filament_g'] < 1000
    assert protected()==report['production_and_A1_fingerprints']
    for row in report['plates']:
        assert row['opening_toolpath_checks']['support_segments_inside_openings']==0
    for item in report['files']:
        assert sha(Path(item['final_file']))==item['final_sha256']
        assert sha(Path(item['editable_file']))==item['editable_sha256']
    growth=json.loads((ROOT/'working/review/veneer-restraint-audit/growth-connectivity-r4.json').read_text())
    for i in [1,2,3]:
        original=next(c for c in growth['cases'] if c['veneer']==f'V{i}' and c['revision']=='production')
        candidate=next(c for c in growth['cases'] if c['veneer']==f'V{i}' and c['revision']=='r4')
        for a,b in zip(original['levels'],candidate['levels']):
            for new in b['ungrounded_components']:
                assert any(max(abs(x-y) for x,y in zip(new['bounds_mm'],old['bounds_mm']))<1e-4
                           and abs(new['volume_mm3']-old['volume_mm3'])<1e-5
                           for old in a['ungrounded_components'])
    report['source_geometry_npz_sha256']={f'V{i}':sha(WORK/f'V{i}-candidate.npz') for i in [1,2,3]}
    save_json(OUT/'validation.json',report)
    growth['candidate_geometry_sha256']={f'V{i}':sha(WORK/f'V{i}-candidate.npz') for i in [1,2,3]}
    growth['no_additional_ungrounded_islands_at_sampled_heights']=True
    save_json(OUT/'growth-connectivity.json',growth)
    total=report['native_total_filament_g']
    old=json.loads((ROOT/'output/Dara-A2L-Veneer-Wall-Cradle-r3/validation.json').read_text())
    savings=old['native_total_filament_g']-total
    holes=sum(p['geometry']['opening_count'] for p in report['plates'])
    lines=[]
    for row in report['plates']:
        sec=round(row['estimated_seconds']);h,rem=divmod(sec,3600);m,s=divmod(rem,60)
        lines.append(f"{row['veneer']} (source plate {row['source_plate']}): {row['estimated_filament_g']:.2f} g; {h} h {m} min {s} sec")
    probes=sum(p['bond_toolpath_check']['bond_probes_checked'] for p in report['plates'])
    wall_probes=sum(c['bond_probes_checked'] for p in report['plates'] for c in p['grounded_wall_toolpath_checks'].values())
    text=f'''DARA A2L VENEER WALL CRADLE r4 - 2026-10-21
UNPRINTED REVIEW CANDIDATE - PHYSICAL STIFFNESS AND ANTI-WARP PERFORMANCE UNQUALIFIED

The user requested removal of the outer plate outline and support-free lightening openings. r4 supersedes r3; r1 and r2 remain withdrawn.
The continuous wall structure introduced in r3 remains. A continuous inclined front wall extends down to the bed across its width, with a rear wall and two broad connecting webs.
The original fused attachment necks join the veneer to this modeled wall assembly. Generated tree supports are supplementary, not counted as positive bed ties.
Openings are for material reduction. No production file is replaced and no printer job has been sent.

CURRENT FILES
Native sliced A2L projects: Dara-A2L-Veneer-Wall-Cradle-r4-V1.3mf, -V2.3mf and -V3.3mf. Open as projects.
Matching -Editable.3mf files are the unsliced sources. These are full veneer plates, not cropped samples.
Production Dara.3mf, named A2L complete/editable files, M cores, knot and A1 companion files remain unchanged.

GEOMETRY CHANGE
No long individual starter ribs or fin end posts remain below the retained attachment region.
Front wall: 1.20 mm thick, swept down the incline to the bed. Rear wall and both connecting webs: 1.00 mm thick.
The retained original upper carrier stock overlaps the new front sheet; the veneer and attachment geometry at and above assembly Z5.7 is preserved, excluding only the removed low guard/base lead.
The veneer, fused necks, rear pockets, visible texture, seams and seating features are unchanged. The outer 2 mm wide / 1.6 mm high rectangular guard and its now-unused lead are removed. The smaller local base network remains.
The removed outer guard was intended to keep generated tree-support feet away from the plate edge in the original fin design. Native bounds are rechecked after removal.
There are {holes} whole pointed openings across the rear walls and webs: 28 mm wide by 48 mm high, with 60-degree roof slopes. All are inset at least 12 mm from wall edges; grid lands are 16 mm. Rear-wall joins to the webs remain uncut. No openings are added to the inclined backing behind the veneer.
Front-wall upper surface remains at assembly Z4.4, with a nominal 4.2 mm gap to the veneer rear plane; original fused necks cross that gap.
Saved 55-degree lean and in-plane orientation are unchanged. No new attachment to the show face is added.

NATIVE SLICER ESTIMATES - ALL THREE VENEERS AND THEIR SUPPORTS
{chr(10).join(lines)}
TOTAL: {total:.2f} g; {report['native_total_seconds']/3600:.2f} hours.
Headroom to 1,000 g: {1000-total:.2f} g. Reduction from the user's 1,203.88 g estimate: {1203.88-total:.2f} g.
Reduction from r3's 976.94 g native estimate: {savings:.2f} g.
This is a slicer estimate, not measured spool consumption. 

PRESERVED SETTINGS
A2L, 0.4 mm nozzle, 0.20 mm layers and first layer, 4 wall loops, 5 top and bottom layers, Textured PEI Plate.
Global 8% gyroid; veneer and bonded modeled carrier retain the source 100% solid object override. The walls are solid geometry, not sparse infill.
Filament slots remain 1 white, 2 wood tan, 3 copper silk, 4 Azurite blue. These plates extrude copper silk slot 3.
Source tree supports, brim settings, cooling, speeds, accelerations, temperatures and purge settings are preserved.
Only the process display label and tower array indexing differ for the separate single-plate files; tower coordinates are preserved.

CHECKS PERFORMED
Source boolean comparisons preserve the upper geometry except the explicitly removed guard/base lead. Candidate solids are connected and closed.
Editable and native meshes agree within 0.001 mm. Full global/object/volume settings checked; effective constants checked in saved projects and G-code.
All {probes} original attachment-neck probes have nearby MODEL extrusion, excluding slicer support extrusion.
{wall_probes} additional MODEL extrusion probes check the actual wall perimeters at the first layer, 1 mm and 10 mm intervals starting at 5 mm.
Growth connectivity checked at 0.2, 2, 5, 10, 25, 50, 100, 200 and 297.4 mm per veneer (27 combinations).
No additional ungrounded model islands at those heights. A tiny V3 tip at 5 mm is identical to production (about 0.005 mm3).
No generated support extrusion occupies the {holes} lightening openings in the native toolpaths. Roof printing is still physically untested.
Print bounds including bead width (including generated supports), print heights, copper-only model extrusion and checksums checked.
No floating-region or collision warnings; only inherited traditional-timelapse compatibility warnings remain.
Protected production and A1 hashes verified unchanged after all work.

LIMITS
These digital checks do not establish mechanical stiffness, bed adhesion, resistance to silk shrinkage/warping, clean removal or finished appearance.
r4 is unprinted and is not a physically qualified production release. r1/r2 rejections were design feedback, not reported physical print failures.
See wall-structure.png for actual 3D geometry and bed-tie-detail.png for an actual section through a fused neck.
Diagram colors and transparency identify the parts only; all actual material is copper silk. Walls are solid around the openings. The flat gray rectangle under the rendering is a bed illustration, not printed geometry.

SOURCE
{report['source']}
SHA-256: {report['source_sha256']}

CURRENT NATIVE SHA-256
'''
    for item in report['files']:
        text+=Path(item['final_file']).name+'\n'+item['final_sha256']+'\n'
    text+='\nSee validation.json, growth-connectivity.json and native-slice-result.json for evidence. SHA256.json hashes the included files.\n'
    (OUT/'README.txt').write_text(text,encoding='utf-8')
    save_json(OUT/'SHA256.json',{p.name:sha(p) for p in sorted(OUT.iterdir())
        if p.is_file() and p.name!='SHA256.json' and p.suffix!='.zip'})
    package=OUT/'Dara-A2L-Veneer-Wall-Cradle-r4-Review.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(OUT.iterdir()):
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    assert protected()==report['production_and_A1_fingerprints']
    print(json.dumps({'package':str(package),'sha256':sha(package),'total_g':total,
                      'wall_probes':wall_probes,'neck_probes':probes},indent=2))


if __name__=='__main__':main()
