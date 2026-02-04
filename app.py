import os
import logging
from datetime import datetime

import requests
from fastapi import FastAPI, Request, Response

from db import init_db, take_next_no, set_state, get_state, clear_state
from pdf import make_receipt_pdf

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

AMOUNTS = {
    "39900": ("ПНС", 39900),
    "49900": ("ПНС", 49900),
    "17900": ("ПНС", 17900),
    "22900": ("ПНС", 22900),
}

app = FastAPI()


def tg(method: str, payload: dict):
    r = requests.post(f"{TG_API}/{method}", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    tg("sendMessage", payload)


def send_pdf(chat_id: int, filename: str, pdf_bytes: bytes):
    files = {"document": (filename, pdf_bytes, "application/pdf")}
    r = requests.post(
        f"{TG_API}/sendDocument",
        data={"chat_id": str(chat_id)},
        files=files,
        timeout=60,
    )
    r.raise_for_status()


def answer_callback(callback_query_id: str):
    try:
        tg("answerCallbackQuery", {"callback_query_id": callback_query_id})
    except Exception:
        # не критично
        pass


def menu():
    return {
        "inline_keyboard": [
            [{"text": "39 900", "callback_data": "AMOUNT_39900"}],
            [{"text": "49 900", "callback_data": "AMOUNT_49900"}],
            [{"text": "17 900", "callback_data": "AMOUNT_17900"}],
            [{"text": "22 900", "callback_data": "AMOUNT_22900"}],
            [{"text": "Другая сумма", "callback_data": "AMOUNT_other"}],
        ]
    }


def parse_other(text: str):
    # формат: услуга; сумма
    parts = [p.strip() for p in text.split(";") if p.strip()]
    if len(parts) < 
