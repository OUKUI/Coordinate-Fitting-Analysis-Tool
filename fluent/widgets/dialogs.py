"""Fluent 输入对话框与进度对话框。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from ..theme import palette as P
from ..window import FluentDialog
from .button import FluentButton
from .lineedit import FluentLineEdit
from .progressbar import FluentProgressBar
from .spinbox import FluentSpinBox


class FluentInputDialog(FluentDialog):
    """Fluent 输入对话框。

    用法::

        name = FluentInputDialog.get_text(window, "重命名", "新名称：", "默认")
        pwd  = FluentInputDialog.get_password(window, "解锁", "请输入密码：")
        num  = FluentInputDialog.get_int(window, "数量", "请输入数量：", 5, 0, 99)
    """

    def __init__(self, title: str, label: str, default: str = "",
                 placeholder: str = "", password: bool = False,
                 parent=None) -> None:
        super().__init__(title, width=420, height=200, parent=parent)
        self.setModal(True)
        self._result = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 18)
        root.setSpacing(14)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; background: transparent;")
        root.addWidget(lbl)

        self._edit = FluentLineEdit(default, placeholder)
        if password:
            self._edit.setEchoMode(FluentLineEdit.EchoMode.Password)
        self._edit.returnPressed.connect(self._accept)
        root.addWidget(self._edit)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = FluentButton("取消")
        cancel.clicked.connect(self.reject)
        ok = FluentButton("确定", variant="accent")
        ok.clicked.connect(self._accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        root.addLayout(btns)

        self._edit.setFocus()

    def _accept(self) -> None:
        self._result = self._edit.text()
        self.accept()

    @staticmethod
    def get_text(parent, title: str, label: str, default: str = "",
                 placeholder: str = "") -> str | None:
        dlg = FluentInputDialog(title, label, default, placeholder, parent=parent)
        dlg.exec()
        return dlg._result

    @staticmethod
    def get_password(parent, title: str, label: str, placeholder: str = "") -> str | None:
        dlg = FluentInputDialog(title, label, "", placeholder, password=True,
                                parent=parent)
        dlg.exec()
        return dlg._result

    @staticmethod
    def get_int(parent, title: str, label: str, default: int = 0,
                minimum: int = 0, maximum: int = 9999) -> int | None:
        dlg = FluentInputDialog(title, label, parent=parent)
        # 把输入框替换为数字输入框
        idx = dlg.layout().indexOf(dlg._edit)
        old = dlg._edit
        dlg.layout().removeWidget(old)
        old.deleteLater()
        spin = FluentSpinBox(value=default, minimum=minimum, maximum=maximum)
        spin.returnPressed.connect(dlg._accept)
        dlg.layout().insertWidget(idx, spin)
        dlg._edit = spin
        spin.setFocus()
        dlg.exec()
        return None if dlg._result is None else spin.value()


class FluentProgressDialog(FluentDialog):
    """Fluent 进度对话框。

    用法::

        dlg = FluentProgressDialog(window, "正在导出", "准备中…")
        for i in range(101):
            dlg.set_value(i)
            QApplication.processEvents()
            time.sleep(0.02)
        dlg.close()
    """

    cancelled = Signal()

    def __init__(self, parent=None, title: str = "进度", label: str = "",
                 maximum: int = 100, cancellable: bool = True) -> None:
        super().__init__(title, width=440, height=200, parent=parent)
        self.setModal(False)
        self._cancel = False

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 18)
        root.setSpacing(14)

        self._label = QLabel(label)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            "font-size: 13px; background: transparent;")
        root.addWidget(self._label)

        self._bar = FluentProgressBar(0, maximum)
        self._bar.setFixedHeight(6)
        root.addWidget(self._bar)

        btns = QHBoxLayout()
        btns.addStretch(1)
        if cancellable:
            cancel = FluentButton("取消")
            cancel.clicked.connect(self._on_cancel)
            btns.addWidget(cancel)
        root.addLayout(btns)

    def _on_cancel(self) -> None:
        self._cancel = True
        self.cancelled.emit()

    def was_cancelled(self) -> bool:
        return self._cancel

    def set_value(self, value: int) -> None:
        self._bar.setValue(value)

    def set_maximum(self, maximum: int) -> None:
        self._bar.setMaximum(maximum)

    def set_label(self, text: str) -> None:
        self._label.setText(text)

    @staticmethod
    def run(parent, title: str, worker_fn, label: str = "",
            cancellable: bool = True):
        """在主线程中逐步执行 worker_fn(progress_signal) 并更新进度。

        worker_fn 接收一个回调 progress(int) 用于汇报进度，返回最终结果。
        """
        from PySide6.QtWidgets import QApplication

        dlg = FluentProgressDialog(parent, title, label, cancellable=cancellable)
        dlg.show()
        result = None
        cancelled = False

        def _progress(value: int, text: str = "") -> bool:
            dlg.set_value(value)
            if text:
                dlg.set_label(text)
            QApplication.processEvents()
            return not dlg.was_cancelled()

        try:
            result = worker_fn(_progress)
        except Exception as e:  # noqa: BLE001
            from .messagebox import FluentMessageBox
            FluentMessageBox.error(dlg, "错误", str(e))
        finally:
            dlg.close()
        return result
