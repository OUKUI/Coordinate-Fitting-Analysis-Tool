"""Fluent 嵌入式日历视图与日期范围选择器。"""
from __future__ import annotations

import calendar as _cal
from datetime import date

from PySide6.QtCore import QDate, QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from ..theme import palette as P

_WEEK = ["一", "二", "三", "四", "五", "六", "日"]


class FluentCalendarView(QWidget):
    """Fluent 日历视图：可嵌入任意界面，支持选中/今天/悬停高亮。"""

    dateChanged = Signal(QDate)

    def __init__(self, date: QDate | None = None, parent=None) -> None:
        super().__init__(parent)
        self._current = QDate(date) if date else QDate.currentDate()
        self._selected = QDate(self._current)
        self._hover = None
        self.setMinimumSize(260, 300)
        self.setMouseTracking(True)

    def selected_date(self) -> QDate:
        return self._selected

    def set_selected_date(self, d: QDate) -> None:
        self._selected = QDate(d)
        self._current = QDate(d)
        self.update()

    # ---- 布局计算 ----
    def _header_rect(self) -> QRectF:
        return QRectF(0, 8, self.width(), 34)

    def _week_rect(self) -> QRectF:
        return QRectF(10, 44, self.width() - 20, 22)

    def _grid_rect(self) -> QRectF:
        return QRectF(10, 70, self.width() - 20, self.height() - 84)

    def _cell_rect(self, index: int) -> QRectF:
        g = self._grid_rect()
        cw = g.width() / 7
        ch = g.height() / 6
        row, col = divmod(index, 7)
        return QRectF(g.left() + col * cw, g.top() + row * ch, cw, ch)

    def _index_at(self, pos) -> int | None:
        g = self._grid_rect()
        if not g.contains(pos):
            return None
        cw = g.width() / 7
        ch = g.height() / 6
        col = int((pos.x() - g.left()) / cw)
        row = int((pos.y() - g.top()) / ch)
        return max(0, min(41, row * 7 + col))

    # ---- 交互 ----
    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        hr = self._header_rect()
        if hr.contains(pos):
            mid = self.width() / 2
            if pos.x() < mid - 40:
                self._shift_month(-1)
            elif pos.x() > mid + 40:
                self._shift_month(1)
            return
        idx = self._index_at(pos)
        if idx is not None:
            day = self._day_at_index(idx)
            if day is not None:
                self._selected = day
                self.update()
                self.dateChanged.emit(day)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        self._hover = self._index_at(event.position())
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = None
        self.update()
        super().leaveEvent(event)

    def _shift_month(self, delta: int) -> None:
        self._current = self._current.addMonths(delta)
        self.update()

    def _day_at_index(self, idx: int) -> QDate | None:
        first = self._current.addDays(1 - self._current.day())
        first_dow = first.dayOfWeek()  # 1=周一
        leading = first_dow - 1
        d = first.addDays(idx - leading)
        if d.month() != self._current.month():
            return None
        return d

    # ---- 绘制 ----
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 头部
        hr = self._header_rect()
        p.setFont(self._header_font())
        p.setPen(QColor(P.text_primary))
        label = f"{self._current.year()} 年 {self._current.month()} 月"
        p.drawText(QRectF(0, hr.top(), self.width(), hr.height()),
                   Qt.AlignmentFlag.AlignCenter, label)
        p.setPen(QColor(P.text_secondary))
        p.drawText(QRectF(8, hr.top(), 30, hr.height()),
                   Qt.AlignmentFlag.AlignVCenter, "◀")
        p.drawText(QRectF(self.width() - 38, hr.top(), 30, hr.height()),
                   Qt.AlignmentFlag.AlignVCenter, "▶")

        # 星期表头
        wr = self._week_rect()
        cw = wr.width() / 7
        p.setFont(self._week_font())
        for i, w in enumerate(_WEEK):
            p.setPen(QColor(P.text_secondary))
            p.drawText(QRectF(wr.left() + i * cw, wr.top(), cw, wr.height()),
                       Qt.AlignmentFlag.AlignCenter, w)

        # 日期格
        g = self._grid_rect()
        cw, ch = g.width() / 7, g.height() / 6
        today = QDate.currentDate()
        for idx in range(42):
            d = self._day_at_index(idx)
            rect = self._cell_rect(idx).adjusted(2, 2, -2, -2)
            in_month = d is not None and d.month() == self._current.month()
            if d is None:
                continue
            if self._hover == idx:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(P.fill_hover))
                p.drawRoundedRect(rect, 6, 6)
            if d == self._selected:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(P.accent))
                p.drawRoundedRect(rect, 6, 6)
                p.setPen(QColor(P.accent_on))
            elif d == today:
                pen = QPen(QColor(P.accent), 2)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(rect, 6, 6)
                p.setPen(QColor(P.text_primary))
            else:
                p.setPen(QColor(P.text_primary if in_month else P.text_tertiary))
            p.setFont(self._day_font())
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(d.day()))
        p.end()

    def _header_font(self) -> QFont:
        f = QFont(self.font())
        f.setBold(True)
        f.setPointSizeF(f.pointSizeF() + 1)
        return f

    def _week_font(self) -> QFont:
        f = QFont(self.font())
        f.setPointSizeF(max(7.0, f.pointSizeF() - 1))
        return f

    def _day_font(self) -> QFont:
        return QFont(self.font())


