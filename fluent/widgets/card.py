"""Fluent 卡片（Card）与设置卡片（SettingsCard）。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..theme import palette as P


class FluentCard(QFrame):
    """Fluent 卡片容器：圆角 + 填充背景。"""

    def __init__(self, parent=None, clickable: bool = False) -> None:
        super().__init__(parent)
        self._clickable = clickable
        self.setObjectName("FluentCard")
        self.setStyleSheet(f"""
            #FluentCard {{
                background-color: {P.card};
                border: 1px solid {P.divider};
                border-radius: {P.radius_card}px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(10)
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def addWidget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def enterEvent(self, event) -> None:
        if self._clickable:
            self.setStyleSheet(f"""
                #FluentCard {{
                    background-color: {P.fill_hover};
                    border: 1px solid {P.stroke_layer};
                    border-radius: {P.radius_card}px;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self._clickable:
            self.setStyleSheet(f"""
                #FluentCard {{
                    background-color: {P.card};
                    border: 1px solid {P.divider};
                    border-radius: {P.radius_card}px;
                }}
            """)
        super().leaveEvent(event)


class FluentSettingsCard(QFrame):
    """Fluent 设置卡片：左侧标题/副标题 + 右侧控件。

    用法::

        card = FluentSettingsCard("夜间模式", "切换应用的主题", toggle)
    """

    def __init__(self, title: str, subtitle: str = "", widget: QWidget = None,
                 parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsCard")
        self.setStyleSheet(f"""
            #SettingsCard {{
                background-color: {P.card};
                border: 1px solid {P.divider};
                border-radius: {P.radius_card}px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {P.text_primary}; font-size: 13px; background: transparent;")
        text_col.addWidget(title_lbl)
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setWordWrap(True)
            sub_lbl.setStyleSheet(
                f"color: {P.text_secondary}; font-size: 11px; background: transparent;")
            text_col.addWidget(sub_lbl)
        lay.addLayout(text_col, 1)

        if widget is not None:
            lay.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)

    def _apply(self, bg: str) -> None:
        self.setStyleSheet(f"""
            #SettingsCard {{
                background-color: {bg};
                border: 1px solid {P.divider};
                border-radius: {P.radius_card}px;
            }}
        """)

    def enterEvent(self, event) -> None:
        self._apply(P.fill_hover)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._apply(P.card)
        super().leaveEvent(event)
