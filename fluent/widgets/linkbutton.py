"""Fluent 超链接按钮与标签（Tag）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ..theme import palette as P
from .icons import CloseButton


class FluentHyperlinkButton(QPushButton):
    """Fluent 超链接按钮：强调色文字，悬停下划线。"""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {P.accent_light};
                border: none;
                padding: 2px 4px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
            QPushButton:pressed {{
                color: {P.accent_hover};
            }}
            QPushButton:disabled {{
                color: {P.text_disabled};
            }}
        """)


class FluentTag(QWidget):
    """Fluent 标签/徽章，带可选关闭按钮。

    variant 取值：default / accent / success / warning / danger。
    """

    closed = Signal()

    def __init__(self, text: str, variant: str = "default", closable: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self.variant = variant
        self.setObjectName("FluentTag")

        self._fg, self._bg = self._colors()
        self.setStyleSheet(f"""
            #FluentTag {{
                background-color: {self._bg};
                border-radius: 12px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 2, 6, 2)
        lay.setSpacing(4)

        self.label = QLabel(text)
        self.label.setStyleSheet(
            f"color: {self._fg}; background: transparent; font-size: 12px;")
        lay.addWidget(self.label)

        if closable:
            btn = CloseButton(self, size=16)
            btn.setFixedSize(16, 16)
            btn.clicked.connect(self.close_tag)
            lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def close_tag(self) -> None:
        self.hide()
        self.closed.emit()

    def _colors(self) -> tuple[str, str]:
        return {
            "default": (P.text_primary, P.fill_hover),
            "accent": (P.accent_light, "#1E3A5A"),
            "success": ("#3FB950", "#14320F"),
            "warning": ("#E3B341", "#3A2E0A"),
            "danger": ("#F14C4C", "#3A1212"),
        }.get(self.variant, (P.text_primary, P.fill_hover))
