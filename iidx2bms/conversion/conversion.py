from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import mmap
import os
import re
import shutil
import subprocess
import struct
import sys
import tempfile
import time
from pathlib import Path

from ifstools.ifs import IFS
from search_engine.search_engine import SearchResult


_BME_REMOVE_PREFIXES = (
    "#SUBARTIST",
    "#VOLWAV",
    "#MOVIEDELAY",
    "#PLAYTIME",
    "#PREVIEW",
    "#TOTALNOTES",
    "#REALNOTES",
    "#BACKBMP",
)
_GAME_VERSION_CACHE: dict[str, dict[int, int]] = {}
_SONG_META_CACHE: dict[str, dict[int, dict[str, object]]] = {}
_MOVIE_FILE_CACHE: dict[str, dict[str, Path]] = {}
_TEMP_DIR_PREFIX = "iidx2bms_"


def cleanup_temp_workdirs() -> int:
    temp_dir = Path(tempfile.gettempdir())
    removed = 0
    for path in temp_dir.glob(f"{_TEMP_DIR_PREFIX}*"):
        if not path.is_dir():
            continue
        shutil.rmtree(path, ignore_errors=True)
        removed += 1
    return removed


def _sanitize_result_folder_name(text: str) -> str:
    clean = re.sub(r'[<>:"/\\|?*]', "_", text).strip().rstrip(". ")
    return clean


def _run_external_command(
    command: list[str],
    working_directory: Path,
    stdin_data: str | None = None,
    raise_on_error: bool = True,
) -> tuple[int, str]:
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    completed = subprocess.run(
        command,
        cwd=str(working_directory),
        input=stdin_data,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags,
        check=False,
    )
    output = completed.stdout or ""
    if raise_on_error and completed.returncode != 0:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n{output.strip()}"
        )
    return completed.returncode, output


def _find_chart_source(sound_root: Path, song_id_display: str) -> tuple[str, dict[str, Path]]:
    base_dirs = [sound_root / song_id_display, sound_root]
    for base_dir in base_dirs:
        one_file = base_dir / f"{song_id_display}.1"
        s3p_file = base_dir / f"{song_id_display}.s3p"
        pre_file = base_dir / f"{song_id_display}_pre.2dx"
        if one_file.is_file() and s3p_file.is_file() and pre_file.is_file():
            return (
                "standard",
                {
                    "one": one_file,
                    "audio": s3p_file,
                    "preview": pre_file,
                },
            )

        ifs_file = base_dir / f"{song_id_display}.ifs"
        if ifs_file.is_file():
            return ("ifs", {"ifs": ifs_file})

    raise RuntimeError(f"Chart source files not found for ID {song_id_display}")


def _copy_chart_files(files: dict[str, Path], target_dir: Path) -> dict[str, Path]:
    copied: dict[str, Path] = {}
    for key, source_path in files.items():
        destination = target_dir / source_path.name
        shutil.copy2(source_path, destination)
        copied[key] = destination
    return copied


def _prepare_from_ifs(
    project_root: Path,
    work_dir: Path,
    song_id_display: str,
    ifs_file: Path,
) -> dict[str, Path]:
    copied_ifs = _copy_chart_files({"ifs": ifs_file}, work_dir)["ifs"]
    out_dir = work_dir / f"{song_id_display}_ifs"
    archive = IFS(str(copied_ifs))
    try:
        archive.extract(
            path=str(out_dir),
            progress=False,
            recurse=True,
            extract_manifest=False,
            rename_dupes=True,
        )
    finally:
        archive.close()

    extracted_chart_dir = out_dir / song_id_display
    if not extracted_chart_dir.is_dir():
        raise RuntimeError(f"IFS unpacked chart folder not found: {extracted_chart_dir}")

    required_names_2dx = {
        f"{song_id_display}.1",
        f"{song_id_display}.2dx",
        f"{song_id_display}_pre.2dx",
    }
    required_names_s3p = {
        f"{song_id_display}.1",
        f"{song_id_display}.s3p",
        f"{song_id_display}_pre.2dx",
    }
    all_files = [path for path in extracted_chart_dir.iterdir() if path.is_file()]
    all_file_names = {path.name for path in all_files}
    if all_file_names != required_names_2dx and all_file_names != required_names_s3p:
        raise RuntimeError(
            f"Chart {song_id_display} is non-standard. Found files: {sorted(all_file_names)}"
        )

    audio_file_name = (
        f"{song_id_display}.2dx"
        if f"{song_id_display}.2dx" in all_file_names
        else f"{song_id_display}.s3p"
    )

    return _copy_chart_files(
        {
            "one": extracted_chart_dir / f"{song_id_display}.1",
            "audio": extracted_chart_dir / audio_file_name,
            "preview": extracted_chart_dir / f"{song_id_display}_pre.2dx",
        },
        work_dir,
    )


