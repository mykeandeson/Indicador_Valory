# data_ingest.py — versão completa, atualizada e compatível com Valory
import asyncio
import socketio
import pandas as pd
from collections import defaultdict, deque
from datetime import datetime, timezone
from signal_engine import evaluate_signal
from db import SessionLocal, Signal, Candle
from config import WS_URL, MONITORED_ASSETS
import os, logging, time
from notifier import notify_if_needed

LOG = logging.getLogger("data_ingest")
LOG.setLevel(logging.INFO)

sio = socketio.AsyncClient(logger=False, engineio_logger=False)
tick_buffers = defaultdict(list)
candles_buf = defaultdict(lambda: deque(maxlen=2000))
WS_AUTH_PARAMS = os.getenv("WS_AUTH_PARAMS")

async def connect_and_listen(on_new_signal):
    connect_url = WS_URL
    if WS_AUTH_PARAMS:
        sep = "&" if "?" in connect_url else "?"
        connect_url = connect_url + sep + WS_AUTH_PARAMS

    LOG.info(f"Connecting to {connect_url}")

    await sio.connect(
        connect_url,
        transports=['websocket'],
        namespaces=['/symbol-prices']
    )

    LOG.info("Connected to WS namespace /symbol-prices")

    @sio.event
    async def connect():
        LOG.info("socketio connected")

    @sio.on("message", namespace="/symbol-prices")
    async def on_price_message(payload):
        await handle_real_valory_payload(payload, on_new_signal)

    while True:
        await asyncio.sleep(1)

async def handle_real_valory_payload(raw, on_new_signal):
    try:
        if not isinstance(raw, list) or len(raw) != 2:
            LOG.debug(f"Unexpected payload: {raw}")
            return

        event_name = raw[0]
        body = raw[1]
        if event_name != "message":
            return
        if not isinstance(body, dict):
            return
        if body.get("event") != "symbol.price.update":
            return

        data = body.get("data", {}) or {}
        symbol = data.get("symbol")
        if not symbol:
            channel = body.get("channel")
            if channel and ":" in channel:
                symbol = channel.split(":")[-1]

        if not symbol:
            LOG.debug(f"Symbol not found in payload: {raw}")
            return

        if symbol not in MONITORED_ASSETS:
            return

        price = data.get("price") or data.get("p") or data.get("last")
        if price is None:
            LOG.debug(f"Price not found in payload: {raw}")
            return
        try:
            price = float(price)
        except:
            return

        ts = data.get("timestamp") or data.get("ts") or data.get("time")
        if ts:
            try:
                ts_pd = pd.to_datetime(ts, unit='ms', utc=True)
            except:
                ts_pd = pd.Timestamp.utcnow()
        else:
            ts_pd = pd.Timestamp.utcnow()

        tick_buffers[symbol].append((ts_pd, price))
        await try_build_candle(symbol, on_new_signal)

    except Exception:
        LOG.exception("Error processing real Valory payload")

async def try_build_candle(symbol, on_new_signal):
    ticks = tick_buffers[symbol]
    if not ticks:
        return
    df = pd.DataFrame(ticks, columns=['ts', 'price'])
    df['minute'] = df['ts'].dt.floor('T')
    minutes = sorted(df['minute'].unique())
    for minute in minutes[:-1]:
        group = df[df['minute'] == minute]
        if group.empty:
            continue
        o = group['price'].iloc[0]
        h = group['price'].max()
        l = group['price'].min()
        c = group['price'].iloc[-1]
        v = len(group)
        candle_ts = pd.to_datetime(minute)
        candles_buf[symbol].append({
            "timestamp": candle_ts,
            "o": o, "h": h, "l": l, "c": c, "v": v
        })
        tick_buffers[symbol] = [
            (ts, p) for ts, p in ticks if ts.floor('T') > minute
        ]
        try:
            with SessionLocal() as s:
                s.add(Candle(timestamp=candle_ts.to_pydatetime(), ativo=symbol, o=o, h=h, l=l, c=c, v=v))
                s.commit()
        except Exception:
            LOG.exception("DB store candle failed")
        dfc = pd.DataFrame(list(candles_buf[symbol]))
        if dfc.empty:
            continue
        dfc = dfc.set_index("timestamp")
        signal = evaluate_signal(dfc, symbol, volume_proxy_series=dfc['v'])
        if signal:
            try:
                with SessionLocal() as s:
                    sig = Signal(timestamp=pd.Timestamp.utcnow().to_pydatetime(), ativo=signal['ativo'],
                                 minuto_entrada=pd.to_datetime(signal['minuto_entrada']).to_pydatetime(),
                                 tipo=signal['tipo'], confluencias=signal['confluencias'],
                                 probabilidade=signal['probabilidade'], detalhes=signal['detalhes'],
                                 expiracao_sugerida_min=signal['expiracao_sugerida_min'])
                    s.add(sig)
                    s.commit()
            except Exception:
                LOG.exception("Saving signal to DB failed")
            try:
                notify_if_needed(signal)
            except:
                LOG.exception("Notifier error")
            try:
                await on_new_signal(signal)
            except:
                LOG.exception("on_new_signal callback failed")
