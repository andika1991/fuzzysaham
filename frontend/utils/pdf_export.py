from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def generate_ranking_pdf(ranking_data, tanggal):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24
    )

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("Laporan Ranking Saham LQ45", styles["Title"])
    subtitle = Paragraph(f"Tanggal Ranking: {tanggal}", styles["Normal"])

    elements.append(title)
    elements.append(Spacer(1, 8))
    elements.append(subtitle)
    elements.append(Spacer(1, 16))

    table_data = [[
        "No",
        "Ticker",
        "Perusahaan",
        "Skor",
        "Kategori",
        "EPS",
        "PER",
        "ROE",
        "DER",
        "FCF",
        "MA50",
        "MA200",
        "RSI",
        "Volume",
        "Sentimen"
    ]]

    for index, sah in enumerate(ranking_data, start=1):
        table_data.append([
            index,
            sah.get("ticker", "-"),
            sah.get("nama_perusahaan", "-"),
            f"{(sah.get('fuzzy_score') or 0) * 100:.2f}%",
            sah.get("kategori", "-"),
            sah.get("eps_level", "-"),
            sah.get("per_level", "-"),
            sah.get("roe_level", "-"),
            sah.get("der_level", "-"),
            sah.get("fcf_level", "-"),
            sah.get("trend_ma50", "-"),
            sah.get("trend_ma200", "-"),
            sah.get("rsi_level", "-"),
            sah.get("volume_level", "-"),
            sah.get("sentimen_level", "-")
        ])

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            28,   # No
            50,   # Ticker
            135,  # Perusahaan
            48,   # Skor
            58,   # Kategori
            48,   # EPS
            48,   # PER
            48,   # ROE
            48,   # DER
            48,   # FCF
            52,   # MA50
            52,   # MA200
            48,   # RSI
            54,   # Volume
            58    # Sentimen
        ]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("FONTSIZE", (0, 1), (-1, -1), 6),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf