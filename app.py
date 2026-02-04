import os
import logging
from fastapi import FastAPI, Request
import requests

from pdf import generate_pdf

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= APP =================
app = FastAPI()
logging.basicConfig(level=logging.INFO)


# --------- ROOT (чтобы Render был жив) ---------
@app.get("/")
async def root():
    return {"status": "ok"}


# --------- TELEGRAM WEBHOOK ---------
@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    logging.info(f"UPDATE: {data}")

    # сообщение
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/start"):
            send_menu(chat_id)
        else:
            send_message(chat_id, "Напиши /start")

    # callback-кнопки
    if "callback_query" in data:
        cq = data["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data_cb = cq["data"]

        if data_cb.isdigit():
            amount = int(data_cb)
            pdf_path = generate_pdf(amount)
            send_document(chat_id, pdf_path)

        answer_callback(cq["id"])

    return {"ok": True}


# ================= TELEGRAM HELPERS =================
def send_message(chat_id: int, text: str):
    requests.post(
        f"{TG_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )


def send_menu(chat_id: int):
    keyboard = {
        "inline_keyboard": [
            [{"text": "17 900", "callback_data": "17900"}],
            [{"text": "22 900", "callback_data": "22900"}],
            [{"text": "39 900", "callback_data": "39900"}],
            [{"text": "49 900", "callback_data": "49900"}],
        ]
    }

    requests.post(
        f"{TG_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "Какой вариант квитанции нужен?",
            "reply_markup": keyboard
        },
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


def answer_callback(callback_id: str):
    requests.post(
        f"{TG_API}/answerCallbackQuery",
        json={"callback_query_id": callback_id},
        timeout=5
    )
