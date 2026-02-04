from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os


def generate_pdf(service: str, amount: int, receipt_no: int) -> str:
    """
    Создаёт PDF квитанцию и возвращает путь к файлу
    """

    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%M")

    filename = f"receipt_{receipt_no}_{amount}.pdf"
    filepath = os.path.join("/tmp", filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica", 12)

    y = height - 80
    c.drawString(50, y, "КВИТАНЦИЯ")
    y -= 40

    c.drawString(50, y, f"Номер квитанции: {receipt_no}")
    y -= 25

    c.drawString(50, y, f"Дата: {date_str}")
    y -= 25

    c.drawString(50, y, f"Время: {time_str}")
    y -= 40

    c.drawString(50, y, f"Услуга: {service}")
    y -= 25

    c.drawString(50, y, f"Сумма: {amount} ₽")

    c.showPage()
    c.save()

    return filepath
