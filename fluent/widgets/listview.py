"""Fluent 列表视图（ListView）与列表项。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QScrollArea,
                               QVBoxLayout, QWidget)

from ..theme import palette as P


class FluentListItem(QFrame):
    """列表项：标题 + 副标题 + 可选右侧控件，悬停/选中高亮。"""

    clicked = Signal(int)

    _hover = False
    _selected = False
    index = 0

    def __init__(self, title: str, subtitle: str = "", trailing=None,
                 index: int = 0, parent=None) -> None:
        super().__init__(parent)
        self.index = index
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setObjectName("FluentListItem")
        self.setStyleSheet("#FluentListItem { background: transparent; border: none; }")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 12, 8)
        lay.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            "font-size: 13px; background: transparent;")
        text_col.addWidget(self.title_lbl)
        if subtitle:
            self.sub_lbl = QLabel(subtitle)
            self.sub_lbl.setStyleSheet(
                "font-size: 11px; color: #8A8A8A; background: transparent;")
            text_col.addWidget(self.sub_lbl)
        lay.addLayout(text_col, 1)

        if trailing is not None:
            lay.addWidget(trailing, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(True)
            self.clicked.emit(self.index)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._selected:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(P.fill_selected))
            p.drawRoundedRect(self.rect(), 6, 6)
            p.setBrush(QColor(P.accent))
            p.drawRoundedRect(QRectF(2, 8, 3, self.height() - 16), 1.5, 1.5)
        elif self._hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(P.fill_hover))
            p.drawRoundedRect(self.rect(), 6, 6)
        p.end()


class FluentListView(QScrollArea):
    """Fluent 风格列表容器，管理一组 FluentListItem。

    用法::

        view = FluentListView()
        view.addItem("无线网络", "已连接", trailing=toggle)
        view.addItem("蓝牙")
        view.itemClicked.connect(lambda i: ...)
    """

    itemClicked = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setContentsMargins(2, 2, 2, 2)
        self._vbox.setSpacing(4)
        self._vbox.addStretch(1)
        self.setWidget(self._container)

        self._items: list[FluentListItem] = []
        self._current = -1

    def addItem(self, title: str, subtitle: str = "", trailing=None) -> FluentListItem:
        item = FluentListItem(title, subtitle, trailing,
                              index=len(self._items), parent=self._container)
        item.clicked.connect(self._on_clicked)
        self._vbox.insertWidget(self._vbox.count() - 1, item)
        self._items.append(item)
        return item

    def clear(self) -> None:
        for item in self._items:
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        self._current = -1

    def _on_clicked(self, index: int) -> None:
        self._current = index
        for i, item in enumerate(self._items):
            item.set_selected(i == index)
        self.itemClicked.emit(index)

    def current_index(self) -> int:
        return self._current
