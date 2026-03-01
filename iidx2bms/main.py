import sys
import ctypes
import tempfile
from datetime import date
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from ctypes import wintypes

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPalette
from PyQt6.QtWidgets import QApplication

from conversion.conversion import cleanup_temp_workdirs


if sys.platform == "win32":
    _dwmapi = ctypes.windll.dwmapi

BUILD_VERSION_SUFFIX = 0


def _accent_selection_rgba() -> str:
    if sys.platform == "win32":
        try:
            color_ref = wintypes.DWORD()
            opaque = wintypes.BOOL()
            result = _dwmapi.DwmGetColorizationColor(ctypes.byref(color_ref), ctypes.byref(opaque))
            if result == 0:
                argb = int(color_ref.value)
                red = (argb >> 16) & 0xFF
                green = (argb >> 8) & 0xFF
                blue = argb & 0xFF
                return f"rgba({red}, {green}, {blue}, 70)"
        except Exception:
            pass

    highlight = QGuiApplication.palette().color(QPalette.ColorRole.Highlight)
    if not isinstance(highlight, QColor) or not highlight.isValid():
        return "rgba(38, 42, 50, 150)"
    return f"rgba({highlight.red()}, {highlight.green()}, {highlight.blue()}, 70)"


def _history_selected_border_color() -> str:
    highlight = QGuiApplication.palette().color(QPalette.ColorRole.Highlight)
    if not isinstance(highlight, QColor) or not highlight.isValid():
        return "#8ea4c0"
    return highlight.lighter(118).name()


def _build_app_version() -> str:
    if getattr(sys, "frozen", False):
        try:
            build_dt = datetime.fromtimestamp(Path(sys.executable).stat().st_mtime)
            build_date = build_dt.date()
            return f"{build_date.year}.{build_date.month}{build_date.day:02d}.{int(BUILD_VERSION_SUFFIX)}"
        except Exception:
            pass
    today = date.today()
    return f"{today.year}.{today.month}{today.day:02d}.{int(BUILD_VERSION_SUFFIX)}"


def _write_runtime_svg_icon(file_name: str, svg_bytes: bytes) -> Path:
    assets_dir = Path(tempfile.gettempdir()) / "iidx2bms_runtime_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    icon_path = assets_dir / file_name
    if not icon_path.exists() or icon_path.read_bytes() != svg_bytes:
        icon_path.write_bytes(svg_bytes)
    return icon_path


def main() -> None:
    cleanup_temp_workdirs()
    version = _build_app_version()
    from gui.gui import (
        CHECKBOX_CHECK_ICON_SVG,
        InstantTooltipStyle,
        SCROLL_DOWN_ICON_SVG,
        SCROLL_UP_ICON_SVG,
        MainWindow,
        STYLESHEET,
    )

    app = QApplication(sys.argv)
    app.setApplicationVersion(version)
    app.setStyle(InstantTooltipStyle("Fusion"))
    app.setEffectEnabled(Qt.UIEffect.UI_FadeTooltip, False)
    app.setEffectEnabled(Qt.UIEffect.UI_AnimateTooltip, False)

    font = QFont("Segoe UI")
    font.setPointSizeF(9.0)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    app_icon = QIcon(str((Path(__file__).resolve().parent / "icon" / "iidx2bms_logo.ico")))
    scroll_up_icon = quote(
        _write_runtime_svg_icon("scroll_up.svg", SCROLL_UP_ICON_SVG).as_posix(),
        safe="/:",
    )
    scroll_down_icon = quote(
        _write_runtime_svg_icon("scroll_down.svg", SCROLL_DOWN_ICON_SVG).as_posix(),
        safe="/:",
    )
    check_icon = quote(
        _write_runtime_svg_icon("check.svg", CHECKBOX_CHECK_ICON_SVG).as_posix(),
        safe="/:",
    )
    accent_bg = _accent_selection_rgba()
    history_selected_border = _history_selected_border_color()

    app.setStyleSheet(
        STYLESHEET.replace("__SCROLL_UP_ICON__", scroll_up_icon)
        .replace("__SCROLL_DOWN_ICON__", scroll_down_icon)
        .replace("__CHECK_ICON__", check_icon)
        .replace("__ACCENT_BG__", accent_bg)
        .replace("__HISTORY_SELECTED_BORDER__", history_selected_border)
    )

    app.setWindowIcon(app_icon)
    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    try:
        exit_code = app.exec()
    finally:
        cleanup_temp_workdirs()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
