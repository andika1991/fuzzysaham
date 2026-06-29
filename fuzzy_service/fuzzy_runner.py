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
        row = r.copy()

        ticker = row["ticker"]
        stockdata_id = row["stockdata_id"]

        # =====================
        # SENTIMEN -> NUMERIK
        # =====================
        row["sent_v"] = get_sentiment_value(ticker)

        # =====================
        # FUZZY EVALUATION
        # =====================
        res = engine.evaluate(row)

        # Debug sementara
        print("DEBUG FUZZY:", ticker, res["rule_id"], res["rule_condition"], res["firing_strength"])

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
            horizon=res["horizon"],
            rule_id=res["rule_id"],
            rule_condition=res["rule_condition"],
            firing_strength=res["firing_strength"]
        )

        results.append({
            "ticker": ticker,
            "score": res["score"],
            "label": res["label"],
            "horizon": res["horizon"],
            "rule_id": res["rule_id"],
            "rule_condition": res["rule_condition"],
            "firing_strength": res["firing_strength"]
        })

    return {
        "status": "fuzzy selesai",
        "total": len(results),
        "results": results
    }