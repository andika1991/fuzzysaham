# ============================================================
# STOCK FETCHER LQ45 + FCF AKTIF
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import time
from db import get_conn, get_lq45_stocks


# ============================================================
# RSI
# ============================================================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ============================================================
# HITUNG FREE CASH FLOW (HYBRID)
# ============================================================
def get_fcf(yf_ticker):
    try:
        t = yf.Ticker(yf_ticker)
        cf = t.cashflow

        if cf is None or cf.empty:
            print(f"   ⚠️ FCF kosong: {yf_ticker}")
            return None

        # normalisasi index
        cf.index = cf.index.str.lower()

        # =========================
        # 1️⃣ DIRECT FREE CASH FLOW
        # =========================
        for key in cf.index:
            if "free cash flow" in key:
                val = cf.loc[key].iloc[0]
                if pd.notna(val):
                    return float(val)

        # =========================
        # 2️⃣ OPERATING - CAPEX
        # =========================
        ocf = None
        capex = None

        for key in cf.index:
            if "operating" in key and ocf is None:
                ocf = cf.loc[key].iloc[0]
            if ("capital" in key or "capex" in key) and capex is None:
                capex = cf.loc[key].iloc[0]

        if pd.notna(ocf) and pd.notna(capex):
            return float(ocf - capex)

        print(f"   ⚠️ FCF tidak ditemukan lengkap: {yf_ticker}")
        return None

    except Exception as e:
        print(f"[FCF ERROR] {yf_ticker}: {e}")
        return None


# ============================================================
# INSERT KE DATABASE
# ============================================================
def insert_stock_data(rows):
    if not rows:
        return

    conn = get_conn()
    cur = conn.cursor()

    sql = """
    INSERT INTO stock_data
    (date, close_price, eps, per, roe, der, fcf,
     ma50, ma200, volume, volma200, rsi, sentimen, id_stock)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
        close_price = VALUES(close_price),
        volume = VALUES(volume),
        rsi = VALUES(rsi),
        ma50 = VALUES(ma50),
        ma200 = VALUES(ma200),
        volma200 = VALUES(volma200),
        fcf = VALUES(fcf)
    """

    cur.executemany(sql, rows)
    conn.commit()
    cur.close()
    conn.close()

def get_recent_prices(id_stock, limit=200):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT date, close_price, volume
        FROM stock_data
        WHERE id_stock = %s
        ORDER BY date DESC
        LIMIT %s
    """, (id_stock, limit))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values("date")
    return df

def update_technical_indicators(id_stock):

    df = get_recent_prices(id_stock, 200)

    if len(df) < 20:
        return

    df["ma50"] = df["close_price"].rolling(50).mean()
    df["ma200"] = df["close_price"].rolling(200).mean()
    df["volma200"] = df["volume"].rolling(200).mean()
    df["rsi"] = compute_rsi(df["close_price"])

    latest = df.iloc[-1]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE stock_data
        SET ma50=%s,
            ma200=%s,
            volma200=%s,
            rsi=%s
        WHERE id_stock=%s AND date=%s
    """, (
        latest["ma50"],
        latest["ma200"],
        latest["volma200"],
        int(latest["rsi"]) if pd.notna(latest["rsi"]) else None,
        id_stock,
        latest["date"]
    ))

    conn.commit()
    cur.close()
    conn.close()



# ============================================================
# FETCH & SIMPAN DATA SAHAM
# ============================================================
def fetch_and_save_stock_data(mode="daily", years=5):

    stocks = get_lq45_stocks()
    today = dt.datetime.today()

    if mode == "daily":
        # Ambil 2-3 hari untuk jaga-jaga weekend/libur
        start_date = today - dt.timedelta(days=3)
        end_date = today
        print("🕔 MODE DAILY (ambil 1 data terbaru saja)")
    else:
        start_date = today - dt.timedelta(days=365 * years)
        end_date = today
        print("📦 MODE HISTORY:", years, "tahun")

    for s in stocks:

        ticker = s["ticker"]
        id_stock = s["id_stock"]
        yf_ticker = f"{ticker}.JK"

        print(f"\n📥 Fetch {yf_ticker}")

        try:
            df = yf.download(
                yf_ticker,
                start=start_date,
                end=end_date,
                progress=False,
                threads=False
            )
        except Exception as e:
            print("❌ Download error:", e)
            continue

        if df.empty:
            print("⚠️ Data kosong")
            continue

        # =========================================================
        # HANDLE MULTI INDEX
        # =========================================================
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.rename(columns={
            "Close": "close_price",
            "Volume": "volume"
        })

        df.reset_index(inplace=True)
        df.rename(columns={"Date": "date"}, inplace=True)

        # =========================================================
        # HITUNG INDIKATOR TEKNIKAL
        # =========================================================
        if mode == "full":

            # Hitung seluruh indikator dari data historis
            df["ma50"] = (
                df["close_price"]
                .rolling(window=50, min_periods=50)
                .mean()
            )

            df["ma200"] = (
                df["close_price"]
                .rolling(window=200, min_periods=200)
                .mean()
            )

            df["volma200"] = (
                df["volume"]
                .rolling(window=200, min_periods=200)
                .mean()
            )

            df["rsi"] = compute_rsi(df["close_price"])

        else:

            # Daily hanya ambil data terakhir
            df = df.sort_values("date").tail(1)

            df["ma50"] = None
            df["ma200"] = None
            df["volma200"] = None
            df["rsi"] = None

        # =========================================================
        # FUNDAMENTAL
        # =========================================================
        try:

            ticker_obj = yf.Ticker(yf_ticker)
            info = ticker_obj.info

            eps = info.get("trailingEps")
            per = info.get("trailingPE")
            roe = info.get("returnOnEquity")
            der = info.get("debtToEquity")
            fcf = get_fcf(yf_ticker)

        except Exception as e:

            print("⚠️ Fundamental error:", e)

            eps = None
            per = None
            roe = None
            der = None
            fcf = None

        df = df.replace({np.nan: None})

        # =========================================================
        # BUILD ROWS
        # =========================================================
        rows = []

        for _, r in df.iterrows():

            rows.append((

                pd.to_datetime(r["date"]).date(),

                float(r["close_price"]) if r["close_price"] is not None else None,

                eps,
                per,
                roe,
                der,
                fcf,

                None if pd.isna(r["ma50"]) else float(r["ma50"]),
                None if pd.isna(r["ma200"]) else float(r["ma200"]),

                int(r["volume"]) if r["volume"] is not None else None,

                None if pd.isna(r["volma200"]) else float(r["volma200"]),

                None if pd.isna(r["rsi"]) else float(r["rsi"]),

                None,

                id_stock
            ))

        # =========================================================
        # INSERT DATABASE
        # =========================================================
        insert_stock_data(rows)

        # Daily baru dihitung dari database
        if mode == "daily":
            update_technical_indicators(id_stock)

        time.sleep(1)