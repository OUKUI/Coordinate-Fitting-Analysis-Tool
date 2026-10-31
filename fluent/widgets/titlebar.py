"""Fluent 无边框窗口：自绘标题栏 + 圆角 + Acrylic 毛玻璃（Windows）。

标题栏支持：拖动移动、双击最大化/还原、最小化/最大化/关闭按钮。
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from ..theme import palette as P

_TITLEBAR_HEIGHT = 40


def _hwnd(widget) -> int | None:
    if sys.platform != "win32":
        return None
    try:
        return int(widget.winId())
    except Exception:  # noqa: BLE001
        return None


def enable_blur_behind(widget, enabled: bool = True) -> bool:
    """Win 平台 DWM 模糊背景；失败静默返回 False。"""
    if sys.platform != "win32":
        return False
    import ctypes
    try:
        hwnd = _hwnd(widget)
        if hwnd is None:
            return False
        class DWM_BLURBEHIND(ctypes.Structure):
            _fields_ = [("dwFlags", ctypes.c_uint),
                        ("fEnable", ctypes.c_int),
                        ("hRgnBlur", ctypes.c_void_p),
                        ("fTransitionOnMaximized", ctypes.c_int)]
        bb = DWM_BLURBEHIND()
        bb.dwFlags = 1  # DWM_BB_ENABLE
        bb.fEnable = 1 if enabled else 0
        bb.hRgnBlur = None
        bb.fTransitionOnMaximized = 0
        ctypes.windll.dwmapi.DwmEnableBlurBehindWindow(
            ctypes.c_void_p(hwnd), ctypes.byref(bb))
        return True
    except Exception:  # noqa: BLE001
        return False


def enable_acrylic(widget, tint: int = 0x8C202020, opacity: float = 0.85,
                   enabled: bool = True) -> bool:
    """Win10 1803+ 丙烯酸效果（tint 为 0xAABBGGRR）；失败回退为 blur。"""
    if sys.platform != "win32":
        return False
    import ctypes
    try:
        hwnd = _hwnd(widget)
        if hwnd is None:
            return False
        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int),
                        ("AccentFlags", ctypes.c_int),
                        ("GradientColor", ctypes.c_uint),
                        ("AnimationId", ctypes.c_int)]
        class WINCOMPATTRDATA(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int),
                        ("Data", ctypes.c_void_p),
                        ("SizeOfData", ctypes.c_size_t)]
        accent = ACCENT_POLICY()
        accent.AccentState = 4 if enabled else 0  # ACRYLIC / DISABLED
        accent.AccentFlags = 2 if enabled else 0
        accent.GradientColor = int(tint * opacity) & 0xFFFFFFFF if enabled else 0
        data = WINCOMPATTRDATA(19,
                               ctypes.cast(ctypes.pointer(accent),
                                           ctypes.c_void_p),
                               ctypes.sizeof(accent))
        ctypes.windll.user32.SetWindowCompositionAttribute(
            ctypes.c_void_p(hwnd), ctypes.byref(data))
        return True
    except Exception:  # noqa: BLE001
        return False


class FluentTitleBar(QWidget):
    """Fluent 自绘标题栏。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(_TITLEBAR_HEIGHT)
        self.setObjectName("FluentTitleBar")
        self.setStyleSheet(f"""
            #FluentTitleBar {{ background: transparent; }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 0, 0)
        lay.setSpacing(0)

        icon = QLabel("◆")
        icon.setStyleSheet("color: #4CC2FF; background: transparent; font-size: 13px;")
        lay.addWidget(icon)
        lay.addSpacing(8)

        self._title = QLabel(title)
        self._title.setStyleSheet(
            "color: #FFFFFF; background: transparent; font-size: 12px;")
        lay.addWidget(self._title)
        lay.addStretch(1)

        self._min_btn = self._win_button("─", "min")
        self._max_btn = self._win_button("□", "max")
        self._close_btn = self._win_button("✕", "close")

        lay.addWidget(self._min_btn)
        lay.addWidget(self._max_btn)
        lay.addWidget(self._close_btn)

        self._min_btn.clicked.connect(self._on_min)
        self._max_btn.clicked.connect(self._on_max)
        self._close_btn.clicked.connect(self._on_close)

        self._drag_start = None

    def _win_button(self, glyph: str, role: str) -> QPushButton:
        btn = QPushButton(glyph)
        btn.setFixedSize(46, _TITLEBAR_HEIGHT)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_bg = "#C42B1C"
        close_hover = "#E74856"
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #D0D0D0;
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {close_bg if role == "close" else "#3A3A3A"};
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: {close_hover if role == "close" else "#2E2E2E"};
            }}
        """)
        return btn

    def set_title(self, text: str) -> None:
        self._title.setText(text)

    # ---- 窗口操作 ----
    def _on_min(self) -> None:
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        w.showMinimized()

    def _on_max(self) -> None:
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def _on_close(self) -> None:
        self.window().close()

    # ---- 拖动 ----
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_start is not None and event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if not win.isMaximized():
                win.startSystemMove()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_max()
        super().mouseDoubleClickEvent(event)


class FluentFramelessWindow(QWidget):
    """Fluent 无边框圆角窗口：自绘标题栏 + 内容区，可启用 Acrylic 毛玻璃。

    用法::

        win = FluentFramelessWindow("我的窗口", 900, 600)
        win.set_content(widget)
        win.set_acrylic(True)
        win.show()
    """

    def __init__(self, title: str = "", width: int = 900, height: int = 600,
                 content=None) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setMinimumSize(420, 320)
        self._radius = 8

        self._frame = QFrame(self)
        self._frame.setObjectName("FramelessFrame")
        lay = QVBoxLayout(self._frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._titlebar = FluentTitleBar(title, self._frame)
        lay.addWidget(self._titlebar)

        self._content_host = QWidget(self._frame)
        self._host_lay = QVBoxLayout(self._content_host)
        self._host_lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._content_host, 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._frame)

        if content is not None:
            self.set_content(content)
        self._apply_style(solid=True)
        self._acrylic = False

    def _apply_style(self, solid: bool) -> None:
        if solid:
            bg = "rgba(32, 32, 32, 245)"
        else:
            bg = "rgba(32, 32, 32, 190)"  # 半透明让毛玻璃透出
        self._frame.setStyleSheet(f"""
            #FramelessFrame {{
                background-color: {bg};
                border-radius: {self._radius}px;
            }}
        """)

    def set_content(self, widget: QWidget) -> None:
        from ..window import make_scrollable
        self._host_lay.addWidget(make_scrollable(widget))

    def set_title(self, text: str) -> None:
        self._titlebar.set_title(text)
        self.setWindowTitle(text)

    def set_acrylic(self, on: bool = True) -> None:
        self._acrylic = on
        if on:
            ok = enable_acrylic(self)
            if not ok:
                ok = enable_blur_behind(self)
            self._apply_style(solid=not ok)
        else:
            enable_acrylic(self, enabled=False)
            enable_blur_behind(self, False)
            self._apply_style(solid=True)

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            maxed = self.isMaximized()
            self._radius = 0 if maxed else 8
            self._frame.setStyleSheet(self._frame.styleSheet())
            self._apply_style(solid=not self._acrylic)
