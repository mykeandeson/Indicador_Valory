# indicators.py
import numpy as np
import pandas as pd

def ema(series: pd.Series, period: int):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rs = ma_up / (ma_down + 1e-9)
    return 100 - (100 / (1 + rs))

def bollinger_bands(series: pd.Series, period: int = 20, std: int = 2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    upper = ma + std * sd
    lower = ma - std * sd
    return upper, ma, lower

def detect_hammer(candle):
    o,h,l,c = candle['o'], candle['h'], candle['l'], candle['c']
    body = abs(c - o)
    lower_wick = min(o,c) - l
    upper_wick = h - max(o,c)
    if body == 0:
        return False
    return (lower_wick >= 2*body) and (upper_wick <= 0.5*body)

def detect_shooting_star(candle):
    o,h,l,c = candle['o'], candle['h'], candle['l'], candle['c']
    body = abs(c - o)
    upper_wick = h - max(o,c)
    lower_wick = min(o,c) - l
    if body == 0:
        return False
    return (upper_wick >= 2*body) and (lower_wick <= 0.5*body)

def is_bollinger_touch(price, upper, lower, prox=0.002):
    if price >= upper*(1-prox):
        return "upper"
    if price <= lower*(1+prox):
        return "lower"
    return None

def calc_support_resistance(highs, lows, lookback=50):
    recent_high = max(highs[-lookback:]) if len(highs)>=1 else None
    recent_low = min(lows[-lookback:]) if len(lows)>=1 else None
    return recent_low, recent_high