class FluentDateRangePicker(QFrame):
    """Fluent 日期范围选择器：点击弹出双日历面板选择起止日期。"""

    rangeChanged = Signal(QDate, QDate)

    def __init__(self, start: QDate | None = None, end: QDate | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self._start = QDate(start) if start else QDate.currentDate().addDays(-6)
        self._end = QDate(end) if end else QDate.currentDate()
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background: transparent;")
        lay.addWidget(self._label)
        self._refresh()
        self._popup = None

    def _refresh(self) -> None:
        self.setStyleSheet(f"""
            FluentDateRangePicker {{
                background-color: {P.fill_layer};
                border: 1px solid {P.stroke_layer};
                border-radius: {P.radius_input}px;
            }}
            FluentDateRangePicker:hover {{
                background-color: {P.fill_hover};
                border: 1px solid {P.stroke_hover};
            }}
        """)
        self._label.setText(
            f"{self._start.toString('yyyy-MM-dd')}  ~  {self._end.toString('yyyy-MM-dd')}")

    def range(self) -> tuple[QDate, QDate]:
        return self._start, self._end

    def set_range(self, start: QDate, end: QDate) -> None:
        if start <= end:
            self._start, self._end = QDate(start), QDate(end)
            self._refresh()
            self.rangeChanged.emit(self._start, self._end)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_popup()
        super().mousePressEvent(event)

    def _open_popup(self) -> None:
        popup = QFrame(self.window(), Qt.WindowType.Popup)
        popup.setStyleSheet(f"""
            QFrame {{
                background-color: {P.bg_layer_glass};
                border: 1px solid {P.stroke_layer};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(popup)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        cal_row = QHBoxLayout()
        cal_row.setSpacing(10)
        self._cal1 = FluentCalendarView(self._start)
        self._cal2 = FluentCalendarView(self._end)
        self._cal1.setFixedWidth(250)
        self._cal2.setFixedWidth(250)
        self._cal1.dateChanged.connect(self._on_pick)
        self._cal2.dateChanged.connect(self._on_pick)
        cal_row.addWidget(self._cal1)
        cal_row.addWidget(self._cal2)
        lay.addLayout(cal_row)

        presets = QHBoxLayout()
        for text, days in [("最近 7 天", 7), ("最近 30 天", 30),
                           ("本月", 0), ("今年", 1)]:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {P.fill_layer};
                    color: {P.text_primary};
                    border: 1px solid {P.stroke_layer};
                    border-radius: 4px;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{
                    background-color: {P.fill_hover};
                    border-color: {P.stroke_hover};
                }}
            """)
            btn.clicked.connect(lambda _=False, d=days: self._apply_preset(popup, d))
            presets.addWidget(btn)
        presets.addStretch(1)
        lay.addLayout(presets)

        popup.adjustSize()
        pos = self.mapToGlobal(QPoint(0, self.height() + 2))
        popup.move(pos)
        self._popup = popup
        popup.show()
        popup.raise_()

    def _apply_preset(self, popup: QFrame, days: int) -> None:
        today = QDate.currentDate()
        if days > 0:
            self.set_range(today.addDays(-(days - 1)), today)
        elif days == 0:  # 本月
            self.set_range(QDate(today.year(), today.month(), 1), today)
        else:  # 今年
            self.set_range(QDate(today.year(), 1, 1), today)
        self._close_popup(popup)

    def _on_pick(self, d: QDate) -> None:
        if self._cal1 is not None and d == self._cal1.selected_date() \
                and self._start != d:
            if d <= self._end:
                self._start = d
                self._refresh()
                self.rangeChanged.emit(self._start, self._end)
        elif self._cal2 is not None:
            if d >= self._start:
                self._end = d
                self._refresh()
                self.rangeChanged.emit(self._start, self._end)

    def _close_popup(self, popup: QFrame) -> None:
        self._popup = None
        popup.close()
        popup.deleteLater()
