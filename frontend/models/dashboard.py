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

        try:
            cursor.execute("""
                SELECT COUNT(*) AS total_rekomendasi
                FROM (
                    SELECT sd.id_stock
                    FROM fuzzy_output f
                    JOIN stock_data sd
                        ON sd.stockdata_id = f.stockdata_id
                    JOIN (
                        SELECT id_stock, MAX(DATE(date)) AS tanggal_terakhir
                        FROM stock_data
                        GROUP BY id_stock
                    ) latest
                        ON latest.id_stock = sd.id_stock
                        AND DATE(sd.date) = latest.tanggal_terakhir
                    JOIN (
                        SELECT stockdata_id, MAX(output_id) AS output_terakhir
                        FROM fuzzy_output
                        GROUP BY stockdata_id
                    ) fo_latest
                        ON fo_latest.stockdata_id = f.stockdata_id
                        AND fo_latest.output_terakhir = f.output_id
                    WHERE f.kategori = 'Potensial'
                    GROUP BY sd.id_stock
                ) AS rekomendasi
            """)

            result = cursor.fetchone()
            return result["total_rekomendasi"] or 0

        finally:
            cursor.close()
            conn.close()


    @staticmethod
    def toprank():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    l.ticker,
                    f.fuzzy_score,
                    f.kategori,
                    f.horizon,
                    sd.date AS tanggal
                FROM fuzzy_output f
                JOIN stock_data sd
                    ON sd.stockdata_id = f.stockdata_id
                JOIN stock_lq45 l
                    ON l.id_stock = sd.id_stock
                JOIN (
                    SELECT id_stock, MAX(DATE(date)) AS tanggal_terakhir
                    FROM stock_data
                    GROUP BY id_stock
                ) latest
                    ON latest.id_stock = sd.id_stock
                    AND DATE(sd.date) = latest.tanggal_terakhir
                JOIN (
                    SELECT stockdata_id, MAX(output_id) AS output_terakhir
                    FROM fuzzy_output
                    GROUP BY stockdata_id
                ) fo_latest
                    ON fo_latest.stockdata_id = f.stockdata_id
                    AND fo_latest.output_terakhir = f.output_id
                WHERE f.kategori = 'Potensial'
                ORDER BY f.fuzzy_score DESC
                LIMIT 1
            """)

            return cursor.fetchone()

        finally:
            cursor.close()
            conn.close()


    @staticmethod
    def get_top5_ranking():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    l.ticker,
                    f.fuzzy_score,
                    f.kategori,
                    f.horizon,
                    sd.date AS tanggal
                FROM fuzzy_output f
                JOIN stock_data sd
                    ON sd.stockdata_id = f.stockdata_id
                JOIN stock_lq45 l
                    ON l.id_stock = sd.id_stock
                JOIN (
                    SELECT id_stock, MAX(DATE(date)) AS tanggal_terakhir
                    FROM stock_data
                    GROUP BY id_stock
                ) latest
                    ON latest.id_stock = sd.id_stock
                    AND DATE(sd.date) = latest.tanggal_terakhir
                JOIN (
                    SELECT stockdata_id, MAX(output_id) AS output_terakhir
                    FROM fuzzy_output
                    GROUP BY stockdata_id
                ) fo_latest
                    ON fo_latest.stockdata_id = f.stockdata_id
                    AND fo_latest.output_terakhir = f.output_id
                WHERE f.kategori = 'Potensial'
                ORDER BY f.fuzzy_score DESC
                LIMIT 5
            """)

            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

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