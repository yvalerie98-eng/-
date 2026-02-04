from io import BytesIO
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# === ШРИФТ (кириллица) ===
FONT_REGULAR = Path(__file__).parent / "fonts" / "Roboto-Regular.ttf"

# регистрируем шрифт один раз
pdfmetrics.registerFont(TTFont("Roboto", str(FONT_REGULAR)))


def make_receipt_pdf(
    receipt_no: int,
    service_name: str,
    amount: int,
    dt: datetime
) -> bytes:
    """
    Возвращает PDF (bytes).
    С кириллицей, номером квитанции, датой и временем.
    """

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # ===== Заголовок =====
    c.setFont("Roboto", 16)
    c.drawString(50, h - 60, "Квитанция")

    # ===== Основная информация =====
    c.setFont("Roboto", 12)
    c.drawString(50, h - 100, f"Номер: {receipt_no}")

    c.drawString(50, h - 120, f"Дата: {dt.strftime('%d.%m.%Y')}")
    c.drawString(250, h - 120, f"Время: {dt.strftime('%H:%M')}")

    c.drawString(50, h - 160, f"Услуга: {service_name}")
    c.drawString(50, h - 180, f"Сумма: {amount} ₽")

    # ===== Низ страницы =====
    c.setFont("Roboto", 10)
    c.drawString(50, 50, "Сформировано автоматически")

    c.showPage()
    c.save()

    return buf.getvalue()
    c.drawString(50, 50, "Сформировано автоматически")

    c.showPage()
    c.save()
    return buf.getvalue()
