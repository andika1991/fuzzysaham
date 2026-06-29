import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_investment_insight(row_data, sentiment_data=None):
    if sentiment_data is None:
        sentiment_data = {}

    if hasattr(row_data, "to_dict"):
        row_data = row_data.to_dict()

    # ==========================
    # 1. EKSTRAKSI DATA UTAMA
    # ==========================
    ticker = row_data.get("Ticker", row_data.get("ticker", "UNKNOWN"))
    date = row_data.get("Date", row_data.get("date", ""))
    sector = row_data.get("Sector", row_data.get("sector", row_data.get("Sektor", "")))
    price = row_data.get("close_price", row_data.get("Harga", row_data.get("price", 0)))

    score = row_data.get("Score", row_data.get("score", 0))
    label = row_data.get("Label", row_data.get("label", "Netral"))
    horizon = row_data.get("Time_Horizon", row_data.get("horizon", "Tidak tersedia"))

    # Fundamental
    eps = row_data.get("eps", row_data.get("EPS", 0))
    per = row_data.get("per", row_data.get("PER", 0))
    roe = row_data.get("roe", row_data.get("ROE", 0))
    fcf = row_data.get("fcf", row_data.get("FCF", 0))
    der = row_data.get("der", row_data.get("DER", 0))

    # Teknikal
    ma50 = row_data.get("ma50", row_data.get("MA50", 0))
    ma200 = row_data.get("ma200", row_data.get("MA200", 0))
    gradien = row_data.get(
        "gradien",
        row_data.get("gradient", row_data.get("GRADIEN", row_data.get("GRADIENT", 0)))
    )
    volume = row_data.get("volume", row_data.get("Volume", 0))
    volma200 = row_data.get("volma200", row_data.get("VolMA200", row_data.get("VOLMA200", 0)))
    rsi = row_data.get("rsi", row_data.get("RSI", 0))

    # Sentimen
    sentimen = sentiment_data.get(
        "sentiment",
        row_data.get("sentimen", row_data.get("Sentimen", "Netral"))
    )

    # ==========================
    # 2. DATA BERITA OPSIONAL
    # ==========================
    judul_list = sentiment_data.get("judul", [])

    news_title = row_data.get("news_title", "")
    news_summary = row_data.get("news_summary", "")
    news_sentiment = row_data.get("news_sentiment", sentimen)
    news_score = row_data.get("news_score", sentiment_data.get("score", ""))

    if judul_list:
        news_title = "\n".join([f"- {j}" for j in judul_list])

    if news_title:
        news_block = f"""
Data berita:
Judul berita:
{news_title}

Ringkasan berita: {news_summary}
Sentimen berita: {news_sentiment}
Skor sentimen berita: {news_score}
"""
    else:
        news_block = """
Data berita:
Tidak tersedia.
"""

    # ==========================
    # 3. HASIL FUZZY
    # ==========================
    active_rule = row_data.get(
        "active_rule",
        row_data.get("rule_id", row_data.get("RULE", "Tidak tersedia"))
    )

    rule_condition = row_data.get(
        "rule_condition",
        row_data.get("rule", row_data.get("kondisi_rule", "Tidak tersedia"))
    )

    firing_strength = row_data.get("firing_strength", 0)

    # ==========================
    # 4. AREA HARGA SEDERHANA
    # ==========================
    try:
        p = float(price)
        buy_min = int(p * 0.90)
        buy_max = int(p * 1.02)
        target_price = int(p * 1.20)
    except Exception:
        buy_min, buy_max, target_price = 0, 0, 0

    # ==========================
    # 5. PROMPT SYSTEM
    # ==========================
    prompt_system = f"""
Anda adalah asisten analisis saham yang bertugas menjelaskan hasil rekomendasi dari sistem fuzzy Mamdani.

Gaya bahasa:
- Profesional, objektif, ringkas, dan mudah dipahami.
- Jangan memberikan kepastian keuntungan.
- Jangan menyatakan ajakan beli atau jual secara mutlak.
- Jelaskan bahwa hasil hanya sebagai alat bantu analisis.
- Penjelasan harus mengacu pada data, hasil fuzifikasi, rule aktif, firing strength, dan nilai defuzzifikasi.
- Bagian rule aktif harus dianalisis, bukan hanya disebutkan.
- Output rekomendasi utama tetap mengikuti hasil sistem fuzzy Mamdani.
- Jangan mengubah kategori akhir, horizon, rule aktif, firing strength, atau skor fuzzy.

Data saham:
Kode saham: {ticker}
Tanggal analisis: {date}
Sektor: {sector}
Harga saat ini: {price}

Informasi sektor:
Fuzifikasi indikator fundamental dilakukan berdasarkan perbandingan nilai saham terhadap rata-rata dan standar deviasi seluruh saham pada sektor {sector}. Dengan demikian, EPS, PER, ROE, FCF, dan DER dinilai secara relatif terhadap karakteristik sektor yang sama.

Data fundamental:
EPS: {eps}
PER: {per}
ROE: {roe}
FCF: {fcf}
DER: {der}

Data teknikal dan sentimen:
MA50: {ma50}
MA200: {ma200}
Gradien: {gradien}
Volume: {volume}
VolMA200: {volma200}
RSI: {rsi}
Sentimen: {sentimen}

{news_block}

Hasil fuzifikasi fundamental:
EPS Rendah: {row_data.get("eps_low", 0)}
EPS Sedang: {row_data.get("eps_mid", 0)}
EPS Tinggi: {row_data.get("eps_high", 0)}

PER Rendah: {row_data.get("per_low", 0)}
PER Sedang: {row_data.get("per_mid", 0)}
PER Tinggi: {row_data.get("per_high", 0)}

ROE Rendah: {row_data.get("roe_low", 0)}
ROE Sedang: {row_data.get("roe_mid", 0)}
ROE Tinggi: {row_data.get("roe_high", 0)}

FCF Rendah: {row_data.get("fcf_low", 0)}
FCF Sedang: {row_data.get("fcf_mid", 0)}
FCF Tinggi: {row_data.get("fcf_high", 0)}

DER Rendah: {row_data.get("der_low", 0)}
DER Sedang: {row_data.get("der_mid", 0)}
DER Tinggi: {row_data.get("der_high", 0)}

Hasil fuzifikasi teknikal dan sentimen:
MA50 Bearish: {row_data.get("ma50_bear", 0)}
MA50 Netral: {row_data.get("ma50_net", 0)}
MA50 Bullish: {row_data.get("ma50_bull", 0)}

MA200 Bearish: {row_data.get("ma200_bear", 0)}
MA200 Netral: {row_data.get("ma200_net", 0)}
MA200 Bullish: {row_data.get("ma200_bull", 0)}

Gradien Negatif: {row_data.get("gradien_neg", row_data.get("gradient_neg", 0))}
Gradien Netral: {row_data.get("gradien_net", row_data.get("gradient_net", 0))}
Gradien Positif: {row_data.get("gradien_pos", row_data.get("gradient_pos", 0))}

Volume Rendah: {row_data.get("volume_low", 0)}
Volume Sedang: {row_data.get("volume_mid", 0)}
Volume High: {row_data.get("volume_high", 0)}

RSI Oversold: {row_data.get("rsi_oversold", 0)}
RSI Netral: {row_data.get("rsi_netral", 0)}
RSI Overbought: {row_data.get("rsi_overbought", 0)}

Sentimen Negatif: {row_data.get("sentimen_negatif", 0)}
Sentimen Netral: {row_data.get("sentimen_netral", 0)}
Sentimen Positif: {row_data.get("sentimen_positif", 0)}

Hasil inferensi fuzzy:
Rule aktif: {active_rule}
Kondisi rule aktif: {rule_condition}
Firing strength: {firing_strength}
Output rule: {label}
Horizon rule: {horizon}

Hasil defuzzifikasi:
Nilai defuzzifikasi: {score}
Kategori akhir: {label}
Horizon rekomendasi: {horizon}

TUGAS:
Buatlah penjelasan rekomendasi saham dengan format markdown berikut.

OUTPUT FORMAT:

# 📑 RENCANA INVESTASI: {ticker}
**Horizon: {horizon}** | **Skor Fuzzy: {score}/1.0**

---

### 🏢 1. FUNDAMENTAL CHECK (Kualitas Bisnis)
Jelaskan kondisi EPS, PER, ROE, FCF, dan DER berdasarkan hasil fuzifikasi fundamental.
Jelaskan bahwa fundamental dinilai secara relatif terhadap sektor {sector}.
Tekankan faktor yang mendukung dan faktor yang perlu diperhatikan.

### 📈 2. TEKNIKAL, MOMENTUM & SENTIMEN
Jelaskan kondisi MA50, MA200, gradien, volume, RSI, dan sentimen.
Jika data berita tersedia, jelaskan pengaruh berita terhadap sentimen.
Jika data berita tidak tersedia, cukup jelaskan bahwa tidak terdapat data berita spesifik yang digunakan dalam penjelasan.

### 🔎 3. ANALISIS RULE AKTIF SISTEM
Sebutkan rule aktif yang digunakan sistem, yaitu {rule_condition}.
Jelaskan kondisi rule aktif: {rule_condition}.
Jelaskan mengapa rule tersebut aktif berdasarkan hasil fuzifikasi.

Analisis makna kondisi rule:
- Gradien Positif menunjukkan arah perubahan harga sedang meningkat.
- Volume High menunjukkan aktivitas transaksi berada di atas rata-rata.
- RSI Overbought menunjukkan tekanan beli tinggi, tetapi juga perlu diwaspadai karena berpotensi koreksi.
- Sentimen Netral menunjukkan tidak terdapat dorongan berita positif maupun tekanan berita negatif yang dominan.

Jelaskan bahwa firing strength sebesar {firing_strength} menunjukkan tingkat aktivasi rule.
Jika firing strength bernilai 1, jelaskan bahwa seluruh kondisi pada rule terpenuhi secara penuh.

Jelaskan alasan output rule menjadi {label} dengan horizon {horizon}.
Tekankan bahwa output Potensial pada rule ini lebih didorong oleh momentum teknikal jangka pendek, bukan oleh sinyal investasi jangka panjang.

### 🗺️ 4. STRATEGI BERDASARKAN HORIZON
* **Rekomendasi Sistem**: {label}
* **Horizon**: {horizon}
* **Rule Aktif**: {active_rule}
* **Firing Strength**: {firing_strength}
* **Area Pantauan Harga**: Rp {buy_min} - Rp {buy_max}
* **Estimasi Target Teknis**: Menuju Rp {target_price}

Jelaskan bahwa horizon {horizon} harus dipahami sesuai karakter rule aktif.
Jika horizon adalah Scalping, tekankan bahwa rekomendasi hanya untuk peluang jangka sangat pendek, bukan investasi jangka panjang.
Jika horizon adalah Fast Trade, tekankan bahwa rekomendasi digunakan untuk peluang 1–5 hari.
Jika horizon adalah Swing Trade, tekankan bahwa rekomendasi digunakan untuk peluang 1–4 minggu.
Jika horizon adalah Hold Menengah, tekankan bahwa rekomendasi digunakan untuk peluang 1–3 bulan.
Jika horizon adalah Hold Menengah-Panjang, tekankan bahwa rekomendasi digunakan untuk peluang di atas 6 bulan.
Jika horizon adalah Wait atau Watchlist, jelaskan bahwa saham belum memiliki sinyal yang cukup kuat.
Jika horizon adalah Avoid, jelaskan bahwa saham tidak direkomendasikan oleh sistem.

### 🛡️ 5. RISIKO & BATASAN ANALISIS
Jelaskan faktor risiko, seperti RSI overbought, MA200 bearish, DER tinggi, sentimen yang belum positif, atau tidak tersedianya berita jika relevan.
Jelaskan kapan rekomendasi dapat menjadi tidak valid.

Akhiri dengan disclaimer:
Analisis ini hanya sebagai alat bantu pengambilan keputusan dan bukan ajakan membeli atau menjual saham secara mutlak.
"""

    prompt_user = f"Susun rencana investasi untuk saham {ticker} berdasarkan hasil fuzzy Mamdani."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ],
            temperature=0.4
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error OpenAI: {e}"