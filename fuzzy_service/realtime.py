import pandas as pd
import json

from db import get_conn


def save_stock_realtime(
    id_stock,
    snapshot_at,

    eps=None,
    per=None,
    roe=None,
    der=None,
    fcf=None,

    close_price=None,
    volume=None,
    ma50=None,
    ma200=None,
    volma200=None,
    rsi=None,
    gradient=None,

    sentimen=None,

    fuzzy_score=None,
    kategori=None,
    horizon=None,

    insight=None,
    membership=None
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

            insight,
            membership
        )
        VALUES (
            %s, %s,

            %s, %s, %s, %s, %s,

            %s, %s, %s, %s, %s, %s, %s,

            %s,

            %s, %s, %s,

            %s, %s
        )
    """

    membership_json = (
        json.dumps(membership, ensure_ascii=False)
        if membership is not None
        else None
    )

    values = (
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

        insight,
        membership_json
    )

    cur.execute(sql, values)

    realtime_id = cur.lastrowid

    conn.commit()

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

def get_realtime_history(ticker, tanggal=None):
    sql = """
        SELECT
            sr.*,
            sl.ticker,
            sl.nama_perusahaan,
            sl.sektor
        FROM stock_realtime sr
        JOIN stock_lq45 sl
            ON sr.id_stock = sl.id_stock
        WHERE sl.ticker = %s
    """

    params = [ticker]

    if tanggal:
        sql += " AND DATE(sr.snapshot_at) = %s"
        params.append(tanggal)

    sql += " ORDER BY sr.snapshot_at ASC"

    conn = get_conn()

    try:
        return pd.read_sql(
            sql,
            conn,
            params=params
        )
    finally:
        conn.close()

def update_realtime_insight(id_realtime, insight):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        UPDATE stock_realtime
        SET insight = %s
        WHERE id_realtime = %s
    """

    cur.execute(sql, (insight, id_realtime))

    conn.commit()

    cur.close()
    conn.close()

def get_previous_realtime(ticker, current_id):

    conn = get_conn()

    cur = conn.cursor(
        dictionary=True
    )

    sql = """
        SELECT
            sr.id_realtime,
            sr.kategori,
            sr.horizon,
            sr.sentimen,
            sr.fuzzy_score,
            sr.insight,
            sr.snapshot_at
        FROM stock_realtime sr
        JOIN stock_lq45 s
            ON s.id_stock = sr.id_stock
        WHERE s.ticker = %s
          AND sr.id_realtime < %s
        ORDER BY sr.id_realtime DESC
        LIMIT 1
    """

    cur.execute(
        sql,
        (
            ticker,
            current_id
        )
    )

    result = cur.fetchone()

    cur.close()

    conn.close()

    return result

def get_latest_realtime():

    conn = get_conn()

    sql = """
        SELECT
            sr.id_realtime,
            sr.id_stock,

            sl.ticker,
            sl.nama_perusahaan,
            sl.sektor,

            sr.snapshot_at,

            /* =========================
               FUNDAMENTAL
               ========================= */

            sr.eps,
            sr.per,
            sr.roe,
            sr.der,
            sr.fcf,

            /* =========================
               TEKNIKAL
               ========================= */

            sr.close_price,
            sr.volume,
            sr.ma50,
            sr.ma200,
            sr.volma200,
            sr.rsi,
            sr.gradient,

            /* =========================
               SENTIMEN
               ========================= */

            sr.sentimen,

            /* =========================
               FUZZY
               ========================= */

            sr.membership,
            sr.fuzzy_score,
            sr.kategori,
            sr.horizon,

            /* =========================
               RULE
               ========================= */

            sr.insight,

            sr.created_at

        FROM stock_realtime sr

        INNER JOIN stock_lq45 sl
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

        ORDER BY
            sr.fuzzy_score DESC,
            sl.ticker ASC
    """

    try:

        cur = conn.cursor(dictionary=True)

        cur.execute(sql)

        rows = cur.fetchall()

        return rows

    finally:

        cur.close()
        conn.close()