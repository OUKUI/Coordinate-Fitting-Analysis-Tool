"""Fluent 滑块（Slider）：水平滑块，自绘轨道与滑块。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSlider

from ..theme import palette as P


class FluentSlider(QSlider):
    """Fluent 风格水平滑块。"""

    def __init__(self, value: int = 0, minimum: int = 0, maximum: int = 100,
                 parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setRange(minimum, maximum)
        self.setValue(value)
        self.setMinimumHeight(24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _groove_rect(self) -> QRectF:
        w, h = self.width(), self.height()
        g_h = 4
        return QRectF(6, (h - g_h) / 2, w - 12, g_h)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        groove = self._groove_rect()
        px, py = self._thumb_pos()

        # 轨道背景
        p.setPen(Qt.PenStyle.NoPen)
        hover = self.underMouse()
        p.setBrush(QColor(P.fill_hover if hover else P.fill_layer))
        p.drawRoundedRect(groove, 2, 2)

        # 已填充部分
        span = groove.width()
        filled = max(0.0, min(1.0, (self.value() - self.minimum())
                              / max(1, self.maximum() - self.minimum())))
        if filled > 0:
            fill_rect = QRectF(groove.left(), groove.top(),
                               span * filled, groove.height())
            p.setBrush(QColor(P.accent))
            p.drawRoundedRect(fill_rect, 2, 2)

        # 滑块
        r = 8 if self.isSliderDown() or self.underMouse() else 6
        p.setBrush(QColor(P.text_primary))
        p.setPen(QPen(QColor(P.accent), 2))
        p.drawEllipse(QRectF(px - r, py - r, 2 * r, 2 * r))

        p.end()

    def _thumb_pos(self):
        """滑块中心点。"""
        groove = self._groove_rect()
        t = 0.0
        if self.maximum() != self.minimum():
            t = (self.value() - self.minimum()) / (self.maximum() - self.minimum())
        x = groove.left() + groove.width() * t
        return (x, groove.center().y())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            groove = self._groove_rect()
            t = (event.position().x() - groove.left()) / max(1.0, groove.width())
            t = max(0.0, min(1.0, t))
            v = self.minimum() + t * (self.maximum() - self.minimum())
            self.setValue(round(v))
            event.accept()
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)
