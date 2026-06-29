from db import (
    get_latest_fuzzy_for_insight,
    get_latest_sentiment_with_news,
    save_insight
)
from insight_engine import generate_investment_insight


def run_insight(ticker=None):
    df = get_latest_fuzzy_for_insight(ticker)

    if df is None or df.empty:
        return []

    results = []

    for _, row in df.iterrows():
        row_data = row.to_dict()

        sentiment_data = get_latest_sentiment_with_news(row_data["ticker"])

        if not sentiment_data:
            sentiment_data = {
                "sentiment": "netral",
                "judul": []
            }

        insight = generate_investment_insight(row_data, sentiment_data)

        save_insight(row_data["output_id"], insight)

        results.append({
            "ticker": row_data["ticker"],
            "output_id": row_data["output_id"],
            "rule_id": row_data.get("rule_id"),
            "rule_condition": row_data.get("rule_condition"),
            "firing_strength": row_data.get("firing_strength"),
            "sentiment": sentiment_data.get("sentiment", "netral"),
            "news_used": len(sentiment_data.get("judul", []))
        })

    return results