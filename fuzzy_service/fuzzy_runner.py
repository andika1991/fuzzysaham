import pandas as pd
from datetime import date

from fuzzy_engine import FuzzyMamdaniEngine

from db import (
    get_stock_rows_by_date,
    get_latest_stock_rows,
    get_sector_stats,
    get_fuzzy_rules,
    get_sentiment_value,
    save_fuzzy_membership,
    save_fuzzy_output
)


def run_fuzzy(
    mode="daily",
    start_date=None,
    end_date=None
):

    # =====================================================
    # TENTUKAN DATA YANG AKAN DIPROSES
    # =====================================================

    if mode == "custom":

        if not start_date or not end_date:

            return {
                "status": "error",
                "message": (
                    "start_date dan end_date "
                    "wajib diisi untuk mode custom"
                )
            }

        # ---------------------------------------------
        # AMBIL DATA SESUAI RENTANG TANGGAL
        # ---------------------------------------------

        df_stock = get_stock_rows_by_date(
            start_date,
            end_date
        )

    else:

        # ---------------------------------------------
        # DAILY
        # ---------------------------------------------

        df_stock = get_latest_stock_rows()


    # =====================================================
    # AMBIL RULE FUZZY
    # =====================================================

    rules_df = get_fuzzy_rules()


    # =====================================================
    # AMBIL SECTOR STATS
    # =====================================================

    sector_stats = get_sector_stats()


    # =====================================================
    # VALIDASI DATA STOCK
    # =====================================================

    if df_stock.empty:

        return {
            "status": "tidak ada data stock",
            "mode": mode,
            "start_date": start_date,
            "end_date": end_date
        }


    # =====================================================
    # VALIDASI RULE
    # =====================================================

    if rules_df.empty:

        return {
            "status": "rule fuzzy kosong"
        }


    # =====================================================
    # VALIDASI SECTOR STATS
    # =====================================================

    if sector_stats.empty:

        return {
            "status": "sector_stats kosong"
        }


    # =====================================================
    # INIT FUZZY ENGINE
    # =====================================================

    engine = FuzzyMamdaniEngine(
        sector_stats,
        rules_df
    )


    # =====================================================
    # HASIL
    # =====================================================

    results = []


    # =====================================================
    # LOOP PER DATA SAHAM
    # =====================================================

    for _, r in df_stock.iterrows():

        row = r.copy()

        ticker = row["ticker"]

        stockdata_id = row["stockdata_id"]


        # =================================================
        # SENTIMEN → NUMERIK
        # =================================================

        row["sent_v"] = get_sentiment_value(
            ticker
        )


        # =================================================
        # FUZZY EVALUATION
        # =================================================

        res = engine.evaluate(
            row
        )


        # =================================================
        # DEBUG
        # =================================================

        print(
            "DEBUG FUZZY:",
            ticker,
            res["rule_id"],
            res["rule_condition"],
            res["firing_strength"]
        )


        # =================================================
        # SIMPAN MEMBERSHIP
        # =================================================

        save_fuzzy_membership(

            stockdata_id=stockdata_id,

            mbs=res["mbs"]

        )


        # =================================================
        # SIMPAN OUTPUT
        # =================================================

        save_fuzzy_output(

            stockdata_id=stockdata_id,

            score=res["score"],

            kategori=res["label"],

            horizon=res["horizon"],

            rule_id=res["rule_id"],

            rule_condition=res["rule_condition"],

            firing_strength=res["firing_strength"]

        )


        # =================================================
        # SIMPAN HASIL KE RESPONSE
        # =================================================

        result_item = {

            "ticker": ticker,

            "stockdata_id": int(
                stockdata_id
            ),

            "score": res["score"],

            "label": res["label"],

            "horizon": res["horizon"],

            "rule_id": res["rule_id"],

            "rule_condition": res["rule_condition"],

            "firing_strength": res[
                "firing_strength"
            ]

        }


        # Tambahkan tanggal jika tersedia
        if "date" in row:

            result_item["date"] = str(
                row["date"]
            )


        results.append(
            result_item
        )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "status": "fuzzy selesai",
        "mode": mode,
        "start_date": start_date,
        "end_date": end_date,
        "total": len(results),
        "results": results

    }