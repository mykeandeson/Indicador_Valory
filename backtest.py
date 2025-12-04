# backtest.py
import argparse
import pandas as pd
import json
from db import engine
from signal_engine import evaluate_signal
from sqlalchemy import text
from datetime import timedelta
import logging

LOG = logging.getLogger("backtest")
LOG.setLevel(logging.INFO)

def load_from_db(asset):
    sql = text("SELECT timestamp, o, h, l, c, v FROM candles WHERE ativo = :asset ORDER BY timestamp")
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"asset": asset}, parse_dates=["timestamp"])
    if df.empty:
        return None
    df = df.set_index("timestamp")
    return df

def load_from_csv(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.set_index("timestamp")
    return df

def simulate(df, asset, expiration_min=2):
    results = []
    df = df.sort_index()
    min_history = 50
    for i in range(min_history, len(df)-expiration_min):
        window = df.iloc[:i+1]
        signal = evaluate_signal(window, asset)
        if not signal:
            continue
        entry_time = pd.to_datetime(signal['minuto_entrada'])
        try:
            price_entry = df.loc[entry_time - pd.Timedelta(minutes=1)]['c']
        except Exception:
            price_entry = window['c'].iloc[-1]
        try:
            price_out = df.iloc[i+expiration_min]['c']
        except Exception:
            continue
        direction = 1 if (signal['tipo']=='CALL' and price_out > price_entry) or (signal['tipo']=='PUT' and price_out < price_entry) else 0
        results.append({
            "timestamp": signal['minuto_entrada'],
            "asset": asset,
            "tipo": signal['tipo'],
            "confluencias": signal['confluencias'],
            "probability": signal['probabilidade'],
            "result": direction
        })
    return results

def run_backtest(assets, csv_map=None, expiration_min=2, out_csv="backtest_results.csv"):
    all_results = []
    for asset in assets:
        if csv_map and asset in csv_map:
            df = load_from_csv(csv_map[asset])
        else:
            df = load_from_db(asset)
        if df is None or df.empty:
            LOG.warning(f"No data for {asset}")
            continue
        res = simulate(df, asset, expiration_min=expiration_min)
        all_results.extend(res)
    if not all_results:
        LOG.info("No signals found in backtest")
        return None
    dfres = pd.DataFrame(all_results)
    dfres.to_csv(out_csv, index=False)
    LOG.info(f"Backtest saved to {out_csv}")
    report = {}
    grouped = dfres.groupby("confluencias")
    for name, g in grouped:
        report[name] = {
            "count": len(g),
            "win_rate": float(g['result'].mean() * 100)
        }
    dfres['prob_bucket'] = (pd.cut(dfres['probability'], bins=[0,50,60,70,80,90,100], labels=["<50","50-60","60-70","70-80","80-90","90-100"]))
    pb = dfres.groupby('prob_bucket')['result'].agg(['count','mean']).reset_index()
    pb['win_rate'] = pb['mean']*100
    out = {"by_confluences": report, "by_prob_bucket": pb.to_dict(orient='records')}
    cal_path = "calibration.json"
    with open(cal_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    LOG.info(f"Calibration saved to {cal_path}")
    return dfres, out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", nargs="+", help="assets to backtest", required=True)
    parser.add_argument("--csv_map", help="optional mapping JSON file with asset->csvpath", default=None)
    parser.add_argument("--expiration", type=int, default=2)
    parser.add_argument("--out", default="backtest_results.csv")
    args = parser.parse_args()
    csv_map = None
    if args.csv_map:
        csv_map = json.load(open(args.csv_map))
    run_backtest(args.assets, csv_map=csv_map, expiration_min=args.expiration, out_csv=args.out)
