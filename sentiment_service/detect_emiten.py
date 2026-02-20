import pandas as pd

df = pd.read_csv("data/LQ45_saham.csv")
ALL_TICKERS = df["Ticker"].astype(str).str.upper().tolist()

def detect_emiten(text):
    text = text.lower()
    detected = []

    for _, r in df.iterrows():
        if r["Ticker"].lower() in text or r["Nama Perusahaan"].lower() in text:
            detected.append(r["Ticker"])

    return detected
