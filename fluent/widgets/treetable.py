"""Fluent 树形表格（多列表格 + 可展开层级）。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QAbstractItemView, QHeaderView, QTreeWidget,
                               QTreeWidgetItem)

from ..theme import palette as P

_QSS = f"""
QTreeWidget {{
    background-color: {P.bg_layer_default};
    alternate-background-color: {P.bg_layer_glass};
    color: {P.text_primary};
    border: 1px solid {P.divider};
    border-radius: 8px;
    gridline-color: {P.divider};
    outline: none;
}}
QTreeWidget::item {{
    height: 32px;
    border-radius: 4px;
}}
QTreeWidget::item:hover {{
    background-color: {P.fill_hover};
}}
QTreeWidget::item:selected {{
    background-color: rgba(0, 103, 192, 120);
    color: {P.text_primary};
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
QTreeWidget::branch {{
    background: transparent;
}}
"""


class FluentTreeTable(QTreeWidget):
    """Fluent 树形表格：多列 + 可展开层级 + 深色样式。

    用法::

        tree = FluentTreeTable(headers=["名称", "状态", "大小"])
        root = tree.add_node("项目 A", values=["运行中", "12 MB"])
        tree.add_node("子任务 1", parent=root, values=["完成", "3 MB"])
    """

    def __init__(self, headers=(), parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(_QSS)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setHeaderHidden(not headers)
        if headers:
            self.setHeaderLabels(list(headers))
        self.setIndentation(20)
        self.header().setStretchLastSection(True)
        self.header().setHighlightSections(False)
        self.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def add_node(self, text: str, parent: QTreeWidgetItem | None = None,
                 values=(), icon: QIcon | None = None,
                 data=None) -> QTreeWidgetItem:
        cols = [text, *[str(v) for v in values]]
        item = QTreeWidgetItem(cols)
        if icon is not None:
            item.setIcon(0, icon)
        if data is not None:
            item.setData(0, Qt.ItemDataRole.UserRole, data)
        if parent is not None:
            parent.addChild(item)
        else:
            self.addTopLevelItem(item)
        return item

