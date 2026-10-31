"""Fluent 搜索框（SearchBox）：左侧放大镜、右侧清除按钮。"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLineEdit

from ..theme import palette as P


class FluentSearchBox(QLineEdit):
    """Fluent 风格搜索框。

    - 左侧自绘放大镜图标
    - 有输入时右侧显示清除按钮（点击清空并发射 cleared）
    - 回车发射 search(text)
    """

    search = Signal(str)
    cleared = Signal()

    _hover = False

    def __init__(self, placeholder: str = "搜索…", parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(P.control_height)
        self.textChanged.connect(lambda _: self.update())
        self.returnPressed.connect(lambda: self.search.emit(self.text().strip()))
        self._refresh()

    def _refresh(self) -> None:
        border = P.accent if self.hasFocus() else (P.stroke_hover if self._hover
                                                   else P.stroke_layer)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {P.bg_layer_glass};
                color: {P.text_primary};
                border: 1px solid {border};
                border-radius: {P.radius_input}px;
                padding: 0 30px 0 32px;
                selection-background-color: {P.accent};
                selection-color: {P.accent_on};
            }}
            QLineEdit:hover {{
                border: 1px solid {P.stroke_hover};
            }}
            QLineEdit:focus {{
                border: 1px solid {P.accent};
            }}
            QLineEdit:disabled {{
                background-color: {P.fill_disabled};
                color: {P.text_disabled};
            }}
            QLineEdit::placeholder {{
                color: {P.text_tertiary};
            }}
        """)

    # ---- 图标与清除 ----
    def _clear_rect(self) -> QRectF:
        d = 16
        return QRectF(self.width() - 26, (self.height() - d) / 2, d, d)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 放大镜
        cy = self.height() / 2
        col = QColor(P.text_secondary)
        pen = QPen(col, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(13 - 5, cy - 5, 10, 10))
        p.drawLine(QPointF(17, cy + 3.5), QPointF(21, cy + 7.5))

        # 清除按钮
        if self.text():
            rect = self._clear_rect()
            cursor = getattr(self, "_cursor_pos", None)
            hover = bool(cursor) and rect.contains(cursor)
            if hover:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(P.fill_hover))
                p.drawEllipse(rect)
            c = QColor(P.text_primary if hover else P.text_secondary)
            pen = QPen(c, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            d = rect.width() * 0.28
            cx, cyc = rect.center().x(), rect.center().y()
            p.drawLine(QPointF(cx - d, cyc - d), QPointF(cx + d, cyc + d))
            p.drawLine(QPointF(cx + d, cyc - d), QPointF(cx - d, cyc + d))
        p.end()

    _cursor_pos = None

    def mouseMoveEvent(self, event) -> None:
        self._cursor_pos = event.position()
        self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.text():
            if self._clear_rect().contains(event.position()):
                self.clear()
                self.cleared.emit()
                event.accept()
                return
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        self._hover = True
        self._refresh()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._cursor_pos = None
        self._refresh()
        super().leaveEvent(event)
