from db import get_db


class FuzzyOutput:

    @staticmethod
    def get_available_dates():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT DATE(created_at) AS tanggal
            FROM fuzzy_output
            ORDER BY tanggal DESC
        """)

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results


    @staticmethod
    def get_latest_date():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT MAX(DATE(created_at)) AS last_date
            FROM fuzzy_output
        """)

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result:
            return None

        return result["last_date"]


    @staticmethod
    def get_ranking_by_date(tanggal):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                fo.output_id,
                fo.fuzzy_score,
                fo.kategori,
                fo.horizon,
                fo.created_at,

                s.ticker,
                s.nama_perusahaan,

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
            JOIN stock_data sd 
                ON fo.stockdata_id = sd.stockdata_id
            JOIN stock_lq45 s 
                ON sd.id_stock = s.id_stock
            LEFT JOIN fuzzy_membership fm
                ON fo.stockdata_id = fm.stockdata_id
            WHERE DATE(fo.created_at) = %s
            ORDER BY fo.fuzzy_score DESC
        """

        cursor.execute(query, (tanggal,))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results


    @staticmethod
    def get_latest_ranking():
        last_date = FuzzyOutput.get_latest_date()

        if not last_date:
            return []

        return FuzzyOutput.get_ranking_by_date(last_date)