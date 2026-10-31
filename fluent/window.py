"""Fluent 风格主窗口 / 对话框基类。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QMainWindow,
                               QScrollArea, QSizePolicy)

from .styles import build_global_qss


def apply_theme(app) -> None:
    """为 QApplication 应用全局 Fluent 深色主题（进程内调用一次即可）。"""
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    app.setStyleSheet(build_global_qss())
    return app


def clamp_to_screen(widget) -> None:
    """把窗口收拢到当前屏幕可用区域内，避免高缩放比下内容被裁切。

    - 窗口尺寸超过屏幕时收缩到屏幕大小（并相应降低最小尺寸）
    - 窗口位置超出屏幕时移回屏幕内
    """
    screen = widget.screen() or QApplication.primaryScreen()
    if screen is None:
        return
    geo = screen.availableGeometry()
    if widget.minimumWidth() > geo.width():
        widget.setMinimumWidth(max(320, geo.width()))
    if widget.minimumHeight() > geo.height():
        widget.setMinimumHeight(max(240, geo.height()))
    widget.resize(min(widget.width(), geo.width()),
                  min(widget.height(), geo.height()))
    x = max(geo.left(), min(widget.x(), geo.right() - widget.width() + 1))
    y = max(geo.top(), min(widget.y(), geo.bottom() - widget.height() + 1))
    widget.move(x, y)


def make_scrollable(content) -> QScrollArea:
    """把内容放入滚动容器：内容超高/超宽时出现滚动条，保证不裁切。"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(content)
    return scroll


class FluentWindow(QMainWindow):
    """Fluent 深色主窗口。

    特性：
    - 内容自动放入滚动容器，超高/超宽时可滚动，内容不会被裁切
    - 显示时自动收拢到屏幕可用区域内（适配高缩放比 / 小屏）
    """

    def __init__(self, title: str = "", width: int = 920, height: int = 600,
                 central_widget=None, maximized: bool = False) -> None:
        super().__init__()
        self._requested_size = (width, height)
        self._maximized = maximized
        self._shown = False
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setMinimumSize(420, 320)
        if central_widget is not None:
            self.setCentralWidget(central_widget)

    def setCentralWidget(self, widget) -> None:
        super().setCentralWidget(make_scrollable(widget))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._shown:
            self._shown = True
            if self._maximized:
                self.showMaximized()
                return
            # 恢复请求尺寸（设置滚动中央控件可能被布局收缩）
            if self._requested_size:
                self.resize(*self._requested_size)
        if not self.isMaximized():
            clamp_to_screen(self)


class FluentDialog(QDialog):
    """Fluent 深色对话框。"""

    def __init__(self, title: str = "", width: int = 480, height: int = 360,
                 parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        clamp_to_screen(self)


class FluentApp:
    """便捷入口：创建已应用深色主题的 QApplication。

    若进程内已存在 QApplication 实例（例如由 run_demo.py 的选择弹窗
    或宿主程序创建），则直接复用，避免重复创建导致崩溃。
    """

    def __init__(self, argv=None) -> None:
        existing = QApplication.instance()
        if existing is not None:
            self.qt_app = existing
            return
        self.qt_app = QApplication(argv if argv is not None else [])
        apply_theme(self.qt_app)

    def exec(self) -> int:
        return self.qt_app.exec()
