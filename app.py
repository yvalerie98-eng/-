import os
import logging
from datetime import datetime

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from db import init_db, take_next_no, set_state, get_state, clear_state
from pdf import make_receipt_pdf

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

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
    r = requests.post(f"{BASE_URL}/{method}", json=payload, timeout=25)
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
        data={"chat_id": str(chat_id)},
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
    parts = [p.strip() for p in (text or "").split(";") if p.strip()]
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
    log.info("startup ok")


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/diag")
def diag():
    return {"diag": "ok", "ts": datetime.utcnow().isoformat()}


async def handle_update(update: dict):
    # MESSAGE
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()
        low = text.lower()

        if text.startswith("/start") or low.startswith("старт"):
            clear_state(chat_id)
            send_message(chat_id, "Какой вариант квитанции нужен?", reply_markup=menu())
            return

        st = get_state(chat_id)
        if st and st.get("step") == "WAIT_OTHER":
            parsed = parse_other(text)
            if not parsed:
                send_message(chat_id, "Формат: Услуга; сумма\nПример: сопровождение; 5000")
                return

            service, amount = parsed
            clear_state(chat_id)

            no = take_next_no("other")
            pdf_bytes = make_receipt_pdf(no, service, amount, datetime.now())
            send_document(chat_id, f"receipt_other_{no}.pdf", pdf_bytes)
            send_message(chat_id, "Готово ✅")
            return

        send_message(chat_id, "Напиши /start")
        return

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
            return

        if data.startswith("AMOUNT_"):
            key = data.replace("AMOUNT_", "")
            if key in AMOUNTS:
                service_name, amount = AMOUNTS[key]
                no = take_next_no(key)
                pdf_bytes = make_receipt_pdf(no, service_name, amount, datetime.now())
                send_document(chat_id, f"receipt_{key}_{no}.pdf", pdf_bytes)
                send_message(chat_id, "Готово ✅")
                return

        send_message(chat_id, "Не поняла кнопку. Напиши /start.")
        return


# ✅ Принимаем Telegram и на "/" и на "/webhook" — чтобы точно не было 404
@app.post("/")
async def webhook_root(req: Request):
    try:
        update = await req.json()
        await handle_update(update)
        return JSONResponse({"ok": True})
    except Exception as e:
        log.exception("webhook error")
        return JSONResponse({"ok": False, "error": str(e)})


@app.post("/webhook")
async def webhook_alias(req: Request):
    return await webhook_root(req)
