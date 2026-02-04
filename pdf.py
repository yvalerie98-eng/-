from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def make_receipt_pdf(receipt_no: int, service: str, amount: int, dt: datetime) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 60, "КВИТАНЦИЯ (ПНС)")

    c.setFont("Helvetica", 11)
    c.drawString(50, h - 90, f"Квитанция № {receipt_no}")
    c.drawString(50, h - 110, f"Дата: {dt.strftime('%d.%m.%Y')}")
    c.drawString(220, h - 110, f"Время: {dt.strftime('%H:%M')}")

    c.line(50, h - 130, w - 50, h - 130)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, h - 160, "Услуга:")
    c.setFont("Helvetica", 11)
    c.drawString(50, h - 180, service[:100])

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, h - 220, "Сумма:")
    c.setFont("Helvetica", 11)
    c.drawString(120, h - 220, f"{amount} руб.")

    c.line(50, h - 250, w - 50, h - 250)
    c.setFont("Helvetica", 10)
    c.drawString(50, h - 270, "Признак расчёта: приход")

    c.showPage()
    c.save()

    return buf.getvalue()
