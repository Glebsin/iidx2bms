from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


@dataclass(slots=True)
class ConversionHistoryUi:
    page: QWidget
    previous_conversions: QListWidget
    conversion_details: QListWidget
    clear_history_button: QPushButton
    add_to_selected_button: QPushButton


@dataclass(slots=True)
class ChartHistoryEntry:
    song_id_display: str
    artist: str
    title: str
    genre: str
    game_name: str
    status: str
    spb_level: int = 0
    spn_level: int = 0
    sph_level: int = 0
    spa_level: int = 0
    spl_level: int = 0
    dpb_level: int = 0
    dpn_level: int = 0
    dph_level: int = 0
    dpa_level: int = 0
    dpl_level: int = 0


@dataclass(slots=True)
class ConversionHistoryRun:
    run_id: str
    timestamp: str
    success_count: int
    failed_count: int
    charts: list[ChartHistoryEntry]

    @property
    def total_count(self) -> int:
        return len(self.charts)

    def summary_text(self) -> str:
        return (
            f"{self.timestamp}  "
            f"Success: {self.success_count}  "
            f"Failed: {self.failed_count}  "
            f"Total: {self.total_count}"
        )


class ConversionHistoryStore:
    def __init__(self) -> None:
        self._path = self._resolve_history_path()

    @staticmethod
    def _resolve_history_path() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / "history.json"
        return Path(sys.argv[0]).resolve().parent / "history.json"

    @property
    def path(self) -> Path:
        return self._path

    def load_runs(self) -> list[ConversionHistoryRun]:
        if not self._path.is_file():
            return []
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return []
        raw_runs = payload.get("runs", [])
        if not isinstance(raw_runs, list):
            return []
        runs: list[ConversionHistoryRun] = []
        for raw_run in raw_runs:
            run = _parse_run(raw_run)
            if run is not None:
                runs.append(run)
        return runs

    def save_runs(self, runs: list[ConversionHistoryRun]) -> None:
        payload = {
            "version": 1,
            "runs": [_serialize_run(run) for run in runs],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append_run(self, run: ConversionHistoryRun) -> list[ConversionHistoryRun]:
        runs = self.load_runs()
        runs.insert(0, run)
        self.save_runs(runs)
        return runs


class ConversionSessionRecorder:
    def __init__(self, store: ConversionHistoryStore) -> None:
        self._store = store
        self._entries: dict[str, ChartHistoryEntry] = {}

    def start(self, charts: list[object]) -> None:
        self._entries.clear()
        for chart in charts:
            song_id_display = str(getattr(chart, "song_id_display", "")).strip()
            if not song_id_display:
                continue
            self._entries[song_id_display] = ChartHistoryEntry(
                song_id_display=song_id_display,
                artist=str(getattr(chart, "artist", "") or ""),
                title=str(getattr(chart, "title", "") or ""),
                genre=str(getattr(chart, "genre", "") or ""),
                game_name=str(getattr(chart, "game_name", "") or ""),
                status="pending",
                spb_level=int(getattr(chart, "spb_level", 0) or 0),
                spn_level=int(getattr(chart, "spn_level", 0) or 0),
                sph_level=int(getattr(chart, "sph_level", 0) or 0),
                spa_level=int(getattr(chart, "spa_level", 0) or 0),
                spl_level=int(getattr(chart, "spl_level", 0) or 0),
                dpb_level=int(getattr(chart, "dpb_level", 0) or 0),
                dpn_level=int(getattr(chart, "dpn_level", 0) or 0),
                dph_level=int(getattr(chart, "dph_level", 0) or 0),
                dpa_level=int(getattr(chart, "dpa_level", 0) or 0),
                dpl_level=int(getattr(chart, "dpl_level", 0) or 0),
            )

    def mark_success(self, song_id_display: str) -> None:
        entry = self._entries.get(song_id_display)
        if entry is not None:
            entry.status = "success"

    def mark_failed(self, song_id_display: str) -> None:
        entry = self._entries.get(song_id_display)
        if entry is not None:
            entry.status = "failed"

    def set_chart_level(self, song_id_display: str, field_name: str, value: int) -> None:
        entry = self._entries.get(song_id_display)
        if entry is None or not hasattr(entry, field_name):
            return
        try:
            normalized = int(value)
        except Exception:
            normalized = 0
        setattr(entry, field_name, max(0, normalized))

    def has_active_session(self) -> bool:
        return bool(self._entries)

    def finalize(self) -> list[ConversionHistoryRun]:
        if not self._entries:
            return self._store.load_runs()
        charts: list[ChartHistoryEntry] = []
        success_count = 0
        failed_count = 0
        for song_id in sorted(self._entries.keys()):
            entry = self._entries[song_id]
            if entry.status not in {"success", "failed"}:
                entry.status = "failed"
            if entry.status == "success":
                success_count += 1
            else:
                failed_count += 1
            charts.append(
                ChartHistoryEntry(
                    song_id_display=entry.song_id_display,
                    artist=entry.artist,
                    title=entry.title,
                    genre=entry.genre,
                    game_name=entry.game_name,
                    status=entry.status,
                    spb_level=entry.spb_level,
                    spn_level=entry.spn_level,
                    sph_level=entry.sph_level,
                    spa_level=entry.spa_level,
                    spl_level=entry.spl_level,
                    dpb_level=entry.dpb_level,
                    dpn_level=entry.dpn_level,
                    dph_level=entry.dph_level,
                    dpa_level=entry.dpa_level,
                    dpl_level=entry.dpl_level,
                )
            )
        run = ConversionHistoryRun(
            run_id=uuid4().hex,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            success_count=success_count,
            failed_count=failed_count,
            charts=charts,
        )
        self._entries.clear()
        return self._store.append_run(run)

    def clear(self) -> None:
        self._entries.clear()


def _build_history_panel(
    title: str,
    action_text: str | None = None,
) -> tuple[QFrame, QVBoxLayout, QPushButton | None]:
    panel = QFrame()
    panel.setObjectName("ChartPanel")
    panel.setMinimumWidth(0)
    panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    panel_layout = QVBoxLayout(panel)
    panel_layout.setContentsMargins(0, 0, 0, 0)
    panel_layout.setSpacing(0)

    header_wrap = QWidget()
    header_layout = QHBoxLayout(header_wrap)
    header_layout.setContentsMargins(16, 7, 8 if action_text else 18, 7)
    header_layout.setSpacing(0)
    header_wrap.setFixedHeight(42)

    title_label = QLabel(title)
    title_label.setObjectName("PanelTitle")
    header_layout.addWidget(title_label)
    header_layout.addStretch(1)
    action_button: QPushButton | None = None
    if action_text:
        action_button = QPushButton(action_text)
        action_button.setObjectName("PanelActionButton")
        action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        action_width = action_button.fontMetrics().horizontalAdvance(action_text) + 16
        action_button.setFixedSize(action_width, 22)
        header_layout.addWidget(action_button, 0, Qt.AlignmentFlag.AlignVCenter)

    header_line = QFrame()
    header_line.setObjectName("PanelHeaderLine")

    body = QFrame()
    body.setObjectName("PanelBody")
    body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(8, 8, 8, 8)
    body_layout.setSpacing(0)

    panel_layout.addWidget(header_wrap)
    panel_layout.addWidget(header_line)
    panel_layout.addWidget(body, 1)
    return panel, body_layout, action_button


def build_conversion_history_page(
    list_widget_cls: type[QListWidget],
) -> ConversionHistoryUi:
    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)
    page_layout.setSpacing(0)

    panels_row = QWidget()
    panels_layout = QHBoxLayout(panels_row)
    panels_layout.setContentsMargins(0, 0, 0, 0)
    panels_layout.setSpacing(2)

    previous_panel, previous_body_layout, clear_history_button = _build_history_panel(
        "Previous Conversions",
        action_text="Clear history",
    )
    previous_list = list_widget_cls()
    previous_list.setObjectName("HistoryRunsList")
    previous_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    previous_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    previous_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    previous_list.setWordWrap(True)
    previous_list.setUniformItemSizes(False)
    previous_body_layout.addWidget(previous_list, 1)

    details_panel, details_body_layout, add_to_selected_button = _build_history_panel(
        "Conversion Details",
        action_text="Add to Selected charts",
    )
    details_text = list_widget_cls()
    details_text.setObjectName("HistoryDetailsList")
    details_text.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    details_text.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    details_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    details_text.setWordWrap(True)
    details_text.setUniformItemSizes(False)
    details_text.setSpacing(0)
    details_body_layout.addWidget(details_text, 1)

    panels_layout.addWidget(previous_panel, 1)
    panels_layout.addWidget(details_panel, 1)
    page_layout.addWidget(panels_row, 1)

    if clear_history_button is None:
        raise RuntimeError("Failed to build clear history button")
    if add_to_selected_button is None:
        raise RuntimeError("Failed to build add to selected charts button")
    return ConversionHistoryUi(
        page=page,
        previous_conversions=previous_list,
        conversion_details=details_text,
        clear_history_button=clear_history_button,
        add_to_selected_button=add_to_selected_button,
    )


