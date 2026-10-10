import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
from zoneinfo import ZoneInfo
from db import (
    get_lq45_stocks,
    get_sector_stats,
    get_fuzzy_rules,
    get_sentiment_value,
    get_latest_sentiment_with_news
)
from fuzzy_engine import FuzzyMamdaniEngine
from realtime import (
    save_stock_realtime,
    update_realtime_insight,
    get_previous_realtime
)
from insight_engine import generate_investment_insight
# ============================================================
# RSI
# ============================================================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (
        delta.where(delta > 0, 0)
        .rolling(period)
        .mean()
    )
    loss = (
        -delta.where(delta < 0, 0)
        .rolling(period)
        .mean()
    )
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
# ============================================================
# FREE CASH FLOW
# ============================================================
def get_fcf(yf_ticker):
    try:
        ticker = yf.Ticker(yf_ticker)
        cf = ticker.cashflow
        if cf is None or cf.empty:
            print(
                f"⚠️ FCF kosong: {yf_ticker}"
            )
            return None
        cf.index = cf.index.str.lower()
        # Cari Free Cash Flow langsung
        for key in cf.index:
            if "free cash flow" in key:
                val = cf.loc[key].iloc[0]
                if pd.notna(val):
                    return float(val)
        # Fallback OCF - CapEx
        ocf = None
        capex = None
        for key in cf.index:
            if (
                "operating" in key
                and ocf is None
            ):
                ocf = cf.loc[key].iloc[0]
            if (
                (
                    "capital" in key
                    or "capex" in key
                )
                and capex is None
            ):
                capex = cf.loc[key].iloc[0]
        if (
            ocf is not None
            and capex is not None
            and pd.notna(ocf)
            and pd.notna(capex)
        ):
            return float(
                ocf - capex
            )
        return None
    except Exception as e:
        print(
            f"[FCF ERROR] {yf_ticker}: {e}"
        )
        return None
# ============================================================
# FUNDAMENTAL
# ============================================================
def get_fundamental_data(yf_ticker):
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
        return {
            "eps": (
                float(eps)
                if eps is not None
                else None
            ),
            "per": (
                float(per)
                if per is not None
                else None
            ),
            "roe": (
                float(roe)
                if roe is not None
                else None
            ),
            "der": (
                float(der)
                if der is not None
                else None
            ),
            "fcf": (
                float(fcf)
                if fcf is not None
                else None
            )
        }
    except Exception as e:
        print(
            f"⚠️ Fundamental error "
            f"{yf_ticker}: {e}"
        )
        return {
            "eps": None,
            "per": None,
            "roe": None,
            "der": None,
            "fcf": None
        }
