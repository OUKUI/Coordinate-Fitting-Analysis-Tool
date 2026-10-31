"""Fluent 开关（ToggleSwitch）。

自绘开关，带 120ms 滑块过渡动画。
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, Property, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton

from ..theme import palette as P


class FluentToggleSwitch(QAbstractButton):
    """Fluent 风格开关。

    用法::

        sw = FluentToggleSwitch("夜间模式")
        sw.setChecked(True)
        sw.toggled.connect(...)
    """

    _hover = False

    def __init__(self, text: str = "", parent=None, checked: bool = False) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self._blend = 1.0 if checked else 0.0  # 实例级，随初始选中态同步
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(80, P.toggle_size + 8)

        self._anim = QPropertyAnimation(self, b"blend", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # ---- 动画 ----
    def _get_blend(self) -> float:
        return self._blend

    def _set_blend(self, v: float) -> None:
        self._blend = v
        self.update()

    blend = Property(float, _get_blend, _set_blend)

    def checkStateSet(self) -> None:
        """程序化 setChecked 时同步滑块位置（不做动画）。"""
        super().checkStateSet()
        self._blend = 1.0 if self.isChecked() else 0.0
        self.update()

    def nextCheckState(self) -> None:
        super().nextCheckState()
        self._anim.stop()
        self._anim.setStartValue(self._blend)
        self._anim.setEndValue(1.0 if self.isChecked() else 0.0)
        self._anim.start()

    # ---- 绘制 ----
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        track_h = P.toggle_size - 16  # 高 24
        track_w = P.toggle_size       # 宽 40
        ty = (h - track_h) / 2
        tx = 0

        # 轨道
        track_rect = QRectF(tx, ty, track_w, track_h)
        p.setPen(Qt.PenStyle.NoPen)
        if self.isChecked():
            p.setBrush(QColor(P.accent_hover if self._hover else P.accent))
        else:
            p.setBrush(QColor(P.fill_hover if self._hover else P.fill_layer))
            p.setPen(QPen(QColor(P.stroke_hover if self._hover else P.stroke_layer), 1))
        p.drawRoundedRect(track_rect, track_h / 2, track_h / 2)

        # 滑块：开启为白色，关闭为灰色（与开启态明显区分）
        thumb_r = P.toggle_thumb / 2
        offset = self._blend * (track_w - P.toggle_thumb - 4) + 2
        cx = tx + thumb_r + offset
        cy = ty + track_h / 2
        p.setPen(Qt.PenStyle.NoPen)
        if self.isChecked():
            p.setBrush(QColor(P.accent_on))
        else:
            p.setBrush(QColor("#8A8A8A"))
        p.drawEllipse(QRectF(cx - thumb_r, cy - thumb_r, thumb_r * 2, thumb_r * 2))

        # 文案
        if self.text():
            from PySide6.QtWidgets import QStyleOption
            opt = QStyleOption()
            opt.initFrom(self)
            fm = p.fontMetrics()
            txt_x = track_w + 10
            txt_y = ty + (track_h - fm.height()) / 2 + fm.ascent()
            col = QColor(P.text_primary if self.isEnabled() else P.text_disabled)
            p.setPen(col)
            p.drawText(txt_x, txt_y, self.text())

        p.end()
