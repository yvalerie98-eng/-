import os
from datetime import datetime

import requests
from fastapi import FastAPI, Request

from db import init_db, take_next_no, set_state, get_state, clear_state
from pdf import make_receipt_pdf

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

AMOUNTS = {
    "39900": ("ПНС", 39900),
    "49900": ("ПНС", 49900),
    "17900": ("ПНС", 17900),
    "22900": ("ПНС", 22900),
}

app = FastAPI()


def tg(method: str, payload: dict):
    r = requests.post(f"{BASE_URL}/{method}", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    tg("sendMessage", payload)


def send_document(chat_id: int, filename: str, data: bytes):
    files = {"document": (filename, data, "application/pdf")}
    r = requests.post(
        f"{BASE_URL}/sendDocument",
        data={"chat_id": chat_id},
        files=files,
        timeout=60,
    )
    r.raise_for_status()


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
    parts = [p.strip() for p in text.split(";") if p.strip()]
    if len(parts) < 2:
        return None

    service = parts[0]
    amount_raw = parts[1].replace(" ", "").replace(",", ".")

    try:
        amount = int(float(amount_raw))
    except Exception:
        return None

    return service, amount


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/diag")
def diag():
    return {
        "status": "ok",
        "bot_token_set": bool(BOT_TOKEN)
    }

# ✅ ВАЖНО: Telegram теперь шлёт на "/" — значит webhook должен быть тут
@app.post("/")
async def webhook_root(req: Request):
    update = await req.json()

    # MESSAGE
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()

        if text.startswith("/start") or text.lower() == "старт":
            clear_state(chat_id)
            send_message(chat_id, "Какой вариант квитанции нужен?", reply_markup=menu())
            return {"ok": True}

        st = get_state(chat_id)
        if st and st.get("step") == "WAIT_OTHER":
            parsed = parse_other(text)
            if not parsed:
                send_message(chat_id, "Формат: Услуга; сумма\nПример: сопровождение; 5000")
                return {"ok": True}

            service, amount = parsed
            clear_state(chat_id)

            no = take_next_no("other")
            pdf = make_receipt_pdf(no, service, amount, datetime.now())
            send_document(chat_id, f"receipt_other_{no}.pdf", pdf)
            send_message(chat_id, "Готово ✅")
            return {"ok": True}

        send_message(chat_id, "Напиши /start")
        return {"ok": True}

    # CALLBACK
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq.get("data", "")

        try:
            tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
        except Exception:
            pass

        if data == "AMOUNT_other":
            set_state(chat_id, "WAIT_OTHER")
            send_message(chat_id, "Напиши: Услуга; сумма\nПример: сопровождение; 5000")
            return {"ok": True}

        if data.startswith("AMOUNT_"):
            key = data.replace("AMOUNT_", "")
            if key in AMOUNTS:
                service_name, amount = AMOUNTS[key]
                no = take_next_no(key)
                pdf = make_receipt_pdf(no, service_name, amount, datetime.now())
                send_document(chat_id, f"receipt_{key}_{no}.pdf", pdf)
                send_message(chat_id, "Готово ✅")
                return {"ok": True}

        send_message(chat_id, "Не поняла кнопку. Напиши /start.")
        return {"ok": True}

    return {"ok": True}
