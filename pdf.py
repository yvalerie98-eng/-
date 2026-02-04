from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def make_receipt_pdf(receipt_no: int, service_name: str, amount: int, dt: datetime) -> bytes:
    """
    Возвращает PDF (bytes). Важно: номер квитанции + дата + время.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h - 60, "Квитанция")

    c.setFont("Helvetica", 12)
    c.drawString(50, h - 90, f"Номер: {receipt_no}")

    c.drawString(50, h - 110, f"Дата: {dt.strftime('%d.%m.%Y')}")
    c.drawString(250, h - 110, f"Время: {dt.strftime('%H:%M')}")

    c.drawString(50, h - 150, f"Услуга: {service_name}")
    c.drawString(50, h - 170, f"Сумма: {amount} ₽")

    # Низ
    c.setFont("Helvetica", 10)
    c.drawString(50, 50, "Сформировано автоматически")

    c.showPage()
    c.save()
    return buf.getvalue()
