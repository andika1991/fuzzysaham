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

    conn = get_conn()

    sql = """
    SELECT
        x.stockdata_id,
        x.id_stock,
        x.ticker,
        x.Sektor,

        x.close_price,
        x.eps,
        x.per,
        x.roe,
        x.der,
        x.fcf,

        x.ma50,
        x.ma200,
        x.volume,
        x.volma200,
        x.rsi,
        x.gradient,

        x.date

    FROM (
        SELECT
            sd.stockdata_id,
            sd.id_stock,

            sl.ticker AS ticker,
            sl.sektor AS Sektor,

            sd.close_price,
            sd.eps,
            sd.per,
            sd.roe,
            sd.der,
            sd.fcf,

            sd.ma50,
            sd.ma200,
            sd.volume,
            sd.volma200,
            sd.rsi,

            (
                sd.close_price
                -
                LAG(sd.close_price, 5)
                OVER (
                    PARTITION BY sd.id_stock
                    ORDER BY sd.date
                )
            )
            /
            NULLIF(
                LAG(sd.close_price, 5)
                OVER (
                    PARTITION BY sd.id_stock
                    ORDER BY sd.date
                ),
                0
            ) AS gradient,

            sd.date

        FROM stock_data sd

        JOIN stock_lq45 sl
            ON sd.id_stock = sl.id_stock

    ) AS x

    WHERE x.date = (
        SELECT MAX(s2.date)
        FROM stock_data s2
        WHERE s2.id_stock = x.id_stock
    )

    ORDER BY x.ticker
    """

    try:

        df = pd.read_sql(
            sql,
            conn
        )

        return df

    finally:

        conn.close()



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

def get_latest_fuzzy_for_insight(ticker=None, tanggal=None):

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

        sd.date AS tanggal,
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

    WHERE 1 = 1
    """

    params = []


    # ============================================
    # FILTER TICKER
    # ============================================

    if ticker:

        sql += """
        AND sl.ticker = %s
        """

        params.append(ticker)


    # ============================================
    # FILTER TANGGAL
    # ============================================

    if tanggal:

        sql += """
        AND DATE(sd.date) = %s
        """

        params.append(tanggal)

    else:

        # Jika tanggal tidak diberikan,
        # ambil tanggal terbaru untuk ticker

        sql += """
        AND DATE(sd.date) = (
            SELECT MAX(DATE(sd2.date))
            FROM stock_data sd2
            JOIN stock_lq45 sl2
                ON sd2.id_stock = sl2.id_stock
            WHERE sl2.ticker = sl.ticker
        )
        """


    # ============================================
    # URUTKAN
    # ============================================

    sql += """
    ORDER BY fo.fuzzy_score DESC
    """


    try:

        return pd.read_sql(
            sql,
            conn,
            params=params
        )

    finally:

        conn.close()
        
def get_latest_sentiment_with_news(
    ticker,
    tanggal=None,
    limit=3
):
    sql = """
    SELECT
        s.sentiment,
        GROUP_CONCAT(
            d.judul
            ORDER BY d.date DESC
            SEPARATOR ' || '
        ) AS judul_berita

    FROM sentiment_emiten_daily s

    LEFT JOIN sentiment_emiten_detail d
        ON s.ticker = d.ticker
        AND s.date = DATE(d.date)

    WHERE s.ticker = %s
    """

    params = [ticker]

    # ========================================================
    # JIKA TANGGAL DIBERIKAN
    # ========================================================

    if tanggal:

        sql += """
        AND DATE(s.date) = %s
        """

        params.append(tanggal)

    # ========================================================
    # JIKA TIDAK ADA TANGGAL
    # AMBIL SENTIMENT TERBARU
    # ========================================================

    else:

        sql += """
        AND s.date = (
            SELECT MAX(date)
            FROM sentiment_emiten_daily
            WHERE ticker = %s
        )
        """

        params.append(ticker)

    sql += """
    GROUP BY s.sentiment
    """

    conn = get_conn()

    try:

        cur = conn.cursor()

        cur.execute(
            sql,
            tuple(params)
        )

        row = cur.fetchone()

        cur.close()

    finally:

        conn.close()


    # ========================================================
    # TIDAK ADA DATA
    # ========================================================

    if not row:

        return {
            "sentiment": "netral",
            "judul": []
        }


    # ========================================================
    # HASIL SENTIMENT
    # ========================================================

    sentiment = row[0] or "netral"

    judul_berita = row[1]

    judul = (
        judul_berita.split(" || ")
        if judul_berita
        else []
    )

    return {
        "sentiment": sentiment,
        "judul": judul[:limit]
    }
def stock_data_exists(start_date, end_date):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM stock_data
            WHERE date BETWEEN %s AND %s
        )
    """, (
        start_date,
        end_date
    ))

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return bool(result)


