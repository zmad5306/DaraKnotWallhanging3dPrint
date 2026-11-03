import sys,json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'.work/python-libs'),str(ROOT/'output/Dara-B1-Cover-Source/scripts')]
import prepare_hammered_bands as b
from prepare_cover_crown_test import shape
from prepare_cover_edge_test import surface_error
from integrate_hammered_dara import selected_entries
report=json.loads((ROOT/'working/bambu/Dara-Photo-Frame-A1-Jointed/cover-crown-validation.json').read_text())
with zipfile.ZipFile(ROOT/'Dara.3mf') as z:
    paths=['3D/3dmodel.model','Metadata/model_settings.config']+[r['mesh_path'] for r in report['geometry_checks']]
    files={p:z.read(p) for p in paths}
entries=selected_entries(files,{r['name'] for r in report['geometry_checks']})
rows=[]
for i,r in enumerate(report['geometry_checks'],1):
    body=entries[r['name']][0]['mesh'];t=b.np.array(r['build_transform']);t[1,3]-=1536
    body.apply_transform(b.np.linalg.inv(t))
    region,floor,top=shape(i)
    error=surface_error(body,top)
    assert error['max_mm']<.00101
    assert body.is_volume and body.is_watertight and body.body_count==1
    points=body.triangles_center[body.face_normals[:,2]>.01,:2]
    row=dict(name=r['name'],triangles=len(body.faces),watertight=body.is_watertight,body_count=body.body_count,
             show_face_sampled_error=error,min_sampled_vertical_thickness_mm=float((top(points)-floor(points)).min()))
    rows.append(row);print(row,flush=True)
record=dict(production_sha256=hashlib.sha256((ROOT/'Dara.3mf').read_bytes()).hexdigest(),meshes=rows,
            limits='Triangle centers and edge-midpoint sample checks against the intended surface; not a proof of physical finish. Topological checks do not exclude all geometric defects.')
(ROOT/'.work/cover-marks/current-mesh-checks.json').write_text(json.dumps(record,indent=2))
