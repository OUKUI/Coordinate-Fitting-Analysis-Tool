"""Fluent 分页表格：深色表格 + 分页栏 + 点击表头排序 + 右键菜单。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMenu, QPushButton,
                               QVBoxLayout, QWidget)

from ..theme import palette as P
from .combobox import FluentComboBox
from .table import FluentTableWidget


class FluentPagedTable(QWidget):
    """Fluent 分页表格。

    - set_rows(所有行) 自动分页
    - 点击表头排序（数值/文本自动识别）
    - 右键菜单：复制单元格 / 复制整行 / 导出 CSV / 刷新
    """

    pageChanged = Signal(int)

    def __init__(self, headers=(), rows=(), page_size: int = 20,
                 parent=None) -> None:
        super().__init__(parent)
        self._headers = list(headers)
        self._data: list[list] = []
        self._page_size = page_size
        self._page = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self._table = FluentTableWidget(self._headers, [])
        self._table.horizontalHeader().sectionClicked.connect(self._on_sort)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_menu)
        root.addWidget(self._table, 1)

        # 分页栏
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self._info = QLabel()
        self._info.setStyleSheet(
            "color: #8A8A8A; background: transparent; font-size: 12px;")
        bar.addWidget(self._info)

        bar.addStretch(1)

        self._prev = self._nav_btn("◀ 上一页")
        self._next = self._nav_btn("下一页 ▶")
        bar.addWidget(self._prev)
        bar.addWidget(self._next)

        self._pages_lbl = QLabel()
        self._pages_lbl.setStyleSheet(
            "color: #9D9D9D; background: transparent; font-size: 12px;")
        bar.addWidget(self._pages_lbl)

        bar.addSpacing(8)
        lbl_page = QLabel("每页")
        lbl_page.setStyleSheet(
            "color: #8A8A8A; background: transparent; font-size: 12px;")
        bar.addWidget(lbl_page)
        self._page_size_cb = FluentComboBox(["10", "20", "50", "100"])
        self._page_size_cb.setCurrentText(str(page_size))
        self._page_size_cb.setFixedWidth(64)
        self._page_size_cb.currentTextChanged.connect(self._on_page_size)
        bar.addWidget(self._page_size_cb)

        root.addLayout(bar)

        self._prev.clicked.connect(self.prev_page)
        self._next.clicked.connect(self.next_page)

        if rows:
            self.set_rows(rows)

    def _nav_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {P.fill_layer};
                color: {P.text_primary};
                border: 1px solid {P.stroke_layer};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {P.fill_hover};
                border-color: {P.stroke_hover};
            }}
            QPushButton:disabled {{
                color: {P.text_disabled};
                background-color: {P.fill_disabled};
            }}
        """)
        return btn

    # ---- 数据 ----
    def set_rows(self, rows) -> None:
        self._data = [list(r) for r in rows]
        self._page = 0
        self._render()

    def set_headers(self, headers) -> None:
        self._headers = list(headers)
        self._table.setHeaders(self._headers)

    def current_rows(self) -> list:
        start = self._page * self._page_size
        return self._data[start:start + self._page_size]

    def total_pages(self) -> int:
        return max(1, -(-len(self._data) // self._page_size))

    # ---- 分页 ----
    def _render(self) -> None:
        page_rows = self.current_rows()
        self._table.set_rows(page_rows)
        total_pages = self.total_pages()
        self._info.setText(f"共 {len(self._data)} 条")
        self._pages_lbl.setText(f"{self._page + 1} / {total_pages} 页")
        self._prev.setEnabled(self._page > 0)
        self._next.setEnabled(self._page < total_pages - 1)
        self.pageChanged.emit(self._page)

    def prev_page(self) -> None:
        if self._page > 0:
            self._page -= 1
            self._render()

    def next_page(self) -> None:
        if self._page < self.total_pages() - 1:
            self._page += 1
            self._render()

    def _on_page_size(self, text: str) -> None:
        try:
            self._page_size = int(text)
            self._page = 0
            self._render()
        except ValueError:
            pass

    # ---- 排序 ----
    def _on_sort(self, col: int) -> None:
        header = self._table.horizontalHeader()
        ascending = header.sortIndicatorSection() != col \
            or header.sortIndicatorOrder() == Qt.SortOrder.DescendingOrder
        if ascending:
            header.setSortIndicator(col, Qt.SortOrder.AscendingOrder)
        else:
            header.setSortIndicator(col, Qt.SortOrder.DescendingOrder)
        self._sort(col, ascending)

    def _sort(self, col: int, ascending: bool) -> None:
        def key(row):
            v = row[col] if col < len(row) else ""
            try:
                return (0, float(v))
            except (TypeError, ValueError):
                return (1, str(v).lower())
        self._data.sort(key=key, reverse=not ascending)
        self._render()

    # ---- 右键菜单 ----
    def _show_menu(self, pos) -> None:
        item = self._table.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self._table)
        act_copy_cell = menu.addAction("复制单元格")
        act_copy_row = menu.addAction("复制整行")
        menu.addSeparator()
        act_export = menu.addAction("导出 CSV…")
        act_refresh = menu.addAction("刷新")

        chosen = menu.exec(self._table.mapToGlobal(pos))
        row = item.row()
        col = item.column()
        if chosen == act_copy_cell:
            self._copy_text(self._table.item(row, col).text() if self._table.item(row, col) else "")
        elif chosen == act_copy_row:
            values = [self._table.item(row, c).text()
                      if self._table.item(row, c) else "" for c in range(self._table.columnCount())]
            self._copy_text("\t".join(values))
        elif chosen == act_export:
            self._export_csv()
        elif chosen == act_refresh:
            self._render()

    def _copy_text(self, text: str) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

    def _export_csv(self) -> None:
        from pathlib import Path
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 CSV", str(Path.home() / "table_export.csv"),
            "CSV 文件 (*.csv)")
        if not path:
            return
        import csv
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(self._headers)
            writer.writerows(self._data)
        from .toast import FluentToast
        FluentToast.popup(self.window(), f"已导出到 {Path(path).name}")