def count_stock_data(start_date, end_date):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM stock_data
        WHERE date BETWEEN %s AND %s
    """, (
        start_date,
        end_date
    ))

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result

# ============================================================
# JUMLAH DATA STOCK PADA RENTANG TANGGAL
# ============================================================

def count_stock_data(start_date, end_date):

    sql = """
        SELECT COUNT(*) AS total
        FROM stock_data
        WHERE date BETWEEN %s AND %s
    """

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            sql,
            (start_date, end_date)
        )

        row = cursor.fetchone()

        return row["total"]

    finally:

        cursor.close()
        conn.close()


# ============================================================
# CEK FUZZY SUDAH DIPROSES PADA TANGGAL
# ============================================================

def fuzzy_data_exists(start_date, end_date):
    """
    Mengecek apakah fuzzy_output sudah tersedia
    untuk data saham pada rentang tanggal tertentu.
    """

    sql = """
        SELECT COUNT(*) AS total
        FROM fuzzy_output fo
        JOIN stock_data sd
            ON fo.stockdata_id = sd.stockdata_id
        WHERE sd.date BETWEEN %s AND %s
    """

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            sql,
            (start_date, end_date)
        )

        row = cursor.fetchone()

        return row["total"] > 0

    finally:

        cursor.close()
        conn.close()

def count_fuzzy_data(start_date, end_date):

    sql = """
        SELECT COUNT(*) AS total
        FROM fuzzy_output fo
        JOIN stock_data sd
            ON fo.stockdata_id = sd.stockdata_id
        WHERE sd.date BETWEEN %s AND %s
    """

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute(
            sql,
            (start_date, end_date)
        )

        row = cursor.fetchone()

        return row["total"]

    finally:

        cursor.close()
        conn.close()

def get_stock_rows_by_date(
    start_date,
    end_date
):

    conn = get_conn()

    sql = """
    SELECT
        x.stockdata_id,
        x.id_stock,
        x.ticker,
        x.Sektor,

        x.close_price,
        x.eps,
        x.per,
        x.roe,
        x.der,
        x.fcf,

        x.ma50,
        x.ma200,
        x.volume,
        x.volma200,
        x.rsi,
        x.gradient,

        x.date

    FROM (
        SELECT
            sd.stockdata_id,
            sd.id_stock,

            sl.ticker AS ticker,
            sl.sektor AS Sektor,

            sd.close_price,
            sd.eps,
            sd.per,
            sd.roe,
            sd.der,
            sd.fcf,

            sd.ma50,
            sd.ma200,
            sd.volume,
            sd.volma200,
            sd.rsi,

            (
                sd.close_price
                -
                LAG(sd.close_price, 5)
                OVER (
                    PARTITION BY sd.id_stock
                    ORDER BY sd.date
                )
            )
            /
            NULLIF(
                LAG(sd.close_price, 5)
                OVER (
                    PARTITION BY sd.id_stock
                    ORDER BY sd.date
                ),
                0
            ) AS gradient,

            sd.date

        FROM stock_data sd

        JOIN stock_lq45 sl
            ON sd.id_stock = sl.id_stock

    ) AS x

    WHERE x.date BETWEEN %s AND %s

    ORDER BY
        x.date,
        x.ticker
    """

    try:

        df = pd.read_sql(
            sql,
            conn,
            params=(
                start_date,
                end_date
            )
        )

        return df

    finally:

        conn.close()



def stock_date_exists(id_stock, tanggal):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM stock_data
            WHERE id_stock = %s
              AND date = %s
        """, (
            id_stock,
            tanggal
        ))

        return cur.fetchone()[0] > 0

    finally:
        cur.close()
        conn.close()

def stock_date_complete(tanggal):

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COUNT(DISTINCT id_stock)
            FROM stock_data
            WHERE date = %s
        """, (tanggal,))

        existing = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM stock_lq45
        """)

        total_stock = cur.fetchone()[0]

        return existing >= total_stock

    finally:
        cur.close()
        conn.close()

def get_latest_stock_date():
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT MAX(date)
            FROM stock_data
        """)

        result = cur.fetchone()[0]

        return result

    finally:
        cur.close()
        conn.close()


def save_stock_realtime(
    id_stock,
    snapshot_at,
    eps,
    per,
    roe,
    der,
    fcf,
    close_price,
    volume,
    ma50,
    ma200,
    volma200,
    rsi,
    gradient,
    sentimen,
    fuzzy_score,
    kategori,
    horizon,
    insight=None
):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        INSERT INTO stock_realtime (
            id_stock,
            snapshot_at,
            eps,
            per,
            roe,
            der,
            fcf,
            close_price,
            volume,
            ma50,
            ma200,
            volma200,
            rsi,
            gradient,
            sentimen,
            fuzzy_score,
            kategori,
            horizon,
            insight
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    cur.execute(sql, (
        id_stock,
        snapshot_at,
        eps,
        per,
        roe,
        der,
        fcf,
        close_price,
        volume,
        ma50,
        ma200,
        volma200,
        rsi,
        gradient,
        sentimen,
        fuzzy_score,
        kategori,
        horizon,
        insight
    ))

    conn.commit()

    realtime_id = cur.lastrowid

    cur.close()
    conn.close()

    return realtime_id

def get_latest_realtime():
    sql = """
        SELECT
            sr.*,
            sl.ticker,
            sl.nama_perusahaan,
            sl.sektor
        FROM stock_realtime sr
        JOIN stock_lq45 sl
            ON sr.id_stock = sl.id_stock
        INNER JOIN (
            SELECT
                id_stock,
                MAX(snapshot_at) AS latest_snapshot
            FROM stock_realtime
            GROUP BY id_stock
        ) latest
            ON sr.id_stock = latest.id_stock
            AND sr.snapshot_at = latest.latest_snapshot
        ORDER BY sr.fuzzy_score DESC
    """

    conn = get_conn()

    try:
        df = pd.read_sql(sql, conn)
        return df
    finally:
        conn.close()