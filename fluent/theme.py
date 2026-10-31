"""Fluent Design 深色主题色板

颜色取自 Windows 11 Fluent / WinUI 3 深色主题标准色值。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FluentPalette:
    """Fluent 深色主题颜色。

    Windows 11 深色模式配色，遵循 WinUI 3 的 Layer / Fill / Stroke 体系。
    """

    # ---- 背景层（Layer） ----
    bg_layer_default: str = "#202020"
    bg_layer_alt: str = "#1B1B1B"
    bg_layer_glass: str = "#2C2C2C"

    # ---- 填充层（Fill） ----
    fill_layer: str = "#2B2B2B"
    fill_hover: str = "#3F3F3F"     # 悬停：明显亮于背景
    fill_pressed: str = "#353535"
    fill_selected: str = "#4E4E4E"  # 选中：明显亮于悬停
    fill_disabled: str = "#262626"

    # ---- 描边（Stroke） ----
    stroke_layer: str = "#454545"
    stroke_hover: str = "#7C7C7C"
    stroke_pressed: str = "#454545"

    # ---- 文本 ----
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#9D9D9D"
    text_tertiary: str = "#6E6E6E"
    text_disabled: str = "#5C5C5C"

    # ---- 强调色（Accent，Fluent 默认蓝，已加深保证白字对比度） ----
    accent: str = "#0067C0"       # 填充底色，白字对比约 5.7:1
    accent_hover: str = "#005FB8"  # 悬停（更深）
    accent_pressed: str = "#00528F"  # 按下（更深）
    accent_light: str = "#4CC2FF"  # 深色背景上的浅色强调文字/线条
    accent_disabled: str = "#3A3A3A"
    accent_on: str = "#FFFFFF"  # 强调色之上的文字

    # ---- 状态色 ----
    success: str = "#0F7B0F"
    warning: str = "#9D5D00"
    danger: str = "#C42B1C"
    danger_hover: str = "#E74856"
    info: str = "#0067C0"

    # ---- 通用 ----
    card: str = "#2B2B2B"
    divider: str = "#3B3B3B"
    tooltip_bg: str = "#3B3B3B"

    # ---- 控件半径（Fluent 规范） ----
    radius_button: int = 4
    radius_input: int = 4
    radius_card: int = 8
    radius_control: int = 4

    # ---- 控件尺寸（Fluent 规范，逻辑像素） ----
    button_height: int = 32
    control_height: int = 32
    toggle_size: int = 40  # 开关总宽度
    toggle_thumb: int = 16  # 滑块直径


# 全局默认深色主题实例
palette: FluentPalette = FluentPalette()


# ---- 颜色对比度工具 ----

def relative_luminance(color) -> float:
    """计算颜色的相对亮度（WCAG 定义）。"""
    from PySide6.QtGui import QColor
    c = QColor(color)

    def _lin(v: float) -> float:
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * _lin(c.red()) + 0.7152 * _lin(c.green()) + 0.0722 * _lin(c.blue())


def contrast_ratio(fg, bg) -> float:
    """两个颜色之间的对比度（WCAG，1:1 ~ 21:1）。"""
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def text_color_on(bg) -> str:
    """根据背景亮度自动选择可读的深色/浅色文字。"""
    return "#000000" if relative_luminance(bg) > 0.40 else "#FFFFFF"
