"""Fluent 折叠面板（Expander）与分组框（GroupBox）。"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (QFrame, QGroupBox, QHBoxLayout, QLabel,
                               QVBoxLayout, QWidget)

from ..theme import palette as P


class FluentExpander(QFrame):
    """Fluent 折叠面板：点击标题栏展开/收起内容区（带动画）。

    用法::

        exp = FluentExpander("更多选项")
        exp.addWidget(FluentToggleSwitch("自动更新"))
        exp.addWidget(FluentButton("重置"))
    """

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(parent)
        self._expanded = True
        self.setObjectName("FluentExpander")
        self.setStyleSheet(f"""
            #FluentExpander {{
                background-color: {P.card};
                border: 1px solid {P.divider};
                border-radius: 8px;
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._header = QFrame(self)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet("""
            QFrame { background: transparent; border: none; border-radius: 8px; }
            QFrame:hover { background-color: rgba(255, 255, 255, 12); }
        """)
        header_lay = QHBoxLayout(self._header)
        header_lay.setContentsMargins(14, 12, 14, 12)
        self._chevron = QLabel("▾")
        self._chevron.setStyleSheet("background: transparent; color: #9D9D9D;")
        header_lay.addWidget(self._chevron)
        self._title = QLabel(title)
        self._title.setStyleSheet(
            "background: transparent; font-size: 13px; font-weight: 600;")
        header_lay.addWidget(self._title)
        header_lay.addStretch(1)
        outer.addWidget(self._header)

        self._body = QWidget(self)
        self._body.setStyleSheet("background: transparent;")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(14, 0, 14, 12)
        self._body_lay.setSpacing(8)
        outer.addWidget(self._body)

        self._header.mousePressEvent = self._on_header_click

        self._anim = QPropertyAnimation(self._body, b"maximumHeight", self)
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._body.setMaximumHeight(16777215)

    def title(self) -> str:
        return self._title.text()

    def setTitle(self, title: str) -> None:
        self._title.setText(title)

    def content_layout(self):
        return self._body_lay

    def addWidget(self, widget: QWidget) -> None:
        self._body_lay.addWidget(widget)

    def is_expanded(self) -> bool:
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._chevron.setText("▾" if expanded else "▸")
        self._anim.stop()
        if expanded:
            self._body.setMaximumHeight(0)
            self._anim.setStartValue(0)
            target = self._body_lay.sizeHint().height()
            self._anim.setEndValue(max(1, target))
        else:
            self._anim.setStartValue(self._body.height())
            self._anim.setEndValue(0)
        self._anim.start()

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)

    def _on_header_click(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
        QFrame.mousePressEvent(self._header, event)


class FluentGroupBox(QGroupBox):
    """Fluent 风格分组框。"""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self.setStyleSheet(f"""
            QGroupBox {{
                background-color: {P.card};
                border: 1px solid {P.divider};
                border-radius: 8px;
                margin-top: 14px;
                font-size: 13px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: 2px;
                padding: 0 6px;
                color: {P.text_primary};
                background: transparent;
            }}
        """)
