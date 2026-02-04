import os
import logging
import requests
from fastapi import FastAPI, Request

from pdf import generate_pdf

# ================= НАСТРОЙКИ =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= APP =================

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ---- ROOT (ОБЯЗАТЕЛЬНО ДЛЯ RENDER) ----
@app.get("/")
def root():
    return {"status": "ok"}

# ---- WEBHOOK ----
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    logging.info(data)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "Напиши: услуга; сумма\n\nПример:\nсопровождение; 5000")
            return {"ok": True}

        if ";" in text:
            try:
                service, amount = text.split(";", 1)
                service = service.strip()
                amount = int(amount.strip())

                pdf_path = generate_pdf(service, amount)

                send_document(chat_id, pdf_path)
                send_message(chat_id, "Готово ✅")

            except Exception as e:
                logging.exception(e)
                send_message(chat_id, "Ошибка при создании PDF 😔")

    return {"ok": True}

# ================= TELEGRAM HELPERS =================

def send_message(chat_id: int, text: str):
    requests.post(
        f"{TG_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )

def send_document(chat_id: int, file_path: str):
    with open(file_path, "rb") as f:
        requests.post(
            f"{TG_API}/sendDocument",
            data={"chat_id": chat_id},
            files={"document": f},
            timeout=30
        )
