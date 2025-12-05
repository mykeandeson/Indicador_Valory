from flask import Flask, jsonify, render_template, send_from_directory
import os

# Importa o Telegram (sem isso o backend quebra)
from notifier import send_telegram_message

app = Flask(__name__)

# ===== STATUS DO SCANNER ===== #
scanner_ativo = False

# Estrutura esperada para cada sinal armazenado:
# {
#   "ativo": "EUR/USD",
#   "tipo": "CALL",
#   "confluencias": 5,
#   "nivel": "Forte",
#   "probabilidade": 71,
#   "minuto_entrada": "2025-12-05T08:07:00"
# }
sinais = []


# ===== ROTAS DO FRONT (PWA) ===== #

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# ===== ROTAS DO SISTEMA ===== #

@app.route("/start", methods=["POST"])
def start_scan():
    global scanner_ativo
    scanner_ativo = True
    print("Scanner iniciado!")
    return jsonify({"status": "scanner_started"})


@app.route("/stop", methods=["POST"])
def stop_scan():
    global scanner_ativo
    scanner_ativo = False
    print("Scanner parado.")
    return jsonify({"status": "scanner_stopped"})


@app.route("/signals/current")
def get_signals():
    """
    Retorna a lista de sinais atuais.
    """
    return jsonify(sinais)


# ===== EXECUTAR NO RENDER ===== #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

