"""Fluent UI 控件库（深色模式 / 高 DPI / Fluent Design）。

授权说明
--------
- 依赖库：PySide6（Qt for Python），采用 LGPL v3 许可，
  符合「免费商业授权」要求；Qt 6 自 6.2 起默认启用高 DPI 缩放，
  无需额外配置即可适配高分辨率屏幕。
- 本控件库代码同样以宽松许可发布，可自由集成进商业项目。

快速上手
--------
.. code-block:: python

    from fluent.window import FluentApp
    from fluent.widgets import FluentButton

    app = FluentApp()
    from PySide6.QtWidgets import QWidget, QVBoxLayout
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(FluentButton("你好", variant="accent"))
    w.show()
    app.exec()

更多示例见 demos/ 目录。
"""
from .styles import build_global_qss
from .theme import FluentPalette, palette
from .window import FluentApp, FluentDialog, FluentWindow, apply_theme

__version__ = "0.1.0"
__all__ = [
    "FluentApp",
    "FluentDialog",
    "FluentWindow",
    "FluentPalette",
    "palette",
    "apply_theme",
    "build_global_qss",
]