def _extract_wavs_from_2dx(project_root: Path, work_dir: Path, archive_path: Path) -> Path:
    out_dir = work_dir / f"{archive_path.name}.out"
    out_dir.mkdir(parents=True, exist_ok=True)

    magic = b"2DX9"
    keysound_count_offset = 0x14
    file_size_offset = 0x08
    data_offset = 0x18
    min_filename_digits = 4

    with archive_path.open("rb") as fp:
        with mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ) as arc:
            fsize = arc.size()
            keysound_num = 0
            if fsize >= keysound_count_offset + 2:
                keysound_num = int.from_bytes(
                    arc[keysound_count_offset : keysound_count_offset + 2],
                    byteorder="little",
                    signed=False,
                )

            exports: list[tuple[int, int]] = []
            i = 0
            while i < fsize:
                pos = arc.find(magic, i)
                if pos < 0:
                    break
                size_pos = pos + file_size_offset
                wav_data_pos = pos + data_offset
                if size_pos + 4 > fsize or wav_data_pos > fsize:
                    break
                wav_fsize = int.from_bytes(arc[size_pos : size_pos + 4], "little", signed=False)
                wav_end = wav_data_pos + wav_fsize
                if wav_end > fsize:
                    break
                exports.append((wav_data_pos, wav_fsize))
                i = wav_end

            count_for_padding = max(len(exports), keysound_num, 1)
            digits = max(min_filename_digits, len(str(count_for_padding)))
            for idx, (pos, wav_size) in enumerate(exports, start=1):
                out_name = f"{idx:0{digits}d}.wav"
                with open(out_dir / out_name, "wb") as out_fp:
                    out_fp.write(arc[pos : pos + wav_size])

    if not any(out_dir.glob("*.wav")):
        raise RuntimeError(f"2DX output folder not found: {out_dir}")
    return out_dir


