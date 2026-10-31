"""Fluent 信息栏（InfoBar）：info / success / warning / error。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ..theme import palette as P
from .icons import CloseButton, IconBadge, _kind_color


class FluentInfoBar(QFrame):
    """Fluent 风格信息栏。

    kind 取值：info / success / warning / error。
    通过 classmethod 快速弹出，或作为控件嵌入布局。
    """

    closed = Signal()

    def __init__(self, title: str = "", message: str = "", kind: str = "info",
                 closable: bool = True, parent=None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.setObjectName("InfoBar")
        self._tint = QColor(_kind_color(kind))
        self.setStyleSheet("#InfoBar { background: transparent; border: none; }")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 8, 10)
        lay.setSpacing(12)

        lay.addWidget(IconBadge(kind, size=28), 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 600; background: transparent;")
        text_col.addWidget(self.title_lbl)
        self.message_lbl = QLabel(message)
        self.message_lbl.setWordWrap(True)
        self.message_lbl.setStyleSheet(
            "font-size: 12px; color: #BDBDBD; background: transparent;")
        text_col.addWidget(self.message_lbl)
        lay.addLayout(text_col, 1)

        if closable:
            btn = CloseButton(self, size=24)
            btn.clicked.connect(self._close)
            lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignTop)
        self._clickable_close = closable

    def _close(self) -> None:
        self.hide()
        self.closed.emit()

    def set_text(self, title: str = "", message: str = "") -> None:
        if title:
            self.title_lbl.setText(title)
        if message:
            self.message_lbl.setText(message)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(self._tint)
        bg.setAlpha(34)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(self.rect(), 6, 6)

        # 左侧色条
        p.setBrush(self._tint)
        p.drawRoundedRect(QRectF(0, 6, 4, self.height() - 12), 2, 2)
        p.end()

    @classmethod
    def info(cls, title: str = "", message: str = "", parent=None) -> "FluentInfoBar":
        return cls(title, message, "info", parent=parent)

    @classmethod
    def success(cls, title: str = "", message: str = "", parent=None) -> "FluentInfoBar":
        return cls(title, message, "success", parent=parent)

    @classmethod
    def warning(cls, title: str = "", message: str = "", parent=None) -> "FluentInfoBar":
        return cls(title, message, "warning", parent=parent)

    @classmethod
    def error(cls, title: str = "", message: str = "", parent=None) -> "FluentInfoBar":
        return cls(title, message, "error", parent=parent)
