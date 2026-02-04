from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_pdf(service: str, amount: int) -> str:
    now = datetime.now()
    receipt_no = now.strftime("%Y%m%d%H%M%S")

    filename = f"receipt_{receipt_no}.pdf"
    path = os.path.join("/tmp", filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica", 14)
    c.drawString(50, height - 50, "Квитанция")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Дата: {now.strftime('%d.%m.%Y %H:%M')}")
    c.drawString(50, height - 130, f"Номер квитанции: {receipt_no}")
    c.drawString(50, height - 170, f"Услуга: {service}")
    c.drawString(50, height - 200, f"Сумма: {amount} ₽")

    c.showPage()
    c.save()

    return path
