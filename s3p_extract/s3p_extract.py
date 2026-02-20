from __future__ import annotations

import argparse
import mmap
import os
import struct
import sys
from pathlib import Path
from typing import Iterable

S3P_MAGIC = b"S3P0"
S3V_MAGIC = b"S3V0"
END_MARKER = 0x12345678

HEADER_STRUCT = struct.Struct("<4sI")
ENTRY_STRUCT = struct.Struct("<II")
S3V0_STRUCT = struct.Struct("<4sII20s")


def _copy_file_fast(src_fileno: int, dst_fileno: int, size: int) -> None:
    if size <= 0:
        return

    if hasattr(os, "sendfile"):
        sent_total = 0
        try:
            while sent_total < size:
                sent = os.sendfile(dst_fileno, src_fileno, sent_total, size - sent_total)
                if sent == 0:
                    break
                sent_total += sent
            if sent_total == size:
                return
            os.lseek(src_fileno, sent_total, os.SEEK_SET)
        except OSError:
            os.lseek(src_fileno, 0, os.SEEK_SET)

    chunk_size = 4 * 1024 * 1024
    remaining = size
    while remaining:
        data = os.read(src_fileno, min(chunk_size, remaining))
        if not data:
            break
        os.write(dst_fileno, data)
        remaining -= len(data)


def pack(infiles: Iterable[Path], out_filename: Path) -> None:
    infiles = [Path(p) for p in infiles]
    infile_count = len(infiles)
    print(f"Packing {infile_count} files")

    with out_filename.open("wb", buffering=0) as out_f:
        out_f.write(HEADER_STRUCT.pack(S3P_MAGIC, infile_count))
        out_f.write(b"\x00" * (ENTRY_STRUCT.size * infile_count))

        entries: list[tuple[int, int]] = []

        for src_path in infiles:
            print(f"Packing {src_path}")
            src_size = src_path.stat().st_size
            if src_size > 0xFFFFFFFF:
                raise ValueError(f"File too large for S3V0 length field: {src_path}")

            offset = out_f.tell()
            out_f.write(S3V0_STRUCT.pack(S3V_MAGIC, 0x20, src_size, b"\x00" * 20))

            with src_path.open("rb", buffering=0) as src_f:
                _copy_file_fast(src_f.fileno(), out_f.fileno(), src_size)

            end_pos = out_f.tell()
            length = end_pos - offset
            if offset > 0xFFFFFFFF or length > 0xFFFFFFFF:
                raise ValueError("Archive exceeds 32-bit offset/length limits")
            entries.append((offset, length))

        out_f.write(struct.pack("<I", END_MARKER))

        out_f.seek(HEADER_STRUCT.size)
        table = bytearray(ENTRY_STRUCT.size * infile_count)
        for i, (off, ln) in enumerate(entries):
            ENTRY_STRUCT.pack_into(table, i * ENTRY_STRUCT.size, off, ln)
        out_f.write(table)


def _extract_one(mm: mmap.mmap, offset: int, length: int, out_file: Path) -> None:
    if offset < 0 or length < S3V0_STRUCT.size or offset + length > len(mm):
        raise ValueError("Entry points outside file bounds")

    magic, filestart, _payload_len, _unknown = S3V0_STRUCT.unpack_from(mm, offset)
    if magic != S3V_MAGIC:
        got = bytes(mm[offset : offset + 4])
        raise ValueError(f"Bad magic! Need S3V0 got {got!r}")

    data_start = offset + filestart
    data_end = offset + length
    if data_start > data_end:
        raise ValueError("Invalid filestart in S3V0 header")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("wb", buffering=4 * 1024 * 1024) as wf:
        wf.write(mm[data_start:data_end])


def convert(path: Path) -> None:
    print(path)
    out_dir = Path(f"{path}.out")
    out_dir.mkdir(exist_ok=True)

    with path.open("rb") as f:
        file_size = f.seek(0, os.SEEK_END)
        if file_size < HEADER_STRUCT.size:
            raise ValueError("File too small for S3P header")
        f.seek(0)
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:

            magic, entries_count = HEADER_STRUCT.unpack_from(mm, 0)
            if magic != S3P_MAGIC:
                raise ValueError("Bad magic! Expected S3P0")

            entries_table_end = HEADER_STRUCT.size + entries_count * ENTRY_STRUCT.size
            if entries_table_end > len(mm):
                raise ValueError("Entry table exceeds file bounds")

            entries_region = mm[HEADER_STRUCT.size:entries_table_end]

            for i, (offset, length) in enumerate(ENTRY_STRUCT.iter_unpack(entries_region), start=1):
                print(f"{(i / entries_count) * 100:.2f}%")
                out_file = out_dir / f"{i:04d}.wav"
                _extract_one(mm, offset, length, out_file)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="s3p_extract",
        description="Extract and repack S3P0 archives (outputs .wav on extract)",
        allow_abbrev=False,
    )

    parser.add_argument("-pack", action="store_true", help="Pack input files into an S3P archive")
    parser.add_argument("-o", metavar="OUT", default="out.s3p", help="Output S3P filename (pack mode)")
    parser.add_argument("files", nargs="+", help="Input files")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.pack:
            pack([Path(p) for p in args.files], Path(args.o))
            return 0

        for p in args.files:
            convert(Path(p))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
