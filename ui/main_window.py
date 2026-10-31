import json

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from fluent.widgets import (FluentCommandBar, FluentMessageBox, FluentSplitter,
                            FluentSystemDialog, FluentToast)
from fluent.window import FluentWindow

from ui.widgets.data_import_widget import DataImportWidget
from ui.widgets.fit_result_widget import FitResultWidget
from ui.widgets.chart_widget import ChartWidget
from ui.widgets.advice_table_widget import AdviceTableWidget

from core.circle_fitting import fit_least_squares, fit_taubin
from core.deviation_analysis import analyze
from core.mold_advisor import apply_advice, get_advice_table
from core.report_generator import generate_and_save
from models.data_models import FeatureType, MeasurePoint, FittedCircle


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__(title="注塑件模具修模分析工具", width=1360, height=860,
                         maximized=True)
        self._result = None
        self._design_radius = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.data_import = DataImportWidget()
        self.fit_result = FitResultWidget()
        self.chart = ChartWidget()
        self.advice_table = AdviceTableWidget()

        main_page = QWidget()
        main_page.setObjectName("main_page")
        main_layout = QVBoxLayout(main_page)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = FluentSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self.data_import)
        left_layout.addWidget(self.fit_result)
        left_layout.addWidget(self.advice_table, 1)
        splitter.addWidget(left)
        left.setMinimumWidth(300)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.chart)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 5)
        main_layout.addWidget(splitter, 1)

        # 工具栏
        bar = FluentCommandBar()
        self._btns = {}
        self._btns["pdf"] = bar.add_action("导出 PDF", on_clicked=self._export_pdf)
        self._btns["csv"] = bar.add_action("导出 CSV", on_clicked=self._export_csv)
        bar.add_separator()
        self._btns["save"] = bar.add_action("保存会话", on_clicked=self._save_session)
        self._btns["load"] = bar.add_action("加载会话", on_clicked=self._load_session)
        bar.add_separator()
        self._btns["about"] = bar.add_action("关于", on_clicked=self._show_about)
        bar.add_stretch()
        main_layout.addWidget(bar)

        self.setCentralWidget(main_page)

    def _connect_signals(self):
        self.fit_result.fit_clicked.connect(self._run_analysis)
        self.fit_result.feature_changed.connect(self._on_feature_change)
        self.fit_result.design_radius_changed.connect(self._apply_design_radius)
        self.advice_table.point_highlighted.connect(self.chart.highlight_point)
        self.chart.unit_changed.connect(self._on_unit_change)

    def _run_analysis(self):
        pts = self.data_import.points
        if len(pts) < 3:
            FluentMessageBox.warning(self, "提示", "请先导入至少 3 个测量点")
            return
        method = self.fit_result.get_fitting_method()
        if method == "taubin":
            fitted = fit_taubin(pts)
        else:
            fitted = fit_least_squares(pts)
        if fitted is None:
            FluentMessageBox.warning(self, "错误", "拟合失败")
            return
        ft = self.fit_result.get_feature_type()
        self._result = analyze(pts, fitted, ft)
        apply_advice(self._result.polar_points, ft)
        unit = self.chart.get_unit()
        self.fit_result.update_results(self._result, unit)
        self.chart.set_result(self._result)
        self.advice_table.update_data(self._result.polar_points, unit)
        locked_radius = self.fit_result.enable_design_radius(fitted.radius)
        self._enable_actions(True)
        if locked_radius:
            self._apply_design_radius(locked_radius, notify=False)
        FluentToast.popup(self, "拟合完成", kind="success")

    def _apply_design_radius(self, r_design, notify=True):
        if self._result is None:
            return
        self._design_radius = r_design
        unit = self.chart.get_unit()
        errors = []
        for pp in self._result.polar_points:
            pp.delta_r = pp.r - r_design
            errors.append(pp.delta_r)
        self._result.roundness = float(
            max(pp.r for pp in self._result.polar_points) -
            min(pp.r for pp in self._result.polar_points))
        self._result.peak_error = float(np.max(errors))
        self._result.valley_error = float(np.min(errors))
        ft = self._result.feature_type
        apply_advice(self._result.polar_points, ft)
        self.fit_result.update_results(self._result, unit, r_design)
        self.chart.set_result(self._result, design_radius=r_design)
        self.advice_table.update_data(self._result.polar_points, unit)
        if notify:
            FluentToast.popup(self, f"已按设计半径 {r_design:.4f} 重新计算偏差")

    def _on_feature_change(self, ft):
        if self._result is not None:
            self._result.feature_type = ft
            apply_advice(self._result.polar_points, ft)
            unit = self.chart.get_unit()
            self.advice_table.update_data(self._result.polar_points, unit)

    def _on_unit_change(self, unit):
        if self._result is not None:
            self.fit_result.update_results(self._result, unit, self._design_radius)
            self.advice_table.update_data(self._result.polar_points, unit)

    def _enable_actions(self, on):
        for btn in self._btns.values():
            btn.setEnabled(on)

    def _show_about(self):
        FluentMessageBox.info(
            self, "关于",
            "注塑件模具修模分析工具\n"
            "Fluent Design · Dark Mode\n\n"
            "如有问题或建议，欢迎联系:\n"
            "kui_ou@outlook.com")

    def _export_pdf(self):
        if not self._result:
            return
        path = FluentSystemDialog.save_file(self, "保存 PDF", filters="PDF (*.pdf)")
        if not path:
            return
        try:
            svg_data = self.chart.render_export_svg()
            if svg_data is None:
                FluentMessageBox.warning(self, "导出失败", "无数据可导出")
                return
            generate_and_save(self._result, svg_data, path)
            FluentMessageBox.info(self, "完成", f"PDF 已保存: {path}")
        except Exception as e:  # noqa: BLE001
            FluentMessageBox.warning(self, "导出失败", str(e))

    def _export_csv(self):
        if not self._result:
            return
        path = FluentSystemDialog.save_file(self, "保存 CSV", filters="CSV (*.csv)")
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["no", "angle", "delta_r", "x", "y"],
                                   extrasaction="ignore")
                w.writeheader()
                w.writerows(get_advice_table(self._result.polar_points))
            FluentMessageBox.info(self, "完成", f"CSV 已保存: {path}")
        except Exception as e:  # noqa: BLE001
            FluentMessageBox.warning(self, "导出失败", str(e))

    def _save_session(self):
        if not self._result:
            return
        path = FluentSystemDialog.save_file(self, "保存会话", filters="JSON (*.json)")
        if not path:
            return
        try:
            data = {
                "result": self._result.to_dict(),
                "points": [{"x": p.x, "y": p.y} for p in self._result.points],
                "polar": [{"theta": p.theta, "delta_r": p.delta_r, "advice": p.advice}
                          for p in self._result.polar_points],
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            FluentMessageBox.info(self, "完成", "会话已保存")
        except Exception as e:  # noqa: BLE001
            FluentMessageBox.warning(self, "保存失败", str(e))

    def _load_session(self):
        path = FluentSystemDialog.open_file(self, "加载会话", filters="JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pts = [MeasurePoint(p["x"], p["y"]) for p in data["points"]]
            rd = data["result"]
            ft = FeatureType.CAVITY if rd.get("feature_type") == "型腔" else FeatureType.CORE
            fitted = FittedCircle(rd["cx"], rd["cy"], rd["radius"], rd.get("rmse", 0))
            self._result = analyze(pts, fitted, ft)
            self._result.roundness = rd["roundness"]
            self._result.peak_error = rd["peak_error"]
            self._result.valley_error = rd["valley_error"]
            apply_advice(self._result.polar_points, ft)
            unit = self.chart.get_unit()
            self.fit_result.update_results(self._result, unit, self._design_radius)
            self.chart.set_result(self._result, design_radius=self._design_radius)
            self.advice_table.update_data(self._result.polar_points, unit)
            self._enable_actions(True)
            FluentMessageBox.info(self, "完成", "会话已加载")
        except Exception as e:  # noqa: BLE001
            FluentMessageBox.warning(self, "加载失败", str(e))
