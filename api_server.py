# api_server.py
import uvicorn
from fastapi import FastAPI
from db import init_db, SessionLocal, Signal
from pydantic import BaseModel
from typing import List
from datetime import datetime
import threading
from data_ingest import connect_and_listen
import pandas as pd

app = FastAPI(title="Valory Scanner API")

init_db()

class SignalOut(BaseModel):
    id: int
    timestamp: datetime
    ativo: str
    minuto_entrada: datetime
    tipo: str
    confluencias: int
    probabilidade: float
    detalhes: dict
    expiracao_sugerida_min: int

@app.get("/signals/current", response_model=List[SignalOut])
def get_current(top: int = 10):
    db = SessionLocal()
    q = db.query(Signal).order_by(Signal.probabilidade.desc()).limit(top).all()
    return q

@app.get("/signals/history", response_model=List[SignalOut])
def get_history(limit: int = 100):
    db = SessionLocal()
    q = db.query(Signal).order_by(Signal.timestamp.desc()).limit(limit).all()
    return q

_bg_thread = None
def _run_ws():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def on_new_signal(sig):
        print("New signal:", sig)
    loop.run_until_complete(connect_and_listen(on_new_signal))

@app.post("/start")
def start_scan():
    global _bg_thread
    if _bg_thread and _bg_thread.is_alive():
        return {"status":"already_running"}
    _bg_thread = threading.Thread(target=_run_ws, daemon=True)
    _bg_thread.start()
    return {"status":"started"}

@app.post("/stop")
def stop_scan():
    return {"status":"stopping_not_implemented"}

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
