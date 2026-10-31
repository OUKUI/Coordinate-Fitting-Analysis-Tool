"""Fluent 系统集成：托盘图标 / 文件对话框封装 / 通知中心。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QMenu, QPushButton, QScrollArea, QSystemTrayIcon,
                               QVBoxLayout, QWidget)

from ..theme import palette as P
from .icons import CloseButton, IconBadge


def make_letter_icon(text: str, color: str = "#0067C0", size: int = 64) -> QIcon:
    """根据文字首字符生成一个圆角色块图标。"""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawRoundedRect(0, 0, size, size, size // 4, size // 4)
    f = QFont()
    f.setBold(True)
    f.setPixelSize(int(size * 0.5))
    p.setFont(f)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter,
               (text[:1] or "◆").upper())
    p.end()
    return QIcon(pm)


class FluentTrayIcon(QSystemTrayIcon):
    """Fluent 系统托盘图标：深色右键菜单 + 气泡消息。"""

    def __init__(self, text: str = "", tooltip: str = "", parent=None,
                 color: str = "#0067C0") -> None:
        super().__init__(parent)
        self.setIcon(make_letter_icon(text, color))
        self.setToolTip(tooltip or text)
        self._menu = QMenu()
        self.setContextMenu(self._menu)

    def add_action(self, text: str, callback=None) -> None:
        self._menu.addAction(text, callback)

    def add_separator(self) -> None:
        self._menu.addSeparator()

    def add_quit(self, text: str = "退出") -> None:
        from PySide6.QtWidgets import QApplication
        self.add_separator()
        self._menu.addAction(text, QApplication.instance().quit)

    def show_message(self, title: str, message: str,
                     kind: str = "info", duration: int = 3000) -> None:
        icon = {KIND_INFO: QSystemTrayIcon.MessageIcon.Information,
                KIND_SUCCESS: QSystemTrayIcon.MessageIcon.Information,
                KIND_WARNING: QSystemTrayIcon.MessageIcon.Warning,
                KIND_ERROR: QSystemTrayIcon.MessageIcon.Critical}.get(
                    kind, QSystemTrayIcon.MessageIcon.Information)
        self.showMessage(title, message, icon, duration)


KIND_INFO = "info"
KIND_SUCCESS = "success"
KIND_WARNING = "warning"
KIND_ERROR = "error"


class FluentSystemDialog:
    """原生文件/目录/颜色对话框便捷封装（系统主题自动适配）。"""

    @staticmethod
    def open_file(parent=None, title: str = "选择文件", directory: str = "",
                  filters: str = "所有文件 (*.*)") -> str:
        path, _ = QFileDialog.getOpenFileName(parent, title, directory, filters)
        return path

    @staticmethod
    def open_files(parent=None, title: str = "选择文件", directory: str = "",
                   filters: str = "所有文件 (*.*)") -> list:
        paths, _ = QFileDialog.getOpenFileNames(parent, title, directory, filters)
        return paths

    @staticmethod
    def save_file(parent=None, title: str = "保存文件", directory: str = "",
                  filters: str = "所有文件 (*.*)") -> str:
        path, _ = QFileDialog.getSaveFileName(parent, title, directory, filters)
        return path

    @staticmethod
    def directory(parent=None, title: str = "选择文件夹",
                  directory: str = "") -> str:
        return QFileDialog.getExistingDirectory(parent, title, directory)


class FluentNotificationCenter(QWidget):
    """Fluent 通知中心：收集消息条，自动消失，可清空。"""

    notificationAdded = Signal(str, str, str)

    def __init__(self, parent=None, width: int = 320) -> None:
        super().__init__(parent)
        self.setFixedWidth(width)
        self.setObjectName("NotificationCenter")
        self.setStyleSheet(f"""
            #NotificationCenter {{
                background-color: {P.bg_layer_glass};
                border: 1px solid {P.divider};
                border-radius: 8px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("通知")
        title.setStyleSheet(
            "font-size: 13px; font-weight: 600; background: transparent;")
        header.addWidget(title)
        header.addStretch(1)
        clear_btn = QPushButton("全部清除")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {P.accent_light};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{ text-decoration: underline; }}
        """)
        clear_btn.clicked.connect(self.clear)
        header.addWidget(clear_btn)
        root.addLayout(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setContentsMargins(0, 0, 2, 0)
        self._vbox.setSpacing(6)
        self._vbox.addStretch(1)
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll, 1)

    def notify(self, title: str, message: str, kind: str = "info",
               duration: int = 5000) -> None:
        row = _NotificationRow(title, message, kind)
        row.closed.connect(lambda r=row: self._remove(r))
        self._vbox.insertWidget(self._vbox.count() - 1, row)
        if duration > 0:
            QTimer.singleShot(duration, row.close)
        self.notificationAdded.emit(title, message, kind)

    def clear(self) -> None:
        rows = [self._vbox.itemAt(i).widget()
                for i in range(self._vbox.count())
                if self._vbox.itemAt(i).widget() is not None]
        for r in rows:
            if isinstance(r, _NotificationRow):
                r.close()

    def _remove(self, row: "_NotificationRow") -> None:
        self._vbox.removeWidget(row)
        row.deleteLater()


class _NotificationRow(QFrame):
    closed = Signal()

    def __init__(self, title: str, message: str, kind: str = "info",
                 parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("NotifyRow")
        self.setStyleSheet(f"""
            #NotifyRow {{
                background-color: {P.fill_layer};
                border: 1px solid {P.divider};
                border-radius: 6px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 6, 8)
        lay.setSpacing(8)
        lay.addWidget(IconBadge(kind, size=22), 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        t = QLabel(title)
        t.setStyleSheet(
            "font-size: 12px; font-weight: 600; background: transparent;")
        text_col.addWidget(t)
        m = QLabel(message)
        m.setWordWrap(True)
        m.setStyleSheet(
            "font-size: 11px; color: #A0A0A0; background: transparent;")
        text_col.addWidget(m)
        lay.addLayout(text_col, 1)

        close = CloseButton(self, size=16)
        close.clicked.connect(lambda: self.closed.emit())
        lay.addWidget(close, 0, Qt.AlignmentFlag.AlignTop)
