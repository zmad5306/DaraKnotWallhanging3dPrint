import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.work/python-libs'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
W=ROOT/'.work/cover-marks';OUT=ROOT/'working/review/plate-31-surface';OUT.mkdir(parents=True,exist_ok=True)
meshes=json.loads((W/'current-mesh-checks.json').read_text())
paths=json.loads((W/'paths.json').read_text())
prior=json.loads((ROOT/'.work/cover-tessellation/toolpaths.json').read_text())
trial=json.loads((W/'tight-arcs-joins.json').read_text());trial.pop('joins')
report=dict(date='2026-10-15',source='Dara.3mf, saved Plate 31',production_sha256=meshes['production_sha256'],
    conclusion='Physical smear cause remains unresolved. The proposed Arachne / mismatched-grid / abrupt plateau-slope diagnosis is unsupported for the current project. No production change or print-quality claim is warranted by the digital measurements.',
    settings=dict(wall_generator='classic',resolution_mm=.012,arc_fitting=True,scarf_seams=False),
    current_mesh_checks=meshes['meshes'],current_saved_toolpaths=paths,
    earlier_controlled_tests=prior,fresh_single_cover_tight_arc_trial=trial,
    findings=[
      'The exported SCAD is an explicit polyhedron. Changing $fn, $fa or $fs does not retessellate its supplied faces.',
      'band_envelope defaults to 0.25 mm and the floor envelope is explicitly 0.25 mm; both use an assembly-aligned grid. The upper bevel additionally receives constrained/adaptive triangulation.',
      'The cap in crown() uses 2.2*(2*t-t*t), t capped at 1. Its derivative with respect to distance reaches zero at the flat plateau; this cap is not a first-derivative jump. Nearest-edge changes can cause a separate medial ridge in the original formula.',
      'The current outer face uses Gaussian smoothing and a bicubic spline. The original underside is retained for fit. All five sampled outer-surface errors are about 0.001 mm or less.',
      'Saved production face paths have arc/line joins aligned across layers. All sampled interior front moves have 0.42 mm width and 99.4485 mm/s commanded feedrate; sampled extrusion per distance is effectively constant.',
      'Arc tangent discontinuities are measurable, but no angle threshold or causal relationship to the printed scar has been established.',
      'The earlier investigation reproduced similar preview notches by changing segment rendering only, and records an unsuccessful orientation change. This limits claims based on preview appearance alone.',
      'Fresh B1 trial with resolution 0.001 mm and arcs enabled has max interior join angle 0.718 degrees versus 0.764 degrees in the existing fine linear-path test. This is not evidence of a cured physical finish.'
    ],
    limitations=[meshes['limits'],'Preview screenshot is not a measured printed-surface profile. A close-up of the scar on an identified current-revision part is needed to correlate the physical mark with mesh curvature and toolpaths.','No production meshes, settings or saved slices were modified.'],
    provenance=dict(source_archive='output/Dara-B1-Cover-Source',prior_history='codex/hammered-m-production:working/review/cover-edge/README.md',scratch_scripts=['.work/analyze_cover_marks.py','.work/cover-marks/check_current_meshes.py','.work/cover-marks/slice_precision.py'],renderer_source='https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/resources/shaders/140/gcode.vs'))
(OUT/'review.json').write_text(json.dumps(report,indent=2)+'\n')
fig,axs=plt.subplots(5,1,figsize=(11,9),layout='constrained')
for row,ax in zip(paths,axs):
    pts=[j['xy'] for j in row['joins']]
    ax.scatter([p[1] for p in pts],[p[0] for p in pts],s=12,color='#a94323')
    ax.set_ylim(-6,6);ax.grid(alpha=.2);ax.set_ylabel(row['name']+'\nwidth (mm)')
    ax.set_title(f"Connected path joins: largest direction change {max(j['angle_deg'] for j in row['joins']):.2f} degrees",fontsize=10)
axs[-1].set_xlabel('Position along each cover (mm; assembly joint origin)')
fig.suptitle('Where fitted segments meet on the five cover faces\nSaved production Plate 31 — these dots are joins, not proven print defects',fontsize=14)
fig.savefig(OUT/'segment-join-locations.png',dpi=150)
assert hashlib.sha256((ROOT/'Dara.3mf').read_bytes()).hexdigest()==meshes['production_sha256']
print(OUT/'review.json')