# ============================================================
# REALTIME TECHNICAL DATA
# ============================================================
def get_realtime_data(ticker):
    yf_ticker=f"{ticker}.JK"
    stock=yf.Ticker(yf_ticker)
    hist=stock.history(period="5y",interval="1d",auto_adjust=False)
    if hist.empty:
        raise ValueError(f"Tidak ada data untuk {ticker}")
    hist=hist.dropna(subset=["Close"])
    close=pd.to_numeric(hist["Close"],errors="coerce")
    volume=pd.to_numeric(hist["Volume"],errors="coerce")
    valid=close.notna()&volume.notna()
    close=close[valid]
    volume=volume[valid]
    if close.empty:
        raise ValueError(f"Data harga kosong untuk {ticker}")
    ma20=close.rolling(20,min_periods=20).mean().iloc[-1]
    ma50=close.rolling(50,min_periods=50).mean().iloc[-1]
    ma100=close.rolling(100,min_periods=100).mean().iloc[-1]
    ma200=close.rolling(200,min_periods=200).mean().iloc[-1]
    volma20=volume.rolling(20,min_periods=20).mean().iloc[-1]
    volma50=volume.rolling(50,min_periods=50).mean().iloc[-1]
    volma100=volume.rolling(100,min_periods=100).mean().iloc[-1]
    volma200=volume.rolling(200,min_periods=200).mean().iloc[-1]
    g_h1=close.pct_change(1).iloc[-1]
    g_h5=close.pct_change(5).iloc[-1]
    if pd.notna(g_h1) and pd.notna(g_h5):
        gradient=0.70*g_h1+0.30*g_h5
    elif pd.notna(g_h1):
        gradient=g_h1
    elif pd.notna(g_h5):
        gradient=g_h5
    else:
        gradient=None
    if pd.notna(volma20) and volma20!=0:
        d20=(volume-volma20)/volma20
    else:
        d20=pd.Series(np.nan,index=volume.index)
    if pd.notna(volma50) and volma50!=0:
        d50=(volume-volma50)/volma50
    else:
        d50=pd.Series(np.nan,index=volume.index)
    if pd.notna(volma100) and volma100!=0:
        d100=(volume-volma100)/volma100
    else:
        d100=pd.Series(np.nan,index=volume.index)
    if pd.notna(volma200) and volma200!=0:
        d200=(volume-volma200)/volma200
    else:
        d200=pd.Series(np.nan,index=volume.index)
    volume_ratio_series=0.40*d20+0.30*d50+0.20*d100+0.10*d200
    volume_ratio=volume_ratio_series.iloc[-1]
    rsi=compute_rsi(close).iloc[-1]
    return {
        "close_price":float(close.iloc[-1]),
        "volume":int(volume.iloc[-1]),
        "ma20":float(ma20) if pd.notna(ma20) else None,
        "ma50":float(ma50) if pd.notna(ma50) else None,
        "ma100":float(ma100) if pd.notna(ma100) else None,
        "ma200":float(ma200) if pd.notna(ma200) else None,
        "volma20":float(volma20) if pd.notna(volma20) else None,
        "volma50":float(volma50) if pd.notna(volma50) else None,
        "volma100":float(volma100) if pd.notna(volma100) else None,
        "volma200":float(volma200) if pd.notna(volma200) else None,
        "g_h1":float(g_h1) if pd.notna(g_h1) else None,
        "g_h5":float(g_h5) if pd.notna(g_h5) else None,
        "gradient":float(gradient) if gradient is not None and pd.notna(gradient) else None,
        "volume_ratio":float(volume_ratio) if pd.notna(volume_ratio) else None,
        "rsi":float(rsi) if pd.notna(rsi) else None
    }
