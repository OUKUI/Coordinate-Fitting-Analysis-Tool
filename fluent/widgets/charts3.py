"""Fluent 高级图表：箱线图 / 时间序列图。"""
from __future__ import annotations

import math
from datetime import date, datetime

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from ..theme import palette as P
from .charts import SERIES_COLORS, _ChartBase, _fmt

_GRID = QColor("#3A3A3A")
_LABEL = QColor("#9D9D9D")


class FluentBoxChart(_ChartBase):
    """Fluent 箱线图（盒须图）：每个分类可含多个箱体。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._categories: list[str] = []
        self._boxes: dict[str, list] = {}
        self._hover: tuple[int, int] | None = None

    def add_box(self, category: str, q1: float, median: float, q3: float,
                whisker_min: float, whisker_max: float,
                color: str = "") -> "FluentBoxChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._boxes.get(category, [])) % len(SERIES_COLORS)])
        self._boxes.setdefault(category, []).append(
            (q1, median, q3, whisker_min, whisker_max, c))
        if category not in self._categories:
            self._categories.append(category)
        self.update()
        return self

    def _bounds(self) -> tuple[float, float]:
        lo, hi = 0.0, 1.0
        for boxes in self._boxes.values():
            for q1, med, q3, wmin, wmax, _ in boxes:
                lo = min(lo, wmin)
                hi = max(hi, wmax)
        return lo, hi

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        if not self._categories:
            p.setFont(self._tick_font())
            p.setPen(_LABEL)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            p.end()
            return
        plot = self._plot_rect()
        lo, hi = self._bounds()
        self._draw_y_grid(p, plot, lo, hi)
        n = len(self._categories)
        self._draw_x_labels(p, plot, self._categories)
        slot_w = plot.width() / n

        def y(v): return plot.bottom() - (v - lo) / (hi - lo) * plot.height()

        for ci, cat in enumerate(self._categories):
            boxes = self._boxes[cat]
            cx = plot.left() + ci * slot_w + slot_w / 2
            group_w = slot_w * 0.6
            bw = min(24.0, group_w / len(boxes) * 0.7)
            for bi, (q1, med, q3, wmin, wmax, color) in enumerate(boxes):
                x = cx + (bi - (len(boxes) - 1) / 2) * (group_w / len(boxes))
                hover = self._hover == (ci, bi)
                c = color.lighter(150) if hover else color
                pen = QPen(c, 2)
                p.setPen(pen)
                # 须线
                p.drawLine(QPointF(x, y(wmax)), QPointF(x, y(wmin)))
                p.drawLine(QPointF(x - bw / 4, y(wmax)), QPointF(x + bw / 4, y(wmax)))
                p.drawLine(QPointF(x - bw / 4, y(wmin)), QPointF(x + bw / 4, y(wmin)))
                # 箱体
                rect = QRectF(x - bw / 2, y(q3), bw, y(q1) - y(q3))
                p.setBrush(QColor(color).lighter(120))
                p.drawRect(rect)
                # 中位线
                p.drawLine(QPointF(x - bw / 2, y(med)), QPointF(x + bw / 2, y(med)))
        p.end()

    def mouseMoveEvent(self, event) -> None:
        plot = self._plot_rect()
        n = len(self._categories)
        slot_w = plot.width() / n if n else 0
        if n and plot.contains(event.position()):
            ci = int((event.position().x() - plot.left()) / slot_w)
            ci = max(0, min(n - 1, ci))
            cat = self._categories[ci]
            boxes = self._boxes[cat]
            cx = plot.left() + ci * slot_w + slot_w / 2
            group_w = slot_w * 0.6
            best, best_d = 0, 1e9
            for bi in range(len(boxes)):
                x = cx + (bi - (len(boxes) - 1) / 2) * (group_w / len(boxes))
                d = abs(event.position().x() - x)
                if d < best_d:
                    best, best_d = bi, d
            self._hover = (ci, best)
            q1, med, q3, wmin, wmax, color = boxes[best]
            self._show_tip(int(event.position().x()), int(event.position().y()),
                           f"<b style='color:#FFF'>{cat}</b><br/>"
                           f"最小 {_fmt(wmin)} · Q1 {_fmt(q1)} · 中位 {_fmt(med)}<br/>"
                           f"Q3 {_fmt(q3)} · 最大 {_fmt(wmax)}")
        else:
            self._hover = None
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)


class FluentTimeSeriesChart(_ChartBase):
    """Fluent 时间序列折线图：x 轴为日期。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._series: list[tuple[str, list[datetime], list[float], QColor]] = []
        self._hover_idx = -1

    def add_series(self, name: str, dates, values,
                   color: str = "") -> "FluentTimeSeriesChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._series) % len(SERIES_COLORS)])
        dts = [datetime.combine(d, datetime.min.time()) if isinstance(d, date)
               else d for d in dates]
        self._series.append((name, dts, [float(v) for v in values], c))
        self.update()
        return self

    def _bounds(self) -> tuple:
        lo_t, hi_t = None, None
        lo_v, hi_v = 0.0, 1.0
        for _, dts, vals, _ in self._series:
            if dts:
                lo_t = dts[0] if lo_t is None else min(lo_t, dts[0])
                hi_t = dts[-1] if hi_t is None else max(hi_t, dts[-1])
            if vals:
                lo_v = min(lo_v, min(vals))
                hi_v = max(hi_v, max(vals))
        if lo_t is None or hi_t == lo_t:
            hi_t = (lo_t or datetime.now()) + 1
        pad = (hi_v - lo_v) * 0.08
        return lo_t, hi_t, lo_v - pad, hi_v + pad

    def _x(self, plot: QRectF, t: datetime, lo_t, hi_t) -> float:
        span = (hi_t - lo_t).total_seconds() or 1
        return plot.left() + (t - lo_t).total_seconds() / span * plot.width()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        if not self._series:
            p.setFont(self._tick_font())
            p.setPen(_LABEL)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            p.end()
            return
        plot = self._plot_rect()
        lo_t, hi_t, lo_v, hi_v = self._bounds()
        self._draw_y_grid(p, plot, lo_v, hi_v)

        # x 轴日期刻度（约 6 个）
        span = (hi_t - lo_t).total_seconds()
        fm = self.fontMetrics()
        p.setFont(self._tick_font())
        ticks = 6
        for i in range(ticks + 1):
            t = lo_t + (hi_t - lo_t) * i / ticks
            x = self._x(plot, t, lo_t, hi_t)
            p.setPen(QPen(_GRID, 1))
            p.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            p.setPen(_LABEL)
            p.drawText(QRectF(x - 40, plot.bottom() + 4, 80, 18),
                       Qt.AlignmentFlag.AlignHCenter, t.strftime("%m-%d"))
        _ = span

        for name, dts, vals, color in self._series:
            pts = [QPointF(self._x(plot, t, lo_t, hi_t),
                           plot.bottom() - (v - lo_v) / (hi_v - lo_v) * plot.height())
                   for t, v in zip(dts, vals)]
            pen = QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            for i in range(1, len(pts)):
                p.drawLine(pts[i - 1], pts[i])

        # 悬停
        if self._hover_idx >= 0:
            for name, dts, vals, color in self._series:
                if self._hover_idx < len(vals):
                    t, v = dts[self._hover_idx], vals[self._hover_idx]
                    x = self._x(plot, t, lo_t, hi_t)
                    y = plot.bottom() - (v - lo_v) / (hi_v - lo_v) * plot.height()
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(color)
                    p.drawEllipse(QPointF(x, y), 4, 4)
        p.end()

    def mouseMoveEvent(self, event) -> None:
        plot = self._plot_rect()
        lo_t, hi_t, lo_v, hi_v = self._bounds()
        series = self._series
        n = max((len(dts) for _, dts, _, _ in series), default=0)
        if plot.contains(event.position()) and n > 1 and series:
            idx = int(round((event.position().x() - plot.left())
                            / plot.width() * (n - 1)))
            idx = max(0, min(n - 1, idx))
            self._hover_idx = idx
            dts = series[0][1]
            lines = [f"<b style='color:#FFF'>{dts[idx].strftime('%Y-%m-%d')}</b>"]
            for name, _, vals, color in series:
                v = vals[idx] if idx < len(vals) else 0.0
                lines.append(f"<span style='color:{color.name()}'>{name}</span>: "
                             f"{_fmt(v)}")
            self._show_tip(int(event.position().x()), int(event.position().y()),
                           "<br/>".join(lines))
        else:
            self._hover_idx = -1
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)
