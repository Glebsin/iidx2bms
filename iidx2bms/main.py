import sys
import ctypes
import os
from datetime import date
from pathlib import Path
from urllib.parse import quote
from ctypes import wintypes

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPalette
from PyQt6.QtWidgets import QApplication

from conversion.conversion import cleanup_temp_workdirs


if sys.platform == "win32":
    _dwmapi = ctypes.windll.dwmapi


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


def _build_app_version() -> str:
    today = date.today()
    return f"{today.year}.{today.month}{today.day:02d}.0"


def main() -> None:
    cleanup_temp_workdirs()
    version = os.environ.get("IIDX2BMS_VERSION", "").strip() or _build_app_version()
    os.environ["IIDX2BMS_VERSION"] = version
    from gui.gui import InstantTooltipStyle, MainWindow, STYLESHEET

    app = QApplication(sys.argv)
    app.setApplicationVersion(version)
    app.setStyle(InstantTooltipStyle("Fusion"))
    app.setEffectEnabled(Qt.UIEffect.UI_FadeTooltip, False)
    app.setEffectEnabled(Qt.UIEffect.UI_AnimateTooltip, False)

    font = QFont("Segoe UI")
    font.setPointSizeF(9.0)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    assets_dir = Path(__file__).resolve().parent / "gui" / "assets"
    app_icon = QIcon(str((Path(__file__).resolve().parent / "icon" / "iidx2bms_logo.ico")))
    scroll_up_icon = quote((assets_dir / "scroll_up.svg").as_posix(), safe="/:")
    scroll_down_icon = quote((assets_dir / "scroll_down.svg").as_posix(), safe="/:")
    check_icon = quote((assets_dir / "check.svg").as_posix(), safe="/:")
    accent_bg = _accent_selection_rgba()

    app.setStyleSheet(
        STYLESHEET.replace("__SCROLL_UP_ICON__", scroll_up_icon)
        .replace("__SCROLL_DOWN_ICON__", scroll_down_icon)
        .replace("__CHECK_ICON__", check_icon)
        .replace("__ACCENT_BG__", accent_bg)
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
