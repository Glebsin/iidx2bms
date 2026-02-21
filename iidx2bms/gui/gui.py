import sys
import ctypes
import os
import re
import html
from dataclasses import replace
from pathlib import Path
from ctypes import wintypes
from PyQt6.QtCore import (
    QByteArray,
    QElapsedTimer,
    QEvent,
    QObject,
    QPoint,
    QRunnable,
    QSize,
    QThreadPool,
    QTimer,
    Qt,
    QSettings,
    pyqtSignal,
)
from PyQt6.QtGui import QCursor, QDesktopServices, QGuiApplication, QIcon, QPainter, QPixmap, QColor, QTextCursor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QDialog,
    QPushButton,
    QProxyStyle,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QTextEdit,
    QToolTip,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from search_engine.search_engine import SearchEngine, SearchResult
from conversion.conversion import convert_chart
from PyQt6.QtCore import QUrl


SEARCH_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#9a9a9a" d="M480 272C480 317.9 465.1 360.3 440 394.7L566.6 521.4C579.1 533.9 579.1 554.2 566.6 566.7C554.1 579.2 533.8 579.2 521.3 566.7L394.7 440C360.3 465.1 317.9 480 272 480C157.1 480 64 386.9 64 272C64 157.1 157.1 64 272 64C386.9 64 480 157.1 480 272zM272 416C351.5 416 416 351.5 416 272C416 192.5 351.5 128 272 128C192.5 128 128 192.5 128 272C128 351.5 192.5 416 272 416z"/></svg>'
CLEAR_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#be0420" d="M183.1 137.4C170.6 124.9 150.3 124.9 137.8 137.4C125.3 149.9 125.3 170.2 137.8 182.7L275.2 320L137.9 457.4C125.4 469.9 125.4 490.2 137.9 502.7C150.4 515.2 170.7 515.2 183.2 502.7L320.5 365.3L457.9 502.6C470.4 515.1 490.7 515.1 503.2 502.6C515.7 490.1 515.7 469.8 503.2 457.3L365.8 320L503.1 182.6C515.6 170.1 515.6 149.8 503.1 137.3C490.6 124.8 470.3 124.8 457.8 137.3L320.5 274.7L183.1 137.4z"/></svg>'
TRASH_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="#d66b6b" d="M136.7 5.9C141.1-7.2 153.3-16 167.1-16l113.9 0c13.8 0 26 8.8 30.4 21.9L320 32 416 32c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 96C14.3 96 0 81.7 0 64S14.3 32 32 32l96 0 8.7-26.1zM32 144l384 0 0 304c0 35.3-28.7 64-64 64L96 512c-35.3 0-64-28.7-64-64l0-304zm88 64c-13.3 0-24 10.7-24 24l0 192c0 13.3 10.7 24 24 24s24-10.7 24-24l0-192c0-13.3-10.7-24-24-24zm104 0c-13.3 0-24 10.7-24 24l0 192c0 13.3 10.7 24 24 24s24-10.7 24-24l0-192c0-13.3-10.7-24-24-24zm104 0c-13.3 0-24 10.7-24 24l0 192c0 13.3 10.7 24 24 24s24-10.7 24-24l0-192c0-13.3-10.7-24-24-24z"/></svg>'
CHECK_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="#cfcfcf" d="M434.8 70.1c14.3 10.4 17.5 30.4 7.1 44.7l-256 352c-5.5 7.6-14 12.3-23.4 13.1s-18.5-2.7-25.1-9.3l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l101.5 101.5 234-321.7c10.4-14.3 30.4-17.5 44.7-7.1z"/></svg>'
CHECK_GREEN_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="#00e37f" d="M434.8 70.1c14.3 10.4 17.5 30.4 7.1 44.7l-256 352c-5.5 7.6-14 12.3-23.4 13.1s-18.5-2.7-25.1-9.3l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l101.5 101.5 234-321.7c10.4-14.3 30.4-17.5 44.7-7.1z"/></svg>'
RESET_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#f0f0f0" d="M320 128C263.2 128 212.1 152.7 176.9 192L224 192C241.7 192 256 206.3 256 224C256 241.7 241.7 256 224 256L96 256C78.3 256 64 241.7 64 224L64 96C64 78.3 78.3 64 96 64C113.7 64 128 78.3 128 96L128 150.7C174.9 97.6 243.5 64 320 64C461.4 64 576 178.6 576 320C576 461.4 461.4 576 320 576C233 576 156.1 532.6 109.9 466.3C99.8 451.8 103.3 431.9 117.8 421.7C132.3 411.5 152.2 415.1 162.4 429.6C197.2 479.4 254.8 511.9 320 511.9C426 511.9 512 425.9 512 319.9C512 213.9 426 128 320 128z"/></svg>'

if sys.platform == "win32":
    class _POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class _RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class _CANDIDATEFORM(ctypes.Structure):
        _fields_ = [
            ("dwIndex", wintypes.DWORD),
            ("dwStyle", wintypes.DWORD),
            ("ptCurrentPos", _POINT),
            ("rcArea", _RECT),
        ]

    class _COMPOSITIONFORM(ctypes.Structure):
        _fields_ = [
            ("dwStyle", wintypes.DWORD),
            ("ptCurrentPos", _POINT),
            ("rcArea", _RECT),
        ]

    _CFS_POINT = 0x0002
    _CFS_CANDIDATEPOS = 0x0040
    _imm32 = ctypes.windll.imm32
    _user32 = ctypes.windll.user32
    _dwmapi = ctypes.windll.dwmapi


STYLESHEET = """
QMainWindow {
    background: #1e1e1e;
}
QWidget#Root {
    background: #1e1e1e;
    color: #e6e6e6;
}
QWidget#TopBar {
    background: #1e1e1e;
}
QFrame#TopSeparator {
    background: #3c3c3c;
    border: none;
    min-height: 1px;
    max-height: 1px;
}
QWidget#ContentArea {
    background: #1e1e1e;
}
QToolTip {
    background: #2d2d2d;
    border: 1px solid #7a7a7a;
    border-radius: 4px;
    color: #f0f0f0;
    padding: 2px 4px;
}
QToolButton#MiniButton {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 22px;
    max-height: 22px;
    padding: 0 6px;
    text-align: center;
}
QToolButton#MiniButton:hover {
    background: #333333;
}
QToolButton#MiniButton:pressed {
    background: #383838;
}
QToolButton#MiniButton[activePage="true"] {
    background: #383838;
    border-color: #4a4a4a;
}
QFrame#ChartPanel {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 8px;
}
QFrame#ChartPanel[attention="true"] {
    background: __ACCENT_BG__;
    border: 1px solid #4a4a4a;
    border-radius: 8px;
}
QLabel#PanelTitle {
    color: #f0f0f0;
    font-size: 12px;
    font-weight: 600;
}
QFrame#PanelHeaderLine {
    background: #3c3c3c;
    border: none;
    min-height: 1px;
    max-height: 1px;
}
QFrame#PanelBody {
    background: #2d2d2d;
    border: none;
    border-bottom-left-radius: 7px;
    border-bottom-right-radius: 7px;
}
QFrame#PanelBody[attention="true"] {
    background: __ACCENT_BG__;
    border: none;
    border-bottom-left-radius: 7px;
    border-bottom-right-radius: 7px;
}
QPushButton#PanelActionButton {
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 22px;
    max-height: 22px;
    padding: 0 6px;
    text-align: center;
}
QPushButton#PanelActionButton:hover {
    background: #333333;
}
QPushButton#PanelActionButton:pressed {
    background: #383838;
}
QPushButton#PanelActionButton:disabled {
    background: #242424;
    border: 1px solid #333333;
    color: #7a7a7a;
}
QPushButton#HeaderTextButton {
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 22px;
    max-height: 22px;
    margin-top: 1px;
    padding: 0 8px;
    text-align: center;
}
QPushButton#HeaderTextButton:hover {
    background: #333333;
}
QPushButton#HeaderTextButton:pressed {
    background: #383838;
}
QPushButton#HeaderIconButton {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
    padding: 0px;
}
QPushButton#HeaderIconButton:hover {
    background: #333333;
}
QPushButton#HeaderIconButton:pressed {
    background: #383838;
}
QCheckBox#ConversionOptionCheck {
    color: #d7d7d7;
    spacing: 6px;
    background: transparent;
}
QCheckBox#ConversionOptionCheck[stagefile="true"] {
    padding-bottom: 1px;
}
QCheckBox#ConversionOptionCheck[stagefile="true"]::indicator {
    margin-bottom: 1px;
}
QCheckBox#ConversionOptionCheck::indicator {
    width: 13px;
    height: 13px;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    background: #1e1e1e;
}
QCheckBox#ConversionOptionCheck::indicator:checked {
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    background: #1e1e1e;
    image: url("__CHECK_ICON__");
}
QFrame#MiniPopup {
    background: transparent;
    border: none;
}
QFrame#MiniPopupSurface {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 8px;
}
QFrame#MiniPopupSeparator {
    background: #3c3c3c;
    border: none;
}
QPushButton#MiniPopupItem {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #f0f0f0;
    min-height: 24px;
    max-height: 24px;
    padding: 0 6px 0 6px;
    text-align: left;
}
QPushButton#MiniPopupItem[hasCheck="true"] {
    padding: 0 22px 0 6px;
}
QPushButton#MiniPopupItem:hover {
    background: #3a3a3a;
}
QPushButton#MiniPopupItem[active="true"] {
    background: #343434;
}
QPushButton#MiniPopupItem[active="true"]:hover {
    background: #3a3a3a;
}
QPushButton#MiniPopupItem:pressed {
    background: #3a3a3a;
}
QFrame#SearchBox {
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    min-height: 32px;
    max-height: 32px;
}
QLabel#SearchIcon {
    border: none;
    background: transparent;
}
QPushButton#SearchClearButton {
    background: transparent;
    border: none;
    border-radius: 4px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0px;
}
QPushButton#SearchClearButton:hover {
    background: #2a2a2a;
}
QPushButton#SearchClearButton:pressed {
    background: #252525;
}
QLineEdit#SearchInput {
    background: transparent;
    border: none;
    color: #dcdcdc;
    selection-background-color: #3a3a3a;
    selection-color: #f0f0f0;
}
QLineEdit#SearchInput:focus {
    border: none;
}
QLineEdit#SearchInput::placeholder {
    color: #8f8f8f;
}
QListWidget#SearchResults {
    background: #1e1e1e;
    border: 1px solid #101010;
    border-radius: 4px;
    color: #f0f0f0;
    outline: none;
}
QTextEdit#ConversionLogs {
    background: #1e1e1e;
    border: 1px solid #101010;
    border-radius: 4px;
    outline: none;
    selection-background-color: __ACCENT_BG__;
    selection-color: #f0f0f0;
}
QListWidget#SearchResults::item {
    border: none;
    padding: 0px;
}
QListWidget#SearchResults::item:selected {
    background: transparent;
}
QFrame#SearchChartItem {
    background: transparent;
    border: none;
    border-radius: 4px;
}
QFrame#SearchChartItem[selected="true"] {
    background: __ACCENT_BG__;
}
QLabel#SearchChartPrimary {
    color: #f0f0f0;
}
QLabel#SearchChartSecondary {
    color: #f0f0f0;
}
QLabel#SearchChartLevels {
    color: #dcdcdc;
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    padding: 0 4px;
}
QListWidget#SelectedResults {
    background: #1e1e1e;
    border: 1px solid #101010;
    border-radius: 4px;
    color: #f0f0f0;
    outline: none;
}
QListWidget#SelectedResults::item {
    border: none;
    padding: 0px;
}
QFrame#SelectedChartItem {
    background: #1e1e1e;
    border: none;
    border-radius: 4px;
}
QFrame#SelectedChartItem[selected="true"] {
    background: __ACCENT_BG__;
}
QFrame#SelectedChartItem[matched="true"] {
    background: __ACCENT_BG__;
}
QLabel#SelectedChartPrimary {
    color: #f0f0f0;
}
QLabel#SelectedChartSecondary {
    color: #f0f0f0;
}
QLabel#SelectedChartLevels {
    color: #dcdcdc;
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    padding: 0 4px;
}
QPushButton#TrashButton {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0px;
}
QPushButton#TrashButton:hover {
    background: #333333;
}
QPushButton#TrashButton:pressed {
    background: #383838;
}
QPushButton#SelectedResetButton {
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0px;
}
QPushButton#SelectedResetButton:hover {
    background: #2a2a2a;
}
QPushButton#SelectedResetButton:pressed {
    background: #252525;
}
QLineEdit#ChartEditInput {
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 20px;
    max-height: 20px;
    padding: 0 6px;
    selection-background-color: #3a3a3a;
    selection-color: #f0f0f0;
}
QLineEdit#ChartEditInput:focus {
    border: 1px solid #4d4d4d;
}
QLineEdit#ChartEditInput:disabled {
    background: #232323;
    border: 1px solid #363636;
    color: #9a9a9a;
}
QLabel#ChartEditPrefix {
    color: #dcdcdc;
}
QListWidget#SearchResults QScrollBar:vertical,
QListWidget#SelectedResults QScrollBar:vertical {
    background: #1f1f1f;
    width: 10px;
    margin: 12px 1px 12px 1px;
    border: none;
    border-radius: 5px;
}
QListWidget#SearchResults QScrollBar::handle:vertical,
QListWidget#SelectedResults QScrollBar::handle:vertical {
    background: #6a6a6a;
    min-height: 28px;
    border: none;
    border-radius: 4px;
    margin: 1px 0px;
}
QListWidget#SearchResults QScrollBar::handle:vertical:hover,
QListWidget#SelectedResults QScrollBar::handle:vertical:hover {
    background: #6a6a6a;
}
QListWidget#SearchResults QScrollBar::add-line:vertical,
QListWidget#SelectedResults QScrollBar::add-line:vertical,
QListWidget#SearchResults QScrollBar::sub-line:vertical,
QListWidget#SelectedResults QScrollBar::sub-line:vertical {
    background: transparent;
    border: none;
    height: 12px;
    width: 10px;
    subcontrol-origin: margin;
}
QListWidget#SearchResults QScrollBar::sub-line:vertical,
QListWidget#SelectedResults QScrollBar::sub-line:vertical {
    subcontrol-position: top;
}
QListWidget#SearchResults QScrollBar::add-line:vertical,
QListWidget#SelectedResults QScrollBar::add-line:vertical {
    subcontrol-position: bottom;
}
QListWidget#SearchResults QScrollBar::up-arrow:vertical,
QListWidget#SelectedResults QScrollBar::up-arrow:vertical {
    image: url("__SCROLL_UP_ICON__");
    width: 8px;
    height: 8px;
}
QListWidget#SearchResults QScrollBar::down-arrow:vertical,
QListWidget#SelectedResults QScrollBar::down-arrow:vertical {
    image: url("__SCROLL_DOWN_ICON__");
    width: 8px;
    height: 8px;
}
QListWidget#SearchResults QScrollBar::add-page:vertical,
QListWidget#SelectedResults QScrollBar::add-page:vertical,
QListWidget#SearchResults QScrollBar::sub-page:vertical,
QListWidget#SelectedResults QScrollBar::sub-page:vertical {
    background: transparent;
}
QFrame#ConfirmPopup {
    background: transparent;
    border: none;
}
QFrame#ConfirmSurface {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 8px;
}
QLabel#ConfirmMessage {
    color: #f0f0f0;
}
QPushButton#ConfirmButton {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 22px;
    max-height: 22px;
    padding: 0 8px;
}
QPushButton#ConfirmButton:hover {
    background: #333333;
}
QPushButton#ConfirmButton:pressed {
    background: #383838;
}
QFrame#HoverHint {
    background: #2d2d2d;
    border: 1px solid #7a7a7a;
    border-radius: 4px;
}
QLabel#HoverHintText {
    color: #f0f0f0;
    padding: 2px 4px;
}
QDialog#FilePathsDialog {
    background: #1e1e1e;
    border: none;
    border-radius: 8px;
}
QLabel#FilePathsLabel {
    color: #dcdcdc;
}
QLineEdit#FilePathsInput {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    color: #f0f0f0;
    min-height: 24px;
    padding: 0 6px;
}
QPushButton#FilePathsBrowseButton {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 24px;
    max-height: 24px;
    min-width: 32px;
    max-width: 32px;
}
QPushButton#FilePathsBrowseButton:hover {
    background: #333333;
}
QPushButton#FilePathsBrowseButton:pressed {
    background: #383838;
}
QPushButton#FilePathsDialogButton {
    background: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 24px;
    max-height: 24px;
    min-width: 72px;
    padding: 0 10px;
}
QPushButton#FilePathsDialogButton:hover {
    background: #333333;
}
QPushButton#FilePathsDialogButton:pressed {
    background: #383838;
}
"""


