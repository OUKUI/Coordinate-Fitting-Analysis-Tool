import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QCheckBox, QLabel, QComboBox
from PySide6.QtCore import Qt, Signal

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartWidget(QWidget):
    unit_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = None
        self._view_mode = "polar"
        self._k = 20.0
        self._show_fitted = True
        self._show_profile = True
        self._show_center = True
        self._show_labels = True
        self._show_dist_labels = False
        self._unit = "mm"
        self._highlight_idx = -1
        self._design_radius = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.fig = Figure(tight_layout=True, facecolor="#12121e")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: #12121e;")

        ctrl = QHBoxLayout()
        ctrl.setSpacing(4)

        lbl_k = QLabel("\u653e\u5927 k:")
        lbl_k.setStyleSheet("color: #9898b8; font-size: 9pt;")
        ctrl.addWidget(lbl_k)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 500)
        self.slider.setValue(20)
        self.slider.valueChanged.connect(self._on_slider)
        ctrl.addWidget(self.slider)

        self.lbl_k = QLabel("20")
        self.lbl_k.setStyleSheet("color: #e8e8f0; font-size: 9pt;")
        ctrl.addWidget(self.lbl_k)

        sep = QLabel("|")
        sep.setStyleSheet("color: #333355; font-size: 11pt;")
        ctrl.addWidget(sep)

        self.view_combo = QComboBox()
        self.view_combo.addItems(["\u6781\u5750\u6807\u504f\u5dee", "\u5e73\u9762\u5750\u6807", "\u4e09\u9762\u677f"])
        self.view_combo.currentIndexChanged.connect(self._on_view_change)
        self.view_combo.setStyleSheet("""
            QComboBox { background: #252542; color: #e8e8f0;
                       border: none; padding: 3px 8px;
                       border-radius: 3px; font-size: 9pt; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #1e1e36; color: #e8e8f0;
                                         selection-background-color: #3b82f6; }
        """)
        ctrl.addWidget(self.view_combo)

        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #333355; font-size: 11pt;")
        ctrl.addWidget(sep2)

        lbl_unit = QLabel("单位:")
        lbl_unit.setStyleSheet("color: #9898b8; font-size: 9pt;")
        ctrl.addWidget(lbl_unit)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["mm", "\u03bcm"])
        self.unit_combo.currentIndexChanged.connect(self._on_unit_change)
        self.unit_combo.setStyleSheet("""
            QComboBox { background: #252542; color: #e8e8f0;
                       border: none; padding: 3px 8px;
                       border-radius: 3px; font-size: 9pt; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #1e1e36; color: #e8e8f0;
                                         selection-background-color: #3b82f6; }
        """)
        ctrl.addWidget(self.unit_combo)

        lbl0 = QLabel("0\u00b0:")
        lbl0.setStyleSheet("color: #9898b8; font-size: 9pt;")
        ctrl.addWidget(lbl0)

        self._zero_combo = QComboBox()
        self._zero_combo.addItems(["\u53f3(3\u70b9)", "\u4e0a(12\u70b9)", "\u5de6(9\u70b9)", "\u4e0b(6\u70b9)"])
        self._zero_combo.currentIndexChanged.connect(lambda: self._render())
        self._zero_combo.setStyleSheet("""
            QComboBox { background: #252542; color: #e8e8f0;
                       border: none; padding: 3px 6px;
                       border-radius: 3px; font-size: 9pt; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #1e1e36; color: #e8e8f0;
                                         selection-background-color: #3b82f6; }
        """)
        ctrl.addWidget(self._zero_combo)

        ctrl.addStretch()
        layout.addLayout(ctrl)

        toggles = QHBoxLayout()
        toggles.setSpacing(6)
        self._checkboxes = {}
        for key, txt in [("fitted", "\u62df\u5408\u5706"), ("profile", "\u5b9e\u6d4b\u8f6e\u5ed3"),
                          ("center", "\u5706\u5fc3"), ("labels", "\u504f\u5dee\u6807\u6ce8"),
                          ("dist", "\u8ddd\u5706\u5fc3\u8ddd")]:
            cb = QCheckBox(txt)
            cb.setChecked(True)
            cb.stateChanged.connect(lambda _, k=key: self._toggle(k))
            cb.setStyleSheet("color: #e8e8f0; font-size: 8pt;")
            toggles.addWidget(cb)
            self._checkboxes[key] = cb
        self._checkboxes["dist"].setChecked(False)
        toggles.addStretch()
        layout.addLayout(toggles)

        layout.addWidget(self.canvas)

    def set_result(self, result, design_radius=None):
        self._result = result
        self._design_radius = design_radius
        self._render()

    def render_export_svg(self):
        """Render current view with white background for PDF export.
        Returns an RGB numpy array (H, W, 3)."""
        import matplotlib
        matplotlib.use("QtAgg")
        import matplotlib.pyplot as plt

        r = self._result
        if r is None:
            return None

        polar = r.polar_points
        thetas = np.array([p.theta for p in polar])
        deltas = np.array([p.delta_r for p in polar])
        thetas_loop = np.append(thetas, thetas[0] + 2 * np.pi)
        deltas_loop = np.append(deltas, deltas[0])

        unit_factor = 1000.0 if self._unit == "\u03bcm" else 1.0
        max_err = max(abs(r.peak_error), abs(r.valley_error), 1e-6)
        rlim = max_err * 1.4 * (self._k / 20.0)
        offset = rlim

        # ── Light colour palette ──────────────────────────────────────────
        BG = "#ffffff"
        GRID = "#e0e0e0"
        TEXT = "#333333"
        MUTED = "#888888"
        PROFILE_LINE = "#1976D2"
        PROFILE_DOT = "#64B5F6"
        POS_FILL = "#FFCDD2"
        NEG_FILL = "#C8E6C9"
        POS_LINE = "#F44336"
        NEG_LINE = "#4CAF50"
        FIT_CIRCLE = "#aaaaaa"

        # Respect UI zero-direction setting
        zero_map = {"\u53f3(3\u70b9)": 0, "\u4e0a(12\u70b9)": 90,
                     "\u5de6(9\u70b9)": 180, "\u4e0b(6\u70b9)": 270}
        theta_zero = np.radians(zero_map.get(self._zero_combo.currentText(), 0))

        if self._view_mode == "xy":
            fig = plt.figure(figsize=(9, 7), facecolor=BG)
            ax = fig.add_subplot(111)
            ax.set_facecolor(BG)
            pts = r.points
            xs, ys = [p.x for p in pts], [p.y for p in pts]

            if self._design_radius is not None and self._design_radius != r.fitted.radius:
                dc = plt.Circle((r.fitted.cx, r.fitted.cy), self._design_radius,
                                fill=False, linestyle="-", color="#1976D2", lw=1.8)
                ax.add_patch(dc)
                ax.annotate(f"Design R={self._design_radius:.3f}",
                            xy=(0.98, 0.97), xycoords="axes fraction",
                            fontsize=9, fontweight="bold", color="#1976D2",
                            ha="right", va="top",
                            bbox=dict(boxstyle="round,pad=0.3", fc="#e3f2fd",
                                      ec="#1976D2", lw=1))
            circle = plt.Circle((r.fitted.cx, r.fitted.cy), r.fitted.radius,
                                fill=False, linestyle="--", color=FIT_CIRCLE, lw=1.5)
            ax.add_patch(circle)
            opolar = r.polar_points
            oxs = [p.x for p in opolar] + [opolar[0].x]
            oys = [p.y for p in opolar] + [opolar[0].y]
            ax.plot(oxs, oys, "-", color=PROFILE_LINE, lw=2)
            ax.scatter(xs, ys, c=PROFILE_DOT, s=15, zorder=5)
            ax.scatter([r.fitted.cx], [r.fitted.cy], c="#FF9800", marker="+",
                       s=80, lw=2, zorder=6)
            ax.set_aspect("equal")
            ax.set_title(f"XY View  [R={r.fitted.radius:.2f}]", color=TEXT, fontsize=12)
            # +/- comparison box
            pu = r.peak_error * unit_factor
            vu = r.valley_error * unit_factor
            ax.annotate(f"+{pu:.3f} {self._unit}\n{vu:.3f} {self._unit}",
                        xy=(0.95, 0.95), xycoords="axes fraction",
                        fontsize=9, fontweight="bold", ha="right", va="top",
                        color="#333",
                        bbox=dict(boxstyle="round,pad=0.4", fc="#fff5f5",
                                  ec="#F44336", lw=1.5))
            # Peak / valley point annotations on XY
            polar = r.polar_points
            peak_idx = np.argmax(deltas)
            valley_idx = np.argmin(deltas)
            for idx, val, clr in [(peak_idx, r.peak_error, POS_LINE),
                                   (valley_idx, r.valley_error, NEG_LINE)]:
                px, py = polar[idx].x, polar[idx].y
                ax.annotate(f"{val * unit_factor:+.3f}",
                            xy=(px, py), fontsize=7, fontweight="bold",
                            color=clr, xytext=(8, 8),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                      ec=clr, lw=0.8))
            ax.tick_params(colors=MUTED, labelsize=8)
            ax.grid(True, alpha=0.3, color=GRID)

        elif self._view_mode == "full":
            fig = plt.figure(figsize=(14, 9), facecolor=BG)
            gs = fig.add_gridspec(2, 2, width_ratios=[1, 1], height_ratios=[3, 1],
                                   hspace=0.28, wspace=0.32)

            # Top-left: profile
            ax1 = fig.add_subplot(gs[0, 0], polar=True)
            ax1.set_facecolor(BG)
            ax1.set_theta_offset(theta_zero)
            profile_r = r.fitted.radius + deltas
            if self._design_radius is not None and self._design_radius != r.fitted.radius:
                ax1.plot(thetas_loop, np.full_like(thetas_loop, self._design_radius),
                         "-", color="#60a5fa", lw=1.5, alpha=0.7)
            ax1.plot(thetas_loop, np.full_like(thetas_loop, r.fitted.radius),
                     "--", color=FIT_CIRCLE, lw=1, alpha=0.7)
            ax1.plot(thetas_loop, r.fitted.radius + deltas_loop, "o-",
                     color=PROFILE_LINE, lw=2, ms=4)
            ax1.fill(thetas_loop, r.fitted.radius + deltas_loop,
                     alpha=0.1, color=PROFILE_LINE)
            ax1.set_title(f"Profile  [R={r.fitted.radius:.2f}]",
                          color=TEXT, fontsize=10, pad=10)
            ax1.tick_params(colors=MUTED, labelsize=7)
            ax1.grid(True, alpha=0.3, color=GRID)

            # Peak / valley markers on profile
            peak_idx = np.argmax(deltas)
            valley_idx = np.argmin(deltas)
            for idx, val, clr in [(peak_idx, r.peak_error, POS_LINE),
                                   (valley_idx, r.valley_error, NEG_LINE)]:
                ax1.annotate(f"{val * unit_factor:+.3f}",
                             xy=(thetas[idx], profile_r[idx]),
                             fontsize=7, fontweight="bold", color=clr,
                             xytext=(6, 6), textcoords="offset points",
                             bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                       ec=clr, lw=0.7))

            # Distance labels for profile
            if self._show_dist_labels:
                r_max = r.fitted.radius + max(abs(r.peak_error), abs(r.valley_error))
                outer_r = r_max * 1.25
                label_gap = r_max * 0.06
                thetas_deg = np.degrees(thetas) % 360
                closest_0 = np.argmin(np.minimum(thetas_deg, 360 - thetas_deg))
                for k in range(len(thetas)):
                    idx = (closest_0 + k) % len(thetas)
                    t = thetas[idx]
                    r_val = profile_r[idx]
                    stagger = (k % 5) * label_gap * 0.5
                    lr = outer_r + stagger
                    ax1.plot([t, t], [r_val, lr], "-", color=GRID, lw=0.3, alpha=0.5)
                    ax1.annotate(f"#{k+1} {r.polar_points[idx].r:.3f}",
                                 xy=(t, lr), fontsize=4, color=MUTED,
                                 ha="center", va="bottom")
                ax1.set_ylim(0, outer_r + label_gap * 3)

            # Top-right: deviation polar
            ax2 = fig.add_subplot(gs[0, 1], polar=True)
            ax2.set_facecolor(BG)
            ax2.set_theta_offset(theta_zero)
            dev_shift = deltas + offset
            dev_shift_loop = deltas_loop + offset
            ax2.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.25,
                             where=(deltas_loop >= 0), color=POS_FILL)
            ax2.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.25,
                             where=(deltas_loop < 0), color=NEG_FILL)
            ax2.plot(thetas_loop, dev_shift_loop, "-", color=PROFILE_LINE, lw=2)
            ax2.plot(thetas_loop, dev_shift_loop, ".", color=PROFILE_DOT, ms=4)
            fitted_r = offset + (r.fitted.radius - self._design_radius
                        if self._design_radius else 0)
            ax2.plot(thetas_loop, np.full_like(thetas_loop, fitted_r), "--",
                     color=FIT_CIRCLE, lw=1, alpha=0.6)
            if self._design_radius is not None and self._design_radius != r.fitted.radius:
                ax2.plot(thetas_loop, np.full_like(thetas_loop, offset), "-",
                         color="#1976D2", lw=1.5, alpha=0.7)
            ax2.plot(thetas_loop, np.full_like(thetas_loop, r.peak_error + offset),
                     ":", color=POS_LINE, lw=0.8)
            ax2.plot(thetas_loop, np.full_like(thetas_loop, r.valley_error + offset),
                     ":", color=NEG_LINE, lw=0.8)
            ax2.set_ylim(0, 2 * offset)
            tick_vals = np.linspace(0, 2 * offset, 5)
            ax2.set_yticks(tick_vals)
            ax2.set_yticklabels([f"{(v - offset) * unit_factor:.1f}" for v in tick_vals],
                                color=MUTED, fontsize=6)

            # Distance labels
            if self._show_dist_labels:
                outer_r = 2 * offset
                label_gap = outer_r * 0.20
                thetas_deg = np.degrees(thetas) % 360
                closest_0 = np.argmin(np.minimum(thetas_deg, 360 - thetas_deg))
                for k in range(len(thetas)):
                    idx = (closest_0 + k) % len(thetas)
                    t = thetas[idx]
                    r_val = dev_shift[idx]
                    stagger = (k % 5) * label_gap * 0.5
                    lr = outer_r + stagger
                    ax2.plot([t, t], [r_val, lr], "-", color=GRID, lw=0.3, alpha=0.5)
                    ax2.annotate(f"#{k+1} {r.polar_points[idx].r:.3f}",
                                 xy=(t, lr), fontsize=4, color=MUTED,
                                 ha="center", va="bottom")
                ax2.set_ylim(0, outer_r + label_gap * 3)

            ax2.set_title(f"Deviation (polar)  [\u00b1{rlim * unit_factor:.2f}{self._unit}]",
                          color=TEXT, fontsize=10, pad=10)
            # +/- comparison box
            pu = r.peak_error * unit_factor
            vu = r.valley_error * unit_factor
            ax2.annotate(f"+{pu:.3f} {self._unit}\n{vu:.3f} {self._unit}",
                         xy=(0.92, 0.92), xycoords="axes fraction",
                         fontsize=8, fontweight="bold", ha="right", va="top",
                         color="#333",
                         bbox=dict(boxstyle="round,pad=0.3", fc="#fff5f5",
                                   ec="#F44336", lw=1.2))
            # Peak / valley point annotations
            peak_idx = np.argmax(deltas)
            valley_idx = np.argmin(deltas)
            for idx, val, clr in [(peak_idx, r.peak_error, POS_LINE),
                                   (valley_idx, r.valley_error, NEG_LINE)]:
                ax2.annotate(f"{val * unit_factor:+.3f}",
                             xy=(thetas[idx], dev_shift[idx]),
                             fontsize=7, fontweight="bold", color=clr,
                             xytext=(6, 6), textcoords="offset points",
                             bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                       ec=clr, lw=0.7))
            ax2.tick_params(colors=MUTED, labelsize=7)
            ax2.grid(True, alpha=0.25, color=GRID)

            # Bottom: linear deviation
            ax3 = fig.add_subplot(gs[1, :])
            ax3.set_facecolor(BG)
            lin_thetas = np.where(thetas < 0, thetas + 2 * np.pi, thetas)
            lin_order = np.argsort(lin_thetas)
            lt = np.degrees(lin_thetas[lin_order])
            ld = deltas[lin_order] * unit_factor
            ax3.axhline(0, color=GRID, lw=1, ls="--", alpha=0.7)
            ax3.fill_between(lt, ld, 0, alpha=0.2, where=(ld >= 0), color=POS_FILL)
            ax3.fill_between(lt, ld, 0, alpha=0.2, where=(ld < 0), color=NEG_FILL)
            ax3.plot(lt, ld, "-", color=PROFILE_LINE, lw=2)
            ax3.plot(lt, ld, ".", color=PROFILE_DOT, ms=5)
            ax3.axhline(r.peak_error * unit_factor, color=POS_LINE, lw=0.7, ls=":")
            ax3.axhline(r.valley_error * unit_factor, color=NEG_LINE, lw=0.7, ls=":")
            ax3.set_xlim(-5, 365)
            ax3.set_xticks([0, 90, 180, 270, 360])
            ax3.set_title(f"Deviation (linear)  [{self._unit}]", color=TEXT, fontsize=11)
            ax3.set_xlabel("Angle (\u00b0)", color=MUTED, fontsize=9)
            ax3.set_ylabel(f"Error ({self._unit})", color=MUTED, fontsize=9)
            ax3.tick_params(colors=MUTED, labelsize=7)
            ax3.grid(True, alpha=0.25, color=GRID)

            # Summary footer
            ru = r.roundness * unit_factor
            pu = r.peak_error * unit_factor
            vu = r.valley_error * unit_factor
            summary = (
                f"C: ({r.fitted.cx:.3f}, {r.fitted.cy:.3f})  "
                f"R: {r.fitted.radius:.3f}  "
                f"Roundness: {ru:.3f}{self._unit}  "
                f"Peak: +{pu:.4f}  Valley: {vu:.4f}  "
                f"RMSE: {r.fitted.rmse * unit_factor:.5f}{self._unit}"
            )
            fig.text(0.5, 0.01, summary, ha="center", va="bottom",
                     color=MUTED, fontsize=8)
            fig.tight_layout(rect=[0, 0.04, 1, 1])

        else:  # polar (default)
            fig = plt.figure(figsize=(9, 7), facecolor=BG)
            ax = fig.add_subplot(111, polar=True)
            ax.set_facecolor(BG)
            ax.set_theta_offset(theta_zero)
            dev_shift = deltas + offset
            dev_shift_loop = deltas_loop + offset
            ax.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.25,
                            where=(deltas_loop >= 0), color=POS_FILL)
            ax.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.25,
                            where=(deltas_loop < 0), color=NEG_FILL)
            ax.plot(thetas_loop, dev_shift_loop, "-", color=PROFILE_LINE, lw=2)
            ax.plot(thetas_loop, dev_shift_loop, ".", color=PROFILE_DOT, ms=5)
            fitted_r = offset + (r.fitted.radius - self._design_radius
                        if self._design_radius else 0)
            ax.plot(thetas_loop, np.full_like(thetas_loop, fitted_r), "--",
                    color=FIT_CIRCLE, lw=1, alpha=0.6)
            if self._design_radius is not None and self._design_radius != r.fitted.radius:
                ax.plot(thetas_loop, np.full_like(thetas_loop, offset), "-",
                        color="#1976D2", lw=1.8, alpha=0.8)
                ax.annotate(f"Design R={self._design_radius:.3f}",
                            xy=(0.92, 0.95), xycoords="axes fraction",
                            fontsize=8, fontweight="bold", color="#1976D2",
                            ha="right", va="top",
                            bbox=dict(boxstyle="round,pad=0.25", fc="#e3f2fd",
                                      ec="#1976D2", lw=0.8))
            ax.plot(thetas_loop, np.full_like(thetas_loop, r.peak_error + offset),
                    ":", color=POS_LINE, lw=0.8)
            ax.plot(thetas_loop, np.full_like(thetas_loop, r.valley_error + offset),
                    ":", color=NEG_LINE, lw=0.8)
            ax.set_ylim(0, 2 * offset)
            tick_vals = np.linspace(0, 2 * offset, 5)
            ax.set_yticks(tick_vals)
            ax.set_yticklabels([f"{(v - offset) * unit_factor:.1f}" for v in tick_vals],
                               color=MUTED, fontsize=7)

            # Distance labels
            if self._show_dist_labels:
                outer_r = 2 * offset
                label_gap = outer_r * 0.20
                thetas_deg = np.degrees(thetas) % 360
                closest_0 = np.argmin(np.minimum(thetas_deg, 360 - thetas_deg))
                for k in range(len(thetas)):
                    idx = (closest_0 + k) % len(thetas)
                    t = thetas[idx]
                    r_val = dev_shift[idx]
                    stagger = (k % 5) * label_gap * 0.5
                    lr = outer_r + stagger
                    ax.plot([t, t], [r_val, lr], "-", color=GRID, lw=0.4, alpha=0.5)
                    ax.annotate(f"#{k+1} {r.polar_points[idx].r:.3f}",
                                xy=(t, lr), fontsize=4, color=MUTED,
                                ha="center", va="bottom")
                ax.set_ylim(0, outer_r + label_gap * 3)

            ru = r.roundness * unit_factor
            pu = r.peak_error * unit_factor
            vu = r.valley_error * unit_factor
            info = (f"Deviation [k={self._k}]  Roundness={ru:.2f}{self._unit}  "
                    f"Peak=+{pu:.2f}  Valley={vu:.2f}")
            ax.set_title(info, color=TEXT, fontsize=11, pad=14)

            # +/- comparison box
            ax.annotate(f"+{pu:.3f} {self._unit}\n{vu:.3f} {self._unit}",
                        xy=(0.95, 0.90), xycoords="axes fraction",
                        fontsize=9, fontweight="bold", ha="right", va="top",
                        color="#333",
                        bbox=dict(boxstyle="round,pad=0.4", fc="#fff5f5",
                                  ec="#F44336", lw=1.5))

            # Peak / valley point annotations
            peak_idx = np.argmax(deltas)
            valley_idx = np.argmin(deltas)
            for idx, val, clr in [(peak_idx, r.peak_error, POS_LINE),
                                   (valley_idx, r.valley_error, NEG_LINE)]:
                ax.annotate(f"{val * unit_factor:+.3f}",
                            xy=(thetas[idx], dev_shift[idx]),
                            fontsize=7, fontweight="bold", color=clr,
                            xytext=(8, 8), textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.2", fc="white",
                                      ec=clr, lw=0.8))
            ax.tick_params(colors=MUTED, labelsize=8)
            ax.grid(True, alpha=0.3, color=GRID)

        import io
        svg_buf = io.BytesIO()
        fig.savefig(svg_buf, format="svg", bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        svg_buf.seek(0)
        return svg_buf.read().decode("utf-8")

    def highlight_point(self, idx):
        """Highlight the point at the given index in the chart."""
        self._highlight_idx = idx
        self._render()

    def _on_slider(self, val):
        self._k = val
        self.lbl_k.setText(str(val))
        self._render()

    def _on_view_change(self, idx):
        modes = ["polar", "xy", "full"]
        self._view_mode = modes[idx] if idx < len(modes) else "polar"
        self._render()

    def _on_unit_change(self, idx):
        self._unit = "mm" if idx == 0 else "\u03bcm"
        self.unit_changed.emit(self._unit)
        self._render()

    def get_unit(self):
        return self._unit

    def set_unit(self, unit_str):
        """Set unit from external caller (syncs combo)."""
        if unit_str != self._unit:
            self._unit = unit_str
            self.unit_combo.blockSignals(True)
            self.unit_combo.setCurrentIndex(0 if unit_str == "mm" else 1)
            self.unit_combo.blockSignals(False)
            self._render()

    def _toggle(self, name):
        state = self._checkboxes[name].isChecked()
        m = {"fitted": "_show_fitted", "profile": "_show_profile", "center": "_show_center",
             "labels": "_show_labels", "dist": "_show_dist_labels"}
        setattr(self, m[name], state)
        self._render()

    def _render(self):
        self.fig.clear()
        if not self._result:
            self.canvas.draw_idle()
            return

        r = self._result
        polar = r.polar_points
        thetas = np.array([p.theta for p in polar])
        deltas = np.array([p.delta_r for p in polar])
        thetas_loop = np.append(thetas, thetas[0] + 2 * np.pi)
        deltas_loop = np.append(deltas, deltas[0])

        self.canvas.draw_idle()

    def _render(self):
        self.fig.clear()
        if not self._result:
            self.canvas.draw_idle()
            return

        r = self._result
        polar = r.polar_points
        thetas = np.array([p.theta for p in polar])
        deltas = np.array([p.delta_r for p in polar])
        thetas_loop = np.append(thetas, thetas[0] + 2 * np.pi)
        deltas_loop = np.append(deltas, deltas[0])

        if self._view_mode == "polar":
            self._render_polar(thetas, deltas, thetas_loop, deltas_loop, r)
        elif self._view_mode == "xy":
            self._render_xy(r)
        else:
            self._render_full(thetas, deltas, thetas_loop, deltas_loop, r)

        self.canvas.draw_idle()

    def _render_polar(self, thetas, deltas, thetas_loop, deltas_loop, r):
        ax = self.fig.add_subplot(111, polar=True)
        ax.set_facecolor("#12121e")
        zero_map = {"\u53f3(3\u70b9)": 0, "\u4e0a(12\u70b9)": 90,
                     "\u5de6(9\u70b9)": 180, "\u4e0b(6\u70b9)": 270}
        ax.set_theta_offset(np.radians(zero_map.get(self._zero_combo.currentText(), 0)))

        max_err = max(abs(r.peak_error), abs(r.valley_error), 1e-6)
        rlim = max_err * 1.4 * (self._k / 20.0)
        offset = rlim
        dev_shift = deltas + offset

        if self._show_profile:
            dev_shift_loop = deltas_loop + offset
            ax.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.3,
                            where=(deltas_loop >= 0), color="#f87171")
            ax.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.3,
                            where=(deltas_loop < 0), color="#4ade80")
            ax.plot(thetas_loop, dev_shift_loop, "-", color="#93c5fd", lw=1.5)
            ax.plot(thetas_loop, dev_shift_loop, ".", color="#e0e7ff", ms=3)

        if self._show_fitted:
            # Fitted circle line: shifts when design radius is the reference
            fitted_r = offset + (r.fitted.radius - self._design_radius
                        if self._design_radius else 0)
            ax.plot(thetas_loop, np.full_like(thetas_loop, fitted_r), "--",
                    color="#555577", lw=1, alpha=0.5)
        # Design circle = new zero-reference (solid blue)
        if self._design_radius is not None and self._design_radius != r.fitted.radius:
            ax.plot(thetas_loop, np.full_like(thetas_loop, offset), "-",
                    color="#60a5fa", lw=1.5, alpha=0.8)

        if self._show_center:
            ax.plot(thetas_loop, np.full_like(thetas_loop, r.peak_error + offset),
                    ":", color="#f87171", lw=0.6)
            ax.plot(thetas_loop, np.full_like(thetas_loop, r.valley_error + offset),
                    ":", color="#4ade80", lw=0.6)

        if self._show_labels:
            self._annotate_extremes(ax, thetas, deltas, offset, r)

        # Highlight selected point (linked from advice table)
        if self._highlight_idx >= 0 and self._highlight_idx < len(thetas):
            ax.plot(thetas[self._highlight_idx], dev_shift[self._highlight_idx],
                    'o', color='#fbbf24', ms=10, markeredgecolor='#ffffff',
                    markeredgewidth=1.5, zorder=10)

        if self._show_dist_labels and hasattr(r, 'polar_points'):
            n = len(thetas)
            outer_r = 2 * offset
            label_gap = outer_r * 0.20
            thetas_deg = np.degrees(thetas) % 360
            closest_0 = np.argmin(np.minimum(thetas_deg, 360 - thetas_deg))
            for k in range(n):
                idx = (closest_0 + k) % n
                t = thetas[idx]
                r_val = dev_shift[idx]
                stagger = (k % 5) * label_gap * 0.5
                label_r = outer_r + stagger
                ax.plot([t, t], [r_val, label_r], "-",
                        color="#6b6b8a", lw=0.3, alpha=0.35)
                ax.annotate(f"#{k + 1} {r.polar_points[idx].r:.3f}",
                            xy=(t, label_r), fontsize=4.5,
                            color="#6b6b8a", ha="center", va="bottom")
            ax.set_ylim(0, outer_r + label_gap * 3)
        else:
            ax.set_ylim(0, 2 * offset)

        unit_factor = 1000.0 if self._unit == "\u03bcm" else 1.0
        ax.set_yticks(np.linspace(0, 2 * offset, 5))
        ax.set_yticklabels([f"{(v - offset) * unit_factor:.1f}" for v in np.linspace(0, 2 * offset, 5)],
                           color="#9898b8", fontsize=6)
        ax.tick_params(colors="#9898b8", labelsize=7)
        ax.grid(True, alpha=0.15, color="#555577")

        ru = r.roundness * unit_factor
        pu = r.peak_error * unit_factor
        vu = r.valley_error * unit_factor
        info = (f"\u504f\u5dee [k={self._k}]  \u5706\u5ea6={ru:.2f}{self._unit}  "
                f"Peak=+{pu:.2f}  Valley={vu:.2f}")
        ax.set_title(info, color="#e8e8f0", fontsize=9, pad=12)

    def _render_xy(self, r):
        ax = self.fig.add_subplot(111)
        ax.set_facecolor("#12121e")
        pts = r.points
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]

        if self._show_fitted:
            circle = plt.Circle((r.fitted.cx, r.fitted.cy), r.fitted.radius,
                                fill=False, linestyle="--", color="#555577", lw=1)
            ax.add_patch(circle)
        if self._design_radius is not None and self._design_radius != r.fitted.radius:
            design_circle = plt.Circle((r.fitted.cx, r.fitted.cy), self._design_radius,
                                       fill=False, linestyle="-", color="#60a5fa", lw=1.5)
            ax.add_patch(design_circle)
            ax.annotate(f"Design R={self._design_radius:.3f}",
                        xy=(0.98, 0.97), xycoords="axes fraction",
                        fontsize=8, fontweight="bold", color="#60a5fa",
                        ha="right", va="top",
                        bbox=dict(boxstyle="round,pad=0.2", fc="#1a1a2e",
                                  ec="#60a5fa", lw=0.8))

        if self._show_profile:
            polar = r.polar_points
            oxs = [p.x for p in polar] + [polar[0].x]
            oys = [p.y for p in polar] + [polar[0].y]
            ax.plot(oxs, oys, "-", color="#93c5fd", lw=1.5)
            ax.scatter(xs, ys, c="#e0e7ff", s=8)

        if self._show_center:
            ax.scatter([r.fitted.cx], [r.fitted.cy], c="#fbbf24", marker="+", s=60, lw=1.5)

        # Highlight selected point (linked from advice table)
        if self._highlight_idx >= 0 and self._highlight_idx < len(xs):
            ax.scatter([xs[self._highlight_idx]], [ys[self._highlight_idx]],
                       c='#fbbf24', s=120, marker='o', edgecolors='white',
                       linewidths=1.5, zorder=10)

        ax.set_aspect("equal")
        ax.tick_params(colors="#9898b8", labelsize=7)
        ax.set_title(f"XY 视图  [R={r.fitted.radius:.2f}]", color="#e8e8f0", fontsize=10)
        ax.grid(True, alpha=0.1, color="#333355")

    def _render_full(self, thetas, deltas, thetas_loop, deltas_loop, r):
        """Three-panel combined view: profile | deviation-polar | deviation-linear."""
        unit_factor = 1000.0 if self._unit == "\u03bcm" else 1.0
        max_err = max(abs(r.peak_error), abs(r.valley_error), 1e-6)
        rlim = max_err * 1.4 * (self._k / 20.0)
        offset = rlim
        dev_shift = deltas + offset
        zero_map = {"\u53f3(3\u70b9)": 0, "\u4e0a(12\u70b9)": 90,
                     "\u5de6(9\u70b9)": 180, "\u4e0b(6\u70b9)": 270}
        theta_zero = np.radians(zero_map.get(self._zero_combo.currentText(), 0))

        gs = self.fig.add_gridspec(2, 2, width_ratios=[1, 1], height_ratios=[3, 1],
                                    hspace=0.28, wspace=0.32)

        # ── Top-left: Polar profile ──────────────────────────────────────
        ax1 = self.fig.add_subplot(gs[0, 0], polar=True)
        ax1.set_facecolor("#12121e")
        ax1.set_theta_offset(theta_zero)
        profile_r = r.fitted.radius + deltas
        ax1.plot(thetas_loop, np.full_like(thetas_loop, r.fitted.radius),
                 "--", color="#555577", lw=1, alpha=0.6)
        ax1.plot(thetas_loop, r.fitted.radius + deltas_loop, "o-",
                 color="#60a5fa", lw=1.5, ms=3)
        ax1.fill(thetas_loop, r.fitted.radius + deltas_loop,
                 alpha=0.12, color="#60a5fa")
        ax1.plot(thetas_loop, np.full_like(thetas_loop, r.fitted.radius + r.peak_error),
                 ":", color="#f87171", lw=0.6)
        ax1.plot(thetas_loop, np.full_like(thetas_loop, r.fitted.radius + r.valley_error),
                 ":", color="#4ade80", lw=0.6)
        ax1.set_title(f"Profile  [R={r.fitted.radius:.2f}]", color="#e8e8f0",
                      fontsize=9, pad=10)
        ax1.tick_params(colors="#9898b8", labelsize=7)
        ax1.grid(True, alpha=0.15, color="#555577")

        # Distance labels with guide lines for profile view
        if self._show_dist_labels and hasattr(r, "polar_points"):
            n = len(thetas)
            r_max = r.fitted.radius + max(abs(r.peak_error), abs(r.valley_error))
            outer_r = r_max * 1.25
            label_gap = r_max * 0.06
            thetas_deg = np.degrees(thetas) % 360
            closest_0 = np.argmin(np.minimum(thetas_deg, 360 - thetas_deg))
            for k in range(n):
                idx = (closest_0 + k) % n
                t = thetas[idx]
                r_val = profile_r[idx]
                stagger = (k % 5) * label_gap * 0.5
                label_r = outer_r + stagger
                ax1.plot([t, t], [r_val, label_r], "-",
                         color="#6b6b8a", lw=0.3, alpha=0.35)
                ax1.annotate(f"#{k + 1} {r.polar_points[idx].r:.3f}",
                             xy=(t, label_r), fontsize=4.5,
                             color="#6b6b8a", ha="center", va="bottom")
            ax1.set_ylim(0, outer_r + label_gap * 3)

        # Highlight
        if self._highlight_idx >= 0 and self._highlight_idx < len(thetas):
            ax1.plot(thetas[self._highlight_idx],
                     profile_r[self._highlight_idx],
                     "o", color="#fbbf24", ms=10, markeredgecolor="#fff",
                     markeredgewidth=1.5, zorder=10)

        # ── Top-right: Polar deviation ───────────────────────────────────
        ax2 = self.fig.add_subplot(gs[0, 1], polar=True)
        ax2.set_facecolor("#12121e")
        ax2.set_theta_offset(theta_zero)
        dev_shift_loop = deltas_loop + offset
        ax2.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.3,
                         where=(deltas_loop >= 0), color="#f87171")
        ax2.fill_between(thetas_loop, offset, dev_shift_loop, alpha=0.3,
                         where=(deltas_loop < 0), color="#4ade80")
        ax2.plot(thetas_loop, dev_shift_loop, "-", color="#93c5fd", lw=1.5)
        ax2.plot(thetas_loop, dev_shift_loop, ".", color="#e0e7ff", ms=3)
        ax2.plot(thetas_loop, np.full_like(thetas_loop, offset), "-",
                 color="#555577", lw=1, alpha=0.5)
        ax2.plot(thetas_loop, np.full_like(thetas_loop, r.peak_error + offset),
                 ":", color="#f87171", lw=0.6)
        ax2.plot(thetas_loop, np.full_like(thetas_loop, r.valley_error + offset),
                 ":", color="#4ade80", lw=0.6)
        ax2.set_ylim(0, 2 * offset)
        tick_vals = np.linspace(0, 2 * offset, 5)
        ax2.set_yticks(tick_vals)
        ax2.set_yticklabels([f"{(v - offset) * unit_factor:.1f}" for v in tick_vals],
                            color="#9898b8", fontsize=6)
        ax2.set_title(f"Deviation (polar)  [\u00b1{rlim * unit_factor:.2f}{self._unit}]",
                      color="#e8e8f0", fontsize=9, pad=10)
        ax2.tick_params(colors="#9898b8", labelsize=7)
        ax2.grid(True, alpha=0.15, color="#555577")

        # Distance labels with guide lines (when checkbox enabled)
        if self._show_dist_labels and hasattr(r, "polar_points"):
            n = len(thetas)
            outer_r = 2 * offset
            label_gap = outer_r * 0.20
            thetas_deg = np.degrees(thetas) % 360
            closest_0 = np.argmin(np.minimum(thetas_deg, 360 - thetas_deg))
            for k in range(n):
                idx = (closest_0 + k) % n
                t = thetas[idx]
                r_val = dev_shift[idx]
                stagger = (k % 5) * label_gap * 0.5
                label_r = outer_r + stagger
                ax2.plot([t, t], [r_val, label_r], "-",
                         color="#6b6b8a", lw=0.3, alpha=0.35)
                ax2.annotate(f"#{k + 1} {r.polar_points[idx].r:.3f}",
                             xy=(t, label_r), fontsize=4.5,
                             color="#6b6b8a", ha="center", va="bottom")
            ax2.set_ylim(0, outer_r + label_gap * 3)

        # Highlight
        if self._highlight_idx >= 0 and self._highlight_idx < len(thetas):
            ax2.plot(thetas[self._highlight_idx],
                     dev_shift[self._highlight_idx],
                     "o", color="#fbbf24", ms=10, markeredgecolor="#fff",
                     markeredgewidth=1.5, zorder=10)

        # ── Bottom: Linear deviation ─────────────────────────────────────
        ax3 = self.fig.add_subplot(gs[1, :])
        ax3.set_facecolor("#12121e")

        # Normalise thetas from [-π,π] to [0,2π] → degrees, re-sort
        lin_thetas = np.where(thetas < 0, thetas + 2 * np.pi, thetas)
        lin_order = np.argsort(lin_thetas)
        lt = np.degrees(lin_thetas[lin_order])    # degrees for x-axis
        ld = deltas[lin_order] * unit_factor      # deviation in chosen unit

        ax3.axhline(0, color="#555577", lw=1, ls="--", alpha=0.5)
        ax3.fill_between(lt, ld, 0, alpha=0.3,
                         where=(ld >= 0), color="#f87171")
        ax3.fill_between(lt, ld, 0, alpha=0.3,
                         where=(ld < 0), color="#4ade80")
        ax3.plot(lt, ld, "-", color="#60a5fa", lw=1.5)
        ax3.plot(lt, ld, ".", color="#93c5fd", ms=4)
        ax3.axhline(r.peak_error * unit_factor, color="#f87171", lw=0.6, ls=":")
        ax3.axhline(r.valley_error * unit_factor, color="#4ade80", lw=0.6, ls=":")
        ax3.set_xlim(-5, 365)
        ax3.set_xticks([0, 90, 180, 270, 360])
        ax3.set_title(f"Deviation (linear)  [{self._unit}]", color="#e8e8f0", fontsize=10)
        ax3.set_xlabel("Angle (\u00b0)", color="#9898b8", fontsize=8)
        ax3.set_ylabel(f"Error ({self._unit})", color="#9898b8", fontsize=8)
        ax3.tick_params(colors="#9898b8", labelsize=7)
        ax3.grid(True, alpha=0.15, color="#555577")

        # Highlight (linear chart uses degree-sorted data)
        if self._highlight_idx >= 0 and self._highlight_idx < len(thetas):
            t_deg = np.degrees(thetas[self._highlight_idx]) % 360
            ax3.plot(t_deg,
                     deltas[self._highlight_idx] * unit_factor,
                     "o", color="#fbbf24", ms=10, markeredgecolor="#fff",
                     markeredgewidth=1.5, zorder=10)

        # ── Summary footer ────────────────────────────────────────────────
        ru = r.roundness * unit_factor
        pu = r.peak_error * unit_factor
        vu = r.valley_error * unit_factor
        summary = (
            f"C: ({r.fitted.cx:.3f}, {r.fitted.cy:.3f})  "
            f"R: {r.fitted.radius:.3f}  "
            f"Roundness: {ru:.3f}{self._unit}  "
            f"Peak: +{pu:.4f}  Valley: {vu:.4f}  "
            f"RMSE: {r.fitted.rmse * unit_factor:.5f}{self._unit}  "
            f"k={self._k}"
        )
        self.fig.text(0.5, 0.01, summary, ha="center", va="bottom",
                      color="#9898b8", fontsize=7)

        self.fig.tight_layout(rect=[0, 0.04, 1, 1])

    def _annotate_extremes(self, ax, thetas, deltas, offset, r):
        peak_idx = np.argmax(deltas)
        valley_idx = np.argmin(deltas)
        unit_factor = 1000.0 if self._unit == "\u03bcm" else 1.0
        for idx, val, clr, lbl in [
            (peak_idx, r.peak_error, "#f87171", f"+{r.peak_error * unit_factor:.2f}"),
            (valley_idx, r.valley_error, "#4ade80", f"{r.valley_error * unit_factor:.2f}"),
        ]:
            ax.annotate(lbl, xy=(thetas[idx], deltas[idx] + offset),
                        fontsize=7, color=clr, ha="center",
                        bbox=dict(boxstyle="round,pad=0.2", fc="#1a1a2e", ec=clr, lw=0.5))


import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt

