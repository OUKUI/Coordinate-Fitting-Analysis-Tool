"""Fluent 数字输入框（SpinBox / DoubleSpinBox）。"""
from __future__ import annotations

from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox

from ..theme import palette as P


class _SpinMixin:
    """Fluent 数字输入框公共外观（自绘上下箭头 + 悬停描边）。

    注意：这是普通 mixin，不继承 Qt 类；QSS 选择器使用 C++ 类名。
    """

    _hover = False
    _qss_type = "QAbstractSpinBox"

    def _refresh(self) -> None:
        t = self._qss_type
        border = P.accent if self._hover else P.stroke_layer
        bg = P.fill_hover if self._hover else P.fill_layer
        self.setStyleSheet(f"""
            {t} {{
                background-color: {bg};
                color: {P.text_primary};
                border: 1px solid {border};
                border-radius: {P.radius_input}px;
                padding: 0 8px;
                selection-background-color: {P.accent};
                selection-color: {P.accent_on};
            }}
            {t}:focus {{
                border: 1px solid {P.accent};
                background-color: {P.bg_layer_glass};
            }}
            {t}:disabled {{
                background-color: {P.fill_disabled};
                color: {P.text_disabled};
            }}
            {t}::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-top-right-radius: {P.radius_input}px;
                background-color: {P.fill_layer};
            }}
            {t}::up-button:hover {{
                background-color: {P.fill_hover};
            }}
            {t}::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-bottom-right-radius: {P.radius_input}px;
                background-color: {P.fill_layer};
            }}
            {t}::down-button:hover {{
                background-color: {P.fill_hover};
            }}
            {t}::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid {P.text_secondary};
                margin-top: 4px;
            }}
            {t}::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {P.text_secondary};
                margin-bottom: 4px;
            }}
        """)

    def enterEvent(self, event) -> None:
        self._hover = True
        self._refresh()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._refresh()
        super().leaveEvent(event)


class FluentSpinBox(QSpinBox, _SpinMixin):
    """Fluent 风格整数输入框，带自绘上下箭头。"""

    _qss_type = "QSpinBox"

    def __init__(self, value: int = 0, minimum: int = 0, maximum: int = 100,
                 parent=None) -> None:
        super().__init__(parent)
        self.setRange(minimum, maximum)
        self.setValue(value)
        self.setMinimumHeight(P.control_height)
        self._refresh()


class FluentDoubleSpinBox(QDoubleSpinBox, _SpinMixin):
    """Fluent 风格浮点输入框，带自绘上下箭头。"""

    _qss_type = "QDoubleSpinBox"

    def __init__(self, value: float = 0.0, minimum: float = 0.0,
                 maximum: float = 100.0, decimals: int = 2,
                 suffix: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setRange(minimum, maximum)
        self.setDecimals(decimals)
        if suffix:
            self.setSuffix(suffix)
        self.setValue(value)
        self.setMinimumHeight(P.control_height)
        self._refresh()
