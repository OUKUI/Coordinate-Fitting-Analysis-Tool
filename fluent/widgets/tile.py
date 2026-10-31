"""Fluent 磁贴（Tile）与磁贴网格（GridView）。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QFrame, QGridLayout, QLabel, QScrollArea,
                               QVBoxLayout, QWidget)

from ..theme import palette as P


class FluentTile(QFrame):
    """Fluent 磁贴：圆角色块 + 图形符号 + 标题，可点击。

    用法::

        FluentTile("照片", glyph="▣", color="#0067C0")
    """

    clicked = Signal()

    def __init__(self, title: str = "", subtitle: str = "", glyph: str = "",
                 color: str = "#0067C0", size: int = 110, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._glyph = glyph
        self._hover = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("FluentTile")
        self.setStyleSheet("#FluentTile { background: transparent; border: none; }")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 12, 10, 10)
        lay.setSpacing(2)
        lay.addStretch(1)

        self._glyph_lbl = QLabel(glyph)
        self._glyph_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._glyph_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._glyph_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            "background: transparent; font-size: 13px; font-weight: 600;")
        lay.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub_lbl.setStyleSheet(
                "background: transparent; font-size: 10px; color: #8A8A8A;")
            lay.addWidget(sub_lbl)

        lay.addStretch(1)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(self._color)
        bg.setAlpha(40)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(self.rect(), 8, 8)

        if self._hover:
            p.setBrush(QColor(255, 255, 255, 26))
            p.drawRoundedRect(self.rect(), 8, 8)

        if self._glyph:
            f = QFont()
            f.setPixelSize(26)
            p.setFont(f)
            p.setPen(self._color.lighter(150))
            p.drawText(QRectF(0, 10, self.width(), 34),
                       Qt.AlignmentFlag.AlignHCenter, self._glyph)
        p.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
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


class FluentGridView(QScrollArea):
    """Fluent 磁贴网格容器。

    用法::

        grid = FluentGridView(columns=4)
        grid.add_tile("照片", glyph="▣", color="#0067C0")
        grid.tileClicked.connect(lambda i, tile: ...)
    """

    tileClicked = Signal(int)

    def __init__(self, columns: int = 4, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._columns = max(1, columns)
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setSpacing(10)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        self._tiles: list[FluentTile] = []

    def add_tile(self, title: str = "", subtitle: str = "", glyph: str = "",
                 color: str = "#0067C0", size: int = 110) -> FluentTile:
        tile = FluentTile(title, subtitle, glyph, color, size)
        self.add_widget(tile)
        return tile

    def add_widget(self, widget) -> None:
        index = len(self._tiles)
        self._tiles.append(widget)
        row, col = divmod(index, self._columns)
        self._grid.addWidget(widget, row, col)
        if isinstance(widget, FluentTile):
            widget.clicked.connect(
                lambda _=False, i=index: self.tileClicked.emit(i))

    def clear(self) -> None:
        for t in self._tiles:
            t.setParent(None)
            t.deleteLater()
        self._tiles.clear()
