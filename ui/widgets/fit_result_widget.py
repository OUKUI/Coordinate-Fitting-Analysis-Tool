from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel

from fluent.widgets import FluentButton, FluentCard, FluentComboBox, FluentLineEdit
from models.data_models import FeatureType


class FitResultWidget(FluentCard):
    feature_changed = Signal(FeatureType)
    fit_clicked = Signal()
    design_radius_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self._locked = False
        self._setup_ui()

    def _setup_ui(self):
        title = QLabel("拟合设置")
        title.setStyleSheet("font-size: 13px; font-weight: 600; background: transparent;")
        self.addWidget(title)

        self.btn_fit = FluentButton("执行拟合", variant="accent")
        self.btn_fit.clicked.connect(self.fit_clicked.emit)
        self.addWidget(self.btn_fit)

        self.addWidget(self._label("特征类型："))
        self.feature_combo = FluentComboBox(["型腔(Cavity)", "型芯(Core)"])
        self.feature_combo.currentIndexChanged.connect(self._on_change)
        self.addWidget(self.feature_combo)

        self.addWidget(self._label("拟合方法："))
        self.method_combo = FluentComboBox(["Taubin (推荐)", "Kasa (最小二乘)"])
        self.addWidget(self.method_combo)

        # ── 设计半径输入 ──
        self.addWidget(self._label("设计半径："))
        dr_row = QHBoxLayout()
        self.design_radius_input = FluentLineEdit(placeholder="输入图纸设计半径…")
        dr_row.addWidget(self.design_radius_input, 1)
        self.btn_apply_dr = FluentButton("应用")
        self.btn_apply_dr.setEnabled(False)
        self.btn_apply_dr.clicked.connect(self._apply_design_radius)
        dr_row.addWidget(self.btn_apply_dr)

        self.btn_lock = FluentButton("锁定")
        self.btn_lock.setCheckable(True)
        self.btn_lock.setMinimumWidth(64)
        self.btn_lock.toggled.connect(self._on_lock_toggled)
        dr_row.addWidget(self.btn_lock)
        self.layout().addLayout(dr_row)

        sep = QLabel("— 拟合结果 —")
        sep.setStyleSheet("color: #6E6E6E; background: transparent; padding: 4px 0;")
        self.addWidget(sep)

        self._labels = {}
        for key, txt in [("cx", "X:"), ("cy", "Y:"), ("r", "R:"),
                          ("roundness", "圆度:"), ("rmse", "RMSE:")]:
            lbl = QLabel(f"{txt} —")
            lbl.setStyleSheet("color: #9D9D9D; background: transparent; font-size: 12px;")
            self.addWidget(lbl)
            self._labels[key] = lbl

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #9D9D9D; background: transparent; font-size: 12px;")
        return lbl

    def _on_change(self, idx):
        ft = FeatureType.CAVITY if idx == 0 else FeatureType.CORE
        self.feature_changed.emit(ft)

    def get_feature_type(self):
        return FeatureType.CAVITY if self.feature_combo.currentIndex() == 0 else FeatureType.CORE

    def get_fitting_method(self):
        return "taubin" if self.method_combo.currentIndex() == 0 else "kasa"

    def _apply_design_radius(self):
        try:
            val = float(self.design_radius_input.text().strip())
            if val > 0:
                self.design_radius_changed.emit(val)
        except ValueError:
            pass

    def _on_lock_toggled(self, checked):
        self._locked = checked
        self.design_radius_input.setReadOnly(checked)
        self.btn_lock.setText("已锁定" if checked else "锁定")
        self.btn_lock.variant = "accent" if checked else "standard"
        self.btn_lock.update()
        if checked:
            val = self.get_design_radius()
            if val and val > 0:
                self.design_radius_changed.emit(val)

    def get_design_radius(self):
        try:
            return float(self.design_radius_input.text().strip())
        except ValueError:
            return None

    def enable_design_radius(self, fitted_radius):
        """拟合后预填拟合半径并启用应用按钮。

        若设计半径已锁定，则保留用户输入值并返回它以便自动重新应用，
        否则用拟合半径覆盖输入框并返回 None。
        """
        self.btn_apply_dr.setEnabled(True)
        if self._locked:
            return self.get_design_radius()
        self.design_radius_input.setText(f"{fitted_radius:.4f}")
        return None

    def update_results(self, result, unit="mm", design_radius=None):
        factor = 1000.0 if unit == "μm" else 1.0
        r_text = f"R(拟合): {result.fitted.radius:.4f}"
        if design_radius is not None:
            r_text += f"  |  设计: {design_radius:.4f}"
        vals = {"cx": f"X: {result.fitted.cx:.4f}",
                "cy": f"Y: {result.fitted.cy:.4f}",
                "r": r_text,
                "roundness": f"圆度: {result.roundness * factor:.4f} {unit}",
                "rmse": f"RMSE: {result.fitted.rmse * factor:.6f} {unit}"}
        for key, text in vals.items():
            self._labels[key].setText(text)
            self._labels[key].setStyleSheet(
                "color: #FFFFFF; background: transparent; font-size: 12px;")
