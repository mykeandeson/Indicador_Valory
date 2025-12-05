import requests
import os

# Pegamos TOKEN e CHAT_ID das variáveis de ambiente (Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(ativo, tipo, minuto_entrada, confluencias, probabilidade):
    """
    Envia mensagem para o Telegram.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TOKEN ou CHAT_ID não configurado no Render.")
        return

    text = (
        f"📊 *Sinal Detectado*\n\n"
        f"Ativo: *{ativo}*\n"
        f"Tipo: *{tipo}*\n"
        f"Entrada: *{minuto_entrada}*\n"
        f"Confluências: *{confluencias}/7*\n"
        f"Nível: *{nivel_sinal(confluencias)}*\n"
        f"Probabilidade: *{probabilidade}%*\n"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, json=data)
        print("Telegram retorno:", r.text)
    except Exception as e:
        print("Erro enviando Telegram:", e)


def nivel_sinal(confluencias):
    """Classifica o sinal."""
    if confluencias < 3:
        return "Fraco"
    if 3 <= confluencias <= 4:
        return "Moderado"
    if 5 <= confluencias <= 6:
        return "Forte"
    if confluencias == 7:
        return "Premium"

