"""Package the validated r5 review candidate without changing production."""
import json
from pathlib import Path
import zipfile
from build_veneer_wall_cradle_r5 import ROOT,OUT,WORK,protected
from development_3mf import sha,save_json


def main():
    assert not (OUT/'WITHDRAWN.txt').exists()
    report=json.loads((OUT/'validation.json').read_text())
    assert report['native_total_filament_g']<1000
    assert protected()==report['production_and_A1_fingerprints']
    for row in report['plates']:
        assert row['opening_toolpath_checks']['support_segments_inside_openings']==0
        assert row['geometry']['legacy_base_stock_remaining_mm3']<1e-5
        assert row['geometry']['difference_from_r4_above_base_mm3']<1e-5
        assert len(row['geometry']['bed_tie_bands'])==2
        assert row['grounded_wall_toolpath_checks']['bands']['bond_probes_checked']>0
    for item in report['files']:
        assert sha(Path(item['final_file']))==item['final_sha256']
        assert sha(Path(item['editable_file']))==item['editable_sha256']
        sidecar=Path(item['editable_file']).with_suffix('.json')
        metadata=json.loads(sidecar.read_text())
        assert metadata['source_sha256']==report['source_sha256']
        metadata.update(native_slice_validated=True,native_file=Path(item['final_file']).name,
                        native_sha256=item['final_sha256'],editable_sha256=item['editable_sha256'])
        save_json(sidecar,metadata)
    growth=json.loads((ROOT/'working/review/veneer-restraint-audit/growth-connectivity-r5.json').read_text())
    for i in [1,2,3]:
        original=next(c for c in growth['cases'] if c['veneer']==f'V{i}' and c['revision']=='production')
        candidate=next(c for c in growth['cases'] if c['veneer']==f'V{i}' and c['revision']=='r5')
        for a,b in zip(original['levels'],candidate['levels']):
            for new in b['ungrounded_components']:
                assert any(max(abs(x-y) for x,y in zip(new['bounds_mm'],old['bounds_mm']))<1e-4
                           and abs(new['volume_mm3']-old['volume_mm3'])<1e-5
                           for old in a['ungrounded_components'])
    geometry_hashes={f'V{i}':sha(WORK/f'V{i}-candidate.npz') for i in [1,2,3]}
    report['source_geometry_npz_sha256']=geometry_hashes
    save_json(OUT/'validation.json',report)
    growth['candidate_geometry_sha256']=geometry_hashes
    growth['no_additional_ungrounded_islands_at_sampled_heights']=True
    save_json(OUT/'growth-connectivity.json',growth)
    total=report['native_total_filament_g']
    previous=json.loads((ROOT/'output/Dara-A2L-Veneer-Wall-Cradle-r4/validation.json').read_text())
    lines=[]
    for row in report['plates']:
        seconds=round(row['estimated_seconds']);hours,remainder=divmod(seconds,3600);minutes,seconds=divmod(remainder,60)
        lines.append(f"{row['veneer']} (source plate {row['source_plate']}): {row['estimated_filament_g']:.2f} g; {hours} h {minutes} min {seconds} sec")
    necks=sum(p['bond_toolpath_check']['bond_probes_checked'] for p in report['plates'])
    bands=sum(p['grounded_wall_toolpath_checks']['bands']['bond_probes_checked'] for p in report['plates'])
    walls=sum(c['bond_probes_checked'] for p in report['plates'] for label,c in p['grounded_wall_toolpath_checks'].items() if label!='bands')
    holes=sum(p['geometry']['opening_count'] for p in report['plates'])
    text=f'''DARA A2L VENEER WALL CRADLE r5 - 2026-10-21
UNPRINTED REVIEW CANDIDATE - PHYSICAL STIFFNESS AND ANTI-WARP PERFORMANCE UNQUALIFIED

r5 removes the obsolete local base framework shown in the user's screenshot and adds two thin bed bands at the user's request. It supersedes r4 as the separate review candidate. r1/r2 remain withdrawn.
The curved local rail, crossbars, broad center strip and old starter feet are removed. The outer plate guard was already removed in r4.
Two 4 mm wide, 0.6 mm thick bands sit beneath the two connecting walls on each veneer plate. Each band spans the front and rear walls and prints in three 0.20 mm layers.

CURRENT FILES
Native sliced A2L projects: Dara-A2L-Veneer-Wall-Cradle-r5-V1.3mf, -V2.3mf and -V3.3mf. Open as projects.
Matching -Editable.3mf files are the unsliced sources. These are full veneer plates, not cropped samples.
Production Dara.3mf, named A2L complete/editable files, M cores, knot and A1 companion files remain unchanged. No print job was sent.

GEOMETRY
Only the bottom 1.60001 mm changes relative to r4. Original fused attachment-neck stock is retained where it crosses that layer.
Above that layer, the r4 wall assembly and veneer are preserved: front inclined wall 1.20 mm thick, rear wall and two connecting webs 1.00 mm thick.
The front wall reaches the bed continuously across its width. No long individual starter posts are reintroduced.
Original fused necks connect the veneer to the front wall. Generated tree supports remain supplementary and are not counted as positive bed ties.
The existing {holes} pointed openings in the rear walls and webs remain: 28 x 48 mm, 60-degree roof slopes, at least 12 mm from wall edges, with 16 mm grid lands. Rear-to-web joins remain uncut.
The inclined wall behind the veneer remains solid. Its upper surface remains at assembly Z4.4 with a nominal 4.2 mm gap to the veneer rear plane, crossed by the fused necks.
Saved 55-degree lean, in-plane orientation, veneer appearance, pockets, seams and seating features are preserved.

NATIVE SLICER ESTIMATES - ALL THREE VENEERS AND ALL SUPPORTS
{chr(10).join(lines)}
TOTAL: {total:.2f} g; {report['native_total_seconds']/3600:.2f} hours.
Headroom to 1,000 g: {1000-total:.2f} g.
Reduction from the user's 1,203.88 g estimate: {1203.88-total:.2f} g.
Reduction from r4's {previous['native_total_filament_g']:.2f} g native estimate: {previous['native_total_filament_g']-total:.2f} g.
These are slicer estimates, not measured spool consumption.

PRESERVED SETTINGS
A2L; 0.4 mm nozzle; 0.20 mm layers and first layer; 4 wall loops; 5 top and bottom layers; Textured PEI Plate.
Global 8% gyroid; veneer and modeled carrier keep their source 100% solid object override. The thin bands and walls are solid geometry.
Slots remain 1 white, 2 wood tan, 3 copper silk, 4 Azurite blue. These plates extrude copper silk slot 3.
Tree supports, brim settings, cooling, speeds, accelerations, temperatures and purge settings are preserved.
Only the process display label and indexing of the preserved tower coordinates differ for the separate single-plate files.

CHECKS PERFORMED
Boolean comparisons confirm no obsolete base geometry remains outside the new walls/bands and original low neck stock. Changes above the old base layer are below 0.00001 mm3.
Source-neck comparison residuals are below 0.0001 mm3 total and 0.001 mm thickness, accounting for rounded coincident faces. The solid veneer and upper geometry are preserved to the recorded boolean tolerances.
Candidates are closed, connected solids. Editable/native/generated meshes agree within 0.001 mm.
Full global/object/volume settings checked. Locked constants checked in saved projects and G-code.
All {necks} original attachment-neck probes have nearby MODEL extrusion, excluding generated supports.
{walls} additional probes check continuous wall extrusion from the first layer through the height.
{bands} band probes check actual MODEL extrusion separately at Z0.20, Z0.40 and Z0.60 mm; adjacent layers cannot satisfy these band checks.
Growth connectivity checked at 0.2, 2, 5, 10, 25, 50, 100, 200 and 297.4 mm per veneer. No additional ungrounded islands at those heights relative to production.
A tiny V3 tip at 5 mm is unchanged from production (about 0.005 mm3).
No generated support extrusion occupies the {holes} lightening openings in the native toolpaths.
Print bounds including bead widths and generated supports, print heights, copper-only extrusion and G-code checksums checked.
No floating-region or collision warnings; only inherited traditional-timelapse compatibility warnings remain.
Protected production and A1 hashes verified unchanged.

PREVIEWS AND LIMITS
bed-base-before-after.png compares the actual V2 model footprint at Z0.1 mm. all-bed-footprints.png shows all three. Orange marks the wider bed bands and blue the wall footprint; the actual printed material remains copper silk.
bed-tie-detail.png shows an actual section through a fused neck and continuous inclined wall.
These digital checks do not establish physical rigidity, bed adhesion, silk warping resistance, roof quality, clean removal or finished appearance. r5 is unprinted and is not a physically qualified production release.

SOURCE
{report['source']}
SHA-256: {report['source_sha256']}

CURRENT NATIVE SHA-256
'''
    for item in report['files']:
        text+=Path(item['final_file']).name+'\n'+item['final_sha256']+'\n'
    text+='\nSee validation.json, growth-connectivity.json and native-slice-result.json for evidence. SHA256.json hashes the included files.\n'
    (OUT/'README.txt').write_text(text,encoding='utf-8')
    save_json(OUT/'SHA256.json',{p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256.json' and p.suffix!='.zip'})
    package=OUT/'Dara-A2L-Veneer-Wall-Cradle-r5-Review.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(OUT.iterdir()):
            if p.is_file() and p.suffix!='.zip':z.write(p,p.name)
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    assert protected()==report['production_and_A1_fingerprints']
    print(json.dumps(dict(package=str(package),sha256=sha(package),total_g=total,wall_probes=walls,band_probes=bands,neck_probes=necks),indent=2))


if __name__=='__main__':main()