_OPEN_CONFIRM_POPUPS: list["ConfirmPopup"] = []


class InstantTooltipStyle(QProxyStyle):
    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QStyle.StyleHint.SH_ToolTip_WakeUpDelay:
            return 0
        return super().styleHint(hint, option, widget, returnData)


class ConfirmPopup(QFrame):
    def __init__(self, url: str) -> None:
        super().__init__(
            None,
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint,
        )
        self._url = url
        self.setObjectName("ConfirmPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        surface = QFrame()
        surface.setObjectName("ConfirmSurface")
        surface_layout = QVBoxLayout(surface)
        surface_layout.setContentsMargins(10, 10, 10, 10)
        surface_layout.setSpacing(8)

        message = QLabel(f"Do you want to open\n{url} ?")
        message.setObjectName("ConfirmMessage")
        message.setWordWrap(True)
        surface_layout.addWidget(message)

        buttons_row = QHBoxLayout()
        buttons_row.setContentsMargins(0, 0, 0, 0)
        buttons_row.setSpacing(6)
        buttons_row.addStretch(1)

        yes_button = QPushButton("Yes")
        yes_button.setObjectName("ConfirmButton")
        yes_button.clicked.connect(self._accept)
        no_button = QPushButton("No")
        no_button.setObjectName("ConfirmButton")
        no_button.clicked.connect(self.close)

        buttons_row.addWidget(yes_button)
        buttons_row.addWidget(no_button)
        surface_layout.addLayout(buttons_row)

        root_layout.addWidget(surface)
        self.setFixedWidth(320)
        self.adjustSize()

    def _accept(self) -> None:
        QDesktopServices.openUrl(QUrl(self._url))
        self.close()


class FilePathsDialog(QDialog):
    def __init__(
        self,
        sound_path: str,
        movie_path: str,
        results_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("FilePathsDialog")
        self.setWindowTitle("File paths")
        flags = (
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setModal(True)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(8)

        sound_row = QWidget()
        sound_row_layout = QHBoxLayout(sound_row)
        sound_row_layout.setContentsMargins(0, 0, 0, 0)
        sound_row_layout.setSpacing(8)
        sound_label = QLabel(r"\contents\data\sound")
        sound_label.setObjectName("FilePathsLabel")
        sound_label.setFixedWidth(140)
        self.sound_input = QLineEdit(sound_path)
        self.sound_input.setObjectName("FilePathsInput")
        sound_browse = QPushButton("...")
        sound_browse.setObjectName("FilePathsBrowseButton")
        sound_browse.clicked.connect(lambda: self._pick_folder(self.sound_input))
        sound_row_layout.addWidget(sound_label)
        sound_row_layout.addWidget(self.sound_input, 1)
        sound_row_layout.addWidget(sound_browse)

        movie_row = QWidget()
        movie_row_layout = QHBoxLayout(movie_row)
        movie_row_layout.setContentsMargins(0, 0, 0, 0)
        movie_row_layout.setSpacing(8)
        movie_label = QLabel(r"\contents\data\movie")
        movie_label.setObjectName("FilePathsLabel")
        movie_label.setFixedWidth(140)
        self.movie_input = QLineEdit(movie_path)
        self.movie_input.setObjectName("FilePathsInput")
        movie_browse = QPushButton("...")
        movie_browse.setObjectName("FilePathsBrowseButton")
        movie_browse.clicked.connect(lambda: self._pick_folder(self.movie_input))
        movie_row_layout.addWidget(movie_label)
        movie_row_layout.addWidget(self.movie_input, 1)
        movie_row_layout.addWidget(movie_browse)

        results_row = QWidget()
        results_row_layout = QHBoxLayout(results_row)
        results_row_layout.setContentsMargins(0, 0, 0, 0)
        results_row_layout.setSpacing(8)
        results_label = QLabel("Output folder")
        results_label.setObjectName("FilePathsLabel")
        results_label.setFixedWidth(140)
        self.results_input = QLineEdit(results_path)
        self.results_input.setObjectName("FilePathsInput")
        results_browse = QPushButton("...")
        results_browse.setObjectName("FilePathsBrowseButton")
        results_browse.clicked.connect(lambda: self._pick_folder(self.results_input))
        results_row_layout.addWidget(results_label)
        results_row_layout.addWidget(self.results_input, 1)
        results_row_layout.addWidget(results_browse)

        buttons_row = QWidget()
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 6, 0, 0)
        buttons_layout.setSpacing(8)
        buttons_layout.addStretch(1)
        ok_button = QPushButton("OK")
        ok_button.setObjectName("FilePathsDialogButton")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("FilePathsDialogButton")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)

        root_layout.addWidget(sound_row)
        root_layout.addWidget(movie_row)
        root_layout.addWidget(results_row)
        root_layout.addWidget(buttons_row)
        self.setFixedWidth(660)

    def _pick_folder(self, target_input: QLineEdit) -> None:
        start_dir = target_input.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select folder", start_dir)
        if folder:
            target_input.setText(folder)


class ActionConfirmDialog(QDialog):
    def __init__(self, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("FilePathsDialog")
        self.setWindowTitle("Confirm")
        flags = (
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        self.setWindowFlags(flags)
        self.setModal(True)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        message_label = QLabel(message)
        message_label.setObjectName("ConfirmMessage")
        message_label.setWordWrap(True)
        root_layout.addWidget(message_label)

        buttons_row = QWidget()
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        buttons_layout.addStretch(1)

        yes_button = QPushButton("Yes")
        yes_button.setObjectName("ConfirmButton")
        yes_button.clicked.connect(self.accept)
        no_button = QPushButton("No")
        no_button.setObjectName("ConfirmButton")
        no_button.clicked.connect(self.reject)
        buttons_layout.addWidget(yes_button)
        buttons_layout.addWidget(no_button)
        root_layout.addWidget(buttons_row)

        self.setFixedWidth(360)


class HoverHint(QFrame):
    def __init__(self, text: str) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint,
        )
        self.setObjectName("HoverHint")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        label = QLabel(text)
        label.setObjectName("HoverHintText")
        layout.addWidget(label)
        self.adjustSize()


class PopupItemButton(QPushButton):
    _check_icon: QPixmap | None = None

    def __init__(self, text: str, show_check: bool = False) -> None:
        super().__init__(text)
        self._show_check = show_check

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._show_check:
            return
        if PopupItemButton._check_icon is None:
            renderer = QSvgRenderer(QByteArray(CHECK_ICON_SVG))
            pixmap = QPixmap(10, 10)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            renderer.render(painter)
            painter.end()
            PopupItemButton._check_icon = pixmap
        painter = QPainter(self)
        icon = PopupItemButton._check_icon
        x = self.width() - icon.width() - 8
        y = (self.height() - icon.height()) // 2
        painter.drawPixmap(x, y, icon)


class MiniPopup(QFrame):
    def __init__(self, items: list[tuple[str, str | None]], on_action=None, is_action_active=None) -> None:
        super().__init__(
            None,
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint,
        )
        self.setObjectName("MiniPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._hover_hint: HoverHint | None = None
        self._on_action = on_action
        self._is_action_active = is_action_active

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        surface = QFrame()
        surface.setObjectName("MiniPopupSurface")
        surface_layout = QVBoxLayout(surface)
        surface_layout.setContentsMargins(2, 2, 2, 2)
        surface_layout.setSpacing(0)

        max_item_width = 0
        for index, (text, url) in enumerate(items):
            action_name = url[len("action:") :] if url and url.startswith("action:") else None
            has_check = action_name is not None
            is_active = bool(self._is_action_active(action_name)) if action_name and self._is_action_active else False
            item_button = PopupItemButton(text, show_check=is_active)
            item_button.setObjectName("MiniPopupItem")
            if has_check:
                item_button.setProperty("hasCheck", True)
            if is_active:
                item_button.setProperty("active", True)
            item_button.setCursor(Qt.CursorShape.PointingHandCursor)
            if url and url.startswith("copy:"):
                item_button.setProperty("copy_hint", True)
                item_button.installEventFilter(self)
            item_button.clicked.connect(lambda checked=False, u=url: self._on_item_clicked(u))
            surface_layout.addWidget(item_button)
            text_width = self.fontMetrics().horizontalAdvance(text)
            item_width = text_width + 12 + (16 if has_check else 0)
            max_item_width = max(max_item_width, item_width)
            if index < len(items) - 1:
                separator_wrap = QWidget()
                separator_wrap.setFixedHeight(5)
                separator_layout = QVBoxLayout(separator_wrap)
                separator_layout.setContentsMargins(6, 0, 6, 0)
                separator_layout.setSpacing(0)
                separator_layout.addSpacing(2)
                separator = QFrame()
                separator.setObjectName("MiniPopupSeparator")
                separator.setFixedHeight(1)
                separator_layout.addWidget(separator)
                separator_layout.addSpacing(2)
                surface_layout.addWidget(separator_wrap)

        outer_layout.addWidget(surface)

        surface_padding = 2 + 2
        border = 2
        popup_width = max_item_width + surface_padding + border
        separator_count = max(0, len(items) - 1)
        popup_height = surface_padding + (len(items) * 24) + (separator_count * 5) + border
        self.setFixedSize(popup_width, popup_height)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched.property("copy_hint"):
            if event.type() == QEvent.Type.Enter:
                self._show_copy_hint(watched)
            elif event.type() in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress):
                self._hide_copy_hint()
        return super().eventFilter(watched, event)

    def _show_copy_hint(self, button: QObject) -> None:
        if not isinstance(button, QWidget):
            return
        x = button.width() + 8
        y = button.height() // 2
        QToolTip.showText(button.mapToGlobal(QPoint(x, y)), "Click to copy version", button)

    def _hide_copy_hint(self) -> None:
        QToolTip.hideText()

    def _on_item_clicked(self, url: str | None) -> None:
        if url and url.startswith("action:"):
            if self._on_action is not None:
                self._on_action(url[len("action:") :])
            self.close()
            return
        if url and url.startswith("copy:"):
            self._hide_copy_hint()
            QApplication.clipboard().setText(url[len("copy:") :])
            self.close()
            return
        if url:
            confirm_popup = ConfirmPopup(url)
            confirm_popup.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            _OPEN_CONFIRM_POPUPS.append(confirm_popup)
            confirm_popup.destroyed.connect(lambda: _OPEN_CONFIRM_POPUPS.pop(0) if _OPEN_CONFIRM_POPUPS else None)
            confirm_popup.move(QCursor.pos() + QPoint(0, 2))
            confirm_popup.show()
            confirm_popup.raise_()
        self.close()

    def closeEvent(self, event) -> None:
        self._hide_copy_hint()
        if self._hover_hint is not None:
            self._hover_hint.deleteLater()
            self._hover_hint = None
        super().closeEvent(event)


class SearchLineEdit(QLineEdit):
    navigateRequested = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.cursorPositionChanged.connect(self._sync_input_method)
        self.textEdited.connect(self._sync_input_method)
        self.selectionChanged.connect(self._sync_input_method)

    def _sync_input_method(self) -> None:
        self.updateMicroFocus()
        QGuiApplication.inputMethod().update(
            Qt.InputMethodQuery.ImCursorRectangle
            | Qt.InputMethodQuery.ImCursorPosition
            | Qt.InputMethodQuery.ImAnchorPosition
            | Qt.InputMethodQuery.ImEnabled
            | Qt.InputMethodQuery.ImHints
        )
        if sys.platform == "win32":
            self._sync_windows_input_anchor()

    def _sync_windows_input_anchor(self) -> None:
        if not self.hasFocus():
            return

        hwnd = int(self.winId())
        if hwnd == 0:
            return

        cursor = self.cursorRect()
        x = int(cursor.left())
        y = int(cursor.bottom())

        _user32.SetCaretPos(x, y)

        himc = _imm32.ImmGetContext(hwnd)
        if not himc:
            return

        candidate = _CANDIDATEFORM()
        candidate.dwIndex = 0
        candidate.dwStyle = _CFS_CANDIDATEPOS
        candidate.ptCurrentPos = _POINT(x, y)
        candidate.rcArea = _RECT(0, 0, 0, 0)
        _imm32.ImmSetCandidateWindow(himc, ctypes.byref(candidate))

        composition = _COMPOSITIONFORM()
        composition.dwStyle = _CFS_POINT
        composition.ptCurrentPos = _POINT(x, y)
        composition.rcArea = _RECT(0, 0, 0, 0)
        _imm32.ImmSetCompositionWindow(himc, ctypes.byref(composition))

        _imm32.ImmReleaseContext(hwnd, himc)

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        QTimer.singleShot(0, self._sync_input_method)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        QTimer.singleShot(0, self._sync_input_method)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key.Key_Down:
            self.navigateRequested.emit(1)
            event.accept()
            return
        if key == Qt.Key.Key_Up:
            self.navigateRequested.emit(-1)
            event.accept()
            return
        super().keyPressEvent(event)
        QTimer.singleShot(0, self._sync_input_method)


class SmoothListWidget(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self._scroll_pos = 0.0
        self._scroll_target = 0.0
        self._scroll_clock = QElapsedTimer()
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._scroll_timer.setInterval(0)
        self._scroll_timer.timeout.connect(self._animate_scroll)

    def wheelEvent(self, event) -> None:
        delta = event.pixelDelta().y()
        if delta == 0:
            angle = event.angleDelta().y()
            if angle == 0:
                super().wheelEvent(event)
                return
            steps = angle / 120.0
            delta = int(steps * 52)

        bar = self.verticalScrollBar()
        if not self._scroll_timer.isActive():
            self._scroll_pos = float(bar.value())
            self._scroll_target = float(bar.value())
            self._scroll_clock.restart()

        self._scroll_target = max(float(bar.minimum()), min(float(bar.maximum()), self._scroll_target - float(delta)))
        if not self._scroll_timer.isActive():
            self._scroll_timer.start()
        event.accept()

    def _animate_scroll(self) -> None:
        bar = self.verticalScrollBar()
        if not self._scroll_clock.isValid():
            self._scroll_clock.restart()

        dt = max(0.001, self._scroll_clock.restart() / 1000.0)
        diff = self._scroll_target - self._scroll_pos

        if abs(diff) < 0.25:
            self._scroll_pos = self._scroll_target
            bar.setValue(int(round(self._scroll_pos)))
            self._scroll_timer.stop()
            return

        response = 13.0
        alpha = 1.0 - pow(2.718281828459045, -response * dt)
        move = diff * alpha
        max_speed_px_per_sec = 1400.0
        max_step = max_speed_px_per_sec * dt
        if move > max_step:
            move = max_step
        elif move < -max_step:
            move = -max_step
        self._scroll_pos += move
        bar.setValue(int(round(self._scroll_pos)))


class MarqueeLabel(QLabel):
    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self._full_text = text
        self._offset = 0
        self._gap = 30
        self._hovered = False
        self._overflow = False
        self._timer = QTimer(self)
        self._timer.setInterval(24)
        self._timer.timeout.connect(self._on_tick)

    def setText(self, text: str) -> None:
        self._full_text = text
        super().setText(text)
        self._offset = 0
        self._update_overflow_state()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_overflow_state()

    def enterEvent(self, event) -> None:
        self._hovered = True
        if self._overflow and not self._timer.isActive():
            self._timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._timer.stop()
        self._offset = 0
        self.update()
        super().leaveEvent(event)

    def _update_overflow_state(self) -> None:
        text_width = self.fontMetrics().horizontalAdvance(self._full_text)
        self._overflow = text_width > self.contentsRect().width()
        self.setToolTip(self._full_text if self._overflow else "")
        if not self._overflow:
            self._timer.stop()
            self._offset = 0
        elif self._hovered and not self._timer.isActive():
            self._timer.start()
        self.update()

    def _on_tick(self) -> None:
        if not self._overflow:
            self._timer.stop()
            return
        text_width = self.fontMetrics().horizontalAdvance(self._full_text)
        cycle = max(1, text_width + self._gap)
        self._offset = (self._offset + 1) % cycle
        self.update()

    def paintEvent(self, event) -> None:
        if not self._overflow:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        rect = self.contentsRect()
        metrics = self.fontMetrics()
        baseline = rect.y() + (rect.height() + metrics.ascent() - metrics.descent()) // 2
        text_width = metrics.horizontalAdvance(self._full_text)
        start_x = rect.x() - self._offset

        painter.setPen(self.palette().windowText().color())
        painter.setClipRect(rect)
        painter.drawText(start_x, baseline, self._full_text)
        painter.drawText(start_x + text_width + self._gap, baseline, self._full_text)


class SearchWorkerSignals(QObject):
    completed = pyqtSignal(int, list)


class SearchWorker(QRunnable):
    def __init__(self, engine: SearchEngine, query: str, request_id: int, limit: int) -> None:
        super().__init__()
        self.engine = engine
        self.query = query
        self.request_id = request_id
        self.limit = limit
        self.signals = SearchWorkerSignals()

    def run(self) -> None:
        results = self.engine.search(self.query, self.limit)
        self.signals.completed.emit(self.request_id, results)


class ConversionWorkerSignals(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(int, int)


class ConversionWorker(QRunnable):
    def __init__(
        self,
        charts: list[SearchResult],
        sound_root: Path,
        movie_root: Path,
        project_root: Path,
        results_root: Path,
        fully_overwrite: bool,
        include_stagefile: bool,
        include_bga: bool,
        include_preview: bool,
    ) -> None:
        super().__init__()
        self.charts = charts
        self.sound_root = sound_root
        self.movie_root = movie_root
        self.project_root = project_root
        self.results_root = results_root
        self.fully_overwrite = fully_overwrite
        self.include_stagefile = include_stagefile
        self.include_bga = include_bga
        self.include_preview = include_preview
        self.signals = ConversionWorkerSignals()

    def run(self) -> None:
        succeeded = 0
        failed = 0
        for result in self.charts:
            try:
                output_dir = convert_chart(
                    result,
                    self.sound_root,
                    self.movie_root,
                    self.project_root,
                    self.results_root,
                    fully_overwrite=self.fully_overwrite,
                    include_stagefile=self.include_stagefile,
                    include_bga=self.include_bga,
                    include_preview=self.include_preview,
                )
                succeeded += 1
                self.signals.progress.emit(
                    f"[Start conversion] Done: {result.song_id_display} -> {output_dir}"
                )
            except Exception as error:
                failed += 1
                self.signals.progress.emit(
                    f"[Start conversion] Failed: {result.song_id_display}: {error}"
                )
        self.signals.finished.emit(succeeded, failed)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("iidx2bms")
        self.resize(980, 620)
        self._hard_min_width = 1100
        self._hard_min_height = 620
        self.setMinimumSize(self._hard_min_width, self._hard_min_height)
        self._active_popup: MiniPopup | None = None
        self._active_popup_button: QToolButton | None = None
        self._search_input: SearchLineEdit | None = None
        self._search_results: QListWidget | None = None
        self._conversion_logs_results: QTextEdit | None = None
        self._chart_editing_results: QListWidget | None = None
        self._chart_editing_panel: QFrame | None = None
        self._chart_editing_body: QFrame | None = None
        self._chart_editing_status_label: QLabel | None = None
        self._chart_editing_reset_button: QPushButton | None = None
        self._chart_editing_continue_button: QPushButton | None = None
        self._chart_edit_selected_widget: QWidget | None = None
        self._chart_edit_selected_song_id: int | None = None
        self._chart_editing_attention_on = False
        self._chart_editing_attention_timer = QTimer(self)
        self._chart_editing_attention_timer.setInterval(360)
        self._chart_editing_attention_timer.timeout.connect(self._toggle_chart_editing_attention)
        self._chart_name_overrides: dict[int, dict[str, str]] = {}
        self._pending_conversion_context: dict[str, object] | None = None
        self._awaiting_chart_editing_action = False
        self._page_stack: QStackedWidget | None = None
        self._main_page_button: QToolButton | None = None
        self._processing_page_button: QToolButton | None = None
        self._search_item_by_song_id: dict[int, QListWidgetItem] = {}
        self._search_selected_song_id: int | None = None
        self._pending_restore_search_song_id: int | None = None
        self._search_selected_widget: QWidget | None = None
        self._selected_results: QListWidget | None = None
        self._selected_item_by_song_id: dict[int, QListWidgetItem] = {}
        self._matched_selected_song_id: int | None = None
        self._selected_song_ids: set[int] = set()
        self._selected_reset_button: QPushButton | None = None
        self._start_conversion_button: QPushButton | None = None
        self._include_stagefile_checkbox: QCheckBox | None = None
        self._include_preview_checkbox: QCheckBox | None = None
        self._include_bga_checkbox: QCheckBox | None = None
        self._conversion_active = False
        self._active_conversion_workers: list[ConversionWorker] = []
        self._pending_conversion_jobs = 0
        self._conversion_succeeded_total = 0
        self._conversion_failed_total = 0
        self._non_standard_charts_found = False
        self._level_line_cache: dict[tuple[str, int, int, int, int, int], str] = {}
        self._settings = QSettings("Glebsin", "iidx2bms")
        self._show_chart_difficulty = bool(
            self._settings.value("ui/show_chart_difficulty", False, bool)
        )
        self._show_game_version = bool(
            self._settings.value("ui/show_game_version", False, bool)
        )
        self._show_chart_genre = bool(
            self._settings.value("ui/show_chart_genre", False, bool)
        )
        self._show_ascii_song_title = bool(
            self._settings.value("ui/show_ascii_song_title", False, bool)
        )
        self._include_stagefile = bool(
            self._settings.value("conversion/include_stagefile", True, bool)
        )
        self._include_bga = bool(
            self._settings.value("conversion/include_bga", True, bool)
        )
        self._include_preview = bool(
            self._settings.value("conversion/include_preview", True, bool)
        )
        self._always_skip_chart_names_editing = bool(
            self._settings.value("conversion/always_skip_chart_names_editing", False, bool)
        )
        self._fully_overwrite_results = bool(
            self._settings.value("conversion/fully_overwrite_results", False, bool)
        )
        self._parallel_converting = bool(
            self._settings.value("conversion/parallel_converting", True, bool)
        )
        self._sound_path = str(self._settings.value("paths/sound", "", str) or "")
        self._movie_path = str(self._settings.value("paths/movie", "", str) or "")
        self._output_base_path = self._load_output_base_path()
        self._search_request_id = 0
        self._search_limit = 120
        data_path = Path(__file__).resolve().parent.parent / "music_data" / "music_data.json"
        self._search_engine = SearchEngine(data_path)
        self._search_engine.set_include_levels(self._show_chart_difficulty)
        self._search_engine.set_include_game_version(self._show_game_version)
        self._search_engine.set_include_genre(self._show_chart_genre)
        self._search_pool = QThreadPool.globalInstance()
        self._search_pool.setMaxThreadCount(self._search_engine.cpu_budget)
        self._conversion_pool = QThreadPool(self)
        self._conversion_pool.setMaxThreadCount(1)
        self._build_ui()

    def _screen_can_fit_hard_min_size(self) -> bool:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return True
        available = screen.availableGeometry()
        return (
            available.width() >= self._hard_min_width
            and available.height() >= self._hard_min_height
        )

    def _restore_from_invalid_maximize(self) -> None:
        if not self.isMaximized():
            return
        self.showNormal()
        self.resize(self._hard_min_width, self._hard_min_height)

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() != QEvent.Type.WindowStateChange:
            return
        if self.isMaximized() and not self._screen_can_fit_hard_min_size():
            QTimer.singleShot(0, self._restore_from_invalid_maximize)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.setSpacing(2)
        main_page_button = self._make_nav_button("Main page", self._show_main_page)
        processing_page_button = self._make_nav_button(
            "Processing && Edit", self._show_processing_page
        )
        self._main_page_button = main_page_button
        self._processing_page_button = processing_page_button
        top_layout.addWidget(main_page_button)
        top_layout.addWidget(processing_page_button)
        top_layout.addWidget(
            self._make_menu_button(
                "Settings",
                self._settings_menu_items(),
                self._on_popup_action,
            )
        )
        top_layout.addWidget(
            self._make_menu_button(
                "About",
                [
                    ("iidx2bms GitHub page", "https://github.com/Glebsin/iidx2bms/"),
                    ("Version: 2026.217.0", "copy:2026.217.0"),
                ],
            )
        )
        top_layout.addStretch(1)

        top_separator = QFrame()
        top_separator.setObjectName("TopSeparator")

        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.setSpacing(0)

        panels_row = QWidget()
        panels_layout = QHBoxLayout(panels_row)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(2)
        panels_layout.addWidget(self._build_chart_panel("Chart select", with_action=False), 1)
        panels_layout.addWidget(self._build_chart_panel("Selected charts", with_action=True), 1)

        processing_panels_row = QWidget()
        processing_panels_layout = QHBoxLayout(processing_panels_row)
        processing_panels_layout.setContentsMargins(0, 0, 0, 0)
        processing_panels_layout.setSpacing(2)
        processing_panels_layout.addWidget(self._build_conversion_logs_panel(), 1)
        processing_panels_layout.addWidget(self._build_chart_editing_panel(), 1)

        page_stack = QStackedWidget()
        page_stack.setObjectName("PageStack")
        page_stack.addWidget(panels_row)
        page_stack.addWidget(processing_panels_row)
        self._page_stack = page_stack
        content_layout.addWidget(page_stack, 1)

        root_layout.addWidget(top_bar, 0, Qt.AlignmentFlag.AlignTop)
        root_layout.addWidget(top_separator)
        root_layout.addWidget(content_area, 1)
        self.setCentralWidget(root)
        self._show_main_page()
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()

    def _search_icon_pixmap(self, size: int = 12) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(SEARCH_ICON_SVG))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _clear_icon_pixmap(self, size: int = 15) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(CLEAR_ICON_SVG))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _trash_icon_pixmap(self, size: int = 14) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(TRASH_ICON_SVG))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _reset_icon_pixmap(self, size: int = 13) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(RESET_ICON_SVG))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _green_check_icon_pixmap(self, size: int = 11) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(CHECK_GREEN_ICON_SVG))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _build_chart_panel(self, title: str, with_action: bool) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ChartPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        header_wrap = QWidget()
        header_layout = QHBoxLayout(header_wrap)
        if with_action:
            header_layout.setContentsMargins(16, 6, 17, 7)
        else:
            header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(0)
        header_wrap.setFixedHeight(42)
        header_wrap.setFixedHeight(42)

        title_label = QLabel(title)
        title_label.setObjectName("PanelTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        if not with_action:
            ascii_checkbox = QCheckBox("Show ASCII song title")
            ascii_checkbox.setObjectName("ConversionOptionCheck")
            ascii_checkbox.setChecked(self._show_ascii_song_title)
            ascii_checkbox.toggled.connect(self._on_show_ascii_song_title_toggled)
            header_layout.addWidget(ascii_checkbox, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            reset_button = QPushButton()
            reset_button.setObjectName("SelectedResetButton")
            reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
            reset_button.setToolTip("Reset selected charts and all changes")
            reset_button.setIcon(QIcon(self._reset_icon_pixmap(14)))
            reset_button.setIconSize(QSize(14, 14))
            reset_button.setFixedSize(28, 28)
            reset_button.clicked.connect(self._on_reset_selected_charts)
            self._selected_reset_button = reset_button
            header_layout.addWidget(reset_button, 0, Qt.AlignmentFlag.AlignVCenter)

        header_line = QFrame()
        header_line.setObjectName("PanelHeaderLine")

        body = QFrame()
        body.setObjectName("PanelBody")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(0)

        if with_action:
            body_layout.setContentsMargins(8, 8, 8, 5)
            selected_results = SmoothListWidget()
            selected_results.setObjectName("SelectedResults")
            selected_results.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            selected_results.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            selected_results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            selected_results.setWordWrap(True)
            selected_results.setUniformItemSizes(True)
            self._selected_results = selected_results

            body_layout.addWidget(selected_results, 1)
            body_layout.addSpacing(5)
            controls_row = QWidget()
            controls_row.setFixedHeight(38)
            controls_layout = QHBoxLayout(controls_row)
            controls_layout.setContentsMargins(0, 0, 0, 0)
            controls_layout.setSpacing(8)

            options_wrap = QWidget()
            options_layout = QVBoxLayout(options_wrap)
            options_layout.setContentsMargins(0, 0, 0, 0)
            options_layout.setSpacing(1)

            include_stagefile_checkbox = QCheckBox("Include STAGEFILE")
            include_stagefile_checkbox.setObjectName("ConversionOptionCheck")
            include_stagefile_checkbox.setProperty("stagefile", True)
            include_stagefile_checkbox.setChecked(self._include_stagefile)
            include_stagefile_checkbox.toggled.connect(self._on_include_stagefile_toggled)
            self._include_stagefile_checkbox = include_stagefile_checkbox

            include_preview_checkbox = QCheckBox("Include preview_auto_generator.wav")
            include_preview_checkbox.setObjectName("ConversionOptionCheck")
            include_preview_checkbox.setChecked(self._include_preview)
            include_preview_checkbox.toggled.connect(self._on_include_preview_toggled)
            self._include_preview_checkbox = include_preview_checkbox

            include_bga_checkbox = QCheckBox("Include BGA")
            include_bga_checkbox.setObjectName("ConversionOptionCheck")
            include_bga_checkbox.setChecked(self._include_bga)
            include_bga_checkbox.toggled.connect(self._on_include_bga_toggled)
            self._include_bga_checkbox = include_bga_checkbox

            first_options_row = QWidget()
            first_options_layout = QHBoxLayout(first_options_row)
            first_options_layout.setContentsMargins(0, 0, 0, 0)
            first_options_layout.setSpacing(10)
            first_options_layout.addWidget(include_stagefile_checkbox)
            first_options_layout.addWidget(include_preview_checkbox)
            first_options_layout.addStretch(1)
            options_layout.addWidget(first_options_row)
            options_layout.addWidget(include_bga_checkbox)

            action_button = QPushButton("Start conversion")
            action_button.setObjectName("PanelActionButton")
            action_button.setCursor(Qt.CursorShape.PointingHandCursor)
            action_button.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
            width = action_button.fontMetrics().horizontalAdvance("Start conversion") + 16
            action_button.setFixedSize(width, 22)
            action_button.clicked.connect(self._on_start_conversion)
            self._start_conversion_button = action_button
            controls_layout.addWidget(options_wrap, 0, Qt.AlignmentFlag.AlignVCenter)
            controls_layout.addStretch(1)
            controls_layout.addWidget(action_button, 0, Qt.AlignmentFlag.AlignVCenter)
            body_layout.addWidget(controls_row)
        else:
            search_box = QFrame()
            search_box.setObjectName("SearchBox")
            search_layout = QHBoxLayout(search_box)
            search_layout.setContentsMargins(8, 0, 4, 0)
            search_layout.setSpacing(6)

            search_icon = QLabel()
            search_icon.setObjectName("SearchIcon")
            search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            search_icon.setFixedSize(12, 12)
            search_icon.setPixmap(self._search_icon_pixmap(12))

            search_input = SearchLineEdit()
            search_input.setObjectName("SearchInput")
            search_input.setPlaceholderText("Search by 5-digit ID, artist or track title")
            search_box.setFocusProxy(search_input)

            search_layout.addWidget(search_icon)
            search_layout.addWidget(search_input, 1)

            clear_button = QPushButton()
            clear_button.setObjectName("SearchClearButton")
            clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
            clear_button.setToolTip("Clear search")
            clear_button.setIcon(QIcon(self._clear_icon_pixmap(15)))
            clear_button.setIconSize(QSize(15, 15))
            clear_button.clicked.connect(search_input.clear)
            search_layout.addWidget(clear_button, 0, Qt.AlignmentFlag.AlignVCenter)

            results = SmoothListWidget()
            results.setObjectName("SearchResults")
            results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            results.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            results.setWordWrap(True)
            results.setUniformItemSizes(True)

            self._search_input = search_input
            self._search_results = results
            self._search_input.textChanged.connect(self._on_search_text_changed)
            self._search_input.navigateRequested.connect(self._on_navigate_requested)
            self._search_input.returnPressed.connect(self._add_current_search_result)
            results.itemActivated.connect(self._on_search_item_activated)
            results.itemDoubleClicked.connect(self._on_search_item_activated)
            results.currentItemChanged.connect(
                lambda current, previous: self._on_search_current_item_changed(current)
            )

            body_layout.addWidget(search_box)
            body_layout.addSpacing(6)
            body_layout.addWidget(results, 1)

        panel_layout.addWidget(header_wrap)
        panel_layout.addWidget(header_line)
        panel_layout.addWidget(body, 1)
        return panel

    def _build_conversion_logs_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ChartPanel")
        panel.setMinimumWidth(0)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        header_wrap = QWidget()
        header_layout = QHBoxLayout(header_wrap)
        header_layout.setContentsMargins(16, 7, 18, 7)
        header_layout.setSpacing(0)
        header_wrap.setFixedHeight(42)

        title_label = QLabel("Conversion logs")
        title_label.setObjectName("PanelTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        header_line = QFrame()
        header_line.setObjectName("PanelHeaderLine")

        body = QFrame()
        body.setObjectName("PanelBody")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(0)

        logs_list = QTextEdit()
        logs_list.setObjectName("ConversionLogs")
        logs_list.setReadOnly(True)
        logs_list.setAcceptRichText(False)
        logs_list.setUndoRedoEnabled(False)
        logs_list.setCursorWidth(0)
        logs_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        logs_list.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        logs_list.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self._conversion_logs_results = logs_list
        body_layout.addWidget(logs_list, 1)
        body_layout.addSpacing(8)

        buttons_row = QWidget()
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)

        return_button = QPushButton("Return to Main page")
        return_button.setObjectName("PanelActionButton")
        return_button.setCursor(Qt.CursorShape.PointingHandCursor)
        return_button.clicked.connect(self._show_main_page)
        return_width = return_button.fontMetrics().horizontalAdvance("Return to Main page") + 16
        return_button.setFixedSize(return_width, 22)

        open_results_button = QPushButton("Open Results folder")
        open_results_button.setObjectName("PanelActionButton")
        open_results_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_results_button.clicked.connect(self._open_results_folder)
        open_width = open_results_button.fontMetrics().horizontalAdvance("Open Results folder") + 16
        open_results_button.setFixedSize(open_width, 22)

        buttons_layout.addWidget(return_button, 0, Qt.AlignmentFlag.AlignLeft)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(open_results_button, 0, Qt.AlignmentFlag.AlignRight)
        body_layout.addWidget(buttons_row)

        panel_layout.addWidget(header_wrap)
        panel_layout.addWidget(header_line)
        panel_layout.addWidget(body, 1)
        return panel

    def _build_chart_editing_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ChartPanel")
        panel.setMinimumWidth(0)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chart_editing_panel = panel
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        header_wrap = QWidget()
        header_layout = QHBoxLayout(header_wrap)
        header_layout.setContentsMargins(16, 6, 17, 7)
        header_layout.setSpacing(0)
        header_wrap.setFixedHeight(42)

        title_label = QLabel("Chart editing")
        title_label.setObjectName("PanelTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        status_label = QLabel("Chart name")
        status_label.setObjectName("PanelTitle")
        status_label.setStyleSheet("font-weight: 400; color: #cfcfcf;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_label.setFixedWidth(190)
        status_label.setVisible(False)
        self._chart_editing_status_label = status_label
        header_layout.addWidget(status_label, 0, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addSpacing(6)

        continue_button = QPushButton("Skip editing and continue conversion")
        continue_button.setObjectName("HeaderTextButton")
        continue_button.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_button.setIcon(QIcon(self._green_check_icon_pixmap(11)))
        continue_button.setIconSize(QSize(11, 11))
        continue_button.setFixedHeight(22)
        continue_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        continue_button.clicked.connect(self._on_chart_editing_continue_clicked)
        continue_button.setVisible(False)
        self._chart_editing_continue_button = continue_button
        header_layout.addWidget(continue_button, 0, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addSpacing(6)

        reset_button = QPushButton()
        reset_button.setObjectName("SelectedResetButton")
        reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_button.setToolTip("Reset edited chart names")
        reset_button.setIcon(QIcon(self._reset_icon_pixmap(14)))
        reset_button.setIconSize(QSize(14, 14))
        reset_button.setFixedSize(28, 28)
        reset_button.setVisible(False)
        reset_button.clicked.connect(self._on_reset_chart_editing_names_clicked)
        self._chart_editing_reset_button = reset_button
        header_layout.addWidget(reset_button, 0, Qt.AlignmentFlag.AlignVCenter)

        header_line = QFrame()
        header_line.setObjectName("PanelHeaderLine")

        body = QFrame()
        body.setObjectName("PanelBody")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chart_editing_body = body

        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(0)

        editing_list = SmoothListWidget()
        editing_list.setObjectName("SelectedResults")
        editing_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        editing_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        editing_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editing_list.setWordWrap(True)
        editing_list.setUniformItemSizes(True)
        editing_list.viewport().installEventFilter(self)
        editing_list.currentItemChanged.connect(
            lambda current, previous: self._on_chart_editing_current_item_changed(current)
        )
        self._chart_editing_results = editing_list
        body_layout.addWidget(editing_list, 1)

        panel_layout.addWidget(header_wrap)
        panel_layout.addWidget(header_line)
        panel_layout.addWidget(body, 1)
        return panel

    def _on_search_text_changed(self, text: str) -> None:
        if self._search_results is None:
            return

        self._search_request_id += 1
        request_id = self._search_request_id
        self._pending_restore_search_song_id = self._search_selected_song_id
        if not text.strip():
            self._search_results.clear()
            self._search_item_by_song_id.clear()
            self._set_search_selected_visual(None)
            return

        worker = SearchWorker(self._search_engine, text, request_id, self._search_limit)
        worker.signals.completed.connect(self._apply_search_results)
        self._search_pool.start(worker)

    def _apply_search_results(self, request_id: int, results: list[SearchResult]) -> None:
        if request_id != self._search_request_id or self._search_results is None:
            return

        self._search_results.clear()
        self._search_item_by_song_id.clear()
        for result in results:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, result)
            self._search_results.addItem(item)
            self._search_item_by_song_id[result.song_id] = item
            widget = self._build_search_result_widget(result)
            item.setSizeHint(QSize(0, 56))
            self._search_results.setItemWidget(item, widget)

        restore_song_id = self._pending_restore_search_song_id
        self._pending_restore_search_song_id = None
        if self._search_results.count() > 0:
            if restore_song_id is not None and restore_song_id in self._search_item_by_song_id:
                self._search_results.setCurrentItem(self._search_item_by_song_id[restore_song_id])
            else:
                self._search_results.setCurrentRow(0)
            self._on_search_current_item_changed(self._search_results.currentItem())
        else:
            self._set_search_selected_visual(None)

    def _on_navigate_requested(self, direction: int) -> None:
        if self._search_results is None:
            return
        count = self._search_results.count()
        if count == 0:
            return

        current = self._search_results.currentRow()
        if current < 0:
            current = 0 if direction > 0 else count - 1
        else:
            current = max(0, min(count - 1, current + direction))

        self._search_results.setCurrentRow(current)
        self._search_results.scrollToItem(self._search_results.item(current))

    def _on_search_item_activated(self, item: QListWidgetItem) -> None:
        self._add_search_result_item(item)

    def _on_search_current_item_changed(self, item: QListWidgetItem | None) -> None:
        if item is None:
            self._search_selected_song_id = None
            self._set_search_selected_visual(None)
            self._highlight_selected_chart(None)
            return
        result = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResult):
            self._search_selected_song_id = None
            self._set_search_selected_visual(None)
            self._highlight_selected_chart(None)
            return
        self._search_selected_song_id = result.song_id
        self._set_search_selected_visual(item)
        if result.song_id in self._selected_song_ids:
            self._focus_selected_chart(result.song_id)
        else:
            self._highlight_selected_chart(None)

    def _set_search_selected_visual(self, item: QListWidgetItem | None) -> None:
        if self._search_results is None:
            return
        if self._search_selected_widget is not None:
            self._search_selected_widget.setProperty("selected", False)
            self._search_selected_widget.style().unpolish(self._search_selected_widget)
            self._search_selected_widget.style().polish(self._search_selected_widget)
            self._search_selected_widget.update()
            self._search_selected_widget = None
        if item is None:
            return
        widget = self._search_results.itemWidget(item)
        if widget is None:
            return
        widget.setProperty("selected", True)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
        self._search_selected_widget = widget

    def _settings_menu_items(self) -> list[tuple[str, str | None]]:
        return [
            ("File paths", "action:file_paths"),
            ("Fully overwrite existing folders", "action:toggle_fully_overwrite_results"),
            ("Always skip chart editing", "action:toggle_always_skip_chart_names_editing"),
            ("Parallel converting", "action:toggle_parallel_converting"),
            ("Show chart difficulty", "action:toggle_chart_difficulty"),
            ("Show game version", "action:toggle_game_version"),
            ("Show chart genre", "action:toggle_chart_genre"),
        ]

    def _on_popup_action(self, action: str) -> None:
        if action == "file_paths":
            self._open_file_paths_dialog()
        elif action == "toggle_fully_overwrite_results":
            self._toggle_fully_overwrite_results()
        elif action == "toggle_always_skip_chart_names_editing":
            self._toggle_always_skip_chart_names_editing()
        elif action == "toggle_parallel_converting":
            self._toggle_parallel_converting()
        elif action == "toggle_chart_difficulty":
            self._toggle_chart_difficulty()
        elif action == "toggle_game_version":
            self._toggle_game_version()
        elif action == "toggle_chart_genre":
            self._toggle_chart_genre()

    def _is_popup_action_active(self, action: str | None) -> bool:
        if action == "toggle_chart_difficulty":
            return self._show_chart_difficulty
        if action == "toggle_game_version":
            return self._show_game_version
        if action == "toggle_chart_genre":
            return self._show_chart_genre
        if action == "toggle_parallel_converting":
            return self._parallel_converting
        if action == "toggle_fully_overwrite_results":
            return self._fully_overwrite_results
        if action == "toggle_always_skip_chart_names_editing":
            return self._always_skip_chart_names_editing
        return False

    def _open_file_paths_dialog(self) -> None:
        dialog = FilePathsDialog(self._sound_path, self._movie_path, self._output_base_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._sound_path = dialog.sound_input.text().strip()
            self._movie_path = dialog.movie_input.text().strip()
            output_base_text = dialog.results_input.text().strip()
            if output_base_text:
                self._output_base_path = str(Path(output_base_text).expanduser())
            else:
                self._output_base_path = str(self._default_output_base_path())
            self._settings.setValue("paths/sound", self._sound_path)
            self._settings.setValue("paths/movie", self._movie_path)
            self._settings.setValue("paths/output_base", self._output_base_path)
            self._settings.sync()

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _default_output_base_path(self) -> Path:
        if getattr(sys, "frozen", False):
            executable = getattr(sys, "executable", "")
            if executable:
                return Path(executable).resolve().parent
        return self._project_root()

    def _load_output_base_path(self) -> str:
        default_path = str(self._default_output_base_path())
        if self._settings.contains("paths/output_base"):
            value = str(self._settings.value("paths/output_base", default_path, str) or "").strip()
            return value or default_path
        legacy_value = str(self._settings.value("paths/results", "", str) or "").strip()
        if legacy_value:
            legacy_path = Path(legacy_value).expanduser()
            if legacy_path.name.lower() == "results":
                return str(legacy_path.parent)
            return str(legacy_path)
        return default_path

    def _selected_results_data(self) -> list[SearchResult]:
        selected: list[SearchResult] = []
        if self._selected_results is None:
            return selected
        for row_index in range(self._selected_results.count()):
            item = self._selected_results.item(row_index)
            result = item.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(result, SearchResult):
                continue
            result = self._search_engine.ensure_levels(result)
            result = self._search_engine.ensure_genre(result)
            if not result.game_name:
                result = self._search_engine.ensure_game_name(result)
            item.setData(Qt.ItemDataRole.UserRole + 1, result)
            selected.append(result)
        return selected

    def _primary_line_text(self, result: SearchResult, use_ascii: bool) -> str:
        title = result.title_ascii if use_ascii else result.title
        if not title:
            title = result.title if use_ascii else result.title_ascii
        return f"ID: {result.song_id_display}  {result.artist} - {title}"

    def _contains_non_standard_symbols(self, text: str) -> bool:
        return re.search(r"[^A-Za-z0-9 \t\-\_\.\,\!\?\:\;\'\"\/\&\+\(\)\[\]]", text) is not None

    def _is_chart_non_standard(self, result: SearchResult) -> bool:
        fields = [result.title, result.artist, result.genre]
        return any(self._contains_non_standard_symbols(value or "") for value in fields)

    def _secondary_line_text_for_edit(self, result: SearchResult) -> str:
        genre = result.genre or ""
        game = result.game_name or ""
        chunks = [f"Genre: {genre}"]
        if game:
            chunks.append(f"Game: {game}")
        return "  ".join(chunks)

    def _chart_editing_warning_message(self, charts_count: int) -> str:
        if charts_count <= 1:
            return "Non-standard symbols in chart name or genre, see Chart editing tab to continue"
        return "Non-standard symbols in chart names or genres, see Chart editing tab to continue"

    def _chart_editing_locked_tooltip(self) -> str:
        return "\"Always skip chart editing\" option is enabled,\nturn it off to edit"

    def _edited_charts_count(self, charts: list[SearchResult]) -> int:
        song_ids = {chart.song_id for chart in charts}
        return sum(
            1
            for song_id, values in self._chart_name_overrides.items()
            if song_id in song_ids and bool(values)
        )

    def _update_start_conversion_button_state(self) -> None:
        if self._start_conversion_button is None:
            return
        has_charts = bool(self._selected_song_ids)
        if self._selected_reset_button is not None:
            self._selected_reset_button.setVisible(has_charts)
        if self._conversion_active:
            self._start_conversion_button.setEnabled(False)
            self._start_conversion_button.setText("Converting...")
            self._start_conversion_button.setToolTip("")
            return
        self._start_conversion_button.setText("Start conversion")
        self._start_conversion_button.setEnabled(has_charts)
        if has_charts:
            self._start_conversion_button.setToolTip("")
        else:
            self._start_conversion_button.setToolTip("Select at least one chart to start conversion")

    def _clear_chart_editing_warning_logs(self) -> None:
        if self._conversion_logs_results is None:
            return
        warning_single = self._chart_editing_warning_message(1)
        warning_multi = self._chart_editing_warning_message(2)
        finish_editing_first = (
            'Finish chart editing first (use "Apply and continue conversion" button '
            'or "Skip editing and continue conversion" button).'
        )
        lines = self._conversion_logs_results.toPlainText().splitlines()
        kept_lines = [
            line
            for line in lines
            if line not in {warning_single, warning_multi, finish_editing_first}
        ]
        self._conversion_logs_results.clear()
        for line in kept_lines:
            self._append_conversion_log(line, error=False)

    def _has_chart_name_overrides(self) -> bool:
        return any(bool(values) for values in self._chart_name_overrides.values())

    def _apply_chart_name_override(self, result: SearchResult) -> SearchResult:
        override = self._chart_name_overrides.get(result.song_id)
        if not override:
            return result
        updates = {
            key: value
            for key, value in override.items()
            if key in {"artist", "title", "genre"}
        }
        if not updates:
            return result
        return replace(result, **updates)

    def _refresh_chart_editing_header_controls(self) -> None:
        charts_count = self._chart_editing_results.count() if self._chart_editing_results is not None else 0
        has_edits = self._has_chart_name_overrides()
        if self._chart_editing_status_label is not None:
            if charts_count <= 0 or not has_edits:
                self._chart_editing_status_label.setVisible(False)
            else:
                self._chart_editing_status_label.setVisible(True)
                self._chart_editing_status_label.setText("Chart names are edited*")
        if self._chart_editing_reset_button is not None:
            self._chart_editing_reset_button.setVisible(charts_count > 0 and has_edits)
        if self._chart_editing_continue_button is not None:
            waiting = self._awaiting_chart_editing_action and charts_count > 0
            self._chart_editing_continue_button.setVisible(waiting)
            if waiting:
                text = (
                    "Apply and continue conversion"
                    if has_edits
                    else "Skip editing and continue conversion"
                )
                self._chart_editing_continue_button.setText(text)
                width = (
                    self._chart_editing_continue_button.fontMetrics().horizontalAdvance(text)
                    + 40
                )
                self._chart_editing_continue_button.setFixedWidth(width)

    def _set_chart_editing_attention(self, enabled: bool) -> None:
        if self._chart_editing_panel is None:
            return
        if not enabled:
            self._chart_editing_attention_timer.stop()
            self._chart_editing_attention_on = False
            self._chart_editing_panel.setProperty("attention", False)
            self._chart_editing_panel.style().unpolish(self._chart_editing_panel)
            self._chart_editing_panel.style().polish(self._chart_editing_panel)
            self._chart_editing_panel.update()
            if self._chart_editing_body is not None:
                self._chart_editing_body.setProperty("attention", False)
                self._chart_editing_body.style().unpolish(self._chart_editing_body)
                self._chart_editing_body.style().polish(self._chart_editing_body)
                self._chart_editing_body.update()
            return
        self._chart_editing_attention_on = False
        if not self._chart_editing_attention_timer.isActive():
            self._chart_editing_attention_timer.start()
        self._toggle_chart_editing_attention()

    def _toggle_chart_editing_attention(self) -> None:
        if self._chart_editing_panel is None:
            return
        self._chart_editing_attention_on = not self._chart_editing_attention_on
        self._chart_editing_panel.setProperty("attention", self._chart_editing_attention_on)
        self._chart_editing_panel.style().unpolish(self._chart_editing_panel)
        self._chart_editing_panel.style().polish(self._chart_editing_panel)
        self._chart_editing_panel.update()
        if self._chart_editing_body is not None:
            self._chart_editing_body.setProperty("attention", self._chart_editing_attention_on)
            self._chart_editing_body.style().unpolish(self._chart_editing_body)
            self._chart_editing_body.style().polish(self._chart_editing_body)
            self._chart_editing_body.update()

    def _set_chart_name_override(self, song_id: int, field: str, value: str) -> None:
        if self._selected_results is None:
            return
        selected_item = self._selected_item_by_song_id.get(song_id)
        if selected_item is None:
            return
        base_result = selected_item.data(Qt.ItemDataRole.UserRole + 2)
        if not isinstance(base_result, SearchResult):
            return

        normalized_value = value.strip()
        base_value = str(getattr(base_result, field, "") or "")
        song_override = dict(self._chart_name_overrides.get(song_id, {}))
        if normalized_value == base_value:
            song_override.pop(field, None)
        else:
            song_override[field] = normalized_value
        if song_override:
            self._chart_name_overrides[song_id] = song_override
        else:
            self._chart_name_overrides.pop(song_id, None)
        self._refresh_chart_editing_header_controls()

    def _focus_chart_editing_song(self, song_id: int) -> None:
        if self._chart_editing_results is None:
            return
        for row_index in range(self._chart_editing_results.count()):
            candidate = self._chart_editing_results.item(row_index)
            if candidate is None:
                continue
            if candidate.data(Qt.ItemDataRole.UserRole) == song_id:
                self._chart_editing_results.setCurrentItem(candidate)
                return

    def _build_chart_editing_result_widget(self, result: SearchResult, item: QListWidgetItem) -> QWidget:
        row = QFrame()
        row.setObjectName("SelectedChartItem")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(6)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        first_line = QWidget()
        first_line_layout = QHBoxLayout(first_line)
        first_line_layout.setContentsMargins(0, 0, 0, 0)
        first_line_layout.setSpacing(6)
        id_label = QLabel(f"ID: {result.song_id_display}")
        id_label.setObjectName("ChartEditPrefix")
        first_line_layout.addWidget(id_label, 0, Qt.AlignmentFlag.AlignVCenter)

        artist_input = QLineEdit(result.artist)
        artist_input.setObjectName("ChartEditInput")
        artist_input.setPlaceholderText("Artist")
        artist_input.setProperty("chart_editing_song_id", result.song_id)
        artist_input.installEventFilter(self)
        artist_input.setEnabled(not self._always_skip_chart_names_editing)
        artist_input.setToolTip(
            self._chart_editing_locked_tooltip() if self._always_skip_chart_names_editing else ""
        )
        artist_input.textChanged.connect(
            lambda text, sid=result.song_id: self._set_chart_name_override(sid, "artist", text)
        )
        first_line_layout.addWidget(artist_input, 1)

        dash_label = QLabel("-")
        dash_label.setObjectName("ChartEditPrefix")
        first_line_layout.addWidget(dash_label, 0, Qt.AlignmentFlag.AlignVCenter)

        title_input = QLineEdit(result.title)
        title_input.setObjectName("ChartEditInput")
        title_input.setPlaceholderText("Title")
        title_input.setProperty("chart_editing_song_id", result.song_id)
        title_input.installEventFilter(self)
        title_input.setEnabled(not self._always_skip_chart_names_editing)
        title_input.setToolTip(
            self._chart_editing_locked_tooltip() if self._always_skip_chart_names_editing else ""
        )
        title_input.textChanged.connect(
            lambda text, sid=result.song_id: self._set_chart_name_override(sid, "title", text)
        )
        first_line_layout.addWidget(title_input, 1)
        left_layout.addWidget(first_line)

        second_line = QWidget()
        second_line_layout = QHBoxLayout(second_line)
        second_line_layout.setContentsMargins(0, 0, 0, 0)
        second_line_layout.setSpacing(6)

        genre_prefix = QLabel("Genre:")
        genre_prefix.setObjectName("ChartEditPrefix")
        second_line_layout.addWidget(genre_prefix, 0, Qt.AlignmentFlag.AlignVCenter)

        genre_input = QLineEdit(result.genre)
        genre_input.setObjectName("ChartEditInput")
        genre_input.setPlaceholderText("Genre")
        genre_input.setProperty("chart_editing_song_id", result.song_id)
        genre_input.installEventFilter(self)
        genre_input.setEnabled(not self._always_skip_chart_names_editing)
        genre_input.setToolTip(
            self._chart_editing_locked_tooltip() if self._always_skip_chart_names_editing else ""
        )
        genre_input.textChanged.connect(
            lambda text, sid=result.song_id: self._set_chart_name_override(sid, "genre", text)
        )
        second_line_layout.addWidget(genre_input, 1)

        if result.game_name:
            game_label = QLabel(f"Game: {result.game_name}")
            game_label.setObjectName("ChartEditPrefix")
            second_line_layout.addWidget(game_label, 0, Qt.AlignmentFlag.AlignVCenter)
        left_layout.addWidget(second_line)

        def _show_from_start(edit: QLineEdit) -> None:
            edit.setCursorPosition(0)
            edit.deselect()

        for edit in (artist_input, title_input, genre_input):
            _show_from_start(edit)
            QTimer.singleShot(0, lambda e=edit: _show_from_start(e))

        def _select_editing_item() -> None:
            self._focus_chart_editing_song(result.song_id)

        artist_input.cursorPositionChanged.connect(lambda old, new: _select_editing_item())
        title_input.cursorPositionChanged.connect(lambda old, new: _select_editing_item())
        genre_input.cursorPositionChanged.connect(lambda old, new: _select_editing_item())

        row_layout.addWidget(left_column, 1)
        return row

    def _update_chart_editing_list(self) -> int:
        if self._chart_editing_results is None or self._selected_results is None:
            return 0
        selected_song_ids: set[int] = set()
        self._chart_editing_results.clear()
        flagged_count = 0
        for row_index in range(self._selected_results.count()):
            item = self._selected_results.item(row_index)
            result = item.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(result, SearchResult):
                continue
            selected_song_ids.add(result.song_id)

            base_result = item.data(Qt.ItemDataRole.UserRole + 2)
            if not isinstance(base_result, SearchResult):
                base_result = result
            base_result = self._search_engine.ensure_levels(base_result)
            base_result = self._search_engine.ensure_genre(base_result)
            if not base_result.game_name:
                base_result = self._search_engine.ensure_game_name(base_result)
            item.setData(Qt.ItemDataRole.UserRole + 2, base_result)

            result = self._apply_chart_name_override(base_result)
            item.setData(Qt.ItemDataRole.UserRole + 1, result)
            base_non_standard = self._is_chart_non_standard(base_result)
            effective_non_standard = self._is_chart_non_standard(result)
            if not base_non_standard and result.song_id not in self._chart_name_overrides:
                continue
            if base_non_standard:
                flagged_count += 1
            edit_item = QListWidgetItem()
            edit_item.setData(Qt.ItemDataRole.UserRole, result.song_id)
            edit_item.setData(Qt.ItemDataRole.UserRole + 1, result)
            edit_item.setSizeHint(QSize(0, 72))
            self._chart_editing_results.addItem(edit_item)
            self._chart_editing_results.setItemWidget(
                edit_item, self._build_chart_editing_result_widget(result, edit_item)
            )
        for song_id in list(self._chart_name_overrides.keys()):
            if song_id not in selected_song_ids:
                self._chart_name_overrides.pop(song_id, None)
        if self._chart_editing_results.count() > 0:
            selected_item: QListWidgetItem | None = None
            if self._chart_edit_selected_song_id is not None:
                for row_index in range(self._chart_editing_results.count()):
                    candidate = self._chart_editing_results.item(row_index)
                    if candidate.data(Qt.ItemDataRole.UserRole) == self._chart_edit_selected_song_id:
                        selected_item = candidate
                        break
            if selected_item is None:
                selected_item = self._chart_editing_results.item(0)
            self._chart_editing_results.setCurrentItem(selected_item)
            self._set_chart_editing_selected_visual(selected_item)
        else:
            self._chart_edit_selected_song_id = None
            self._set_chart_editing_selected_visual(None)
        self._refresh_chart_editing_header_controls()
        return flagged_count

    def _confirm_action(self, message: str) -> bool:
        dialog = ActionConfirmDialog(message, self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def _on_reset_selected_charts(self) -> None:
        if self._selected_results is None:
            return
        if self._selected_results.count() == 0:
            return
        if not self._confirm_action("Reset selected charts and all changes?"):
            return
        self._selected_results.clear()
        self._selected_item_by_song_id.clear()
        self._selected_song_ids.clear()
        self._matched_selected_song_id = None
        self._highlight_selected_chart(None)
        self._chart_name_overrides.clear()
        self._chart_edit_selected_song_id = None
        self._pending_conversion_context = None
        self._awaiting_chart_editing_action = False
        self._set_chart_editing_attention(False)
        self._clear_chart_editing_warning_logs()
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()

    def _on_reset_chart_editing_names_clicked(self) -> None:
        if not self._chart_name_overrides:
            return
        if not self._confirm_action("Do you want to reset names?"):
            return
        if self._selected_results is None:
            return
        for row_index in range(self._selected_results.count()):
            item = self._selected_results.item(row_index)
            base_result = item.data(Qt.ItemDataRole.UserRole + 2)
            if not isinstance(base_result, SearchResult):
                continue
            item.setData(Qt.ItemDataRole.UserRole + 1, base_result)
        self._chart_name_overrides.clear()
        self._refresh_selected_result_widgets()
        self._update_chart_editing_list()

    def _on_chart_editing_continue_clicked(self) -> None:
        if not self._awaiting_chart_editing_action:
            return
        context = self._pending_conversion_context
        if context is None:
            return
        has_edits = self._has_chart_name_overrides()
        if has_edits:
            message = "Apply edited names and continue conversion?"
        else:
            message = "Skip editing and continue conversion?"
        if not self._confirm_action(message):
            return

        charts = list(context["charts"])
        resolved_charts: list[SearchResult] = []
        for chart in charts:
            resolved_charts.append(self._apply_chart_name_override(chart))
        charts_to_convert, fully_overwrite = self._resolve_overwrite_policy(
            resolved_charts,
            context["results_root"],
        )
        if not charts_to_convert:
            self._awaiting_chart_editing_action = False
            self._pending_conversion_context = None
            self._set_chart_editing_attention(False)
            self._clear_chart_editing_warning_logs()
            self._refresh_chart_editing_header_controls()
            print("[Start conversion] No charts left to convert")
            return

        self._awaiting_chart_editing_action = False
        self._pending_conversion_context = None
        self._set_chart_editing_attention(False)
        self._clear_chart_editing_warning_logs()
        self._refresh_chart_editing_header_controls()
        edited_count = self._edited_charts_count(charts_to_convert)
        self._clear_selected_charts_after_start()
        self._begin_conversion(
            charts_to_convert,
            context["sound_root"],
            context["movie_root"],
            context["project_root"],
            context["results_root"],
            fully_overwrite,
            context["include_stagefile"],
            context["include_bga"],
            context["include_preview"],
            context["parallel_converting"],
            edited_count,
        )

    def _begin_conversion(
        self,
        charts: list[SearchResult],
        sound_root: Path,
        movie_root: Path,
        project_root: Path,
        results_root: Path,
        fully_overwrite: bool,
        include_stagefile: bool,
        include_bga: bool,
        include_preview: bool,
        parallel_converting: bool,
        edited_count: int,
    ) -> None:
        stagefile_text = "yes" if include_stagefile else "no"
        bga_text = "yes" if include_bga else "no"
        preview_text = "yes" if include_preview else "no"
        self._append_conversion_log(
            f"Started. Charts: {len(charts)}, Edited: {edited_count}, "
            f"STAGEFILE: {stagefile_text}, BGA: {bga_text}, Audio preview: {preview_text}"
        )
        self._conversion_active = True
        self._update_start_conversion_button_state()
        self._conversion_pool.setMaxThreadCount(4 if parallel_converting else 1)
        self._active_conversion_workers = []
        self._pending_conversion_jobs = len(charts)
        self._conversion_succeeded_total = 0
        self._conversion_failed_total = 0
        for chart in charts:
            worker = ConversionWorker(
                [chart],
                sound_root,
                movie_root,
                project_root,
                results_root,
                fully_overwrite,
                include_stagefile,
                include_bga,
                include_preview,
            )
            worker.signals.progress.connect(self._on_conversion_progress)
            worker.signals.finished.connect(self._on_conversion_worker_finished)
            self._active_conversion_workers.append(worker)
            self._conversion_pool.start(worker)

    def _existing_result_song_ids(self, results_root: Path) -> set[str]:
        ids: set[str] = set()
        if not results_root.is_dir():
            return ids
        for entry in results_root.iterdir():
            if not entry.is_dir():
                continue
            name = entry.name.strip()
            if " -" not in name:
                continue
            prefix = name.split(" -", 1)[0].strip()
            if re.fullmatch(r"\d{5}", prefix):
                ids.add(prefix)
        return ids

    def _resolve_overwrite_policy(
        self, charts: list[SearchResult], results_root: Path
    ) -> tuple[list[SearchResult], bool]:
        if not charts:
            return [], False
        if self._fully_overwrite_results:
            return list(charts), True

        existing_song_ids = self._existing_result_song_ids(results_root)
        conflicting_song_ids = {chart.song_id_display for chart in charts if chart.song_id_display in existing_song_ids}
        if not conflicting_song_ids:
            return list(charts), False

        question = (
            "Some chart folders already exist in Results.\n"
            "Overwrite all matching chart folders by song ID?"
        )
        if self._confirm_action(question):
            return list(charts), True

        filtered = [chart for chart in charts if chart.song_id_display not in conflicting_song_ids]
        skipped = len(charts) - len(filtered)
        if skipped > 0:
            self._append_conversion_log(
                f"Skipped existing charts: {skipped} (overwrite declined).",
                error=True,
            )
        return filtered, False

    def _on_start_conversion(self) -> None:
        if self._conversion_active:
            print("[Start conversion] Already in progress")
            return
        if self._awaiting_chart_editing_action:
            self._show_processing_page()
            self._set_chart_editing_attention(True)
            return
        initial_charts = self._selected_results_data()
        if not initial_charts:
            print("[Start conversion] No selected charts")
            return

        sound_path = self._sound_path.strip()
        sound_root = Path(sound_path)
        if not sound_path or not sound_root.is_dir():
            print("[Start conversion] Sound path is not set or does not exist")
            return
        movie_path = self._movie_path.strip()
        movie_root = Path(movie_path)
        if not movie_path or not movie_root.is_dir():
            print("[Start conversion] Movie path is not set or does not exist")
            return
        output_base_path = self._output_base_path.strip()
        output_base_root = (
            Path(output_base_path).expanduser()
            if output_base_path
            else self._default_output_base_path()
        )
        if output_base_root.exists() and not output_base_root.is_dir():
            print("[Start conversion] Output folder path exists and is not a folder")
            return
        results_root = output_base_root / "Results"

        if self._conversion_logs_results is not None:
            self._conversion_logs_results.clear()
        self._show_processing_page()
        flagged_count = self._update_chart_editing_list()
        charts = [
            self._apply_chart_name_override(chart)
            for chart in self._selected_results_data()
        ]
        include_stagefile = self._include_stagefile
        include_bga = self._include_bga
        include_preview = self._include_preview
        parallel_converting = self._parallel_converting
        project_root = self._project_root()
        base_charts: list[SearchResult] = []
        if self._selected_results is not None:
            for row_index in range(self._selected_results.count()):
                item = self._selected_results.item(row_index)
                base_result = item.data(Qt.ItemDataRole.UserRole + 2)
                if isinstance(base_result, SearchResult):
                    base_charts.append(base_result)
                else:
                    current_result = item.data(Qt.ItemDataRole.UserRole + 1)
                    if isinstance(current_result, SearchResult):
                        base_charts.append(current_result)
        self._pending_conversion_context = {
            "charts": base_charts,
            "sound_root": sound_root,
            "movie_root": movie_root,
            "project_root": project_root,
            "results_root": results_root,
            "fully_overwrite": self._fully_overwrite_results,
            "include_stagefile": include_stagefile,
            "include_bga": include_bga,
            "include_preview": include_preview,
            "parallel_converting": parallel_converting,
        }
        if flagged_count > 0 and not self._always_skip_chart_names_editing:
            self._awaiting_chart_editing_action = True
            self._set_chart_editing_attention(True)
            self._append_conversion_log(
                self._chart_editing_warning_message(flagged_count),
                error=True,
            )
            self._refresh_chart_editing_header_controls()
            return

        self._awaiting_chart_editing_action = False
        self._set_chart_editing_attention(False)
        self._refresh_chart_editing_header_controls()
        self._pending_conversion_context = None
        charts_to_convert, fully_overwrite = self._resolve_overwrite_policy(charts, results_root)
        if not charts_to_convert:
            print("[Start conversion] No charts left to convert")
            return
        edited_count = self._edited_charts_count(charts_to_convert)
        self._clear_selected_charts_after_start()
        self._begin_conversion(
            list(charts_to_convert),
            sound_root,
            movie_root,
            project_root,
            results_root,
            fully_overwrite,
            include_stagefile,
            include_bga,
            include_preview,
            parallel_converting,
            edited_count,
        )

    def _on_include_stagefile_toggled(self, checked: bool) -> None:
        self._include_stagefile = bool(checked)
        self._settings.setValue("conversion/include_stagefile", self._include_stagefile)
        self._settings.sync()

    def _on_include_bga_toggled(self, checked: bool) -> None:
        self._include_bga = bool(checked)
        self._settings.setValue("conversion/include_bga", self._include_bga)
        self._settings.sync()

    def _on_include_preview_toggled(self, checked: bool) -> None:
        self._include_preview = bool(checked)
        self._settings.setValue("conversion/include_preview", self._include_preview)
        self._settings.sync()

    def _on_conversion_progress(self, message: str) -> None:
        self._append_conversion_log(message)

    def _on_conversion_worker_finished(self, succeeded: int, failed: int) -> None:
        self._conversion_succeeded_total += succeeded
        self._conversion_failed_total += failed
        self._pending_conversion_jobs -= 1
        if self._pending_conversion_jobs > 0:
            return
        self._conversion_active = False
        self._active_conversion_workers.clear()
        self._append_conversion_log(
            f"[Start conversion] Finished. Success: {self._conversion_succeeded_total}, "
            f"Failed: {self._conversion_failed_total}"
        )
        self._clear_selected_charts_after_start()

    def _clear_selected_charts_after_start(self) -> None:
        if self._selected_results is not None:
            self._selected_results.clear()
        self._selected_item_by_song_id.clear()
        self._selected_song_ids.clear()
        self._matched_selected_song_id = None
        self._chart_edit_selected_song_id = None
        self._chart_name_overrides.clear()
        self._awaiting_chart_editing_action = False
        self._pending_conversion_context = None
        self._set_chart_editing_attention(False)
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()

    def _toggle_parallel_converting(self) -> None:
        self._parallel_converting = not self._parallel_converting
        self._settings.setValue("conversion/parallel_converting", self._parallel_converting)
        self._settings.sync()

    def _toggle_fully_overwrite_results(self) -> None:
        self._fully_overwrite_results = not self._fully_overwrite_results
        self._settings.setValue("conversion/fully_overwrite_results", self._fully_overwrite_results)
        self._settings.sync()

    def _toggle_always_skip_chart_names_editing(self) -> None:
        if self._awaiting_chart_editing_action:
            self._append_conversion_log(
                'Finish chart editing first (use "Apply and continue conversion" button '
                'or "Skip editing and continue conversion" button).',
                error=True,
            )
            self._set_chart_editing_attention(True)
            QTimer.singleShot(0, lambda: self._set_chart_editing_attention(True))
            return

        enable_option = not self._always_skip_chart_names_editing
        if not enable_option:
            self._always_skip_chart_names_editing = False
            self._settings.setValue("conversion/always_skip_chart_names_editing", False)
            self._settings.sync()
            self._update_chart_editing_list()
            return

        has_edits = self._has_chart_name_overrides()
        if has_edits:
            message = (
                "Are you sure you want to enable this option?\n"
                "All changes in names and genres will be lost."
            )
        else:
            message = (
                "Are you sure you want to enable this option?\n"
                "You will not be able to edit chart names or genres."
            )
        if not self._confirm_action(message):
            return

        if has_edits:
            self._chart_name_overrides.clear()
            self._refresh_selected_result_widgets()
        self._awaiting_chart_editing_action = False
        self._pending_conversion_context = None
        if not has_edits:
            self._set_chart_editing_attention(False)
        self._clear_chart_editing_warning_logs()
        self._always_skip_chart_names_editing = True
        self._settings.setValue("conversion/always_skip_chart_names_editing", True)
        self._settings.sync()
        self._update_chart_editing_list()

    def _on_show_ascii_song_title_toggled(self, checked: bool) -> None:
        self._show_ascii_song_title = bool(checked)
        self._settings.setValue("ui/show_ascii_song_title", self._show_ascii_song_title)
        self._settings.sync()
        self._refresh_search_result_widgets()
        self._refresh_selected_result_widgets()

    def _on_chart_editing_current_item_changed(self, item: QListWidgetItem | None) -> None:
        if self._awaiting_chart_editing_action:
            self._set_chart_editing_attention(False)
        if item is None:
            self._chart_edit_selected_song_id = None
            self._set_chart_editing_selected_visual(None)
            return
        song_id = item.data(Qt.ItemDataRole.UserRole)
        self._chart_edit_selected_song_id = song_id if isinstance(song_id, int) else None
        self._set_chart_editing_selected_visual(item)

    def _set_chart_editing_selected_visual(self, item: QListWidgetItem | None) -> None:
        if self._chart_editing_results is None:
            return
        if self._chart_edit_selected_widget is not None:
            self._chart_edit_selected_widget.setProperty("selected", False)
            self._chart_edit_selected_widget.style().unpolish(self._chart_edit_selected_widget)
            self._chart_edit_selected_widget.style().polish(self._chart_edit_selected_widget)
            self._chart_edit_selected_widget.update()
            self._chart_edit_selected_widget = None
        if item is None:
            return
        widget = self._chart_editing_results.itemWidget(item)
        if widget is None:
            return
        widget.setProperty("selected", True)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
        self._chart_edit_selected_widget = widget

    def _append_conversion_log(self, message: str, error: bool = False) -> None:
        rendered = message
        if rendered.startswith("[Start conversion] "):
            rendered = rendered[len("[Start conversion] "):]
        print(rendered)
        if self._conversion_logs_results is None:
            return
        cursor = self._conversion_logs_results.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._conversion_logs_results.setTextCursor(cursor)
        finished_match = re.match(r"^Finished\. Success:\s*(\d+),\s*Failed:\s*(\d+)\s*$", rendered)
        if finished_match and not error:
            success_count, failed_count = finished_match.groups()
            cursor.insertHtml(
                "Finished. Success: "
                f'<span style="color:#00e37f;">{html.escape(success_count)}</span>, '
                "Failed: "
                f'<span style="color:#be0420;">{html.escape(failed_count)}</span>'
            )
        else:
            line_color = "#be0420" if (error or rendered.startswith("Failed:")) else "#f0f0f0"
            cursor.insertHtml(f'<span style="color:{line_color};">{html.escape(rendered)}</span>')
        cursor.insertBlock()
        self._conversion_logs_results.setTextCursor(cursor)
        self._conversion_logs_results.ensureCursorVisible()

    def _open_results_folder(self) -> None:
        output_base_path = self._output_base_path.strip()
        output_base_root = (
            Path(output_base_path).expanduser()
            if output_base_path
            else self._default_output_base_path()
        )
        results_dir = (output_base_root / "Results").resolve()
        results_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(results_dir))
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(results_dir)))
        except Exception as error:
            self._append_conversion_log(f"[Open Results folder] Failed: {error}")

    def _toggle_chart_difficulty(self) -> None:
        self._show_chart_difficulty = not self._show_chart_difficulty
        self._search_engine.set_include_levels(self._show_chart_difficulty)
        self._settings.setValue("ui/show_chart_difficulty", self._show_chart_difficulty)
        self._settings.sync()
        self._level_line_cache.clear()
        self._refresh_search_result_widgets()
        self._refresh_selected_result_widgets()

    def _toggle_game_version(self) -> None:
        self._show_game_version = not self._show_game_version
        self._search_engine.set_include_game_version(self._show_game_version)
        self._settings.setValue("ui/show_game_version", self._show_game_version)
        self._settings.sync()
        self._refresh_search_result_widgets()
        self._refresh_selected_result_widgets()

    def _toggle_chart_genre(self) -> None:
        self._show_chart_genre = not self._show_chart_genre
        self._search_engine.set_include_genre(self._show_chart_genre)
        self._settings.setValue("ui/show_chart_genre", self._show_chart_genre)
        self._settings.sync()
        self._refresh_search_result_widgets()
        self._refresh_selected_result_widgets()

    def _refresh_search_result_widgets(self) -> None:
        if self._search_results is None:
            return
        scroll_bar = self._search_results.verticalScrollBar()
        saved_scroll = scroll_bar.value()
        current_item = self._search_results.currentItem()
        current_song_id: int | None = None
        if current_item is not None:
            current_result = current_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(current_result, SearchResult):
                current_song_id = current_result.song_id

        for row_index in range(self._search_results.count()):
            item = self._search_results.item(row_index)
            result = item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(result, SearchResult):
                continue
            if self._show_chart_difficulty:
                result = self._search_engine.ensure_levels(result)
            if self._show_chart_genre:
                result = self._search_engine.ensure_genre(result)
            if self._show_game_version and not result.game_name:
                result = self._search_engine.ensure_game_name(result)
            item.setData(Qt.ItemDataRole.UserRole, result)
            widget = self._build_search_result_widget(result)
            self._search_results.setItemWidget(item, widget)

        if current_song_id is not None:
            restored_item = self._search_item_by_song_id.get(current_song_id)
            if restored_item is not None:
                self._search_results.setCurrentItem(restored_item)
                self._set_search_selected_visual(restored_item)

        scroll_bar.setValue(saved_scroll)

    def _refresh_selected_result_widgets(self) -> None:
        if self._selected_results is None:
            return
        scroll_bar = self._selected_results.verticalScrollBar()
        saved_scroll = scroll_bar.value()
        matched_song_id = self._matched_selected_song_id
        for row_index in range(self._selected_results.count()):
            item = self._selected_results.item(row_index)
            result = item.data(Qt.ItemDataRole.UserRole + 1)
            if isinstance(result, SearchResult):
                if self._show_chart_difficulty:
                    result = self._search_engine.ensure_levels(result)
                if self._show_chart_genre:
                    result = self._search_engine.ensure_genre(result)
                if self._show_game_version and not result.game_name:
                    result = self._search_engine.ensure_game_name(result)
                item.setData(Qt.ItemDataRole.UserRole + 1, result)
                widget = self._build_selected_result_widget(result, item)
                self._selected_results.setItemWidget(item, widget)
        if matched_song_id is not None:
            self._matched_selected_song_id = None
            self._highlight_selected_chart(matched_song_id)
        scroll_bar.setValue(saved_scroll)
        self._update_chart_editing_list()

    def _secondary_line_text(self, result: SearchResult) -> str:
        chunks: list[str] = []
        if self._show_chart_genre:
            chunks.append(f"Genre: {result.genre}")
        if self._show_game_version and result.game_name:
            chunks.append(f"Game: {result.game_name}")
        return "  ".join(chunks)

    def _add_current_search_result(self) -> None:
        if self._search_results is None:
            return
        self._add_search_result_item(self._search_results.currentItem())

    def _add_search_result_item(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        result = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResult):
            return
        if result.song_id in self._selected_song_ids:
            self._focus_selected_chart(result.song_id)
            return
        self._add_selected_chart(result)

    def _format_level_line(
        self,
        prefix: str,
        b_level: int,
        n_level: int,
        h_level: int,
        a_level: int,
        l_level: int,
    ) -> str:
        key = (prefix, b_level, n_level, h_level, a_level, l_level)
        cached = self._level_line_cache.get(key)
        if cached is not None:
            return cached
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
        line = f'<span style="color:#dcdcdc;">{prefix}:</span> ' + " ".join(chunks)
        self._level_line_cache[key] = line
        return line

    def _build_levels_column(self, result: SearchResult, object_name: str) -> QWidget:
        if not self._show_chart_difficulty:
            spacer = QWidget()
            spacer.setFixedWidth(0)
            return spacer
        levels_column = QWidget()
        levels_layout = QVBoxLayout(levels_column)
        levels_layout.setContentsMargins(0, 0, 0, 0)
        levels_layout.setSpacing(2)

        sp_label = QLabel(
            self._format_level_line(
                "SP",
                result.spb_level,
                result.spn_level,
                result.sph_level,
                result.spa_level,
                result.spl_level,
            )
        )
        sp_label.setObjectName(object_name)
        sp_label.setTextFormat(Qt.TextFormat.RichText)
        sp_label.setWordWrap(False)
        sp_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        levels_layout.addWidget(sp_label, 0, Qt.AlignmentFlag.AlignRight)

        dp_label = QLabel(
            self._format_level_line(
                "DP",
                result.dpb_level,
                result.dpn_level,
                result.dph_level,
                result.dpa_level,
                result.dpl_level,
            )
        )
        dp_label.setObjectName(object_name)
        dp_label.setTextFormat(Qt.TextFormat.RichText)
        dp_label.setWordWrap(False)
        dp_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        dp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        levels_layout.addWidget(dp_label, 0, Qt.AlignmentFlag.AlignRight)
        return levels_column

    def _build_search_result_widget(self, result: SearchResult) -> QWidget:
        row = QFrame()
        row.setObjectName("SearchChartItem")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        primary_label = MarqueeLabel(
            self._primary_line_text(result, use_ascii=self._show_ascii_song_title)
        )
        primary_label.setObjectName("SearchChartPrimary")
        primary_label.setWordWrap(False)
        primary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(primary_label)

        secondary_label = MarqueeLabel(self._secondary_line_text(result))
        secondary_label.setObjectName("SearchChartSecondary")
        secondary_label.setWordWrap(False)
        secondary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(secondary_label)

        row_layout.addWidget(left_column, 1)
        row_layout.addWidget(self._build_levels_column(result, "SearchChartLevels"), 0)
        return row

    def _build_selected_result_widget(self, result: SearchResult, item: QListWidgetItem) -> QWidget:
        row = QFrame()
        row.setObjectName("SelectedChartItem")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        primary_label = MarqueeLabel(
            self._primary_line_text(result, use_ascii=self._show_ascii_song_title)
        )
        primary_label.setObjectName("SelectedChartPrimary")
        primary_label.setWordWrap(False)
        primary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(primary_label)

        secondary_label = MarqueeLabel(self._secondary_line_text(result))
        secondary_label.setObjectName("SelectedChartSecondary")
        secondary_label.setWordWrap(False)
        secondary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(secondary_label)

        row_layout.addWidget(left_column, 1)
        row_layout.addWidget(self._build_levels_column(result, "SelectedChartLevels"), 0)

        remove_button = QPushButton()
        remove_button.setObjectName("TrashButton")
        remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_button.setToolTip("Remove chart")
        remove_button.setIcon(QIcon(self._trash_icon_pixmap(14)))
        remove_button.setIconSize(QSize(14, 14))
        remove_button.clicked.connect(lambda checked=False, list_item=item: self._remove_selected_chart_item(list_item))
        row_layout.addWidget(remove_button, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def _add_selected_chart(self, result: SearchResult) -> None:
        if self._selected_results is None:
            return
        if result.song_id in self._selected_song_ids:
            return

        self._selected_song_ids.add(result.song_id)
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, result.song_id)
        item.setData(Qt.ItemDataRole.UserRole + 1, result)
        item.setData(Qt.ItemDataRole.UserRole + 2, result)
        row = self._build_selected_result_widget(result, item)

        item.setSizeHint(QSize(0, 56))
        self._selected_results.addItem(item)
        self._selected_results.setItemWidget(item, row)
        self._selected_item_by_song_id[result.song_id] = item
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()

    def _remove_selected_chart_item(self, item: QListWidgetItem) -> None:
        if self._selected_results is None:
            return

        row = self._selected_results.row(item)
        if row < 0:
            return
        removed = self._selected_results.takeItem(row)
        song_id = removed.data(Qt.ItemDataRole.UserRole)
        if isinstance(song_id, int):
            self._selected_item_by_song_id.pop(song_id, None)
            self._selected_song_ids.discard(song_id)
            self._chart_name_overrides.pop(song_id, None)
            if self._matched_selected_song_id == song_id:
                self._matched_selected_song_id = None
            if self._chart_edit_selected_song_id == song_id:
                self._chart_edit_selected_song_id = None
        if not self._conversion_active:
            self._awaiting_chart_editing_action = False
            self._pending_conversion_context = None
            self._set_chart_editing_attention(False)
            if self._conversion_logs_results is not None:
                self._conversion_logs_results.clear()
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()

    def _highlight_selected_chart(self, song_id: int | None) -> None:
        if self._selected_results is None:
            return
        if self._matched_selected_song_id == song_id:
            return

        if self._matched_selected_song_id is not None:
            old_item = self._selected_item_by_song_id.get(self._matched_selected_song_id)
            if old_item is not None:
                old_widget = self._selected_results.itemWidget(old_item)
                if old_widget is not None:
                    old_widget.setProperty("matched", False)
                    old_widget.style().unpolish(old_widget)
                    old_widget.style().polish(old_widget)
                    old_widget.update()

        self._matched_selected_song_id = song_id
        if song_id is None:
            return
        new_item = self._selected_item_by_song_id.get(song_id)
        if new_item is None:
            return
        new_widget = self._selected_results.itemWidget(new_item)
        if new_widget is not None:
            new_widget.setProperty("matched", True)
            new_widget.style().unpolish(new_widget)
            new_widget.style().polish(new_widget)
            new_widget.update()

    def _focus_selected_chart(self, song_id: int) -> None:
        if self._selected_results is None:
            return
        item = self._selected_item_by_song_id.get(song_id)
        if item is None:
            return
        self._highlight_selected_chart(song_id)
        self._selected_results.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        song_id_prop = watched.property("chart_editing_song_id")
        if isinstance(song_id_prop, int) and event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.FocusIn,
        ):
            self._focus_chart_editing_song(song_id_prop)
            if self._awaiting_chart_editing_action:
                self._set_chart_editing_attention(False)

        if (
            self._chart_editing_results is not None
            and watched is self._chart_editing_results.viewport()
            and event.type() == QEvent.Type.MouseButtonPress
            and self._awaiting_chart_editing_action
        ):
            self._set_chart_editing_attention(False)
        return super().eventFilter(watched, event)

    def _make_menu_button(self, title: str, items: list[tuple[str, str | None]], on_action=None) -> QToolButton:
        button = QToolButton()
        button.setObjectName("MiniButton")
        button.setText(title)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        width = button.fontMetrics().horizontalAdvance(title.replace("&&", "&")) + 16
        button.setFixedSize(width, 22)
        button.clicked.connect(lambda checked=False, b=button, i=items, a=on_action: self._show_popup(b, i, a))
        return button

    def _make_nav_button(self, title: str, on_click) -> QToolButton:
        button = QToolButton()
        button.setObjectName("MiniButton")
        button.setText(title)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        width = button.fontMetrics().horizontalAdvance(title.replace("&&", "&")) + 16
        button.setFixedSize(width, 22)
        button.clicked.connect(on_click)
        return button

    def _set_active_page_button(self, button: QToolButton | None, active: bool) -> None:
        if button is None:
            return
        button.setProperty("activePage", active)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def _show_main_page(self) -> None:
        if self._page_stack is not None:
            self._page_stack.setCurrentIndex(0)
        self._set_active_page_button(self._main_page_button, True)
        self._set_active_page_button(self._processing_page_button, False)

    def _show_processing_page(self) -> None:
        if self._page_stack is not None:
            self._page_stack.setCurrentIndex(1)
        self._set_active_page_button(self._main_page_button, False)
        self._set_active_page_button(self._processing_page_button, True)

    def _show_popup(self, button: QToolButton, items: list[tuple[str, str | None]], on_action=None) -> None:
        if self._active_popup is not None:
            self._active_popup.close()
            self._active_popup = None

        popup = MiniPopup(items, on_action, self._is_popup_action_active)
        popup.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        popup.destroyed.connect(self._clear_active_popup)
        self._active_popup = popup
        self._active_popup_button = button
        popup.move(button.mapToGlobal(QPoint(0, button.height() + 5)))
        popup.show()
        popup.raise_()

    def _clear_active_popup(self) -> None:
        self._active_popup = None
        owner = self._active_popup_button
        self._active_popup_button = None
        if owner is not None:
            owner.setDown(False)
            owner.clearFocus()
            QApplication.sendEvent(owner, QEvent(QEvent.Type.Leave))
            owner.style().unpolish(owner)
            owner.style().polish(owner)
            owner.update()
