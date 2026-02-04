import os
import logging
import asyncio
from datetime import datetime

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from db import init_db, take_next_no, set_state, get_state, clear_state
from pdf import make_psn_payment_doc_pdf

# ================== НАСТРОЙКИ ==================

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Фиксированные варианты
AMOUNTS = {
    "39900": (
        "Дополнительное образование в сфере питания в формате сопровождения, 12 недель (вариант 1)",
        39900,
    ),
    "49900": (
        "Дополнительное образование в сфере питания в формате сопровождения, 12 недель (вариант 2)",
        49900,
    ),
    "17900": (
        "Дополнительное образование в сфере питания в формате сопровождения, 4 недели (вариант 1)",
        17900,
    ),
    "22900": (
        "Дополнительное образование в сфере питания в формате сопровождения, 4 недели (вариант 2)",
        22900,
    ),
}

app = FastAPI()

# ================== TELEGRAM API ==================

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
        data={"chat_id": str(chat_id)},
        files=files,
        timeout=60,
    )
    r.raise_for_status()

# ================== UI ==================

def menu():
    return {
        "inline_keyboard": [
            [{"text": "12 недель — 39 900", "callback_data": "AMOUNT_39900"}],
            [{"text": "12 недель — 49 900", "callback_data": "AMOUNT_49900"}],
            [{"text": "4 недели — 17 900", "callback_data": "AMOUNT_17900"}],
            [{"text": "4 недели — 22 900", "callback_data": "AMOUNT_22900"}],
            [{"text": "Другая услуга / сумма", "callback_data": "AMOUNT_OTHER"}],
        ]
    }

# ================== PARSER ==================

def parse_other(text: str):
    if not text or ";" not in text:
        return None

    service, amount_raw = text.split(";", 1)
    service = service.strip()
    if len(service) < 5:
        return None

    amount_raw = amount_raw.replace(" ", "").replace(",", ".")
    try:
        amount = int(float(amount_raw))
    except Exception:
        return None

    if amount <= 0:
        return None

    return service, amount

# ================== STARTUP ==================

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

# ================== UPDATE HANDLER ==================

async def handle_update(update: dict):
    # ---------- MESSAGE ----------
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()
        low = text.lower()

        if text.startswith("/start") or low.startswith("старт"):
            clear_state(chat_id)
            send_message(
                chat_id,
                "Выберите вариант услуги или укажите свою сумму:",
                reply_markup=menu(),
            )
            return

        st = get_state(chat_id)
        if st and st.get("step") == "WAIT_OTHER":
            parsed = parse_other(text)
            if not parsed:
                send_message(
                    chat_id,
                    "Напишите в формате:\n"
                    "Название услуги; сумма\n\n"
                    "Пример:\n"
                    "Дополнительное образование в сфере питания, индивидуальное сопровождение 6 недель; 25000"
                )
                return

            service, amount = parsed
            clear_state(chat_id)

            no = take_next_no("other")
            pdf_bytes = make_psn_payment_doc_pdf(
                doc_no=no,
                service_name=service,
                amount_rub=amount,
                dt=datetime.now(),
            )
            send_document(chat_id, f"payment_doc_{no}.pdf", pdf_bytes)
            send_message(chat_id, "Документ сформирован ✅")
            return

        send_message(chat_id, "Напишите /start")
        return

    # ---------- CALLBACK ----------
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq.get("data", "")

        try:
            tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
        except Exception:
            pass

        if data == "AMOUNT_OTHER":
            set_state(chat_id, "WAIT_OTHER")
            send_message(
                chat_id,
                "Напишите:\n"
                "Название услуги; сумма\n\n"
                "Пример:\n"
                "Дополнительное образование в сфере питания, индивидуальное сопровождение 6 недель; 25000"
            )
            return

        if data.startswith("AMOUNT_"):
            key = data.replace("AMOUNT_", "")
            if key in AMOUNTS:
                service_name, amount = AMOUNTS[key]
                no = take_next_no(key)
                pdf_bytes = make_psn_payment_doc_pdf(
                    doc_no=no,
                    service_name=service_name,
                    amount_rub=amount,
                    dt=datetime.now(),
                )
                send_document(chat_id, f"payment_doc_{key}_{no}.pdf", pdf_bytes)
                send_message(chat_id, "Документ сформирован ✅")
                return

        send_message(chat_id, "Неверная кнопка. Напишите /start.")
        return

# ================== WEBHOOK ==================

@app.post("/")
async def webhook_root(req: Request):
    try:
        update = await req.json()
        asyncio.create_task(handle_update(update))
        return JSONResponse({"ok": True})
    except Exception as e:
        log.exception("webhook error")
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/webhook")
async def webhook_alias(req: Request):
    return await webhook_root(req)
