"""Fluent 图片查看器（缩放/平移）与音频频谱可视化。"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QLinearGradient, QPainter, QPen, QPixmap)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                               QWidget)

from ..theme import palette as P


class FluentImageViewer(QWidget):
    """Fluent 图片查看器：滚轮缩放、拖拽平移、双击适配窗口。

    用法::

        viewer = FluentImageViewer()
        viewer.load("photo.png")
        viewer.set_pixmap(pixmap)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._scale = 1.0
        self._offset = QPointF(0, 0)
        self._fit = True
        self._dragging = False
        self._last_pos = QPointF()
        self.setMinimumSize(300, 240)
        self.setMouseTracking(True)
        self._build_toolbar()

    def _build_toolbar(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        bar = QHBoxLayout()
        bar.setContentsMargins(8, 6, 8, 6)
        bar.setSpacing(6)

        def btn(text: str, tip: str, cb) -> QPushButton:
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedHeight(26)
            b.clicked.connect(cb)
            b.setStyleSheet(f"""
                QPushButton {{
                    background-color: {P.fill_layer};
                    color: {P.text_primary};
                    border: 1px solid {P.stroke_layer};
                    border-radius: 4px;
                    padding: 0 10px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {P.fill_hover};
                    border-color: {P.stroke_hover};
                }}
            """)
            return b

        self._zoom_lbl = QLabel("100%")
        self._zoom_lbl.setStyleSheet(
            "color: #9D9D9D; background: transparent; font-size: 12px;")
        bar.addWidget(self._zoom_lbl)

        bar.addStretch(1)
        bar.addWidget(btn("适配窗口", "双击图片也可适配", self.set_fit))
        bar.addWidget(btn("−", "缩小", lambda: self.zoom_by(1 / 1.2)))
        bar.addWidget(btn("＋", "放大", lambda: self.zoom_by(1.2)))
        bar.addWidget(btn("100%", "原尺寸", lambda: self.zoom_reset()))
        outer.addLayout(bar)

    # ---- 接口 ----
    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._scale = 1.0
        self._offset = QPointF(0, 0)
        self._fit = True
        self.update()

    def load(self, path: str) -> bool:
        pm = QPixmap(path)
        if pm.isNull():
            return False
        self.set_pixmap(pm)
        return True

    def zoom_reset(self) -> None:
        self._scale = 1.0
        self._offset = QPointF(0, 0)
        self._fit = False
        self.update()

    def set_fit(self) -> None:
        self._fit = True
        self.update()

    def zoom_by(self, factor: float, center: QPointF | None = None) -> None:
        if self._pixmap is None:
            return
        if center is None:
            center = QPointF(self.width() / 2, self.height() / 2)
        old = self._scale
        new = max(0.05, min(20.0, old * factor))
        if new == old:
            return
        # 保持光标下内容不动
        rel = (center - self._content_pos()) / old
        self._scale = new
        self._offset = center - rel * new - self._centered_base(center)
        self._fit = False
        self.update()

    def _centered_base(self, center: QPointF) -> QPointF:
        if self._pixmap is None:
            return QPointF(0, 0)
        return QPointF(center.x() - self._pixmap.width() * self._scale / 2,
                       center.y() - self._pixmap.height() * self._scale / 2)

    def _content_pos(self) -> QPointF:
        if self._pixmap is None:
            return QPointF(0, 0)
        return QPointF((self.width() - self._pixmap.width() * self._scale) / 2,
                       (self.height() - self._pixmap.height() * self._scale) / 2) \
            + self._offset

    # ---- 交互 ----
    def wheelEvent(self, event) -> None:
        if self._pixmap is not None:
            self.zoom_by(1.2 if event.angleDelta().y() > 0 else 1 / 1.2,
                         event.position())
        super().wheelEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._pixmap is not None:
            self._dragging = True
            self._last_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._dragging and self._pixmap is not None:
            delta = event.position() - self._last_pos
            self._last_pos = event.position()
            self._offset += delta
            self._fit = False
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if self._pixmap is not None:
            self.set_fit()
        super().mouseDoubleClickEvent(event)

    # ---- 绘制 ----
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QColor("#1F1F1F"))

        if self._pixmap is None or self._pixmap.isNull():
            p.setPen(QColor("#6E6E6E"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "无图片")
            p.end()
            return

        pm = self._pixmap
        if self._fit:
            s = min(self.width() / pm.width(), self.height() / pm.height())
            if s > 0:
                w, h = pm.width() * s, pm.height() * s
                x, y = (self.width() - w) / 2, (self.height() - h) / 2
                p.drawPixmap(int(x), int(y), int(w), int(h), pm)
            self._zoom_lbl.setText("适配")
        else:
            pos = self._content_pos()
            p.drawPixmap(int(pos.x()), int(pos.y()),
                         int(pm.width() * self._scale),
                         int(pm.height() * self._scale), pm)
            self._zoom_lbl.setText(f"{self._scale * 100:.0f}%")
        p.end()


class FluentAudioVisualizer(QWidget):
    """Fluent 音频频谱可视化：柱状频谱动画。

    用法::

        viz = FluentAudioVisualizer(bars=48)
        viz.start_demo()            # 模拟动画
        viz.set_levels([0.1, 0.5, ...])  # 或喂入真实频谱
    """

    def __init__(self, bars: int = 48, parent=None) -> None:
        super().__init__(parent)
        self._bars = bars
        self._levels = [0.0] * bars
        self._phase = 0.0
        self.setMinimumHeight(120)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._demo_tick)

    def set_levels(self, levels) -> None:
        """levels: 0.0 ~ 1.0 的列表，长度与 bars 相同。"""
        self._levels = [max(0.0, min(1.0, v)) for v in levels[:self._bars]]
        if len(self._levels) < self._bars:
            self._levels += [0.0] * (self._bars - len(self._levels))
        self.update()

    def start_demo(self, interval: int = 70) -> None:
        if not self._timer.isActive():
            self._timer.start(interval)

    def stop_demo(self) -> None:
        self._timer.stop()

    def _demo_tick(self) -> None:
        self._phase += 0.18
        levels = []
        for i in range(self._bars):
            base = 0.12 + 0.4 * abs(math.sin(self._phase + i * 0.45))
            wave = 0.3 * abs(math.sin(self._phase * 1.7 + i * 0.13))
            levels.append(min(1.0, base + wave))
        self.set_levels(levels)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#1B1B1B"))
        if not self._bars:
            p.end()
            return
        gap = max(2, w / (self._bars * 3))
        bar_w = max(2, (w - gap * (self._bars + 1)) / self._bars)
        grad = QLinearGradient(0, h, 0, 0)
        grad.setColorAt(0.0, QColor(P.accent))
        grad.setColorAt(1.0, QColor(P.accent_light))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        for i, v in enumerate(self._levels):
            bh = max(2.0, (h - 8) * v)
            x = gap + i * (bar_w + gap)
            rect = QRectF(x, h - 4 - bh, bar_w, bh)
            p.drawRoundedRect(rect, 2, 2)
        p.end()
