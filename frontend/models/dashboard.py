from db import get_db




class DashboardModel:

    @staticmethod
    def get_total_saham():
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT COUNT(*) AS total
            FROM stock_lq45
        """)

        result = cur.fetchone()

        cur.close()
        conn.close()

        return result["total"]
    
    @staticmethod
    def get_last_update():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT MAX(created_at) AS last_update
            FROM fuzzy_output
        """)

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return row["last_update"]
    
    @staticmethod
    def get_total_rekomendasi():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT COUNT(*) AS total_rekomendasi
        FROM fuzzy_output
        WHERE kategori = 'Potensial'
        AND DATE(created_at) = (
            SELECT DATE(MAX(created_at))
            FROM fuzzy_output
        )
    """)

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result["total_rekomendasi"]
    
    @staticmethod
    def toprank():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                l.ticker,
                f.fuzzy_score
            FROM fuzzy_output f
            JOIN stock_data sd
                ON sd.stockdata_id = f.stockdata_id
            JOIN stock_lq45 l
                ON l.id_stock = sd.id_stock
            WHERE f.kategori = 'Potensial'
            AND DATE(f.created_at) = (
                SELECT DATE(MAX(created_at))
                FROM fuzzy_output
            )
            ORDER BY f.fuzzy_score DESC
            LIMIT 1
        """)

        top_rank = cursor.fetchone()

        cursor.close()
        conn.close()

        return top_rank
    
    @staticmethod
    def get_top5_ranking():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                l.ticker,
                f.fuzzy_score,
                f.kategori,
                f.horizon
            FROM fuzzy_output f
            JOIN stock_data sd
                ON sd.stockdata_id = f.stockdata_id
            JOIN stock_lq45 l
                ON l.id_stock = sd.id_stock
            WHERE DATE(f.created_at) = (
                SELECT DATE(MAX(created_at))
                FROM fuzzy_output
            )
            AND f.kategori = 'Potensial'
            ORDER BY f.fuzzy_score DESC
            LIMIT 5
        """)

        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return result
    
    @staticmethod
    def get_top_gainer():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                l.ticker,
                ROUND(
                    ((t.close_price - y.close_price) / y.close_price) * 100,
                    2
                ) AS return_pct
            FROM stock_data t
            JOIN stock_data y
                ON t.id_stock = y.id_stock
            JOIN stock_lq45 l
                ON l.id_stock = t.id_stock
            WHERE t.date = (
                SELECT MAX(date)
                FROM stock_data
            )
            AND y.date = (
                SELECT MAX(date)
                FROM stock_data
                WHERE date < (
                    SELECT MAX(date)
                    FROM stock_data
                )
            )
            ORDER BY return_pct DESC
            LIMIT 3
        """)

        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return result


    @staticmethod
    def get_top_loser():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                l.ticker,
                ROUND(
                    ((t.close_price - y.close_price) / y.close_price) * 100,
                    2
                ) AS return_pct
            FROM stock_data t
            JOIN stock_data y
                ON t.id_stock = y.id_stock
            JOIN stock_lq45 l
                ON l.id_stock = t.id_stock
            WHERE t.date = (
                SELECT MAX(date)
                FROM stock_data
            )
            AND y.date = (
                SELECT MAX(date)
                FROM stock_data
                WHERE date < (
                    SELECT MAX(date)
                    FROM stock_data
                )
            )
            ORDER BY return_pct ASC
            LIMIT 3
        """)

        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return result