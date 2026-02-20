import mysql.connector
import os
from mysql.connector import Error
from datetime import date

# ===============================
# KONFIGURASI DB
# ===============================
DB_CONFIG = {
  "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306))
}

# ===============================
# KONEKSI
# ===============================
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ===============================
# SIMPAN DETAIL BERITA
# ===============================
def save_sentiment_detail(ticker, judul, link, sentiment):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO sentiment_emiten_detail
        (date, ticker, judul, link, sentiment)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            date.today(),
            ticker,
            judul,
            link,
            sentiment
        ))

        conn.commit()

    except Error as e:
        print(f"[DB ERROR] save_sentiment_detail: {e}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


def save_sentiment_daily(ticker, sentiment, total_berita):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO sentiment_emiten_daily
        (date, ticker, sentiment, total_berita)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sentiment = VALUES(sentiment),
            total_berita = VALUES(total_berita),
            created_at = CURRENT_TIMESTAMP
        """

        cursor.execute(sql, (
            date.today(),
            ticker,
            sentiment,
            total_berita
        ))

        conn.commit()

    except Error as e:
        print(f"[DB ERROR] save_sentiment_daily: {e}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
