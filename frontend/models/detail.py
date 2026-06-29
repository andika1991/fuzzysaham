from db import get_db

class StockDetail:

    @staticmethod
    def get_detail_by_ticker(ticker, tanggal=None):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                fo.output_id,
                fo.fuzzy_score,
                fo.kategori,
                fo.horizon,
                fo.created_at,
                fo.insight,

                s.ticker,
                s.nama_perusahaan,

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
            JOIN stock_data sd
                ON fo.stockdata_id = sd.stockdata_id
            JOIN stock_lq45 s
                ON sd.id_stock = s.id_stock
            WHERE s.ticker = %s
        """

        params = [ticker]

        if tanggal:
            query += " AND DATE(fo.created_at) = %s"
            params.append(tanggal)

        query += """
            ORDER BY fo.created_at DESC
            LIMIT 1
        """

        cursor.execute(query, tuple(params))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result

    @staticmethod
    def get_recent_news(ticker):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM sentiment_emiten_detail
            WHERE ticker = %s
              AND date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ORDER BY date DESC
        """, (ticker,))

        news = cursor.fetchall()

        cursor.close()
        conn.close()

        return news

    @staticmethod
    def get_membership_by_ticker(ticker, tanggal=None):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                fm.*
            FROM fuzzy_membership fm
            JOIN fuzzy_output fo
                ON fm.stockdata_id = fo.stockdata_id
            JOIN stock_data sd
                ON fo.stockdata_id = sd.stockdata_id
            JOIN stock_lq45 s
                ON sd.id_stock = s.id_stock
            WHERE s.ticker = %s
        """

        params = [ticker]

        if tanggal:
            query += " AND DATE(fo.created_at) = %s"
            params.append(tanggal)

        query += """
            ORDER BY fo.created_at DESC
            LIMIT 1
        """

        cursor.execute(query, tuple(params))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return result