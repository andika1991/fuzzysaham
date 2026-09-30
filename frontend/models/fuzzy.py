from db import get_db


class FuzzyOutput:

    # ============================================================
    # TANGGAL YANG TERSEDIA
    # Berdasarkan tanggal data saham
    # ============================================================

    @staticmethod
    def get_available_dates():

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT DISTINCT
                    sd.date AS tanggal

                FROM fuzzy_output fo

                INNER JOIN stock_data sd
                    ON fo.stockdata_id = sd.stockdata_id

                WHERE sd.date IS NOT NULL

                ORDER BY sd.date DESC
            """)

            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()


    # ============================================================
    # TANGGAL TERBARU
    # ============================================================

    @staticmethod
    def get_latest_date():

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    MAX(sd.date) AS last_date

                FROM fuzzy_output fo

                INNER JOIN stock_data sd
                    ON fo.stockdata_id = sd.stockdata_id

                WHERE sd.date IS NOT NULL
            """)

            result = cursor.fetchone()

            if result and result["last_date"]:
                return result["last_date"]

            return None

        finally:
            cursor.close()
            conn.close()


    # ============================================================
    # RANKING BERDASARKAN TANGGAL
    #
    # 1 fuzzy_output = 1 saham
    # fuzzy_membership yang double hanya diambil 1
    # ============================================================

    @staticmethod
    def get_ranking_by_date(tanggal):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            query = """
                SELECT
                    fo.output_id,
                    fo.fuzzy_score,
                    fo.kategori,
                    fo.horizon,
                    fo.created_at,

                    s.ticker,
                    s.nama_perusahaan,

                    sd.date,
                    sd.close_price,

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

                FROM fuzzy_output fo

                INNER JOIN stock_data sd
                    ON fo.stockdata_id = sd.stockdata_id

                INNER JOIN stock_lq45 s
                    ON sd.id_stock = s.id_stock

                LEFT JOIN fuzzy_membership fm
                    ON fm.id_fuzzymembership = (
                        SELECT MAX(fm2.id_fuzzymembership)
                        FROM fuzzy_membership fm2
                        WHERE fm2.stockdata_id = fo.stockdata_id
                    )

                WHERE sd.date = %s

                ORDER BY fo.fuzzy_score DESC
            """

            cursor.execute(query, (tanggal,))
            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()


    # ============================================================
    # RANKING TERBARU
    # ============================================================

    @staticmethod
    def get_latest_ranking():

        last_date = FuzzyOutput.get_latest_date()

        if not last_date:
            return []

        return FuzzyOutput.get_ranking_by_date(
            last_date
        )