def _extract_wavs_from_s3p(project_root: Path, work_dir: Path, archive_path: Path) -> Path:
    out_dir = work_dir / f"{archive_path.name}.out"
    out_dir.mkdir(parents=True, exist_ok=True)

    s3p_magic = b"S3P0"
    s3v_magic = b"S3V0"
    header_struct = struct.Struct("<4sI")
    entry_struct = struct.Struct("<II")
    s3v0_struct = struct.Struct("<4sII20s")

    with archive_path.open("rb") as file_obj:
        with mmap.mmap(file_obj.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            if len(mm) < header_struct.size:
                raise RuntimeError(f"S3P output folder not found: {out_dir}")

            magic, entries_count = header_struct.unpack_from(mm, 0)
            if magic != s3p_magic:
                raise RuntimeError(f"S3P output folder not found: {out_dir}")

            entries_table_end = header_struct.size + entries_count * entry_struct.size
            if entries_table_end > len(mm):
                raise RuntimeError(f"S3P output folder not found: {out_dir}")

            entries_region = mm[header_struct.size:entries_table_end]
            for index, (offset, length) in enumerate(entry_struct.iter_unpack(entries_region), start=1):
                if offset < 0 or length < s3v0_struct.size or offset + length > len(mm):
                    continue
                magic_s3v, file_start, _payload_len, _unknown = s3v0_struct.unpack_from(mm, offset)
                if magic_s3v != s3v_magic:
                    continue
                data_start = offset + file_start
                data_end = offset + length
                if data_start > data_end:
                    continue
                out_name = f"{index:04d}.wav"
                with (out_dir / out_name).open("wb", buffering=4 * 1024 * 1024) as wf:
                    wf.write(mm[data_start:data_end])

    if not any(out_dir.glob("*.wav")):
        raise RuntimeError(f"S3P output folder not found: {out_dir}")
    return out_dir


def _collect_bmes(source_dir: Path, min_mtime: float) -> list[Path]:
    candidates = []
    for bme_file in source_dir.rglob("*.bme"):
        try:
            if bme_file.stat().st_mtime >= min_mtime:
                candidates.append(bme_file)
        except OSError:
            continue
    return sorted(candidates)


def _run_one2bme(project_root: Path, work_dir: Path, one_file: Path) -> Path:
    one2bme_exe = project_root / "one2bme" / "one2bme.exe"
    if not one2bme_exe.is_file():
        raise RuntimeError(f"one2bme.exe not found: {one2bme_exe}")

    bme_dir = work_dir / ".bme files"
    bme_dir.mkdir(parents=True, exist_ok=True)
    start_time = time.time() - 1.0

    strategies: list[tuple[list[str], Path]] = [
        ([str(one2bme_exe), one_file.name], work_dir),
        ([str(one2bme_exe), str(one_file)], work_dir),
        ([str(one2bme_exe)], work_dir),
    ]

    one2bme_work = work_dir / "_one2bme_work"
    one2bme_work.mkdir(parents=True, exist_ok=True)
    local_exe = one2bme_work / "one2bme.exe"
    local_one = one2bme_work / one_file.name
    shutil.copy2(one2bme_exe, local_exe)
    shutil.copy2(one_file, local_one)
    strategies.extend(
        [
            ([str(local_exe), local_one.name], one2bme_work),
            ([str(local_exe)], one2bme_work),
        ]
    )

    attempt_logs: list[str] = []
    for command, cwd in strategies:
        code, output = _run_external_command(command, cwd, "\n\n", raise_on_error=False)
        preview = output.strip().splitlines()
        preview_text = " | ".join(preview[-3:]) if preview else ""
        attempt_logs.append(f"cmd={' '.join(command)} cwd={cwd} code={code} out={preview_text}")

        recent_bmes = []
        recent_bmes.extend(_collect_bmes(work_dir, start_time))
        recent_bmes.extend(_collect_bmes(one2bme_work, start_time))
        recent_bmes.extend(_collect_bmes(project_root / "one2bme", start_time))

        unique_recent = []
        seen = set()
        for path in recent_bmes:
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            unique_recent.append(path)

        if unique_recent:
            for source_bme in unique_recent:
                shutil.copy2(source_bme, bme_dir / source_bme.name)
            return bme_dir

    joined_logs = "\n".join(attempt_logs)
    raise RuntimeError(f"one2bme did not generate any .bme files\n{joined_logs}")


def _copy_results(
    project_root: Path,
    results_root: Path,
    result: SearchResult,
    movie_root: Path,
    bme_dir: Path,
    main_audio_out_dir: Path,
    preview_out_dir: Path | None,
    fully_overwrite: bool = False,
    include_stagefile: bool = True,
    include_bga: bool = True,
    include_preview: bool = True,
) -> Path:
    results_root.mkdir(parents=True, exist_ok=True)
    if fully_overwrite:
        id_prefix_new = f"{result.song_id_display} "
        id_prefix_old = f"{result.song_id_display} -"
        for existing in results_root.iterdir():
            if not existing.is_dir():
                continue
            if existing.name.startswith(id_prefix_new) or existing.name.startswith(id_prefix_old):
                shutil.rmtree(existing, ignore_errors=True)
    song_meta = _resolve_song_meta(result, project_root)
    title_attr = getattr(result, "title", None)
    if title_attr is None:
        title = str(song_meta.get("title") or result.title_ascii or "").strip()
    else:
        title = str(title_attr).strip()
    sanitized_title = _sanitize_result_folder_name(title)
    folder_name = f"{result.song_id_display} {sanitized_title}" if sanitized_title else f"{result.song_id_display}"
    result_dir = results_root / folder_name
    result_dir.mkdir(parents=True, exist_ok=True)
    game_version = _resolve_game_version(result, project_root)
    genre_attr = getattr(result, "genre", None)
    title_attr = getattr(result, "title", None)
    artist_attr = getattr(result, "artist", None)
    genre_value = str(song_meta.get("genre") or "").strip() if genre_attr is None else str(genre_attr).strip()
    title_value = (
        str(song_meta.get("title") or result.title_ascii or "").strip()
        if title_attr is None
        else str(title_attr).strip()
    )
    artist_value = str(song_meta.get("artist") or "").strip() if artist_attr is None else str(artist_attr).strip()
    bga_base_value = str(song_meta.get("bga_filename") or "").strip()
    bmp01_value, bmp01_source = _resolve_bga_with_extension(movie_root, bga_base_value)
    stage_target_name = "1.png"
    if include_stagefile:
        if game_version < 0:
            raise RuntimeError(f"game_version is missing for song_id={result.song_id}")
        stage_source = _pick_stage_image(project_root, game_version)
        shutil.copy2(stage_source, result_dir / stage_target_name)

    for bme_file in sorted(bme_dir.glob("*.bme")):
        normalized_name = bme_file.name.lstrip()
        copied_bme = result_dir / normalized_name
        shutil.copy2(bme_file, copied_bme)
        _strip_bme_metadata(copied_bme)
        difficulty = _difficulty_for_bme_name(normalized_name, result)
        _set_bme_difficulty(copied_bme, difficulty)
        if include_stagefile:
            _set_bme_stagefile(copied_bme, stage_target_name)
        _set_bme_tag(copied_bme, "#GENRE", genre_value)
        _set_bme_tag(copied_bme, "#TITLE", title_value)
        _set_bme_tag(copied_bme, "#ARTIST", artist_value)
        if include_bga:
            _set_bme_tag(copied_bme, "#BMP01", bmp01_value)
    if include_bga and bmp01_source is not None:
        shutil.copy2(bmp01_source, result_dir / bmp01_source.name)
    for wav_file in sorted(main_audio_out_dir.glob("*.wav")):
        shutil.copy2(wav_file, result_dir / wav_file.name)

    if include_preview:
        if preview_out_dir is None:
            raise RuntimeError("Preview output directory is missing")
        preview_wavs = sorted(preview_out_dir.glob("*.wav"))
        if not preview_wavs:
            raise RuntimeError("Preview .2dx did not produce any .wav files")
        shutil.copy2(preview_wavs[0], result_dir / "preview_auto_generator.wav")
    return result_dir


def _read_text_with_fallback(path: Path) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "cp932", "shift_jis", "latin-1"):
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1"), "latin-1"


