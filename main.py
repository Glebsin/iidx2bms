import subprocess
import time
from pathlib import Path
import shutil
import pyautogui
import bme_format
import re

BASE_DIR = Path(__file__).parent

INPUT_DIR = BASE_DIR / "put .1 and .s3p or only .ifs files here"
MEDIA_DIR = BASE_DIR / "put .png and .mp4 here"

S3P_DIR = BASE_DIR / "s3p_extract"
IFS_DIR = BASE_DIR / "ifs_extract"
DX2_DIR = BASE_DIR / "2dx_extract"
WMA2WAV_DIR = BASE_DIR / "wma2wav"

BME_DIR = BASE_DIR / ".bme files"
RESULT_DIR = BASE_DIR / "result"

DIGITS_5 = re.compile(r"^\d{5}$")

def cleanup_and_wait():
    shutil.rmtree(BASE_DIR / "__pycache__", ignore_errors=True)
    input("Press Enter to exit...")

def clean_ifs_dir():
    for p in IFS_DIR.iterdir():
        if p.name.lower() == "ifs_extract.exe":
            continue
        if p.is_file():
            p.unlink(missing_ok=True)
        else:
            shutil.rmtree(p, ignore_errors=True)

def run_one2bme(one_file: Path):
    tmp = BASE_DIR / one_file.name
    shutil.copy(one_file, tmp)

    subprocess.Popen([str(BASE_DIR / "one2bme.exe")], cwd=BASE_DIR)
    time.sleep(2)
    pyautogui.press("enter")
    time.sleep(2)

    for bme in BASE_DIR.glob("*.bme"):
        shutil.move(bme, BME_DIR / bme.name)

    tmp.unlink(missing_ok=True)

def handle_media(song_id: str, final_dir: Path):
    MEDIA_DIR.mkdir(exist_ok=True)

    pngs = [f for f in MEDIA_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".png"]
    mp4s = [f for f in MEDIA_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".mp4"]

    has_png = bool(pngs)
    has_mp4 = bool(mp4s)

    if has_png:
        dst = final_dir / "1.png"
        if dst.exists():
            dst.unlink()
        shutil.move(pngs[0], dst)

    if has_mp4:
        dst = final_dir / f"{song_id}.mp4"
        if dst.exists():
            dst.unlink()
        shutil.move(mp4s[0], dst)

    if not has_png and not has_mp4:
        print(f'Add STAGEFILE 1.png and BGA {song_id}.mp4 into "\\result\\{final_dir.name}" if you want')
    elif has_png and not has_mp4:
        print(f'Add BGA {song_id}.mp4 into "\\result\\{final_dir.name}" if you want')
    elif not has_png and has_mp4:
        print(f'Add STAGEFILE 1.png into "\\result\\{final_dir.name}" if you want')
    else:
        print(f'Chart converted in "\\result\\{final_dir.name}" folder')

