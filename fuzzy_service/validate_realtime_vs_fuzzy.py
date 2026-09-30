import pandas as pd
import numpy as np

from fuzzy_engine import FuzzyMamdaniEngine

from db import (
    get_stock_rows_by_date,
    get_sector_stats,
    get_fuzzy_rules,
    get_sentiment_value
)

from realtime_recommendation import (
    get_fundamental_data,
    get_realtime_data
)


# ============================================================
# KONFIGURASI VALIDASI
# ============================================================

STOCKDATA_ID = 52385
DATE = "2026-09-22"


# ============================================================
# 1. AMBIL DATA FUZZY RUN BIASA
# ============================================================

def get_fuzzy_data():

    print("\nMengambil data Fuzzy Run...")

    df = get_stock_rows_by_date(
        DATE,
        DATE
    )

    if df.empty:
        raise ValueError(
            f"Data stock_data untuk {DATE} tidak ditemukan."
        )

    # Cari stockdata_id yang ingin divalidasi
    df = df[
        df["stockdata_id"].astype(int)
        == STOCKDATA_ID
    ]

    if df.empty:
        raise ValueError(
            f"stockdata_id {STOCKDATA_ID} tidak ditemukan."
        )

    row = df.iloc[0].copy()

    ticker = row["ticker"]

    print(
        f"Data ditemukan: "
        f"{ticker} | "
        f"stockdata_id={STOCKDATA_ID}"
    )

    # --------------------------------------------------------
    # SENTIMEN
    # --------------------------------------------------------

    sent_v = get_sentiment_value(
        ticker
    )

    row["sent_v"] = sent_v

    if sent_v == 1.0:

        row["sentimen"] = "positif"

    elif sent_v == 0.0:

        row["sentimen"] = "negatif"

    else:

        row["sentimen"] = "netral"

    return row


# ============================================================
# 2. AMBIL DATA REALTIME
# ============================================================

def get_realtime_data_for_validation(
    ticker,
    sektor
):

    print("\nMengambil data Realtime...")

    # --------------------------------------------------------
    # FUNDAMENTAL
    # --------------------------------------------------------

    fundamental = get_fundamental_data(
        f"{ticker}.JK"
    )

    # --------------------------------------------------------
    # TECHNICAL
    # --------------------------------------------------------

    technical = get_realtime_data(
        ticker
    )

    # --------------------------------------------------------
    # SENTIMEN
    # --------------------------------------------------------

    sent_v = get_sentiment_value(
        ticker
    )

    if sent_v == 1.0:

        sentimen = "positif"

    elif sent_v == 0.0:

        sentimen = "negatif"

    else:

        sentimen = "netral"

    # --------------------------------------------------------
    # GABUNGKAN
    # --------------------------------------------------------

    data = {

        **fundamental,

        **technical,

        "sentimen": sentimen,

        "sent_v": sent_v,

        "Sektor": sektor,

        "ticker": ticker
    }

    return pd.Series(data)


# ============================================================
# 3. TAMPILKAN DATA INPUT
# ============================================================

def print_input_comparison(
    fuzzy_data,
    realtime_data
):

    print("\n")
    print("=" * 100)
    print("PERBANDINGAN DATA INPUT")
    print("=" * 100)

    print(
        f"{'VARIABEL':15}"
        f"{'FUZZY RUN':25}"
        f"{'REALTIME':25}"
        f"{'STATUS'}"
    )

    print("-" * 100)

    variables = [

        "eps",
        "per",
        "roe",
        "der",
        "fcf",

        "close_price",
        "ma50",
        "ma200",
        "volume",
        "volma200",
        "rsi",
        "gradient",

        "sent_v",
        "sentimen"
    ]

    for variable in variables:

        fuzzy_value = fuzzy_data.get(
            variable,
            None
        )

        realtime_value = realtime_data.get(
            variable,
            None
        )

        # ----------------------------------------------------
        # PERBANDINGAN ANGKA
        # ----------------------------------------------------

        if (
            isinstance(
                fuzzy_value,
                (int, float, np.integer, np.floating)
            )
            and
            isinstance(
                realtime_value,
                (int, float, np.integer, np.floating)
            )
        ):

            if (
                pd.isna(fuzzy_value)
                and
                pd.isna(realtime_value)
            ):

                same = True

            elif (
                pd.isna(fuzzy_value)
                or
                pd.isna(realtime_value)
            ):

                same = False

            else:

                same = np.isclose(
                    float(fuzzy_value),
                    float(realtime_value),
                    rtol=1e-6,
                    atol=1e-8
                )

        else:

            same = (
                fuzzy_value
                ==
                realtime_value
            )

        status = (
            "SAMA"
            if same
            else
            "BERBEDA"
        )

        print(
            f"{variable:15}"
            f"{str(fuzzy_value):25}"
            f"{str(realtime_value):25}"
            f"{status}"
        )


