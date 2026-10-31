"""Fluent 进度条（自绘圆角轨道）。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QProgressBar

from ..theme import palette as P


class FluentProgressBar(QProgressBar):
    """Fluent 风格进度条。

    - 普通模式：显示实际进度
    - 不确定模式：setRange(0, 0) 时显示循环动画
    """

    _pos = 0.0  # 不确定模式动画偏移

    def __init__(self, value: int = 0, maximum: int = 100, parent=None) -> None:
        super().__init__(parent)
        self.setRange(0, maximum)
        self.setValue(value)
        self.setFixedHeight(4)
        self.setTextVisible(False)

        from PySide6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def _tick(self) -> None:
        if self.maximum() == 0 and self.minimum() == 0:
            self._pos = (self._pos + 0.5) % self.width()
            self.update()

    def setRange(self, mn: int, mx: int) -> None:
        super().setRange(mn, mx)
        timer = getattr(self, "_timer", None)
        if timer is not None:
            timer.start() if mx == 0 and mn == 0 else timer.stop()
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 轨道
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(P.fill_layer))
        p.drawRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)

        # 填充
        if self.maximum() > self.minimum():
            t = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
            t = max(0.0, min(1.0, t))
            fill_w = max(0.0, w * t)
        else:
            # 不确定模式：一段 40% 宽的光斑循环移动
            seg = w * 0.4
            x = self._pos - seg
            fill_w = seg
            p.save()
            p.setOpacity(0.9)
            p.drawRoundedRect(QRectF(x, 0, fill_w, h), h / 2, h / 2)
            p.restore()
            p.end()
            return

        if fill_w > 0:
            p.setBrush(QColor(P.accent))
            p.drawRoundedRect(QRectF(0, 0, fill_w, h), h / 2, h / 2)

        p.end()