def _strip_bme_metadata(path: Path) -> None:
    raw_text, encoding = _read_text_with_fallback(path)
    lines = raw_text.splitlines(keepends=True)
    filtered_lines = []
    for line in lines:
        normalized = line.lstrip().upper()
        if normalized.startswith(_BME_REMOVE_PREFIXES):
            continue
        filtered_lines.append(line)
    path.write_text("".join(filtered_lines), encoding=encoding)


def _difficulty_for_bme_name(file_name: str, result: SearchResult) -> int | None:
    upper_name = file_name.upper()
    mapping = (
        ("[BEGINNER7]", result.spb_level),
        ("[BEGINNER14]", result.dpb_level),
        ("[NORMAL7]", result.spn_level),
        ("[NORMAL14]", result.dpn_level),
        ("[HYPER7]", result.sph_level),
        ("[HYPER14]", result.dph_level),
        ("[ANOTHER7]", result.spa_level),
        ("[ANOTHER14]", result.dpa_level),
        ("[LEGGENDARIA7]", result.spl_level),
        ("[LEGGENDARIA14]", result.dpl_level),
    )
    for token, value in mapping:
        if token in upper_name:
            return int(value)
    return None


def _set_bme_difficulty(path: Path, difficulty: int | None) -> None:
    if difficulty is None:
        return
    raw_text, encoding = _read_text_with_fallback(path)
    lines = raw_text.splitlines(keepends=True)
    line_break = "\r\n" if "\r\n" in raw_text else "\n"
    filtered_lines = []
    replaced = False
    for line in lines:
        if line.lstrip().upper().startswith("#PLAYLEVEL"):
            filtered_lines.append(f"#PLAYLEVEL {difficulty}{line_break}")
            replaced = True
        else:
            filtered_lines.append(line)
    if not replaced:
        filtered_lines.append(f"#PLAYLEVEL {difficulty}{line_break}")
    path.write_text("".join(filtered_lines), encoding=encoding)


