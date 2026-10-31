"""Fluent 文本框（LineEdit）与多行文本框（TextEdit）。"""
from __future__ import annotations

from PySide6.QtWidgets import QLineEdit, QTextEdit

from ..theme import palette as P


class FluentLineEdit(QLineEdit):
    """Fluent 风格单行输入框。"""

    def __init__(self, text: str = "", placeholder: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(P.control_height)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {P.fill_layer};
                color: {P.text_primary};
                border: 1px solid {P.stroke_layer};
                border-radius: {P.radius_input}px;
                padding: 0 10px;
                selection-background-color: {P.accent};
                selection-color: {P.accent_on};
            }}
            QLineEdit:hover {{
                border: 1px solid {P.stroke_hover};
            }}
            QLineEdit:focus {{
                border: 1px solid {P.accent};
                background-color: {P.bg_layer_glass};
            }}
            QLineEdit:disabled {{
                background-color: {P.fill_disabled};
                color: {P.text_disabled};
            }}
            QLineEdit::placeholder {{
                color: {P.text_tertiary};
            }}
        """)


class FluentTextEdit(QTextEdit):
    """Fluent 风格多行文本框。"""

    def __init__(self, text: str = "", placeholder: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {P.fill_layer};
                color: {P.text_primary};
                border: 1px solid {P.stroke_layer};
                border-radius: {P.radius_input}px;
                padding: 8px;
                selection-background-color: {P.accent};
                selection-color: {P.accent_on};
            }}
            QTextEdit:hover {{
                border: 1px solid {P.stroke_hover};
            }}
            QTextEdit:focus {{
                border: 1px solid {P.accent};
            }}
            QTextEdit:disabled {{
                background-color: {P.fill_disabled};
                color: {P.text_disabled};
            }}
        """)

    def insertFromMimeData(self, source) -> None:
        if source.hasText():
            self.insertPlainText(source.text().replace("\xa0", " "))
        else:
            super().insertFromMimeData(source)
