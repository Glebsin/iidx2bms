from pathlib import Path
import shutil
import sys

BASE_DIR = Path(__file__).parent

def main():
    folders = [
        BASE_DIR / ".bme files",
        BASE_DIR / "put .1 and .s3p or only .ifs files here",
        BASE_DIR / "put .png and .mp4 here",
        BASE_DIR / "result",
        BASE_DIR / "wma2wav" / "output .wav",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    readme = BASE_DIR / "README.md"
    if readme.exists():
        readme.unlink()

    setup_bat = BASE_DIR / "setup.bat"
    if setup_bat.exists():
        setup_bat.unlink()

    print("Setup is done")
    input("Press Enter to exit...")

    try:
        Path(__file__).unlink()
    except:
        pass

if __name__ == "__main__":
    main()