def render_runs_list(widget: QListWidget, runs: list[ConversionHistoryRun]) -> None:
    widget.clear()
    total = len(runs)
    for idx, run in enumerate(runs):
        row = QListWidgetItem()
        row.setData(Qt.ItemDataRole.UserRole, run.run_id)
        row_widget = _build_run_row_widget(run)
        row_widget.ensurePolished()
        bottom_gap = 1 if idx < (total - 1) else 0
        row_height = max(62, row_widget.sizeHint().height() + 4)
        row_widget.setFixedHeight(row_height)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, bottom_gap)
        container_layout.setSpacing(0)
        container_layout.addWidget(row_widget)
        container.setMinimumHeight(row_height + bottom_gap)

        row.setSizeHint(QSize(0, row_height + bottom_gap))
        widget.addItem(row)
        widget.setItemWidget(row, container)


def render_run_details(widget: QListWidget, run: ConversionHistoryRun | None) -> None:
    widget.clear()
    if run is None:
        return
    total = len(run.charts)
    for idx, entry in enumerate(run.charts):
        item = QListWidgetItem()
        row_widget = _build_chart_row_widget(entry)
        row_widget.ensurePolished()
        # Keep real 1px gap between cards without clipping card borders.
        bottom_gap = 1 if idx < (total - 1) else 0
        row_height = max(62, row_widget.sizeHint().height() + 4)
        row_widget.setFixedHeight(row_height)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, bottom_gap)
        container_layout.setSpacing(0)
        container_layout.addWidget(row_widget)
        container.setMinimumHeight(row_height + bottom_gap)

        item.setSizeHint(QSize(0, row_height + bottom_gap))
        widget.addItem(item)
        widget.setItemWidget(item, container)


