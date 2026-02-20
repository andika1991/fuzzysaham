import pandas as pd
from datetime import datetime, timedelta
import os

FILE = "sentiment_rolling_7d.csv"

def update_rolling(berita_per_saham):
    today = datetime.now().date()

    if os.path.exists(FILE):
        df = pd.read_csv(FILE)
    else:
        df = pd.DataFrame(
            columns=["date", "ticker", "sentimen", "judul", "link"]
        )

    rows = []
    for ticker, items in berita_per_saham.items():
        for it in items:
            rows.append({
                "date": today,
                "ticker": ticker,
                "sentimen": it["sentimen"],
                "judul": it["judul"],
                "link": it["link"]
            })

    if rows:
        new_df = pd.DataFrame(rows)
        df = pd.concat([df, new_df], ignore_index=True)

        # 🔥 ANTI DUPLIKASI
        df = df.drop_duplicates(
            subset=["ticker", "link"],
            keep="last"
        )

    # Rolling 7 hari
    df["date"] = pd.to_datetime(df["date"])
    cutoff = pd.Timestamp(today - timedelta(days=6))
    df = df[df["date"] >= cutoff]

    df.to_csv(FILE, index=False)
    return df