def set_bme_playlevel(path: Path, difficulty: int) -> None:
    _set_bme_difficulty(path, int(difficulty))


def _set_bme_stagefile(path: Path, stagefile_name: str) -> None:
    raw_text, encoding = _read_text_with_fallback(path)
    lines = raw_text.splitlines(keepends=True)
    line_break = "\r\n" if "\r\n" in raw_text else "\n"
    filtered_lines = []
    replaced = False
    for line in lines:
        if line.lstrip().upper().startswith("#STAGEFILE"):
            filtered_lines.append(f"#STAGEFILE {stagefile_name}{line_break}")
            replaced = True
        else:
            filtered_lines.append(line)
    if not replaced:
        filtered_lines.append(f"#STAGEFILE {stagefile_name}{line_break}")
    path.write_text("".join(filtered_lines), encoding=encoding)


def _set_bme_tag(path: Path, tag_name: str, tag_value: str) -> None:
    raw_text, encoding = _read_text_with_fallback(path)
    lines = raw_text.splitlines(keepends=True)
    line_break = "\r\n" if "\r\n" in raw_text else "\n"
    filtered_lines = []
    replaced = False
    tag_upper = tag_name.upper()
    for line in lines:
        if line.lstrip().upper().startswith(tag_upper):
            filtered_lines.append(f"{tag_name} {tag_value}{line_break}")
            replaced = True
        else:
            filtered_lines.append(line)
    if not replaced:
        filtered_lines.append(f"{tag_name} {tag_value}{line_break}")
    path.write_text("".join(filtered_lines), encoding=encoding)


def _game_version_map(project_root: Path) -> dict[int, int]:
    cache_key = str(project_root.resolve())
    cached = _GAME_VERSION_CACHE.get(cache_key)
    if cached is not None:
        return cached

    mapping: dict[int, int] = {}
    for song_id, meta in _song_meta_map(project_root).items():
        mapping[song_id] = int(meta.get("game_version", -1))
    _GAME_VERSION_CACHE[cache_key] = mapping
    return mapping


def _song_meta_map(project_root: Path) -> dict[int, dict[str, object]]:
    cache_key = str(project_root.resolve())
    cached = _SONG_META_CACHE.get(cache_key)
    if cached is not None:
        return cached

    data_path = project_root / "music_data" / "music_data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    mapping: dict[int, dict[str, object]] = {}
    for chart in data.get("data", []):
        song_id = int(chart.get("song_id", 0))
        raw_version = chart.get("game_version", -1)
        game_version = -1 if raw_version is None else int(raw_version)
        mapping[song_id] = {
            "game_version": game_version,
            "genre": str(chart.get("genre", "") or ""),
            "title": str(chart.get("title", "") or ""),
            "artist": str(chart.get("artist", "") or ""),
            "bga_filename": str(chart.get("bga_filename", "") or ""),
        }
    _SONG_META_CACHE[cache_key] = mapping
    return mapping


def _resolve_game_version(result: SearchResult, project_root: Path) -> int:
    if int(result.game_version) >= 0:
        return int(result.game_version)
    return int(_game_version_map(project_root).get(result.song_id, -1))


def _resolve_song_meta(result: SearchResult, project_root: Path) -> dict[str, object]:
    return _song_meta_map(project_root).get(result.song_id, {})


def _movie_file_map(movie_root: Path) -> dict[str, Path]:
    cache_key = str(movie_root.resolve())
    cached = _MOVIE_FILE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    mapping: dict[str, Path] = {}
    priorities: dict[str, int] = {
        ".mp4": 0,
        ".wmv": 1,
        ".avi": 2,
        ".mpg": 3,
        ".mpeg": 4,
        ".mov": 5,
        ".mkv": 6,
        ".webm": 7,
    }
    chosen_priority: dict[str, int] = {}
    for file_path in movie_root.rglob("*"):
        if not file_path.is_file():
            continue
        ext = file_path.suffix.lower()
        if ext not in priorities:
            continue
        stem = file_path.stem.strip().lower()
        if not stem:
            continue
        ext_priority = priorities[ext]
        current = chosen_priority.get(stem)
        if current is None or ext_priority < current:
            chosen_priority[stem] = ext_priority
            mapping[stem] = file_path
    _MOVIE_FILE_CACHE[cache_key] = mapping
    return mapping


