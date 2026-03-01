import sys
import ctypes
import os
import re
import html
import json
import subprocess
from datetime import date
from datetime import datetime
from dataclasses import replace
from pathlib import Path
from ctypes import wintypes
from PyQt6.QtCore import (
    QAbstractAnimation,
    QByteArray,
    QElapsedTimer,
    QEvent,
    QEasingCurve,
    QFileSystemWatcher,
    QObject,
    QPoint,
    QPropertyAnimation,
    QProcess,
    QProcessEnvironment,
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
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QDialog,
    QPushButton,
    QProgressBar,
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
from conversion.conversion import convert_chart, set_bme_playlevel
from remywiki.remywiki import build_remywiki_url
from history.history import (
    ConversionHistoryRun,
    ConversionHistoryStore,
    ConversionSessionRecorder,
    build_conversion_history_page,
    find_run_by_id,
    render_run_details,
    render_runs_list,
)
from window.window import restore_window_placement, save_window_placement
from PyQt6.QtCore import QUrl

if getattr(sys, "frozen", False):
    try:
        _build_dt = datetime.fromtimestamp(Path(sys.executable).stat().st_mtime)
        _today = _build_dt.date()
    except Exception:
        _today = date.today()
else:
    _today = date.today()
APP_VERSION = f"{_today.year}.{_today.month}{_today.day:02d}.0"


SEARCH_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#9a9a9a" d="M480 272C480 317.9 465.1 360.3 440 394.7L566.6 521.4C579.1 533.9 579.1 554.2 566.6 566.7C554.1 579.2 533.8 579.2 521.3 566.7L394.7 440C360.3 465.1 317.9 480 272 480C157.1 480 64 386.9 64 272C64 157.1 157.1 64 272 64C386.9 64 480 157.1 480 272zM272 416C351.5 416 416 351.5 416 272C416 192.5 351.5 128 272 128C192.5 128 128 192.5 128 272C128 351.5 192.5 416 272 416z"/></svg>'
CLEAR_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#be0420" d="M183.1 137.4C170.6 124.9 150.3 124.9 137.8 137.4C125.3 149.9 125.3 170.2 137.8 182.7L275.2 320L137.9 457.4C125.4 469.9 125.4 490.2 137.9 502.7C150.4 515.2 170.7 515.2 183.2 502.7L320.5 365.3L457.9 502.6C470.4 515.1 490.7 515.1 503.2 502.6C515.7 490.1 515.7 469.8 503.2 457.3L365.8 320L503.1 182.6C515.6 170.1 515.6 149.8 503.1 137.3C490.6 124.8 470.3 124.8 457.8 137.3L320.5 274.7L183.1 137.4z"/></svg>'
TRASH_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="#be0420" d="M136.7 5.9C141.1-7.2 153.3-16 167.1-16l113.9 0c13.8 0 26 8.8 30.4 21.9L320 32 416 32c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 96C14.3 96 0 81.7 0 64S14.3 32 32 32l96 0 8.7-26.1zM32 144l384 0 0 304c0 35.3-28.7 64-64 64L96 512c-35.3 0-64-28.7-64-64l0-304zm88 64c-13.3 0-24 10.7-24 24l0 192c0 13.3 10.7 24 24 24s24-10.7 24-24l0-192c0-13.3-10.7-24-24-24zm104 0c-13.3 0-24 10.7-24 24l0 192c0 13.3 10.7 24 24 24s24-10.7 24-24l0-192c0-13.3-10.7-24-24-24zm104 0c-13.3 0-24 10.7-24 24l0 192c0 13.3 10.7 24 24 24s24-10.7 24-24l0-192c0-13.3-10.7-24-24-24z"/></svg>'
CHECK_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="#cfcfcf" d="M434.8 70.1c14.3 10.4 17.5 30.4 7.1 44.7l-256 352c-5.5 7.6-14 12.3-23.4 13.1s-18.5-2.7-25.1-9.3l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l101.5 101.5 234-321.7c10.4-14.3 30.4-17.5 44.7-7.1z"/></svg>'
CHECK_GREEN_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="#40c977" d="M434.8 70.1c14.3 10.4 17.5 30.4 7.1 44.7l-256 352c-5.5 7.6-14 12.3-23.4 13.1s-18.5-2.7-25.1-9.3l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0l101.5 101.5 234-321.7c10.4-14.3 30.4-17.5 44.7-7.1z"/></svg>'
RESET_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#f0f0f0" d="M320 128C263.2 128 212.1 152.7 176.9 192L224 192C241.7 192 256 206.3 256 224C256 241.7 241.7 256 224 256L96 256C78.3 256 64 241.7 64 224L64 96C64 78.3 78.3 64 96 64C113.7 64 128 78.3 128 96L128 150.7C174.9 97.6 243.5 64 320 64C461.4 64 576 178.6 576 320C576 461.4 461.4 576 320 576C233 576 156.1 532.6 109.9 466.3C99.8 451.8 103.3 431.9 117.8 421.7C132.3 411.5 152.2 415.1 162.4 429.6C197.2 479.4 254.8 511.9 320 511.9C426 511.9 512 425.9 512 319.9C512 213.9 426 128 320 128z"/></svg>'
SCROLL_UP_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#6a6a6a" d="M355.2 85C348.2 72.1 334.7 64 320 64C305.3 64 291.8 72.1 284.8 85L68.8 485C62.1 497.4 62.4 512.4 69.6 524.5C76.8 536.6 89.9 544 104 544L536 544C550.1 544 563.1 536.6 570.4 524.5C577.7 512.4 577.9 497.4 571.2 485L355.2 85z"/></svg>'
SCROLL_DOWN_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="#6a6a6a" d="M284.8 555C291.8 567.9 305.3 576 320 576C334.7 576 348.2 567.9 355.2 555L571.2 155C577.9 142.6 577.6 127.6 570.4 115.5C563.2 103.4 550.1 96 536 96L104 96C89.9 96 76.9 103.4 69.6 115.5C62.3 127.6 62.1 142.6 68.8 155L284.8 555z"/></svg>'
CHECKBOX_CHECK_ICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="#cfcfcf" d="M6.3 12.2L2.7 8.6l1.1-1.1 2.5 2.5 5.9-5.9 1.1 1.1z"/></svg>'

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
    margin: 0px;
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
QToolButton#MiniButton[attention="true"] {
    background: #3e3210;
    border-color: #f2c94c;
}
QToolButton#MiniButton[attentionDanger="true"] {
    background: #3a1212;
    border-color: #be0420;
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
QPushButton#SearchClearButton[conversionLocked="true"],
QPushButton#TrashButton[conversionLocked="true"] {
    background: #1f1f1f;
    border-color: #2a2a2a;
    color: #7a7a7a;
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
QLineEdit#SearchInput[conversionLocked="true"] {
    color: #8b8b8b;
}
QListWidget#SearchResults {
    background: #1e1e1e;
    border: 1px solid #101010;
    border-radius: 4px;
    color: #f0f0f0;
    outline: none;
}
QListWidget#SearchResults[conversionLocked="true"],
QListWidget#SelectedResults[conversionLocked="true"] {
    background: #1a1a1a;
    border-color: #151515;
}
QTextEdit#ConversionLogs {
    background: #1e1e1e;
    border: 1px solid #101010;
    border-radius: 4px;
    outline: none;
    selection-background-color: __ACCENT_BG__;
    selection-color: #f0f0f0;
}
QListWidget#ConversionProgressList {
    background: #1e1e1e;
    border: 1px solid #101010;
    border-radius: 4px;
    outline: none;
}
QListWidget#ConversionProgressList::item {
    border: none;
    padding: 0px;
}
QFrame#ConversionProgressItem {
    background: #1e1e1e;
    border: none;
}
QLabel#ConversionProgressLabel {
    color: #f0f0f0;
}
QProgressBar#ConversionProgressBar {
    background: #1f1f1f;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    color: #f0f0f0;
    text-align: center;
    padding: 0px;
    margin: 0px;
}
QProgressBar#ConversionProgressBar[textDark="true"] {
    color: #101010;
}
QProgressBar#ConversionProgressBar::chunk {
    background: #026e0d;
    border-radius: 3px;
    margin: 0px;
}
QProgressBar#ConversionProgressBar[pending="true"]::chunk {
    background: #b88f00;
    border-radius: 3px;
    margin: 0px;
}
QProgressBar#ConversionProgressBar[failed="true"] {
    border: 1px solid #ff0000;
}
QListWidget#SearchResults::item {
    border: none;
    padding: 0 0 1px 0;
}
QListWidget#SearchResults::item:selected {
    background: transparent;
}
QFrame#SearchChartItem {
    background: transparent;
    border: 1px solid #5b6068;
    border-radius: 4px;
}
QFrame#SearchChartItem[conversionLocked="true"] {
    background: #1a1a1a;
}
QFrame#SearchChartItem[selected="true"] {
    background: __ACCENT_BG__;
    border: 1px solid __HISTORY_SELECTED_BORDER__;
    border-radius: 4px;
}
QFrame#SearchChartItem[selected="true"][conversionLocked="true"] {
    background: #4a2530;
    border: 1px solid __HISTORY_SELECTED_BORDER__;
    border-radius: 4px;
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
    padding: 0 0 1px 0;
}
QListWidget#HistoryRunsList,
QListWidget#HistoryDetailsList {
    background: #1e1e1e;
    border: 1px solid #101010;
    border-radius: 4px;
    color: #f0f0f0;
    outline: none;
}
QListWidget#HistoryRunsList::item,
QListWidget#HistoryDetailsList::item {
    border: none;
    padding: 0px;
}
QFrame#SelectedChartItem {
    background: #1e1e1e;
    border: 1px solid #5b6068;
    border-radius: 4px;
}
QFrame#SelectedChartItem[conversionLocked="true"] {
    background: #1a1a1a;
}
QFrame#SelectedChartItem[selected="true"] {
    background: __ACCENT_BG__;
    border: 1px solid __HISTORY_SELECTED_BORDER__;
    border-radius: 4px;
}
QFrame#SelectedChartItem[matched="true"] {
    background: __ACCENT_BG__;
    border: 1px solid __HISTORY_SELECTED_BORDER__;
    border-radius: 4px;
}
QFrame#SelectedChartItem[selected="true"][conversionLocked="true"],
QFrame#SelectedChartItem[matched="true"][conversionLocked="true"] {
    background: #4a2530;
    border: 1px solid __HISTORY_SELECTED_BORDER__;
    border-radius: 4px;
}
QFrame#SelectedChartItem[historyStatus="success"] {
    background: #013f06;
    border-left: 1px solid #1aa32a;
    border-right: 1px solid #1aa32a;
    border-bottom: 1px solid #1aa32a;
    border-top: 1px solid #1aa32a;
    border-radius: 4px;
}
QFrame#SelectedChartItem[historyStatus="failed"] {
    background: #2f0505;
    border-left: 1px solid #7a1414;
    border-right: 1px solid #7a1414;
    border-bottom: 1px solid #7a1414;
    border-top: 1px solid #7a1414;
    border-radius: 4px;
}
QFrame#SelectedChartItem[historyRun="true"] {
    border: 1px solid #5b6068;
    border-radius: 4px;
}
QFrame#SelectedChartItem[historyRun="true"][selected="true"] {
    border: 1px solid __HISTORY_SELECTED_BORDER__;
    border-radius: 4px;
}
QFrame#SelectedChartItem[chartEditingRow="true"] {
    border: 1px solid #5b6068;
    border-radius: 4px;
}
QFrame#SelectedChartItem[chartEditingRow="true"][selected="true"] {
    border: 1px solid __HISTORY_SELECTED_BORDER__;
    border-radius: 4px;
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
QPushButton#TrashButton[conversionLocked="true"]:hover,
QPushButton#TrashButton[conversionLocked="true"]:pressed {
    background: #1f1f1f;
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
QPushButton#SelectedResetButton[applyOffset="true"] {
    margin-top: 7px;
}
QLineEdit#ChartEditInput {
    background: #1e1e1e;
    border: 1px solid #3c3c3c;
    border-radius: 2px;
    color: #f0f0f0;
    min-height: 20px;
    max-height: 20px;
    padding: 0 6px 0 4px;
    selection-background-color: #3a3a3a;
    selection-color: #f0f0f0;
}
QLineEdit#ChartEditInput[textClipped="true"] {
    padding-left: 6px;
}
QLineEdit#ChartEditInput:focus {
    border: 1px solid #4d4d4d;
}
QLineEdit#ChartEditInput:disabled {
    background: #232323;
    border: 1px solid #363636;
    color: #9a9a9a;
}
QLineEdit#ChartEditInput[readOnly="true"] {
    background: #232323;
    border: 1px solid #363636;
    color: #9a9a9a;
}
QLabel#ChartEditPrefix {
    color: #dcdcdc;
}
QListWidget#SearchResults QScrollBar:vertical,
QListWidget#SelectedResults QScrollBar:vertical,
QListWidget#HistoryRunsList QScrollBar:vertical,
QListWidget#HistoryDetailsList QScrollBar:vertical,
QTextEdit#ConversionLogs QScrollBar:vertical,
QListWidget#ConversionProgressList QScrollBar:vertical {
    background: #1f1f1f;
    width: 10px;
    margin: 12px 1px 12px 1px;
    border: none;
    border-radius: 5px;
}
QListWidget#SearchResults QScrollBar::handle:vertical,
QListWidget#SelectedResults QScrollBar::handle:vertical,
QListWidget#HistoryRunsList QScrollBar::handle:vertical,
QListWidget#HistoryDetailsList QScrollBar::handle:vertical,
QTextEdit#ConversionLogs QScrollBar::handle:vertical,
QListWidget#ConversionProgressList QScrollBar::handle:vertical {
    background: #6a6a6a;
    min-height: 28px;
    border: none;
    border-radius: 4px;
    margin: 1px 0px;
}
QListWidget#SearchResults QScrollBar::handle:vertical:hover,
QListWidget#SelectedResults QScrollBar::handle:vertical:hover,
QListWidget#HistoryRunsList QScrollBar::handle:vertical:hover,
QListWidget#HistoryDetailsList QScrollBar::handle:vertical:hover,
QTextEdit#ConversionLogs QScrollBar::handle:vertical:hover,
QListWidget#ConversionProgressList QScrollBar::handle:vertical:hover {
    background: #6a6a6a;
}
QListWidget#SearchResults QScrollBar::add-line:vertical,
QListWidget#SelectedResults QScrollBar::add-line:vertical,
QListWidget#HistoryRunsList QScrollBar::add-line:vertical,
QListWidget#HistoryDetailsList QScrollBar::add-line:vertical,
QListWidget#SearchResults QScrollBar::sub-line:vertical,
QListWidget#SelectedResults QScrollBar::sub-line:vertical,
QListWidget#HistoryRunsList QScrollBar::sub-line:vertical,
QListWidget#HistoryDetailsList QScrollBar::sub-line:vertical,
QTextEdit#ConversionLogs QScrollBar::add-line:vertical,
QTextEdit#ConversionLogs QScrollBar::sub-line:vertical,
QListWidget#ConversionProgressList QScrollBar::add-line:vertical,
QListWidget#ConversionProgressList QScrollBar::sub-line:vertical {
    background: transparent;
    border: none;
    height: 12px;
    width: 10px;
    subcontrol-origin: margin;
}
QListWidget#SearchResults QScrollBar::sub-line:vertical,
QListWidget#SelectedResults QScrollBar::sub-line:vertical,
QListWidget#HistoryRunsList QScrollBar::sub-line:vertical,
QListWidget#HistoryDetailsList QScrollBar::sub-line:vertical,
QTextEdit#ConversionLogs QScrollBar::sub-line:vertical,
QListWidget#ConversionProgressList QScrollBar::sub-line:vertical {
    subcontrol-position: top;
}
QListWidget#SearchResults QScrollBar::add-line:vertical,
QListWidget#SelectedResults QScrollBar::add-line:vertical,
QListWidget#HistoryRunsList QScrollBar::add-line:vertical,
QListWidget#HistoryDetailsList QScrollBar::add-line:vertical,
QTextEdit#ConversionLogs QScrollBar::add-line:vertical,
QListWidget#ConversionProgressList QScrollBar::add-line:vertical {
    subcontrol-position: bottom;
}
QListWidget#SearchResults QScrollBar::up-arrow:vertical,
QListWidget#SelectedResults QScrollBar::up-arrow:vertical,
QListWidget#HistoryRunsList QScrollBar::up-arrow:vertical,
QListWidget#HistoryDetailsList QScrollBar::up-arrow:vertical,
QTextEdit#ConversionLogs QScrollBar::up-arrow:vertical,
QListWidget#ConversionProgressList QScrollBar::up-arrow:vertical {
    image: url("__SCROLL_UP_ICON__");
    width: 8px;
    height: 8px;
}
QListWidget#SearchResults QScrollBar::down-arrow:vertical,
QListWidget#SelectedResults QScrollBar::down-arrow:vertical,
QListWidget#HistoryRunsList QScrollBar::down-arrow:vertical,
QListWidget#HistoryDetailsList QScrollBar::down-arrow:vertical,
QTextEdit#ConversionLogs QScrollBar::down-arrow:vertical,
QListWidget#ConversionProgressList QScrollBar::down-arrow:vertical {
    image: url("__SCROLL_DOWN_ICON__");
    width: 8px;
    height: 8px;
}
QListWidget#SearchResults QScrollBar::add-page:vertical,
QListWidget#SelectedResults QScrollBar::add-page:vertical,
QListWidget#HistoryRunsList QScrollBar::add-page:vertical,
QListWidget#HistoryDetailsList QScrollBar::add-page:vertical,
QListWidget#SearchResults QScrollBar::sub-page:vertical,
QListWidget#SelectedResults QScrollBar::sub-page:vertical,
QListWidget#HistoryRunsList QScrollBar::sub-page:vertical,
QListWidget#HistoryDetailsList QScrollBar::sub-page:vertical,
QTextEdit#ConversionLogs QScrollBar::add-page:vertical,
QTextEdit#ConversionLogs QScrollBar::sub-page:vertical,
QListWidget#ConversionProgressList QScrollBar::add-page:vertical,
QListWidget#ConversionProgressList QScrollBar::sub-page:vertical {
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
QLineEdit#FilePathsInput:disabled {
    background: #252525;
    border: 1px solid #343434;
    color: #9a9a9a;
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
QPushButton#FilePathsBrowseButton:disabled {
    background: #252525;
    border: 1px solid #343434;
    color: #8a8a8a;
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
        if hint == QStyle.StyleHint.SH_ToolTip_FallAsleepDelay:
            return 0
        return QProxyStyle.styleHint(self, hint, option, widget, returnData)


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
        conversion_active: bool = False,
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

        def _display_path(path_value: str) -> str:
            return str(path_value or "").replace("/", "\\")

        sound_row = QWidget()
        sound_row_layout = QHBoxLayout(sound_row)
        sound_row_layout.setContentsMargins(0, 0, 0, 0)
        sound_row_layout.setSpacing(8)
        sound_label = QLabel("\\contents\\data\\sound\\")
        sound_label.setObjectName("FilePathsLabel")
        sound_label.setFixedWidth(140)
        self.sound_input = QLineEdit(_display_path(sound_path))
        self.sound_input.setObjectName("FilePathsInput")
        self.sound_browse_button = QPushButton("...")
        self.sound_browse_button.setObjectName("FilePathsBrowseButton")
        self.sound_browse_button.clicked.connect(lambda: self._pick_folder(self.sound_input))
        sound_row_layout.addWidget(sound_label)
        sound_row_layout.addWidget(self.sound_input, 1)
        sound_row_layout.addWidget(self.sound_browse_button)

        movie_row = QWidget()
        movie_row_layout = QHBoxLayout(movie_row)
        movie_row_layout.setContentsMargins(0, 0, 0, 0)
        movie_row_layout.setSpacing(8)
        movie_label = QLabel("\\contents\\data\\movie\\")
        movie_label.setObjectName("FilePathsLabel")
        movie_label.setFixedWidth(140)
        self.movie_input = QLineEdit(_display_path(movie_path))
        self.movie_input.setObjectName("FilePathsInput")
        self.movie_browse_button = QPushButton("...")
        self.movie_browse_button.setObjectName("FilePathsBrowseButton")
        self.movie_browse_button.clicked.connect(lambda: self._pick_folder(self.movie_input))
        movie_row_layout.addWidget(movie_label)
        movie_row_layout.addWidget(self.movie_input, 1)
        movie_row_layout.addWidget(self.movie_browse_button)

        results_row = QWidget()
        results_row_layout = QHBoxLayout(results_row)
        results_row_layout.setContentsMargins(0, 0, 0, 0)
        results_row_layout.setSpacing(8)
        results_label = QLabel("Output folder")
        results_label.setObjectName("FilePathsLabel")
        results_label.setFixedWidth(140)
        self.results_input = QLineEdit(_display_path(results_path))
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
        self.ok_button = QPushButton("OK")
        self.ok_button.setObjectName("FilePathsDialogButton")
        self.ok_button.setDefault(True)
        self.ok_button.setAutoDefault(True)
        self.ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("FilePathsDialogButton")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(cancel_button)

        root_layout.addWidget(sound_row)
        root_layout.addWidget(movie_row)
        root_layout.addWidget(results_row)
        root_layout.addWidget(buttons_row)
        self.setFixedWidth(660)
        self.sound_input.returnPressed.connect(self.accept)
        self.movie_input.returnPressed.connect(self.accept)
        self.results_input.returnPressed.connect(self.accept)

        if conversion_active:
            self.sound_input.setEnabled(False)
            self.movie_input.setEnabled(False)
            self.sound_browse_button.setEnabled(False)
            self.movie_browse_button.setEnabled(False)
            blocked_hint = "End conversion for edit paths"
            self.sound_input.setToolTip(blocked_hint)
            self.movie_input.setToolTip(blocked_hint)
            self.sound_browse_button.setToolTip(blocked_hint)
            self.movie_browse_button.setToolTip(blocked_hint)

    def _pick_folder(self, target_input: QLineEdit) -> None:
        start_dir = target_input.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select folder", start_dir)
        if folder:
            target_input.setText(folder.replace("/", "\\"))


