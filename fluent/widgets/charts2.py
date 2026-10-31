"""Fluent 高级图表：散点 / 热力图 / 雷达图 / 漏斗图 / 甘特图。

复用 charts.py 的基础设施（标题、坐标区、字体自适应、悬停提示）。
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QLinearGradient,
                           QPainter, QPainterPath, QPen, QPolygonF)

from ..theme import palette as P
from .charts import SERIES_COLORS, _ChartBase, _fmt

_GRID = QColor("#3A3A3A")
_LABEL = QColor("#9D9D9D")


def _grad_color(t: float) -> QColor:
    """蓝→青→黄 热力色标。"""
    t = max(0.0, min(1.0, t))
    stops = [(0.0, (0x0B, 0x2E, 0x4A)), (0.4, (0x00, 0x80, 0xE0)),
             (0.7, (0x00, 0xC8, 0xC8)), (0.9, (0xFF, 0xD6, 0x00)),
             (1.0, (0xFF, 0x6F, 0x00))]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0)
            return QColor(round(c0[0] + (c1[0] - c0[0]) * k),
                          round(c0[1] + (c1[1] - c0[1]) * k),
                          round(c0[2] + (c1[2] - c0[2]) * k))
    return QColor(*stops[-1][1])


class FluentScatterChart(_ChartBase):
    """Fluent 散点图：多系列二维点阵，悬停高亮最近点。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._series: list[tuple[str, list, QColor]] = []
        self._x_labels: list[str] = []
        self._hover: tuple[int, int] | None = None

    def add_series(self, name: str, points, color: str = "") -> "FluentScatterChart":
        """points: [(x, y), ...]"""
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._series) % len(SERIES_COLORS)])
        self._series.append((name, [(float(x), float(y)) for x, y in points], c))
        self.update()
        return self

    def set_x_labels(self, labels) -> "FluentScatterChart":
        self._x_labels = list(labels)
        return self

    def _bounds(self) -> tuple[float, float, float, float]:
        xs = [x for _, pts, _ in self._series for x, _ in pts]
        ys = [y for _, pts, _ in self._series for _, y in pts]
        if not xs:
            return 0, 1, 0, 1
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if x1 == x0:
            x1 = x0 + 1
        if y1 == y0:
            y1 = y0 + 1
        padx, pady = (x1 - x0) * 0.1, (y1 - y0) * 0.1
        return x0 - padx, x1 + padx, y0 - pady, y1 + pady

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
        x0, x1, y0, y1 = self._bounds()
        self._draw_y_grid(p, plot, y0, y1)
        self._draw_x_labels(p, plot, self._x_labels)

        def px(x: float) -> float:
            return plot.left() + (x - x0) / (x1 - x0) * plot.width()

        def py(y: float) -> float:
            return plot.bottom() - (y - y0) / (y1 - y0) * plot.height()

        for si, (name, pts, color) in enumerate(self._series):
            for pi, (x, y) in enumerate(pts):
                hover = self._hover == (si, pi)
                c = color.lighter(150) if hover else color
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(c)
                r = 6 if hover else 4
                p.drawEllipse(QPointF(px(x), py(y)), r, r)
        p.end()

    def mouseMoveEvent(self, event) -> None:
        plot = self._plot_rect()
        x0, x1, y0, y1 = self._bounds()

        def px(x): return plot.left() + (x - x0) / (x1 - x0) * plot.width()
        def py(y): return plot.bottom() - (y - y0) / (y1 - y0) * plot.height()

        best, best_d = None, 14.0
        for si, (name, pts, color) in enumerate(self._series):
            for pi, (x, y) in enumerate(pts):
                d = math.hypot(event.position().x() - px(x),
                               event.position().y() - py(y))
                if d < best_d:
                    best, best_d = (si, pi), d
        self._hover = best
        if best is not None:
            si, pi = best
            name, pts, color = self._series[si]
            x, y = pts[pi]
            self._show_tip(int(event.position().x()), int(event.position().y()),
                           f"<span style='color:{color.name()}'>{name}</span><br/>"
                           f"({_fmt(x)}, {_fmt(y)})")
        else:
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)


