from db import get_db


class StockDetail:

    # ============================================================
    # DETAIL SAHAM
    # fuzzy_output -> stockdata_id -> stock_data
    # ============================================================

    @staticmethod
    def get_detail_by_ticker(ticker, tanggal=None):

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            query = """
                SELECT
                    fo.output_id,
                    fo.stockdata_id,
                    fo.fuzzy_score,
                    fo.kategori,
                    fo.horizon,
                    fo.created_at,
                    fo.insight,

                    s.id_stock,
                    s.ticker,
                    s.nama_perusahaan,

                    sd.date,
                    sd.close_price,
                    sd.eps,
                    sd.per,
                    sd.roe,
                    sd.der,
                    sd.fcf,
                    sd.ma50,
                    sd.ma200,
                    sd.rsi,
                    sd.volume

                FROM fuzzy_output fo

                INNER JOIN stock_data sd
                    ON fo.stockdata_id = sd.stockdata_id

                INNER JOIN stock_lq45 s
                    ON sd.id_stock = s.id_stock

                WHERE s.ticker = %s
            """

            params = [ticker]

            if tanggal:
                query += """
                    AND sd.date = %s
                """
                params.append(tanggal)

            query += """
                ORDER BY
                    sd.date DESC,
                    fo.output_id DESC

                LIMIT 1
            """

            cursor.execute(query, tuple(params))

            return cursor.fetchone()

        finally:
            cursor.close()
            conn.close()


    # ============================================================
    # TANGGAL TERBARU KHUSUS TICKER
    # ============================================================

    @staticmethod
    def get_latest_date_by_ticker(ticker):

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    MAX(sd.date) AS tanggal

                FROM fuzzy_output fo

                INNER JOIN stock_data sd
                    ON fo.stockdata_id = sd.stockdata_id

                INNER JOIN stock_lq45 s
                    ON sd.id_stock = s.id_stock

                WHERE s.ticker = %s
            """, (ticker,))

            result = cursor.fetchone()

            if result and result["tanggal"]:
                return result["tanggal"]

            return None

        finally:
            cursor.close()
            conn.close()


    # ============================================================
    # MEMBERSHIP
    #
    # PENTING:
    # Membership diambil berdasarkan stockdata_id yang sama
    # dengan fuzzy_output.
    # ============================================================

    @staticmethod
    def get_membership_by_ticker(ticker, tanggal=None):

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            query = """
                SELECT
                    fm.id_fuzzymembership,
                    fm.stockdata_id,

                    fm.eps_level,
                    fm.per_level,
                    fm.roe_level,
                    fm.der_level,
                    fm.fcf_level,
                    fm.trend_ma50,
                    fm.trend_ma200,
                    fm.gradient_level,
                    fm.rsi_level,
                    fm.volume_level,
                    fm.sentimen_level

                FROM fuzzy_membership fm

                INNER JOIN fuzzy_output fo
                    ON fo.stockdata_id = fm.stockdata_id

                INNER JOIN stock_data sd
                    ON sd.stockdata_id = fo.stockdata_id

                INNER JOIN stock_lq45 s
                    ON s.id_stock = sd.id_stock

                WHERE s.ticker = %s
            """

            params = [ticker]

            if tanggal:
                query += """
                    AND sd.date = %s
                """
                params.append(tanggal)

            query += """
                ORDER BY fm.id_fuzzymembership DESC
                LIMIT 1
            """

            cursor.execute(query, tuple(params))

            result = cursor.fetchone()

            print("================================")
            print("MEMBERSHIP DEBUG")
            print("ticker       :", ticker)
            print("tanggal      :", tanggal)
            print("membership   :", result)
            print("================================")

            return result

        finally:
            cursor.close()
            conn.close()
        #
    # Mengambil berita berdasarkan ticker DAN tanggal analisis.
    # Jadi kalau ranking tanggal 04 Sep, berita mengikuti
    # sekitar tanggal tersebut.
    # ============================================================

    @staticmethod
    def get_recent_news(ticker, tanggal=None):

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            if tanggal:

                cursor.execute("""
                    SELECT
                        date,
                        ticker,
                        judul,
                        link,
                        sentiment

                    FROM sentiment_emiten_detail

                    WHERE ticker = %s
                      AND date BETWEEN
                          DATE_SUB(%s, INTERVAL 6 DAY)
                          AND %s

                    ORDER BY
                        date DESC

                """, (
                    ticker,
                    tanggal,
                    tanggal
                ))

            else:

                cursor.execute("""
                    SELECT
                        date,
                        ticker,
                        judul,
                        link,
                        sentiment

                    FROM sentiment_emiten_detail

                    WHERE ticker = %s
                      AND date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)

                    ORDER BY
                        date DESC

                """, (ticker,))

            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()