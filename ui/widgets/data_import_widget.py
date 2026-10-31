import re

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from fluent.widgets import (FluentButton, FluentCard, FluentMessageBox,
                            FluentSystemDialog, FluentTextEdit)
from fluent.window import FluentDialog
from core.data_loader import load_csv
from models.data_models import MeasurePoint


class DataImportWidget(FluentCard):
    """数据导入卡片：输入数据 / 导入 CSV。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self._setup_ui()

    def _setup_ui(self):
        title = QLabel("数据导入")
        title.setStyleSheet("font-size: 13px; font-weight: 600; background: transparent;")
        self.addWidget(title)

        btn_row = QHBoxLayout()
        self.btn_paste = FluentButton("输入数据")
        self.btn_paste.clicked.connect(self._show_input_dialog)
        self.btn_csv = FluentButton("导入 CSV")
        self.btn_csv.clicked.connect(self._load_csv)
        btn_row.addWidget(self.btn_paste)
        btn_row.addWidget(self.btn_csv)
        btn_row.addStretch(1)
        self.layout().addLayout(btn_row)

        self.info_label = QLabel("尚未导入数据")
        self.info_label.setStyleSheet("color: #9D9D9D; background: transparent; font-size: 12px;")
        self.addWidget(self.info_label)

    def _show_input_dialog(self):
        from PySide6.QtGui import QFont
        dialog = FluentDialog("输入坐标数据", width=560, height=500, parent=self.window())
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        hint = QLabel(
            "每行输入 X 和 Y，用 Tab / 逗号 / 空格 / 分号 分隔\n"
            "支持 Ctrl+Z 撤销、Ctrl+Shift+Z 重做、Ctrl+V 粘贴")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #9D9D9D; background: transparent; font-size: 12px;")
        layout.addWidget(hint)

        editor = FluentTextEdit(placeholder="100.5  200.3\n150.2  180.7\n120.0  210.5\n...")
        editor.setFont(QFont("Consolas", 11))
        layout.addWidget(editor, 1)

        preview = QLabel("")
        preview.setStyleSheet("color: #9D9D9D; background: transparent; font-size: 12px;")
        layout.addWidget(preview)

        def _update_preview():
            text = editor.toPlainText()
            count = 0
            for line in text.strip().splitlines():
                if len(_parse_line(line)) >= 2:
                    count += 1
            preview.setText(f"有效点数: {count}" if count >= 3
                            else f"有效点数: {count} (需≥3)")
            preview.setStyleSheet(
                ("color: #4ADE80; background: transparent; font-size: 12px;" if count >= 3
                 else "color: #FFB900; background: transparent; font-size: 12px;"))

        editor.textChanged.connect(_update_preview)
        _update_preview()

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_clear = FluentButton("清空")
        btn_clear.clicked.connect(editor.clear)
        btn_close = FluentButton("取消")
        btn_close.clicked.connect(dialog.reject)
        btn_apply = FluentButton("确定", variant="accent")
        btn_apply.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_clear)
        btn_row.addWidget(btn_close)
        btn_row.addWidget(btn_apply)
        layout.addLayout(btn_row)

        if dialog.exec() == FluentDialog.DialogCode.Accepted:
            pts = []
            for line in editor.toPlainText().strip().splitlines():
                nums = _parse_line(line)
                if len(nums) >= 2:
                    pts.append((nums[0], nums[1]))
            self.points = [MeasurePoint(x, y) for x, y in pts]
            self._update_info()

    def _load_csv(self):
        path = FluentSystemDialog.open_file(self.window(), "选择 CSV 文件",
                                            filters="CSV (*.csv);;所有文件 (*.*)")
        if path:
            try:
                self.points = load_csv(path)
                self._update_info()
            except Exception as e:  # noqa: BLE001
                FluentMessageBox.warning(self.window(), "导入失败", str(e))

    def _update_info(self):
        n = len(self.points)
        if n >= 3:
            self.info_label.setText(f"已导入 {n} 个测量点 ✓")
            self.info_label.setStyleSheet(
                "color: #4ADE80; background: transparent; font-size: 12px;")
        elif n > 0:
            self.info_label.setText(f"已导入 {n} 个点（至少需要 3 个）")
            self.info_label.setStyleSheet(
                "color: #FFB900; background: transparent; font-size: 12px;")
        else:
            self.info_label.setText("未解析到有效坐标")
            self.info_label.setStyleSheet(
                "color: #F87171; background: transparent; font-size: 12px;")


def _parse_line(line):
    parts = re.split(r'[\t,; ]+', line.strip())
    nums = []
    for p in parts:
        try:
            nums.append(float(p))
        except ValueError:
            break
    return nums
