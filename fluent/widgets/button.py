"""Fluent 按钮：默认按钮 / 强调色按钮 / 危险按钮 / 超链接按钮。"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Property
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton

from ..theme import palette as P, text_color_on


def _mix(c1: str, c2: str, t: float) -> str:
    """按比例 t 混合两种颜色（用于 hover 过渡）。"""
    a, b = QColor(c1), QColor(c2)
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    ).name()


class FluentButton(QPushButton):
    """Fluent 风格按钮。

    样式类型由 variant 决定：
      - "standard"   默认透明底、描边
      - "accent"     强调色填充
      - "danger"     危险红色
    """

    _hover = False
    _blend = 0.0  # hover 进度 0..1，驱动颜色过渡动画

    def __init__(self, text: str = "", parent=None, variant: str = "standard",
                 icon=None, fixed_width: int = 0) -> None:
        super().__init__(text, parent)
        self.variant = variant
        if icon is not None:
            self.setIcon(icon)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(P.button_height)
        if fixed_width:
            self.setFixedWidth(fixed_width)

        self._anim = QPropertyAnimation(self, b"blend", self)
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ---- hover 动画 ----
    def _get_blend(self) -> float:
        return self._blend

    def _set_blend(self, v: float) -> None:
        self._blend = v
        self.update()

    blend = Property(float, _get_blend, _set_blend)

    def enterEvent(self, event) -> None:
        self._hover = True
        self._anim.stop()
        self._anim.setStartValue(self._blend)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._anim.stop()
        self._anim.setStartValue(self._blend)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)

    def _bg(self) -> str:
        if self.variant == "accent":
            return _mix(P.accent, P.accent_hover, self._blend)
        if self.variant == "danger":
            return _mix(P.danger, P.danger_hover, self._blend)
        return _mix(P.fill_layer, P.fill_hover, self._blend)

    def _border(self) -> str:
        if self.variant == "standard":
            return _mix(P.stroke_layer, P.stroke_hover, self._blend)
        return "transparent"

    def paintEvent(self, event) -> None:
        p = QPushButton.paintEvent

        # 临时改样式表来驱动配色（保持 Qt 内置绘制，最稳定）
        style = f"""
        QPushButton {{
            background-color: {self._bg()};
            color: {P.text_primary};
            border: 1px solid {self._border()};
            border-radius: {P.radius_button}px;
            padding: 0 12px;
        }}
        QPushButton:disabled {{
            background-color: {P.fill_disabled};
            color: {P.text_disabled};
            border: 1px solid {P.fill_disabled};
        }}
        QPushButton:focus {{
            border: 1px solid {P.accent_light};
        }}
        """
        if self.variant == "accent":
            style = style.replace(
                f"color: {P.text_primary};",
                f"color: {text_color_on(self._bg())};", 1)
        self.setStyleSheet(style)
        p(self, event)
