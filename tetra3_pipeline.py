#!/usr/bin/env python3
"""
Tetra3 utility: generate a star-pattern database and solve images.

Features:
- Uses HIPPARCOS/TYCHO/BSC5 catalogs (you must download the raw file yourself).
- Robust argparse CLI.
- CSV logging of solve results.
- Tweakable FOV, magnitude limit, and extraction parameters.
- Helpful checks and error messages.
"""

import argparse
import csv
import os
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import tetra3
except Exception as e:
    print("ERROR: Could not import 'tetra3'. Install it from source (GitHub) first.\n"
          "Repo: https://github.com/esa/tetra3\n"
          f"Details: {e}")
    sys.exit(1)


@contextmanager
def pushd(new_dir: Path):
    prev = Path.cwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(prev)


def ensure_catalog_available(star_catalog: str, catalog_dir: Optional[Path]) -> None:
    """
    Verify that the expected raw catalog file is present where tetra3 expects it.
    If catalog_dir is provided, we'll temporarily chdir there for database generation.
    """
    required = {
        "hip_main": "hip_main.dat",
        "tyc_main": "tyc_main.dat",   # Tycho-2 main file; rename accordingly
        "bsc5":     "bsc5.dat",       # BSC5 byte-format file; rename accordingly
    }
    if star_catalog not in required:
        print(f"ERROR: Unsupported star_catalog '{star_catalog}'. Use one of: {', '.join(required)}")
        sys.exit(2)

    filename = required[star_catalog]
    search_dirs = []
    if catalog_dir:
        search_dirs.append(catalog_dir)
    search_dirs.append(Path.cwd())

    for d in search_dirs:
        if (d / filename).exists():
            return

    where = f"{catalog_dir}" if catalog_dir else str(Path.cwd())
    print(f"ERROR: Required catalog file '{filename}' not found in '{where}' or current directory.")
    if star_catalog == "hip_main":
        print("Download HIPPARCOS 'hip_main.dat' from:")
        print("  https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat")
    elif star_catalog == "bsc5":
        print("Download the BSC5 byte-format file from:")
        print("  http://tdc-www.harvard.edu/catalogs/bsc5.html")
    else:
        print("Ensure you have the correct Tycho-2 main file and rename it to 'tyc_main.dat'.")
    sys.exit(3)


def cmd_generate_db(args: argparse.Namespace) -> None:
    """
    Generate a Tetra3 database tailored to your FOV and magnitude limit.
    """
    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    catalog_dir = Path(args.catalog_dir).expanduser().resolve() if args.catalog_dir else None
    ensure_catalog_available(args.star_catalog, catalog_dir)

    print(f"[{datetime.now().isoformat(timespec='seconds')}] Generating database...")
    print(f"  star_catalog     : {args.star_catalog}")
    print(f"  catalog_dir      : {catalog_dir if catalog_dir else '(current dir)'}")
    print(f"  FOV range (deg)  : {args.min_fov} -> {args.max_fov}")
    print(f"  mag limit        : {args.star_max_magnitude}")
    print(f"  output db        : {out_path}")

    if catalog_dir:
        with pushd(catalog_dir):
            _generate_db_core(args, out_path)
    else:
        _generate_db_core(args, out_path)

    print(f"[OK] Database created: {out_path}")


def _generate_db_core(args: argparse.Namespace, out_path: Path) -> None:
    t3 = tetra3.Tetra3(load_database=None)
    t3.generate_database(
        min_fov=float(args.min_fov),
        max_fov=float(args.max_fov),
        star_catalog=args.star_catalog,
        star_max_magnitude=float(args.star_max_magnitude),
        save_as=str(out_path)
    )


def parse_extract_dict(args: argparse.Namespace) -> Dict[str, Any]:
    ed: Dict[str, Any] = {}
    if args.min_sum is not None:
        ed["min_sum"] = int(args.min_sum)
    if args.max_axis_ratio is not None:
        ed["max_axis_ratio"] = float(args.max_axis_ratio)
    if args.min_distance is not None:
        ed["min_distance"] = int(args.min_distance)
    return ed


