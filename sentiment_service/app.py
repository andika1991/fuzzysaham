from flask import Flask, jsonify, request
from fetch_news import fetch_news
from preprocessing import clean_text
from sentiment_model import classify_sentiment
from detect_emiten import detect_emiten, ALL_TICKERS
from rolling_buffer import update_rolling
from aggregate import aggregate_7d

from db import (
    save_sentiment_detail,
    save_sentiment_daily
)

import pandas as pd
import os

from dotenv import load_dotenv
from functools import wraps


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# API KEY

API_KEY = os.getenv("FUZZY_API_KEY")


def require_api_key(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        client_key = request.headers.get(
            "X-API-Key"
        )

        if not API_KEY:

            return jsonify({
                "status": "error",
                "message": (
                    "API key server belum dikonfigurasi."
                )
            }), 500

        # Header tidak dikirim
        if not client_key:

            return jsonify({
                "status": "error",
                "message": (
                    "X-API-Key wajib diisi."
                )
            }), 401

        # API key salah
        if client_key != API_KEY:

            return jsonify({
                "status": "error",
                "message": (
                    "API key tidak valid."
                )
            }), 403
        return func(*args, **kwargs)

    return wrapper


# ============================================================
# SENTIMENT RUN
# ============================================================

@app.route("/sentiment/run", methods=["POST"])
@require_api_key
def run():

    # ===============================
    # 1. FETCH BERITA
    # ===============================

    news = fetch_news()

    if not news:
        return jsonify({
            "message": "Tidak ada berita"
        }), 200


    # Simpan hasil fetch ke CSV
    pd.DataFrame(news).to_csv(
        "berita_cnbc_market.csv",
        index=False,
        encoding="utf-8-sig"
    )


    # ===============================
    # 2. ANALISIS BERITA
    # ===============================

    berita_per_saham = {}
    berita_tanpa_emiten = []
    for n in news:

        judul = n.get(
            "judul",
            ""
        )

        konten = n.get(
            "konten",
            ""
        )

        link = n.get(
            "link",
            ""
        )
        text = clean_text(
            f"{judul} {konten}"
        )

        sent = classify_sentiment(
            text
        )

        tickers = detect_emiten(
            text
        )

        if not tickers:
            berita_tanpa_emiten.append({
                "sentimen": sent,
                "judul": judul,
                "link": link
            })


            save_sentiment_detail(
                ticker=None,
                judul=judul,
                link=link,
                sentiment=sent
            )

            continue

        for t in tickers:
            if t not in berita_per_saham:
                berita_per_saham[t] = []

            berita_per_saham[t].append({
                "sentimen": sent,
                "judul": judul,
                "link": link

            })

            save_sentiment_detail(
                ticker=t,
                judul=judul,
                link=link,
                sentiment=sent

            )

        df_7d = update_rolling(
        berita_per_saham
    )


    if df_7d.empty:

        sent_7d = {}

    else:

        sent_7d = aggregate_7d(
            df_7d
        )


    # ===============================
    # 4. OUTPUT FINAL
    # ===============================

    final = {}


    print(
        "\nHASIL SENTIMEN PER EMITEN "
        "(AKUMULASI 7 HARI)"
    )

    print("=" * 80)


    for t in ALL_TICKERS:

        berita_t = (

            df_7d[
                df_7d["ticker"] == t
            ]

            if not df_7d.empty

            else pd.DataFrame()

        )


        total_berita = int(
            len(berita_t)
        )


        sentiment = sent_7d.get(
            t,
            "netral"
        )


        final[t] = {

            "sentimen": sentiment,

            "total_berita": total_berita,

            "berita": []

        }


        print(
            f"\n{t}"
        )

        print(
            f"   Sentimen     : {sentiment}"
        )

        print(
            f"   Total Berita : {total_berita}"
        )


        if berita_t.empty:

            print(
                "   - Tidak ada berita terkait"
            )

        else:

            for i, (_, r) in enumerate(
                berita_t.iterrows(),
                start=1
            ):

                print(
                    f"   {i}. {r['judul']}"
                )

                print(
                    f"      Link: {r['link']}"
                )


                final[t]["berita"].append({

                    "judul": r["judul"],

                    "link": r["link"]

                })


        # Simpan sentiment daily
        save_sentiment_daily(

            ticker=t,

            sentiment=sentiment,

            total_berita=total_berita

        )


    # ===============================
    # BERITA TANPA EMITEN
    # ===============================

    final["_tanpa_emiten"] = {

        "total_berita": len(
            berita_tanpa_emiten
        ),

        "berita": [

            {

                "judul": b["judul"],

                "link": b["link"],

                "sentimen": b["sentimen"]

            }

            for b in berita_tanpa_emiten

        ]

    }


    print(
        "\nBERITA TANPA EMITEN"
    )

    print(
        f"   Total Berita : "
        f"{len(berita_tanpa_emiten)}"
    )


    for i, b in enumerate(
        berita_tanpa_emiten,
        start=1
    ):

        print(
            f"   {i}. {b['judul']}"
        )

        print(
            f"      Link: {b['link']}"
        )

        print(
            f"      Sentimen: {b['sentimen']}"
        )


    return jsonify(
        final
    ), 200


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )