"""主题设置（已由自研 fluent 控件库统一处理深色主题，此模块保留兼容）。"""


def setup_theme(dark=True):
    """兼容占位：FluentApp 已自动应用深色主题。"""
    return None


def get_chinese_font(size=9):
    from PySide6.QtGui import QFont
    return QFont("Microsoft YaHei", size)
