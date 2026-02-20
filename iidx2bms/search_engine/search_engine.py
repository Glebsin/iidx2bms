from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
from search_engine.game_names import game_name_for_version


def _display_song_id(song_id: int) -> str:
    song_id_str = str(song_id)
    if len(song_id_str) == 4:
        return f"0{song_id_str}"
    return song_id_str


@dataclass(frozen=True, slots=True)
class SearchResult:
    song_id: int
    song_id_display: str
    artist: str
    title: str
    title_ascii: str
    genre: str
    game_version: int
    game_name: str
    spb_level: int
    spn_level: int
    sph_level: int
    spa_level: int
    spl_level: int
    dpb_level: int
    dpn_level: int
    dph_level: int
    dpa_level: int
    dpl_level: int
    score: int
    tie_breaker: int

    @property
    def primary_line(self) -> str:
        return f"ID: {self.song_id_display}  {self.artist} - {self.title}"

    @property
    def secondary_line(self) -> str:
        if self.game_name:
            return f"Genre: {self.genre}  Game: {self.game_name}"
        return f"Genre: {self.genre}"


@dataclass(frozen=True, slots=True)
class _IndexedChart:
    song_id: int
    song_id_display: str
    title: str
    title_ascii: str
    artist: str
    genre: str
    game_version: int
    game_name: str
    spb_level: int
    spn_level: int
    sph_level: int
    spa_level: int
    spl_level: int
    dpb_level: int
    dpn_level: int
    dph_level: int
    dpa_level: int
    dpl_level: int
    title_norm: str
    title_ascii_norm: str
    artist_norm: str
    searchable: str


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _split_tokens(text: str) -> tuple[str, ...]:
    normalized = _normalize(text)
    if not normalized:
        return ()
    return tuple(token for token in normalized.split(" ") if token)


def _score_entry(
    entry: _IndexedChart,
    query: str,
    tokens: tuple[str, ...],
    is_numeric: bool,
) -> tuple[int, int] | None:
    if is_numeric:
        if entry.song_id_display == query:
            return (0, 0)
        if entry.song_id_display.startswith(query):
            return (1, len(entry.song_id_display) - len(query))
        if query in entry.song_id_display:
            return (2, entry.song_id_display.find(query))

    if entry.title_ascii_norm.startswith(query):
        return (3, len(entry.title_ascii_norm) - len(query))
    if entry.title_norm.startswith(query):
        return (4, len(entry.title_norm) - len(query))
    if entry.artist_norm.startswith(query):
        return (5, len(entry.artist_norm) - len(query))

    if tokens:
        positions = [entry.searchable.find(token) for token in tokens]
        if all(pos >= 0 for pos in positions):
            return (6, sum(positions))
        if any(pos >= 0 for pos in positions):
            best = min(pos for pos in positions if pos >= 0)
            return (7, best)

    if query in entry.searchable:
        return (8, entry.searchable.find(query))

    return None