def _resolve_bga_with_extension(movie_root: Path, bga_name: str) -> tuple[str, Path | None]:
    base = bga_name.strip()
    if not base:
        return "", None
    if Path(base).suffix:
        file_name = Path(base).name
        resolved = movie_root / file_name
        return file_name, (resolved if resolved.is_file() else None)
    resolved = _movie_file_map(movie_root).get(base.lower())
    if resolved is None:
        return base, None
    return resolved.name, resolved


def _pick_stage_image(project_root: Path, game_version: int) -> Path:
    stage_dir = project_root / "stagefiles" / str(game_version)
    if not stage_dir.is_dir():
        raise RuntimeError(f"Stagefile directory not found for game_version={game_version}: {stage_dir}")
    candidates = sorted(
        [
            path
            for path in stage_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        ]
    )
    if not candidates:
        raise RuntimeError(f"No stage image found in {stage_dir}")
    return candidates[0]


def convert_chart(
    result: SearchResult,
    sound_root: Path,
    movie_root: Path,
    project_root: Path,
    results_root: Path,
    fully_overwrite: bool = False,
    include_stagefile: bool = True,
    include_bga: bool = True,
    include_preview: bool = True,
) -> Path:
    source_kind, source_files = _find_chart_source(sound_root, result.song_id_display)
    temp_root = Path(tempfile.mkdtemp(prefix=f"{_TEMP_DIR_PREFIX}{result.song_id_display}_"))
    work_dir = temp_root / result.song_id_display
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        if source_kind == "standard":
            copied = _copy_chart_files(source_files, work_dir)
            bme_dir = _run_one2bme(project_root, work_dir, copied["one"])
            if include_preview:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    main_future = executor.submit(
                        _extract_wavs_from_s3p, project_root, work_dir, copied["audio"]
                    )
                    preview_future = executor.submit(
                        _extract_wavs_from_2dx, project_root, work_dir, copied["preview"]
                    )
                    main_audio_out_dir = main_future.result()
                    preview_out_dir = preview_future.result()
            else:
                main_audio_out_dir = _extract_wavs_from_s3p(project_root, work_dir, copied["audio"])
                preview_out_dir = None
            return _copy_results(
                project_root,
                results_root,
                result,
                movie_root,
                bme_dir,
                main_audio_out_dir,
                preview_out_dir,
                fully_overwrite=fully_overwrite,
                include_stagefile=include_stagefile,
                include_bga=include_bga,
                include_preview=include_preview,
            )

        copied = _prepare_from_ifs(project_root, work_dir, result.song_id_display, source_files["ifs"])
        bme_dir = _run_one2bme(project_root, work_dir, copied["one"])
        if include_preview:
            with ThreadPoolExecutor(max_workers=2) as executor:
                if copied["audio"].suffix.lower() == ".s3p":
                    main_future = executor.submit(_extract_wavs_from_s3p, project_root, work_dir, copied["audio"])
                else:
                    main_future = executor.submit(_extract_wavs_from_2dx, project_root, work_dir, copied["audio"])
                preview_future = executor.submit(_extract_wavs_from_2dx, project_root, work_dir, copied["preview"])
                main_audio_out_dir = main_future.result()
                preview_out_dir = preview_future.result()
        else:
            if copied["audio"].suffix.lower() == ".s3p":
                main_audio_out_dir = _extract_wavs_from_s3p(project_root, work_dir, copied["audio"])
            else:
                main_audio_out_dir = _extract_wavs_from_2dx(project_root, work_dir, copied["audio"])
            preview_out_dir = None
        return _copy_results(
            project_root,
            results_root,
            result,
            movie_root,
            bme_dir,
            main_audio_out_dir,
            preview_out_dir,
            fully_overwrite=fully_overwrite,
            include_stagefile=include_stagefile,
            include_bga=include_bga,
            include_preview=include_preview,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