def find_run_by_id(runs: list[ConversionHistoryRun], run_id: str) -> ConversionHistoryRun | None:
    for run in runs:
        if run.run_id == run_id:
            return run
    return None


def _parse_run(payload: object) -> ConversionHistoryRun | None:
    if not isinstance(payload, dict):
        return None
    run_id = str(payload.get("run_id", "")).strip() or uuid4().hex
    timestamp = str(payload.get("timestamp", "")).strip()
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success_count = int(payload.get("success_count", 0) or 0)
    failed_count = int(payload.get("failed_count", 0) or 0)
    raw_charts = payload.get("charts", [])
    charts: list[ChartHistoryEntry] = []
    if isinstance(raw_charts, list):
        for raw_chart in raw_charts:
            if not isinstance(raw_chart, dict):
                continue
            status = str(raw_chart.get("status", "failed")).lower()
            if status not in {"success", "failed"}:
                status = "failed"
            charts.append(
                ChartHistoryEntry(
                    song_id_display=str(raw_chart.get("song_id_display", "")).strip(),
                    artist=str(raw_chart.get("artist", "") or ""),
                    title=str(raw_chart.get("title", "") or ""),
                    genre=str(raw_chart.get("genre", "") or ""),
                    game_name=str(raw_chart.get("game_name", "") or ""),
                    status=status,
                    spb_level=int(raw_chart.get("spb_level", 0) or 0),
                    spn_level=int(raw_chart.get("spn_level", 0) or 0),
                    sph_level=int(raw_chart.get("sph_level", 0) or 0),
                    spa_level=int(raw_chart.get("spa_level", 0) or 0),
                    spl_level=int(raw_chart.get("spl_level", 0) or 0),
                    dpb_level=int(raw_chart.get("dpb_level", 0) or 0),
                    dpn_level=int(raw_chart.get("dpn_level", 0) or 0),
                    dph_level=int(raw_chart.get("dph_level", 0) or 0),
                    dpa_level=int(raw_chart.get("dpa_level", 0) or 0),
                    dpl_level=int(raw_chart.get("dpl_level", 0) or 0),
                )
            )
    if not charts:
        return None
    if success_count <= 0 and failed_count <= 0:
        success_count = sum(1 for chart in charts if chart.status == "success")
        failed_count = sum(1 for chart in charts if chart.status == "failed")
    return ConversionHistoryRun(
        run_id=run_id,
        timestamp=timestamp,
        success_count=success_count,
        failed_count=failed_count,
        charts=charts,
    )


