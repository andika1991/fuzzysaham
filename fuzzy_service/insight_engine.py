import os
from openai import OpenAI


# ==========================
# GROQ CLIENT
# ==========================

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_investment_insight(row_data, sentiment_data=None):

    if sentiment_data is None:
        sentiment_data = {}

    if hasattr(row_data, "to_dict"):
        row_data = row_data.to_dict()

    # ==========================
    # 1. EKSTRAKSI DATA UTAMA
    # ==========================

    ticker = row_data.get(
        "Ticker",
        row_data.get("ticker", "UNKNOWN")
    )

    date = row_data.get(
        "Date",
        row_data.get("date", "")
    )

    sector = row_data.get(
        "Sector",
        row_data.get(
            "sector",
            row_data.get("Sektor", "")
        )
    )

    price = row_data.get(
        "close_price",
        row_data.get(
            "Harga",
            row_data.get("price", 0)
        )
    )

    score = row_data.get(
        "Score",
        row_data.get("score", 0)
    )

    label = row_data.get(
        "Label",
        row_data.get("label", "Netral")
    )

    horizon = row_data.get(
        "Time_Horizon",
        row_data.get(
            "horizon",
            "Tidak tersedia"
        )
    )

    # ==========================
    # FUNDAMENTAL
    # ==========================

    eps = row_data.get(
        "eps",
        row_data.get("EPS", 0)
    )

    per = row_data.get(
        "per",
        row_data.get("PER", 0)
    )

    roe = row_data.get(
        "roe",
        row_data.get("ROE", 0)
    )

    fcf = row_data.get(
        "fcf",
        row_data.get("FCF", 0)
    )

    der = row_data.get(
        "der",
        row_data.get("DER", 0)
    )

    # ==========================
    # TEKNIKAL
    # ==========================

    ma50 = row_data.get(
        "ma50",
        row_data.get("MA50", 0)
    )

    ma200 = row_data.get(
        "ma200",
        row_data.get("MA200", 0)
    )

    gradien = row_data.get(
        "gradien",
        row_data.get(
            "gradient",
            row_data.get(
                "GRADIEN",
                row_data.get(
                    "GRADIENT",
                    0
                )
            )
        )
    )

    volume = row_data.get(
        "volume",
        row_data.get("Volume", 0)
    )

    volma200 = row_data.get(
        "volma200",
        row_data.get(
            "VolMA200",
            row_data.get(
                "VOLMA200",
                0
            )
        )
    )

    rsi = row_data.get(
        "rsi",
        row_data.get("RSI", 0)
    )

    # ==========================
    # SENTIMEN
    # ==========================

    sentimen = sentiment_data.get(
        "sentiment",
        row_data.get(
            "sentimen",
            row_data.get(
                "Sentimen",
                "Netral"
            )
        )
    )

    # ==========================
    # HASIL MEMBERSHIP FUZZY
    # ==========================
    #
    # Membership dari Fuzzy Engine
    # dapat menggunakan key seperti:
    #
    # EPS
    # PER
    # ROE
    # FCF
    # DER
    # MA50
    # MA200
    # GRADIEN
    # GRADIENT
    # VOLUME
    # RSI
    # SENTIMEN
    #
    # Karena Python case-sensitive,
    # seluruh key dinormalisasi ke lowercase.
    # ==========================

    membership_raw = row_data.get(
        "membership",
        {}
    )

    membership = {}

    if isinstance(membership_raw, dict):

        for key, value in membership_raw.items():

            if not isinstance(value, dict):
                continue

            normalized_key = str(
                key
            ).strip().lower()

            normalized_value = {}

            for member_key, member_value in value.items():

                normalized_member_key = str(
                    member_key
                ).strip().lower()

                normalized_value[
                    normalized_member_key
                ] = member_value

            membership[
                normalized_key
            ] = normalized_value

    # ==========================
    # MEMBERSHIP FUNDAMENTAL
    # ==========================

    eps_membership = membership.get(
        "eps",
        {}
    )

    per_membership = membership.get(
        "per",
        {}
    )

    roe_membership = membership.get(
        "roe",
        {}
    )

    fcf_membership = membership.get(
        "fcf",
        {}
    )

    der_membership = membership.get(
        "der",
        {}
    )

    # ==========================
    # MEMBERSHIP TEKNIKAL
    # ==========================

    ma50_membership = membership.get(
        "ma50",
        {}
    )

    ma200_membership = membership.get(
        "ma200",
        {}
    )

    gradient_membership = membership.get(
        "gradient",
        membership.get(
            "gradien",
            {}
        )
    )

    volume_membership = membership.get(
        "volume",
        {}
    )

    rsi_membership = membership.get(
        "rsi",
        {}
    )

    # ==========================
    # MEMBERSHIP SENTIMEN
    # ==========================

    sentiment_membership = membership.get(
        "sentimen",
        membership.get(
            "sentiment",
            {}
        )
    )

    # ==========================
    # DATA BERITA OPSIONAL
    # ==========================

    judul_list = sentiment_data.get(
        "judul",
        []
    )

    news_title = row_data.get(
        "news_title",
        ""
    )

    news_summary = row_data.get(
        "news_summary",
        ""
    )

    news_sentiment = row_data.get(
        "news_sentiment",
        sentimen
    )

    news_score = row_data.get(
        "news_score",
        sentiment_data.get(
            "score",
            ""
        )
    )

    if judul_list:

        news_title = "\n".join(
            [
                f"- {j}"
                for j in judul_list
            ]
        )

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
    # HASIL FUZZY
    # ==========================

    active_rule = row_data.get(
        "active_rule",
        row_data.get(
            "rule_id",
            row_data.get(
                "RULE",
                "Tidak tersedia"
            )
        )
    )

    rule_condition = row_data.get(
        "rule_condition",
        row_data.get(
            "rule",
            row_data.get(
                "kondisi_rule",
                "Tidak tersedia"
            )
        )
    )

    firing_strength = row_data.get(
        "firing_strength",
        0
    )

    # ==========================
    # AREA HARGA SEDERHANA
    # ==========================

    try:

        p = float(price)

        buy_min = int(
            p * 0.90
        )

        buy_max = int(
            p * 1.02
        )

        target_price = int(
            p * 1.20
        )

    except Exception:

        buy_min = 0
        buy_max = 0
        target_price = 0

    # ==========================
    # PROMPT SYSTEM
    # ==========================

    prompt_system = f"""
Anda adalah asisten analisis saham yang bertugas menjelaskan
hasil rekomendasi dari sistem Fuzzy Mamdani.

Gaya bahasa:
- Profesional, objektif, ringkas, dan mudah dipahami.
- Jangan memberikan kepastian keuntungan.
- Jangan menyatakan ajakan beli atau jual secara mutlak.
- Jelaskan bahwa hasil hanya sebagai alat bantu analisis.
- Penjelasan harus mengacu pada data, hasil fuzzifikasi,
  rule aktif, firing strength, dan nilai defuzzifikasi.
- Bagian rule aktif harus dianalisis, bukan hanya disebutkan.
- Output rekomendasi utama tetap mengikuti hasil sistem
  Fuzzy Mamdani.
- Jangan mengubah kategori akhir, horizon, rule aktif,
  firing strength, atau skor fuzzy.
- Nilai membership fuzzy merupakan hasil langsung dari
  mesin Fuzzy Mamdani.
- Gunakan nilai membership tersebut apa adanya.
- Jangan menghitung ulang nilai membership.
- Jangan mengubah nilai membership.
- Jika nilai membership lebih besar dari 0,
  tampilkan dan jelaskan sesuai nilainya.
- Jika nilai membership bernilai 0,
  tampilkan sebagai 0.

Data saham:

Kode saham: {ticker}
Tanggal analisis: {date}
Sektor: {sector}
Harga saat ini: {price}

Informasi sektor:

Fuzzifikasi indikator fundamental dilakukan berdasarkan
perbandingan nilai saham terhadap rata-rata dan standar
deviasi seluruh saham pada sektor {sector}.

Dengan demikian, EPS, PER, ROE, FCF, dan DER dinilai
secara relatif terhadap karakteristik sektor yang sama.

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


Hasil fuzzifikasi fundamental:

EPS:
- Rendah: {eps_membership.get("low", 0)}
- Sedang: {eps_membership.get("mid", 0)}
- Tinggi: {eps_membership.get("high", 0)}

PER:
- Rendah: {per_membership.get("low", 0)}
- Sedang: {per_membership.get("mid", 0)}
- Tinggi: {per_membership.get("high", 0)}

ROE:
- Rendah: {roe_membership.get("low", 0)}
- Sedang: {roe_membership.get("mid", 0)}
- Tinggi: {roe_membership.get("high", 0)}

FCF:
- Rendah: {fcf_membership.get("low", 0)}
- Sedang: {fcf_membership.get("mid", 0)}
- Tinggi: {fcf_membership.get("high", 0)}

DER:
- Rendah: {der_membership.get("low", 0)}
- Sedang: {der_membership.get("mid", 0)}
- Tinggi: {der_membership.get("high", 0)}


Hasil fuzzifikasi teknikal dan sentimen:

MA50:
- Bearish: {ma50_membership.get("bear", 0)}
- Netral: {ma50_membership.get("netral", 0)}
- Bullish: {ma50_membership.get("bull", 0)}

MA200:
- Bearish: {ma200_membership.get("bear", 0)}
- Netral: {ma200_membership.get("netral", 0)}
- Bullish: {ma200_membership.get("bull", 0)}

Gradien:
- Negatif: {gradient_membership.get("negatif", 0)}
- Netral: {gradient_membership.get("netral", 0)}
- Positif: {gradient_membership.get("positif", 0)}

Volume:
- Rendah: {volume_membership.get("low", 0)}
- Sedang: {volume_membership.get("mid", 0)}
- Tinggi: {volume_membership.get("high", 0)}

RSI:
- Oversold: {rsi_membership.get("oversold", 0)}
- Netral: {rsi_membership.get("netral", 0)}
- Overbought: {rsi_membership.get("overbought", 0)}

Sentimen:
- Negatif: {sentiment_membership.get("negatif", 0)}
- Netral: {sentiment_membership.get("netral", 0)}
- Positif: {sentiment_membership.get("positif", 0)}


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

Buatlah penjelasan rekomendasi saham dengan format
Markdown berikut.


OUTPUT FORMAT:

# 📑 RENCANA INVESTASI: {ticker}

**Horizon: {horizon}** | **Skor Fuzzy: {score}/1.0**

---

### 🏢 1. FUNDAMENTAL CHECK (Kualitas Bisnis)

Jelaskan kondisi EPS, PER, ROE, FCF, dan DER berdasarkan
hasil fuzzifikasi fundamental.

Jelaskan bahwa fundamental dinilai secara relatif terhadap
sektor {sector}.

Tekankan faktor yang mendukung dan faktor yang perlu
diperhatikan.


### 📈 2. TEKNIKAL, MOMENTUM & SENTIMEN

Jelaskan kondisi MA50, MA200, gradien, volume, RSI,
dan sentimen.

Jika data berita tersedia, jelaskan pengaruh berita
terhadap sentimen.

Jika data berita tidak tersedia, cukup jelaskan bahwa
tidak terdapat data berita spesifik yang digunakan
dalam penjelasan.


### 🔎 3. ANALISIS RULE AKTIF SISTEM

Sebutkan rule aktif yang digunakan sistem:

{rule_condition}

Jelaskan kondisi rule aktif berdasarkan hasil fuzzifikasi.

Jelaskan mengapa rule tersebut aktif berdasarkan nilai
membership yang tersedia.

Analisis makna kondisi rule jika relevan:

- Gradien Positif menunjukkan arah perubahan harga sedang meningkat.
- Volume High menunjukkan aktivitas transaksi berada di atas rata-rata.
- RSI Overbought menunjukkan tekanan beli tinggi, tetapi juga perlu
  diwaspadai karena berpotensi koreksi.
- Sentimen Netral menunjukkan tidak terdapat dorongan berita positif
  maupun tekanan berita negatif yang dominan.

Jelaskan bahwa firing strength sebesar
{firing_strength} menunjukkan tingkat aktivasi rule.

Jika firing strength bernilai 1, jelaskan bahwa seluruh
kondisi pada rule terpenuhi secara penuh.

Jelaskan alasan output rule menjadi {label}
dengan horizon {horizon}.

Jangan mengubah hasil rule dari sistem.


### 🗺️ 4. STRATEGI BERDASARKAN HORIZON

* **Rekomendasi Sistem**: {label}
* **Horizon**: {horizon}
* **Rule Aktif**: {active_rule}
* **Firing Strength**: {firing_strength}
* **Area Pantauan Harga**: Rp {buy_min} - Rp {buy_max}
* **Estimasi Target Teknis**: Menuju Rp {target_price}

Jelaskan bahwa horizon {horizon} harus dipahami
sesuai karakter rule aktif.

Jika horizon adalah Scalping, tekankan bahwa rekomendasi
hanya untuk peluang jangka sangat pendek, bukan investasi
jangka panjang.

Jika horizon adalah Fast Trade, tekankan bahwa rekomendasi
digunakan untuk peluang 1–5 hari.

Jika horizon adalah Swing Trade, tekankan bahwa rekomendasi
digunakan untuk peluang 1–4 minggu.

Jika horizon adalah Hold Menengah, tekankan bahwa rekomendasi
digunakan untuk peluang 1–4 bulan.

Jika horizon adalah Hold Menengah-Panjang, tekankan bahwa
rekomendasi digunakan untuk peluang di atas 6 bulan.

Jika horizon adalah Wait atau Watchlist, jelaskan bahwa
saham belum memiliki sinyal yang cukup kuat.

Jika horizon adalah Avoid, jelaskan bahwa saham tidak
direkomendasikan oleh sistem.


### 🛡️ 5. RISIKO & BATASAN ANALISIS

Jelaskan faktor risiko seperti:

- RSI overbought
- MA200 bearish
- DER tinggi
- sentimen belum positif
- tidak tersedianya berita

Gunakan hanya faktor yang relevan dengan data.

Jelaskan kapan hasil analisis dapat menjadi tidak valid.

Akhiri dengan disclaimer:

Analisis ini hanya sebagai alat bantu pengambilan keputusan
dan bukan ajakan membeli atau menjual saham secara mutlak.
"""

    # ==========================
    # 6. GENERATE INSIGHT
    # ==========================

    prompt_user = (
        f"Susun rencana investasi untuk saham "
        f"{ticker} berdasarkan hasil Fuzzy Mamdani."
    )

    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": prompt_system
                },
                {
                    "role": "user",
                    "content": prompt_user
                }
            ],

            temperature=0.4
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"Error Groq: {e}"