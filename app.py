from fastapi import FastAPI, Request
import requests
import os
from datetime import datetime

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ---------- HEALTH CHECK ----------
@app.get("/")
def root():
    return {"ok": True}

# ---------- TELEGRAM WEBHOOK ----------
@app.post("/")
async def telegram_webhook(req: Request):
    update = await req.json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text.startswith("/start"):
            send_menu(chat_id)

    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq["data"]

        answer_callback(cq["id"])

        if data.startswith("AMOUNT_"):
            amount = data.replace("AMOUNT_", "")
            send_pdf_stub(chat_id, amount)

    return {"ok": True}

# ---------- TELEGRAM HELPERS ----------
def tg(method, payload):
    requests.post(f"{TELEGRAM_API}/{method}", json=payload)

def answer_callback(callback_id):
    tg("answerCallbackQuery", {"callback_query_id": callback_id})

def send_menu(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "39 900", "callback_data": "AMOUNT_39900"}],
            [{"text": "49 900", "callback_data": "AMOUNT_49900"}],
            [{"text": "17 900", "callback_data": "AMOUNT_17900"}],
            [{"text": "22 900", "callback_data": "AMOUNT_22900"}],
        ]
    }
    tg("sendMessage", {
        "chat_id": chat_id,
        "text": "Какой вариант квитанции нужен?",
        "reply_markup": keyboard
    })

def send_pdf_stub(chat_id, amount):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    tg("sendMessage", {
        "chat_id": chat_id,
        "text": f"✅ Принято\nСумма: {amount}\nДата: {now}\n\nPDF подключим следующим шагом 🙂"
    })

        send_message(chat_id, "Напиши /start")
        return {"ok": True}

    return {"ok": True}
