from db import (
    get_latest_fuzzy_for_insight,
    get_latest_sentiment_with_news,
    save_insight
)
from insight_engine import generate_investment_insight


def run_insight(ticker=None, tanggal=None):

    df = get_latest_fuzzy_for_insight(
        ticker=ticker,
        tanggal=tanggal
    )

    if df is None or df.empty:
        return []

    results = []
    for _, row in df.iterrows():

        row_data = row.to_dict()

        process_date = tanggal

        if process_date is None:
            process_date = row_data.get("tanggal")

        sentiment_data = get_latest_sentiment_with_news(
            ticker=row_data["ticker"],
            tanggal=process_date
        )


        if not sentiment_data:

            sentiment_data = {
                "sentiment": "netral",
                "judul": []
            }

        insight = generate_investment_insight(
            row_data,
            sentiment_data
        )
        save_insight(
            row_data["output_id"],
            insight
        )


        results.append({

            "ticker": row_data["ticker"],

            "tanggal": (
                str(process_date)
                if process_date
                else None
            ),

            "output_id": row_data["output_id"],

            "rule_id": row_data.get(
                "rule_id"
            ),

            "rule_condition": row_data.get(
                "rule_condition"
            ),

            "firing_strength": row_data.get(
                "firing_strength"
            ),

            "sentiment": sentiment_data.get(
                "sentiment",
                "netral"
            ),

            "news_used": len(
                sentiment_data.get(
                    "judul",
                    []
                )
            )

        })

    return results

def run_realtime_insight(row_data):
    ticker = row_data.get("ticker")

    if not ticker:
        return None

    sentiment_data = get_latest_sentiment_with_news(
        ticker=ticker,
        tanggal=None
    )

    if not sentiment_data:
        sentiment_data = {
            "sentiment": "netral",
            "judul": []
        }

    insight = generate_investment_insight(
        row_data,
        sentiment_data
    )

    return insight