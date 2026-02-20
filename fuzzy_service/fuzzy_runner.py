import pandas as pd
from fuzzy_engine import FuzzyMamdaniEngine
from db import (
    get_latest_stock_rows,
    get_sector_stats,
    get_fuzzy_rules,
    get_sentiment_value,
    save_fuzzy_membership,
    save_fuzzy_output
)

def run_fuzzy():
    # =========================
    # AMBIL DATA
    # =========================
    df_stock = get_latest_stock_rows()
    rules_df = get_fuzzy_rules()
    sector_stats = get_sector_stats()

    if df_stock.empty:
        return {"status": "tidak ada data stock"}

    if rules_df.empty:
        return {"status": "rule fuzzy kosong"}

    if sector_stats.empty:
        return {"status": "sector_stats kosong"}

    # =========================
    # INIT ENGINE
    # =========================
    engine = FuzzyMamdaniEngine(sector_stats, rules_df)

    results = []

    # =========================
    # LOOP PER SAHAM
    # =========================
    for _, r in df_stock.iterrows():
        # 🔒 copy agar aman
        row = r.copy()

        ticker = row["ticker"]
        stockdata_id = row["stockdata_id"]

        # =====================
        # SENTIMEN → NUMERIK
        # =====================
        row["sent_v"] = get_sentiment_value(ticker)

        # =====================
        # FUZZY EVALUATION
        # =====================
        res = engine.evaluate(row)

        # =====================
        # SIMPAN MEMBERSHIP
        # =====================
        save_fuzzy_membership(
            stockdata_id=stockdata_id,
            mbs=res["mbs"]
        )

        # =====================
        # SIMPAN OUTPUT AKHIR
        # =====================
        save_fuzzy_output(
            stockdata_id=stockdata_id,
            score=res["score"],
            kategori=res["label"],
            horizon=res["horizon"]
        )

        results.append({
            "ticker": ticker,
            "score": res["score"],
            "label": res["label"],
            "horizon": res["horizon"]
        })

    return {
        "status": "fuzzy selesai",
        "total": len(results),
        "results": results
    }
