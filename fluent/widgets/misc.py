"""Fluent 头像（Avatar）、评分（Rating）、数量选择器（QuantitySelector）。"""
from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QPainter, QPainterPath, QPen,
                           QPixmap)
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from ..theme import palette as P

_AVATAR_COLORS = [
    "#0067C0", "#5C2D91", "#C239B3", "#E3008C", "#CA5010",
    "#B146C2", "#498205", "#00B7C3", "#7719AA", "#767676",
]


class FluentAvatar(QWidget):
    """Fluent 圆形头像：显示首字母或图片。

    用法::

        FluentAvatar("张", size=40)
        FluentAvatar("张", pixmap=QPixmap("a.png"))
    """

    def __init__(self, name: str = "", size: int = 40, pixmap: QPixmap | None = None,
                 color: str = "", parent=None) -> None:
        super().__init__(parent)
        self._name = name
        self._pixmap = pixmap
        if color:
            self._color = QColor(color)
        else:
            idx = sum(ord(c) for c in name) % len(_AVATAR_COLORS)
            self._color = QColor(_AVATAR_COLORS[idx])
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.width()
        if self._pixmap is not None:
            pm = self._pixmap.scaled(
                r, r, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            path = QPainterPath()
            path.addEllipse(QRectF(0, 0, r, r))
            p.setClipPath(path)
            p.drawPixmap(QRectF(0, 0, r, r), pm)
            p.setClipPath(QPainterPath())
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._color)
            p.drawEllipse(0, 0, r, r)
            letter = (self._name[:1]).upper() or "?"
            f = QFont()
            f.setBold(True)
            f.setPixelSize(max(12, int(r * 0.42)))
            p.setFont(f)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, letter)
        p.end()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()


class FluentRating(QWidget):
    """Fluent 星级评分（支持半星与悬浮预览）。"""

    ratingChanged = Signal(int)

    def __init__(self, rating: int = 0, maximum: int = 5, size: int = 26,
                 parent=None) -> None:
        super().__init__(parent)
        self._rating = rating
        self._maximum = maximum
        self._size = size
        self._hover = -1
        self.setFixedSize(maximum * size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def rating(self) -> int:
        return self._rating

    def setRating(self, rating: int) -> None:
        self._rating = max(0, min(self._maximum, rating))
        self.update()
        self.ratingChanged.emit(self._rating)

    def _star_path(self, i: int) -> QPainterPath:
        cx = i * self._size + self._size / 2
        cy = self._size / 2
        r = self._size * 0.45
        path = QPainterPath()
        for k in range(10):
            ang = math.radians(-90 + k * 36)
            rad = r if k % 2 == 0 else r * 0.48
            x = cx + rad * math.cos(ang)
            y = cy + rad * math.sin(ang)
            if k == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        return path

    def _star_for_pos(self, pos) -> int:
        idx = int(pos.x() // self._size)
        return max(0, min(self._maximum - 1, idx))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setRating(self._star_for_pos(event.position()) + 1)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        self._hover = self._star_for_pos(event.position())
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i in range(self._maximum):
            if self._hover >= 0 and i <= self._hover:
                filled = True
            elif self._hover < 0 and i < self._rating:
                filled = True
            else:
                filled = False
            p.setPen(Qt.PenStyle.NoPen)
            if filled:
                p.setBrush(QColor(P.accent_light))
            else:
                p.setBrush(QColor(P.fill_hover))
            p.drawPath(self._star_path(i))
        p.end()


class FluentQuantitySelector(QWidget):
    """Fluent 数量选择器：− 数值 ＋（长按连续调节）。"""

    valueChanged = Signal(int)

    def __init__(self, value: int = 0, minimum: int = 0, maximum: int = 99,
                 parent=None) -> None:
        super().__init__(parent)
        self._value = value
        self._min, self._max = minimum, maximum

        from PySide6.QtWidgets import QHBoxLayout

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._minus = self._btn("−")
        self._plus = self._btn("＋")
        self._label = QLabel(str(self._value))
        self._label.setFixedWidth(44)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            f"background: transparent; font-size: 14px; font-weight: 600;")

        lay.addWidget(self._minus)
        lay.addWidget(self._label)
        lay.addWidget(self._plus)

        self._minus.clicked.connect(lambda: self._adjust(-1))
        self._plus.clicked.connect(lambda: self._adjust(+1))

        from PySide6.QtCore import QTimer
        self._repeat = QTimer(self)
        self._repeat.setInterval(120)
        self._repeat.timeout.connect(self._repeat_tick)
        self._repeat_dir = 0
        self._minus.pressed.connect(lambda: self._start_repeat(-1))
        self._plus.pressed.connect(lambda: self._start_repeat(+1))
        self._minus.released.connect(self._stop_repeat)
        self._plus.released.connect(self._stop_repeat)

    def _btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {P.fill_layer};
                color: {P.text_primary};
                border: 1px solid {P.stroke_layer};
                border-radius: 15px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {P.fill_hover};
                border: 1px solid {P.stroke_hover};
            }}
            QPushButton:pressed {{
                background-color: {P.accent};
                color: {P.accent_on};
                border: 1px solid {P.accent};
            }}
            QPushButton:disabled {{
                background-color: {P.fill_disabled};
                color: {P.text_disabled};
            }}
        """)
        return btn

    def value(self) -> int:
        return self._value

    def setValue(self, value: int) -> None:
        self._value = max(self._min, min(self._max, value))
        self._label.setText(str(self._value))
        self.valueChanged.emit(self._value)

    def _adjust(self, delta: int) -> None:
        if 0 < delta or self._value > self._min:
            self.setValue(self._value + delta)

    def _start_repeat(self, direction: int) -> None:
        self._repeat_dir = direction
        self._repeat.start()

    def _stop_repeat(self) -> None:
        self._repeat.stop()

    def _repeat_tick(self) -> None:
        self._adjust(self._repeat_dir)
