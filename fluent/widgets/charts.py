"""Fluent 统计图表（纯 QPainter 自绘，深色主题，零额外依赖）。

提供：折线图 / 面积图 / 柱状图 / 饼图（环形）/ 仪表盘。
全部支持悬停查看数值提示，配色沿用 Fluent 深色调色板。
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QLinearGradient,
                           QPainter, QPainterPath, QPen, QPolygonF)
from PySide6.QtWidgets import QToolTip, QWidget

from ..theme import palette as P

# 内置系列配色（Fluent 明快色系，深色下对比良好）
SERIES_COLORS = [
    "#4CC2FF", "#00B7C3", "#FFB900", "#7A5CFF",
    "#FF6F00", "#E3008C", "#7CBA5A", "#C2E0F4",
]

_GRID = QColor("#3A3A3A")
_LABEL = QColor("#9D9D9D")


def _nice_ticks(vmin: float, vmax: float, count: int = 5) -> list[float]:
    """生成整数化的坐标刻度。"""
    if vmax <= vmin:
        vmin, vmax = 0.0, 1.0
    span = vmax - vmin
    step_raw = span / count
    mag = 10 ** math.floor(math.log10(step_raw))
    norm = step_raw / mag
    if norm < 1.5:
        step = 1
    elif norm < 3:
        step = 2
    elif norm < 7:
        step = 5
    else:
        step = 10
    step *= mag
    start = math.ceil(vmin / step) * step
    ticks = []
    v = start
    while v <= vmax + step * 1e-9:
        ticks.append(v)
        v += step
    return ticks


def _fmt(v: float) -> str:
    if abs(v) >= 1000 or abs(v) < 0.01:
        return f"{v:g}"
    if v == int(v):
        return str(int(v))
    return f"{v:.1f}"


class _ChartBase(QWidget):
    """图表公共基类：标题、坐标区、悬停提示。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(parent)
        self._title = title
        self.setMouseTracking(True)
        self.setMinimumHeight(200)
        self.setMinimumWidth(240)
        self._hover_idx = -1

    # ---- 随 DPI 自适应的字体（使用控件默认字体派生，自动缩放） ----
    def _title_font(self) -> QFont:
        f = QFont(self.font())
        f.setBold(True)
        f.setPointSizeF(max(9.0, f.pointSizeF() + 1.5))
        return f

    def _tick_font(self) -> QFont:
        f = QFont(self.font())
        f.setPointSizeF(max(7.0, f.pointSizeF() - 0.5))
        return f

    # ---- 坐标区（边距随字体尺寸自适应） ----
    def _plot_rect(self) -> QRectF:
        r = self.rect()
        fm = QFontMetrics(self._tick_font())
        left = fm.horizontalAdvance("-8888.8") + 14
        right = 12
        top = 34
        bottom = fm.height() + 22
        w = r.width() - left - right
        h = r.height() - top - bottom
        return QRectF(r.left() + left, r.top() + top, max(40, w), max(40, h))

    # ---- 标题 ----
    def _draw_title(self, p: QPainter) -> None:
        if self._title:
            p.setFont(self._title_font())
            p.setPen(QColor(P.text_primary))
            p.drawText(QRectF(0, 6, self.width(), 22),
                       Qt.AlignmentFlag.AlignHCenter, self._title)

    def _draw_y_grid(self, p: QPainter, plot: QRectF, lo: float, hi: float) -> list[float]:
        ticks = _nice_ticks(lo, hi)
        f = self._tick_font()
        p.setFont(f)
        fm = QFontMetrics(f)
        for t in ticks:
            y = plot.bottom() - (t - lo) / max(1e-9, hi - lo) * plot.height()
            p.setPen(QPen(_GRID, 1))
            p.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            p.setPen(_LABEL)
            p.drawText(QRectF(0, y - 9, plot.left() - 8, 18),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       _fmt(t))
        _ = fm
        return ticks

    def _draw_x_labels(self, p: QPainter, plot: QRectF, labels: list[str]) -> None:
        if not labels:
            return
        n = len(labels)
        p.setFont(self._tick_font())
        for i, text in enumerate(labels):
            x = plot.left() + (i + 0.5) / n * plot.width()
            p.setPen(_LABEL)
            p.drawText(QRectF(x - 44, plot.bottom() + 6, 88, 18),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                       text)

    def _x_at(self, plot: QRectF, index: int, n: int) -> float:
        if n <= 1:
            return plot.center().x()
        return plot.left() + index / (n - 1) * plot.width()

    # ---- 悬停提示 ----
    def _show_tip(self, x: int, y: int, html: str) -> None:
        QToolTip.showText(self.mapToGlobal(QPoint(x + 8, y + 8)), html, self)

    def _hide_tip(self) -> None:
        QToolTip.hideText()

    def leaveEvent(self, event) -> None:
        self._hover_idx = -1
        self._hide_tip()
        self.update()
        super().leaveEvent(event)


