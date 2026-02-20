import argparse
import os
from ifstools.ifs import IFS


def default_out_dir(ifs_path: str) -> str:
    base = os.path.splitext(os.path.basename(ifs_path))[0]
    return os.path.join(os.path.dirname(os.path.abspath(ifs_path)), base + "_ifs")


def main() -> int:
    parser = argparse.ArgumentParser(description="Unpack a single IFS file")
    parser.add_argument("ifs_file", nargs="?", default="14052.ifs", help="Path to .ifs file (default: 14052.ifs)")
    parser.add_argument("-o", "--out", default=None, help="Output directory (default: <ifs_name>_ifs)")
    parser.add_argument("-m", "--manifest", action="store_true", help="Also extract ifs_manifest.xml")
    parser.add_argument("--no-recurse", action="store_true", help="Do not recurse into nested IFS files")
    args = parser.parse_args()

    ifs_path = os.path.abspath(args.ifs_file)
    if not os.path.isfile(ifs_path):
        print("ERROR: file not found:", ifs_path)
        return 1

    out_dir = os.path.abspath(args.out) if args.out else default_out_dir(ifs_path)

    archive = IFS(ifs_path)
    try:
        archive.extract(
            path=out_dir,
            progress=True,
            recurse=not args.no_recurse,
            extract_manifest=args.manifest,
            rename_dupes=True,
        )
    finally:
        archive.close()

    print("Done:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
