import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from svglib.svglib import svg2rlg

from models.data_models import AnalysisResult
from core.mold_advisor import get_advice_table

DARK_BG = HexColor("#1a1a2e")
LIGHT_TEXT = HexColor("#e8e8f0")

# Register Chinese font
_CJK_REGISTERED = False
def _register_cjk():
    global _CJK_REGISTERED
    if _CJK_REGISTERED:
        return
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simsun.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("CJKFont", fp))
                _CJK_REGISTERED = True
                return
            except Exception:
                continue
    # Fallback: try to find any CJK font
    import glob
    patterns = [
        "C:/Windows/Fonts/msyh*",
        "C:/Windows/Fonts/simsun*",
        "C:/Windows/Fonts/deng*",
        "C:/Windows/Fonts/yahei*",
    ]
    for pat in patterns:
        for fp in glob.glob(pat):
            try:
                pdfmetrics.registerFont(TTFont("CJKFont", fp))
                _CJK_REGISTERED = True
                return
            except Exception:
                continue


_register_cjk()
CJK = "CJKFont" if _CJK_REGISTERED else "Helvetica"


def generate_report(result, svg_data, output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=42*mm, bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=16, textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=8, fontName=CJK,
    )
    normal_style = ParagraphStyle(
        "CustomNormal", parent=styles["Normal"],
        fontSize=9, leading=12, fontName=CJK,
    )
    heading_style = ParagraphStyle(
        "CustomHeading", parent=styles["Heading2"],
        fontSize=12, textColor=colors.HexColor("#3b82f6"),
        spaceBefore=8, spaceAfter=4, fontName=CJK,
    )

    elements = []

    n_points = len(result.polar_points)
    generated = datetime.now().strftime('%Y-%m-%d %H:%M')
    report_title = "圆度拟合 · 圆度分析报告"
    report_subtitle = f"时间：{generated} | 点数：{n_points}"

    def _draw_brand(canvas):
        w, h = A4
        left = 15 * mm
        top = h - 15 * mm
        # 左上角品牌标识 + 版权
        canvas.setFillColor(HexColor("#1f3864"))
        canvas.setFont(CJK, 11)
        canvas.drawString(left, top, "圆度拟合 v2.0")
        canvas.setFillColor(HexColor("#9aa3b2"))
        canvas.setFont(CJK, 8)
        canvas.drawString(left, top - 12, "Copyright © 2026 OUKUI. All rights reserved.")

    def _draw_header_first(canvas, _doc):
        canvas.saveState()
        _draw_brand(canvas)
        w, h = A4
        top = h - 15 * mm
        # 首屏居中报告标题 + 时间/点数
        canvas.setFillColor(HexColor("#1a1a2e"))
        canvas.setFont(CJK, 18)
        canvas.drawCentredString(w / 2, top - 34, report_title)
        canvas.setFillColor(HexColor("#6b7280"))
        canvas.setFont(CJK, 9)
        canvas.drawCentredString(w / 2, top - 50, report_subtitle)
        canvas.restoreState()

    def _draw_header_later(canvas, _doc):
        canvas.saveState()
        _draw_brand(canvas)
        canvas.restoreState()

    # ── 拟合结果（列表形式） ──
    elements.append(Paragraph("拟合结果", heading_style))
    d = result.to_dict()
    result_rows = [
        ("特征类型", result.feature_type.value),
        ("圆心", f"({d['cx']:.4f}, {d['cy']:.4f})"),
        ("拟合半径", f"{d['radius']:.4f} {result.unit}"),
        ("点数", str(d['n_points'])),
        ("圆度值", f"{d['roundness']:.4f} {result.unit}"),
        ("RMSE", f"{d['rmse']:.6f} {result.unit}"),
        ("最大正偏差", f"+{d['peak_error']:.4f} {result.unit}"),
        ("最大负偏差", f"{d['valley_error']:.4f} {result.unit}"),
    ]
    cell_style = ParagraphStyle("SummaryCell", fontName=CJK, fontSize=9, leading=12)
    head_cell = ParagraphStyle("SummaryHead", fontName=CJK, fontSize=9, leading=12,
                               textColor=colors.white)
    table_rows = [[Paragraph("指标", head_cell), Paragraph("数值", head_cell)]]
    for k, v in result_rows:
        table_rows.append([Paragraph(k, cell_style), Paragraph(v, cell_style)])
    results_tbl = Table(table_rows, colWidths=[50*mm, 130*mm])
    results_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#3b82f6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#f0f4ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(results_tbl)
    elements.append(Spacer(1, 3*mm))

    # Chart (vector SVG)
    if svg_data:
        chart_heading = Paragraph("极坐标偏差图", heading_style)
        elements.append(chart_heading)

        # 估算结果表与标题占用高度，限制图片高度，避免被挤到第二页
        page_w, page_h = A4
        content_w = page_w - doc.leftMargin - doc.rightMargin
        content_h = page_h - doc.topMargin - doc.bottomMargin
        try:
            reserved = (
                Paragraph("拟合结果", heading_style).wrap(content_w, content_h)[1]
                + heading_style.spaceBefore + heading_style.spaceAfter
                + results_tbl.wrap(content_w, content_h)[1]
                + 3*mm
                + chart_heading.wrap(content_w, content_h)[1]
                + heading_style.spaceBefore + heading_style.spaceAfter
            )
        except Exception:
            reserved = 0
        max_chart_h = max(content_h - reserved - 6*mm, 60*mm)

        with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False,
                                          encoding="utf-8") as f:
            f.write(svg_data)
            svg_path = f.name
        try:
            drawing = svg2rlg(svg_path)
            if drawing is not None:
                target_w = 170 * mm
                scale = target_w / drawing.width
                new_w = target_w
                new_h = drawing.height * scale
                if new_h > max_chart_h:
                    cap = max_chart_h / new_h
                    scale *= cap
                    new_w *= cap
                    new_h = max_chart_h
                drawing.width = new_w
                drawing.height = new_h
                drawing.scale(scale, scale)
                elements.append(drawing)
        finally:
            os.unlink(svg_path)
        elements.append(Spacer(1, 4*mm))

    # ── Page break → advice table on page 2 ─────────────────────────────
    elements.append(PageBreak())

    # Advice table
    elements.append(Paragraph("测量点偏差表", heading_style))
    table_data = get_advice_table(result.polar_points)
    if table_data:
        cell_style = ParagraphStyle("CellStyle", fontName=CJK, fontSize=8, leading=10)
        tbl = [[Paragraph(c, cell_style) for c in ["#", "角度(\u00b0)", f"\u504f\u5dee({result.unit})", "X", "Y"]]]
        for row in table_data:
            tbl.append([Paragraph(str(row["no"]), cell_style),
                        Paragraph(row["angle"], cell_style),
                        Paragraph(row["delta_r"], cell_style),
                        Paragraph(row["x"], cell_style),
                        Paragraph(row["y"], cell_style)])
        t = Table(tbl, colWidths=[15*mm, 35*mm, 40*mm, 45*mm, 45*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#3b82f6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#f0f4ff")]),
        ]))
        elements.append(t)

    doc.build(elements, onFirstPage=_draw_header_first, onLaterPages=_draw_header_later)
    return output_path


def generate_and_save(result, svg_data, output_path):
    """Generate PDF from result and SVG chart data."""
    return generate_report(result, svg_data, output_path)
