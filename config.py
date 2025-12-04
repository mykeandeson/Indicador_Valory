# config.py
WS_URL = "wss://symbol-prices-api.mybroker.dev/socket.io/?EIO=4&transport=websocket"
MONITORED_ASSETS = ["EURUSD", "BTCUSDT", "USDJPY", "ETHUSDT", "XRPUSDT", "SOLUSDT", "GBPUSD", "EURGBP"]  # example: edit as needed
MIN_CONFLUENCES = 3
TIMEFRAME = "1m"
EMA_SHORT = 9
EMA_LONG = 21
RSI_PERIOD = 14
BB_PERIOD = 20
BB_STD = 2
WEIGHTS = {
    "ema": 0.20,
    "candle": 0.20,
    "rsi": 0.15,
    "bollinger": 0.15,
    "volume": 0.15,
    "sr": 0.15
}
DB_PATH = "signals.db"
TOP_N = 10
