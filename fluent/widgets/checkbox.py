"""Fluent 复选框与单选框（自绘勾选/圆点）。"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QButtonGroup

from ..theme import palette as P, text_color_on


class _BaseFluentCheck(QAbstractButton):
    _box: int = 16  # 图形边长

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(28)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        fm = self.fontMetrics()
        return QSize(self._box + 8 + fm.horizontalAdvance(self.text()) + 8, 28)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        x, y, box = 0, (self.height() - self._box) / 2, self._box
        hover = self.underMouse() and self.isEnabled()
        bg = P.fill_hover if hover else P.fill_layer

        if self.isChecked():
            p.setPen(QPen(QColor(P.accent), 2))
            p.setBrush(QColor(P.accent))
        else:
            p.setPen(QPen(QColor(P.stroke_hover if hover else P.stroke_layer), 1.5))
            p.setBrush(QColor(bg))

        self._draw_shape(p, QRectF(x, y, box, box))

        # 勾选标记 / 圆点
        if self.isChecked():
            p.setPen(QPen(QColor(text_color_on(P.accent)), 1.8,
                          Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            self._draw_mark(p, x, y, box)

        if self.text():
            fm = p.fontMetrics()
            ty = (self.height() - fm.height()) / 2 + fm.ascent()
            p.setPen(QColor(P.text_primary if self.isEnabled() else P.text_disabled))
            p.drawText(x + box + 8, ty, self.text())

        p.end()

    def _draw_shape(self, p, rect: QRectF) -> None:  # pragma: no cover
        raise NotImplementedError

    def _draw_mark(self, p, x: int, y: int, box: int) -> None:  # pragma: no cover
        raise NotImplementedError


class FluentCheckBox(_BaseFluentCheck):
    """Fluent 复选框。"""

    def _draw_shape(self, p, rect: QRectF) -> None:
        p.drawRoundedRect(rect, 4, 4)

    def _draw_mark(self, p, x, y, box) -> None:
        p.drawPolyline([
            _pt(x + 3.5, y + 8.5),
            _pt(x + 6.5, y + 11.5),
            _pt(x + 12.5, y + 5.0),
        ])


class FluentRadioButton(_BaseFluentCheck):
    """Fluent 单选框（同一父容器内自动互斥）。"""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setAutoExclusive(True)

    def _draw_shape(self, p, rect: QRectF) -> None:
        p.drawEllipse(rect)

    def _draw_mark(self, p, x, y, box) -> None:
        c = QColor(text_color_on(P.accent))
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(x + 4.5, y + 4.5, box - 9, box - 9))


def _pt(x: float, y: float):
    from PySide6.QtCore import QPointF
    return QPointF(x, y)


def make_radio_group(items, parent=None, default_index: int = 0) -> tuple[QButtonGroup, list]:
    """便捷函数：创建一组 FluentRadioButton，返回 (group, buttons)。"""
    group = QButtonGroup(parent)
    buttons = []
    for i, label in enumerate(items):
        rb = FluentRadioButton(label, parent)
        group.addButton(rb, i)
        buttons.append(rb)
        if i == default_index:
            rb.setChecked(True)
    return group, buttons
