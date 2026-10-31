"""Fluent 特效：玻璃拟态卡片 / Reveal 悬停光效 / 淡入动画。"""
from __future__ import annotations

from PySide6.QtCore import (QEasingCurve, QPointF, QPropertyAnimation, QRectF,
                            Qt)
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QPushButton, QWidget

from ..theme import palette as P


class FluentAcrylicCard(QFrame):
    """Fluent 玻璃拟态卡片：半透明 + 渐变高光 + 描边。"""

    def __init__(self, parent=None, tint: str = "#0067C0",
                 opacity: float = 0.16, radius: int = 10) -> None:
        super().__init__(parent)
        self._tint = QColor(tint)
        self._opacity = opacity
        self._radius = radius
        self.setObjectName("AcrylicCard")
        self.setStyleSheet("#AcrylicCard { background: transparent; border: none; }")

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)

        # 基底半透明深色
        base = QColor(255, 255, 255)
        base.setAlpha(round(14 * self._opacity * 10))
        p.fillRect(self.rect(), QColor(32, 32, 32, 230))

        # 顶部高光渐变（玻璃感）
        grad = QLinearGradient(0, 0, 0, self.height())
        top = QColor(255, 255, 255)
        top.setAlpha(round(60 * self._opacity))
        bot = QColor(255, 255, 255)
        bot.setAlpha(0)
        grad.setColorAt(0.0, top)
        grad.setColorAt(1.0, bot)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(r, self._radius, self._radius)

        # 色调
        tint = QColor(self._tint)
        tint.setAlpha(round(255 * self._opacity))
        p.setBrush(tint)
        p.drawRoundedRect(r, self._radius, self._radius)

        # 描边
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 40), 1))
        p.drawRoundedRect(r, self._radius, self._radius)
        p.end()


class FluentRevealButton(QPushButton):
    """Fluent 按钮：悬停时光效跟随鼠标（Reveal）。"""

    def __init__(self, text: str = "", parent=None, variant: str = "standard") -> None:
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(P.button_height)
        self.setMouseTracking(True)
        self._hover = False
        self._cursor = QPointF()

    def _bg(self) -> str:
        if self.variant == "accent":
            return P.accent
        if self.variant == "danger":
            return P.danger
        return P.fill_layer

    def _fg(self) -> str:
        if self.variant in ("accent", "danger"):
            return "#FFFFFF"
        return P.text_primary

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        bg = QColor(self._bg())
        if self.variant == "standard" and self._hover:
            bg = QColor(P.fill_hover)
        p.setPen(QPen(QColor(P.stroke_layer), 1))
        p.setBrush(bg)
        p.drawRoundedRect(r, P.radius_button, P.radius_button)

        if self._hover and self.underMouse():
            # 跟随鼠标的光斑
            glow = QRadialGradient(self._cursor, max(60, r.width() * 0.5))
            c = QColor(255, 255, 255)
            c.setAlpha(46 if self.variant in ("accent", "danger") else 26)
            glow.setColorAt(0.0, c)
            c2 = QColor(255, 255, 255)
            c2.setAlpha(0)
            glow.setColorAt(1.0, c2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(glow)
            p.drawRoundedRect(r, P.radius_button, P.radius_button)

        p.setPen(QColor(self._fg()))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event) -> None:
        self._cursor = event.position()
        self.update()
        super().mouseMoveEvent(event)


class FluentAnimatedWidget(QWidget):
    """淡入动画容器：显示时 200ms 淡入。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
