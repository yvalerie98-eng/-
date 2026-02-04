from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def make_receipt_pdf(receipt_no: int, service: str, amount: int, dt: datetime) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h - 60, "КВИТАНЦИЯ")

    c.setFont("Helvetica", 11)
    c.drawString(50, h - 95, f"Квитанция №: {receipt_no}")
    c.drawString(50, h - 115, f"Дата: {dt.strftime('%d.%m.%Y')}")
    c.drawString(250, h - 115, f"Время: {dt.strftime('%H:%M')}")

    c.line(50, h - 130, w - 50, h - 130)

    y = h - 160
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Услуга:")
    c.setFont("Helvetica", 11)
    c.drawString(120, y, service)

    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Сумма:")
    c.setFont("Helvetica", 11)
    c.drawString(120, y, f"{amount} руб.")

    y -= 30
    c.line(50, y, w - 50, y)

    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Признак расчёта: приход")

    c.showPage()
    c.save()

    return buf.getvalue()
