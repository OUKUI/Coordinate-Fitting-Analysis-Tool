"""Fluent 布局控件：分隔条 / 流式布局 / 面包屑 / 可展开导航。"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QPushButton, QSplitter, QVBoxLayout, QWidget)

from ..theme import palette as P


class FluentSplitter(QSplitter):
    """Fluent 分隔条：句柄显示高亮短线，悬停变强调色。"""

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None) -> None:
        super().__init__(orientation, parent)
        self.setChildrenCollapsible(False)
        self.setHandleWidth(6)
        self.setStyleSheet(f"""
            QSplitter {{
                background: transparent;
            }}
            QSplitter::handle {{
                background: transparent;
            }}
            QSplitter::handle:horizontal {{
                width: 6px;
                border-left: 1px solid #3F3F3F;
                margin: 10px 0;
            }}
            QSplitter::handle:vertical {{
                height: 6px;
                border-top: 1px solid #3F3F3F;
                margin: 0 10px;
            }}
            QSplitter::handle:horizontal:hover {{
                border-left: 2px solid {P.accent};
                background-color: rgba(0, 103, 192, 50);
            }}
            QSplitter::handle:vertical:hover {{
                border-top: 2px solid {P.accent};
                background-color: rgba(0, 103, 192, 50);
            }}
        """)


class FluentFlowLayout(QLayout):
    """经典流式布局：控件自动换行排列。"""

    def __init__(self, parent=None, margin: int = 0, spacing: int = 8) -> None:
        super().__init__(parent)
        self._items: list = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m = self.contentsMargins()
        x, y = rect.x() + m.left(), rect.y() + m.top()
        line_h = 0
        spacing = self.spacing()
        for item in self._items:
            hint = item.sizeHint()
            if x + hint.width() > rect.right() - m.right() and line_h > 0:
                x = rect.x() + m.left()
                y += line_h + spacing
                line_h = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + spacing
            line_h = max(line_h, hint.height())
        return y + line_h - rect.y() + m.bottom()


class FluentBreadcrumbBar(QFrame):
    """Fluent 面包屑导航：项之间用 "›" 分隔，末项高亮。"""

    itemClicked = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("BreadcrumbBar")
        self.setStyleSheet(f"""
            #BreadcrumbBar {{
                background-color: {P.bg_layer_glass};
                border: 1px solid {P.divider};
                border-radius: 6px;
            }}
        """)
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(8, 6, 8, 6)
        self._lay.setSpacing(2)

    def set_items(self, items) -> None:
        """items: [名称, ...] 或 [(名称, 回调), ...]"""
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, entry in enumerate(items):
            text, callback = entry if isinstance(entry, tuple) else (entry, None)
            last = i == len(items) - 1
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setEnabled(not last)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 12px;
                    color: {P.text_primary if last else P.accent_light};
                }}
                QPushButton:hover {{
                    background-color: {P.fill_hover};
                }}
                QPushButton:disabled {{
                    color: {P.text_secondary};
                }}
            """)
            if callback is not None:
                btn.clicked.connect(callback)
            btn.clicked.connect(lambda _=False, idx=i: self.itemClicked.emit(idx))
            self._lay.addWidget(btn)
            if not last:
                sep = QLabel("›")
                sep.setStyleSheet(
                    "background: transparent; color: #6E6E6E; font-size: 12px;")
                self._lay.addWidget(sep)
        self._lay.addStretch(1)


class FluentNavEntry(QFrame):
    """导航项：可带子菜单，点击展开/收起或选中。"""

    clicked = Signal()
    toggled = Signal()

    _hover = False
    _selected = False

    def __init__(self, text: str, has_children: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.has_children = has_children
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self.setObjectName("NavEntry")
        self.setStyleSheet("#NavEntry { background: transparent; border: none; }")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 12, 0)
        lay.setSpacing(8)
        self._chevron = QLabel("▾" if has_children else "")
        self._chevron.setFixedWidth(14)
        self._chevron.setStyleSheet("background: transparent; color: #8A8A8A;")
        lay.addWidget(self._chevron)
        self._label = QLabel(text)
        lay.addWidget(self._label, 1)

    def text(self) -> str:
        return self._label.text()

    def set_selected(self, on: bool) -> None:
        self._selected = on
        self.update()

    def set_expanded(self, on: bool) -> None:
        if self.has_children:
            self._chevron.setText("▾" if on else "▸")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.has_children:
                self.toggled.emit()
            else:
                self.set_selected(True)
                self.clicked.emit()
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
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor, QPainter
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._selected:
            p.setBrush(QColor(P.fill_selected))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(self.rect(), 6, 6)
            p.setBrush(QColor(P.accent))
            p.drawRoundedRect(QRectF(2, 9, 3, self.height() - 18), 1.5, 1.5)
            self._label.setStyleSheet(
                f"color: {P.text_primary}; background: transparent;")
        elif self._hover:
            p.setBrush(QColor(P.fill_hover))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(self.rect(), 6, 6)
            self._label.setStyleSheet(
                f"color: {P.text_primary}; background: transparent;")
        else:
            self._label.setStyleSheet(
                f"color: {P.text_secondary}; background: transparent;")
        p.end()


class FluentNavigationView(QFrame):
    """Fluent 侧边导航（支持可展开的子菜单）。

    用法::

        nav = FluentNavigationView()
        nav.add_item("首页")
        nav.add_item("数据中心", children=["报表", "看板", "明细"])
        nav.itemSelected.connect(on_select)
    """

    itemSelected = Signal(str)

    def __init__(self, width: int = 210, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(width)
        self.setObjectName("NavigationView")
        self.setStyleSheet(f"""
            #NavigationView {{
                background-color: {P.bg_layer_alt};
                border-right: 1px solid {P.divider};
            }}
        """)
        self._vbox = QVBoxLayout(self)
        self._vbox.setContentsMargins(8, 10, 8, 10)
        self._vbox.setSpacing(2)
        self._vbox.addStretch(1)
        self._container_map: dict[FluentNavEntry, QWidget | None] = {}

    def set_header(self, text: str) -> None:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 12px; color: #8A8A8A; padding: 0 10px 6px 10px;"
            "background: transparent;")
        self._vbox.insertWidget(0, lbl)

    def add_item(self, text: str, children=None) -> None:
        entry = FluentNavEntry(text, has_children=bool(children))
        entry.clicked.connect(self._on_select)
        entry.toggled.connect(lambda e=entry: self._toggle(e))
        self._vbox.insertWidget(self._vbox.count() - 1, entry)

        if children:
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            cl = QVBoxLayout(container)
            cl.setContentsMargins(22, 0, 4, 0)
            cl.setSpacing(2)
            for child in children:
                sub = FluentNavEntry(child, has_children=False)
                sub.setFixedHeight(34)
                sub.clicked.connect(self._on_select)
                cl.addWidget(sub)
            container.hide()
            self._vbox.insertWidget(self._vbox.count() - 1, container)
            self._container_map[entry] = container
        else:
            self._container_map[entry] = None

    def _toggle(self, entry: FluentNavEntry) -> None:
        container = self._container_map.get(entry)
        if container is None:
            return
        visible = container.isVisible()
        entry.set_expanded(not visible)
        container.setVisible(not visible)

    def _on_select(self) -> None:
        for w in self.findChildren(FluentNavEntry):
            if not w.has_children:
                w.set_selected(False)
        entry = self.sender()
        if entry is not None:
            entry.set_selected(True)
            self.itemSelected.emit(entry.text())