# ============================================================
# 4. EVALUASI FUZZY
# ============================================================

def evaluate_engine(
    row,
    engine
):

    row = row.copy()

    return engine.evaluate(
        row
    )


# ============================================================
# 5. TAMPILKAN HASIL
# ============================================================

def print_fuzzy_result(
    title,
    result
):

    print("\n")
    print("=" * 100)
    print(title)
    print("=" * 100)

    print(
        f"Score        : "
        f"{result.get('score')}"
    )

    print(
        f"Kategori     : "
        f"{result.get('label')}"
    )

    print(
        f"Horizon      : "
        f"{result.get('horizon')}"
    )

    print(
        f"Rule ID      : "
        f"{result.get('rule_id')}"
    )

    print(
        f"Rule         : "
        f"{result.get('rule_condition')}"
    )

    print(
        f"Firing       : "
        f"{result.get('firing_strength')}"
    )

    print("\nMembership")
    print("-" * 100)

    membership = result.get(
        "mbs",
        {}
    )

    for variable, values in membership.items():

        print(
            f"{variable:15}: {values}"
        )


# ============================================================
# 6. BANDINGKAN MEMBERSHIP
# ============================================================

def compare_membership(
    fuzzy_result,
    realtime_result
):

    print("\n")
    print("=" * 100)
    print("PERBANDINGAN MEMBERSHIP")
    print("=" * 100)

    fuzzy_mbs = fuzzy_result.get(
        "mbs",
        {}
    )

    realtime_mbs = realtime_result.get(
        "mbs",
        {}
    )

    variables = sorted(
        set(fuzzy_mbs.keys())
        |
        set(realtime_mbs.keys())
    )

    all_same = True

    for variable in variables:

        fuzzy_values = fuzzy_mbs.get(
            variable,
            {}
        )

        realtime_values = realtime_mbs.get(
            variable,
            {}
        )

        members = sorted(
            set(fuzzy_values.keys())
            |
            set(realtime_values.keys())
        )

        variable_same = True

        for member in members:

            fuzzy_value = fuzzy_values.get(
                member,
                0.0
            )

            realtime_value = realtime_values.get(
                member,
                0.0
            )

            if not np.isclose(
                float(fuzzy_value),
                float(realtime_value),
                rtol=1e-6,
                atol=1e-8
            ):

                variable_same = False

        if not variable_same:

            all_same = False

        print(
            f"\n{variable}"
        )

        print(
            f"  Fuzzy    : "
            f"{fuzzy_values}"
        )

        print(
            f"  Realtime : "
            f"{realtime_values}"
        )

        print(
            f"  Status   : "
            f"{'SAMA' if variable_same else 'BERBEDA'}"
        )

    return all_same


# ============================================================
# 7. BANDINGKAN OUTPUT
# ============================================================

