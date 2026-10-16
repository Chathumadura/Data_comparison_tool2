from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf_report(summary, mismatch_breakdown=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Data Comparison Report", styles["Title"]),
        Paragraph(f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Spacer(1, 8*mm),
    ]

    rows = [
        ["Metric", "Value"],
        ["Rows in Dataset A", summary.get("rows_a", 0)],
        ["Rows in Dataset B", summary.get("rows_b", 0)],
        ["Common Keys", summary.get("common_keys", 0)],
        ["Fully Matched Rows", summary.get("matched_rows", 0)],
        ["Mismatched Rows", summary.get("mismatched_rows", 0)],
        ["Only in Dataset A", summary.get("only_a", 0)],
        ["Only in Dataset B", summary.get("only_b", 0)],
        ["Compared Columns", summary.get("compared_columns", 0)],
        ["Cell-level Mismatches", summary.get("cell_mismatches", 0)],
    ]
    table = Table(rows, colWidths=[95*mm, 55*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1D4ED8")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(table)

    if mismatch_breakdown is not None and not mismatch_breakdown.empty:
        story += [Spacer(1, 10*mm), Paragraph("Mismatch Breakdown", styles["Heading2"])]
        data = [["Column", "Mismatch Count"]] + mismatch_breakdown.astype(str).values.tolist()
        bt = Table(data, colWidths=[105*mm, 45*mm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0F172A")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ]))
        story.append(bt)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