class FluentLineChart(_ChartBase):
    """Fluent 折线图，支持多系列、可选填充、悬停查看数值。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._series: list[tuple[str, list[float], QColor]] = []
        self._x_labels: list[str] = []
        self._fill = False
        self._show_legend = True

    def add_series(self, name: str, values, color: str = "") -> "FluentLineChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._series) % len(SERIES_COLORS)])
        self._series.append((name, [float(v) for v in values], c))
        self.update()
        return self

    def set_x_labels(self, labels) -> "FluentLineChart":
        self._x_labels = list(labels)
        self.update()
        return self

    def set_fill(self, on: bool) -> "FluentLineChart":
        self._fill = on
        self.update()
        return self

    def set_show_legend(self, on: bool) -> "FluentLineChart":
        self._show_legend = on
        self.update()
        return self

    def clear_series(self) -> None:
        self._series.clear()
        self.update()

    def _bounds(self) -> tuple[float, float]:
        vals = [v for _, s, _ in self._series for v in s]
        if not vals:
            return 0.0, 1.0
        lo, hi = min(vals), max(vals)
        if hi == lo:
            hi = lo + 1
        pad = (hi - lo) * 0.08
        return lo - pad, hi + pad

    def _n(self) -> int:
        return max((len(s) for _, s, _ in self._series), default=0)

    def _draw_legend(self, p: QPainter, plot: QRectF) -> None:
        if not self._show_legend or not self._series:
            return
        f = self._tick_font()
        p.setFont(f)
        fm = QFontMetrics(f)
        x = plot.right()
        total = 0
        for name, _, c in self._series:
            w = 12 + 4 + fm.horizontalAdvance(name) + 12
            total += w
        x = plot.right() - total
        y = 12
        for name, _, c in self._series:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(QRectF(x, y + 4, 10, 10), 3, 3)
            p.setPen(_LABEL)
            p.drawText(QRectF(x + 14, y, 200, 18), Qt.AlignmentFlag.AlignLeft, name)
            x += 14 + fm.horizontalAdvance(name) + 14

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        if not self._series:
            self._draw_empty(p)
            p.end()
            return
        plot = self._plot_rect()
        lo, hi = self._bounds()
        self._draw_y_grid(p, plot, lo, hi)
        self._draw_x_labels(p, plot, self._x_labels)
        self._draw_legend(p, plot)
        n = self._n()

        for name, values, color in self._series:
            pts = QPolygonF()
            for i in range(n):
                x = self._x_at(plot, i, n)
                v = values[i] if i < len(values) else 0.0
                y = plot.bottom() - (v - lo) / (hi - lo) * plot.height()
                pts.append(QPointF(x, y))
            if self._fill and pts.size() >= 2:
                path = QPainterPath(pts.first())
                for pt in pts:
                    path.lineTo(pt)
                path.lineTo(pts.last().x(), plot.bottom())
                path.lineTo(pts.first().x(), plot.bottom())
                path.closeSubpath()
                grad = QLinearGradient(plot.topLeft(), plot.bottomLeft())
                c = QColor(color)
                c.setAlpha(90)
                c2 = QColor(color)
                c2.setAlpha(0)
                grad.setColorAt(0.0, c)
                grad.setColorAt(1.0, c2)
                p.fillPath(path, grad)
            pen = QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                       Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolyline(pts)

        # 悬停指示
        if 0 <= self._hover_idx < n:
            x = self._x_at(plot, self._hover_idx, n)
            p.setPen(QPen(QColor(255, 255, 255, 60), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            for name, values, color in self._series:
                v = values[self._hover_idx] if self._hover_idx < len(values) else 0.0
                y = plot.bottom() - (v - lo) / (hi - lo) * plot.height()
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(color)
                p.drawEllipse(QPointF(x, y), 4, 4)
        p.end()

    def _draw_empty(self, p: QPainter) -> None:
        p.setFont(self._tick_font())
        p.setPen(_LABEL)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")

    def mouseMoveEvent(self, event) -> None:
        plot = self._plot_rect()
        n = self._n()
        if plot.contains(event.position()) and n > 1 and self._series:
            idx = int(round((event.position().x() - plot.left())
                            / plot.width() * (n - 1)))
            idx = max(0, min(n - 1, idx))
            self._hover_idx = idx
            label = self._x_labels[idx] if idx < len(self._x_labels) else f"#{idx + 1}"
            lines = [f"<b style='color:#FFF'>{label}</b>"]
            for name, values, color in self._series:
                v = values[idx] if idx < len(values) else 0.0
                lines.append(f"<span style='color:{color.name()}'>{name}</span>: "
                             f"{_fmt(v)}")
            self._show_tip(int(event.position().x()), int(event.position().y()),
                           "<br/>".join(lines))
        else:
            self._hover_idx = -1
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)


class FluentAreaChart(_ChartBase):
    """Fluent 面积图：渐变填充，支持堆叠（stacked）。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._series: list[tuple[str, list[float], QColor]] = []
        self._x_labels: list[str] = []
        self._stacked = False

    def add_series(self, name: str, values, color: str = "") -> "FluentAreaChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._series) % len(SERIES_COLORS)])
        self._series.append((name, [float(v) for v in values], c))
        self.update()
        return self

    def set_x_labels(self, labels) -> "FluentAreaChart":
        self._x_labels = list(labels)
        self.update()
        return self

    def set_stacked(self, on: bool) -> "FluentAreaChart":
        self._stacked = on
        self.update()
        return self

    def _bounds(self) -> tuple[float, float]:
        n = max((len(s) for _, s, _ in self._series), default=0)
        if self._stacked:
            totals = [0.0] * n
            for _, s, _ in self._series:
                for i in range(n):
                    totals[i] += s[i] if i < len(s) else 0.0
            hi = max(totals, default=1.0)
            return 0.0, hi * 1.1
        vals = [v for _, s, _ in self._series for v in s]
        if not vals:
            return 0.0, 1.0
        return 0.0, max(vals) * 1.1

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
        lo, hi = self._bounds()
        self._draw_y_grid(p, plot, lo, hi)
        self._draw_x_labels(p, plot, self._x_labels)
        n = max((len(s) for _, s, _ in self._series), default=0)

        prev_cum: list[float] = [0.0] * n
        for name, values, color in self._series:
            cum = [0.0] * n
            for i in range(n):
                base = prev_cum[i] if self._stacked else 0.0
                cum[i] = base + (values[i] if i < len(values) else 0.0)
            pts = QPolygonF()
            for i in range(n):
                x = self._x_at(plot, i, n)
                y = plot.bottom() - (cum[i] - lo) / (hi - lo) * plot.height()
                pts.append(QPointF(x, y))
            path = QPainterPath(pts.first())
            for pt in pts:
                path.lineTo(pt)
            if self._stacked:
                base_y = [plot.bottom() - (prev_cum[i] - lo) / (hi - lo) * plot.height()
                          for i in range(n)]
                path.lineTo(pts.last().x(), base_y[-1])
                for i in range(n - 1, -1, -1):
                    x = self._x_at(plot, i, n)
                    path.lineTo(QPointF(x, base_y[i]))
            else:
                path.lineTo(pts.last().x(), plot.bottom())
                path.lineTo(pts.first().x(), plot.bottom())
            path.closeSubpath()
            grad = QLinearGradient(plot.topLeft(), plot.bottomLeft())
            c1 = QColor(color)
            c1.setAlpha(130)
            c2 = QColor(color)
            c2.setAlpha(20)
            grad.setColorAt(0.0, c1)
            grad.setColorAt(1.0, c2)
            p.fillPath(path, grad)
            pen = QPen(color, 2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolyline(pts)
            prev_cum = cum
        p.end()


class FluentBarChart(_ChartBase):
    """Fluent 柱状图：分组柱或堆叠柱，圆角柱身。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._series: list[tuple[str, list[float], QColor]] = []
        self._categories: list[str] = []
        self._stacked = False

    def add_series(self, name: str, values, color: str = "") -> "FluentBarChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._series) % len(SERIES_COLORS)])
        self._series.append((name, [float(v) for v in values], c))
        self.update()
        return self

    def set_categories(self, categories) -> "FluentBarChart":
        self._categories = list(categories)
        self.update()
        return self

    def set_stacked(self, on: bool) -> "FluentBarChart":
        self._stacked = on
        self.update()
        return self

    def _bounds(self) -> tuple[float, float]:
        n = max((len(s) for _, s, _ in self._series), default=0)
        if self._stacked:
            totals = [0.0] * n
            for _, s, _ in self._series:
                for i in range(n):
                    totals[i] += s[i] if i < len(s) else 0.0
            return 0.0, max(totals, default=1.0) * 1.12
        vals = [v for _, s, _ in self._series for v in s]
        return 0.0, (max(vals, default=1.0) * 1.12)

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
        lo, hi = self._bounds()
        self._draw_y_grid(p, plot, lo, hi)
        n = max((len(s) for _, s, _ in self._series), default=0)
        if n == 0:
            p.end()
            return
        labels = self._categories or [str(i + 1) for i in range(n)]
        self._draw_x_labels(p, plot, labels)

        slot_w = plot.width() / n
        if self._stacked:
            # 堆叠
            prev_tot = [0.0] * n
            for name, values, color in self._series:
                for i in range(n):
                    v = values[i] if i < len(values) else 0.0
                    base = prev_tot[i]
                    top = base + v
                    y0 = plot.bottom() - base / (hi - lo) * plot.height()
                    y1 = plot.bottom() - top / (hi - lo) * plot.height()
                    x = plot.left() + i * slot_w
                    self._bar(p, QRectF(x + slot_w * 0.15, y1,
                                        slot_w * 0.7, y0 - y1), color,
                              i == self._hover_idx)
                    prev_tot[i] = top
        else:
            group_w = slot_w * 0.72
            bar_w = group_w / len(self._series)
            for gi, (name, values, color) in enumerate(self._series):
                for i in range(n):
                    v = values[i] if i < len(values) else 0.0
                    y = plot.bottom() - v / (hi - lo) * plot.height()
                    x = plot.left() + i * slot_w + slot_w * 0.14 + gi * bar_w
                    self._bar(p, QRectF(x, y, bar_w * 0.8, plot.bottom() - y),
                              color, i == self._hover_idx and gi == self._hover_series)
        p.end()

    def _bar(self, p: QPainter, rect: QRectF, color: QColor, hover: bool) -> None:
        c = color.lighter(140) if hover else color
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        r = min(4.0, rect.width() / 2)
        p.drawRoundedRect(rect, r, r)

    _hover_series = 0

    def mouseMoveEvent(self, event) -> None:
        plot = self._plot_rect()
        n = max((len(s) for _, s, _ in self._series), default=0)
        if plot.contains(event.position()) and n and self._series:
            slot_w = plot.width() / n
            idx = int((event.position().x() - plot.left()) / slot_w)
            idx = max(0, min(n - 1, idx))
            self._hover_idx = idx
            label = (self._categories[idx] if idx < len(self._categories)
                     else f"#{idx + 1}")
            lines = [f"<b style='color:#FFF'>{label}</b>"]
            total = 0.0
            for name, values, color in self._series:
                v = values[idx] if idx < len(values) else 0.0
                total += v
                lines.append(f"<span style='color:{color.name()}'>{name}</span>: "
                             f"{_fmt(v)}")
            if self._stacked:
                lines.append(f"合计: {_fmt(total)}")
            self._show_tip(int(event.position().x()), int(event.position().y()),
                           "<br/>".join(lines))
        else:
            self._hover_idx = -1
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)


class FluentPieChart(_ChartBase):
    """Fluent 环形饼图：悬停高亮扇区并提示。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._segments: list[tuple[str, float, QColor]] = []
        self._thickness = 26.0
        self._hover_seg = -1

    def add_segment(self, name: str, value: float, color: str = "") -> "FluentPieChart":
        c = QColor(color) if color else QColor(
            SERIES_COLORS[len(self._segments) % len(SERIES_COLORS)])
        self._segments.append((name, float(value), c))
        self.update()
        return self

    def set_thickness(self, t: float) -> "FluentPieChart":
        self._thickness = t
        self.update()
        return self

    def clear_segments(self) -> None:
        self._segments.clear()
        self.update()

    def _total(self) -> float:
        return sum(v for _, v, _ in self._segments)

    def _donut_rect(self) -> QRectF:
        size = min(self.width() - 20, self.height() - 60)
        return QRectF((self.width() - size) / 2, 40, size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)
        total = self._total()
        if not self._segments or total <= 0:
            p.setFont(self._tick_font())
            p.setPen(_LABEL)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")
            p.end()
            return
        rect = self._donut_rect()
        pen_w = self._thickness
        start = 90.0  # 从顶部顺时针

        # 轨道
        track = QPen(QColor(P.fill_layer), pen_w,
                     Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
        p.setPen(track)
        p.drawArc(rect, 0, 360 * 16)

        for i, (name, value, color) in enumerate(self._segments):
            span = -360.0 * value / total
            c = color.lighter(150) if i == self._hover_seg else color
            seg = QPen(c, pen_w + (6 if i == self._hover_seg else 0),
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
            p.setPen(seg)
            p.drawArc(rect, int(start * 16), int(span * 16))
            start += span

        # 中心文字
        p.setFont(self._title_font())
        p.setPen(QColor(P.text_primary))
        p.drawText(rect.adjusted(0, 0, 0, -14),
                   Qt.AlignmentFlag.AlignCenter, _fmt(total))
        p.setFont(self._tick_font())
        p.setPen(_LABEL)
        p.drawText(rect.adjusted(0, 16, 0, 0),
                   Qt.AlignmentFlag.AlignCenter, "总计")

        # 图例
        f = self._tick_font()
        p.setFont(f)
        fm = QFontMetrics(f)
        y = rect.bottom() + 10
        x = self.width() / 2
        items = [(f"{name} {value / total * 100:.0f}%", color)
                 for name, value, color in self._segments]
        total_w = sum(fm.horizontalAdvance(t) + 22 for t, _ in items)
        x = self.width() / 2 - total_w / 2
        for text, color in items:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(QRectF(x, y + 3, 10, 10), 3, 3)
            p.setPen(_LABEL)
            p.drawText(QRectF(x + 14, y, 300, 16), Qt.AlignmentFlag.AlignLeft, text)
            x += fm.horizontalAdvance(text) + 24
        p.end()

    def mouseMoveEvent(self, event) -> None:
        rect = self._donut_rect()
        total = self._total()
        if self._segments and total > 0 and rect.contains(event.position()):
            dx = event.position().x() - rect.center().x()
            dy = event.position().y() - rect.center().y()
            ang = math.degrees(math.atan2(-dy, dx))
            ang = (ang + 360) % 360  # 0°=右, 顺时针
            # 起始在 90°(顶)，顺时针负 sweep
            sweep_start = 90.0
            for i, (name, value, color) in enumerate(self._segments):
                span = 360.0 * value / total
                end = sweep_start - span
                # 检查 ang 是否在 [end, sweep_start]（顺时针）
                if end <= ang <= sweep_start or (
                        end > sweep_start and (ang <= sweep_start or ang >= end)):
                    self._hover_seg = i
                    pct = value / total * 100
                    self._show_tip(int(event.position().x()),
                                   int(event.position().y()),
                                   f"<b style='color:#FFF'>{name}</b><br/>"
                                   f"<span style='color:{color.name()}'>◼</span> "
                                   f"{_fmt(value)} ({pct:.1f}%)")
                    break
            else:
                self._hover_seg = -1
                self._hide_tip()
        else:
            self._hover_seg = -1
            self._hide_tip()
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover_seg = -1
        self._hide_tip()
        self.update()
        super().leaveEvent(event)


class FluentGaugeChart(_ChartBase):
    """Fluent 仪表盘：270° 圆弧，可选分段色带，居中显示数值。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self._min = 0.0
        self._max = 100.0
        self._value = 0.0
        self._zones: list[tuple[float, float, str]] = []
        self._tick_count = 10

    def set_range(self, minimum: float, maximum: float) -> "FluentGaugeChart":
        self._min, self._max = minimum, maximum
        self.update()
        return self

    def set_value(self, value: float) -> "FluentGaugeChart":
        self._value = max(self._min, min(self._max, value))
        self.update()
        return self

    def value(self) -> float:
        return self._value

    def set_zones(self, zones) -> "FluentGaugeChart":
        """zones: [(下限, 上限, 颜色), ...] 在背景轨上绘制色带。"""
        self._zones = list(zones)
        self.update()
        return self

    def _fraction(self, v: float) -> float:
        if self._max <= self._min:
            return 0.0
        return (v - self._min) / (self._max - self._min)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_title(p)

        size = min(self.width() - 20, self.height() - 50)
        rect = QRectF((self.width() - size) / 2, 40, size, size)
        pen_w = size * 0.09
        r = rect

        # 起始角 135°，扫 270°（顺时针向下）
        start_deg = 135.0
        span_total = 270.0

        # 背景轨 + 色带
        track = QPen(QColor(P.fill_layer), pen_w,
                     Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
        p.setPen(track)
        p.drawArc(r, int(start_deg * 16), int(-span_total * 16))

        # 分段色带
        for lo, hi, color in self._zones:
            f0, f1 = self._fraction(lo), self._fraction(hi)
            a0 = start_deg - span_total * f0
            a1 = start_deg - span_total * f1
            p.setPen(QPen(QColor(color), pen_w, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.FlatCap))
            p.drawArc(r, int(a0 * 16), int((a1 - a0) * 16))

        # 当前值弧
        f = self._fraction(self._value)
        a = start_deg - span_total * f
        p.setPen(QPen(QColor(P.accent_light), pen_w, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.FlatCap))
        p.drawArc(r, int(start_deg * 16), int((a - start_deg) * 16))

        # 刻度
        for i in range(self._tick_count + 1):
            fi = i / self._tick_count
            ang = math.radians(start_deg - span_total * fi)
            cx = r.center().x()
            cy = r.center().y()
            R = r.width() / 2
            x1 = cx + (R - pen_w / 2 - 4) * math.cos(ang)
            y1 = cy + (R - pen_w / 2 - 4) * math.sin(ang)
            x2 = cx + (R - pen_w / 2 - 10) * math.cos(ang)
            y2 = cy + (R - pen_w / 2 - 10) * math.sin(ang)
            p.setPen(QPen(_LABEL, 1.6))
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # 数值
        p.setFont(self._title_font())
        p.setPen(QColor(P.text_primary))
        p.drawText(QRectF(0, r.center().y() - 26, self.width(), 40),
                   Qt.AlignmentFlag.AlignCenter, _fmt(self._value))
        p.setFont(self._tick_font())
        p.setPen(_LABEL)
        p.drawText(QRectF(0, r.center().y() + 6, self.width(), 20),
                   Qt.AlignmentFlag.AlignCenter, f"{_fmt(self._min)}  ~  {_fmt(self._max)}")
        p.end()