def process_realtime_stock(stock, engine, snapshot_at):
    ticker = stock["ticker"]
    id_stock = stock["id_stock"]
    sektor = stock["sektor"]
    yf_ticker = f"{ticker}.JK"
    # =========================================================
    # 1. AMBIL DATA FUNDAMENTAL
    # =========================================================
    fundamental = get_fundamental_data(yf_ticker)
    # =========================================================
    # 2. AMBIL DATA TEKNIKAL
    # =========================================================
    technical = get_realtime_data(ticker)
    # =========================================================
    # 3. AMBIL SENTIMEN
    # =========================================================
    sentimen_value = get_sentiment_value(ticker)
    if sentimen_value == 1.0:
        sentimen = "positif"
    elif sentimen_value == 0.0:
        sentimen = "negatif"
    else:
        sentimen = "netral"
    # =========================================================
    # 4. GABUNGKAN DATA
    # =========================================================
    data = {
        **fundamental,
        **technical,
        "sentimen": sentimen,
        "sent_v": sentimen_value,
        "Sektor": sektor,
        "ticker": ticker
    }
    row = pd.Series(data)
    # =========================================================
    # 5. FUZZY MAMDANI
    # =========================================================
    res = engine.evaluate(row)
    membership = res.get("mbs", {})
    # =========================================================
    # 6. LOG DATA REALTIME
    # =========================================================
    print("\n")
    print("=" * 90)
    print(f"REALTIME RECOMMENDATION : {ticker}")
    print("=" * 90)
    print(f"Snapshot       : {snapshot_at}")
    print(f"Ticker         : {ticker}")
    print(f"Sektor         : {sektor}")
    # =========================================================
    # FUNDAMENTAL
    # =========================================================
    print("\n" + "-" * 90)
    print("DATA FUNDAMENTAL")
    print("-" * 90)
    print(f"EPS            : {data.get('eps')}")
    print(f"PER            : {data.get('per')}")
    print(f"ROE            : {data.get('roe')}")
    print(f"DER            : {data.get('der')}")
    print(f"FCF            : {data.get('fcf')}")
    # =========================================================
    # TEKNIKAL
    # =========================================================
    print("\n" + "-" * 90)
    print("DATA TEKNIKAL")
    print("-" * 90)
    print(f"Close Price    : {data.get('close_price')}")
    print(f"Volume         : {data.get('volume')}")
    print(f"MA50           : {data.get('ma50')}")
    print(f"MA200          : {data.get('ma200')}")
    print(f"VolMA200       : {data.get('volma200')}")
    print(f"RSI            : {data.get('rsi')}")
    print(f"Gradient       : {data.get('gradient')}")
    # =========================================================
    # SENTIMEN
    # =========================================================
    print("\n" + "-" * 90)
    print("SENTIMEN")
    print("-" * 90)
    print(f"Sentimen Value : {sentimen_value}")
    print(f"Sentimen       : {sentimen}")
    # =========================================================
    # FUZZY RESULT
    # =========================================================
    print("\n" + "-" * 90)
    print("HASIL FUZZY MAMDANI")
    print("-" * 90)
    print(f"Score          : {res['score']}")
    print(f"Label          : {res['label']}")
    print(f"Horizon        : {res['horizon']}")
    print(f"Rule ID        : {res['rule_id']}")
    print(f"Rule Condition : {res['rule_condition']}")
    print(f"Firing Strength: {res['firing_strength']}")
    # =========================================================
    # MEMBERSHIP
    # =========================================================
    print("\n" + "-" * 90)
    print("MEMBERSHIP")
    print("-" * 90)
    for variable, values in membership.items():
        print(f"\n{variable}:")
        if isinstance(values, dict):
            for level, value in values.items():
                print(f"   {level:<12}: {value:.6f}")
        else:
            print(f"   {values}")
    # =========================================================
    # DATA UNTUK INSIGHT
    # =========================================================
    insight_data = {
        **data,
        "Score": res["score"],
        "score": res["score"],
        "Label": res["label"],
        "label": res["label"],
        "Time_Horizon": res["horizon"],
        "horizon": res["horizon"],
        "rule_id": res["rule_id"],
        "rule_condition": res["rule_condition"],
        "firing_strength": res["firing_strength"],
        "membership": membership
    }
    # =========================================================
    # 7. SIMPAN SNAPSHOT
    # =========================================================
    realtime_id = save_stock_realtime(
        id_stock=id_stock,
        snapshot_at=snapshot_at,
        eps=data.get("eps"),
        per=data.get("per"),
        roe=data.get("roe"),
        der=data.get("der"),
        fcf=data.get("fcf"),
        close_price=data.get("close_price"),
        volume=data.get("volume"),
        ma20=data.get("ma20"),
        ma50=data.get("ma50"),
        ma100=data.get("ma100"),
        ma200=data.get("ma200"),
        volma20=data.get("volma20"),
        volma50=data.get("volma50"),
        volma100=data.get("volma100"),
        volma200=data.get("volma200"),
        g_h1=data.get("g_h1"),
        g_h5=data.get("g_h5"),
        gradient=data.get("gradient"),
        volume_ratio=data.get("volume_ratio"),
        rsi=data.get("rsi"),
        sentimen=data.get("sentimen"),
        fuzzy_score=res["score"],
        kategori=res["label"],
        horizon=res["horizon"],
        insight=None,
        # SIMPAN HASIL FUZZIFIKASI
        membership=membership
    )
    # =========================================================
    # 8. PROSES INSIGHT
    # =========================================================
    insight = None
    previous = None
    same_day = False
    try:
        # -----------------------------------------------------
        # Ambil snapshot sebelumnya
        # -----------------------------------------------------
        previous = get_previous_realtime(
            ticker,
            realtime_id
        )
        # -----------------------------------------------------
        # Kondisi saat ini
        # -----------------------------------------------------
        current_condition = (
            res["label"],
            res["horizon"],
            data["sentimen"]
        )
        # -----------------------------------------------------
        # Kondisi sebelumnya
        # -----------------------------------------------------
        previous_condition = None
        if previous:
            previous_condition = (
                previous.get("kategori"),
                previous.get("horizon"),
                previous.get("sentimen")
            )
            # -------------------------------------------------
            # Cek tanggal snapshot sebelumnya
            # -------------------------------------------------
            previous_snapshot = previous.get("snapshot_at")
            if previous_snapshot:
                if hasattr(previous_snapshot, "date"):
                    same_day = (
                        previous_snapshot.date()
                        == snapshot_at.date()
                    )
                else:
                    same_day = (
                        str(previous_snapshot)[:10]
                        == str(snapshot_at)[:10]
                    )
        # =====================================================
        # LOG STATUS INSIGHT
        # =====================================================
        print("\n" + "-" * 90)
        print("PROSES INSIGHT")
        print("-" * 90)
        if previous:
            print(
                f"Previous Snapshot : "
                f"{previous.get('snapshot_at')}"
            )
            print(
                f"Previous Insight  : "
                f"{'ADA' if previous.get('insight') else 'KOSONG'}"
            )
            print(
                f"Same Day          : "
                f"{same_day}"
            )
            print(
                f"Current Condition : "
                f"{current_condition}"
            )
            print(
                f"Previous Condition: "
                f"{previous_condition}"
            )
        else:
            print("Previous Snapshot : TIDAK ADA")
        can_reuse = (
            previous
            and same_day
            and current_condition == previous_condition
            and previous.get("insight")
        )
        if can_reuse:
            print(
                f"\n[INSIGHT] {ticker} "
                f"→ kondisi sama, reuse insight sebelumnya"
            )
            insight = previous.get("insight")
        else:
            if previous and not same_day:
                print(
                    f"\n[INSIGHT] {ticker} "
                    f"→ hari baru, reset dan generate insight baru"
                )
            elif previous and current_condition != previous_condition:
                print(
                    f"\n[INSIGHT] {ticker} "
                    f"→ kondisi berubah, generate insight baru"
                )
            elif previous and not previous.get("insight"):
                print(
                    f"\n[INSIGHT] {ticker} "
                    f"→ insight sebelumnya kosong, generate insight baru"
                )
            else:
                print(
                    f"\n[INSIGHT] {ticker} "
                    f"→ generate insight baru"
                )
            # =================================================
            # AMBIL BERITA + SENTIMEN
            # =================================================
            sentiment_data = get_latest_sentiment_with_news(
                ticker=ticker,
                tanggal=None
            )
            if not sentiment_data:
                sentiment_data = {
                    "sentiment": data["sentimen"],
                    "judul": []
                }
                print(
                    f"[INSIGHT] {ticker} "
                    f"→ tidak ada berita terbaru"
                )
            else:
                print(
                    f"[INSIGHT] {ticker} "
                    f"→ data berita berhasil diambil"
                )
            # =================================================
            # GENERATE INSIGHT PERTAMA
            # =================================================
            print(
                f"[INSIGHT] {ticker} "
                f"→ generate dengan Groq..."
            )
            insight = generate_investment_insight(
                insight_data,
                sentiment_data
            )
            # =================================================
            # JIKA KOSONG → GENERATE ULANG
            # =================================================
            if not insight:
                print(
                    f"[INSIGHT] {ticker} "
                    f"→ hasil generate kosong"
                )
                print(
                    f"[INSIGHT] {ticker} "
                    f"→ mencoba generate ulang..."
                )
                insight = generate_investment_insight(
                    insight_data,
                    sentiment_data
                )
            # =================================================
            # HASIL AKHIR
            # =================================================
            if insight:
                print(
                    f"[INSIGHT] {ticker} "
                    f"→ generate berhasil"
                )
            else:
                print(
                    f"[INSIGHT] {ticker} "
                    f"→ generate tetap kosong"
                )
                # -------------------------------------------------
                # FALLBACK HANYA UNTUK HARI YANG SAMA
                # -------------------------------------------------
                if same_day and previous:
                    previous_insight = previous.get("insight")
                    if previous_insight:
                        print(
                            f"[INSIGHT] {ticker} "
                            f"→ fallback ke insight sebelumnya"
                        )
                        insight = previous_insight
                    else:
                        print(
                            f"[INSIGHT] {ticker} "
                            f"→ insight sebelumnya juga kosong"
                        )
    except Exception as e:
        print(
            f"\n[INSIGHT ERROR] {ticker}: {e}"
        )
        # =====================================================
        # FALLBACK JIKA ERROR
        # =====================================================
        try:
            if same_day and previous:
                previous_insight = previous.get("insight")
                if previous_insight:
                    insight = previous_insight
                    print(
                        f"[INSIGHT] {ticker} "
                        f"→ fallback ke insight hari yang sama"
                    )
        except Exception as fallback_error:
            print(
                f"[INSIGHT FALLBACK ERROR] "
                f"{ticker}: {fallback_error}"
            )
    # =========================================================
    # 10. SIMPAN INSIGHT
    # =========================================================
    if insight:
        update_realtime_insight(
            id_realtime=realtime_id,
            insight=insight
        )
        print(
            f"\n[INSIGHT] {ticker} "
            f"→ insight berhasil disimpan"
        )
        print(
            f"[INSIGHT LENGTH] "
            f"{len(str(insight))} karakter"
        )
    else:
        print(
            f"\n[INSIGHT] {ticker} "
            f"→ insight masih kosong"
        )
    # =========================================================
    # 11. RINGKASAN
    # =========================================================
    print("\n" + "=" * 90)
    print(f"SELESAI : {ticker}")
    print("=" * 90)
    print(f"Snapshot       : {snapshot_at}")
    print(f"Close          : {data.get('close_price')}")
    print(f"RSI            : {data.get('rsi')}")
    print(f"Gradient       : {data.get('gradient')}")
    print(f"Sentimen       : {data.get('sentimen')}")
    print(f"Fuzzy Score    : {res['score']}")
    print(f"Kategori       : {res['label']}")
    print(f"Horizon        : {res['horizon']}")
    print(f"Rule ID        : {res['rule_id']}")
    print(f"Firing Strength: {res['firing_strength']}")
    print(
        f"Insight        : "
        f"{'ADA' if insight else 'KOSONG'}"
    )
    print("=" * 90)
    return {
        "ticker": ticker,
        "id_stock": id_stock,
        "realtime_id": realtime_id,
        "score": res["score"],
        "label": res["label"],
        "horizon": res["horizon"],
        "rule_id": res["rule_id"],
        "rule_condition": res["rule_condition"],
        "firing_strength": res["firing_strength"],
        "insight": insight,
        "data": data
    }
