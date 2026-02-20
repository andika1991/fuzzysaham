from collections import defaultdict

def aggregate(results):
    if not results:
        return {}

    rekap = defaultdict(lambda: {"positif":0,"negatif":0,"netral":0})

    for r in results:
        for t in r["tickers"]:
            rekap[t][r["sentiment"]] += 1

    final = {}
    for t, v in rekap.items():
        final[t] = max(v, key=v.get)

    return final

def aggregate_7d(df):
    result = {}

    for t in df["ticker"].unique():
        sub = df[df["ticker"] == t]
        result[t] = sub["sentimen"].value_counts().idxmax()

    return result
