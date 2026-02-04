from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def make_receipt_pdf(receipt_no: int, service: str, amount: int, dt: datetime) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 60, "КВИТАНЦИЯ")

    c.setFont("Helvetica", 11)
    c.drawString(50, h - 100, f"Номер квитанции: {receipt_no}")
    c.drawString(50, h - 120, f"Дата: {dt.strftime('%d.%m.%Y')}")
    c.drawString(250, h - 120, f"Время: {dt.strftime('%H:%M')}")

    c.line(50, h - 135, w - 50, h - 135)

    c.drawString(50, h - 170, f"Услуга: {service}")
    c.drawString(50, h - 200, f"Сумма: {amount} руб.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
