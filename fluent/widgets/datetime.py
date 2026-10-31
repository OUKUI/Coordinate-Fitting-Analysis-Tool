"""Fluent 日期选择器与时间选择器（点击弹出日历 / 时间面板）。"""
from __future__ import annotations

from PySide6.QtCore import QDate, QPoint, QRectF, Qt, QTime, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QCalendarWidget, QFrame, QHBoxLayout, QLabel,
                               QTimeEdit, QVBoxLayout)
from PySide6.QtCore import QLocale

from ..theme import palette as P

_CALENDAR_QSS = f"""
QCalendarWidget QWidget {{
    background-color: {P.bg_layer_glass};
    color: {P.text_primary};
}}
QCalendarWidget QAbstractItemView {{
    background-color: {P.bg_layer_glass};
    color: {P.text_primary};
    selection-background-color: {P.accent};
    selection-color: {P.accent_on};
    outline: none;
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {P.text_tertiary};
}}
QCalendarWidget QToolButton {{
    background: transparent;
    color: {P.text_primary};
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 13px;
}}
QCalendarWidget QToolButton:hover {{ background: {P.fill_hover}; }}
QCalendarWidget QToolButton::menu-indicator {{ image: none; }}
QCalendarWidget QSpinBox {{
    background-color: {P.fill_layer};
    color: {P.text_primary};
    border: 1px solid {P.stroke_layer};
    border-radius: 4px;
}}
QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {{
    width: 14px;
    background-color: {P.fill_hover};
}}
QCalendarWidget QSpinBox::up-arrow {{
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-bottom: 4px solid {P.text_secondary};
}}
QCalendarWidget QSpinBox::down-arrow {{
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid {P.text_secondary};
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {P.bg_layer_alt};
    border-bottom: 1px solid {P.divider};
}}
"""

_TIME_QSS = f"""
QTimeEdit {{
    background-color: {P.fill_layer};
    color: {P.text_primary};
    border: 1px solid {P.stroke_layer};
    border-radius: {P.radius_input}px;
    padding: 0 10px;
    font-size: 20px;
    font-weight: 600;
}}
QTimeEdit:focus {{ border: 1px solid {P.accent}; }}
QTimeEdit::up-button, QTimeEdit::down-button {{
    width: 22px;
    background-color: {P.fill_hover};
}}
QTimeEdit::up-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {P.text_secondary};
}}
QTimeEdit::down-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {P.text_secondary};
}}
"""


class _PickerField(QFrame):
    """日期/时间字段公共外观：文字 + 右侧小图标。"""

    _icon = "date"

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PickerField")
        self.setFixedHeight(P.control_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            #PickerField {{
                background-color: {P.fill_layer};
                border: 1px solid {P.stroke_layer};
                border-radius: {P.radius_input}px;
            }}
            #PickerField:hover {{
                background-color: {P.fill_hover};
                border: 1px solid {P.stroke_hover};
            }}
            #PickerField[pressed="true"] {{
                border: 1px solid {P.accent};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 8, 0)
        self._label = QLabel(text)
        self._label.setStyleSheet("background: transparent; color: #BDBDBD;")
        lay.addWidget(self._label)
        self._pressed = False

    def set_text(self, text: str) -> None:
        self._label.setText(text)
        self._label.setStyleSheet(
            "background: transparent; color: " + P.text_primary + ";")

    def set_pressed(self, on: bool) -> None:
        self._pressed = on
        self.setProperty("pressed", on)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(P.text_secondary), 1.4)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx = self.width() - 18
        cy = self.height() / 2
        if self._icon == "date":
            r = 5
            p.drawRoundedRect(QRectF(cx - r, cy - r + 1, 2 * r, 2 * r - 1), 2, 2)
            p.drawLine(QPoint(cx - r, cy - 2.2), QPoint(cx + r, cy - 2.2))
            p.drawLine(QPoint(cx - 2, cy - r), QPoint(cx - 2, cy - r + 2.5))
            p.drawLine(QPoint(cx + 2, cy - r), QPoint(cx + 2, cy - r + 2.5))
        else:
            p.drawEllipse(QPoint(cx, cy - 2), 4.5, 4.5)
            p.drawLine(QPoint(cx, cy + 1), QPoint(cx, cy + 5))
            p.drawLine(QPoint(cx, cy + 5), QPoint(cx - 2, cy + 5))
        p.end()


