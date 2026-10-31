"""Fluent 选色组件：颜色按钮 + 选色面板 + 选色对话框。

全部自绘（HSV 取色区 / 色相条），深色主题，无第三方图片资源。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (QColor, QIcon, QLinearGradient, QPainter, QPen,
                           QPixmap)
from PySide6.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)

from ..theme import palette as P
from .button import FluentButton
from .lineedit import FluentLineEdit
from .spinbox import FluentSpinBox

_HEX_RE = re.compile(r"^[0-9a-fA-F]{6}$")

# 预设色板：中性色 + 常用强调色
PRESET_COLORS: list[str] = [
    "#FFFFFF", "#F5F5F5", "#E0E0E0", "#C0C0C0", "#9E9E9E",
    "#757575", "#555555", "#333333", "#171717", "#000000",
    "#FF0000", "#FF6F00", "#FFC400", "#00B050", "#00B0F0",
    "#0067C0", "#5C2D91", "#E3008C", "#00B8C8", "#C00000",
    "#F1C40F", "#E67E22", "#E74C3C", "#16A085", "#27AE60",
    "#2ECC71", "#3498DB", "#2980B9", "#8E44AD", "#9B59B6",
]


class _SVField(QWidget):
    """饱和度/明度二维取色区。"""

    changed = Signal()

    def __init__(self, hue: float = 0.58, sat: float = 1.0, val: float = 1.0,
                 parent=None) -> None:
        super().__init__(parent)
        self._hue, self._sat, self._val = hue, sat, val
        self.setFixedSize(220, 160)
        self.setCursor(Qt.CursorShape.CrossCursor)

    @property
    def hue(self) -> float:
        return self._hue

    @property
    def sat(self) -> float:
        return self._sat

    @property
    def val(self) -> float:
        return self._val

    def set_hue(self, hue: float) -> None:
        self._hue = hue
        self.update()

    def set_hsv(self, hue: float, sat: float, val: float) -> None:
        self._hue, self._sat, self._val = hue, sat, val
        self.update()

    def _apply_pos(self, pos) -> None:
        w, h = self.width(), self.height()
        self._sat = max(0.0, min(1.0, pos.x() / max(1, w)))
        self._val = max(0.0, min(1.0, 1.0 - pos.y() / max(1, h)))
        self.changed.emit()
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._apply_pos(event.position())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._apply_pos(event.position())
        super().mouseMoveEvent(event)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()

        hue_color = QColor.fromHsvF(self._hue, 1.0, 1.0)
        hg = QLinearGradient(r.left(), r.top(), r.right(), r.top())
        hg.setColorAt(0.0, QColor(255, 255, 255))
        hg.setColorAt(1.0, hue_color)
        p.fillRect(r, hg)

        vg = QLinearGradient(r.left(), r.top(), r.left(), r.bottom())
        vg.setColorAt(0.0, QColor(0, 0, 0, 0))
        vg.setColorAt(1.0, QColor(0, 0, 0, 255))
        p.fillRect(r, vg)

        x = self._sat * r.width()
        y = (1.0 - self._val) * r.height()
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x, y), 6, 6)
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.drawEllipse(QPointF(x, y), 3, 3)
        p.end()


class _HueBar(QWidget):
    """色相条。"""

    changed = Signal()

    _STOPS = [
        (0.00, "#FF0000"), (0.17, "#FFFF00"), (0.33, "#00FF00"),
        (0.50, "#00FFFF"), (0.67, "#0000FF"), (0.83, "#FF00FF"),
        (1.00, "#FF0000"),
    ]

    def __init__(self, hue: float = 0.58, parent=None) -> None:
        super().__init__(parent)
        self._hue = hue
        self.setFixedHeight(18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def hue(self) -> float:
        return self._hue

    def set_hue(self, hue: float) -> None:
        self._hue = hue
        self.update()

    def _apply_pos(self, pos) -> None:
        self._hue = max(0.0, min(1.0, pos.x() / max(1, self.width())))
        self.changed.emit()
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._apply_pos(event.position())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._apply_pos(event.position())
        super().mouseMoveEvent(event)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        g = QLinearGradient(r.left(), 0, r.right(), 0)
        for t, c in self._STOPS:
            g.setColorAt(t, QColor(c))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(r, 9, 9)

        x = self._hue * r.width()
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(x, r.center().y()), 7, 7)
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.drawEllipse(QPointF(x, r.center().y()), 4, 4)
        p.end()


class FluentColorPicker(QWidget):
    """Fluent 选色面板（可独立嵌入任意界面）。"""

    colorChanged = Signal(QColor)

    def __init__(self, color: str = "#0078D4", parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._updating = False

        self._hue, self._sat, self._val, _a = self._color.getHsvF()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # ---- 取色区 + 右侧预览/输入 ----
        top = QHBoxLayout()
        top.setSpacing(16)

        self._sv = _SVField(self._hue, self._sat, self._val)
        self._sv.changed.connect(self._on_sv_changed)
        top.addWidget(self._sv)

        right = QVBoxLayout()
        right.setSpacing(10)

        self._preview = QLabel()
        self._preview.setFixedSize(44, 44)
        right.addWidget(self._preview, 0, Qt.AlignmentFlag.AlignHCenter)

        right.addWidget(self._field_label("十六进制"))
        self._hex = FluentLineEdit()
        self._hex.setFixedWidth(110)
        self._hex.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hex.textEdited.connect(self._on_hex)
        right.addWidget(self._hex, 0, Qt.AlignmentFlag.AlignHCenter)

        self._r = self._spin()
        self._g = self._spin()
        self._b = self._spin()
        for name, spin in (("R", self._r), ("G", self._g), ("B", self._b)):
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(name)
            lbl.setFixedWidth(16)
            lbl.setStyleSheet("color: #8A8A8A; background: transparent;")
            row.addWidget(lbl)
            row.addWidget(spin)
            right.addLayout(row)

        top.addLayout(right)
        top.addStretch(1)
        root.addLayout(top)

        # ---- 色相条 ----
        self._huebar = _HueBar(self._hue)
        self._huebar.changed.connect(self._on_hue_changed)
        root.addWidget(self._huebar)

        # ---- 预设色板 ----
        preset_lbl = QLabel("预设颜色")
        preset_lbl.setStyleSheet("color: #8A8A8A; background: transparent; font-size: 12px;")
        root.addWidget(preset_lbl)

        grid = QGridLayout()
        grid.setSpacing(6)
        cols = 10
        for i, c in enumerate(PRESET_COLORS):
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(c)
            btn.setStyleSheet(
                f"background-color: {c}; border: 1px solid {P.stroke_layer};"
                f"border-radius: 4px;")
            btn.clicked.connect(lambda _=False, cc=c: self.set_color(cc))
            grid.addWidget(btn, i // cols, i % cols)
        root.addLayout(grid)

        self._sync()
        self._on_color_changed()

    # ---- 工具 ----
    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #8A8A8A; background: transparent; font-size: 12px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        return lbl

    def _spin(self) -> FluentSpinBox:
        spin = FluentSpinBox(value=0, minimum=0, maximum=255)
        spin.setFixedWidth(76)
        spin.valueChanged.connect(self._on_rgb)
        return spin

    # ---- 对外接口 ----
    def color(self) -> QColor:
        return self._color

    def set_color(self, color) -> None:
        self._color = QColor(color)
        self._hue, self._sat, self._val, _a = self._color.getHsvF()
        self._sv.set_hsv(self._hue, self._sat, self._val)
        self._huebar.set_hue(self._hue)
        self._sync()
        self._on_color_changed()

    # ---- 内部联动 ----
    def _on_sv_changed(self) -> None:
        self._hue = self._sv.hue
        self._sat = self._sv.sat
        self._val = self._sv.val
        self._apply()

    def _on_hue_changed(self) -> None:
        self._hue = self._huebar.hue
        self._sv.set_hue(self._hue)
        self._apply()

    def _on_hex(self, text: str) -> None:
        if self._updating:
            return
        t = text.strip().lstrip("#")
        if _HEX_RE.match(t):
            self.set_color("#" + t)

    def _on_rgb(self, _v: int) -> None:
        if self._updating:
            return
        self.set_color(QColor(self._r.value(), self._g.value(), self._b.value()))

    def _apply(self) -> None:
        self._color = QColor.fromHsvF(self._hue, self._sat, self._val)
        self._sync()
        self._on_color_changed()

    def _sync(self) -> None:
        self._updating = True
        self._hex.setText(self._color.name().upper())
        self._r.setValue(self._color.red())
        self._g.setValue(self._color.green())
        self._b.setValue(self._color.blue())
        self._preview.setStyleSheet(
            f"background-color: {self._color.name()};"
            f"border: 1px solid {P.stroke_layer}; border-radius: 6px;")
        self._updating = False

    def _on_color_changed(self) -> None:
        self.colorChanged.emit(self._color)


class FluentColorDialog(QDialog):
    """Fluent 选色对话框。"""

    def __init__(self, color: str = "#0078D4", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择颜色")
        self.setModal(True)
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(16)

        title = QLabel("选择颜色")
        title.setStyleSheet(
            "font-size: 16px; font-weight: 600; background: transparent;")
        root.addWidget(title)

        self.picker = FluentColorPicker(color)
        root.addWidget(self.picker)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel = FluentButton("取消")
        cancel.clicked.connect(self.reject)
        ok = FluentButton("确定", variant="accent")
        ok.clicked.connect(self.accept)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        root.addLayout(btn_row)

    def color(self) -> QColor:
        return self.picker.color()

    @staticmethod
    def getColor(initial: str = "#0078D4", parent=None) -> QColor | None:
        """模态选色；取消返回 None。"""
        dlg = FluentColorDialog(initial, parent)
        if dlg.exec() == FluentColorDialog.DialogCode.Accepted:
            return dlg.color()
        return None


class FluentColorButton(FluentButton):
    """显示颜色色块 + 十六进制文字的颜色按钮，点击弹出选色对话框。"""

    colorChanged = Signal(QColor)

    def __init__(self, color: str = "#0078D4", parent=None, text: str = "") -> None:
        super().__init__("", parent, variant="standard")
        self._color = QColor(color)
        self._custom_text = text
        self.clicked.connect(self._pick)
        self._refresh_ui()

    def color(self) -> QColor:
        return self._color

    def setColor(self, color) -> None:
        self._color = QColor(color)
        self._refresh_ui()
        self.colorChanged.emit(self._color)

    def _refresh_ui(self) -> None:
        self.setText(self._custom_text or self._color.name().upper())
        pm = QPixmap(18, 18)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(P.stroke_layer), 1))
        p.setBrush(self._color)
        p.drawRoundedRect(QRectF(1, 1, 16, 16), 3, 3)
        p.end()
        self.setIcon(QIcon(pm))
        self.setIconSize(QSize(18, 18))

    def _pick(self) -> None:
        c = FluentColorDialog.getColor(self._color.name(), self.window())
        if c is not None:
            self.setColor(c)
