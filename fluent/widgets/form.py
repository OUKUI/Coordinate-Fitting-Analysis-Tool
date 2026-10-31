"""Fluent 自动表单：根据字段定义生成表单并读取/校验数值。"""
from __future__ import annotations

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QScrollArea,
                               QVBoxLayout, QWidget)

from ..theme import palette as P
from ..window import FluentDialog
from .button import FluentButton
from .checkbox import FluentCheckBox, FluentRadioButton
from .colorpicker import FluentColorButton
from .combobox import FluentComboBox
from .datetime import FluentDatePicker
from .lineedit import FluentLineEdit, FluentTextEdit
from .misc import FluentQuantitySelector, FluentRating
from .slider import FluentSlider
from .spinbox import FluentSpinBox
from .toggle import FluentToggleSwitch


class FluentForm(QScrollArea):
    """根据字段定义自动生成表单。

    字段类型：text / password / multiline / int / float / bool / combo /
    radio / slider / quantity / rating / date / color / spacer

    用法::

        fields = {
            "名称": {"type": "text", "default": "", "required": True},
            "数量": {"type": "int", "default": 5, "min": 0, "max": 99},
            "启用": {"type": "bool", "default": True},
            "级别": {"type": "combo", "options": ["低", "中", "高"]},
        }
        form = FluentForm(fields)
        form.values()   # -> {"名称": ..., "数量": ..., ...}
    """

    valuesChanged = Signal()

    def __init__(self, fields: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._fields: dict = {}
        self._widgets: dict[str, QWidget] = {}

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setContentsMargins(0, 0, 8, 0)
        self._vbox.setSpacing(12)
        self.setWidget(self._container)

        if fields:
            self.set_fields(fields)

    def set_fields(self, fields: dict) -> None:
        self._fields = dict(fields)
        self._rebuild()

    def _rebuild(self) -> None:
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._widgets.clear()

        for label, spec in self._fields.items():
            if isinstance(spec, str):
                spec = {"type": spec}
            spec = dict(spec)
            ftype = spec.get("type", "text")
            if ftype == "spacer":
                self._vbox.addSpacing(int(spec.get("height", 8)))
                continue

            row = QHBoxLayout()
            row.setSpacing(12)
            lbl = QLabel(label)
            lbl.setFixedWidth(96)
            lbl.setStyleSheet("color: #BDBDBD; background: transparent; font-size: 12px;")
            row.addWidget(lbl)

            widget = self._make_widget(ftype, spec)
            if widget is not None:
                self._widgets[label] = widget
                row.addWidget(widget, 1)
            self._vbox.addLayout(row)

        self._vbox.addStretch(1)

    def _make_widget(self, ftype: str, spec: dict):
        default = spec.get("default", "")
        if ftype in ("text", "password"):
            w = FluentLineEdit(str(default), spec.get("placeholder", ""))
            if ftype == "password":
                w.setEchoMode(FluentLineEdit.EchoMode.Password)
        elif ftype == "multiline":
            w = FluentTextEdit(str(default), spec.get("placeholder", ""))
            w.setFixedHeight(90)
        elif ftype == "int":
            w = FluentSpinBox(value=int(default),
                              minimum=int(spec.get("min", -10**9)),
                              maximum=int(spec.get("max", 10**9)))
        elif ftype == "float":
            w = FluentSpinBox(value=int(float(default)),
                              minimum=int(spec.get("min", -10**9)),
                              maximum=int(spec.get("max", 10**9)))
        elif ftype == "bool":
            w = FluentToggleSwitch("", checked=bool(default))
        elif ftype == "combo":
            w = FluentComboBox(list(spec.get("options", [])))
            try:
                w.setCurrentText(str(default))
            except Exception:  # noqa: BLE001
                pass
        elif ftype == "radio":
            w = QWidget()
            hl = QHBoxLayout(w)
            hl.setContentsMargins(0, 0, 0, 0)
            for i, opt in enumerate(spec.get("options", [])):
                rb = FluentRadioButton(str(opt))
                rb.setChecked(str(default) == str(opt) or i == 0)
                hl.addWidget(rb)
            hl.addStretch(1)
        elif ftype == "slider":
            w = FluentSlider(value=int(default),
                             minimum=int(spec.get("min", 0)),
                             maximum=int(spec.get("max", 100)))
        elif ftype == "quantity":
            w = FluentQuantitySelector(value=int(default),
                                       minimum=int(spec.get("min", 0)),
                                       maximum=int(spec.get("max", 99)))
        elif ftype == "rating":
            w = FluentRating(rating=int(default), maximum=int(spec.get("max", 5)))
        elif ftype == "date":
            w = FluentDatePicker()
            if default:
                try:
                    w.setDate(QDate.fromString(str(default), "yyyy-MM-dd"))
                except Exception:  # noqa: BLE001
                    pass
        elif ftype == "color":
            w = FluentColorButton(str(default) or "#0067C0")
        else:
            w = FluentLineEdit(str(default))
        return w

    # ---- 读取 ----
    def values(self) -> dict:
        result = {}
        for label, spec in self._fields.items():
            if isinstance(spec, str):
                spec = {"type": spec}
            w = self._widgets.get(label)
            if w is None:
                continue
            ftype = spec.get("type", "text")
            if ftype in ("text", "password", "multiline"):
                result[label] = w.text()
            elif ftype == "int":
                result[label] = w.value()
            elif ftype == "float":
                result[label] = float(w.value())
            elif ftype == "bool":
                result[label] = w.isChecked()
            elif ftype == "combo":
                result[label] = w.currentText()
            elif ftype == "radio":
                for rb in w.findChildren(FluentRadioButton):
                    if rb.isChecked():
                        result[label] = rb.text()
                        break
            elif ftype in ("slider", "quantity"):
                result[label] = w.value()
            elif ftype == "rating":
                result[label] = w.rating()
            elif ftype == "date":
                result[label] = w.date().toString("yyyy-MM-dd")
            elif ftype == "color":
                result[label] = w.color().name()
        return result

    def validate(self) -> tuple[bool, str]:
        """校验必填字段；返回 (是否通过, 错误信息)。"""
        for label, spec in self._fields.items():
            if isinstance(spec, str):
                spec = {"type": spec}
            if spec.get("required"):
                w = self._widgets.get(label)
                if w is not None and hasattr(w, "text") and not w.text().strip():
                    return False, f"「{label}」为必填项"
        return True, ""

    # ---- 对话框 ----
    @staticmethod
    def get_values(parent, title: str, fields: dict) -> dict | None:
        """弹出表单对话框，确定返回数值字典，取消返回 None。"""
        dlg = FluentDialog(title, width=480, height=520, parent=parent)
        dlg.setModal(True)
        root = QVBoxLayout(dlg)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        form = FluentForm(fields)
        root.addWidget(form, 1)

        err = QLabel("")
        err.setStyleSheet("color: #E74856; background: transparent; font-size: 12px;")
        root.addWidget(err)

        btns = QHBoxLayout()
        btns.addStretch(1)
        ok = FluentButton("确定", variant="accent")
        cancel = FluentButton("取消")

        def _ok():
            ok_flag, msg = form.validate()
            if ok_flag:
                dlg._result = form.values()
                dlg.accept()
            else:
                err.setText(msg)

        ok.clicked.connect(_ok)
        cancel.clicked.connect(dlg.reject)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        root.addLayout(btns)
        dlg._result = None
        dlg.exec()
        return dlg._result
