from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableWidgetItem

from fluent.widgets import FluentTableWidget
from core.mold_advisor import get_advice_table


class AdviceTableWidget(FluentTableWidget):
    point_highlighted = Signal(int)

    def __init__(self, parent=None):
        super().__init__(
            headers=["#", "角度(°)", "偏差", "X", "Y", "修模建议"],
            parent=parent)
        self.setEditTriggers(FluentTableWidget.EditTrigger.NoEditTriggers)
        self.itemSelectionChanged.connect(self._on_selection)

    def update_data(self, polar_points, unit="mm"):
        factor = 1000.0 if unit == "μm" else 1.0
        rows = get_advice_table(polar_points)
        self.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.setItem(i, 0, QTableWidgetItem(str(row["no"])))
            self.setItem(i, 1, QTableWidgetItem(row["angle"]))
            val = float(row["delta_r"])
            item_delta = QTableWidgetItem(f"{val * factor:+.2f}")
            item_delta.setForeground(QColor("#F87171") if val > 0 else QColor("#4ADE80"))
            item_delta.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(i, 2, item_delta)
            self.setItem(i, 3, QTableWidgetItem(row["x"]))
            self.setItem(i, 4, QTableWidgetItem(row["y"]))
            self.setItem(i, 5, QTableWidgetItem(row["advice"]))

    def _on_selection(self):
        rows = self.selectedIndexes()
        if rows:
            self.point_highlighted.emit(rows[0].row())
