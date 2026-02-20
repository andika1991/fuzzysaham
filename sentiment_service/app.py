from flask import Flask, jsonify
from fetch_news import fetch_news
from preprocessing import clean_text
from sentiment_model import classify_sentiment
from detect_emiten import detect_emiten, ALL_TICKERS
from rolling_buffer import update_rolling
from aggregate import aggregate_7d
from db import save_sentiment_detail, save_sentiment_daily
import pandas as pd

app = Flask(__name__)

@app.route("/sentiment/run", methods=["POST"])
def run():
    # ===============================
    # 1. FETCH BERITA
    # ===============================
    news = fetch_news()

    if not news:
        return jsonify({"message": "Tidak ada berita"}), 200

    # Simpan hasil fetch ke CSV (arsip/debug)
    pd.DataFrame(news).to_csv(
        "berita_cnbc_market.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # ===============================
    # 2. ANALISIS BERITA
    # ===============================
    berita_per_saham = {}

    for n in news:
        judul = n.get("judul", "")
        konten = n.get("konten", "")
        link = n.get("link", "")

        text = clean_text(f"{judul} {konten}")
        sent = classify_sentiment(text)
        tickers = detect_emiten(text)

        # Skip berita tanpa emiten
        if not tickers:
            continue

        for t in tickers:
            # In-memory buffer
            if t not in berita_per_saham:
                berita_per_saham[t] = []

            berita_per_saham[t].append({
                "sentimen": sent,
                "judul": judul,
                "link": link
            })

            # ===============================
            # SIMPAN DETAIL KE DB
            # ===============================
            save_sentiment_detail(
                ticker=t,
                judul=judul,
                link=link,
                sentiment=sent
            )

    # ===============================
    # 3. ROLLING 7 HARI
    # ===============================
    df_7d = update_rolling(berita_per_saham)

    if df_7d.empty:
        sent_7d = {}
    else:
        sent_7d = aggregate_7d(df_7d)

    # ===============================
    # 4. OUTPUT FINAL + SIMPAN DAILY
    # ===============================
    final = {}

    print("\n📌 HASIL SENTIMEN PER EMITEN (AKUMULASI 7 HARI)")
    print("=" * 80)

    for t in ALL_TICKERS:
        berita_t = (
            df_7d[df_7d["ticker"] == t]
            if not df_7d.empty else pd.DataFrame()
        )

        total_berita = int(len(berita_t))
        sentiment = sent_7d.get(t, "netral")

        final[t] = {
            "sentimen": sentiment,
            "total_berita": total_berita,
            "berita": []
        }

        print(f"\n📈 {t}")
        print(f"   Sentimen     : {sentiment}")
        print(f"   Total Berita : {total_berita}")

        if berita_t.empty:
            print("   - Tidak ada berita terkait")
        else:
            for i, (_, r) in enumerate(berita_t.iterrows(), start=1):
                print(f"   {i}. {r['judul']}")
                print(f"      🔗 {r['link']}")

                final[t]["berita"].append({
                    "judul": r["judul"],
                    "link": r["link"]
                })

        # ===============================
        # SIMPAN DAILY KE DB
        # ===============================
        save_sentiment_daily(
            ticker=t,
            sentiment=sentiment,
            total_berita=total_berita
        )

    return jsonify(final), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
