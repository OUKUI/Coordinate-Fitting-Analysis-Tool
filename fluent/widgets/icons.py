"""自绘图标（纯 QPainter 绘制，无需图片资源）。

提供信息/成功/警告/错误徽章与关闭按钮，供信息栏、消息框等复用。
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget

from ..theme import palette as P

KIND_INFO = "info"
KIND_SUCCESS = "success"
KIND_WARNING = "warning"
KIND_ERROR = "error"


def _kind_color(kind: str) -> str:
    return {
        KIND_INFO: P.info,
        KIND_SUCCESS: P.success,
        KIND_WARNING: P.warning,
        KIND_ERROR: P.danger,
    }.get(kind, P.info)


class IconBadge(QWidget):
    """圆形徽章：info 显示 i，success 显示勾，warning 显示 !，error 显示叉。"""

    def __init__(self, kind: str = KIND_INFO, color: str = "", size: int = 28,
                 parent=None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.color = color
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = self.width()
        c = QColor(self.color or _kind_color(self.kind))

        bg = QColor(c)
        bg.setAlpha(45)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawEllipse(0, 0, size, size)

        pen = QPen(c, max(1.6, size / 14), Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx = cy = size / 2

        if self.kind == KIND_SUCCESS:
            p.drawPolyline([
                QPointF(cx - size * 0.28, cy),
                QPointF(cx - size * 0.08, cy + size * 0.2),
                QPointF(cx + size * 0.3, cy - size * 0.22),
            ])
        elif self.kind == KIND_ERROR:
            d = size * 0.2
            p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
            p.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))
        elif self.kind == KIND_WARNING:
            tri = [QPointF(cx, cy - size * 0.22),
                   QPointF(cx - size * 0.26, cy + size * 0.24),
                   QPointF(cx + size * 0.26, cy + size * 0.24)]
            p.drawPolygon(tri)
            f = QFont()
            f.setBold(True)
            f.setPixelSize(max(8, int(size * 0.42)))
            p.setFont(f)
            p.setPen(c)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "!")
        else:  # info
            p.drawEllipse(QPointF(cx, cy - size * 0.16), size * 0.06, size * 0.06)
            p.drawLine(QPointF(cx, cy - size * 0.05), QPointF(cx, cy + size * 0.24))
        p.end()


class CloseButton(QAbstractButton):
    """圆形关闭按钮：默认透明，悬停时显示背景圆 + 加亮叉号。"""

    def __init__(self, parent=None, size: int = 24) -> None:
        super().__init__(parent)
        self._hover = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(P.fill_hover))
            p.drawEllipse(self.rect())
        d = self.width() * 0.3
        c = QColor(P.text_primary if self._hover else P.text_secondary)
        pen = QPen(c, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(self.width() / 2 - d, self.height() / 2 - d),
                   QPointF(self.width() / 2 + d, self.height() / 2 + d))
        p.drawLine(QPointF(self.width() / 2 + d, self.height() / 2 - d),
                   QPointF(self.width() / 2 - d, self.height() / 2 + d))
        p.end()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)
