"""Fluent 多语言助手：词典式翻译 + 语言切换信号。"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class FluentTranslator(QObject):
    """轻量多语言助手。

    用法::

        tr = FluentTranslator({
            "zh": {"hello": "你好", "exit": "退出"},
            "en": {"hello": "Hello", "exit": "Exit"},
        })
        tr.set_language("zh")
        tr.t("hello")        # "你好"
        tr.languageChanged.connect(...)
    """

    languageChanged = Signal(str)

    def __init__(self, tables: dict | None = None,
                 default_language: str = "zh") -> None:
        super().__init__()
        self._tables: dict[str, dict] = dict(tables or {})
        self._language = default_language

    def set_language(self, lang: str) -> None:
        if lang != self._language and lang in self._tables:
            self._language = lang
            self.languageChanged.emit(lang)

    def language(self) -> str:
        return self._language

    def add_table(self, lang: str, mapping: dict) -> None:
        self._tables.setdefault(lang, {}).update(mapping)

    def t(self, key: str, *args, **kwargs) -> str:
        """翻译 key；无翻译时回退为 key 本身。"""
        text = self._tables.get(self._language, {}).get(key, key)
        if args or kwargs:
            try:
                text = text.format(*args, **kwargs)
            except (IndexError, KeyError):
                pass
        return text

    def available_languages(self) -> list:
        return list(self._tables.keys())

    @staticmethod
    def detect_system() -> str:
        """根据系统区域设置猜测语言（简化为 zh / en）。"""
        import locale
        try:
            code = locale.getdefaultlocale()[0] or "en"
        except Exception:  # noqa: BLE001
            code = "en"
        return "zh" if code.lower().startswith("zh") else "en"
