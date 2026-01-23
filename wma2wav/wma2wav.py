import subprocess
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_DIR = Path(sys.argv[1])
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output .wav"

OUTPUT_DIR.mkdir(exist_ok=True)

wma_files = list(INPUT_DIR.glob("*.wma"))
total = len(wma_files)

MAX_WORKERS = 6

def convert(wma_file):
    wav_file = OUTPUT_DIR / (wma_file.stem + ".wav")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-threads", "0",
            "-i", str(wma_file),
            "-acodec", "pcm_s16le",
            str(wav_file)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

done = 0
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(convert, f) for f in wma_files]
    for _ in as_completed(futures):
        done += 1
        percent = int(done / total * 100)
        print(f"\rConverting WMA → WAV: {done}/{total} ({percent}%)", end="", flush=True)

print()
