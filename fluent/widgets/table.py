"""Fluent 表格（TableWidget）与树形视图（TreeView）。"""
from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QAbstractItemView, QHeaderView, QTableWidget,
                               QTableWidgetItem, QTreeWidget, QTreeWidgetItem)

from ..theme import palette as P

_TABLE_QSS = f"""
QTableWidget {{
    background-color: {P.bg_layer_default};
    alternate-background-color: {P.bg_layer_glass};
    color: {P.text_primary};
    border: 1px solid {P.divider};
    border-radius: 8px;
    gridline-color: {P.divider};
    selection-background-color: rgba(0, 103, 192, 120);
    selection-color: {P.text_primary};
}}
QTableWidget::item {{
    padding: 2px 8px;
    border: none;
}}
QTableWidget::item:hover {{
    background-color: {P.fill_hover};
}}
QHeaderView::section {{
    background-color: {P.bg_layer_glass};
    color: {P.text_secondary};
    border: none;
    border-bottom: 1px solid {P.stroke_layer};
    border-right: 1px solid {P.divider};
    padding: 8px 10px;
    font-weight: 600;
}}
QTableCornerButton::section {{
    background-color: {P.bg_layer_glass};
    border: none;
    border-bottom: 1px solid {P.stroke_layer};
}}
QTableWidget QScrollBar:vertical {{
    margin: 0;
}}
"""

_TREE_QSS = f"""
QTreeWidget {{
    background-color: transparent;
    color: {P.text_primary};
    border: none;
    outline: none;
}}
QTreeWidget::item {{
    height: 34px;
    padding: 0 6px;
    border-radius: 4px;
}}
QTreeWidget::item:hover {{
    background-color: {P.fill_hover};
}}
QTreeWidget::item:selected {{
    background-color: {P.fill_selected};
    color: {P.text_primary};
}}
QTreeWidget::branch {{
    background: transparent;
}}
QTreeWidget::branch:has-children:closed {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {P.text_secondary};
    margin-left: 8px;
    margin-top: 6px;
}}
QTreeWidget::branch:has-children:open {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {P.text_primary};
    margin-left: 8px;
    margin-top: 2px;
}}
"""


class FluentTableWidget(QTableWidget):
    """Fluent 风格表格。"""

    def __init__(self, headers: Iterable[str] = (), rows: Iterable[Iterable] = (),
                 parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(_TABLE_QSS)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        if headers:
            self.setHeaders(headers)
        if rows:
            self.set_rows(rows)

    def setHeaders(self, headers: Iterable[str]) -> None:
        self.setColumnCount(len(list(headers)))
        self.setHorizontalHeaderLabels(list(headers))

    def set_rows(self, rows: Iterable[Iterable]) -> None:
        rows = [list(r) for r in rows]
        self.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.setItem(r, c, QTableWidgetItem(str(value)))

    def set_editable(self, editable: bool) -> None:
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
            if editable else QAbstractItemView.EditTrigger.NoEditTriggers)


class FluentTreeView(QTreeWidget):
    """Fluent 风格树形视图。"""

    def __init__(self, headers: Iterable[str] = ("",), parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(_TREE_QSS)
        self.setHeaderHidden(len(list(headers)) <= 1 or not headers)
        if headers:
            self.setHeaderLabels(list(headers))
        self.setIndentation(18)

    def add_node(self, text: str, parent: QTreeWidgetItem | None = None,
                 icon: QIcon | None = None, data=None) -> QTreeWidgetItem:
        item = QTreeWidgetItem([text])
        if icon is not None:
            item.setIcon(0, icon)
        if data is not None:
            item.setData(0, Qt.ItemDataRole.UserRole, data)
        if parent is not None:
            parent.addChild(item)
        else:
            self.addTopLevelItem(item)
        return item

