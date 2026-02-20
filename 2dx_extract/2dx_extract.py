from __future__ import annotations

import mmap
import sys
from dataclasses import dataclass
from pathlib import Path

MAGIC = b"2DX9"
KEYSOUND_COUNT_OFFSET = 0x14
FILE_SIZE_OFFSET = 0x08
DATA_OFFSET = 0x18
MIN_FILENAME_DIGITS = 4


@dataclass(slots=True)
class Info:
    verbose: bool = False
    super_verbose: bool = False
    info: bool = False


@dataclass(slots=True)
class WavEntry:
    pos: int
    fsize: int


def print_usage(prog: str) -> None:
    print(
        f"Usage: {prog} [options] [.2dx file]\nTry '{prog} -h' for more information.",
        file=sys.stderr,
    )


def print_help() -> None:
    print("2DX Extractor", file=sys.stderr)
    print(
        "Extracts WAV files (And just about anything else) from beatmania IIDX AC .2dx Archives\n",
        file=sys.stderr,
    )
    print("Options:", file=sys.stderr)
    print("    -h - Shows this help page", file=sys.stderr)
    print("    -i - Shows .2dx archive info (Without Extracting)", file=sys.stderr)
    print("    -v - Verbose", file=sys.stderr)
    print("    -V - Super Verbose (Shows more information)", file=sys.stderr)


def parse_argv(argv: list[str]) -> tuple[Info, str | None]:
    if len(argv) < 2:
        print_usage(argv[0])
        raise SystemExit(1)

    data = Info()
    eo = False

    for idx, arg in enumerate(argv):
        if arg.startswith("-") and len(arg) >= 2:
            opt = arg[1]
            if opt == "h":
                print_help()
            elif opt == "i":
                data.info = True
            elif opt == "v":
                data.verbose = True
            elif opt == "V":
                data.super_verbose = True
            else:
                print(f"[WARNING] Invalid Option \"-{opt}\"", file=sys.stderr)
                eo = idx == len(argv) - 1

    if eo:
        print("[ ERROR ] Last argument is not .2dx archive", file=sys.stderr)
        raise SystemExit(2)

    if argv[-1].startswith("-"):
        raise SystemExit(0)

    return data, argv[-1]


def read_2dx(path: Path) -> tuple[int, int, mmap.mmap, object]:
    try:
        fp = path.open("rb")
    except OSError as exc:
        print(f"[ ERROR ] Failed to open 2DX Archive: {exc}", file=sys.stderr)
        raise SystemExit(2)

    try:
        arc = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
    except Exception:
        fp.close()
        raise

    fsize = arc.size()
    if fsize >= KEYSOUND_COUNT_OFFSET + 2:
        keysound_num = int.from_bytes(
            arc[KEYSOUND_COUNT_OFFSET : KEYSOUND_COUNT_OFFSET + 2],
            byteorder="little",
            signed=False,
        )
    else:
        keysound_num = 0

    return keysound_num, fsize, arc, fp


def print_2dx_info(prog: str, archive_arg: str, keysound_num: int, fsize: int) -> None:
    print(f"'{archive_arg}' Archive Information\n")
    print(f"    Filename: {archive_arg}")
    print(f"    Files   : {keysound_num}")
    print(f"    Size    : {fsize} bytes")
    print(f"\nType '{prog} {archive_arg}' to extract the contents of this archive.")


def parse_data(arc: mmap.mmap, fsize: int, data: Info) -> list[WavEntry]:
    exports: list[WavEntry] = []
    i = 0

    while i < fsize:
        pos = arc.find(MAGIC, i)
        if pos < 0:
            break

        size_pos = pos + FILE_SIZE_OFFSET
        data_pos = pos + DATA_OFFSET
        if size_pos + 4 > fsize or data_pos > fsize:
            break

        wav_fsize = int.from_bytes(arc[size_pos : size_pos + 4], "little", signed=False)
        wav_end = data_pos + wav_fsize
        if wav_end > fsize:
            break

        export = WavEntry(pos=data_pos, fsize=wav_fsize)
        exports.append(export)
        n = len(exports)

        if data.verbose:
            print(f"Found {n}.wav")
        if data.super_verbose:
            print(
                f"Found {n}.wav\n"
                f"    Address: 0x{export.pos:08x} ~ 0x{export.pos + export.fsize:08x}\n"
                f"    Size: 0x{export.fsize:x} ({export.fsize} bytes)\n"
            )

        i = wav_end

    return exports


def extract_data(
    arc: mmap.mmap, exports: list[WavEntry], keysound_num: int, archive_path: Path
) -> None:
    count_for_padding = max(len(exports), keysound_num, 1)
    digits = max(MIN_FILENAME_DIGITS, len(str(count_for_padding)))
    out_dir = Path(f"{archive_path.name}.out")
    out_dir.mkdir(parents=True, exist_ok=True)

    for idx, export in enumerate(exports, start=1):
        out_name = f"{idx:0{digits}d}.wav"
        print(f"Extracting {out_name}... ", end="")

        with open(out_dir / out_name, "wb") as fp:
            fp.write(arc[export.pos : export.pos + export.fsize])

        print("Done")


def main(argv: list[str]) -> int:
    data, archive_arg = parse_argv(argv)
    if archive_arg is None:
        return 0

    archive_path = Path(archive_arg)
    keysound_num, fsize, arc, fp = read_2dx(archive_path)

    try:
        if data.info:
            print_2dx_info(argv[0], archive_arg, keysound_num, fsize)
        else:
            exports = parse_data(arc, fsize, data)
            extract_data(arc, exports, keysound_num, archive_path)
    finally:
        arc.close()
        fp.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
