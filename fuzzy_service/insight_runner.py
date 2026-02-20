from db import (
    get_latest_fuzzy_for_insight,
    get_latest_sentiment_with_news,
    save_insight
)
from insight_engine import generate_investment_insight

def run_insight(ticker=None):
    df = get_latest_fuzzy_for_insight(ticker)
    results = []

    for _, row in df.iterrows():
        sentiment_data = get_latest_sentiment_with_news(row["ticker"])

        insight = generate_investment_insight(row, sentiment_data)
        save_insight(row["output_id"], insight)

        results.append({
            "ticker": row["ticker"],
            "sentiment": sentiment_data["sentiment"],
            "news_used": len(sentiment_data["judul"])
        })

    return results