class SearchEngine:
    def __init__(self, json_path: str | Path) -> None:
        self._json_path = Path(json_path)
        self._index: list[_IndexedChart] = []
        self._include_levels = False
        self._include_game_version = False
        self._include_genre = False
        self._details_loaded = False
        self._game_name_by_song_id: dict[int, str] = {}
        self._game_version_by_song_id: dict[int, int] = {}
        self._levels_by_song_id: dict[int, tuple[int, int, int, int, int, int, int, int, int, int]] = {}
        self._genre_by_song_id: dict[int, str] = {}
        self._load_index()

    def _load_index(self) -> None:
        data = json.loads(self._json_path.read_text(encoding="utf-8"))
        charts = data.get("data", [])

        index: list[_IndexedChart] = []
        for chart in charts:
            song_id = int(chart.get("song_id", 0))
            title = str(chart.get("title", "") or "")
            title_ascii = str(chart.get("title_ascii", "") or "")
            artist = str(chart.get("artist", "") or "")

            title_norm = _normalize(title)
            title_ascii_norm = _normalize(title_ascii)
            artist_norm = _normalize(artist)
            song_id_display = _display_song_id(song_id)

            searchable = " | ".join((song_id_display, title_norm, title_ascii_norm, artist_norm))
            index.append(
                _IndexedChart(
                    song_id=song_id,
                    song_id_display=song_id_display,
                    title=title,
                    title_ascii=title_ascii,
                    artist=artist,
                    genre="",
                    game_version=-1,
                    game_name="",
                    spb_level=0,
                    spn_level=0,
                    sph_level=0,
                    spa_level=0,
                    spl_level=0,
                    dpb_level=0,
                    dpn_level=0,
                    dph_level=0,
                    dpa_level=0,
                    dpl_level=0,
                    title_norm=title_norm,
                    title_ascii_norm=title_ascii_norm,
                    artist_norm=artist_norm,
                    searchable=searchable,
                )
            )

        self._index = index

    def _ensure_details_loaded(self) -> None:
        if self._details_loaded:
            return
        data = json.loads(self._json_path.read_text(encoding="utf-8"))
        charts = data.get("data", [])
        for chart in charts:
            song_id = int(chart.get("song_id", 0))
            genre = str(chart.get("genre", "") or "")
            raw_game_version = chart.get("game_version", -1)
            game_version = -1 if raw_game_version is None else int(raw_game_version)
            game_name = game_name_for_version(game_version) if game_version >= 0 else ""
            spb_level = int(chart.get("SPB_level", 0) or 0)
            spn_level = int(chart.get("SPN_level", 0) or 0)
            sph_level = int(chart.get("SPH_level", 0) or 0)
            spa_level = int(chart.get("SPA_level", 0) or 0)
            spl_level = int(chart.get("SPL_level", 0) or 0)
            dpb_level = int(chart.get("DPB_level", 0) or 0)
            dpn_level = int(chart.get("DPN_level", 0) or 0)
            dph_level = int(chart.get("DPH_level", 0) or 0)
            dpa_level = int(chart.get("DPA_level", 0) or 0)
            dpl_level = int(chart.get("DPL_level", 0) or 0)
            self._genre_by_song_id[song_id] = genre
            self._game_name_by_song_id[song_id] = game_name
            self._game_version_by_song_id[song_id] = game_version
            self._levels_by_song_id[song_id] = (
                spb_level,
                spn_level,
                sph_level,
                spa_level,
                spl_level,
                dpb_level,
                dpn_level,
                dph_level,
                dpa_level,
                dpl_level,
            )
        self._details_loaded = True

    def search(self, raw_query: str, limit: int = 100) -> list[SearchResult]:
        query = _normalize(raw_query)
        if not query:
            return []

        tokens = _split_tokens(query)
        is_numeric = query.isdigit()

        matches: list[SearchResult] = []
        append = matches.append
        include_any_details = self._include_levels or self._include_game_version or self._include_genre
        if include_any_details:
            self._ensure_details_loaded()

        for entry in self._index:
            scored = _score_entry(entry, query, tokens, is_numeric)
            if scored is None:
                continue

            score, tie_breaker = scored
            if self._include_levels:
                levels = self._levels_by_song_id.get(entry.song_id, (0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
            else:
                levels = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            game_version = self._game_version_by_song_id.get(entry.song_id, -1) if self._include_game_version else -1
            game_name = self._game_name_by_song_id.get(entry.song_id, "") if self._include_game_version else ""
            genre = self._genre_by_song_id.get(entry.song_id, "") if self._include_genre else ""
            append(
                SearchResult(
                    song_id=entry.song_id,
                    song_id_display=entry.song_id_display,
                    artist=entry.artist,
                    title=entry.title,
                    title_ascii=entry.title_ascii,
                    genre=genre,
                    game_version=game_version,
                    game_name=game_name,
                    spb_level=levels[0],
                    spn_level=levels[1],
                    sph_level=levels[2],
                    spa_level=levels[3],
                    spl_level=levels[4],
                    dpb_level=levels[5],
                    dpn_level=levels[6],
                    dph_level=levels[7],
                    dpa_level=levels[8],
                    dpl_level=levels[9],
                    score=score,
                    tie_breaker=tie_breaker,
                )
            )

        matches.sort(key=lambda item: (item.score, item.tie_breaker, item.song_id))
        if limit <= 0:
            return matches
        return matches[:limit]

    @property
    def size(self) -> int:
        return len(self._index)

    @property
    def cpu_budget(self) -> int:
        cores = os.cpu_count() or 1
        return max(1, cores - 1)

    def set_include_levels(self, include_levels: bool) -> None:
        self._include_levels = include_levels

    def set_include_game_version(self, include_game_version: bool) -> None:
        self._include_game_version = include_game_version

    def set_include_genre(self, include_genre: bool) -> None:
        self._include_genre = include_genre

    def ensure_game_name(self, result: SearchResult) -> SearchResult:
        self._ensure_details_loaded()
        if result.game_name:
            return result
        game_name = self._game_name_by_song_id.get(result.song_id, "")
        game_version = self._game_version_by_song_id.get(result.song_id, result.game_version)
        return replace(result, game_name=game_name, game_version=game_version)

    def ensure_levels(self, result: SearchResult) -> SearchResult:
        self._ensure_details_loaded()
        levels = self._levels_by_song_id.get(result.song_id)
        if levels is None:
            return result
        (
            spb_level,
            spn_level,
            sph_level,
            spa_level,
            spl_level,
            dpb_level,
            dpn_level,
            dph_level,
            dpa_level,
            dpl_level,
        ) = levels
        return replace(
            result,
            spb_level=spb_level,
            spn_level=spn_level,
            sph_level=sph_level,
            spa_level=spa_level,
            spl_level=spl_level,
            dpb_level=dpb_level,
            dpn_level=dpn_level,
            dph_level=dph_level,
            dpa_level=dpa_level,
            dpl_level=dpl_level,
        )

    def ensure_genre(self, result: SearchResult) -> SearchResult:
        self._ensure_details_loaded()
        if result.genre:
            return result
        return replace(result, genre=self._genre_by_song_id.get(result.song_id, ""))
