import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import time

from db import get_conn, get_lq45_stocks


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (
        delta
        .where(delta > 0, 0)
        .rolling(period)
        .mean()
    )
    loss = (
        -delta
        .where(delta < 0, 0)
        .rolling(period)
        .mean()
    )

    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_fcf(yf_ticker):

    try:
        t = yf.Ticker(yf_ticker)
        cf = t.cashflow
        if cf is None or cf.empty:
            print( f"   ⚠️ FCF kosong: {yf_ticker}")
            return None
        cf.index = cf.index.str.lower()

        for key in cf.index:
            if "free cash flow" in key:
                val = cf.loc[key].iloc[0]
                if pd.notna(val):
                    return float(val)

        ocf = None
        capex = None

        for key in cf.index:
            if (
                "operating" in key
                and ocf is None
            ):
                ocf = cf.loc[key].iloc[0]
            if (
                "capital" in key
                or "capex" in key
            ) and capex is None:
                capex = cf.loc[key].iloc[0]
        if (
            ocf is not None
            and capex is not None
            and pd.notna(ocf)
            and pd.notna(capex)
        ):
            return float(ocf - capex)
        print(
            f"   ⚠️ FCF tidak ditemukan lengkap: "
            f"{yf_ticker}"
        )
        return None
    except Exception as e:
        print(
            f"[FCF ERROR] {yf_ticker}: {e}")
        return None