def _serialize_run(run: ConversionHistoryRun) -> dict[str, object]:
    return {
        "run_id": run.run_id,
        "timestamp": run.timestamp,
        "success_count": run.success_count,
        "failed_count": run.failed_count,
        "charts": [
            {
                "song_id_display": entry.song_id_display,
                "artist": entry.artist,
                "title": entry.title,
                "genre": entry.genre,
                "game_name": entry.game_name,
                "status": entry.status,
                "spb_level": entry.spb_level,
                "spn_level": entry.spn_level,
                "sph_level": entry.sph_level,
                "spa_level": entry.spa_level,
                "spl_level": entry.spl_level,
                "dpb_level": entry.dpb_level,
                "dpn_level": entry.dpn_level,
                "dph_level": entry.dph_level,
                "dpa_level": entry.dpa_level,
                "dpl_level": entry.dpl_level,
            }
            for entry in run.charts
        ],
    }


def _build_run_row_widget(run: ConversionHistoryRun) -> QWidget:
    row = QFrame()
    row.setObjectName("SelectedChartItem")
    row.setProperty("historyRun", True)
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(8, 6, 8, 6)
    row_layout.setSpacing(8)

    left_column = QWidget()
    left_layout = QVBoxLayout(left_column)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(0)

    primary_label = QLabel(run.timestamp)
    primary_label.setObjectName("SelectedChartPrimary")
    primary_label.setWordWrap(False)
    left_layout.addWidget(primary_label)

    secondary_label = QLabel(
        f"Success: {run.success_count}  Failed: {run.failed_count}  Total: {run.total_count}"
    )
    secondary_label.setObjectName("SelectedChartSecondary")
    secondary_label.setWordWrap(False)
    left_layout.addWidget(secondary_label)

    row_layout.addWidget(left_column, 1)

    right_column = QWidget()
    right_layout = QVBoxLayout(right_column)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(2)

    success_badge = QLabel(
        f'<span style="color:#dcdcdc;">OK:</span> '
        f'<span style="color:#40c977;">{run.success_count}</span>'
    )
    success_badge.setObjectName("SelectedChartLevels")
    success_badge.setTextFormat(Qt.TextFormat.RichText)
    success_badge.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    right_layout.addWidget(success_badge, 0, Qt.AlignmentFlag.AlignRight)

    failed_badge = QLabel(
        f'<span style="color:#dcdcdc;">FAIL:</span> '
        f'<span style="color:#be0420;">{run.failed_count}</span>'
    )
    failed_badge.setObjectName("SelectedChartLevels")
    failed_badge.setTextFormat(Qt.TextFormat.RichText)
    failed_badge.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    right_layout.addWidget(failed_badge, 0, Qt.AlignmentFlag.AlignRight)

    row_layout.addWidget(right_column, 0)
    return row