class FirstRunSetupDialog(QDialog):
    def __init__(
        self,
        sound_path: str,
        movie_path: str,
        output_base_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("FilePathsDialog")
        self.setWindowTitle("Welcome")
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

        def _display_path(path_value: str) -> str:
            return str(path_value or "").replace("/", "\\")

        title_label = QLabel("Hello ! It's iidx2bms")
        title_label.setObjectName("ConfirmMessage")
        subtitle_label = QLabel("Tools for converting iidx charts to bms charts")
        subtitle_label.setObjectName("ConfirmMessage")
        hint_label = QLabel("Choose your paths to iidx files before use iidx2bms")
        hint_label.setObjectName("ConfirmMessage")
        root_layout.addWidget(title_label)
        root_layout.addWidget(subtitle_label)
        root_layout.addWidget(hint_label)

        sound_row = QWidget()
        sound_row_layout = QHBoxLayout(sound_row)
        sound_row_layout.setContentsMargins(0, 0, 0, 0)
        sound_row_layout.setSpacing(8)
        sound_label = QLabel("\\contents\\data\\sound\\")
        sound_label.setObjectName("FilePathsLabel")
        sound_label.setFixedWidth(140)
        self.sound_input = QLineEdit(_display_path(sound_path))
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
        movie_label = QLabel("\\contents\\data\\movie\\")
        movie_label.setObjectName("FilePathsLabel")
        movie_label.setFixedWidth(140)
        self.movie_input = QLineEdit(_display_path(movie_path))
        self.movie_input.setObjectName("FilePathsInput")
        movie_browse = QPushButton("...")
        movie_browse.setObjectName("FilePathsBrowseButton")
        movie_browse.clicked.connect(lambda: self._pick_folder(self.movie_input))
        movie_row_layout.addWidget(movie_label)
        movie_row_layout.addWidget(self.movie_input, 1)
        movie_row_layout.addWidget(movie_browse)

        output_row = QWidget()
        output_row_layout = QHBoxLayout(output_row)
        output_row_layout.setContentsMargins(0, 0, 0, 0)
        output_row_layout.setSpacing(8)
        output_label = QLabel("Output folder")
        output_label.setObjectName("FilePathsLabel")
        output_label.setFixedWidth(140)
        self.output_input = QLineEdit(_display_path(output_base_path))
        self.output_input.setObjectName("FilePathsInput")
        output_browse = QPushButton("...")
        output_browse.setObjectName("FilePathsBrowseButton")
        output_browse.clicked.connect(lambda: self._pick_folder(self.output_input))
        output_row_layout.addWidget(output_label)
        output_row_layout.addWidget(self.output_input, 1)
        output_row_layout.addWidget(output_browse)

        self.continue_button = QPushButton()
        self.continue_button.setObjectName("FilePathsDialogButton")
        self.continue_button.clicked.connect(self.accept)
        self.sound_input.textChanged.connect(self._update_button_text)
        self.movie_input.textChanged.connect(self._update_button_text)

        buttons_row = QWidget()
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 6, 0, 0)
        buttons_layout.setSpacing(8)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.continue_button)

        root_layout.addWidget(sound_row)
        root_layout.addWidget(movie_row)
        root_layout.addWidget(output_row)
        root_layout.addWidget(buttons_row)
        self._update_button_text()
        self.setFixedWidth(760)

    def _has_required_paths(self) -> bool:
        return bool(self.sound_input.text().strip()) and bool(self.movie_input.text().strip())

    def should_apply_paths(self) -> bool:
        return self._has_required_paths()

    def _update_button_text(self) -> None:
        if self._has_required_paths():
            self.continue_button.setText("Apply and continue")
        else:
            self.continue_button.setText("Skip and specify paths later")

    def _pick_folder(self, target_input: QLineEdit) -> None:
        start_dir = target_input.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select folder", start_dir)
        if folder:
            target_input.setText(folder.replace("/", "\\"))


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
        buttons_layout.setContentsMargins(0, 8, 0, 0)
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


class ActionInfoDialog(QDialog):
    def __init__(self, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("FilePathsDialog")
        self.setWindowTitle("Info")
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

        ok_button = QPushButton("OK")
        ok_button.setObjectName("ConfirmButton")
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)
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
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

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
        self._hide_copy_hint()
        hint = HoverHint("Click to copy version")
        hint.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        hint.adjustSize()
        x = button.width() + 8
        y = max(0, (button.height() - hint.height()) // 2)
        hint.move(button.mapToGlobal(QPoint(x, y)))
        hint.show()
        hint.raise_()
        self._hover_hint = hint

    def _hide_copy_hint(self) -> None:
        if self._hover_hint is None:
            return
        self._hover_hint.close()
        self._hover_hint = None

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
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
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

    def contextMenuEvent(self, event) -> None:
        event.ignore()


class AnchoredLineEdit(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setProperty("textClipped", False)
        self.cursorPositionChanged.connect(self._sync_input_method)
        self.textEdited.connect(self._sync_input_method)
        self.selectionChanged.connect(self._sync_input_method)
        self.textChanged.connect(self._update_clipped_padding)

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
        super().keyPressEvent(event)
        QTimer.singleShot(0, self._sync_input_method)
        QTimer.singleShot(0, self._update_clipped_padding)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._update_clipped_padding)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._update_clipped_padding)

    def _update_clipped_padding(self) -> None:
        text = self.text()
        if not text:
            clipped = False
        else:
            text_width = self.fontMetrics().horizontalAdvance(text)
            clipped = text_width > max(0, self.width() - 14)
        previous = bool(self.property("textClipped"))
        if previous == clipped:
            return
        self.setProperty("textClipped", clipped)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def contextMenuEvent(self, event) -> None:
        event.ignore()


