from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_investment_insight(row, sentiment_data):
    ticker = row["ticker"]
    price = row["close_price"]
    score = row["score"]
    label = row["label"]
    horizon = row["horizon"]

    eps = row["eps"]
    per = row["per"]
    roe = row["roe"]
    der = row["der"]

    ma50 = row["ma50"]
    ma200 = row["ma200"]

    sentiment = sentiment_data["sentiment"]
    judul_list = sentiment_data["judul"]

    # ==========================
    # FORMAT JUDUL BERITA
    # ==========================
    if judul_list:
        berita_text = "\n".join([f"- {j}" for j in judul_list])
    else:
        berita_text = "Tidak ada berita signifikan terbaru."

    system_prompt = f"""
Anda adalah Senior Investment Strategist profesional.
Fokus: investasi rasional, berbasis data & konteks nyata.

DATA SAHAM {ticker}
Harga: {price}
Skor Sistem: {score:.2f} ({label})
Horizon: {horizon}

FUNDAMENTAL:
EPS={eps}, PER={per}, ROE={roe}, DER={der}

TEKNIKAL:
MA50={ma50}, MA200={ma200}

SENTIMEN BERITA TERBARU:
Sentimen Dominan: {sentiment.upper()}
Judul Berita:
{berita_text}

ATURAN PENTING:
- Jika sentimen POSITIF / NEGATIF → gunakan judul berita sebagai konteks
- Jika NETRAL / tidak ada berita → jangan mengarang narasi
"""

    user_prompt = f"""
Buatkan INSIGHT INVESTASI profesional (Markdown):

1. Ringkasan kondisi saham (gabungkan fundamental + sentimen)
2. Interpretasi sentimen berita (APA MAKNA BERITANYA)
3. Strategi investor rasional
4. Risiko utama (bukan spekulasi harga)

Gunakan bahasa analis pasar modal.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content