def _build_chart_row_widget(entry: ChartHistoryEntry) -> QWidget:
    row = QFrame()
    row.setObjectName("SelectedChartItem")
    row.setProperty("historyStatus", "success" if entry.status == "success" else "failed")
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(8, 6, 8, 6)
    row_layout.setSpacing(8)

    left_column = QWidget()
    left_layout = QVBoxLayout(left_column)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(0)

    title_text = f"ID: {entry.song_id_display}  {entry.artist} - {entry.title}"
    primary_label = QLabel(title_text)
    primary_label.setObjectName("SelectedChartPrimary")
    primary_label.setWordWrap(False)
    left_layout.addWidget(primary_label)

    secondary_label = QLabel(f"Genre: {entry.genre}  Game: {entry.game_name}")
    secondary_label.setObjectName("SelectedChartSecondary")
    secondary_label.setWordWrap(False)
    left_layout.addWidget(secondary_label)

    row_layout.addWidget(left_column, 1)
    row_layout.addWidget(_build_levels_column(entry), 0)
    return row


def _format_level_line(
    prefix: str,
    b_level: int,
    n_level: int,
    h_level: int,
    a_level: int,
    l_level: int,
) -> str:
    chunks: list[str] = []
    if b_level > 0:
        chunks.append(f'<span style="color:#00e37f;">{b_level}</span>')
    if n_level > 0:
        chunks.append(f'<span style="color:#00a4ff;">{n_level}</span>')
    if h_level > 0:
        chunks.append(f'<span style="color:#c0840c;">{h_level}</span>')
    if a_level > 0:
        chunks.append(f'<span style="color:#be0420;">{a_level}</span>')
    if l_level > 0:
        chunks.append(f'<span style="color:#7900ff;">{l_level}</span>')
    return f'<span style="color:#dcdcdc;">{prefix}:</span> ' + " ".join(chunks)


def _build_levels_column(entry: ChartHistoryEntry) -> QWidget:
    levels_column = QWidget()
    levels_layout = QVBoxLayout(levels_column)
    levels_layout.setContentsMargins(0, 0, 0, 0)
    levels_layout.setSpacing(2)

    sp_label = QLabel(
        _format_level_line(
            "SP",
            entry.spb_level,
            entry.spn_level,
            entry.sph_level,
            entry.spa_level,
            entry.spl_level,
        )
    )
    sp_label.setObjectName("SelectedChartLevels")
    sp_label.setTextFormat(Qt.TextFormat.RichText)
    sp_label.setWordWrap(False)
    sp_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    sp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    levels_layout.addWidget(sp_label, 0, Qt.AlignmentFlag.AlignRight)

    dp_label = QLabel(
        _format_level_line(
            "DP",
            entry.dpb_level,
            entry.dpn_level,
            entry.dph_level,
            entry.dpa_level,
            entry.dpl_level,
        )
    )
    dp_label.setObjectName("SelectedChartLevels")
    dp_label.setTextFormat(Qt.TextFormat.RichText)
    dp_label.setWordWrap(False)
    dp_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    dp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    levels_layout.addWidget(dp_label, 0, Qt.AlignmentFlag.AlignRight)

    return levels_column
