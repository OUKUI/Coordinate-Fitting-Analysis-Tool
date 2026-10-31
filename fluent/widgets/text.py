"""Fluent Markdown 查看器（内置轻量转换器，零依赖）与富文本编辑器。"""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QHBoxLayout, QTextBrowser, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget)

from ..theme import palette as P


# ---------------- 轻量 Markdown -> HTML ----------------

def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text: str) -> str:
    text = _escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def markdown_to_html(md: str) -> str:
    """把常见的 Markdown 转换为深色主题 HTML。"""
    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    code_lines: list[str] = []
    list_tag: str | None = None
    i = 0
    n = len(lines)

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    while i < n:
        line = lines[i]
        s = line.strip()

        if s.startswith("```"):
            if not in_code:
                in_code, code_lines = True, []
            else:
                in_code = False
                out.append("<pre><code>" + _escape("\n".join(code_lines))
                           + "</code></pre>")
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not s:
            close_list()
            i += 1
            continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            close_list()
            out.append("<hr/>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            close_list()
            level = len(m.group(1))
            sizes = {1: "20px", 2: "17px", 3: "15px", 4: "14px", 5: "13px", 6: "12px"}
            out.append(f"<h{level} style='margin:8px 0 4px 0;"
                       f"font-size:{sizes[level]};color:#FFFFFF;"
                       f"font-weight:bold;'>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if s.startswith(">"):
            close_list()
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(_inline(lines[i].strip()[1:].strip()))
                i += 1
            out.append("<blockquote style='margin:6px 0;padding:6px 12px;"
                       f"color:#A0A0A0;'>{'<br/>'.join(quote)}</blockquote>")
            continue

        ul = re.match(r"^[-*+]\s+(.*)$", s)
        ol = re.match(r"^\d+[.)]\s+(.*)$", s)
        if ul or ol:
            tag = "ul" if ul else "ol"
            if list_tag != tag:
                close_list()
                out.append(f"<{tag} style='margin:4px 0 4px 0;'>")
                list_tag = tag
            out.append(f"<li>{_inline((ul or ol).group(1))}</li>")
            i += 1
            continue

        # 表格（| a | b |）
        if s.startswith("|") and i + 1 < n and \
                re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]):
            close_list()
            rows = []
            while i < n and "|" in lines[i]:
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            if len(rows) > 1:
                head = rows[0]
                body = rows[2:]
                out.append("<table border='0' cellspacing='0' "
                           "cellpadding='4' style='border-collapse:collapse;'>")
                out.append("<tr>" + "".join(
                    f"<th align='left' style='border-bottom:1px solid #454545;"
                    f"color:#FFFFFF;'>{_inline(c)}</th>" for c in head) + "</tr>")
                for row in body:
                    out.append("<tr>" + "".join(
                        f"<td style='border-bottom:1px solid #2C2C2C;"
                        f"color:#D0D0D0;'>{_inline(c)}</td>" for c in row) + "</tr>")
                out.append("</table>")
            continue

        close_list()
        out.append(f"<p style='margin:4px 0;color:#D0D0D0;'>{_inline(s)}</p>")
        i += 1

    close_list()
    if in_code:
        out.append("<pre><code>" + _escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(out)


class FluentMarkdownViewer(QTextBrowser):
    """Fluent Markdown 查看器（只读，内置转换器）。"""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {P.bg_layer_default};
                color: #D0D0D0;
                border: 1px solid {P.divider};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {P.accent};
                selection-color: {P.accent_on};
            }}
        """)
        if text:
            self.set_markdown(text)

    def set_markdown(self, md: str) -> None:
        self.setHtml(markdown_to_html(md))

    def setText(self, text: str) -> None:  # 兼容 setText
        self.set_markdown(text)


class FluentRichTextEditor(QWidget):
    """Fluent 富文本编辑器：工具栏 + 编辑区。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self._edit = QTextEdit()
        self._edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {P.fill_layer};
                color: {P.text_primary};
                border: 1px solid {P.stroke_layer};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {P.accent};
                selection-color: {P.accent_on};
            }}
            QTextEdit:focus {{
                border: 1px solid {P.accent};
            }}
        """)

        def action(glyph: str, tip: str, cb) -> QToolButton:
            btn = QToolButton()
            btn.setText(glyph)
            btn.setToolTip(tip)
            btn.setCheckable(False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(28, 28)
            btn.clicked.connect(cb)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: transparent;
                    color: {P.text_primary};
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QToolButton:hover {{ background-color: {P.fill_hover}; }}
                QToolButton:pressed {{ background-color: {P.fill_pressed}; }}
            """)
            return btn

        def fmt_weight(bold: bool):
            fmt = self._edit.currentCharFormat()
            fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
            self._edit.mergeCurrentCharFormat(fmt)

        def fmt_italic():
            fmt = self._edit.currentCharFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            self._edit.mergeCurrentCharFormat(fmt)

        def fmt_underline():
            fmt = self._edit.currentCharFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            self._edit.mergeCurrentCharFormat(fmt)

        def fmt_strike():
            fmt = self._edit.currentCharFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
            self._edit.mergeCurrentCharFormat(fmt)

        def fmt_color():
            from .colorpicker import FluentColorDialog
            c = FluentColorDialog.getColor("#4CC2FF", self)
            if c is not None:
                fmt = self._edit.currentCharFormat()
                fmt.setForeground(c)
                self._edit.mergeCurrentCharFormat(fmt)

        def fmt_list(bullet: bool):
            cursor = self._edit.textCursor()
            fmt = cursor.blockFormat()
            style = (Qt.ListStyle.Disc if bullet else Qt.ListStyle.Decimal)
            cursor.beginEditBlock()
            cursor.createList(style)
            cursor.endEditBlock()

        toolbar.addWidget(action("B", "加粗", lambda: fmt_weight(True)))
        toolbar.addWidget(action("I", "斜体", fmt_italic))
        toolbar.addWidget(action("U", "下划线", fmt_underline))
        toolbar.addWidget(action("S", "删除线", fmt_strike))
        toolbar.addWidget(action("A", "文字颜色", fmt_color))
        toolbar.addWidget(action("•", "无序列表", lambda: fmt_list(True)))
        toolbar.addWidget(action("1.", "有序列表", lambda: fmt_list(False)))
        toolbar.addWidget(action("⌫", "清空", self._edit.clear))
        toolbar.addStretch(1)

        root.addLayout(toolbar)
        root.addWidget(self._edit, 1)

    def editor(self) -> QTextEdit:
        return self._edit

    def to_html(self) -> str:
        return self._edit.toHtml()

    def set_html(self, html: str) -> None:
        self._edit.setHtml(html)
