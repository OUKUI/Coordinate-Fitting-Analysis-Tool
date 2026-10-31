"""Fluent 命令条（CommandBar）与拆分按钮（SplitButton）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QMenu, QToolButton, QWidget)

from ..theme import palette as P
from .button import FluentButton


class FluentCommandBar(QFrame):
    """Fluent 命令条：一排动作按钮 + 分隔符。

    用法::

        bar = FluentCommandBar()
        bar.add_action("新建", on_clicked=new_handle)
        bar.add_action("打开", on_clicked=open_handle)
        bar.add_separator()
        bar.add_action("删除", on_clicked=del_handle, danger=True)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("FluentCommandBar")
        self.setStyleSheet(f"""
            #FluentCommandBar {{
                background-color: {P.bg_layer_glass};
                border: 1px solid {P.divider};
                border-radius: 8px;
            }}
        """)
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(8, 6, 8, 6)
        self._lay.setSpacing(4)

    def add_action(self, text: str, on_clicked=None, danger: bool = False,
                   icon=None) -> QToolButton:
        btn = QToolButton(self)
        btn.setText(text)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        if icon is not None:
            btn.setIcon(icon)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(30)
        btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {P.text_primary if not danger else P.danger_hover};
                border: none;
                border-radius: 4px;
                padding: 0 10px;
            }}
            QToolButton:hover {{
                background-color: {P.fill_hover};
            }}
            QToolButton:pressed {{
                background-color: {P.fill_pressed};
            }}
        """)
        if on_clicked is not None:
            btn.clicked.connect(on_clicked)
        self._lay.addWidget(btn)
        return btn

    def add_separator(self) -> None:
        line = QFrame(self)
        line.setFixedWidth(1)
        line.setStyleSheet(
            f"background-color: {P.divider}; border: none; margin: 4px 6px;")
        self._lay.addWidget(line)

    def add_widget(self, widget: QWidget) -> None:
        self._lay.addWidget(widget)

    def add_stretch(self) -> None:
        self._lay.addStretch(1)


class FluentSplitButton(QWidget):
    """Fluent 拆分按钮：主操作 + 右侧下拉箭头打开菜单。

    menu_items 为 (label, callback) 列表。
    """

    clicked = Signal()

    def __init__(self, text: str, menu_items=(), parent=None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.main_btn = FluentButton(text)
        self.main_btn.clicked.connect(self.clicked)
        lay.addWidget(self.main_btn)

        self._drop = QToolButton(self)
        self._drop.setText("▾")
        self._drop.setFixedSize(32, P.button_height)
        self._drop.setCursor(Qt.CursorShape.PointingHandCursor)
        self._drop.setStyleSheet(f"""
            QToolButton {{
                background-color: {P.fill_layer};
                color: {P.text_secondary};
                border: 1px solid {P.stroke_layer};
                border-left: none;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }}
            QToolButton:hover {{
                background-color: {P.fill_hover};
                color: {P.text_primary};
            }}
            QToolButton:pressed {{
                background-color: {P.fill_pressed};
            }}
        """)
        self._menu = QMenu(self)
        for label, callback in menu_items:
            self._menu.addAction(label, callback)
        self._drop.clicked.connect(self._open_menu)
        lay.addWidget(self._drop)

    def add_menu_item(self, label: str, callback) -> None:
        self._menu.addAction(label, callback)

    def _open_menu(self) -> None:
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self._menu.exec(pos)
