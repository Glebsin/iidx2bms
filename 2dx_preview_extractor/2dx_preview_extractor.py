import subprocess
from pathlib import Path
import sys


BASE_DIR = Path(__file__).parent
EXTRACT_EXE = BASE_DIR.parent / "2dx_extract" / "2dx_extract.exe"
OUTPUT_WAV = BASE_DIR / "preview_auto_generator.wav"
RAW_WAV = BASE_DIR / "1.wav"


def extract_preview(pre_dx2: Path) -> bool:
    if OUTPUT_WAV.exists():
        OUTPUT_WAV.unlink()
    if RAW_WAV.exists():
        RAW_WAV.unlink()

    subprocess.run([str(EXTRACT_EXE), str(pre_dx2)], cwd=BASE_DIR)

    if RAW_WAV.exists() and RAW_WAV.stat().st_size > 0:
        RAW_WAV.replace(OUTPUT_WAV)
        return True
    return False


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: 2dx_preview_extractor.py <path_to_pre.2dx>")
        return 2

    pre_dx2 = Path(sys.argv[1])
    if not pre_dx2.exists():
        print(f'File not found: "{pre_dx2}"')
        return 1

    ok = extract_preview(pre_dx2)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
