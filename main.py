import sys
import ctypes
from pathlib import Path
from urllib.parse import quote
from ctypes import wintypes

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QPalette
from PyQt6.QtWidgets import QApplication

from gui.gui import InstantTooltipStyle, MainWindow, STYLESHEET


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


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle(InstantTooltipStyle("Fusion"))
    app.setEffectEnabled(Qt.UIEffect.UI_FadeTooltip, False)
    app.setEffectEnabled(Qt.UIEffect.UI_AnimateTooltip, False)

    font = QFont("Segoe UI")
    font.setPointSizeF(9.0)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    assets_dir = Path(__file__).resolve().parent / "gui" / "assets"
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

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
