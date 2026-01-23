from pathlib import Path
import sys

OUTPUT_DIR = Path(sys.argv[1])

files = sorted(
    OUTPUT_DIR.glob("*.wav"),
    key=lambda p: int(p.stem)
)

temp = []
for i, f in enumerate(files, 1):
    t = f.with_name(f"__tmp_{i}.wav")
    f.rename(t)
    temp.append(t)

for i, t in enumerate(temp, 1):
    t.rename(OUTPUT_DIR / f"{i:04d}.wav")