class FluentHeatmapChart(_ChartBase):
    """Fluent 热力图：二维矩阵着色，带行列标签与色标。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._matrix: list[list[float]] = []
        self._row_labels: list[str] = []
        self._col_labels: list[str] = []
        self._hover: tuple[int, int] | None = None

    def set_data(self, matrix, row_labels=None, col_labels=None) -> "FluentHeatmapChart":
        self._matrix = [[float(v) for v in row] for row in matrix]
        self._row_labels = list(row_labels) if row_labels else \
            [str(i + 1) for i in range(len(matrix))]
        self._col_labels = list(col_labels) if col_labels else \
            [str(i + 1) for i in range(len(matrix[0]) if matrix else 0)]
        self.update()
        return self

    def _range(self) -> tuple[float, float]:
        vals = [v for row in self._matrix for v in row]
        if not vals:
            return 0.0, 1.0
        return min(vals), max(vals)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        if not self._matrix:
            p.setFont(self._tick_font())
            p.setPen(_LABEL)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            p.end()
            return
        fm = QFontMetrics(self._tick_font())
        row_w = fm.horizontalAdvance(max(self._row_labels, key=len)) + 12
        rows, cols = len(self._matrix), len(self._matrix[0])
        area = QRectF(self._plot_rect())
        area.setLeft(area.left() + row_w)
        area.setBottom(area.bottom() - fm.height() - 8)
        cw = area.width() / cols
        ch = area.height() / rows
        lo, hi = self._range()
        span = max(1e-9, hi - lo)

        # 色块
        for r in range(rows):
            for c in range(cols):
                t = (self._matrix[r][c] - lo) / span
                rect = QRectF(area.left() + c * cw, area.top() + r * ch, cw, ch)
                p.setPen(QPen(QColor("#1B1B1B"), 1))
                p.setBrush(_grad_color(t))
                p.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))

        # 标签
        p.setFont(self._tick_font())
        for r, lbl in enumerate(self._row_labels):
            p.setPen(_LABEL)
            p.drawText(QRectF(area.left() - row_w + 2, area.top() + r * ch,
                              row_w - 6, ch),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       lbl)
        for c, lbl in enumerate(self._col_labels):
            p.setPen(_LABEL)
            p.drawText(QRectF(area.left() + c * cw, area.bottom() + 2, cw, fm.height()),
                       Qt.AlignmentFlag.AlignCenter, lbl)

        # 色标
        legend = QRectF(area.right() - 120, area.bottom() + 4, 120, 8)
        lg = QLinearGradient(legend.left(), 0, legend.right(), 0)
        for i in range(7):
            lg.setColorAt(i / 6, _grad_color(i / 6))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(lg)
        p.drawRoundedRect(legend, 3, 3)
        p.setPen(_LABEL)
        p.drawText(QRectF(legend.left(), legend.bottom() + 1, legend.width(), 14),
                   Qt.AlignmentFlag.AlignCenter, f"{_fmt(lo)}  ~  {_fmt(hi)}")
        p.end()

    def mouseMoveEvent(self, event) -> None:
        fm = QFontMetrics(self._tick_font())
        row_w = fm.horizontalAdvance(max(self._row_labels, key=len)) + 12
        area = QRectF(self._plot_rect())
        area.setLeft(area.left() + row_w)
        area.setBottom(area.bottom() - fm.height() - 8)
        if area.contains(event.position()) and self._matrix:
            cols = len(self._matrix[0])
            cw = area.width() / cols
            ch = area.height() / len(self._matrix)
            c = int((event.position().x() - area.left()) / cw)
            r = int((event.position().y() - area.top()) / ch)
            if 0 <= r < len(self._matrix) and 0 <= c < cols:
                self._hover = (r, c)
                v = self._matrix[r][c]
                self._show_tip(int(event.position().x()),
                               int(event.position().y()),
                               f"<b style='color:#FFF'>{self._row_labels[r]}</b> · "
                               f"{self._col_labels[c]}<br/>值: {_fmt(v)}")
            else:
                self._hover = None
                self._hide_tip()
        else:
            self._hover = None
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)


class FluentRadarChart(_ChartBase):
    """Fluent 雷达图：多轴多边形，支持多系列。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._categories: list[str] = []
        self._series: list[tuple[str, list[float], QColor]] = []
        self._max = 1.0

    def set_categories(self, categories) -> "FluentRadarChart":
        self._categories = list(categories)
        return self

    def add_series(self, name: str, values, color: str = "") -> "FluentRadarChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._series) % len(SERIES_COLORS)])
        vals = [float(v) for v in values]
        self._series.append((name, vals, c))
        self._max = max(self._max, max(vals, default=0))
        self.update()
        return self

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        n = len(self._categories)
        if not n or not self._series:
            p.setFont(self._tick_font())
            p.setPen(_LABEL)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            p.end()
            return
        cx = self.width() / 2
        r_max = min(self.width(), self.height()) * 0.32
        cy = self.height() * 0.46

        def pt(i: int, f: float) -> QPointF:
            ang = math.radians(-90 + i * 360 / n)
            return QPointF(cx + r_max * f * math.cos(ang),
                           cy + r_max * f * math.sin(ang))

        # 同心网格 + 轴线
        p.setPen(QPen(_GRID, 1))
        for k in range(1, 5):
            poly = QPolygonF([pt(i, k / 4) for i in range(n)])
            p.drawPolygon(poly)
        for i in range(n):
            p.drawLine(QPointF(cx, cy), pt(i, 1.0))

        # 分类标签
        f = self._tick_font()
        p.setFont(f)
        fm = QFontMetrics(f)
        for i, label in enumerate(self._categories):
            p.setPen(_LABEL)
            q = pt(i, 1.12)
            p.drawText(QRectF(q.x() - 50, q.y() - 10, 100, 20),
                       Qt.AlignmentFlag.AlignCenter, label)

        # 系列
        for name, vals, color in self._series:
            poly = QPolygonF([pt(i, min(1.0, vals[i] / self._max))
                              for i in range(n)])
            path = QPainterPath(poly.first())
            for q in poly:
                path.lineTo(q)
            path.closeSubpath()
            fill = QColor(color)
            fill.setAlpha(60)
            p.fillPath(path, fill)
            p.setPen(QPen(color, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolygon(poly)

        # 图例
        p.setFont(self._tick_font())
        fm2 = QFontMetrics(self._tick_font())
        x = cx
        total = sum(fm2.horizontalAdvance(name) + 24 for name, _, _ in self._series)
        x = cx - total / 2
        y = self.height() - 18
        for name, _, color in self._series:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(QRectF(x, y + 2, 10, 10), 3, 3)
            p.setPen(_LABEL)
            p.drawText(QRectF(x + 14, y, 200, 16), Qt.AlignmentFlag.AlignLeft, name)
            x += fm2.horizontalAdvance(name) + 26
        _ = fm
        p.end()


class FluentFunnelChart(_ChartBase):
    """Fluent 漏斗图：横向递减色条。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._stages: list[tuple[str, float, QColor]] = []
        self._hover = -1

    def add_stage(self, name: str, value: float, color: str = "") -> "FluentFunnelChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._stages) % len(SERIES_COLORS)])
        self._stages.append((name, float(value), c))
        self.update()
        return self

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        if not self._stages:
            p.setFont(self._tick_font())
            p.setPen(_LABEL)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            p.end()
            return
        top = 40
        bottom = self.height() - 8
        chart_h = bottom - top
        row_h = chart_h / len(self._stages)
        fm = QFontMetrics(self._tick_font())
        left_w = fm.horizontalAdvance(max((s[0] for s in self._stages), key=len)) + 16
        max_v = max(v for _, v, _ in self._stages)

        for i, (name, value, color) in enumerate(self._stages):
            frac = value / max_v
            bar_w = (self.width() - left_w - 20) * frac
            x = left_w + (self.width() - left_w - bar_w) / 2
            rect = QRectF(x, top + i * row_h + 3, bar_w, row_h - 6)
            c = color.lighter(150) if i == self._hover else color
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(rect, 4, 4)

            p.setPen(_LABEL)
            p.drawText(QRectF(0, rect.top(), left_w - 10, rect.height()),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       name)
            pct = value / max_v * 100
            p.drawText(QRectF(rect.right() + 8, rect.top(), 90, rect.height()),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       f"{_fmt(value)} ({pct:.0f}%)")
        p.end()

    def mouseMoveEvent(self, event) -> None:
        top, bottom = 40, self.height() - 8
        row_h = (bottom - top) / len(self._stages) if self._stages else 0
        if self._stages and top <= event.position().y() < bottom:
            idx = int((event.position().y() - top) / row_h)
            if 0 <= idx < len(self._stages):
                self._hover = idx
                name, value, color = self._stages[idx]
                self._show_tip(int(event.position().x()), int(event.position().y()),
                               f"<span style='color:{color.name()}'>{name}</span>: "
                               f"{_fmt(value)}")
            else:
                self._hover = -1
                self._hide_tip()
        else:
            self._hover = -1
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)


class FluentGanttChart(_ChartBase):
    """Fluent 甘特图：任务条时间轴。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._tasks: list[tuple[str, int, int, QColor]] = []
        self._hover = -1

    def add_task(self, name: str, start_day: int, days: int,
                 color: str = "") -> "FluentGanttChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._tasks) % len(SERIES_COLORS)])
        self._tasks.append((name, int(start_day), max(1, int(days)), c))
        self.update()
        return self

    def clear_tasks(self) -> None:
        self._tasks.clear()
        self.update()

    def _total_days(self) -> int:
        return max((s + d for _, s, d, _ in self._tasks), default=0)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        if not self._tasks:
            p.setFont(self._tick_font())
            p.setPen(_LABEL)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            p.end()
            return
        total = self._total_days()
        fm = QFontMetrics(self._tick_font())
        label_w = fm.horizontalAdvance(max((t[0] for t in self._tasks), key=len)) + 14
        top = 40
        bottom = self.height() - 14
        row_h = (bottom - top) / len(self._tasks)
        chart_left = label_w + 8
        track_w = self.width() - chart_left - 12
        day_w = track_w / total if total else 1

        # 纵向网格（每天）
        p.setFont(self._tick_font())
        for d in range(total + 1):
            x = chart_left + d * day_w
            p.setPen(QPen(_GRID, 1))
            p.drawLine(QPointF(x, top), QPointF(x, bottom))
            if d % 5 == 0 or d == total:
                p.setPen(_LABEL)
                p.drawText(QRectF(x - 10, top - 16, 20, 14),
                           Qt.AlignmentFlag.AlignCenter, str(d))

        # 任务条
        for i, (name, start, days, color) in enumerate(self._tasks):
            y = top + i * row_h
            p.setPen(_LABEL)
            p.drawText(QRectF(0, y, label_w - 8, row_h),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       name)
            rect = QRectF(chart_left + start * day_w, y + row_h * 0.2,
                          days * day_w, row_h * 0.6)
            c = color.lighter(150) if i == self._hover else color
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(rect, 3, 3)
        p.end()

    def mouseMoveEvent(self, event) -> None:
        fm = QFontMetrics(self._tick_font())
        label_w = fm.horizontalAdvance(max((t[0] for t in self._tasks), key=len)) + 14
        top, bottom = 40, self.height() - 14
        row_h = (bottom - top) / len(self._tasks) if self._tasks else 0
        if self._tasks and top <= event.position().y() < bottom and \
                event.position().x() > label_w:
            idx = int((event.position().y() - top) / row_h)
            if 0 <= idx < len(self._tasks):
                self._hover = idx
                name, start, days, color = self._tasks[idx]
                self._show_tip(int(event.position().x()), int(event.position().y()),
                               f"<span style='color:{color.name()}'>{name}</span><br/>"
                               f"第 {start} 天起，持续 {days} 天")
            else:
                self._hover = -1
                self._hide_tip()
        else:
            self._hover = -1
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)
