from db import get_db

class StockDetail:

    @staticmethod
    def get_detail_by_ticker(ticker):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # 🔥 Ambil stockdata terakhir berdasarkan ticker
        cursor.execute("""
            SELECT 
                fo.output_id,
                fo.fuzzy_score,
                fo.kategori,
                fo.horizon,
                fo.insight,
                fo.created_at,
                sd.*,
                s.nama_perusahaan,
                s.ticker,
                s.sektor
            FROM fuzzy_output fo
            JOIN stock_data sd 
                ON fo.stockdata_id = sd.stockdata_id
            JOIN stock_lq45 s 
                ON sd.id_stock = s.id_stock
            WHERE s.ticker = %s
            ORDER BY fo.created_at DESC
            LIMIT 1
        """, (ticker,))

        detail = cursor.fetchone()

        if not detail:
            cursor.close()
            conn.close()
            return None, None

        stockdata_id = detail["stockdata_id"]

        # 🔥 Ambil fuzzy membership
        cursor.execute("""
            SELECT *
            FROM fuzzy_membership
            WHERE stockdata_id = %s
        """, (stockdata_id,))

        membership = cursor.fetchall()

        cursor.close()
        conn.close()

        return detail, membership
    
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
