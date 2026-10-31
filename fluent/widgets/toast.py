"""Fluent 轻提示：Toast / Tooltip / TeachingTip。"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QVBoxLayout, QWidget)

from ..theme import palette as P
from .button import FluentButton
from .icons import CloseButton, IconBadge

_TOAST_QSS = f"""
QFrame {{
    background-color: {P.bg_layer_glass};
    border: 1px solid {P.stroke_layer};
    border-radius: 8px;
}}
"""


class FluentToast(QWidget):
    """Fluent 轻提示：右上角弹出，自动淡入淡出消失。

    用法::

        FluentToast.popup(window, "文件已保存", kind="success")
    """

    _registry: list["FluentToast"] = []

    def __init__(self, parent: QWidget, message: str, kind: str = "info",
                 duration: int = 2500) -> None:
        super().__init__(parent, Qt.WindowType.Tool
                         | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(_TOAST_QSS)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 8, 10)
        lay.setSpacing(10)
        lay.addWidget(IconBadge(kind, size=20))
        msg = QLabel(message)
        msg.setStyleSheet("background: transparent;")
        lay.addWidget(msg)
        close = CloseButton(self, size=20)
        close.clicked.connect(self.close)
        lay.addWidget(close)

        self.adjustSize()
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._fade = QTimer(self)
        self._fade.setInterval(30)
        self._fade.timeout.connect(self._fade_tick)
        self._alpha = 0.0
        self._fading_in = True

        self._position()
        self._fade.start()

        if parent is not None:
            parent.installEventFilter(self)

        if duration > 0:
            QTimer.singleShot(duration, self._start_fade_out)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.parent() and event.type() == QEvent.Type.Move:
            self._position()
        return super().eventFilter(obj, event)

    def _position(self) -> None:
        parent = self.parent()
        if parent is not None and parent.isVisible():
            geo = parent.geometry()
            self.move(geo.right() - self.width() - 24, geo.top() + 24)
        else:
            screen = self.screen()
            if screen is None:
                from PySide6.QtWidgets import QApplication
                screen = QApplication.primaryScreen()
            geo = screen.availableGeometry()
            self.move(geo.right() - self.width() - 24, geo.top() + 24)

    def _fade_tick(self) -> None:
        if self._fading_in:
            self._alpha = min(1.0, self._alpha + 0.08)
            if self._alpha >= 1.0:
                self._fading_in = False
                self._fade.stop()
        else:
            self._alpha = max(0.0, self._alpha - 0.05)
            if self._alpha <= 0.0:
                self._fade.stop()
                self.close()
        self._effect.setOpacity(self._alpha)

    def _start_fade_out(self) -> None:
        if self.isVisible():
            self._fading_in = False
            self._fade.start()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.raise_()

    def closeEvent(self, event) -> None:
        if self in self._registry:
            self._registry.remove(self)
        super().closeEvent(event)

    @classmethod
    def popup(cls, parent: QWidget | None, message: str, kind: str = "info",
              duration: int = 2500) -> "FluentToast":
        toast = cls(parent, message, kind, duration)
        cls._registry.append(toast)
        toast.show()
        return toast


class FluentTooltip(QLabel):
    """Fluent 工具提示：悬停时显示在控件上方，自动消失。"""

    _current: "FluentTooltip | None" = None

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWordWrap(True)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {P.tooltip_bg};
                color: {P.text_primary};
                border: 1px solid {P.stroke_layer};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """)

    @classmethod
    def show_text(cls, target: QWidget, text: str, delay: int = 2000,
                  offset: int = 10) -> "FluentTooltip":
        if cls._current is not None:
            cls._current.close()
        tip = cls(text)
        tip.adjustSize()
        g = target.mapToGlobal(QPoint(0, -offset))
        pos = QPoint(g.x() + (target.width() - tip.width()) // 2,
                     g.y() - tip.height())
        tip.move(pos)
        cls._current = tip
        tip.show()
        if delay > 0:
            QTimer.singleShot(delay, tip.close)
        return tip


class FluentTeachingTip(QFrame):
    """Fluent 教学提示：带箭头的说明气泡，指向目标控件。"""

    _current: "FluentTeachingTip | None" = None

    def __init__(self, target: QWidget | None, title: str, message: str = "") -> None:
        self._target = target
        parent = target.window() if target is not None else None
        super().__init__(parent if parent is not None else None,
                         Qt.WindowType.Tool
                         | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("TeachingTip")
        self.setStyleSheet(f"""
            #TeachingTip {{
                background-color: {P.bg_layer_glass};
                border: 1px solid {P.stroke_layer};
                border-radius: 8px;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 10, 12)
        lay.setSpacing(6)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "background: transparent; font-size: 13px; font-weight: 600;")
        lay.addWidget(title_lbl)
        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setWordWrap(True)
            msg_lbl.setStyleSheet(
                "background: transparent; font-size: 12px; color: #BDBDBD;")
            lay.addWidget(msg_lbl)

        row = QHBoxLayout()
        row.addStretch(1)
        close = CloseButton(self, size=20)
        close.clicked.connect(self.close)
        row.addWidget(close)
        lay.addLayout(row)

        self._target = target
        self._arrow_rect = None
        self.adjustSize()

    def set_action(self, text: str, callback, accent: bool = True) -> None:
        btn = FluentButton(text, variant="accent" if accent else "standard")
        btn.setMinimumHeight(28)
        btn.clicked.connect(callback)
        lay = self.layout()
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(btn)
        lay.addLayout(row)
        self.adjustSize()

    def _position(self) -> None:
        if self._target is None:
            return
        g = self._target.mapToGlobal(self._target.rect().topLeft())
        x = g.x() + (self._target.width() - self.width()) // 2
        y = g.y() - self.height() - 8
        self.move(x, y)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._target is not None:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            cx = self.width() // 2
            h = self.height() - 1
            tri = QPolygonF([
                QPointF(cx - 8, h),
                QPointF(cx + 8, h),
                QPointF(cx, h + 8),
            ])
            p.setBrush(QColor(P.bg_layer_glass))
            p.setPen(QColor(P.stroke_layer))
            p.drawPolygon(tri)
            p.end()

    @classmethod
    def show_tip(cls, target: QWidget, title: str, message: str = "",
                 duration: int = 3000, action=None) -> "FluentTeachingTip":
        if cls._current is not None:
            cls._current.close()
        tip = cls(target, title, message)
        if action is not None:
            text, callback, accent = action
            tip.set_action(text, callback, accent)
        tip._position()
        cls._current = tip
        tip.show()
        if duration > 0:
            QTimer.singleShot(duration, tip.close)
        return tip