def cmd_solve(args: argparse.Namespace) -> None:
    db_path = Path(args.database).expanduser().resolve()
    if not db_path.exists():
        print(f"ERROR: Database file not found: {db_path}")
        print("Generate it first with the 'generate-db' command.")
        sys.exit(4)

    images: List[Path] = []
    for p in args.images:
        pth = Path(p).expanduser()
        if pth.is_dir():
            images.extend(sorted([*pth.glob("*.jpg"), *pth.glob("*.jpeg"),
                                  *pth.glob("*.png"), *pth.glob("*.tif"), *pth.glob("*.tiff"),
                                  *pth.glob("*.bmp"), *pth.glob("*.fits")]))
        else:
            images.append(pth)

    if not images:
        print("ERROR: No images to solve.")
        sys.exit(5)

    print(f"[{datetime.now().isoformat(timespec='seconds')}] Loading database: {db_path}")
    t3 = tetra3.Tetra3(load_database=str(db_path))

    extract_dict = parse_extract_dict(args)
    print(f"FOV estimate: {args.fov_estimate} deg  |  FOV max error: {args.fov_max_error} deg")
    if extract_dict:
        print(f"extract_dict: {extract_dict}")

    csv_path = Path(args.csv).expanduser().resolve() if args.csv else None
    if csv_path:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_file = open(csv_path, "w", newline="", encoding="utf-8")
        writer = csv.writer(csv_file)
        writer.writerow(["image", "success", "ra_deg", "dec_deg", "rotation_deg", "fov_deg"])
    else:
        writer = None
        csv_file = None

    try:
        for img in images:
            print(f"\nSolving: {img}")
            try:
                res = t3.solve_from_image(
                    str(img),
                    fov_estimate=float(args.fov_estimate),
                    fov_max_error=float(args.fov_max_error),
                    extract_dict=extract_dict if extract_dict else None
                )
            except Exception as e:
                print(f"  ERROR during solve: {e}")
                if writer:
                    writer.writerow([str(img), False, "", "", "", ""])
                continue

            success = bool(res.get("success", False))
            ra = res.get("ra_deg", "")
            dec = res.get("dec_deg", "")
            rot = res.get("rotation_deg", "")
            fov = res.get("fov_deg", "")

            if success:
                print(f"  SUCCESS  RA={ra}  DEC={dec}  ROT={rot}  FOV={fov}")
            else:
                print("  FAILED")

            if writer:
                writer.writerow([str(img), success, ra, dec, rot, fov])

    finally:
        if csv_path:
            csv_file.close()
            print(f"\n[OK] Results saved to CSV: {csv_path}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Tetra3 helper: generate DB & solve images (12.5–16 mm HQ cam use-case ready)."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate-db", help="Generate a Tetra3 database from a raw star catalog.")
    g.add_argument("--star-catalog", choices=["hip_main", "tyc_main", "bsc5"], default="hip_main",
                   help="Raw catalog to use. Default: hip_main.")
    g.add_argument("--catalog-dir", default=None,
                   help="Directory containing the raw catalog (e.g., folder with hip_main.dat).")
    g.add_argument("--min-fov", type=float, default=30.0, help="Minimum FOV (deg). Default: 30.")
    g.add_argument("--max-fov", type=float, default=36.0, help="Maximum FOV (deg). Default: 36.")
    g.add_argument("--star-max-magnitude", type=float, default=8.0,
                   help="Magnitude limit for DB generation. Default: 8.0.")
    g.add_argument("-o", "--output", default="db_12p5mm_from_hip.npz",
                   help="Output database filename. Default: db_12p5mm_from_hip.npz")
    g.set_defaults(func=cmd_generate_db)

    s = sub.add_parser("solve", help="Solve one or more images using a generated database.")
    s.add_argument("images", nargs="+",
                   help="Image file(s) or directory(ies).")
    s.add_argument("--database", "-d", default="db_12p5mm_from_hip.npz",
                   help="Path to a generated database .npz file.")
    s.add_argument("--fov-estimate", type=float, default=35.0, help="Estimated FOV (deg).")
    s.add_argument("--fov-max-error", type=float, default=1.5, help="Allowed FOV error (deg).")
    s.add_argument("--min-sum", type=int, default=500, help="extract_dict: min_sum.")
    s.add_argument("--max-axis-ratio", type=float, default=1.5, help="extract_dict: max_axis_ratio.")
    s.add_argument("--min-distance", type=int, default=4, help="extract_dict: min_distance.")
    s.add_argument("--csv", default=None, help="Optional path to save results as CSV.")
    s.set_defaults(func=cmd_solve)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
