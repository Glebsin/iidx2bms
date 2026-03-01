from __future__ import annotations

from PyQt6.QtCore import QByteArray, QSettings, Qt
from PyQt6.QtWidgets import QWidget


def restore_window_placement(window: QWidget, settings: QSettings) -> None:
    geometry = settings.value("ui/window_geometry")
    geometry_bytes: QByteArray | None = None
    if isinstance(geometry, QByteArray):
        geometry_bytes = geometry
    elif isinstance(geometry, (bytes, bytearray)):
        geometry_bytes = QByteArray(bytes(geometry))
    if geometry_bytes is not None and not geometry_bytes.isEmpty():
        window.restoreGeometry(geometry_bytes)

    state_raw = settings.value("ui/window_state_flags", 0)
    try:
        state_flags = int(state_raw)
    except Exception:
        state_flags = 0

    try:
        maximized_flag = int(Qt.WindowState.WindowMaximized.value)
        fullscreen_flag = int(Qt.WindowState.WindowFullScreen.value)
    except Exception:
        maximized_flag = 0x2
        fullscreen_flag = 0x4

    maximized = bool(state_flags & maximized_flag)
    fullscreen = bool(state_flags & fullscreen_flag)
    if fullscreen:
        window.showFullScreen()
    elif maximized:
        window.showMaximized()


def save_window_placement(window: QWidget, settings: QSettings) -> None:
    settings.setValue("ui/window_geometry", window.saveGeometry())
    state = window.windowState()
    try:
        state_flags = int(state.value)
    except Exception:
        # Fallback for enum implementations without `.value`.
        state_flags = int(state) if isinstance(state, int) else 0
    settings.setValue("ui/window_state_flags", state_flags)
    settings.sync()
