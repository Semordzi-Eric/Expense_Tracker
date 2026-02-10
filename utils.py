import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime


def export_excel(weekly_df, monthly_df):
    filename = f"expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        weekly_df.to_excel(writer, sheet_name="Weekly Report", index=False)
        monthly_df.to_excel(writer, sheet_name="Monthly Report", index=False)

    return filename


def export_pdf(weekly_summary, monthly_summary):
    filename = f"expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Personal Expense Report</b>", styles["Title"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Weekly Summary
    elements.append(Paragraph("<b>Weekly Summary</b>", styles["Heading2"]))
    weekly_table = Table(list(weekly_summary.items()))
    weekly_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))
    elements.append(weekly_table)

    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Monthly Summary
    elements.append(Paragraph("<b>Monthly Summary</b>", styles["Heading2"]))
    monthly_table = Table(list(monthly_summary.items()))
    monthly_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))
    elements.append(monthly_table)

    doc.build(elements)

    return filename
