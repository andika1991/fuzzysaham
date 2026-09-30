import mysql.connector
import os
from mysql.connector import Error
from datetime import date


# ============================================================
# KONFIGURASI DB
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}


# ============================================================
# KONEKSI
# ============================================================

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# CEK BERITA SUDAH ADA
# ============================================================

def sentiment_detail_exists(link, tanggal=None):

    if tanggal is None:
        tanggal = date.today()

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        SELECT COUNT(*)
        FROM sentiment_emiten_detail
        WHERE link = %s
          AND date = %s
        """

        cursor.execute(
            sql,
            (
                link,
                tanggal
            )
        )

        result = cursor.fetchone()[0]

        return result > 0

    except Error as e:

        print(
            f"[DB ERROR] sentiment_detail_exists: {e}"
        )

        return False

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None and conn.is_connected():
            conn.close()


# ============================================================
# CEK SEMUA BERITA YANG SUDAH ADA HARI INI
# ============================================================

def news_already_exists_today(links, tanggal=None):

    if tanggal is None:
        tanggal = date.today()

    if not links:
        return True

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        placeholders = ",".join(
            ["%s"] * len(links)
        )

        sql = f"""
        SELECT COUNT(DISTINCT link)
        FROM sentiment_emiten_detail
        WHERE date = %s
          AND link IN ({placeholders})
        """

        params = [tanggal] + links

        cursor.execute(
            sql,
            params
        )

        existing = cursor.fetchone()[0]

        return existing == len(set(links))

    except Error as e:

        print(
            f"[DB ERROR] news_already_exists_today: {e}"
        )

        return False

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None and conn.is_connected():
            conn.close()


# ============================================================
# HITUNG BERITA HARI INI
# ============================================================

def count_today_news(tanggal=None):

    if tanggal is None:
        tanggal = date.today()

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        SELECT COUNT(DISTINCT link)
        FROM sentiment_emiten_detail
        WHERE date = %s
        """

        cursor.execute(
            sql,
            (tanggal,)
        )

        return cursor.fetchone()[0]

    except Error as e:

        print(
            f"[DB ERROR] count_today_news: {e}"
        )

        return 0

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None and conn.is_connected():
            conn.close()


# ============================================================
# SIMPAN DETAIL SENTIMEN
# ============================================================

def save_sentiment_detail(
    ticker,
    judul,
    link,
    sentiment
):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO sentiment_emiten_detail
        (
            date,
            ticker,
            judul,
            link,
            sentiment
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """

        cursor.execute(
            sql,
            (
                date.today(),
                ticker,
                judul,
                link,
                sentiment
            )
        )

        conn.commit()

    except Error as e:

        print(
            f"[DB ERROR] save_sentiment_detail: {e}"
        )

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None and conn.is_connected():
            conn.close()


# ============================================================
# SIMPAN SENTIMEN HARIAN
# ============================================================

def save_sentiment_daily(
    ticker,
    sentiment,
    total_berita
):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO sentiment_emiten_daily
        (
            date,
            ticker,
            sentiment,
            total_berita
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        ON DUPLICATE KEY UPDATE
            sentiment = VALUES(sentiment),
            total_berita = VALUES(total_berita),
            created_at = CURRENT_TIMESTAMP
        """

        cursor.execute(
            sql,
            (
                date.today(),
                ticker,
                sentiment,
                total_berita
            )
        )

        conn.commit()

    except Error as e:

        print(
            f"[DB ERROR] save_sentiment_daily: {e}"
        )

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None and conn.is_connected():
            conn.close()