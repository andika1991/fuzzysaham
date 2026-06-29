# db.py
import mysql.connector
import os
import pandas as pd


DB_CONFIG = {
  "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def get_lq45_stocks():
    """
    Ambil saham LQ45 dari DB
    """
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT id_stock, ticker, sektor
        FROM stock_lq45
        ORDER BY ticker
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_latest_stock_rows():
    sql = """
    SELECT
        sd.stockdata_id,
        sl.ticker AS ticker,
        sl.sektor AS Sektor,
        sd.close_price, sd.eps, sd.per, sd.roe, sd.der, sd.fcf,
        sd.ma50, sd.ma200, sd.volume, sd.volma200, sd.rsi,
        (sd.close_price - LAG(sd.close_price,5)
            OVER (PARTITION BY sd.id_stock ORDER BY sd.date))
        / LAG(sd.close_price,5)
            OVER (PARTITION BY sd.id_stock ORDER BY sd.date)
        AS gradient
    FROM stock_data sd
    JOIN stock_lq45 sl ON sd.id_stock = sl.id_stock
    WHERE sd.date = (
        SELECT MAX(date)
        FROM stock_data s2
        WHERE s2.id_stock = sd.id_stock
    )
    """
    conn = get_conn()
    df = pd.read_sql(sql, conn)
    conn.close()
    return df



def get_fuzzy_rules():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM rule", conn)
    conn.close()
    return df



def get_sentiment_value(ticker):
    sql = """
    SELECT sentiment
    FROM sentiment_emiten_daily
    WHERE ticker=%s
    ORDER BY date DESC
    LIMIT 1
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (ticker,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return 0.5

    return {"positif":1.0, "netral":0.5, "negatif":0.0}.get(row[0], 0.5)





def save_fuzzy_membership(stockdata_id, mbs):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
    INSERT INTO fuzzy_membership
    (eps_level, per_level, roe_level, der_level, fcf_level,
     trend_ma50, trend_ma200, gradient_level, rsi_level, volume_level,
     sentimen_level, stockdata_id)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    def max_key(d): 
        return max(d, key=d.get) if d else None

    cur.execute(sql, (
        max_key(mbs["EPS"]),
        max_key(mbs["PER"]),
        max_key(mbs["ROE"]),
        max_key(mbs["DER"]),
        max_key(mbs["FCF"]),
        max_key(mbs["MA50"]),
        max_key(mbs["MA200"]),
        max_key(mbs["GRADIENT"]),
        max_key(mbs["RSI"]),
        max_key(mbs["VOLUME"]),
        max_key(mbs["SENTIMEN"]),
        stockdata_id
    ))

    conn.commit()
    conn.close()


def save_fuzzy_output(
    stockdata_id,
    score,
    kategori,
    horizon,
    rule_id=None,
    rule_condition=None,
    firing_strength=None
):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO fuzzy_output (
            stockdata_id,
            fuzzy_score,
            kategori,
            horizon,
            rule_id,
            rule_condition,
            firing_strength
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        stockdata_id,
        score,
        kategori,
        horizon,
        rule_id,
        rule_condition,
        firing_strength
    ))

    conn.commit()
    cursor.close()
    conn.close()

def get_sector_stats():
  
    sql = """
    SELECT
        sektor AS Sektor,
        eps_mean, eps_std,
        per_mean, per_std,
        roe_mean, roe_std,
        fcf_mean, fcf_std,
        der_mean, der_std
    FROM sector_stats
    """

    conn = get_conn()
    df = pd.read_sql(sql, conn)
    conn.close()

    return df.set_index("Sektor")


def save_insight(output_id, insight_text):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
    UPDATE fuzzy_output
    SET insight = %s
    WHERE output_id = %s
    """

    cur.execute(sql, (insight_text, output_id))
    conn.commit()
    conn.close()

def get_latest_fuzzy_for_insight(ticker=None):
    conn = get_conn()

    sql = """
    SELECT
        fo.output_id,
        fo.stockdata_id,

        fo.fuzzy_score AS score,
        fo.kategori AS label,
        fo.horizon,
        fo.created_at,

        fo.rule_id,
        fo.rule_condition,
        fo.firing_strength,

        sl.ticker,
        sl.nama_perusahaan,
        sl.sektor,

        sd.close_price,
        sd.eps,
        sd.per,
        sd.roe,
        sd.fcf,
        sd.der,
        sd.ma50,
        sd.ma200,
        sd.volume,
        sd.volma200,
        sd.rsi,

        fm.eps_level,
        fm.per_level,
        fm.roe_level,
        fm.fcf_level,
        fm.der_level,
        fm.trend_ma50,
        fm.trend_ma200,
        fm.gradient_level,
        fm.rsi_level,
        fm.volume_level,
        fm.sentimen_level

    FROM fuzzy_output fo
    JOIN stock_data sd
        ON fo.stockdata_id = sd.stockdata_id
    JOIN stock_lq45 sl
        ON sd.id_stock = sl.id_stock
    LEFT JOIN fuzzy_membership fm
        ON fo.stockdata_id = fm.stockdata_id

    WHERE fo.created_at = (
        SELECT MAX(fo2.created_at)
        FROM fuzzy_output fo2
        JOIN stock_data sd2
            ON fo2.stockdata_id = sd2.stockdata_id
        WHERE sd2.id_stock = sd.id_stock
    )
    """

    params = []

    if ticker:
        sql += """
        AND sl.ticker = %s
        """
        params.append(ticker)

    sql += """
    ORDER BY fo.fuzzy_score DESC
    """

    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
        
def get_latest_sentiment_with_news(ticker, limit=3):
    sql = """
    SELECT
        s.sentiment,
        GROUP_CONCAT(d.judul ORDER BY d.date DESC SEPARATOR ' || ') AS judul_berita
    FROM sentiment_emiten_daily s
    LEFT JOIN sentiment_emiten_detail d
        ON s.ticker = d.ticker
        AND s.date = DATE(d.date)
    WHERE s.ticker = %s
      AND s.date = (
          SELECT MAX(date)
          FROM sentiment_emiten_daily
          WHERE ticker = %s
      )
    GROUP BY s.sentiment
    """

    conn = get_conn()

    try:
        cur = conn.cursor()
        cur.execute(sql, (ticker, ticker))
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if not row:
        return {
            "sentiment": "netral",
            "judul": []
        }

    sentiment = row[0] or "netral"
    judul_berita = row[1]

    judul = judul_berita.split(" || ") if judul_berita else []

    return {
        "sentiment": sentiment,
        "judul": judul[:limit]
    }