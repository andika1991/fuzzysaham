from db import get_db

class FuzzyOutput:

    @staticmethod
    def get_latest_ranking():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # 🔥 Ambil tanggal terakhir dulu
        cursor.execute("""
            SELECT MAX(DATE(created_at)) AS last_date
            FROM fuzzy_output
        """)
        result = cursor.fetchone()

        if not result or not result["last_date"]:
            cursor.close()
            conn.close()
            return []

        last_date = result["last_date"]

        # 🔥 Ambil ranking berdasarkan tanggal terakhir
        query = """
            SELECT 
                fo.output_id,
                fo.fuzzy_score,
                fo.kategori,
                fo.horizon,
                fo.created_at,
                s.ticker,
                s.nama_perusahaan,
                sd.close_price
            FROM fuzzy_output fo
            JOIN stock_data sd 
                ON fo.stockdata_id = sd.stockdata_id
            JOIN stock_lq45 s 
                ON sd.id_stock = s.id_stock
            WHERE DATE(fo.created_at) = %s
            ORDER BY fo.fuzzy_score DESC
        """

        cursor.execute(query, (last_date,))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results
