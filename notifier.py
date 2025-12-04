# notifier.py
import os
import requests
import logging

LOG = logging.getLogger("notifier")
LOG.setLevel(logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("NOTIFY_WEBHOOK_URL")
PROB_THRESHOLD = float(os.getenv("NOTIFY_PROB_THRESHOLD", "70"))

def send_webhook(signal: dict):
    if not WEBHOOK_URL:
        return False
    try:
        resp = requests.post(WEBHOOK_URL, json=signal, timeout=5)
        LOG.info(f"Webhook sent {resp.status_code}")
        return resp.ok
    except Exception as e:
        LOG.exception("Webhook error")
        return False

def send_telegram(signal: dict):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        text = build_message(signal)
        resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
        LOG.info(f"Telegram sent {resp.status_code}")
        return resp.ok
    except Exception as e:
        LOG.exception("Telegram error")
        return False

def build_message(signal: dict) -> str:
    lines = [
        f"*SINAL* — {signal.get('tipo')} {signal.get('ativo')}",
        f"Entrada: `{signal.get('minuto_entrada')}`",
        f"Confluências: {signal.get('confluencias')}",
        f"Probabilidade: {signal.get('probabilidade')}%",
        f"Expiração: {signal.get('expiracao_sugerida_min')} min",
        "",
        "*Detalhes:*"
    ]
    detalhes = signal.get('detalhes', {})
    for k,v in detalhes.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)

def notify_if_needed(signal: dict):
    prob = float(signal.get('probabilidade', 0))
    result = {"webhook": None, "telegram": None, "skipped": False}
    if prob < PROB_THRESHOLD:
        result["skipped"] = True
        return result
    result["webhook"] = send_webhook(signal) if WEBHOOK_URL else None
    result["telegram"] = send_telegram(signal) if (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID) else None
    return result
