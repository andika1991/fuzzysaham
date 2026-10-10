import pandas as pd
import numpy as np

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


def prepare_fuzzy_row(row):

    row = row.copy()

    # =====================================================
    # GRADIENT H-1
    # =====================================================

    if "g_h1" not in row.index:

        if "gradient_h1" in row.index:
            row["g_h1"] = row["gradient_h1"]

        else:
            row["g_h1"] = np.nan


    # =====================================================
    # GRADIENT H-5
    # =====================================================

    if "g_h5" not in row.index:

        if "gradient_h5" in row.index:
            row["g_h5"] = row["gradient_h5"]

        else:
            row["g_h5"] = np.nan


    # =====================================================
    # GRADIENT AKHIR
    # =====================================================

    if (
        pd.notna(row["g_h1"])
        and pd.notna(row["g_h5"])
    ):

        row["gradient"] = (
            0.70 * row["g_h1"] +
            0.30 * row["g_h5"]
        )

    elif pd.notna(row["g_h1"]):

        row["gradient"] = row["g_h1"]

    elif pd.notna(row["g_h5"]):

        row["gradient"] = row["g_h5"]

    else:

        row["gradient"] = np.nan


    # =====================================================
    # VOLUME RATIO
    # =====================================================

    if (
        "volume_ratio" not in row.index
        or pd.isna(row["volume_ratio"])
    ):

        required = [
            "volume",
            "volma20",
            "volma50",
            "volma100",
            "volma200"
        ]

        if all(
            col in row.index
            and pd.notna(row[col])
            for col in required
        ):

            if (
                row["volma20"] != 0
                and row["volma50"] != 0
                and row["volma100"] != 0
                and row["volma200"] != 0
            ):

                d20 = (
                    row["volume"] -
                    row["volma20"]
                ) / row["volma20"]

                d50 = (
                    row["volume"] -
                    row["volma50"]
                ) / row["volma50"]

                d100 = (
                    row["volume"] -
                    row["volma100"]
                ) / row["volma100"]

                d200 = (
                    row["volume"] -
                    row["volma200"]
                ) / row["volma200"]

                row["volume_ratio"] = (
                    0.40 * d20 +
                    0.30 * d50 +
                    0.20 * d100 +
                    0.10 * d200
                )

            else:

                row["volume_ratio"] = np.nan

        else:

            row["volume_ratio"] = np.nan


    return row


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

        df_stock = get_stock_rows_by_date(
            start_date,
            end_date
        )

    else:

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
    # VALIDASI DATA
    # =====================================================

    if df_stock.empty:

        return {
            "status": "tidak ada data stock",
            "mode": mode,
            "start_date": start_date,
            "end_date": end_date
        }


    if rules_df.empty:

        return {
            "status": "rule fuzzy kosong"
        }


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
    # LOOP DATA SAHAM
    # =====================================================

    for _, r in df_stock.iterrows():

        row = prepare_fuzzy_row(r)

        ticker = row["ticker"]

        stockdata_id = row["stockdata_id"]


        # =================================================
        # SENTIMEN
        # =================================================

        row["sent_v"] = get_sentiment_value(
            ticker
        )


        # =================================================
        # DEBUG INPUT
        # =================================================

        print(
            "\nDEBUG INPUT:",
            ticker
        )

        print(
            "Gradient H-1 :",
            row.get("g_h1")
        )

        print(
            "Gradient H-5 :",
            row.get("g_h5")
        )

        print(
            "Gradient Akhir :",
            row.get("gradient")
        )

        print(
            "Volume Ratio :",
            row.get("volume_ratio")
        )


        # =================================================
        # FUZZY EVALUATION
        # =================================================

        res = engine.evaluate(
            row
        )


        # =================================================
        # DEBUG FUZZY
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
        # RESPONSE
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

            "rule_condition": res[
                "rule_condition"
            ],

            "firing_strength": res[
                "firing_strength"
            ]

        }


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