# ============================================================
# RUN REALTIME RECOMMENDATION
# ============================================================
def run_realtime_recommendation():
    stocks = get_lq45_stocks()
    rules_df = get_fuzzy_rules()
    sector_stats = get_sector_stats()
    # ========================================================
    # VALIDASI
    # ========================================================
    if not stocks:
        return {
            "status": "error",
            "message":
                "Data LQ45 kosong"
        }
    if rules_df.empty:
        return {
            "status": "error",
            "message":
                "Rule fuzzy kosong"
        }
    if sector_stats.empty:
        return {
            "status": "error",
            "message":
                "Sector stats kosong"
        }
    # ========================================================
    # INIT FUZZY ENGINE
    # ========================================================
    engine = FuzzyMamdaniEngine(
        sector_stats,
        rules_df
    )
    # ========================================================
    # WAKTU SNAPSHOT WIB
    # ========================================================
    snapshot_at = dt.datetime.now(
        ZoneInfo("Asia/Jakarta")
    )
    print(
        "=" * 50
    )
    print(
        "REALTIME RECOMMENDATION"
    )
    print(
        f"Snapshot : "
        f"{snapshot_at}"
    )
    print(
        f"Total    : "
        f"{len(stocks)} saham"
    )
    print(
        "=" * 50
    )
    # ========================================================
    # PROSES SEMUA SAHAM
    # ========================================================
    results = []
    for stock in stocks:
        try:
            result = (
                process_realtime_stock(
                    stock,
                    engine,
                    snapshot_at
                )
            )
            results.append(
                result
            )
        except Exception as e:
            print(
                f"❌ "
                f"{stock['ticker']}: "
                f"{e}"
            )
    print(
        "=" * 50
    )
    print(
        f"✅ Selesai: "
        f"{len(results)}/"
        f"{len(stocks)} saham"
    )
    print(
        "=" * 50
    )
    return {
        "status":
            "realtime selesai",
        "snapshot_at":
            snapshot_at,
        "total":
            len(results),
        "results":
            results
    }
# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    result = (
        run_realtime_recommendation()
    )
    print(
        result
    )