class SmoothListWidget(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self._scroll_pos = 0.0
        self._scroll_target = 0.0
        self._wheel_step_px = 52
        self._scroll_clock = QElapsedTimer()
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._scroll_timer.setInterval(0)
        self._scroll_timer.timeout.connect(self._animate_scroll)

    def set_wheel_step_px(self, value: int) -> None:
        self._wheel_step_px = max(1, int(value))

    def wheelEvent(self, event) -> None:
        delta = event.pixelDelta().y()
        if delta == 0:
            angle = event.angleDelta().y()
            if angle == 0:
                super().wheelEvent(event)
                return
            steps = angle / 120.0
            delta = int(steps * self._wheel_step_px)

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


class SmoothTextEdit(QTextEdit):
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
        self._hover_hint: HoverHint | None = None
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
        if self._overflow and self._is_overflow_hint_enabled():
            self._show_overflow_hint()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._timer.stop()
        self._offset = 0
        self._hide_overflow_hint()
        self.update()
        super().leaveEvent(event)

    def _update_overflow_state(self) -> None:
        text_width = self.fontMetrics().horizontalAdvance(self._full_text)
        self._overflow = text_width > self.contentsRect().width()
        self.setToolTip("")
        if not self._overflow:
            self._timer.stop()
            self._offset = 0
            self._hide_overflow_hint()
        elif self._hovered and not self._timer.isActive():
            self._timer.start()
        self.update()

    def _show_overflow_hint(self) -> None:
        if not self._is_overflow_hint_enabled():
            return
        self._hide_overflow_hint()
        hint = HoverHint(self._full_text)
        hint.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        hint.adjustSize()
        x = max(0, (self.width() - hint.width()) // 2)
        y = self.height() + 4
        hint.move(self.mapToGlobal(QPoint(x, y)))
        hint.show()
        hint.raise_()
        self._hover_hint = hint

    def _is_overflow_hint_enabled(self) -> bool:
        return not bool(self.property("conversionLocked"))

    def _hide_overflow_hint(self) -> None:
        if self._hover_hint is None:
            return
        self._hover_hint.close()
        self._hover_hint = None

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
                self.signals.progress.emit(
                    f"Start: {result.song_id_display}"
                )
                last_percent = -1

                def _on_chart_progress(percent: int, stage: str) -> None:
                    nonlocal last_percent
                    bounded = min(100, max(0, int(percent)))
                    if bounded == last_percent:
                        return
                    last_percent = bounded
                    self.signals.progress.emit(
                        f"Progress: {result.song_id_display}|{bounded}|{stage}"
                    )

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
                    progress_callback=_on_chart_progress,
                )
                succeeded += 1
                self.signals.progress.emit(
                    f"Done: {result.song_id_display} -> {output_dir}"
                )
            except Exception as error:
                failed += 1
                self.signals.progress.emit(
                    f"Failed: {result.song_id_display}: {error}"
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
        self._active_popup_button: QWidget | None = None
        self._global_hover_hint: HoverHint | None = None
        self._tooltip_filter_active = False
        self._global_hover_hint_closing = False
        self._search_input: SearchLineEdit | None = None
        self._search_results: QListWidget | None = None
        self._conversion_logs_results: QTextEdit | None = None
        self._conversion_progress_list: QListWidget | None = None
        self._conversion_progress_gap: QWidget | None = None
        self._conversion_progress_bars: dict[str, QProgressBar] = {}
        self._chart_editing_results: QListWidget | None = None
        self._chart_editing_panel: QFrame | None = None
        self._chart_editing_body: QFrame | None = None
        self._chart_editing_status_label: QLabel | None = None
        self._chart_editing_reset_button: QPushButton | None = None
        self._chart_editing_reset_placeholder: QWidget | None = None
        self._chart_editing_continue_button: QPushButton | None = None
        self._chart_editing_remywiki_button: QPushButton | None = None
        self._chart_editing_buttons_row: QWidget | None = None
        self._chart_editing_buttons_row_anim: QPropertyAnimation | None = None
        self._chart_editing_bottom_gap: QWidget | None = None
        self._chart_editing_bottom_gap_anim: QPropertyAnimation | None = None
        self._chart_edit_selected_widget: QWidget | None = None
        self._chart_edit_selected_song_id: int | None = None
        self._history_previous_results: QListWidget | None = None
        self._history_details_results: QListWidget | None = None
        self._history_clear_button: QPushButton | None = None
        self._history_add_to_selected_button: QPushButton | None = None
        self._history_runs: list[ConversionHistoryRun] = []
        self._history_selected_widget: QWidget | None = None
        self._history_store = ConversionHistoryStore()
        self._history_recorder = ConversionSessionRecorder(self._history_store)
        self._chart_editing_attention_on = False
        self._chart_editing_attention_timer = QTimer(self)
        self._chart_editing_attention_timer.setInterval(360)
        self._chart_editing_attention_timer.timeout.connect(self._toggle_chart_editing_attention)
        self._chart_name_overrides: dict[int, dict[str, str]] = {}
        self._chart_editing_mode = "names"
        self._playlevel_missing_entries: dict[int, list[dict[str, str]]] = {}
        self._playlevel_source_results: dict[int, SearchResult] = {}
        self._playlevel_value_overrides: dict[str, str] = {}
        self._playlevel_pending_song_ids: set[str] = set()
        self._saved_diff_numbers_cache: dict[str, dict[str, str]] = {}
        self._saved_diff_numbers_cache_loaded = False
        self._saved_diff_numbers_cache_exists = False
        self._saved_diff_numbers_cache_mtime_ns: int | None = None
        self._saved_diff_numbers_watcher = QFileSystemWatcher(self)
        self._saved_diff_numbers_watcher.fileChanged.connect(self._on_saved_diff_numbers_fs_changed)
        self._saved_diff_numbers_watcher.directoryChanged.connect(self._on_saved_diff_numbers_fs_changed)
        self._pending_conversion_context: dict[str, object] | None = None
        self._awaiting_chart_editing_action = False
        self._page_stack: QStackedWidget | None = None
        self._top_bar: QWidget | None = None
        self._top_separator: QFrame | None = None
        self._main_page_button: QToolButton | None = None
        self._processing_page_button: QToolButton | None = None
        self._history_page_button: QToolButton | None = None
        self._welcome_sound_input: QLineEdit | None = None
        self._welcome_movie_input: QLineEdit | None = None
        self._welcome_output_input: QLineEdit | None = None
        self._welcome_continue_button: QPushButton | None = None
        self._main_page_index = 0
        self._processing_page_index = 1
        self._history_page_index = 2
        self._search_item_by_song_id: dict[int, QListWidgetItem] = {}
        self._search_selected_song_id: int | None = None
        self._pending_restore_search_song_id: int | None = None
        self._search_selected_widget: QWidget | None = None
        self._selected_results: QListWidget | None = None
        self._selected_item_by_song_id: dict[int, QListWidgetItem] = {}
        self._matched_selected_song_id: int | None = None
        self._selected_song_ids: set[int] = set()
        self._selected_reset_button: QPushButton | None = None
        self._search_clear_button: QPushButton | None = None
        self._start_conversion_button: QPushButton | None = None
        self._include_stagefile_checkbox: QCheckBox | None = None
        self._include_preview_checkbox: QCheckBox | None = None
        self._include_bga_checkbox: QCheckBox | None = None
        self._conversion_active = False
        self._active_conversion_workers: list[ConversionWorker] = []
        self._pending_conversion_jobs = 0
        self._conversion_succeeded_total = 0
        self._conversion_failed_total = 0
        self._conversion_output_dirs: dict[str, Path] = {}
        self._conversion_chart_by_id_display: dict[str, SearchResult] = {}
        self._non_standard_charts_found = False
        self._level_line_cache: dict[tuple[str, int, int, int, int, int], str] = {}
        self._settings = QSettings("Glebsin", "iidx2bms")
        self._show_chart_difficulty = bool(
            self._settings.value("ui/show_chart_difficulty", True, bool)
        )
        self._show_game_version = bool(
            self._settings.value("ui/show_game_version", True, bool)
        )
        self._show_chart_genre = bool(
            self._settings.value("ui/show_chart_genre", True, bool)
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
        self._open_results_after_conversion = bool(
            self._settings.value("conversion/open_results_after_conversion", False, bool)
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
        self._save_missing_difficulty_numbers = bool(
            self._settings.value("conversion/save_missing_difficulty_numbers", False, bool)
        )
        self._sound_path = str(self._settings.value("paths/sound", "", str) or "")
        self._movie_path = str(self._settings.value("paths/movie", "", str) or "")
        self._output_base_path = self._load_output_base_path()
        self._search_request_id = 0
        self._search_limit = 120
        data_path = Path(__file__).resolve().parent.parent / "music_data" / "music_data.json"
        self._bga_by_song_id = self._load_bga_map(data_path)
        self._search_engine = SearchEngine(data_path)
        self._search_engine.set_include_levels(self._show_chart_difficulty)
        self._search_engine.set_include_game_version(self._show_game_version)
        self._search_engine.set_include_genre(self._show_chart_genre)
        self._search_pool = QThreadPool.globalInstance()
        self._search_pool.setMaxThreadCount(self._search_engine.cpu_budget)
        self._conversion_pool = QThreadPool(self)
        self._conversion_pool.setMaxThreadCount(1)
        self._build_ui()
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._refresh_saved_diff_numbers_watcher()
        restore_window_placement(self, self._settings)
        self._update_conversion_inputs_locked_state()
        QTimer.singleShot(0, self._maybe_show_first_run_setup)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._update_conversion_progress_row_widths)

    def closeEvent(self, event) -> None:
        save_window_placement(self, self._settings)
        super().closeEvent(event)

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
        history_page_button = self._make_nav_button(
            "Conversion history", self._show_history_page
        )
        self._main_page_button = main_page_button
        self._processing_page_button = processing_page_button
        self._history_page_button = history_page_button
        top_layout.addWidget(main_page_button)
        top_layout.addWidget(processing_page_button)
        top_layout.addWidget(history_page_button)
        top_layout.addWidget(
            self._make_menu_button(
                "Settings",
                self._settings_menu_items(),
                self._on_popup_action,
            )
        )
        ui_version = QApplication.instance().applicationVersion().strip() or APP_VERSION
        top_layout.addWidget(
            self._make_menu_button(
                "About",
                [
                    ("iidx2bms GitHub page", "https://github.com/Glebsin/iidx2bms/"),
                    (f"Version: {ui_version}", f"copy:{ui_version}"),
                ],
            )
        )
        top_layout.addStretch(1)
        self._top_bar = top_bar

        top_separator = QFrame()
        top_separator.setObjectName("TopSeparator")
        self._top_separator = top_separator

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
        welcome_page = self._build_first_run_page()
        history_ui = build_conversion_history_page(SmoothListWidget)
        history_page = history_ui.page
        self._history_previous_results = history_ui.previous_conversions
        self._history_details_results = history_ui.conversion_details
        self._history_clear_button = history_ui.clear_history_button
        self._history_add_to_selected_button = history_ui.add_to_selected_button
        self._history_clear_button.clicked.connect(self._on_clear_history_clicked)
        self._history_add_to_selected_button.clicked.connect(self._on_add_history_run_to_selected_clicked)
        self._history_previous_results.currentItemChanged.connect(
            lambda current, previous: self._on_history_run_selected(current)
        )
        page_stack.addWidget(welcome_page)
        self._main_page_index = page_stack.addWidget(panels_row)
        self._processing_page_index = page_stack.addWidget(processing_panels_row)
        self._history_page_index = page_stack.addWidget(history_page)
        self._page_stack = page_stack
        content_layout.addWidget(page_stack, 1)

        root_layout.addWidget(top_bar, 0, Qt.AlignmentFlag.AlignTop)
        root_layout.addWidget(top_separator)
        root_layout.addWidget(content_area, 1)
        self.setCentralWidget(root)
        self._show_main_page()
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()
        self._reload_conversion_history()

    def _build_first_run_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 24, 0, 24)
        layout.setSpacing(0)

        title = QLabel("Hello ! It's iidx2bms")
        title.setObjectName("PanelTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = title.font()
        title_font.setPointSize(21)
        title.setFont(title_font)

        subtitle = QLabel("Tools for converting iidx charts to bms charts")
        subtitle.setObjectName("PanelTitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = subtitle.font()
        subtitle_font.setPointSize(17)
        subtitle.setFont(subtitle_font)

        desc = QLabel("Choose your paths to iidx files before use iidx2bms")
        desc.setObjectName("PanelTitle")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_font = desc.font()
        desc_font.setPointSize(17)
        desc.setFont(desc_font)

        form_wrap = QWidget()
        form_layout = QGridLayout(form_wrap)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(8)
        form_layout.setVerticalSpacing(8)
        form_wrap.setFixedWidth(760)

        sound_label = QLabel("\\contents\\data\\sound\\")
        sound_label.setObjectName("FilePathsLabel")
        self._welcome_sound_input = QLineEdit(str(self._sound_path or "").replace("/", "\\"))
        self._welcome_sound_input.setObjectName("FilePathsInput")
        self._welcome_sound_input.setMinimumWidth(560)
        sound_browse = QPushButton("...")
        sound_browse.setObjectName("FilePathsBrowseButton")
        sound_browse.clicked.connect(
            lambda: self._pick_folder_into_line_edit(self._welcome_sound_input)
        )

        movie_label = QLabel("\\contents\\data\\movie\\")
        movie_label.setObjectName("FilePathsLabel")
        self._welcome_movie_input = QLineEdit(str(self._movie_path or "").replace("/", "\\"))
        self._welcome_movie_input.setObjectName("FilePathsInput")
        self._welcome_movie_input.setMinimumWidth(560)
        movie_browse = QPushButton("...")
        movie_browse.setObjectName("FilePathsBrowseButton")
        movie_browse.clicked.connect(
            lambda: self._pick_folder_into_line_edit(self._welcome_movie_input)
        )

        output_label = QLabel("Output folder")
        output_label.setObjectName("FilePathsLabel")
        self._welcome_output_input = QLineEdit(str(self._output_base_path or "").replace("/", "\\"))
        self._welcome_output_input.setObjectName("FilePathsInput")
        self._welcome_output_input.setMinimumWidth(560)
        output_browse = QPushButton("...")
        output_browse.setObjectName("FilePathsBrowseButton")
        output_browse.clicked.connect(
            lambda: self._pick_folder_into_line_edit(self._welcome_output_input)
        )

        form_layout.addWidget(sound_label, 0, 0)
        form_layout.addWidget(self._welcome_sound_input, 0, 1)
        form_layout.addWidget(sound_browse, 0, 2)
        form_layout.addWidget(movie_label, 1, 0)
        form_layout.addWidget(self._welcome_movie_input, 1, 1)
        form_layout.addWidget(movie_browse, 1, 2)
        form_layout.addWidget(output_label, 2, 0)
        form_layout.addWidget(self._welcome_output_input, 2, 1)
        form_layout.addWidget(output_browse, 2, 2)

        form_layout.setColumnStretch(1, 1)

        self._welcome_continue_button = QPushButton("Skip and specify paths later")
        self._welcome_continue_button.setObjectName("FilePathsDialogButton")
        self._welcome_continue_button.clicked.connect(self._on_first_run_continue_clicked)

        self._welcome_sound_input.textChanged.connect(self._update_first_run_continue_button_text)
        self._welcome_movie_input.textChanged.connect(self._update_first_run_continue_button_text)

        layout.addWidget(title)
        layout.addSpacing(18)
        layout.addWidget(subtitle)
        layout.addSpacing(64)
        layout.addWidget(desc)
        layout.addSpacing(54)
        layout.addWidget(form_wrap, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        layout.addWidget(self._welcome_continue_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(24)
        self._update_first_run_continue_button_text()
        return page

    def _search_icon_pixmap(self, size: int = 12) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(SEARCH_ICON_SVG))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return pixmap

    def _clear_icon_pixmap(self, size: int = 16) -> QPixmap:
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
            reset_button.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
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
        body_layout.setContentsMargins(8, 11, 8, 5)
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
            selected_results.setSpacing(0)
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
            include_stagefile_checkbox.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
            include_stagefile_checkbox.setChecked(self._include_stagefile)
            include_stagefile_checkbox.toggled.connect(self._on_include_stagefile_toggled)
            self._include_stagefile_checkbox = include_stagefile_checkbox

            include_preview_checkbox = QCheckBox("Include preview_auto_generator.wav")
            include_preview_checkbox.setObjectName("ConversionOptionCheck")
            include_preview_checkbox.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
            include_preview_checkbox.setChecked(self._include_preview)
            include_preview_checkbox.toggled.connect(self._on_include_preview_toggled)
            self._include_preview_checkbox = include_preview_checkbox

            include_bga_checkbox = QCheckBox("Include BGA")
            include_bga_checkbox.setObjectName("ConversionOptionCheck")
            include_bga_checkbox.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)
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
            # Move only the search row up by 3px while keeping results list position.
            body_layout.setContentsMargins(8, 8, 8, 5)
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
            clear_button.setIcon(QIcon(self._clear_icon_pixmap(16)))
            clear_button.setIconSize(QSize(16, 16))
            clear_button.clicked.connect(self._on_clear_search_clicked)
            self._search_clear_button = clear_button
            search_layout.addWidget(clear_button, 0, Qt.AlignmentFlag.AlignVCenter)

            results = SmoothListWidget()
            results.setObjectName("SearchResults")
            results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            results.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            results.setWordWrap(True)
            results.setUniformItemSizes(True)
            results.setSpacing(0)

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
            body_layout.addSpacing(8)
            body_layout.addWidget(results, 1)
            body_layout.addSpacing(3)

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

        logs_list = SmoothTextEdit()
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
        progress_list = SmoothListWidget()
        progress_list.setObjectName("ConversionProgressList")
        progress_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        progress_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        progress_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        progress_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        progress_list.setUniformItemSizes(False)
        progress_list.setSpacing(0)
        progress_list.setViewportMargins(0, 4, 0, 4)
        progress_list.set_wheel_step_px(26)
        progress_list.installEventFilter(self)
        progress_list.viewport().installEventFilter(self)
        progress_list.setVisible(False)
        self._conversion_progress_list = progress_list
        progress_gap = QWidget()
        progress_gap.setFixedHeight(8)
        progress_gap.setVisible(False)
        self._conversion_progress_gap = progress_gap
        body_layout.addWidget(progress_list, 0)
        body_layout.addWidget(progress_gap, 0)
        body_layout.addWidget(logs_list, 1)
        body_layout.addSpacing(12)

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
        body_layout.addSpacing(4)

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
        header_layout.setContentsMargins(16, 6, 2, 7)
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

        remywiki_button = QPushButton("Open on RemyWiki")
        remywiki_button.setObjectName("PanelActionButton")
        remywiki_button.setCursor(Qt.CursorShape.PointingHandCursor)
        remywiki_button.clicked.connect(self._on_open_remywiki_clicked)
        remywiki_width = remywiki_button.fontMetrics().horizontalAdvance("Open on RemyWiki") + 16
        remywiki_button.setFixedSize(remywiki_width, 22)
        remywiki_button.setVisible(False)
        self._chart_editing_remywiki_button = remywiki_button
        remywiki_wrap = QWidget()
        remywiki_wrap_layout = QVBoxLayout(remywiki_wrap)
        remywiki_wrap_layout.setContentsMargins(0, 1, 0, 0)  # keep 1px down offset
        remywiki_wrap_layout.setSpacing(0)
        remywiki_wrap_layout.addWidget(remywiki_button, 0, Qt.AlignmentFlag.AlignTop)
        header_layout.addSpacing(6)  # move button block right by 6px
        header_layout.addWidget(remywiki_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        reset_button = QPushButton()
        reset_button.setObjectName("SelectedResetButton")
        reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_button.setToolTip("Reset edited fields")
        reset_button.setIcon(QIcon(self._reset_icon_pixmap(14)))
        reset_button.setIconSize(QSize(14, 14))
        reset_button.setFixedSize(28, 28)
        reset_button.setVisible(False)
        reset_button.clicked.connect(self._on_reset_chart_editing_names_clicked)
        self._chart_editing_reset_button = reset_button

        reset_placeholder = QWidget()
        reset_placeholder.setFixedSize(28, 28)
        reset_placeholder.setVisible(False)
        self._chart_editing_reset_placeholder = reset_placeholder
        header_layout.addWidget(reset_button, 0, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addSpacing(6)

        continue_button = QPushButton("Skip editing and continue conversion")
        continue_button.setObjectName("HeaderTextButton")
        continue_button.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_button.setIcon(QIcon(self._green_check_icon_pixmap(11)))
        continue_button.setIconSize(QSize(11, 11))
        continue_button.setFixedHeight(22)
        continue_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        continue_button_texts = (
            "Apply and finalize conversion",
            "Apply and continue conversion",
            "Skip editing and continue conversion",
        )
        current_continue_text = continue_button.text()
        continue_button_fixed_width = continue_button.sizeHint().width()
        for text in continue_button_texts:
            continue_button.setText(text)
            continue_button_fixed_width = max(continue_button_fixed_width, continue_button.sizeHint().width())
        continue_button.setText(current_continue_text)
        continue_button.setFixedWidth(continue_button_fixed_width)
        continue_button.clicked.connect(self._on_chart_editing_continue_clicked)
        continue_button.setVisible(False)
        self._chart_editing_continue_button = continue_button

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
        editing_list.setSpacing(0)
        editing_list.setLayoutMode(QListView.LayoutMode.Batched)
        editing_list.setBatchSize(64)
        editing_list.viewport().installEventFilter(self)
        editing_list.currentItemChanged.connect(
            lambda current, previous: self._on_chart_editing_current_item_changed(current)
        )
        self._chart_editing_results = editing_list
        body_layout.addWidget(editing_list, 1)

        bottom_gap = QWidget()
        bottom_gap.setMinimumHeight(0)
        bottom_gap.setMaximumHeight(0)
        bottom_gap.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        bottom_gap.setVisible(False)
        self._chart_editing_bottom_gap = bottom_gap
        self._chart_editing_bottom_gap_anim = QPropertyAnimation(bottom_gap, b"maximumHeight", self)
        self._chart_editing_bottom_gap_anim.setDuration(180)
        self._chart_editing_bottom_gap_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._chart_editing_bottom_gap_anim.valueChanged.connect(self._on_chart_editing_bottom_gap_anim_value_changed)
        self._chart_editing_bottom_gap_anim.finished.connect(self._on_chart_editing_bottom_gap_anim_finished)
        body_layout.addWidget(bottom_gap, 0)

        buttons_row = QWidget()
        buttons_row.setMinimumHeight(0)
        buttons_row.setMaximumHeight(0)
        buttons_row.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        buttons_layout = QHBoxLayout(buttons_row)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        buttons_row.setVisible(False)
        self._chart_editing_buttons_row = buttons_row
        self._chart_editing_buttons_row_anim = QPropertyAnimation(buttons_row, b"maximumHeight", self)
        self._chart_editing_buttons_row_anim.setDuration(180)
        self._chart_editing_buttons_row_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._chart_editing_buttons_row_anim.valueChanged.connect(self._on_chart_editing_buttons_row_anim_value_changed)
        self._chart_editing_buttons_row_anim.finished.connect(self._on_chart_editing_buttons_row_anim_finished)

        buttons_layout.addStretch(1)
        buttons_layout.addWidget(
            reset_placeholder,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        buttons_layout.addWidget(
            reset_button,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        buttons_layout.addWidget(
            continue_button,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        body_layout.addWidget(buttons_row, 0)

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
            base_result = result
            display_result = result
            if self._show_chart_difficulty:
                base_result = self._search_engine.ensure_levels(base_result)
                display_result = self._apply_saved_levels_to_result(base_result)
            if self._show_chart_genre:
                base_result = self._search_engine.ensure_genre(base_result)
                display_result = self._search_engine.ensure_genre(display_result)
            if self._show_game_version:
                if not base_result.game_name:
                    base_result = self._search_engine.ensure_game_name(base_result)
                if not display_result.game_name:
                    display_result = self._search_engine.ensure_game_name(display_result)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, display_result)
            item.setData(Qt.ItemDataRole.UserRole + 2, base_result)
            self._search_results.addItem(item)
            self._search_item_by_song_id[result.song_id] = item
            widget = self._build_search_result_widget(display_result)
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
            ("Open results folder after conversion", "action:toggle_open_results_after_conversion"),
            ("Parallel converting", "action:toggle_parallel_converting"),
            ("Show chart difficulty", "action:toggle_chart_difficulty"),
            ("Show game version", "action:toggle_game_version"),
            ("Show chart genre", "action:toggle_chart_genre"),
            ("Save missing difficulty numbers", "action:toggle_save_missing_difficulty_numbers"),
            ("Reset all settings and restart", "action:reset_all_settings_restart"),
        ]

    def _on_popup_action(self, action: str) -> None:
        if action == "file_paths":
            self._open_file_paths_dialog()
        elif action == "toggle_fully_overwrite_results":
            self._toggle_fully_overwrite_results()
        elif action == "toggle_always_skip_chart_names_editing":
            self._toggle_always_skip_chart_names_editing()
        elif action == "toggle_open_results_after_conversion":
            self._toggle_open_results_after_conversion()
        elif action == "toggle_parallel_converting":
            self._toggle_parallel_converting()
        elif action == "toggle_chart_difficulty":
            self._toggle_chart_difficulty()
        elif action == "toggle_game_version":
            self._toggle_game_version()
        elif action == "toggle_chart_genre":
            self._toggle_chart_genre()
        elif action == "toggle_save_missing_difficulty_numbers":
            self._toggle_save_missing_difficulty_numbers()
        elif action == "reset_all_settings_restart":
            self._reset_all_settings_and_restart()

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
        if action == "toggle_open_results_after_conversion":
            return self._open_results_after_conversion
        if action == "toggle_save_missing_difficulty_numbers":
            return self._save_missing_difficulty_numbers
        return False

    def _open_file_paths_dialog(self) -> None:
        dialog = FilePathsDialog(
            self._sound_path,
            self._movie_path,
            self._output_base_path,
            conversion_active=(self._conversion_active or self._awaiting_chart_editing_action),
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._save_file_paths(
                dialog.sound_input.text(),
                dialog.movie_input.text(),
                dialog.results_input.text(),
            )

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _default_output_base_path(self) -> Path:
        if getattr(sys, "frozen", False):
            executable = getattr(sys, "executable", "")
            if executable:
                return Path(executable).resolve().parent
        return self._project_root()

    def _resolve_saved_diff_numbers_path(self) -> Path:
        if getattr(sys, "frozen", False):
            executable = getattr(sys, "executable", "")
            if executable:
                return Path(executable).resolve().parent / "saved_diff_numbers.json"
        return Path(sys.argv[0]).resolve().parent / "saved_diff_numbers.json"

    def _invalidate_saved_diff_numbers_cache(self) -> None:
        self._saved_diff_numbers_cache = {}
        self._saved_diff_numbers_cache_loaded = False
        self._saved_diff_numbers_cache_exists = False
        self._saved_diff_numbers_cache_mtime_ns = None

    def _refresh_saved_diff_numbers_watcher(self) -> None:
        path = self._resolve_saved_diff_numbers_path()
        watch_dir = str(path.parent)
        watch_file = str(path)
        existing_paths = self._saved_diff_numbers_watcher.files() + self._saved_diff_numbers_watcher.directories()
        if existing_paths:
            self._saved_diff_numbers_watcher.removePaths(existing_paths)
        if path.parent.exists():
            self._saved_diff_numbers_watcher.addPath(watch_dir)
        if path.is_file():
            self._saved_diff_numbers_watcher.addPath(watch_file)

    def _on_saved_diff_numbers_fs_changed(self, _changed_path: str) -> None:
        self._invalidate_saved_diff_numbers_cache()
        self._refresh_saved_diff_numbers_watcher()
        self._refresh_search_result_widgets()
        self._refresh_selected_result_widgets()

    def _get_saved_diff_numbers_data(self) -> dict[str, dict[str, str]]:
        if not self._save_missing_difficulty_numbers:
            return {}
        path = self._resolve_saved_diff_numbers_path()
        file_exists = path.is_file()
        mtime_ns: int | None = None
        if file_exists:
            try:
                mtime_ns = path.stat().st_mtime_ns
            except Exception:
                file_exists = False
                mtime_ns = None
        if (
            self._saved_diff_numbers_cache_loaded
            and self._saved_diff_numbers_cache_exists == file_exists
            and self._saved_diff_numbers_cache_mtime_ns == mtime_ns
        ):
            return self._saved_diff_numbers_cache

        self._saved_diff_numbers_cache_loaded = True
        self._saved_diff_numbers_cache = {}
        self._saved_diff_numbers_cache_exists = file_exists
        self._saved_diff_numbers_cache_mtime_ns = mtime_ns
        if not file_exists:
            return self._saved_diff_numbers_cache
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return self._saved_diff_numbers_cache
        if not isinstance(payload, dict):
            return self._saved_diff_numbers_cache

        loaded: dict[str, dict[str, str]] = {}
        for song_id_display, raw_entries in payload.items():
            key = str(song_id_display).strip()
            if not key or not isinstance(raw_entries, dict):
                continue
            row: dict[str, str] = {}
            for file_name, raw_value in raw_entries.items():
                file_key = str(file_name).strip()
                if not file_key:
                    continue
                value = str(raw_value or "").strip()
                if value.isdigit():
                    row[file_key] = value[:2]
            if row:
                loaded[key] = row
        self._saved_diff_numbers_cache = loaded
        return self._saved_diff_numbers_cache

    def _write_saved_diff_numbers_data(self, data: dict[str, dict[str, str]]) -> None:
        path = self._resolve_saved_diff_numbers_path()
        payload: dict[str, dict[str, str]] = {}
        for song_id_display, entries in data.items():
            if not isinstance(entries, dict):
                continue
            key = str(song_id_display).strip()
            if not key:
                continue
            row: dict[str, str] = {}
            for file_name, raw_value in entries.items():
                name = str(file_name).strip()
                value = str(raw_value or "").strip()
                if name and value.isdigit():
                    row[name] = value[:2]
            if row:
                payload[key] = row
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as error:
            self._append_conversion_log(
                f"Failed: could not save missing difficulty numbers: {error}",
                error=True,
            )
            return
        self._saved_diff_numbers_cache = payload
        self._saved_diff_numbers_cache_loaded = True
        self._saved_diff_numbers_cache_exists = True
        try:
            self._saved_diff_numbers_cache_mtime_ns = path.stat().st_mtime_ns
        except Exception:
            self._saved_diff_numbers_cache_mtime_ns = None
        self._refresh_saved_diff_numbers_watcher()

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

    def _save_file_paths(self, sound_path: str, movie_path: str, output_base_path: str) -> None:
        self._sound_path = sound_path.strip().replace("/", "\\")
        self._movie_path = movie_path.strip().replace("/", "\\")
        output_base_text = output_base_path.strip().replace("/", "\\")
        if output_base_text:
            self._output_base_path = str(Path(output_base_text).expanduser())
        else:
            self._output_base_path = str(self._default_output_base_path())
        self._settings.setValue("paths/sound", self._sound_path)
        self._settings.setValue("paths/movie", self._movie_path)
        self._settings.setValue("paths/output_base", self._output_base_path)
        self._settings.sync()

    def _pick_folder_into_line_edit(self, target_input: QLineEdit | None) -> None:
        if target_input is None:
            return
        start_dir = target_input.text().strip() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Select folder", start_dir)
        if folder:
            target_input.setText(folder.replace("/", "\\"))

    def _set_top_navigation_visible(self, visible: bool) -> None:
        if self._top_bar is not None:
            self._top_bar.setVisible(visible)
        if self._top_separator is not None:
            self._top_separator.setVisible(visible)

    def _first_run_has_required_paths(self) -> bool:
        return bool(self._welcome_sound_input and self._welcome_sound_input.text().strip()) and bool(
            self._welcome_movie_input and self._welcome_movie_input.text().strip()
        )

    def _update_first_run_continue_button_text(self) -> None:
        if self._welcome_continue_button is None:
            return
        if self._first_run_has_required_paths():
            self._welcome_continue_button.setText("Apply and continue")
        else:
            self._welcome_continue_button.setText("Skip and specify paths later")

    def _on_first_run_continue_clicked(self) -> None:
        if self._welcome_output_input is not None:
            output_text = self._welcome_output_input.text()
        else:
            output_text = self._output_base_path

        sound_text = self._welcome_sound_input.text() if self._welcome_sound_input is not None else self._sound_path
        movie_text = self._welcome_movie_input.text() if self._welcome_movie_input is not None else self._movie_path

        if self._first_run_has_required_paths():
            self._save_file_paths(sound_text, movie_text, output_text)
        else:
            self._save_file_paths(self._sound_path, self._movie_path, output_text)

        self._settings.setValue("ui/first_run_completed", True)
        self._settings.sync()
        self._set_top_navigation_visible(True)
        self._show_main_page()

    def _maybe_show_first_run_setup(self) -> None:
        if bool(self._settings.value("ui/first_run_completed", False, bool)):
            return
        self._set_top_navigation_visible(False)
        if self._page_stack is not None:
            self._page_stack.setCurrentIndex(0)

    def _reset_all_settings_and_restart(self) -> None:
        dialog = ActionConfirmDialog(
            "Reset all settings and restart iidx2bms?",
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._settings.clear()
        self._settings.sync()

        if getattr(sys, "frozen", False):
            program = str(Path(sys.executable))
            args = sys.argv[1:]
        else:
            program = str(Path(sys.executable))
            script_path = str(Path(sys.argv[0]).resolve())
            args = [script_path, *sys.argv[1:]]

        restart_env = os.environ.copy()
        for key in list(restart_env.keys()):
            if key == "_MEIPASS2" or key.startswith("_PYI"):
                restart_env.pop(key, None)
        restart_env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

        started = False
        try:
            if sys.platform == "win32":
                creation_flags = (
                    subprocess.DETACHED_PROCESS
                    | subprocess.CREATE_NEW_PROCESS_GROUP
                )
                subprocess.Popen(
                    [program, *args],
                    env=restart_env,
                    close_fds=True,
                    creationflags=creation_flags,
                )
            else:
                subprocess.Popen(
                    [program, *args],
                    env=restart_env,
                    close_fds=True,
                    start_new_session=True,
                )
            started = True
        except Exception:
            pass

        if not started:
            process_env = QProcessEnvironment.systemEnvironment()
            if process_env.contains("_MEIPASS2"):
                process_env.remove("_MEIPASS2")
            if process_env.contains("_PYI_APPLICATION_HOME_DIR"):
                process_env.remove("_PYI_APPLICATION_HOME_DIR")
            process_env.insert("PYINSTALLER_RESET_ENVIRONMENT", "1")
            restart_process = QProcess(self)
            restart_process.setProcessEnvironment(process_env)
            started = restart_process.startDetached(program, args)
            if not started:
                QProcess.startDetached(program, args)
        QApplication.instance().quit()

    def _selected_results_data(self) -> list[SearchResult]:
        selected: list[SearchResult] = []
        if self._selected_results is None:
            return selected
        for row_index in range(self._selected_results.count()):
            item = self._selected_results.item(row_index)
            base_result = item.data(Qt.ItemDataRole.UserRole + 2)
            if not isinstance(base_result, SearchResult):
                base_result = item.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(base_result, SearchResult):
                continue
            base_result = self._search_engine.ensure_levels(base_result)
            result = self._apply_saved_levels_to_result(base_result)
            result = self._search_engine.ensure_genre(result)
            if not result.game_name:
                result = self._search_engine.ensure_game_name(result)
            item.setData(Qt.ItemDataRole.UserRole + 2, base_result)
            item.setData(Qt.ItemDataRole.UserRole + 1, result)
            selected.append(result)
        return selected

    def _primary_line_text(self, result: SearchResult, use_ascii: bool) -> str:
        title = result.title_ascii if use_ascii else result.title
        if not title:
            title = result.title if use_ascii else result.title_ascii
        return f"ID: {result.song_id_display}  {result.artist} - {title}"

    def _conversion_progress_label_text(self, result: SearchResult) -> str:
        title = result.title_ascii if self._show_ascii_song_title else result.title
        if not title:
            title = result.title or result.title_ascii or ""
        text = f"ID: {result.song_id_display}  {title}"
        return text if len(text) <= 64 else f"{text[:61]}..."

    def _reset_conversion_progress_rows(self, charts: list[SearchResult]) -> None:
        if self._conversion_progress_list is None:
            return
        self._conversion_progress_list.clear()
        self._conversion_progress_bars.clear()
        self._playlevel_pending_song_ids.clear()
        if not charts:
            self._conversion_progress_list.setVisible(False)
            if self._conversion_progress_gap is not None:
                self._conversion_progress_gap.setVisible(False)
            return

        row_height = 26
        for result in charts:
            row_widget = QFrame()
            row_widget.setObjectName("ConversionProgressItem")
            row_widget.setFixedHeight(row_height)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(8, 4, 8, 4)
            row_layout.setSpacing(10)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            row_widget.setToolTip("")
            row_widget.installEventFilter(self)

            compact_text = self._conversion_progress_label_text(result)
            label = QLabel(compact_text)
            label.setObjectName("ConversionProgressLabel")
            label.setFixedHeight(18)
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            label.setMinimumWidth(0)
            label.setToolTip("")
            label.installEventFilter(self)
            row_layout.addWidget(label, 1)

            progress_bar = QProgressBar()
            progress_bar.setObjectName("ConversionProgressBar")
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setFormat("0%")
            progress_bar.setFixedHeight(18)
            progress_bar.setFixedWidth(120)
            progress_bar.setProperty("pending", False)
            progress_bar.setProperty("textDark", False)
            progress_bar.setToolTip("")
            progress_bar.installEventFilter(self)
            row_layout.addWidget(progress_bar, 0, Qt.AlignmentFlag.AlignVCenter)

            item = QListWidgetItem()
            item.setSizeHint(QSize(0, row_height))
            self._conversion_progress_list.addItem(item)
            self._conversion_progress_list.setItemWidget(item, row_widget)
            self._conversion_progress_bars[result.song_id_display] = progress_bar

        visible_rows = min(max(1, len(charts)), 5)
        self._conversion_progress_list.setFixedHeight(
            (visible_rows * row_height) + 8 + 2
        )
        self._conversion_progress_list.setVisible(True)
        if self._conversion_progress_gap is not None:
            self._conversion_progress_gap.setVisible(True)
        self._update_conversion_progress_row_widths()

    def _update_conversion_progress_row_widths(self) -> None:
        if self._conversion_progress_list is None:
            return
        viewport_width = self._conversion_progress_list.viewport().width()
        if viewport_width <= 0:
            return
        left_right = 8 + 8
        spacing = 10
        progress_width = 120
        label_width = max(40, viewport_width - left_right - spacing - progress_width)
        for row_index in range(self._conversion_progress_list.count()):
            item = self._conversion_progress_list.item(row_index)
            if item is None:
                continue
            row_widget = self._conversion_progress_list.itemWidget(item)
            if row_widget is None:
                continue
            label = row_widget.findChild(QLabel, "ConversionProgressLabel")
            if label is not None:
                label.setFixedWidth(label_width)

    def _set_conversion_chart_progress(self, song_id_display: str, percent: int) -> None:
        progress_bar = self._conversion_progress_bars.get(song_id_display)
        if progress_bar is None:
            return
        bounded = min(100, max(0, int(percent)))
        if progress_bar.property("failed"):
            progress_bar.setProperty("failed", False)
        if progress_bar.property("pending"):
            progress_bar.setProperty("pending", False)
            progress_bar.style().unpolish(progress_bar)
            progress_bar.style().polish(progress_bar)
            progress_bar.update()
        progress_bar.setValue(bounded)
        progress_bar.setFormat(f"{bounded}%")
        use_dark_text = False
        if bool(progress_bar.property("textDark")) != use_dark_text:
            progress_bar.setProperty("textDark", use_dark_text)
            progress_bar.style().unpolish(progress_bar)
            progress_bar.style().polish(progress_bar)
            progress_bar.update()

    def _set_conversion_chart_pending(self, song_id_display: str, percent: int = 99) -> None:
        progress_bar = self._conversion_progress_bars.get(song_id_display)
        if progress_bar is None:
            return
        bounded = min(99, max(0, int(percent)))
        if progress_bar.property("failed"):
            progress_bar.setProperty("failed", False)
        if not progress_bar.property("pending"):
            progress_bar.setProperty("pending", True)
        progress_bar.setProperty("textDark", True)
        progress_bar.style().unpolish(progress_bar)
        progress_bar.style().polish(progress_bar)
        progress_bar.update()
        progress_bar.setValue(bounded)
        progress_bar.setFormat(f"{bounded}%")

    def _set_conversion_chart_failed(self, song_id_display: str) -> None:
        progress_bar = self._conversion_progress_bars.get(song_id_display)
        if progress_bar is None:
            return
        if progress_bar.property("pending"):
            progress_bar.setProperty("pending", False)
        progress_bar.setProperty("failed", True)
        progress_bar.setProperty("textDark", False)
        progress_bar.style().unpolish(progress_bar)
        progress_bar.style().polish(progress_bar)
        progress_bar.update()
        progress_bar.setValue(0)
        progress_bar.setFormat("0%")

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
            return "Non-standard symbols in chart artist name, title or genre, see Chart editing panel to continue."
        return "Non-standard symbols in chart artist names, titles or genres, see Chart editing panel to continue."

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
            self._start_conversion_button.setToolTip("See Processing & Edit tab to continue")
            return
        self._start_conversion_button.setText("Start conversion")
        self._start_conversion_button.setEnabled(has_charts)
        if has_charts:
            self._start_conversion_button.setToolTip("")
        else:
            self._start_conversion_button.setToolTip("Select at least one chart to start conversion")

    def _update_conversion_inputs_locked_state(self) -> None:
        locked = self._conversion_active
        hint = "See Processing & Edit tab to continue"
        if self._search_input is not None:
            self._search_input.setReadOnly(locked)
            self._search_input.setProperty("conversionLocked", locked)
            self._search_input.setToolTip(hint if locked else "")
            self._search_input.style().unpolish(self._search_input)
            self._search_input.style().polish(self._search_input)
            self._search_input.update()
            effect = self._search_input.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._search_input)
                self._search_input.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        if self._search_clear_button is not None:
            self._search_clear_button.setProperty("conversionLocked", locked)
            self._search_clear_button.setToolTip(hint if locked else "Clear search")
            self._search_clear_button.style().unpolish(self._search_clear_button)
            self._search_clear_button.style().polish(self._search_clear_button)
            self._search_clear_button.update()
            effect = self._search_clear_button.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._search_clear_button)
                self._search_clear_button.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        if self._search_results is not None:
            self._search_results.setProperty("conversionLocked", locked)
            self._search_results.setToolTip(hint if locked else "")
            self._search_results.style().unpolish(self._search_results)
            self._search_results.style().polish(self._search_results)
            self._search_results.update()
            effect = self._search_results.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._search_results)
                self._search_results.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        if self._selected_results is not None:
            self._selected_results.setProperty("conversionLocked", locked)
            self._selected_results.setToolTip(hint if locked else "")
            self._selected_results.style().unpolish(self._selected_results)
            self._selected_results.style().polish(self._selected_results)
            self._selected_results.update()
            effect = self._selected_results.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._selected_results)
                self._selected_results.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        if self._selected_reset_button is not None:
            self._selected_reset_button.setEnabled(not locked)
            self._selected_reset_button.setToolTip(
                hint if locked else "Reset selected charts and all changes"
            )
            effect = self._selected_reset_button.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._selected_reset_button)
                self._selected_reset_button.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        if self._include_stagefile_checkbox is not None:
            self._include_stagefile_checkbox.setEnabled(not locked)
            self._include_stagefile_checkbox.setToolTip(hint if locked else "")
            effect = self._include_stagefile_checkbox.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._include_stagefile_checkbox)
                self._include_stagefile_checkbox.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        if self._include_preview_checkbox is not None:
            self._include_preview_checkbox.setEnabled(not locked)
            self._include_preview_checkbox.setToolTip(hint if locked else "")
            effect = self._include_preview_checkbox.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._include_preview_checkbox)
                self._include_preview_checkbox.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        if self._include_bga_checkbox is not None:
            self._include_bga_checkbox.setEnabled(not locked)
            self._include_bga_checkbox.setToolTip(hint if locked else "")
            effect = self._include_bga_checkbox.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(self._include_bga_checkbox)
                self._include_bga_checkbox.setGraphicsEffect(effect)
            effect.setOpacity(0.55 if locked else 1.0)
        self._refresh_search_result_widgets()
        self._refresh_selected_result_widgets()

    def _clear_chart_editing_warning_logs(self) -> None:
        if self._conversion_logs_results is None:
            return
        warning_single = self._chart_editing_warning_message(1)
        warning_multi = self._chart_editing_warning_message(2)
        warning_check_line = "Check Chart Editing panel to continue."
        finish_editing_first = (
            'Finish chart editing first (use "Apply and continue conversion" button '
            'or "Skip editing and continue conversion" button).'
        )
        lines = self._conversion_logs_results.toPlainText().splitlines()
        kept_lines = [
            line
            for line in lines
            if (
                line not in {warning_single, warning_multi, finish_editing_first}
                and line != warning_check_line
                and not line.startswith("Difficulty not found for .bme files:")
                and not line.startswith("Difficulty not found in .bme files for:")
                and not line.startswith("Difficulty not found in.bme files for :")
                and re.fullmatch(r"ID:\s*\d{5}(?:,\s*ID:\s*\d{5})*\.?", line.strip()) is None
                and not line.startswith("Missing PLAYLEVEL values:")
            )
        ]
        self._conversion_logs_results.clear()
        for line in kept_lines:
            self._append_conversion_log(line, error=False)

    def _has_chart_name_overrides(self) -> bool:
        return any(bool(values) for values in self._chart_name_overrides.values())

    def _is_playlevel_editing_mode(self) -> bool:
        return self._chart_editing_mode == "playlevel"

    def _has_playlevel_overrides(self) -> bool:
        return any(bool(value.strip()) for value in self._playlevel_value_overrides.values())

    def _missing_playlevel_values_count(self) -> int:
        total_required = 0
        total_filled = 0
        for entries in self._playlevel_missing_entries.values():
            for entry in entries:
                path = entry.get("path", "")
                if not path:
                    continue
                total_required += 1
                if self._playlevel_value_overrides.get(path, "").strip():
                    total_filled += 1
        return max(0, total_required - total_filled)

    def _set_playlevel_override(self, file_path: str, value: str) -> None:
        normalized = "".join(ch for ch in value if ch.isdigit())[:2]
        if normalized:
            self._playlevel_value_overrides[file_path] = normalized
        else:
            self._playlevel_value_overrides.pop(file_path, None)
        self._refresh_chart_editing_header_controls()

    def _difficulty_label_html(self, label_text: str) -> str:
        bracket_part = label_text
        suffix = ""
        if "]" in label_text:
            close_index = label_text.find("]")
            bracket_part = label_text[: close_index + 1]
            suffix = label_text[close_index + 1 :]
        token_upper = bracket_part.upper()
        if "BEGINNER" in token_upper:
            color = "#00e37f"
        elif "NORMAL" in token_upper:
            color = "#00a4ff"
        elif "HYPER" in token_upper:
            color = "#c0840c"
        elif "ANOTHER" in token_upper:
            color = "#be0420"
        elif "LEGGENDARIA" in token_upper:
            color = "#7900ff"
        else:
            color = "#dcdcdc"
        return (
            f'<span style="color:{color};">{html.escape(bracket_part)}</span>'
            f'<span style="color:#dcdcdc;">{html.escape(suffix)}</span>'
        )

    def _difficulty_field_from_entry(self, label_text: str, file_name: str) -> str | None:
        text = f"{label_text} {file_name}".upper()
        is_dp = (" DP" in text) or text.endswith("DP") or ("DP " in text)
        if ("14]" in text) and (" SP" not in text):
            is_dp = True
        if "BEGINNER" in text:
            suffix = "b"
        elif "NORMAL" in text:
            suffix = "n"
        elif "HYPER" in text:
            suffix = "h"
        elif "ANOTHER" in text:
            suffix = "a"
        elif "LEGGENDARIA" in text:
            suffix = "l"
        elif "14]" in text:
            suffix = "l"
        elif "7]" in text:
            suffix = "l"
        else:
            return None
        return f"{'dp' if is_dp else 'sp'}{suffix}_level"

    def _result_with_level_override(
        self,
        result: SearchResult,
        field_name: str,
        raw_value: str | int,
    ) -> SearchResult:
        try:
            value = int(raw_value)
        except Exception:
            value = 0
        value = max(0, value)
        if getattr(result, field_name, 0) == value:
            return result
        try:
            return replace(result, **{field_name: value})
        except Exception:
            return result

    def _apply_saved_levels_to_result(self, result: SearchResult) -> SearchResult:
        data = self._get_saved_diff_numbers_data()
        if not data:
            return result
        song_entries = data.get(result.song_id_display, {})
        if not song_entries:
            return result
        updated = result
        for file_name, raw_value in song_entries.items():
            field_name = self._difficulty_field_from_entry(file_name, file_name)
            if not field_name:
                continue
            updated = self._result_with_level_override(updated, field_name, raw_value)
        return updated

    def _remember_missing_difficulty_values(self) -> None:
        if not self._save_missing_difficulty_numbers:
            return
        data = dict(self._get_saved_diff_numbers_data())
        changed = False
        for song_id, entries in self._playlevel_missing_entries.items():
            result = self._playlevel_source_results.get(song_id)
            if result is None:
                continue
            song_key = result.song_id_display
            song_bucket = dict(data.get(song_key, {}))
            bucket_changed = False
            for entry in entries:
                file_name = str(entry.get("file_name", "")).strip()
                file_path = str(entry.get("path", "")).strip()
                if not file_name or not file_path:
                    continue
                value = self._playlevel_value_overrides.get(file_path, "").strip()
                if not value.isdigit():
                    continue
                normalized = value[:2]
                if song_bucket.get(file_name) != normalized:
                    song_bucket[file_name] = normalized
                    bucket_changed = True
            if bucket_changed:
                data[song_key] = song_bucket
                changed = True
        if changed:
            self._write_saved_diff_numbers_data(data)
            self._refresh_search_result_widgets()
            self._refresh_selected_result_widgets()

    def _apply_playlevel_value_to_chart_data(
        self,
        song_id: int,
        song_id_display: str,
        label_text: str,
        file_name: str,
        value: str | int,
    ) -> None:
        field_name = self._difficulty_field_from_entry(label_text, file_name)
        if not field_name:
            return
        source = self._playlevel_source_results.get(song_id)
        if source is not None:
            updated_source = self._result_with_level_override(source, field_name, value)
            self._playlevel_source_results[song_id] = updated_source
            self._conversion_chart_by_id_display[song_id_display] = updated_source
            selected_item = self._selected_item_by_song_id.get(song_id)
            if selected_item is not None:
                base_result = selected_item.data(Qt.ItemDataRole.UserRole + 2)
                if not isinstance(base_result, SearchResult):
                    base_result = updated_source
                else:
                    base_result = self._result_with_level_override(base_result, field_name, value)
                selected_item.setData(Qt.ItemDataRole.UserRole + 2, base_result)
                selected_item.setData(Qt.ItemDataRole.UserRole + 1, self._apply_chart_name_override(base_result))
        try:
            self._history_recorder.set_chart_level(song_id_display, field_name, int(value))
        except Exception:
            pass

    def _collect_missing_playlevels(self) -> int:
        self._playlevel_missing_entries.clear()
        self._playlevel_source_results.clear()
        self._playlevel_value_overrides.clear()
        self._playlevel_pending_song_ids.clear()
        saved_data = self._get_saved_diff_numbers_data()
        pending_song_ids: set[str] = set()
        missing_total = 0
        for song_id_display, output_dir in self._conversion_output_dirs.items():
            if not output_dir.is_dir():
                continue
            result = self._conversion_chart_by_id_display.get(song_id_display)
            if result is None:
                continue
            for bme_path in sorted(output_dir.glob("*.bme")):
                try:
                    bme_text = bme_path.read_text(encoding="utf-8-sig", errors="ignore")
                except Exception:
                    continue
                playlevel_value: int | None = None
                for line in bme_text.splitlines():
                    normalized = line.strip()
                    if not normalized.upper().startswith("#PLAYLEVEL"):
                        continue
                    chunks = normalized.split(maxsplit=1)
                    if len(chunks) >= 2:
                        raw_value = chunks[1].strip()
                        if raw_value.isdigit():
                            playlevel_value = int(raw_value)
                    break
                if playlevel_value != 0:
                    continue
                name_upper = bme_path.stem.upper()
                if "14]" in name_upper:
                    suffix = " DP"
                elif "7]" in name_upper:
                    suffix = " SP"
                else:
                    suffix = ""
                entry_label = f"{bme_path.stem}{suffix}"
                self._playlevel_missing_entries.setdefault(result.song_id, []).append(
                    {
                        "label": entry_label,
                        "path": str(bme_path),
                        "file_name": bme_path.name,
                        "song_id_display": result.song_id_display,
                    }
                )
                self._playlevel_source_results[result.song_id] = result
                saved_value = str(
                    saved_data.get(result.song_id_display, {}).get(bme_path.name, "")
                ).strip()
                if saved_value.isdigit():
                    normalized = saved_value[:2]
                    file_path = str(bme_path)
                    self._playlevel_value_overrides[file_path] = normalized
                    self._apply_playlevel_value_to_chart_data(
                        result.song_id,
                        result.song_id_display,
                        entry_label,
                        bme_path.name,
                        normalized,
                    )
                else:
                    pending_song_ids.add(result.song_id_display)
                missing_total += 1
        self._playlevel_pending_song_ids = pending_song_ids
        return missing_total

    def _apply_playlevel_overrides(self, allow_partial: bool = False) -> bool:
        for entries in self._playlevel_missing_entries.values():
            for entry in entries:
                file_path = entry.get("path", "")
                value = self._playlevel_value_overrides.get(file_path, "").strip()
                if not file_path:
                    return False
                if not value:
                    if allow_partial:
                        continue
                    return False
                if not value.isdigit():
                    return False
        try:
            for song_id, entries in self._playlevel_missing_entries.items():
                for entry in entries:
                    file_path = entry.get("path", "")
                    value = self._playlevel_value_overrides.get(file_path, "").strip()
                    if not value and allow_partial:
                        continue
                    set_bme_playlevel(Path(file_path), int(value))
                    file_name = str(entry.get("file_name", "")).strip()
                    label_text = str(entry.get("label", "")).strip()
                    source = self._playlevel_source_results.get(song_id)
                    song_id_display = (
                        source.song_id_display
                        if isinstance(source, SearchResult)
                        else str(entry.get("song_id_display", "")).strip()
                    )
                    if song_id_display:
                        self._apply_playlevel_value_to_chart_data(
                            song_id,
                            song_id_display,
                            label_text,
                            file_name,
                            value,
                        )
        except Exception as error:
            self._append_conversion_log(f"Failed: could not apply PLAYLEVEL edits: {error}", error=True)
            return False
        return True

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
        show_remywiki = False
        show_reset = False
        show_continue = False
        playlevel_mode = self._is_playlevel_editing_mode()
        has_edits = self._has_chart_name_overrides()
        if self._chart_editing_status_label is not None:
            self._chart_editing_status_label.setVisible(False)
            self._chart_editing_status_label.setText("")
        if playlevel_mode:
            if self._chart_editing_reset_button is not None:
                self._chart_editing_reset_button.setVisible(False)
                self._chart_editing_reset_button.setEnabled(False)
            if self._chart_editing_continue_button is not None:
                waiting = self._awaiting_chart_editing_action and charts_count > 0
                show_continue = waiting
                self._chart_editing_continue_button.setVisible(show_continue)
                if waiting:
                    text = "Apply and finalize conversion"
                    self._chart_editing_continue_button.setText(text)
        else:
            if self._chart_editing_reset_button is not None:
                show_reset = charts_count > 0 and has_edits
                self._chart_editing_reset_button.setVisible(show_reset)
                self._chart_editing_reset_button.setEnabled(has_edits)
                self._chart_editing_reset_button.setToolTip("Reset edited fields")
            if self._chart_editing_continue_button is not None:
                waiting = self._awaiting_chart_editing_action and charts_count > 0
                show_continue = waiting
                self._chart_editing_continue_button.setVisible(show_continue)
                if waiting:
                    text = (
                        "Apply and continue conversion"
                        if has_edits
                        else "Skip editing and continue conversion"
                    )
                    self._chart_editing_continue_button.setText(text)
        apply_names_state = (not playlevel_mode) and show_continue and has_edits
        if self._chart_editing_continue_button is not None:
            if show_continue:
                # Keep right edge/suffix alignment stable between Apply/Skip states.
                self._chart_editing_continue_button.setStyleSheet(
                    "text-align: right; padding: 0 7px 0 6px;"
                )
                # Keep button width tight to current text (fix over-wide Apply).
                self._chart_editing_continue_button.setFixedWidth(
                    self._chart_editing_continue_button.sizeHint().width()
                )
            else:
                self._chart_editing_continue_button.setStyleSheet("")

        show_remywiki = self._resolve_chart_for_remywiki_title() is not None
        if self._chart_editing_remywiki_button is not None:
            self._chart_editing_remywiki_button.setVisible(show_remywiki)
            self._chart_editing_remywiki_button.setEnabled(show_remywiki)
        if self._chart_editing_reset_button is not None:
            self._chart_editing_reset_button.setProperty("applyOffset", apply_names_state)
            self._chart_editing_reset_button.style().unpolish(self._chart_editing_reset_button)
            self._chart_editing_reset_button.style().polish(self._chart_editing_reset_button)
            self._chart_editing_reset_button.update()
        if self._chart_editing_reset_placeholder is not None:
            self._chart_editing_reset_placeholder.setVisible(show_continue and not show_reset)
        show_bottom_actions = show_reset or show_continue
        if self._chart_editing_buttons_row is not None:
            if show_continue:
                target_buttons_height = 38
            elif show_reset and not show_continue:
                target_buttons_height = 38
            else:
                target_buttons_height = 0
            self._animate_chart_editing_buttons_row(target_buttons_height)
            row_layout = self._chart_editing_buttons_row.layout()
            if isinstance(row_layout, QHBoxLayout):
                row_layout.setContentsMargins(0, 0, 0, 0)
                if self._chart_editing_continue_button is not None:
                    continue_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    if show_continue:
                        continue_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
                    row_layout.setAlignment(self._chart_editing_continue_button, continue_alignment)
                if self._chart_editing_reset_button is not None:
                    reset_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    if show_continue:
                        reset_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
                    elif show_reset:
                        reset_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
                    row_layout.setAlignment(self._chart_editing_reset_button, reset_alignment)
                if self._chart_editing_reset_placeholder is not None:
                    placeholder_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    if show_continue:
                        placeholder_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
                    row_layout.setAlignment(self._chart_editing_reset_placeholder, placeholder_alignment)
        if self._chart_editing_bottom_gap is not None:
            target_gap_height = 2 if show_bottom_actions else 0
            self._animate_chart_editing_bottom_gap(target_gap_height)
        if self._chart_editing_reset_button is not None:
            reset_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if show_reset and not show_continue:
                reset_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
            row_layout = self._chart_editing_reset_button.parentWidget().layout()
            if isinstance(row_layout, QHBoxLayout):
                if apply_names_state:
                    row_layout.setContentsMargins(0, 0, 0, 4)
                elif show_continue:
                    row_layout.setContentsMargins(0, 0, 0, 4)
                elif show_reset and not show_continue:
                    row_layout.setContentsMargins(0, 0, 0, 1)
                else:
                    row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setAlignment(self._chart_editing_reset_button, reset_alignment)
        if self._chart_editing_reset_placeholder is not None:
            placeholder_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if show_reset and not show_continue:
                placeholder_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
            row_layout = self._chart_editing_reset_placeholder.parentWidget().layout()
            if isinstance(row_layout, QHBoxLayout):
                row_layout.setAlignment(self._chart_editing_reset_placeholder, placeholder_alignment)

    def _animate_chart_editing_buttons_row(self, target_height: int) -> None:
        row = self._chart_editing_buttons_row
        if row is None:
            return
        target_height = max(0, int(target_height))
        current_height = max(0, int(row.maximumHeight()))
        anim = self._chart_editing_buttons_row_anim
        if anim is not None and anim.state() == QAbstractAnimation.State.Running:
            try:
                current_target = int(anim.endValue())
            except (TypeError, ValueError):
                current_target = None
            if current_target == target_height:
                return
        if current_height == target_height:
            row.setMinimumHeight(target_height)
            row.setMaximumHeight(target_height)
            if target_height == 0:
                row.setVisible(False)
            else:
                row.setVisible(True)
            return
        row.setVisible(True)
        if anim is None:
            row.setMinimumHeight(target_height)
            row.setMaximumHeight(target_height)
            if target_height == 0:
                row.setVisible(False)
            return
        anim.stop()
        anim.setStartValue(max(0, current_height))
        anim.setEndValue(max(0, target_height))
        anim.start()

    def _on_chart_editing_buttons_row_anim_value_changed(self, value: object) -> None:
        row = self._chart_editing_buttons_row
        if row is None:
            return
        try:
            height = max(0, int(value))
        except (TypeError, ValueError):
            return
        row.setMinimumHeight(height)
        row.setMaximumHeight(height)

    def _on_chart_editing_buttons_row_anim_finished(self) -> None:
        row = self._chart_editing_buttons_row
        if row is None:
            return
        height = max(0, int(row.maximumHeight()))
        row.setMinimumHeight(height)
        row.setMaximumHeight(height)
        if row.maximumHeight() <= 0:
            row.setVisible(False)

    def _animate_chart_editing_bottom_gap(self, target_height: int) -> None:
        gap = self._chart_editing_bottom_gap
        if gap is None:
            return
        target_height = max(0, int(target_height))
        current_height = max(0, int(gap.maximumHeight()))
        anim = self._chart_editing_bottom_gap_anim
        if anim is not None and anim.state() == QAbstractAnimation.State.Running:
            try:
                current_target = int(anim.endValue())
            except (TypeError, ValueError):
                current_target = None
            if current_target == target_height:
                return
        if current_height == target_height:
            gap.setMinimumHeight(target_height)
            gap.setMaximumHeight(target_height)
            if target_height == 0:
                gap.setVisible(False)
            else:
                gap.setVisible(True)
            return
        gap.setVisible(True)
        if anim is None:
            gap.setMinimumHeight(target_height)
            gap.setMaximumHeight(target_height)
            if target_height == 0:
                gap.setVisible(False)
            return
        anim.stop()
        anim.setStartValue(max(0, current_height))
        anim.setEndValue(max(0, target_height))
        anim.start()

    def _on_chart_editing_bottom_gap_anim_value_changed(self, value: object) -> None:
        gap = self._chart_editing_bottom_gap
        if gap is None:
            return
        try:
            height = max(0, int(value))
        except (TypeError, ValueError):
            return
        gap.setMinimumHeight(height)
        gap.setMaximumHeight(height)

    def _on_chart_editing_bottom_gap_anim_finished(self) -> None:
        gap = self._chart_editing_bottom_gap
        if gap is None:
            return
        height = max(0, int(gap.maximumHeight()))
        gap.setMinimumHeight(height)
        gap.setMaximumHeight(height)
        if gap.maximumHeight() <= 0:
            gap.setVisible(False)

    def _resolve_chart_for_remywiki_title(self) -> str | None:
        if self._chart_editing_results is None:
            return None
        item = self._chart_editing_results.currentItem()
        if item is None and self._chart_editing_results.count() > 0:
            item = self._chart_editing_results.item(0)
        if item is None:
            return None
        base_result = item.data(Qt.ItemDataRole.UserRole + 2)
        if not isinstance(base_result, SearchResult):
            base_result = item.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(base_result, SearchResult):
            return None
        title = (base_result.title or "").strip()
        return title or None

    def _on_open_remywiki_clicked(self) -> None:
        title = self._resolve_chart_for_remywiki_title()
        if not title:
            return
        QDesktopServices.openUrl(QUrl(build_remywiki_url(title)))

    def _set_chart_editing_attention(self, enabled: bool) -> None:
        if self._chart_editing_panel is None:
            return
        if not enabled:
            self._chart_editing_attention_timer.stop()
            self._chart_editing_attention_on = False
            if self._processing_page_button is not None:
                self._processing_page_button.setProperty("attention", False)
                self._processing_page_button.setProperty("attentionDanger", False)
                self._processing_page_button.style().unpolish(self._processing_page_button)
                self._processing_page_button.style().polish(self._processing_page_button)
                self._processing_page_button.update()
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
        if self._processing_page_button is not None and self._awaiting_chart_editing_action:
            self._processing_page_button.setProperty("attention", self._chart_editing_attention_on)
            self._processing_page_button.setProperty(
                "attentionDanger",
                self._chart_editing_attention_on and (not self._is_playlevel_editing_mode()),
            )
            self._processing_page_button.style().unpolish(self._processing_page_button)
            self._processing_page_button.style().polish(self._processing_page_button)
            self._processing_page_button.update()
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
        row.setProperty("chartEditingRow", True)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        line_spacing = 6
        left_layout.setSpacing(line_spacing)

        first_line = QWidget()
        first_line_layout = QHBoxLayout(first_line)
        first_line_layout.setContentsMargins(0, 0, 0, 0)
        first_line_layout.setSpacing(6)
        id_label = QLabel(f"ID: {result.song_id_display}")
        id_label.setObjectName("ChartEditPrefix")
        first_line_layout.addWidget(id_label, 0, Qt.AlignmentFlag.AlignVCenter)

        artist_input = QLineEdit()
        artist_input.setText(result.artist)
        artist_input.setObjectName("ChartEditInput")
        artist_input.setProperty("chart_edit_field", "artist")
        artist_input.setPlaceholderText("Artist")
        artist_input.setProperty("chart_editing_song_id", result.song_id)
        artist_input.installEventFilter(self)
        is_playlevel_mode = self._is_playlevel_editing_mode()
        conversion_names_locked = self._conversion_active and not is_playlevel_mode
        names_edit_locked = conversion_names_locked or (
            self._always_skip_chart_names_editing and not is_playlevel_mode
        )
        if is_playlevel_mode:
            names_locked_tooltip = "Copy-only field"
        elif conversion_names_locked:
            names_locked_tooltip = ""
        else:
            names_locked_tooltip = self._chart_editing_locked_tooltip() if names_edit_locked else ""
        artist_input.setEnabled(not names_edit_locked)
        artist_input.setReadOnly(is_playlevel_mode)
        artist_input.setToolTip(names_locked_tooltip)
        artist_input.textChanged.connect(
            lambda text, sid=result.song_id: self._set_chart_name_override(sid, "artist", text)
        )
        first_line_layout.addWidget(artist_input, 1)

        dash_label = QLabel("-")
        dash_label.setObjectName("ChartEditPrefix")
        first_line_layout.addWidget(dash_label, 0, Qt.AlignmentFlag.AlignVCenter)

        title_input = QLineEdit()
        title_input.setText(result.title)
        title_input.setObjectName("ChartEditInput")
        title_input.setProperty("chart_edit_field", "title")
        title_input.setPlaceholderText("Title")
        title_input.setProperty("chart_editing_song_id", result.song_id)
        title_input.installEventFilter(self)
        title_input.setEnabled(not names_edit_locked)
        title_input.setReadOnly(is_playlevel_mode)
        title_input.setToolTip(names_locked_tooltip)
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

        genre_input = QLineEdit()
        genre_input.setText(result.genre)
        genre_input.setObjectName("ChartEditInput")
        genre_input.setProperty("chart_edit_field", "genre")
        genre_input.setPlaceholderText("Genre")
        genre_input.setProperty("chart_editing_song_id", result.song_id)
        genre_input.installEventFilter(self)
        genre_input.setEnabled(not names_edit_locked)
        genre_input.setReadOnly(is_playlevel_mode)
        genre_input.setToolTip(names_locked_tooltip)
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

        if self._is_playlevel_editing_mode():
            raw_entries = item.data(Qt.ItemDataRole.UserRole + 3)
            if isinstance(raw_entries, list):
                entries = [entry for entry in raw_entries if isinstance(entry, dict)]
            else:
                entries = self._playlevel_missing_entries.get(result.song_id, [])
            for entry in entries:
                level_line = QWidget()
                level_layout = QHBoxLayout(level_line)
                level_layout.setContentsMargins(0, 0, 0, 0)
                level_layout.setSpacing(6)

                label = QLabel(entry.get("label", ""))
                label.setObjectName("ChartEditPrefix")
                label.setTextFormat(Qt.TextFormat.RichText)
                label.setText(self._difficulty_label_html(entry.get("label", "")))
                level_layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)

                value_input = QLineEdit()
                value_input.setText(self._playlevel_value_overrides.get(entry.get("path", ""), ""))
                value_input.setObjectName("ChartEditInput")
                value_input.setPlaceholderText("Difficulty number")
                value_input.setProperty("chart_editing_song_id", result.song_id)
                value_input.installEventFilter(self)
                value_input.textChanged.connect(
                    lambda text, file_path=entry.get("path", ""): self._set_playlevel_override(file_path, text)
                )
                value_input.cursorPositionChanged.connect(lambda old, new: _select_editing_item())
                _show_from_start(value_input)
                QTimer.singleShot(0, lambda e=value_input: _show_from_start(e))
                level_layout.addWidget(value_input, 1)
                left_layout.addWidget(level_line)

        row_layout.addWidget(left_column, 1)
        return row

    def _update_chart_editing_list(self) -> int:
        if self._chart_editing_results is None or self._selected_results is None:
            return 0
        self._chart_editing_results.setUniformItemSizes(not self._is_playlevel_editing_mode())
        self._chart_editing_results.setUpdatesEnabled(False)
        viewport = self._chart_editing_results.viewport()
        if viewport is not None:
            viewport.setUpdatesEnabled(False)
        try:
            if self._is_playlevel_editing_mode():
                self._chart_editing_results.clear()
                flagged_count = 0
                visible_rows: list[tuple[SearchResult, list[dict[str, str]]]] = []
                for song_id, entries in self._playlevel_missing_entries.items():
                    result = self._playlevel_source_results.get(song_id)
                    if result is None:
                        continue
                    unresolved_entries: list[dict[str, str]] = []
                    for entry in entries:
                        file_path = str(entry.get("path", "")).strip()
                        value = self._playlevel_value_overrides.get(file_path, "").strip()
                        if not value.isdigit():
                            unresolved_entries.append(entry)
                    if unresolved_entries:
                        visible_rows.append((result, unresolved_entries))
                total_rows = len(visible_rows)
                for row_index, (result, entries) in enumerate(visible_rows):
                    edit_item = QListWidgetItem()
                    edit_item.setData(Qt.ItemDataRole.UserRole, result.song_id)
                    edit_item.setData(Qt.ItemDataRole.UserRole + 1, result)
                    edit_item.setData(Qt.ItemDataRole.UserRole + 2, result)
                    edit_item.setData(Qt.ItemDataRole.UserRole + 3, entries)
                    row_widget = self._build_chart_editing_result_widget(result, edit_item)
                    row_height = max(72, row_widget.sizeHint().height())
                    row_widget.setFixedHeight(row_height)
                    bottom_gap = 1 if row_index < (total_rows - 1) else 0
                    container = QWidget()
                    container_layout = QVBoxLayout(container)
                    container_layout.setContentsMargins(0, 0, 0, bottom_gap)
                    container_layout.setSpacing(0)
                    container_layout.addWidget(row_widget)
                    container.setMinimumHeight(row_height + bottom_gap)
                    container.setMaximumHeight(row_height + bottom_gap)
                    edit_item.setSizeHint(QSize(0, row_height + bottom_gap))
                    self._chart_editing_results.addItem(edit_item)
                    self._chart_editing_results.setItemWidget(edit_item, container)
                    flagged_count += len(entries)
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
                if not base_non_standard and result.song_id not in self._chart_name_overrides:
                    continue
                if base_non_standard:
                    flagged_count += 1
                edit_item = QListWidgetItem()
                edit_item.setData(Qt.ItemDataRole.UserRole, result.song_id)
                edit_item.setData(Qt.ItemDataRole.UserRole + 1, result)
                edit_item.setData(Qt.ItemDataRole.UserRole + 2, base_result)
                row_widget = self._build_chart_editing_result_widget(result, edit_item)
                row_height = 72
                row_widget.setFixedHeight(row_height)
                container = QWidget()
                container_layout = QVBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 1)
                container_layout.setSpacing(0)
                container_layout.addWidget(row_widget)
                container.setMinimumHeight(row_height + 1)
                container.setMaximumHeight(row_height + 1)
                edit_item.setSizeHint(QSize(0, row_height + 1))
                self._chart_editing_results.addItem(edit_item)
                self._chart_editing_results.setItemWidget(edit_item, container)
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
        finally:
            self._chart_editing_results.setUpdatesEnabled(True)
            if viewport is not None:
                viewport.setUpdatesEnabled(True)
            self._chart_editing_results.viewport().update()

    def _confirm_action(self, message: str) -> bool:
        dialog = ActionConfirmDialog(message, self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def _show_info_dialog(self, message: str) -> None:
        dialog = ActionInfoDialog(message, self)
        dialog.exec()

    def _path_has_chart_source(self, root: Path, song_id: str) -> bool:
        return (root / song_id).is_dir() or (root / f"{song_id}.ifs").is_file()

    def _load_bga_map(self, data_path: Path) -> dict[str, str]:
        try:
            payload = json.loads(data_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        songs = payload.get("songs", {})
        bga_map: dict[str, str] = {}
        if isinstance(songs, dict):
            for song_id_raw, song_meta in songs.items():
                if not isinstance(song_meta, dict):
                    continue
                bga_name = str(song_meta.get("bga_filename", "") or "").strip()
                if not bga_name:
                    continue
                song_id = str(song_id_raw)
                if song_id.isdigit():
                    song_id = f"{int(song_id):05d}"
                bga_map[song_id] = bga_name
        return bga_map

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
        self._reset_conversion_progress_rows([])
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()

    def _on_reset_chart_editing_names_clicked(self) -> None:
        if self._is_playlevel_editing_mode():
            if not self._playlevel_value_overrides:
                return
            if not self._confirm_action("Reset all edited fields ?"):
                return
            self._playlevel_value_overrides.clear()
            self._update_chart_editing_list()
            return
        if not self._chart_name_overrides:
            return
        if not self._confirm_action("Reset all edited fields ?"):
            return
        cleared_song_ids = set(self._chart_name_overrides.keys())
        self._chart_name_overrides.clear()
        self._fast_reset_selected_rows(cleared_song_ids)
        self._fast_reset_chart_editing_rows(cleared_song_ids)
        self._refresh_chart_editing_header_controls()

    def _fast_reset_selected_rows(self, song_ids: set[int]) -> None:
        if self._selected_results is None or not song_ids:
            return
        self._selected_results.setUpdatesEnabled(False)
        viewport = self._selected_results.viewport()
        if viewport is not None:
            viewport.setUpdatesEnabled(False)
        try:
            for row_index in range(self._selected_results.count()):
                item = self._selected_results.item(row_index)
                song_id = item.data(Qt.ItemDataRole.UserRole)
                if not isinstance(song_id, int) or song_id not in song_ids:
                    continue
                base_result = item.data(Qt.ItemDataRole.UserRole + 2)
                if not isinstance(base_result, SearchResult):
                    continue
                item.setData(Qt.ItemDataRole.UserRole + 1, base_result)
                widget = self._selected_results.itemWidget(item)
                if widget is None:
                    continue
                primary = widget.findChild(MarqueeLabel, "SelectedChartPrimary")
                if primary is not None:
                    primary.setText(self._primary_line_text(base_result, use_ascii=self._show_ascii_song_title))
                secondary = widget.findChild(MarqueeLabel, "SelectedChartSecondary")
                if secondary is not None:
                    secondary.setText(self._secondary_line_text(base_result))
        finally:
            self._selected_results.setUpdatesEnabled(True)
            if viewport is not None:
                viewport.setUpdatesEnabled(True)
            self._selected_results.viewport().update()

    def _fast_reset_chart_editing_rows(self, song_ids: set[int]) -> None:
        if self._chart_editing_results is None or not song_ids or self._is_playlevel_editing_mode():
            self._update_chart_editing_list()
            return
        self._chart_editing_results.setUpdatesEnabled(False)
        viewport = self._chart_editing_results.viewport()
        if viewport is not None:
            viewport.setUpdatesEnabled(False)
        try:
            rows_to_remove: list[int] = []
            for row_index in range(self._chart_editing_results.count()):
                item = self._chart_editing_results.item(row_index)
                song_id = item.data(Qt.ItemDataRole.UserRole)
                if not isinstance(song_id, int) or song_id not in song_ids:
                    continue
                base_result = item.data(Qt.ItemDataRole.UserRole + 2)
                if not isinstance(base_result, SearchResult):
                    continue
                item.setData(Qt.ItemDataRole.UserRole + 1, base_result)
                if not self._is_chart_non_standard(base_result):
                    rows_to_remove.append(row_index)
                    continue
                holder = self._chart_editing_results.itemWidget(item)
                if holder is None:
                    continue
                row_widget = holder
                if holder.objectName() != "SelectedChartItem":
                    nested = holder.findChild(QFrame, "SelectedChartItem")
                    if nested is not None:
                        row_widget = nested
                for edit in row_widget.findChildren(QLineEdit):
                    field = edit.property("chart_edit_field")
                    if field == "artist":
                        value = base_result.artist
                    elif field == "title":
                        value = base_result.title
                    elif field == "genre":
                        value = base_result.genre
                    else:
                        continue
                    blocked = edit.blockSignals(True)
                    edit.setText(value)
                    edit.blockSignals(blocked)
                    edit.setCursorPosition(0)
            for row_index in reversed(rows_to_remove):
                removed = self._chart_editing_results.takeItem(row_index)
                if removed is not None:
                    del removed
            if self._chart_editing_results.count() > 0:
                current = self._chart_editing_results.currentItem()
                if current is None:
                    current = self._chart_editing_results.item(0)
                    self._chart_editing_results.setCurrentItem(current)
                self._set_chart_editing_selected_visual(current)
            else:
                self._chart_edit_selected_song_id = None
                self._set_chart_editing_selected_visual(None)
        finally:
            self._chart_editing_results.setUpdatesEnabled(True)
            if viewport is not None:
                viewport.setUpdatesEnabled(True)
            self._chart_editing_results.viewport().update()

    def _on_chart_editing_continue_clicked(self) -> None:
        if not self._awaiting_chart_editing_action:
            return
        if self._is_playlevel_editing_mode():
            missing_count = self._missing_playlevel_values_count()
            confirmed_with_empty = False
            if missing_count > 0:
                if not self._confirm_action(
                    "Difficulty fields are empty. Finalize conversion anyway?"
                ):
                    self._set_chart_editing_attention(True)
                    return
                confirmed_with_empty = True
            if not confirmed_with_empty and not self._confirm_action("Apply difficulty values and finalize conversion?"):
                return
            if not self._apply_playlevel_overrides(allow_partial=True):
                self._set_chart_editing_attention(True)
                return
            self._remember_missing_difficulty_values()
            self._complete_playlevel_finalize()
            return

        context = self._pending_conversion_context
        if context is None:
            return
        has_edits = self._has_chart_name_overrides()
        if has_edits:
            message = "Apply edited fields and continue conversion?"
        else:
            message = "Skip editing and continue conversion?"
        if not self._confirm_action(message):
            return

        resolved_paths = self._resolve_current_conversion_paths()
        if resolved_paths is None:
            return
        sound_root, movie_root, project_root, results_root = resolved_paths
        include_stagefile = self._include_stagefile
        include_bga = self._include_bga
        include_preview = self._include_preview
        parallel_converting = self._parallel_converting

        charts = list(context["charts"])
        resolved_charts: list[SearchResult] = []
        for chart in charts:
            resolved_charts.append(self._apply_chart_name_override(chart))
        charts_to_convert, fully_overwrite = self._resolve_overwrite_policy(
            resolved_charts,
            results_root,
        )
        if not charts_to_convert:
            return

        self._awaiting_chart_editing_action = False
        self._pending_conversion_context = None
        self._set_chart_editing_attention(False)
        self._chart_editing_mode = "names"
        self._clear_chart_editing_warning_logs()
        self._refresh_chart_editing_header_controls()
        edited_count = self._edited_charts_count(charts_to_convert)
        self._begin_conversion(
            charts_to_convert,
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

    def _complete_playlevel_finalize(self) -> None:
        self._awaiting_chart_editing_action = False
        self._set_chart_editing_attention(False)
        self._chart_editing_mode = "names"
        self._playlevel_missing_entries.clear()
        self._playlevel_source_results.clear()
        self._playlevel_value_overrides.clear()
        for song_id_display in self._conversion_output_dirs.keys():
            self._set_conversion_chart_progress(song_id_display, 100)
        self._playlevel_pending_song_ids.clear()
        self._update_chart_editing_list()
        self._clear_chart_editing_warning_logs()
        self._conversion_active = False
        self._append_conversion_log(
            f"Finished. Success: {self._conversion_succeeded_total}, "
            f"Failed: {self._conversion_failed_total}"
        )
        self._history_runs = self._history_recorder.finalize()
        self._reload_conversion_history()
        self._clear_selected_charts_after_start()
        self._update_start_conversion_button_state()
        self._update_conversion_inputs_locked_state()
        if self._open_results_after_conversion:
            self._open_results_folder()

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
        self._clear_chart_editing_warning_logs()
        history_charts: list[SearchResult] = []
        for chart in charts:
            enriched = self._search_engine.ensure_genre(chart)
            if not enriched.game_name:
                enriched = self._search_engine.ensure_game_name(enriched)
            history_charts.append(enriched)
        self._history_recorder.start(history_charts)
        self._conversion_output_dirs.clear()
        self._conversion_chart_by_id_display = {chart.song_id_display: chart for chart in charts}
        self._reset_conversion_progress_rows(charts)
        stagefile_text = "yes" if include_stagefile else "no"
        bga_text = "yes" if include_bga else "no"
        preview_text = "yes" if include_preview else "no"
        self._append_conversion_log(
            f"Started. Charts: {len(charts)}, Edited: {edited_count}, "
            f"STAGEFILE: {stagefile_text}, BGA: {bga_text}, Audio preview: {preview_text}"
        )
        self._conversion_active = True
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()
        self._update_conversion_inputs_locked_state()
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
            match = re.match(r"^(\d{5})(?:\s+-\s+|\s+|$)", name)
            if match:
                ids.add(match.group(1))
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
            "Some chart folders already exist in the Results folder.\n"
            "Overwrite them?"
        )
        if self._confirm_action(question):
            return list(charts), True

        return [], False

    def _on_start_conversion(self) -> None:
        if self._conversion_active:
            return
        if self._awaiting_chart_editing_action:
            self._show_processing_page()
            self._set_chart_editing_attention(True)
            return
        initial_charts = self._selected_results_data()
        if not initial_charts:
            return

        include_bga = self._include_bga
        sound_path_text = self._sound_path.strip()
        movie_path_text = self._movie_path.strip()
        sound_empty = not sound_path_text
        movie_empty = not movie_path_text
        sound_root = Path(sound_path_text) if sound_path_text else None
        movie_root = Path(movie_path_text) if movie_path_text else None
        sound_invalid = (not sound_empty) and (
            sound_root is None or (not sound_root.is_dir())
        )
        movie_invalid = (not movie_empty) and (
            movie_root is None or (not movie_root.is_dir())
        )

        movie_video_exts = {".mp4", ".wmv", ".avi", ".mpg", ".mpeg", ".mov", ".mkv", ".webm"}
        movie_stems: set[str] = set()
        missing_sound_ids: list[str] = []
        missing_movie_bga: list[tuple[str, str]] = []
        charts_with_bga = 0

        if not sound_empty and not sound_invalid and sound_root is not None:
            for chart in initial_charts:
                song_id = chart.song_id_display
                if not self._path_has_chart_source(sound_root, song_id):
                    missing_sound_ids.append(song_id)

        if include_bga and not movie_empty and not movie_invalid and movie_root is not None:
            movie_stems = {
                entry.stem.lower()
                for entry in movie_root.iterdir()
                if entry.is_file() and entry.suffix.lower() in movie_video_exts
            }
            for chart in initial_charts:
                song_id = chart.song_id_display
                bga_name = str(self._bga_by_song_id.get(song_id, "")).strip()
                bga_key = Path(bga_name).stem.lower() if Path(bga_name).suffix else bga_name.lower()
                if bga_key:
                    charts_with_bga += 1
                    if bga_key not in movie_stems:
                        missing_movie_bga.append((song_id, bga_name))

        sound_effective_invalid = sound_invalid or (
            bool(initial_charts) and len(missing_sound_ids) == len(initial_charts)
        )
        all_bga_missing = charts_with_bga > 0 and len(missing_movie_bga) == charts_with_bga
        movie_effective_invalid = movie_invalid or (
            include_bga and (not movie_stems or all_bga_missing)
        )

        if sound_empty or movie_empty or sound_effective_invalid or movie_effective_invalid:
            if (sound_empty or sound_effective_invalid) and (movie_empty or movie_effective_invalid):
                if sound_empty and movie_empty:
                    question = "Sound and movie folder paths are not set.\nOpen File paths to set them?"
                else:
                    question = "Paths for sound and movie are invalid.\nOpen File paths to fix them?"
            elif sound_empty:
                question = "Path for sound is not set.\nOpen File paths to set it?"
            elif movie_empty:
                question = "Path for movie is not set.\nOpen File paths to set it?"
            elif sound_effective_invalid:
                question = "Path for sound is invalid.\nOpen File paths to fix it?"
            else:
                question = "Path for movie is invalid.\nOpen File paths to fix it?"
            if self._confirm_action(question):
                self._open_file_paths_dialog()
            return

        resolved_paths = self._resolve_current_conversion_paths()
        if resolved_paths is None:
            return
        sound_root, movie_root, project_root, results_root = resolved_paths

        if missing_sound_ids:
            if len(missing_sound_ids) == len(initial_charts):
                if self._confirm_action("Path for sound is invalid.\nOpen File paths to fix it?"):
                    self._open_file_paths_dialog()
            else:
                song_id = missing_sound_ids[0]
                self._show_info_dialog(
                    f"iidx2bms could not find {song_id} folder or {song_id}.ifs.\n"
                    "Check if \\contents\\data\\sound\\ path is correct."
                )
            return

        if include_bga and (not movie_stems or missing_movie_bga):
            all_bga_missing = charts_with_bga > 0 and len(missing_movie_bga) == charts_with_bga
            if not movie_stems or all_bga_missing:
                if self._confirm_action("Path for movie is invalid.\nOpen File paths to fix it?"):
                    self._open_file_paths_dialog()
            else:
                song_id, bga_name = missing_movie_bga[0]
                self._show_info_dialog(
                    f"iidx2bms could not find movie file for bga_filename \"{bga_name}\" "
                    f"(song {song_id}).\n"
                    "Check if \\contents\\data\\movie\\ path is correct."
                )
            return

        if self._conversion_logs_results is not None:
            self._conversion_logs_results.clear()
        self._reset_conversion_progress_rows([])
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
            self._chart_editing_mode = "names"
            self._awaiting_chart_editing_action = True
            self._set_chart_editing_attention(True)
            self._append_conversion_log(
                self._chart_editing_warning_message(flagged_count),
                error=True,
            )
            self._refresh_chart_editing_header_controls()
            return

        self._awaiting_chart_editing_action = False
        self._chart_editing_mode = "names"
        self._set_chart_editing_attention(False)
        self._refresh_chart_editing_header_controls()
        self._pending_conversion_context = None
        charts_to_convert, fully_overwrite = self._resolve_overwrite_policy(charts, results_root)
        if not charts_to_convert:
            return
        edited_count = self._edited_charts_count(charts_to_convert)
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
        rendered = message
        progress_match = re.match(r"^Progress:\s*(\d{5})\|(\d{1,3})\|(.+)$", rendered)
        if progress_match:
            song_id_display, percent_text, _stage = progress_match.groups()
            self._set_conversion_chart_progress(song_id_display, min(99, int(percent_text)))
            return
        start_match = re.match(r"^Start:\s*(\d{5})\s*$", rendered)
        if start_match:
            self._set_conversion_chart_progress(start_match.group(1), 0)
        done_match = re.match(r"^Done:\s*(\d{5})\s*->\s*(.+)\s*$", rendered)
        if done_match:
            song_id_display, output_path = done_match.groups()
            self._conversion_output_dirs[song_id_display] = Path(output_path.strip())
            self._set_conversion_chart_progress(song_id_display, 99)
            self._history_recorder.mark_success(song_id_display)
        failed_match = re.match(r"^Failed:\s*(\d{5})\s*:", rendered)
        if failed_match:
            song_id_display = failed_match.group(1)
            self._set_conversion_chart_failed(song_id_display)
            self._history_recorder.mark_failed(song_id_display)
        self._append_conversion_log(message)

    def _resolve_current_conversion_paths(self) -> tuple[Path, Path, Path, Path] | None:
        sound_path = self._sound_path.strip()
        sound_root = Path(sound_path)
        if not sound_path or not sound_root.is_dir():
            return None
        movie_path = self._movie_path.strip()
        movie_root = Path(movie_path)
        if not movie_path or not movie_root.is_dir():
            return None
        output_base_path = self._output_base_path.strip()
        output_base_root = (
            Path(output_base_path).expanduser()
            if output_base_path
            else self._default_output_base_path()
        )
        if output_base_root.exists() and not output_base_root.is_dir():
            return None
        results_root = output_base_root / "Results"
        project_root = self._project_root()
        return sound_root, movie_root, project_root, results_root

    def _on_conversion_worker_finished(self, succeeded: int, failed: int) -> None:
        self._conversion_succeeded_total += succeeded
        self._conversion_failed_total += failed
        self._pending_conversion_jobs -= 1
        if self._pending_conversion_jobs > 0:
            return
        self._active_conversion_workers.clear()
        missing_playlevels = self._collect_missing_playlevels()
        if missing_playlevels > 0:
            if (
                self._save_missing_difficulty_numbers
                and self._missing_playlevel_values_count() == 0
                and self._apply_playlevel_overrides(allow_partial=False)
            ):
                self._remember_missing_difficulty_values()
                self._complete_playlevel_finalize()
                return
            self._chart_editing_mode = "playlevel"
            self._awaiting_chart_editing_action = True
            missing_ids: list[str] = []
            for song_id, entries in self._playlevel_missing_entries.items():
                if not entries:
                    continue
                result = self._playlevel_source_results.get(song_id)
                if isinstance(result, SearchResult):
                    missing_ids.append(result.song_id_display)
                else:
                    missing_ids.append(f"{song_id:05d}")
            missing_ids = sorted(set(missing_ids))
            summary = ", ".join(f"ID: {song_id}" for song_id in missing_ids)
            self._append_conversion_log(
                f"Difficulty not found in .bme files for:\n{summary}.\n"
                "Check Chart Editing panel to continue.",
                warning=True,
            )
            self._update_chart_editing_list()
            for song_id_display in self._conversion_output_dirs.keys():
                if song_id_display not in self._playlevel_pending_song_ids:
                    self._set_conversion_chart_progress(song_id_display, 100)
            for song_id_display in self._playlevel_pending_song_ids:
                self._set_conversion_chart_pending(song_id_display, 99)
            self._set_chart_editing_attention(True)
            self._show_processing_page()
            self._update_start_conversion_button_state()
            self._update_conversion_inputs_locked_state()
            return

        self._conversion_active = False
        self._update_start_conversion_button_state()
        self._update_conversion_inputs_locked_state()
        for song_id_display in self._conversion_output_dirs.keys():
            self._set_conversion_chart_progress(song_id_display, 100)
        self._append_conversion_log(
            f"Finished. Success: {self._conversion_succeeded_total}, "
            f"Failed: {self._conversion_failed_total}"
        )
        self._history_runs = self._history_recorder.finalize()
        self._reload_conversion_history()
        self._clear_selected_charts_after_start()
        if self._open_results_after_conversion:
            self._open_results_folder()

    def _clear_selected_charts_after_start(self) -> None:
        if not self._conversion_active:
            self._history_recorder.clear()
        if self._selected_results is not None:
            self._selected_results.clear()
        self._selected_item_by_song_id.clear()
        self._selected_song_ids.clear()
        self._matched_selected_song_id = None
        self._chart_edit_selected_song_id = None
        self._chart_name_overrides.clear()
        self._chart_editing_mode = "names"
        self._playlevel_missing_entries.clear()
        self._playlevel_source_results.clear()
        self._playlevel_value_overrides.clear()
        self._playlevel_pending_song_ids.clear()
        self._conversion_output_dirs.clear()
        self._conversion_chart_by_id_display.clear()
        self._awaiting_chart_editing_action = False
        self._pending_conversion_context = None
        self._set_chart_editing_attention(False)
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()
        self._update_conversion_inputs_locked_state()

    def _toggle_parallel_converting(self) -> None:
        self._parallel_converting = not self._parallel_converting
        self._settings.setValue("conversion/parallel_converting", self._parallel_converting)
        self._settings.sync()

    def _toggle_fully_overwrite_results(self) -> None:
        self._fully_overwrite_results = not self._fully_overwrite_results
        self._settings.setValue("conversion/fully_overwrite_results", self._fully_overwrite_results)
        self._settings.sync()

    def _toggle_always_skip_chart_names_editing(self) -> None:
        if self._is_playlevel_editing_mode():
            self._always_skip_chart_names_editing = not self._always_skip_chart_names_editing
            self._settings.setValue(
                "conversion/always_skip_chart_names_editing",
                self._always_skip_chart_names_editing,
            )
            self._settings.sync()
            return

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

    def _toggle_open_results_after_conversion(self) -> None:
        self._open_results_after_conversion = not self._open_results_after_conversion
        self._settings.setValue(
            "conversion/open_results_after_conversion",
            self._open_results_after_conversion,
        )
        self._settings.sync()

    def _toggle_save_missing_difficulty_numbers(self) -> None:
        self._save_missing_difficulty_numbers = not self._save_missing_difficulty_numbers
        self._settings.setValue(
            "conversion/save_missing_difficulty_numbers",
            self._save_missing_difficulty_numbers,
        )
        self._settings.sync()
        self._invalidate_saved_diff_numbers_cache()
        self._refresh_search_result_widgets()
        self._refresh_selected_result_widgets()

    def _on_show_ascii_song_title_toggled(self, checked: bool) -> None:
        self._show_ascii_song_title = bool(checked)
        self._settings.setValue("ui/show_ascii_song_title", self._show_ascii_song_title)
        self._settings.sync()
        search_list = self._search_results
        selected_list = self._selected_results
        frozen_widgets: list[QWidget] = []
        for widget in (search_list, selected_list):
            if widget is None:
                continue
            frozen_widgets.append(widget)
            widget.setUpdatesEnabled(False)
            viewport = widget.viewport()
            if viewport is not None:
                frozen_widgets.append(viewport)
                viewport.setUpdatesEnabled(False)
        try:
            self._refresh_search_result_widgets()
            self._refresh_selected_result_widgets()
        finally:
            for widget in reversed(frozen_widgets):
                widget.setUpdatesEnabled(True)
                widget.update()

    def _on_chart_editing_current_item_changed(self, item: QListWidgetItem | None) -> None:
        if self._awaiting_chart_editing_action:
            self._set_chart_editing_attention(False)
        if item is None:
            self._chart_edit_selected_song_id = None
            self._set_chart_editing_selected_visual(None)
            self._refresh_chart_editing_header_controls()
            return
        song_id = item.data(Qt.ItemDataRole.UserRole)
        self._chart_edit_selected_song_id = song_id if isinstance(song_id, int) else None
        self._set_chart_editing_selected_visual(item)
        self._refresh_chart_editing_header_controls()

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
        target_widget = widget
        if widget.objectName() != "SelectedChartItem":
            nested = widget.findChild(QFrame, "SelectedChartItem")
            if nested is not None:
                target_widget = nested
        target_widget.setProperty("selected", True)
        target_widget.style().unpolish(target_widget)
        target_widget.style().polish(target_widget)
        target_widget.update()
        self._chart_edit_selected_widget = target_widget

    def _append_conversion_log(self, message: str, error: bool = False, warning: bool = False) -> None:
        rendered = message
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
                f'<span style="color:#40c977;">{html.escape(success_count)}</span>, '
                "Failed: "
                f'<span style="color:#be0420;">{html.escape(failed_count)}</span>'
            )
        else:
            if warning:
                line_color = "#b88f00"
            elif error or rendered.startswith("Failed:"):
                line_color = "#be0420"
            else:
                line_color = "#f0f0f0"
            rendered_html = html.escape(rendered).replace("\n", "<br/>")
            cursor.insertHtml(f'<span style="color:{line_color};">{rendered_html}</span>')
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
            base_result = item.data(Qt.ItemDataRole.UserRole + 2)
            if not isinstance(base_result, SearchResult):
                base_result = item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(base_result, SearchResult):
                continue
            result = base_result
            if self._show_chart_difficulty:
                result = self._search_engine.ensure_levels(result)
                result = self._apply_saved_levels_to_result(result)
            if self._show_chart_genre:
                result = self._search_engine.ensure_genre(result)
            if self._show_game_version and not result.game_name:
                result = self._search_engine.ensure_game_name(result)
            item.setData(Qt.ItemDataRole.UserRole + 2, base_result)
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
            base_result = item.data(Qt.ItemDataRole.UserRole + 2)
            if not isinstance(base_result, SearchResult):
                base_result = item.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(base_result, SearchResult):
                continue
            display_result = base_result
            if self._show_chart_difficulty:
                base_result = self._search_engine.ensure_levels(base_result)
                display_result = self._apply_saved_levels_to_result(base_result)
            if self._show_chart_genre:
                base_result = self._search_engine.ensure_genre(base_result)
                display_result = self._search_engine.ensure_genre(display_result)
            if self._show_game_version:
                if not base_result.game_name:
                    base_result = self._search_engine.ensure_game_name(base_result)
                if not display_result.game_name:
                    display_result = self._search_engine.ensure_game_name(display_result)
            item.setData(Qt.ItemDataRole.UserRole + 2, base_result)
            result = self._apply_chart_name_override(display_result)
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
        if self._conversion_active:
            return
        if self._search_results is None:
            return
        self._add_search_result_item(self._search_results.currentItem())

    def _on_clear_search_clicked(self) -> None:
        if self._conversion_active:
            return
        if self._search_input is not None:
            self._search_input.clear()

    def _add_search_result_item(self, item: QListWidgetItem | None) -> None:
        if self._conversion_active:
            return
        if item is None:
            return
        result = item.data(Qt.ItemDataRole.UserRole + 2)
        if not isinstance(result, SearchResult):
            result = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResult):
            return
        if result.song_id in self._selected_song_ids:
            self._focus_selected_chart(result.song_id)
            return
        self._add_selected_chart(result)
        self._focus_selected_chart(result.song_id)

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
        row.setProperty("conversionLocked", self._conversion_active)
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
        primary_label.setProperty("conversionLocked", self._conversion_active)
        primary_label.setWordWrap(False)
        primary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(primary_label)

        secondary_label = MarqueeLabel(self._secondary_line_text(result))
        secondary_label.setObjectName("SearchChartSecondary")
        secondary_label.setProperty("conversionLocked", self._conversion_active)
        secondary_label.setWordWrap(False)
        secondary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(secondary_label)

        row_layout.addWidget(left_column, 1)
        row_layout.addWidget(self._build_levels_column(result, "SearchChartLevels"), 0)
        return row

    def _build_selected_result_widget(self, result: SearchResult, item: QListWidgetItem) -> QWidget:
        row = QFrame()
        row.setObjectName("SelectedChartItem")
        row.setProperty("conversionLocked", self._conversion_active)
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
        primary_label.setProperty("conversionLocked", self._conversion_active)
        primary_label.setWordWrap(False)
        primary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(primary_label)

        secondary_label = MarqueeLabel(self._secondary_line_text(result))
        secondary_label.setObjectName("SelectedChartSecondary")
        secondary_label.setProperty("conversionLocked", self._conversion_active)
        secondary_label.setWordWrap(False)
        secondary_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        left_layout.addWidget(secondary_label)

        row_layout.addWidget(left_column, 1)
        row_layout.addWidget(self._build_levels_column(result, "SelectedChartLevels"), 0)

        remove_button = QPushButton()
        remove_button.setObjectName("TrashButton")
        remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_button.setProperty("conversionLocked", self._conversion_active)
        if self._conversion_active:
            remove_button.setToolTip("See Processing & Edit tab to continue")
        else:
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
        self._clear_previous_conversion_history_if_needed()
        base_result = self._search_engine.ensure_levels(result)
        result = self._apply_saved_levels_to_result(base_result)

        self._selected_song_ids.add(result.song_id)
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, result.song_id)
        item.setData(Qt.ItemDataRole.UserRole + 1, result)
        item.setData(Qt.ItemDataRole.UserRole + 2, base_result)
        row = self._build_selected_result_widget(result, item)

        item.setSizeHint(QSize(0, 56))
        self._selected_results.addItem(item)
        self._selected_results.setItemWidget(item, row)
        self._selected_item_by_song_id[result.song_id] = item
        self._update_chart_editing_list()
        self._update_start_conversion_button_state()

    def _clear_previous_conversion_history_if_needed(self) -> None:
        if self._conversion_active or self._selected_song_ids:
            return

        has_logs = False
        if self._conversion_logs_results is not None:
            has_logs = bool(self._conversion_logs_results.toPlainText().strip())
        has_progress = bool(self._conversion_progress_bars)
        if not has_logs and not has_progress:
            return

        self._awaiting_chart_editing_action = False
        self._pending_conversion_context = None
        self._set_chart_editing_attention(False)
        if self._conversion_logs_results is not None:
            self._conversion_logs_results.clear()
        self._reset_conversion_progress_rows([])

    def _remove_selected_chart_item(self, item: QListWidgetItem) -> None:
        if self._conversion_active:
            return
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
            self._reset_conversion_progress_rows([])
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

    def _hide_global_hover_hint(self) -> None:
        if self._global_hover_hint is None or self._global_hover_hint_closing:
            return
        hint = self._global_hover_hint
        self._global_hover_hint = None
        self._global_hover_hint_closing = True
        try:
            hint.close()
        finally:
            self._global_hover_hint_closing = False

    def _show_global_hover_hint(self, widget: QWidget, text: str, global_pos: QPoint | None = None) -> None:
        if not text.strip():
            self._hide_global_hover_hint()
            return
        self._hide_global_hover_hint()
        hint = HoverHint(text)
        hint.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        hint.adjustSize()
        if global_pos is None:
            global_pos = QCursor.pos()
        hint.move(global_pos + QPoint(12, 16))
        hint.show()
        hint.raise_()
        self._global_hover_hint = hint

    def _tooltip_owner_and_text(self, widget: QWidget) -> tuple[QWidget | None, str]:
        current: QWidget | None = widget
        while current is not None:
            text = current.toolTip().strip()
            if text:
                return current, text
            current = current.parentWidget()
        return None, ""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            if self._tooltip_filter_active:
                return False
            if isinstance(watched, QWidget):
                owner, text = self._tooltip_owner_and_text(watched)
                if owner is not None and text:
                    global_pos = None
                    if hasattr(event, "globalPos"):
                        try:
                            global_pos = event.globalPos()
                        except Exception:
                            global_pos = None
                    self._tooltip_filter_active = True
                    try:
                        self._show_global_hover_hint(owner, text, global_pos=global_pos)
                    finally:
                        self._tooltip_filter_active = False
                    return True
            return False

        if event.type() in (
            QEvent.Type.Leave,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.Wheel,
            QEvent.Type.FocusOut,
            QEvent.Type.Hide,
        ):
            self._hide_global_hover_hint()

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
            self._page_stack.setCurrentIndex(self._main_page_index)
        self._set_active_page_button(self._main_page_button, True)
        self._set_active_page_button(self._processing_page_button, False)
        self._set_active_page_button(self._history_page_button, False)

    def _show_processing_page(self) -> None:
        if self._page_stack is not None:
            self._page_stack.setCurrentIndex(self._processing_page_index)
        self._set_active_page_button(self._main_page_button, False)
        self._set_active_page_button(self._processing_page_button, True)
        self._set_active_page_button(self._history_page_button, False)

    def _show_history_page(self) -> None:
        self._reload_conversion_history()
        if self._page_stack is not None:
            self._page_stack.setCurrentIndex(self._history_page_index)
        self._set_active_page_button(self._main_page_button, False)
        self._set_active_page_button(self._processing_page_button, False)
        self._set_active_page_button(self._history_page_button, True)

    def _on_clear_history_clicked(self) -> None:
        if not self._confirm_action("Clear all conversion history?"):
            return
        self._history_store.save_runs([])
        self._history_runs = []
        self._set_history_selected_visual(None)
        self._reload_conversion_history()

    def _reload_conversion_history(self) -> None:
        if self._history_previous_results is None or self._history_details_results is None:
            return
        self._history_runs = self._history_store.load_runs()
        self._backfill_history_metadata()
        if self._history_clear_button is not None:
            has_runs = bool(self._history_runs)
            self._history_clear_button.setEnabled(has_runs)
            self._history_clear_button.setToolTip("" if has_runs else "No history to clear")
        if self._history_add_to_selected_button is not None:
            has_runs = bool(self._history_runs)
            self._history_add_to_selected_button.setEnabled(has_runs)
            self._history_add_to_selected_button.setToolTip(
                "" if has_runs else "No conversion session selected"
            )
        selected_run_id: str | None = None
        current_item = self._history_previous_results.currentItem()
        if current_item is not None:
            current_id = current_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(current_id, str):
                selected_run_id = current_id
        render_runs_list(self._history_previous_results, self._history_runs)
        selected_item = None
        if selected_run_id:
            for row_index in range(self._history_previous_results.count()):
                candidate = self._history_previous_results.item(row_index)
                if candidate.data(Qt.ItemDataRole.UserRole) == selected_run_id:
                    selected_item = candidate
                    break
        if selected_item is None and self._history_previous_results.count() > 0:
            selected_item = self._history_previous_results.item(0)
        if selected_item is not None:
            self._history_previous_results.setCurrentItem(selected_item)
            run_id = selected_item.data(Qt.ItemDataRole.UserRole)
            run = find_run_by_id(self._history_runs, run_id) if isinstance(run_id, str) else None
            render_run_details(self._history_details_results, run)
            if self._history_add_to_selected_button is not None:
                can_add = run is not None and bool(run.charts)
                self._history_add_to_selected_button.setEnabled(can_add)
                self._history_add_to_selected_button.setToolTip(
                    "" if can_add else "No charts in selected session"
                )
        else:
            self._set_history_selected_visual(None)
            render_run_details(self._history_details_results, None)
            if self._history_add_to_selected_button is not None:
                self._history_add_to_selected_button.setEnabled(False)
                self._history_add_to_selected_button.setToolTip("No conversion session selected")

    def _on_history_run_selected(self, item: QListWidgetItem | None) -> None:
        self._set_history_selected_visual(item)
        if self._history_details_results is None:
            return
        if item is None:
            render_run_details(self._history_details_results, None)
            if self._history_add_to_selected_button is not None:
                self._history_add_to_selected_button.setEnabled(False)
                self._history_add_to_selected_button.setToolTip("No conversion session selected")
            return
        run_id = item.data(Qt.ItemDataRole.UserRole)
        run = find_run_by_id(self._history_runs, run_id) if isinstance(run_id, str) else None
        render_run_details(self._history_details_results, run)
        if self._history_add_to_selected_button is not None:
            can_add = run is not None and bool(run.charts)
            self._history_add_to_selected_button.setEnabled(can_add)
            self._history_add_to_selected_button.setToolTip(
                "" if can_add else "No charts in selected session"
            )

    def _on_add_history_run_to_selected_clicked(self) -> None:
        if self._history_previous_results is None:
            return
        selected_item = self._history_previous_results.currentItem()
        if selected_item is None:
            return
        run_id = selected_item.data(Qt.ItemDataRole.UserRole)
        run = find_run_by_id(self._history_runs, run_id) if isinstance(run_id, str) else None
        if run is None or not run.charts:
            return

        added_any = False
        for entry in run.charts:
            song_id_display = entry.song_id_display.strip()
            if not song_id_display.isdigit():
                continue
            try:
                matches = self._search_engine.search(song_id_display, 1)
            except Exception:
                continue
            if not matches:
                continue
            resolved = matches[0]
            resolved = self._search_engine.ensure_levels(resolved)
            resolved = self._search_engine.ensure_genre(resolved)
            if not resolved.game_name:
                resolved = self._search_engine.ensure_game_name(resolved)
            had_song = resolved.song_id in self._selected_song_ids
            self._add_selected_chart(resolved)
            if not had_song and resolved.song_id in self._selected_song_ids:
                added_any = True

        if added_any:
            self._refresh_selected_result_widgets()
        self._show_main_page()

    def _backfill_history_metadata(self) -> None:
        dirty = False
        for run in self._history_runs:
            for entry in run.charts:
                if entry.genre.strip() and entry.game_name.strip():
                    has_levels = (
                        entry.spb_level > 0
                        or entry.spn_level > 0
                        or entry.sph_level > 0
                        or entry.spa_level > 0
                        or entry.spl_level > 0
                        or entry.dpb_level > 0
                        or entry.dpn_level > 0
                        or entry.dph_level > 0
                        or entry.dpa_level > 0
                        or entry.dpl_level > 0
                    )
                    if has_levels:
                        continue
                song_id_display = entry.song_id_display.strip()
                if not song_id_display.isdigit():
                    continue
                try:
                    matches = self._search_engine.search(song_id_display, 1)
                except Exception:
                    continue
                if not matches:
                    continue
                resolved = matches[0]
                resolved = self._search_engine.ensure_genre(resolved)
                if not resolved.game_name:
                    resolved = self._search_engine.ensure_game_name(resolved)
                if not entry.genre.strip() and resolved.genre:
                    entry.genre = resolved.genre
                    dirty = True
                if not entry.game_name.strip() and resolved.game_name:
                    entry.game_name = resolved.game_name
                    dirty = True
                resolved = self._search_engine.ensure_levels(resolved)
                if entry.spb_level != resolved.spb_level:
                    entry.spb_level = resolved.spb_level
                    dirty = True
                if entry.spn_level != resolved.spn_level:
                    entry.spn_level = resolved.spn_level
                    dirty = True
                if entry.sph_level != resolved.sph_level:
                    entry.sph_level = resolved.sph_level
                    dirty = True
                if entry.spa_level != resolved.spa_level:
                    entry.spa_level = resolved.spa_level
                    dirty = True
                if entry.spl_level != resolved.spl_level:
                    entry.spl_level = resolved.spl_level
                    dirty = True
                if entry.dpb_level != resolved.dpb_level:
                    entry.dpb_level = resolved.dpb_level
                    dirty = True
                if entry.dpn_level != resolved.dpn_level:
                    entry.dpn_level = resolved.dpn_level
                    dirty = True
                if entry.dph_level != resolved.dph_level:
                    entry.dph_level = resolved.dph_level
                    dirty = True
                if entry.dpa_level != resolved.dpa_level:
                    entry.dpa_level = resolved.dpa_level
                    dirty = True
                if entry.dpl_level != resolved.dpl_level:
                    entry.dpl_level = resolved.dpl_level
                    dirty = True
        if dirty:
            self._history_store.save_runs(self._history_runs)

    def _set_history_selected_visual(self, item: QListWidgetItem | None) -> None:
        if self._history_previous_results is None:
            return
        if self._history_selected_widget is not None:
            self._history_selected_widget.setProperty("selected", False)
            self._history_selected_widget.style().unpolish(self._history_selected_widget)
            self._history_selected_widget.style().polish(self._history_selected_widget)
            self._history_selected_widget.update()
            self._history_selected_widget = None
        if item is None:
            return
        widget = self._history_previous_results.itemWidget(item)
        if widget is None:
            return
        target_widget = widget
        if widget.objectName() != "SelectedChartItem":
            nested = widget.findChild(QFrame, "SelectedChartItem")
            if nested is not None:
                target_widget = nested
        target_widget.setProperty("selected", True)
        target_widget.style().unpolish(target_widget)
        target_widget.style().polish(target_widget)
        target_widget.update()
        self._history_selected_widget = target_widget

    def _show_popup(self, button: QWidget, items: list[tuple[str, str | None]], on_action=None) -> None:
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
            if hasattr(owner, "setDown"):
                owner.setDown(False)
            owner.clearFocus()
            QApplication.sendEvent(owner, QEvent(QEvent.Type.Leave))
            owner.style().unpolish(owner)
            owner.style().polish(owner)
            owner.update()