def get_existing_stock_dates(
    id_stock,
    start_date,
    end_date
):

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT date
            FROM stock_data
            WHERE id_stock = %s
              AND date BETWEEN %s AND %s
            """,
            (
                id_stock,
                start_date,
                end_date
            )
        )

        rows = cur.fetchall()
        return {
            row[0]
            for row in rows
        }

    finally:
        cur.close()
        conn.close()

def insert_stock_data(rows):

    if not rows:
        return
    conn = get_conn()
    cur = conn.cursor()
    sql = """
    INSERT INTO stock_data
    (
        date,
        close_price,
        eps,
        per,
        roe,
        der,
        fcf,
        ma50,
        ma200,
        volume,
        volma200,
        rsi,
        sentimen,
        id_stock
    )
    VALUES
    (
        %s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s,%s
    )
    ON DUPLICATE KEY UPDATE
        close_price = VALUES(close_price),
        volume = VALUES(volume),
        rsi = VALUES(rsi),
        ma50 = VALUES(ma50),
        ma200 = VALUES(ma200),
        volma200 = VALUES(volma200),
        fcf = VALUES(fcf)
    """
    cur.executemany(
        sql,
        rows
    )

    conn.commit()
    cur.close()
    conn.close()

def get_recent_prices(
    id_stock,
    limit=200
):

    conn = get_conn()
    cur = conn.cursor(
        dictionary=True
    )
    cur.execute(
        """
        SELECT date,close_price,volume FROM stock_data WHERE id_stock = %s ORDER BY date DESC
        LIMIT %s
        """,
        (
            id_stock,
            limit
        )
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.sort_values(
        "date"
    )
    return df

def update_technical_indicators(
    id_stock,
    ticker,
    period_days=730
):
    """
    Hitung indikator teknikal langsung dari Yahoo Finance.
    Database hanya digunakan untuk menyimpan hasilnya.
    """

    yf_ticker = (
        ticker if ticker.endswith(".JK")
        else f"{ticker}.JK"
    )

    today = dt.datetime.today()
    fetch_start_date = (
        today - dt.timedelta(days=period_days)
    )
    fetch_end_date = today + dt.timedelta(days=1)

    try:
        df = yf.download(
            yf_ticker,
            start=fetch_start_date,
            end=fetch_end_date,
            auto_adjust=False,
            progress=False,
            threads=False
        )
    except Exception as e:
        print(
            f"   [TECHNICAL ERROR] {yf_ticker}: {e}"
        )
        return None

    if df.empty:
        print(
            f"   ⚠️ Data Yahoo kosong: {yf_ticker}"
        )
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = (
            df.columns
            .get_level_values(0)
        )

    df = df.rename(
        columns={
            "Close": "close_price",
            "Volume": "volume"
        }
    )

    df.reset_index(inplace=True)

    df.rename(
        columns={
            "Date": "date"
        },
        inplace=True
    )

    df = df.sort_values("date").copy()

    # MA50
    df["ma50"] = (
        df["close_price"]
        .rolling(
            window=50,
            min_periods=50
        )
        .mean()
    )

    # MA200
    df["ma200"] = (
        df["close_price"]
        .rolling(
            window=200,
            min_periods=200
        )
        .mean()
    )

    # Volume MA200
    df["volma200"] = (
        df["volume"]
        .rolling(
            window=200,
            min_periods=200
        )
        .mean()
    )

    # RSI 14
    df["rsi"] = compute_rsi(
        df["close_price"]
    )

    latest = df.iloc[-1]

    result = {
        "date": pd.to_datetime(
            latest["date"]
        ).date(),
        "close_price": (
            float(latest["close_price"])
            if pd.notna(latest["close_price"])
            else None
        ),
        "volume": (
            int(latest["volume"])
            if pd.notna(latest["volume"])
            else None
        ),
        "ma50": (
            float(latest["ma50"])
            if pd.notna(latest["ma50"])
            else None
        ),
        "ma200": (
            float(latest["ma200"])
            if pd.notna(latest["ma200"])
            else None
        ),
        "volma200": (
            float(latest["volma200"])
            if pd.notna(latest["volma200"])
            else None
        ),
        "rsi": (
            float(latest["rsi"])
            if pd.notna(latest["rsi"])
            else None
        )
    }

    print(
        f"   📊 {yf_ticker} Yahoo:"
        f" Close={result['close_price']},"
        f" MA50={result['ma50']},"
        f" MA200={result['ma200']},"
        f" VolMA200={result['volma200']},"
        f" RSI={result['rsi']}"
    )

    return result


# ============================================================
# FETCH & SIMPAN DATA SAHAM
# ============================================================

# ============================================================
# FETCH & SIMPAN DATA SAHAM
# ============================================================

def fetch_and_save_stock_data(
    mode="daily",
    years=5,
    start_date=None,
    end_date=None
):

    # ========================================================
    # AMBIL DAFTAR SAHAM LQ45
    # ========================================================

    stocks = get_lq45_stocks()

    today = dt.datetime.today()

    # ========================================================
    # TENTUKAN PERIODE
    # ========================================================

    if mode == "daily":

        # Download data historis 2 tahun
        # agar MA200 dihitung dari data Yahoo yang cukup
        start_date = today
        end_date = today

        fetch_start_date = (
            today -
            dt.timedelta(days=730)
        )

        fetch_end_date = (
            today +
            dt.timedelta(days=1)
        )

        print("🕔 MODE DAILY")

        print(
            f"   Target data: "
            f"{today.date()}"
        )

        print(
            f"   Periode download: "
            f"{fetch_start_date.date()} "
            f"→ {fetch_end_date.date()}"
        )

    elif mode == "full":

        try:

            start_date = today.replace(
                year=today.year - years
            )

        except ValueError:

            start_date = today.replace(
                year=today.year - years,
                day=28
            )

        end_date = today

        fetch_start_date = start_date

        fetch_end_date = (
            end_date +
            dt.timedelta(days=1)
        )

        print("📦 MODE FULL HISTORY")

        print(
            f"   Periode: "
            f"{start_date.date()} "
            f"→ {end_date.date()}"
        )

        print(
            f"   Total: {years} tahun"
        )

    elif mode == "custom":

        if not start_date:

            raise ValueError(
                "start_date wajib diisi."
            )

        if not end_date:

            raise ValueError(
                "end_date wajib diisi."
            )

        if isinstance(start_date, str):

            start_date = dt.datetime.strptime(
                start_date,
                "%Y-%m-%d"
            )

        if isinstance(end_date, str):

            end_date = dt.datetime.strptime(
                end_date,
                "%Y-%m-%d"
            )

        if start_date > end_date:

            raise ValueError(
                "start_date tidak boleh "
                "lebih besar dari end_date."
            )

        # Download data historis tambahan
        # untuk perhitungan indikator
        fetch_start_date = (
            start_date -
            dt.timedelta(days=365)
        )

        fetch_end_date = (
            end_date +
            dt.timedelta(days=1)
        )

        print("📅 MODE CUSTOM")

        print(
            f"   Periode simpan: "
            f"{start_date.date()} "
            f"→ {end_date.date()}"
        )

        print(
            f"   Periode download indikator: "
            f"{fetch_start_date.date()} "
            f"→ {fetch_end_date.date()}"
        )

    else:

        raise ValueError(
            "Mode harus daily, custom, atau full."
        )

    # ========================================================
    # LOOP SAHAM
    # ========================================================

    total_stocks = len(stocks)

    processed = 0
    skipped = 0

    for index, s in enumerate(
        stocks,
        start=1
    ):

        ticker = s["ticker"]

        id_stock = s["id_stock"]

        yf_ticker = f"{ticker}.JK"

        print(
            f"\n[{index}/{total_stocks}] "
            f"🔎 Cek {yf_ticker}"
        )

        # ====================================================
        # CEK DATA YANG SUDAH ADA
        # ====================================================

        existing_dates = get_existing_stock_dates(
            id_stock,
            start_date.date(),
            end_date.date()
        )

        if existing_dates:

            print(
                f"   ℹ️ Data yang sudah ada: "
                f"{len(existing_dates)} tanggal"
            )

        # ====================================================
        # FETCH DATA DARI YFINANCE
        # ====================================================

        print(
            f"   📥 Fetch {yf_ticker}"
        )

        try:

            df = yf.download(

                yf_ticker,

                start=fetch_start_date,

                end=fetch_end_date,

                auto_adjust=False,

                progress=False,

                threads=False

            )

        except Exception as e:

            print(
                "❌ Download error:",
                e
            )

            continue

        # ====================================================
        # DATA KOSONG
        # ====================================================

        if df.empty:

            print(
                "⚠️ Data kosong"
            )

            continue

        # ====================================================
        # HANDLE MULTI INDEX
        # ====================================================

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):

            df.columns = (
                df.columns
                .get_level_values(0)
            )

        # ====================================================
        # RENAME
        # ====================================================

        df = df.rename(

            columns={

                "Close":
                    "close_price",

                "Volume":
                    "volume"

            }

        )

        # ====================================================
        # RESET INDEX
        # ====================================================

        df.reset_index(
            inplace=True
        )

        df.rename(

            columns={

                "Date":
                    "date"

            },

            inplace=True

        )

        # ====================================================
        # SORT
        # ====================================================

        df = df.sort_values(
            "date"
        )

        # ====================================================
        # NORMALISASI TANGGAL
        # ====================================================

        df["_date_only"] = (

            pd.to_datetime(
                df["date"]
            ).dt.date

        )

        # ====================================================
        # HITUNG INDIKATOR TEKNIKAL
        # ====================================================

        # ----------------------------------------------------
        # MA50
        # ----------------------------------------------------

        df["ma50"] = (

            df["close_price"]

            .rolling(

                window=50,

                min_periods=50

            )

            .mean()

        )

        # ----------------------------------------------------
        # MA200
        # ----------------------------------------------------

        df["ma200"] = (

            df["close_price"]

            .rolling(

                window=200,

                min_periods=200

            )

            .mean()

        )

        # ----------------------------------------------------
        # VOLMA200
        # ----------------------------------------------------

        df["volma200"] = (

            df["volume"]

            .rolling(

                window=200,

                min_periods=200

            )

            .mean()

        )

        # ----------------------------------------------------
        # RSI
        # ----------------------------------------------------

        df["rsi"] = compute_rsi(

            df["close_price"]

        )

        # ----------------------------------------------------
        # DEBUG NILAI TERBARU DARI YAHOO
        # ----------------------------------------------------

        latest_debug = df.iloc[-1]

        print(
            f"   🔎 YAHOO RESULT {yf_ticker}: "
            f"Close={latest_debug['close_price']}, "
            f"MA50={latest_debug['ma50']}, "
            f"MA200={latest_debug['ma200']}, "
            f"VolMA200={latest_debug['volma200']}, "
            f"RSI={latest_debug['rsi']}"
        )

        # ====================================================
        # TENTUKAN DATA YANG AKAN DISIMPAN
        # ====================================================

        if mode == "daily":

            # Mode daily selalu memakai data Yahoo terbaru.
            # Tanggal terbaru tetap diproses meskipun sudah ada di database,
            # sehingga nilai MA50, MA200, VolMA200, dan RSI diperbarui.

            df = (
                df
                .sort_values("date")
                .tail(1)
                .copy()
            )

        elif mode == "custom":

            # Hanya simpan tanggal
            # sesuai periode yang diminta

            df = df[

                (
                    df["_date_only"]
                    >= start_date.date()
                )

                &

                (
                    df["_date_only"]
                    <= end_date.date()
                )

            ].copy()

            # Buang tanggal yang sudah ada

            df = df[

                ~df["_date_only"].isin(
                    existing_dates
                )

            ].copy()

        elif mode == "full":

            # Untuk full, simpan seluruh periode
            # dan buang tanggal yang sudah ada

            df = df[

                ~df["_date_only"].isin(
                    existing_dates
                )

            ].copy()

        # ====================================================
        # TIDAK ADA DATA BARU
        # ====================================================

        if df.empty:

            print(

                f"   ⛔ SKIP: tidak ada tanggal baru "
                f"untuk {yf_ticker}."

            )

            skipped += 1

            continue

        # ====================================================
        # FUNDAMENTAL
        # ====================================================

        try:

            ticker_obj = yf.Ticker(
                yf_ticker
            )

            info = ticker_obj.info

            eps = info.get(
                "trailingEps"
            )

            per = info.get(
                "trailingPE"
            )

            roe = info.get(
                "returnOnEquity"
            )

            der = info.get(
                "debtToEquity"
            )

            fcf = get_fcf(
                yf_ticker
            )

        except Exception as e:

            print(
                "⚠️ Fundamental error:",
                e
            )

            eps = None
            per = None
            roe = None
            der = None
            fcf = None

        # ====================================================
        # HAPUS KOLOM BANTU
        # ====================================================

        if "_date_only" in df.columns:

            df.drop(

                columns=[
                    "_date_only"
                ],

                inplace=True

            )

        # ====================================================
        # NaN → None
        # ====================================================

        df = df.replace(
            {
                np.nan: None
            }
        )

        # ====================================================
        # BUILD ROWS
        # ====================================================

        rows = []

        for _, r in df.iterrows():

            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            row_date = pd.to_datetime(
                r["date"]
            ).date()

            # ------------------------------------------------
            # CLOSE
            # ------------------------------------------------

            close_price = (

                float(
                    r["close_price"]
                )

                if r["close_price"]
                is not None

                else None

            )

            # ------------------------------------------------
            # VOLUME
            # ------------------------------------------------

            volume = (

                int(
                    r["volume"]
                )

                if r["volume"]
                is not None

                else None

            )

            # ------------------------------------------------
            # MA50
            # ------------------------------------------------

            ma50 = (

                float(
                    r["ma50"]
                )

                if r["ma50"] is not None
                and pd.notna(r["ma50"])

                else None

            )

            # ------------------------------------------------
            # MA200
            # ------------------------------------------------

            ma200 = (

                float(
                    r["ma200"]
                )

                if r["ma200"] is not None
                and pd.notna(r["ma200"])

                else None

            )

            # ------------------------------------------------
            # VOLMA200
            # ------------------------------------------------

            volma200 = (

                float(
                    r["volma200"]
                )

                if r["volma200"] is not None
                and pd.notna(r["volma200"])

                else None

            )

            # ------------------------------------------------
            # RSI
            # ------------------------------------------------

            rsi = (

                float(
                    r["rsi"]
                )

                if r["rsi"] is not None
                and pd.notna(r["rsi"])

                else None

            )

            rows.append(
                (
                    row_date,
                    close_price,
                    eps,
                    per,
                    roe,
                    der,
                    fcf,
                    ma50,
                    ma200,
                    volume,
                    volma200,
                    rsi,
                    None,
                    id_stock

                )
            )

        insert_stock_data(
            rows
        )

        processed += 1

        print(

            f"   ✅ {yf_ticker} berhasil disimpan "
            f"({len(rows)} baris baru)"

        )
        time.sleep(1)

    print(
        "\n=================================================="
    )

    print(
        "✅ STOCK FETCH SELESAI"
    )

    print(
        "=================================================="
    )

    print(
        f"Mode       : {mode}"
    )

    if mode == "daily":

        print(
            "Periode    : tanggal terbaru yang tersedia"
        )

    else:

        print(
            f"Periode    : "
            f"{start_date.date()} → {end_date.date()}"
        )

    print(
        f"Berhasil   : {processed}"
    )

    print(
        f"Dilewati   : {skipped}"
    )

    print(
        "=================================================="
    )

    return {

        "status":
            "fetch selesai",

        "mode":
            mode,

        "years": (
            years
            if mode == "full"
            else None

        ),

        "start_date": (

            None
            if mode == "daily"
            else str(
                start_date.date()
            )

        ),

        "end_date": (

            None
            if mode == "daily"
            else str(
                end_date.date()
            )

        ),

        "total_stocks":
            total_stocks,

        "processed":
            processed,

        "skipped":
            skipped

    }