from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def make_receipt_pdf(receipt_no: int, service: str, amount: int, dt: datetime) -> bytes:
    """
    Возвращает PDF (bytes). Главное: номер квитанции, дата, время.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # базовый шрифт
    c.setFont("Helvetica", 12)

    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h - 60, "Квитанция")

    # Номер / дата / время
    c.setFont("Helvetica", 12)
    c.drawString(50, h - 100, f"Квитанция №: {receipt_no}")
    c.drawString(50, h - 120, f"Дата: {dt.strftime('%d.%m.%Y')}")
    c.drawString(50, h - 140, f"Время: {dt.strftime('%H:%M')}")

    # Услуга и сумма
    c.drawString(50, h - 180, f"Услуга: {service}")
    c.drawString(50, h - 200, f"Сумма: {amount} ₽")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
