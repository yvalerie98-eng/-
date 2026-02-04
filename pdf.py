from io import BytesIO
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# === ШРИФТ ===
FONT_REGULAR = Path(__file__).parent / "fonts" / "Roboto-Regular.ttf"
pdfmetrics.registerFont(TTFont("Roboto", str(FONT_REGULAR)))

# === РЕКВИЗИТЫ ИП (ПОСТОЯННЫЕ) ===
IP_FIO = "Индивидуальный предприниматель Герюгова Валерия Владимировна"
IP_INN = "780255641674"
TAX_SYSTEM = "ПСН"
PLACE = "http://valeriagerugova.tilda.ws/"
CASHIER = "ИП Герюгова В.В."


def make_psn_payment_doc_pdf(
    doc_no: int,
    service_name: str,
    amount_rub: int,
    dt: datetime,
) -> bytes:
    """
    Документ, подтверждающий факт расчёта
    (для ИП на ПНС без ККТ по п. 2.1 ст. 2 54-ФЗ)
    """

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    left = 50
    y = h - 60
    lh = 18

    def line(label, value):
        nonlocal y
        c.drawString(left, y, f"{label} {value}")
        y -= lh

    # ===== Заголовок =====
    c.setFont("Roboto", 16)
    c.drawString(left, y, "Документ, подтверждающий факт расчёта")
    y -= 30

    c.setFont("Roboto", 11)

    # ===== Обязательные реквизиты =====
    line("Номер документа:", str(doc_no))
    line("Дата:", dt.strftime("%d.%m.%Y"))
    line("Время:", dt.strftime("%H:%M"))
    line("Место (адрес) расчёта:", PLACE)

    y -= 6

    line("Продавец (ИП):", IP_FIO)
    line("ИНН продавца:", IP_INN)
    line("Система налогообложения:", TAX_SYSTEM)
    line("Признак расчёта:", "ПРИХОД")

    y -= 10

    # ===== Услуга =====
    c.setFont("Roboto", 12)
    c.drawString(left, y, "Оказанная услуга:")
    y -= 20

    c.setFont("Roboto", 11)
    c.drawString(left, y, service_name)
    y -= lh
    c.drawString(left, y, "Количество: 1")
    y -= lh
    c.drawString(left, y, f"Стоимость: {amount_rub} ₽")
    y -= lh + 10

    # ===== Оплата =====
    c.setFont("Roboto", 12)
    c.drawString(left, y, f"ИТОГО К ОПЛАТЕ: {amount_rub} ₽")
    y -= 22

    c.setFont("Roboto", 11)
    line("Форма расчёта:", "БЕЗНАЛИЧНЫЙ")
    line("Оплата наличными:", "0 ₽")
    line("Оплата безналичными:", f"{amount_rub} ₽")

    y -= 6
    line("Лицо, оформившее документ:", CASHIER)

    # ===== Низ =====
    c.setFont("Roboto", 9)
    c.drawString(
        left,
        50,
        "Основание: п. 2.1 ст. 2 и п. 1 ст. 4.7 Федерального закона №54-ФЗ. Документ сформирован автоматически."
    )

    c.showPage()
    c.save()
    return buf.getvalue()
    c.drawString(50, 50, "Сформировано автоматически")

    c.showPage()
    c.save()
    return buf.getvalue()
