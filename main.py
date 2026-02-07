import subprocess
import time
from pathlib import Path
import shutil
import bme_format
import re
import json
import remywiki_search

BASE_DIR = Path(__file__).parent

INPUT_DIR = BASE_DIR / "put .1, .s3p and _pre.2dx or only .ifs files here"
MEDIA_DIR = BASE_DIR / "put .png and .mp4 here"

S3P_DIR = BASE_DIR / "s3p_extract"
IFS_DIR = BASE_DIR / "ifs_extract"
DX2_DIR = BASE_DIR / "2dx_extract"
PREVIEW_DIR = BASE_DIR / "2dx_preview_extractor"
WMA2WAV_DIR = BASE_DIR / "wma2wav"

BME_DIR = BASE_DIR / ".bme files"
RESULT_DIR = BASE_DIR / "result"
SETTINGS_PATH = BASE_DIR / "settings.json"

DIGITS_5 = re.compile(r"^\d{5}$")


def load_saved_preview_choice():
    if not SETTINGS_PATH.exists():
        return None

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    value = data.get("preview_auto_generator")
    if isinstance(value, bool):
        return value
    return None


def save_preview_choice(choice: bool):
    data = {}
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}

    data["preview_auto_generator"] = choice
    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ask_preview_choice():
    saved_choice = load_saved_preview_choice()
    if saved_choice is not None:
        return saved_choice

    while True:
        answer = input(
            "Add preview_auto_generator.wav? (y/n, Enter = y, type ys/ns to save and remember choice): "
        ).strip().lower()

        if answer in {"", "y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        if answer == "ys":
            save_preview_choice(True)
            return True
        if answer == "ns":
            save_preview_choice(False)
            return False

        print("Invalid input. Use y, n, ys, ns, or Enter.")


def full_cleanup_start():
    shutil.rmtree(BASE_DIR / "__pycache__", ignore_errors=True)

    if BME_DIR.exists():
        shutil.rmtree(BME_DIR, ignore_errors=True)
    BME_DIR.mkdir(exist_ok=True)

    if (WMA2WAV_DIR / "output .wav").exists():
        shutil.rmtree(WMA2WAV_DIR / "output .wav", ignore_errors=True)
    (WMA2WAV_DIR / "output .wav").mkdir(parents=True, exist_ok=True)

    if S3P_DIR.exists():
        for p in S3P_DIR.iterdir():
            if p.name.lower() != "s3p_extract.exe":
                if p.is_file():
                    p.unlink(missing_ok=True)
                else:
                    shutil.rmtree(p, ignore_errors=True)

    if DX2_DIR.exists():
        for p in DX2_DIR.iterdir():
            if p.name.lower() != "2dx_extract.exe":
                if p.is_file():
                    p.unlink(missing_ok=True)
                else:
                    shutil.rmtree(p, ignore_errors=True)


def final_cleanup(keep_input: bool = False):
    if IFS_DIR.exists():
        for p in IFS_DIR.iterdir():
            if p.name.lower() != "ifs_extract.exe":
                if p.is_file():
                    p.unlink(missing_ok=True)
                else:
                    shutil.rmtree(p, ignore_errors=True)

    if DX2_DIR.exists():
        for p in DX2_DIR.iterdir():
            if p.name.lower() != "2dx_extract.exe":
                if p.is_file():
                    p.unlink(missing_ok=True)
                else:
                    shutil.rmtree(p, ignore_errors=True)

    if INPUT_DIR.exists() and not keep_input:
        for p in INPUT_DIR.iterdir():
            if p.is_file():
                p.unlink(missing_ok=True)
            else:
                shutil.rmtree(p, ignore_errors=True)

    shutil.rmtree(BASE_DIR / "__pycache__", ignore_errors=True)


def run_one2bme(one_file: Path):
    tmp = BASE_DIR / one_file.name
    shutil.copy(one_file, tmp)

    proc = subprocess.Popen(
        [str(BASE_DIR / "one2bme.exe")],
        cwd=BASE_DIR,
        stdin=subprocess.PIPE
    )
    time.sleep(1)
    proc.stdin.write(b"\n")
    proc.stdin.flush()
    proc.wait()

    for bme in BASE_DIR.glob("*.bme"):
        shutil.move(bme, BME_DIR / bme.name)

    tmp.unlink(missing_ok=True)


def extract_s3p(s3p_file: Path):
    tmp = S3P_DIR / s3p_file.name
    shutil.copy(s3p_file, tmp)

    subprocess.run(
        [str(S3P_DIR / "s3p_extract.exe"), str(tmp)],
        cwd=S3P_DIR
    )

    out_dir = S3P_DIR / f"{s3p_file.stem}.s3p.out"
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


def extract_2dx(dx2_file: Path):
    shutil.copy(dx2_file, DX2_DIR / dx2_file.name)
    subprocess.run(
        [str(DX2_DIR / "2dx_extract.exe"), dx2_file.name],
        cwd=DX2_DIR
    )
    subprocess.run(
        ["python", "rename.py", str(DX2_DIR)],
        cwd=WMA2WAV_DIR
    )


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
    full_cleanup_start()

    if not INPUT_DIR.exists():
        input('Folder "put .1, .s3p and _pre.2dx or only .ifs files here" is empty')
        final_cleanup()
        return
    files = list(INPUT_DIR.iterdir())
    if not files:
        input('Folder "put .1, .s3p and _pre.2dx or only .ifs files here" is empty')
        final_cleanup()
        return

    want_preview = ask_preview_choice()
    ifs = next((f for f in files if f.suffix.lower() == ".ifs"), None)
    one = next((f for f in files if f.suffix.lower() == ".1"), None)
    s3p = next((f for f in files if f.suffix.lower() == ".s3p"), None)
    pre_dx2 = next((f for f in files if f.name.lower().endswith("_pre.2dx")), None)

    song_id = None
    preview_dx2 = None

    if ifs:
        song_id = ifs.stem
        shutil.copy(ifs, IFS_DIR / ifs.name)

        subprocess.run(
            [str(IFS_DIR / "ifs_extract.exe"), ifs.name],
            cwd=IFS_DIR
        )

        out = IFS_DIR / ifs.stem
        one = next(out.glob("*.1"), None)
        s3p = next(out.glob("*.s3p"), None)
        dx2 = next((f for f in out.glob("*.2dx") if not f.name.endswith("_pre.2dx")), None)
        pre_dx2 = next((f for f in out.glob("*_pre.2dx")), None)

        files_in_out = [f for f in out.iterdir() if f.is_file()]
        if (
            not one
            or not DIGITS_5.fullmatch(one.stem)
            or not dx2
            or len(files_in_out) not in (2, 3)
            or any(
                f.name not in {one.name, dx2.name, pre_dx2.name if pre_dx2 else None}
                for f in files_in_out
            )
        ):
            input("Non-standard .ifs file, convert this chart manually. Press Enter to exit...")
            final_cleanup()
            return
        if want_preview:
            if not pre_dx2:
                input(f'To create preview_auto_generator.wav, extracted file "{song_id}_pre.2dx" was not found in "ifs_extract\\{song_id}". Press Enter to exit...')
                final_cleanup()
                return
            if pre_dx2.stem != f"{song_id}_pre":
                input("Non-standard .ifs file, convert this chart manually. Press Enter to exit...")
                final_cleanup()
                return
            preview_dx2 = pre_dx2

        shutil.copy(one, INPUT_DIR / one.name)
        run_one2bme(one)

        if s3p:
            extract_s3p(s3p)
        elif dx2:
            extract_2dx(dx2)

    else:
        if not one:
            input("No .1 file found. Press Enter to exit...")
            final_cleanup()
            return

        song_id = one.stem
        if want_preview:
            if not pre_dx2:
                input('To create preview_auto_generator.wav, put xxxxx_pre.2dx in folder "put .1, .s3p and _pre.2dx or only .ifs files here". Press Enter to exit...')
                final_cleanup(keep_input=True)
                return
            if pre_dx2.stem != f"{song_id}_pre":
                input("Non-standard input files, convert this chart manually. Press Enter to exit...")
                final_cleanup()
                return
            preview_dx2 = pre_dx2

        run_one2bme(one)

        if s3p:
            extract_s3p(s3p)

    remywiki_search.remywiki_search_loop()

    title = bme_format.run(BME_DIR, song_id)
    title_clean = title.strip()
    title_safe = re.sub(r'[<>:"/\\|?*]', "", title_clean)
    title_safe = re.sub(r"\s+", " ", title_safe).strip()
    if title_safe:
        final_dir = RESULT_DIR / f"{song_id} {title_safe}"
    else:
        final_dir = RESULT_DIR / f"{song_id}"
    final_dir.mkdir(parents=True, exist_ok=True)

    for f in BME_DIR.glob("*"):
        shutil.move(f, final_dir / f.name)

    for f in (WMA2WAV_DIR / "output .wav").glob("*.wav"):
        shutil.move(f, final_dir / f.name)

    for f in DX2_DIR.glob("*.wav"):
        shutil.move(f, final_dir / f.name)

    if want_preview and preview_dx2:
        subprocess.run(
            ["python", str(PREVIEW_DIR / "2dx_preview_extractor.py"), str(preview_dx2)],
            cwd=BASE_DIR
        )
        preview_wav = PREVIEW_DIR / "preview_auto_generator.wav"
        if preview_wav.exists():
            shutil.move(preview_wav, final_dir / preview_wav.name)

    handle_media(song_id, final_dir)

    final_cleanup()
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