def compare_output(
    fuzzy_result,
    realtime_result
):

    print("\n")
    print("=" * 100)
    print("PERBANDINGAN OUTPUT")
    print("=" * 100)

    checks = [

        (
            "Score",
            fuzzy_result.get("score"),
            realtime_result.get("score")
        ),

        (
            "Kategori",
            fuzzy_result.get("label"),
            realtime_result.get("label")
        ),

        (
            "Horizon",
            fuzzy_result.get("horizon"),
            realtime_result.get("horizon")
        ),

        (
            "Rule ID",
            fuzzy_result.get("rule_id"),
            realtime_result.get("rule_id")
        ),

        (
            "Firing",
            fuzzy_result.get("firing_strength"),
            realtime_result.get("firing_strength")
        )
    ]

    all_same = True

    for name, fuzzy_value, realtime_value in checks:

        if (
            isinstance(
                fuzzy_value,
                (int, float)
            )
            and
            isinstance(
                realtime_value,
                (int, float)
            )
        ):

            same = np.isclose(
                float(fuzzy_value),
                float(realtime_value),
                rtol=1e-6,
                atol=1e-8
            )

        else:

            same = (
                fuzzy_value
                ==
                realtime_value
            )

        if not same:

            all_same = False

        print(
            f"\n{name}"
        )

        print(
            f"  Fuzzy Run : {fuzzy_value}"
        )

        print(
            f"  Realtime  : {realtime_value}"
        )

        print(
            f"  Status    : "
            f"{'SAMA' if same else 'BERBEDA'}"
        )

    return all_same


# ============================================================
# 8. MAIN VALIDASI
# ============================================================

def main():

    print("\n")
    print("#" * 100)
    print("# VALIDASI FUZZY RUN VS REALTIME")
    print("#" * 100)

    print(
        f"\nStockdata ID : {STOCKDATA_ID}"
    )

    print(
        f"Tanggal      : {DATE}"
    )

    # ========================================================
    # DATA FUZZY RUN
    # ========================================================

    fuzzy_data = get_fuzzy_data()

    ticker = fuzzy_data["ticker"]

    sektor = fuzzy_data["Sektor"]

    print(
        f"Ticker       : {ticker}"
    )

    print(
        f"Sektor       : {sektor}"
    )

    # ========================================================
    # DATA REALTIME
    # ========================================================

    realtime_data = (
        get_realtime_data_for_validation(
            ticker,
            sektor
        )
    )

    # ========================================================
    # BANDINGKAN INPUT
    # ========================================================

    print_input_comparison(
        fuzzy_data,
        realtime_data
    )

    # ========================================================
    # AMBIL RULE
    # ========================================================

    rules_df = get_fuzzy_rules()

    if rules_df.empty:

        raise ValueError(
            "Rule fuzzy kosong."
        )

    # ========================================================
    # AMBIL SECTOR STATS
    # ========================================================

    sector_stats = get_sector_stats()

    if sector_stats.empty:

        raise ValueError(
            "Sector stats kosong."
        )

    # ========================================================
    # BUAT FUZZY ENGINE
    # ========================================================

    engine = FuzzyMamdaniEngine(
        sector_stats,
        rules_df
    )

    # ========================================================
    # EVALUASI FUZZY RUN
    # ========================================================

    fuzzy_result = evaluate_engine(
        fuzzy_data,
        engine
    )

    print_fuzzy_result(
        "HASIL FUZZY RUN BIASA",
        fuzzy_result
    )

    # ========================================================
    # EVALUASI REALTIME
    # ========================================================

    realtime_result = evaluate_engine(
        realtime_data,
        engine
    )

    print_fuzzy_result(
        "HASIL REALTIME",
        realtime_result
    )

    # ========================================================
    # BANDINGKAN MEMBERSHIP
    # ========================================================

    membership_same = compare_membership(
        fuzzy_result,
        realtime_result
    )

    # ========================================================
    # BANDINGKAN OUTPUT
    # ========================================================

    output_same = compare_output(
        fuzzy_result,
        realtime_result
    )

    # ========================================================
    # KESIMPULAN
    # ========================================================

    print("\n")
    print("#" * 100)
    print("# KESIMPULAN VALIDASI")
    print("#" * 100)

    print(
        f"\nMembership : "
        f"{'SAMA' if membership_same else 'BERBEDA'}"
    )

    print(
        f"Output     : "
        f"{'SAMA' if output_same else 'BERBEDA'}"
    )

    if (
        membership_same
        and
        output_same
    ):

        print(
            "\n✅ HASIL FUZZY RUN DAN REALTIME SAMA"
        )

    else:

        print(
            "\n⚠️ HASIL FUZZY RUN DAN REALTIME BERBEDA"
        )

        print(
            "Lihat bagian PERBANDINGAN DATA INPUT "
            "dan PERBANDINGAN MEMBERSHIP."
        )


# ============================================================
# JALANKAN
# ============================================================

if __name__ == "__main__":

    main()