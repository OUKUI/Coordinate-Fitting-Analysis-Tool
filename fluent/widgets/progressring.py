"""Fluent 环形进度（ProgressRing）。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..theme import palette as P


class FluentProgressRing(QWidget):
    """Fluent 风格环形进度条。

    - 确定模式：value/maximum 表示进度，顺时针填充圆弧
    - 不确定模式：setRange(0, 0) 显示旋转光弧动画
    """

    _angle = 0.0  # 不确定模式起始角

    def __init__(self, value: int = 0, maximum: int = 100, size: int = 56,
                 thickness: int = 5, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._thickness = thickness
        self.setRange(0, maximum)
        self.setValue(value)

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def setRange(self, mn: int, mx: int) -> None:
        self._min, self._max = mn, mx
        timer = getattr(self, "_timer", None)
        if timer is not None:
            timer.start() if mx == 0 and mn == 0 else timer.stop()
        self.update()

    def setValue(self, value: int) -> None:
        self._value = max(getattr(self, "_min", 0), min(value, getattr(self, "_max", 100)))
        self.update()

    def value(self) -> int:
        return getattr(self, "_value", 0)

    def minimum(self) -> int:
        return getattr(self, "_min", 0)

    def maximum(self) -> int:
        return getattr(self, "_max", 100)

    def _tick(self) -> None:
        self._angle = (self._angle + 6.0) % 360
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = self.width()
        pen_w = self._thickness
        rect = QRectF(pen_w / 2, pen_w / 2, size - pen_w, size - pen_w)

        # 轨道
        track = QPen(QColor(P.fill_layer), pen_w,
                     Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(track)
        p.drawArc(rect, 0, 360 * 16)

        # 进度弧
        fg = QPen(QColor(P.accent), pen_w,
                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(fg)
        if self._max > self._min:
            span = 360.0 * (self._value - self._min) / (self._max - self._min)
            p.drawArc(rect, 90 * 16, int(-span * 16))
        else:
            # 不确定模式：120° 光弧旋转
            p.drawArc(rect, int(self._angle * 16), 120 * 16)
        p.end()
