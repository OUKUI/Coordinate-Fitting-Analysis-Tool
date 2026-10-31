"""Fluent 全局样式表（QSS）。

提供统一的深色基调：背景、滚动条、工具提示、状态栏、菜单等。
控件本身的细节样式在各自模块内注入。
"""
from __future__ import annotations

from .theme import palette as P


def build_global_qss() -> str:
    return f"""
/* ============ 全局 ============ */
QWidget {{
    background-color: {P.bg_layer_default};
    color: {P.text_primary};
    font-family: "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI", "PingFang SC";
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background-color: {P.bg_layer_default};
}}

/* ============ 工具提示 ============ */
QToolTip {{
    background-color: {P.tooltip_bg};
    color: {P.text_primary};
    border: 1px solid {P.stroke_layer};
    border-radius: 3px;
    padding: 5px 8px;
}}

/* ============ 滚动条 ============ */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {P.fill_hover};
    border-radius: 5px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{
    background: {P.stroke_hover};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {P.fill_hover};
    border-radius: 5px;
    min-width: 32px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {P.stroke_hover};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}

/* ============ 菜单 ============ */
QMenu {{
    background-color: {P.bg_layer_glass};
    color: {P.text_primary};
    border: 1px solid {P.stroke_layer};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 28px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {P.fill_hover};
}}
QMenu::item:disabled {{
    color: {P.text_disabled};
}}
QMenu::separator {{
    height: 1px;
    background: {P.divider};
    margin: 4px 8px;
}}

/* ============ 状态栏 ============ */
QStatusBar {{
    background-color: {P.bg_layer_alt};
    color: {P.text_secondary};
    border-top: 1px solid {P.divider};
}}
QStatusBar::item {{
    border: none;
}}

/* ============ 标签 ============ */
QLabel {{
    background: transparent;
}}
QLabel[role="title"] {{
    font-size: 20px;
    font-weight: 600;
    color: {P.text_primary};
}}
QLabel[role="subtitle"] {{
    font-size: 13px;
    color: {P.text_secondary};
}}
QLabel[role="caption"] {{
    font-size: 11px;
    color: {P.text_tertiary};
}}

/* ============ 工具条按钮 ============ */
QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px;
}}
QToolButton:hover {{
    background-color: {P.fill_hover};
}}
QToolButton:pressed {{
    background-color: {P.fill_pressed};
}}
"""
