"""
注塑件模具修模分析工具
Fluent Design · Dark Mode · High DPI
基于自研 Fluent 控件库（PySide6 / LGPL 可免费商用）
"""

import sys

from fluent.window import FluentApp

from ui.main_window import MainWindow


def main():
    app = FluentApp(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