def main():
    BME_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)
    MEDIA_DIR.mkdir(exist_ok=True)

    if not any(INPUT_DIR.iterdir()):
        print('Folder "put .1 and .s3p or only .ifs files here" are empty, put .1 and .s3p or only .ifs files here')
        cleanup_and_wait()
        return

    clean_ifs_dir()

    files = list(INPUT_DIR.iterdir())
    ifs_files = [f for f in files if f.suffix.lower() == ".ifs"]
    one_files = [f for f in files if f.suffix.lower() == ".1"]
    s3p_files = [f for f in files if f.suffix.lower() == ".s3p"]

    song_id = None

    if ifs_files:
        ifs = ifs_files[0]
        song_id = ifs.stem

        tmp_ifs = IFS_DIR / ifs.name
        shutil.copy(ifs, tmp_ifs)

        subprocess.run(
            [str(IFS_DIR / "ifs_extract.exe"), str(tmp_ifs)],
            cwd=IFS_DIR
        )

        out_dir = IFS_DIR / ifs.stem
        if not out_dir.exists():
            print("Non-standard .ifs file, convert the chart manually")
            cleanup_and_wait()
            return

        one_out = list(out_dir.glob("*.1"))
        dx2_out = [f for f in out_dir.glob("*.2dx") if not f.name.endswith("_pre.2dx")]
        s3p_out = list(out_dir.glob("*.s3p"))

        if len(one_out) != 1 or not DIGITS_5.fullmatch(one_out[0].stem):
            print("Non-standard .ifs file, convert the chart manually")
            cleanup_and_wait()
            return

        shutil.copy(one_out[0], INPUT_DIR / one_out[0].name)
        run_one2bme(INPUT_DIR / one_out[0].name)

        if dx2_out:
            shutil.copy(dx2_out[0], DX2_DIR / dx2_out[0].name)

            subprocess.run(
                [str(DX2_DIR / "2dx_extract.exe"), str(DX2_DIR / dx2_out[0].name)],
                cwd=DX2_DIR
            )

            subprocess.run(
                ["python", "rename.py", str(DX2_DIR)],
                cwd=WMA2WAV_DIR
            )

        elif s3p_out:
            shutil.copy(s3p_out[0], INPUT_DIR / s3p_out[0].name)

            tmp = S3P_DIR / s3p_out[0].name
            shutil.copy(s3p_out[0], tmp)

            subprocess.run(
                [str(S3P_DIR / "s3p_extract.exe"), str(tmp)],
                cwd=S3P_DIR
            )

            out_s3p = S3P_DIR / f"{s3p_out[0].stem}.s3p.out"
            for _ in range(30):
                if out_s3p.exists() and any(out_s3p.glob("*.wma")):
                    break
                time.sleep(1)

            subprocess.run(
                ["python", "wma2wav.py", str(out_s3p)],
                cwd=WMA2WAV_DIR
            )

            subprocess.run(
                ["python", "rename.py", str(WMA2WAV_DIR / "output .wav")],
                cwd=WMA2WAV_DIR
            )

        shutil.rmtree(out_dir, ignore_errors=True)
        tmp_ifs.unlink(missing_ok=True)

    else:
        for f in one_files:
            song_id = f.stem
            run_one2bme(f)

        for f in s3p_files:
            tmp = S3P_DIR / f.name
            shutil.copy(f, tmp)

            subprocess.run(
                [str(S3P_DIR / "s3p_extract.exe"), str(tmp)],
                cwd=S3P_DIR
            )

            out_dir = S3P_DIR / f"{f.stem}.s3p.out"
            for _ in range(30):
                if out_dir.exists() and any(out_dir.glob("*.wma")):
                    break
                time.sleep(1)

            subprocess.run(
                ["python", "wma2wav.py", str(out_dir)],
                cwd=WMA2WAV_DIR
            )

            subprocess.run(
                ["python", "rename.py", str(WMA2WAV_DIR / "output .wav")],
                cwd=WMA2WAV_DIR
            )

            shutil.rmtree(out_dir, ignore_errors=True)
            tmp.unlink(missing_ok=True)

    title = bme_format.run(BME_DIR, song_id)

    final_dir = RESULT_DIR / f"{song_id} {title}"
    final_dir.mkdir(exist_ok=True)

    for f in BME_DIR.glob("*"):
        shutil.move(f, final_dir / f.name)

    for f in DX2_DIR.glob("*.wav"):
        shutil.move(f, final_dir / f.name)

    for f in (WMA2WAV_DIR / "output .wav").glob("*.wav"):
        shutil.move(f, final_dir / f.name)

    for f in DX2_DIR.glob("*.2dx"):
        f.unlink(missing_ok=True)

    for f in INPUT_DIR.iterdir():
        if f.is_file():
            f.unlink(missing_ok=True)

    handle_media(song_id, final_dir)

    shutil.rmtree(BASE_DIR / "__pycache__", ignore_errors=True)
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
