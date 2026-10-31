"""Fluent 侧边导航栏（NavigationView / Pivot）。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QStackedWidget,
                               QVBoxLayout, QWidget)

from ..theme import palette as P


class FluentNavItem(QFrame):
    """导航项：图标 + 文字，悬停高亮、选中左侧强调条。"""

    clicked = Signal(int)
    _hover = False
    _selected = False
    index = 0

    def __init__(self, text: str, index: int = 0, parent=None) -> None:
        super().__init__(parent)
        self.index = index
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setObjectName("FluentNavItem")
        self.setStyleSheet("#FluentNavItem { background: transparent; border: none; }")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 12, 0)
        self.label = QLabel(text)
        lay.addWidget(self.label, 1)

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
            p.setBrush(QColor(P.fill_selected))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(self.rect(), 6, 6)
            p.setBrush(QColor(P.accent))
            p.drawRoundedRect(QRectF(2, 8, 3, self.height() - 16), 1.5, 1.5)
            self.label.setStyleSheet(f"color: {P.text_primary}; background: transparent;")
        elif self._hover:
            p.setBrush(QColor(P.fill_hover))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(self.rect(), 6, 6)
            self.label.setStyleSheet(f"color: {P.text_primary}; background: transparent;")
        else:
            self.label.setStyleSheet(f"color: {P.text_secondary}; background: transparent;")
        p.end()


class FluentNavigation(QFrame):
    """Fluent 侧边导航栏。

    用法::

        nav = FluentNavigation()
        nav.addItem("主页")
        nav.addItem("设置")
        nav.link_stack(stack)   # 与 QStackedWidget 联动
        nav.itemChanged.connect(lambda i: ...)
    """

    itemChanged = Signal(int)

    def __init__(self, width: int = 200, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(width)
        self.setObjectName("FluentNavigation")
        self.setStyleSheet(f"""
            #FluentNavigation {{
                background-color: {P.bg_layer_alt};
                border-right: 1px solid {P.divider};
            }}
        """)

        self._vbox = QVBoxLayout(self)
        self._vbox.setContentsMargins(8, 12, 8, 12)
        self._vbox.setSpacing(4)
        self._vbox.addStretch(1)

        self._items: list[FluentNavItem] = []
        self._current = -1

    def set_header(self, text: str) -> None:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 12px; color: #8A8A8A; padding: 0 10px 6px 10px; background: transparent;")
        self._vbox.insertWidget(0, lbl)

    def addItem(self, text: str) -> int:
        idx = len(self._items)
        item = FluentNavItem(text, idx, self)
        item.clicked.connect(self._on_clicked)
        self._vbox.insertWidget(self._vbox.count() - 1, item)
        self._items.append(item)
        return idx

    def set_current(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self._on_clicked(index)

    def link_stack(self, stack: QStackedWidget) -> None:
        self.itemChanged.connect(lambda i: stack.setCurrentIndex(i))
        if stack.count():
            self.set_current(0)

    def _on_clicked(self, index: int) -> None:
        self._current = index
        for i, item in enumerate(self._items):
            item.set_selected(i == index)
        self.itemChanged.emit(index)

    def current_index(self) -> int:
        return self._current