class FluentDatePicker(_PickerField):
    """Fluent 日期选择器。"""

    dateChanged = Signal(QDate)

    def __init__(self, date: QDate | None = None, parent=None) -> None:
        super().__init__("", parent)
        self._icon = "date"
        self._date = date or QDate.currentDate()
        self._popup: QFrame | None = None
        self.set_text(self._date.toString("yyyy-MM-dd"))
        self._refresh_style()

    def _refresh_style(self) -> None:
        self.setFixedWidth(140)

    def date(self) -> QDate:
        return self._date

    def setDate(self, date: QDate) -> None:
        self._date = QDate(date)
        self.set_text(self._date.toString("yyyy-MM-dd"))
        self.dateChanged.emit(self._date)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_pressed(True)
            self._open_popup()
        super().mousePressEvent(event)

    def _open_popup(self) -> None:
        if self._popup is not None:
            return
        popup = QFrame(self.window(), Qt.WindowType.Popup)
        popup.setStyleSheet(f"""
            QFrame {{
                background-color: {P.bg_layer_glass};
                border: 1px solid {P.stroke_layer};
                border-radius: 8px;
            }}
        """)
        cal = QCalendarWidget(popup)
        cal.setLocale(QLocale(QLocale.Language.Chinese, QLocale.Country.China))
        cal.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal.setGridVisible(False)
        cal.setStyleSheet(_CALENDAR_QSS)
        cal.setSelectedDate(self._date)
        cal.clicked.connect(self._on_picked)
        lay = QVBoxLayout(popup)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addWidget(cal)
        popup.adjustSize()
        pos = self.mapToGlobal(QPoint(0, self.height() + 2))
        popup.move(pos)
        self._popup = popup
        popup.show()
        popup.raise_()

    def _on_picked(self, date: QDate) -> None:
        self.setDate(date)
        self._close_popup()

    def _close_popup(self) -> None:
        if self._popup is not None:
            self._popup.close()
            self._popup.deleteLater()
            self._popup = None
        self.set_pressed(False)


class FluentTimePicker(_PickerField):
    """Fluent 时间选择器。"""

    timeChanged = Signal(QTime)

    def __init__(self, time: QTime | None = None, parent=None) -> None:
        super().__init__("", parent)
        self._icon = "time"
        self._time = time or QTime.currentTime()
        self._popup: QFrame | None = None
        self.set_text(self._time.toString("HH:mm"))
        self.setFixedWidth(140)

    def time(self) -> QTime:
        return self._time

    def setTime(self, time: QTime) -> None:
        self._time = QTime(time)
        self.set_text(self._time.toString("HH:mm"))
        self.timeChanged.emit(self._time)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_pressed(True)
            self._open_popup()
        super().mousePressEvent(event)

    def _open_popup(self) -> None:
        if self._popup is not None:
            return
        popup = QFrame(self.window(), Qt.WindowType.Popup)
        popup.setStyleSheet(f"""
            QFrame {{
                background-color: {P.bg_layer_glass};
                border: 1px solid {P.stroke_layer};
                border-radius: 8px;
            }}
        """)
        edit = QTimeEdit(popup)
        edit.setTime(self._time)
        edit.setStyleSheet(_TIME_QSS)
        edit.setDisplayFormat("HH:mm")
        edit.setFixedSize(160, 48)
        edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit.timeChanged.connect(self._on_picked)
        lay = QVBoxLayout(popup)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(edit)
        popup.adjustSize()
        pos = self.mapToGlobal(QPoint(0, self.height() + 2))
        popup.move(pos)
        self._popup = popup
        popup.show()
        popup.raise_()
        edit.setFocus()
        edit.selectAll()

    def _on_picked(self, time: QTime) -> None:
        self.setTime(time)
        self._close_popup()

    def _close_popup(self) -> None:
        if self._popup is not None:
            self._popup.close()
            self._popup.deleteLater()
            self._popup = None
        self.set_pressed(False)
