"""Fluent 消息对话框（MessageBox）。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from ..theme import palette as P
from ..window import FluentDialog
from .button import FluentButton
from .icons import IconBadge


class FluentMessageBox(FluentDialog):
    """Fluent 风格模态消息框。

    常用 classmethod 用法（parent 在前）::

        FluentMessageBox.info(window, "标题", "这是一条提示")
        FluentMessageBox.warning(window, "警告", "磁盘空间不足")
        FluentMessageBox.error(window, "错误", "保存失败")
        if FluentMessageBox.confirm(window, "确认", "确定要删除吗？"):
            ...
    """

    def __init__(self, title: str, message: str, kind: str = "info",
                 buttons=("ok",), parent=None) -> None:
        super().__init__(title, width=440, height=220, parent=parent)
        self.setModal(True)
        self._result = False

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(IconBadge(kind, size=44), 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 600; background: transparent;")
        text_col.addWidget(title_lbl)
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(
            "font-size: 13px; color: #BDBDBD; background: transparent;")
        text_col.addWidget(msg_lbl)
        text_col.addStretch(1)
        body.addLayout(text_col, 1)
        root.addLayout(body)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        is_confirm = len(buttons) > 1
        for b in buttons:
            if b == "ok":
                btn = FluentButton("确定", variant="accent")
                btn.clicked.connect(lambda: self._done(True))
            elif b == "cancel":
                btn = FluentButton("取消" if is_confirm else "关闭")
                btn.clicked.connect(lambda: self._done(False))
            elif b == "yes":
                btn = FluentButton("是", variant="accent")
                btn.clicked.connect(lambda: self._done(True))
            elif b == "no":
                btn = FluentButton("否")
                btn.clicked.connect(lambda: self._done(False))
            else:
                continue
            btn_row.addWidget(btn)
        root.addLayout(btn_row)

    def _done(self, ok: bool) -> None:
        self._result = ok
        self.accept()

    # ---- 便捷入口（parent 在前，与 Toast / Tooltip / TeachingTip 一致） ----
    @classmethod
    def popup(cls, parent=None, title: str = "", message: str = "",
              kind: str = "info") -> None:
        box = cls(title, message, kind, ("ok",), parent)
        box.exec()

    @classmethod
    def confirm(cls, parent=None, title: str = "", message: str = "",
                yes_text: str = "确定", no_text: str = "取消") -> bool:
        box = cls(title, message, "info", ("yes", "no"), parent)
        # 覆盖按钮文字
        for w in box.findChildren(FluentButton):
            if w.text() == "是":
                w.setText(yes_text)
            elif w.text() == "否":
                w.setText(no_text)
        box.exec()
        return box._result

    @classmethod
    def info(cls, parent=None, title: str = "", message: str = "") -> None:
        cls.popup(parent, title, message, "info")

    @classmethod
    def success(cls, parent=None, title: str = "", message: str = "") -> None:
        cls.popup(parent, title, message, "success")

    @classmethod
    def warning(cls, parent=None, title: str = "", message: str = "") -> None:
        cls.popup(parent, title, message, "warning")

    @classmethod
    def error(cls, parent=None, title: str = "", message: str = "") -> None:
        cls.popup(parent, title, message, "error")
