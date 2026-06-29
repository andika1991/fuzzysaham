from db import get_db


class News:

    @staticmethod
    def get_all_news():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                detail_id,
                ticker,
                judul,
                link,
                sentiment,
                date
            FROM sentiment_emiten_detail
            ORDER BY date DESC
        """)

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results