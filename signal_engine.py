# signal_engine.py
from indicators import ema, rsi, bollinger_bands, detect_hammer, detect_shooting_star, is_bollinger_touch, calc_support_resistance
import pandas as pd
from config import WEIGHTS, MIN_CONFLUENCES

def evaluate_signal(ohlcv_df: pd.DataFrame, asset: str, volume_proxy_series=None):
    out = {}
    close = ohlcv_df['c']
    ema9 = ema(close, 9)
    ema21 = ema(close, 21)
    rsi14 = rsi(close, 14)
    upper, mid, lower = bollinger_bands(close, 20, 2)
    last_idx = ohlcv_df.index[-1]
    last_row = ohlcv_df.iloc[-1]
    price = last_row['c']

    price_above_emas = 1 if price > ema9.iloc[-1] and price > ema21.iloc[-1] else 0
    rsi_val = rsi14.iloc[-1]
    rsi_call = 1 if (30 <= rsi_val <= 50) else 0
    rsi_put  = 1 if (50 <= rsi_val <= 70) else 0
    bb_touch = is_bollinger_touch(price, upper.iloc[-1], lower.iloc[-1])
    candle = {'o': last_row['o'],'h': last_row['h'],'l': last_row['l'],'c': last_row['c']}
    hammer = detect_hammer(candle)
    shooting = detect_shooting_star(candle)

    vol_flag = 0
    if volume_proxy_series is not None and len(volume_proxy_series)>1:
        if volume_proxy_series.iloc[-1] > volume_proxy_series.iloc[-2]:
            vol_flag = 1

    support, resistance = calc_support_resistance(ohlcv_df['h'].tolist(), ohlcv_df['l'].tolist(), lookback=50)
    sr_flag_support = 1 if support is not None and abs(price - support)/support < 0.005 else 0
    sr_flag_res = 1 if resistance is not None and abs(price - resistance)/resistance < 0.005 else 0

    call_conditions = {
        'ema': 1 if (ema9.iloc[-1] > ema21.iloc[-1]) else 0,
        'price_above_emas': price_above_emas,
        'rsi_zone': rsi_call,
        'bollinger_touch': 1 if bb_touch=='lower' else 0,
        'candle_pattern': 1 if hammer else 0,
        'volume': vol_flag,
        'sr': sr_flag_support
    }
    put_conditions = {
        'ema': 1 if (ema9.iloc[-1] < ema21.iloc[-1]) else 0,
        'price_below_emas': 1 if not price_above_emas else 0,
        'rsi_zone': rsi_put,
        'bollinger_touch': 1 if bb_touch=='upper' else 0,
        'candle_pattern': 1 if shooting else 0,
        'volume': vol_flag,
        'sr': sr_flag_res
    }

    def score_and_build(conds):
        confluencias = sum(conds.values())
        score = 0.0
        # map weights by cond name; fallback uniform for unknowns
        for k,v in conds.items():
            w = WEIGHTS.get(k, 1.0/len(conds))
            score += w * float(v)
        prob = score * 100
        return {
            "confluencias": int(confluencias),
            "score": float(score),
            "probability": float(prob),
            "details": conds
        }

    call_res = score_and_build(call_conditions)
    put_res = score_and_build(put_conditions)

    candidate = None
    if call_res['confluencias'] >= MIN_CONFLUENCES:
        candidate = ("CALL", call_res)
    if put_res['confluencias'] >= MIN_CONFLUENCES and (candidate is None or put_res['probability'] > candidate[1]['probability']):
        candidate = ("PUT", put_res)

    if candidate:
        tipo, data = candidate
        signal = {
            "timestamp": pd.Timestamp.utcnow().isoformat(),
            "ativo": asset,
            "minuto_entrada": (last_idx + pd.Timedelta(minutes=1)).isoformat(),
            "tipo": tipo,
            "confluencias": int(data['confluencias']),
            "probabilidade": round(data['probability'],2),
            "detalhes": data['details'],
            "expiracao_sugerida_min": 2
        }
        return signal
    return None
