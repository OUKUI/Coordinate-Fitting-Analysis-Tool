"""Fluent 选项卡（TabWidget / Pivot 风格）。"""
from __future__ import annotations

from PySide6.QtWidgets import QTabWidget

from ..theme import palette as P


class FluentTabWidget(QTabWidget):
    """Fluent 风格选项卡：下划线选中指示，无边框面板。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {P.bg_layer_default};
            }}
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {P.text_secondary};
                padding: 8px 18px;
                margin-right: 4px;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:hover {{
                background-color: {P.fill_hover};
                border-radius: 4px 4px 0 0;
                color: {P.text_primary};
            }}
            QTabBar::tab:selected {{
                color: {P.text_primary};
                border-bottom: 2px solid {P.accent};
            }}
            QTabBar::tab:disabled {{
                color: {P.text_disabled};
            }}
        """)
