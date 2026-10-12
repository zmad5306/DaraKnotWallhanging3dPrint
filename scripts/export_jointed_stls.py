"""Export and verify each distinct printable part of the jointed frame.

Requires OpenSCAD, numpy, and trimesh. Dimensions are millimetres.
Run from any directory; outputs are relative to the repository root.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / ".work/python-libs").is_dir():
    sys.path.insert(0, str(ROOT / ".work/python-libs"))

import numpy as np
import trimesh

CAD = ROOT / "working/Dara-Photo-Frame-A1-Jointed.scad"
OUT = ROOT / "working/stl/Dara-Photo-Frame-A1-Jointed"
LOGS = ROOT / ".work/stl-export"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parts():
    for family, prefix, count in [("frame", "F", 20), ("M", "M", 6)]:
        for i in range(1, count + 1):
            yield f"{prefix}{i}", family, 1, {
                "view_mode": "section", "part_family": family, "section_index": i
            }
    for i in range(1, 9):
        yield f"Backer{i}", "backer", 1, {"view_mode": "backer", "backer_index": i}
    for i in range(1, 5):
        yield f"B{i}", "wall_block", 1, {"view_mode": "wall_block", "wall_mount_index": i}
    yield "Retainer", "retainer", 32, {"view_mode": "retainer"}


def verify(path):
    mesh = trimesh.load_mesh(path, process=True)
    if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
        raise ValueError(f"{path.name}: empty or invalid mesh")
    if not np.isfinite(mesh.vertices).all():
        raise ValueError(f"{path.name}: nonfinite coordinates")
    if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume <= 0:
        raise ValueError(f"{path.name}: invalid solid")
    # Include non-watertight fragments rather than silently dropping them.
    components = len(mesh.split(only_watertight=False))
    if components != 1:
        raise ValueError(f"{path.name}: expected one connected solid, got {components}")
    low, high = mesh.bounds
    margin = float(min(*(low[:2] + 128), *(128 - high[:2])))
    if abs(low[2]) > 1e-5 or high[2] > 256 or margin < 1.499:
        raise ValueError(f"{path.name}: placement exceeds A1 bed allowance: {mesh.bounds}")
    # Binary STL has an 80-byte header, a 4-byte face count, and 50 bytes per face.
    if path.stat().st_size != 84 + 50 * len(mesh.faces):
        raise ValueError(f"{path.name}: unexpected binary STL length")
    return {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "triangles": len(mesh.faces),
        "bounds_mm": mesh.bounds.tolist(),
        "size_mm": mesh.extents.tolist(),
        "volume_mm3": float(mesh.volume),
        "minimum_bed_edge_clearance_mm": margin,
        "connected_solids": components,
        "watertight": bool(mesh.is_watertight),
        "consistent_winding": bool(mesh.is_winding_consistent),
        "on_bed": True,
        "fits_256_mm_bed_with_1_5_mm_edge_allowance": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openscad", help="Path to the OpenSCAD executable")
    parser.add_argument("--jobs", type=int, default=3, help="Concurrent renders (default: 3)")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    executable = args.openscad or shutil.which("openscad")
    if not executable:
        default = Path(r"C:\Program Files (x86)\OpenSCAD\openscad.exe")
        if default.is_file():
            executable = str(default)
    if not executable:
        parser.error("OpenSCAD was not found; supply --openscad")
    version = subprocess.run([executable, "--version"], capture_output=True, text=True, check=True)
    version = (version.stdout + version.stderr).strip()
    source_hash = sha256(CAD)
    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    def export(job):
        name, family, quantity, selectors = job
        temporary = LOGS / f"{name}.stl"
        command = [
            executable, "--hardwarnings", "--export-format=binstl",
            "--camera=0,0,0,0,0,0,700", "-o", str(temporary),
            "-D", "fast_preview=false",
        ]
        for key, value in selectors.items():
            command += ["-D", f"{key}={json.dumps(value)}"]
        command.append(str(CAD))
        start = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True, timeout=1200)
        log = result.stdout + result.stderr
        (LOGS / f"{name}.log").write_text(log, encoding="utf-8")
        if result.returncode or "WARNING:" in log or "ERROR:" in log:
            raise RuntimeError(f"{name}: OpenSCAD failed; see {LOGS / (name + '.log')}")
        record = {
            "file": f"{name}.stl", "part": name, "family": family,
            "print_quantity": quantity, "selectors": selectors, **verify(temporary),
        }
        if sha256(CAD) != source_hash:
            raise RuntimeError("Source CAD changed during export; rerun with a stable source")
        temporary.replace(OUT / record["file"])
        print(f"{name}: verified ({time.monotonic() - start:.1f}s)", flush=True)
        return record

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        records = list(pool.map(export, parts()))
    if sha256(CAD) != source_hash:
        raise RuntimeError("Source CAD changed during export")
    manifest = {
        "source": CAD.relative_to(ROOT).as_posix(), "source_sha256": source_hash,
        "openscad_version": version, "format": "binary STL", "units": "mm",
        "native_csg": True, "fast_preview": False,
        "part_files": len(records), "total_print_quantity": sum(r["print_quantity"] for r in records),
        "bed_mm": [256, 256, 256], "reserved_edge_mm": 1.5,
        "all_passed": True, "parts": records,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported and verified {len(records)} STL files in {OUT}", flush=True)


if __name__ == "__main__":
    main()
