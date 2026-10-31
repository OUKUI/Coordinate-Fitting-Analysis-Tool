"""Fluent 下拉框（ComboBox）。

带明确的悬浮反馈：悬停时背景提亮、描边高亮、箭头变亮；
弹出列表项悬停高亮。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox

from ..theme import palette as P


class FluentComboBox(QComboBox):
    """Fluent 风格下拉框。

    用法::

        cb = FluentComboBox(["Windows 11", "Windows 10", "Ubuntu"])
        cb.currentTextChanged.connect(...)
    """

    _hover = False
    _open = False

    def __init__(self, items=None, parent=None) -> None:
        super().__init__(parent)
        if items:
            self.addItems(items)
        self.setMinimumHeight(P.control_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh()

    # ---- 状态样式 ----
    def _refresh(self) -> None:
        hover = self._hover or self._open
        bg = P.fill_hover if hover else P.fill_layer
        border = P.accent if hover else P.stroke_layer
        arrow = P.text_primary if hover else P.text_secondary
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {bg};
                color: {P.text_primary};
                border: 1px solid {border};
                border-radius: {P.radius_input}px;
                padding: 0 10px;
                min-width: 120px;
            }}
            QComboBox:disabled {{
                background-color: {P.fill_disabled};
                color: {P.text_disabled};
                border: 1px solid {P.fill_disabled};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {arrow};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {P.bg_layer_glass};
                color: {P.text_primary};
                border: 1px solid {P.stroke_layer};
                border-radius: 6px;
                padding: 4px;
                selection-background-color: {P.accent};
                selection-color: {P.accent_on};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {P.fill_hover};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {P.accent};
                color: {P.accent_on};
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

    def showPopup(self) -> None:
        self._open = True
        self._refresh()
        super().showPopup()

    def hidePopup(self) -> None:
        self._open = False
        self._refresh()
        super().hidePopup()
