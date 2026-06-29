from db import get_db


class News:

    @staticmethod
    def get_all_news(tanggal=None):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                ticker,
                judul,
                link,
                sentiment,
                date
            FROM sentiment_emiten_detail
            WHERE DATE(date) = %s
            ORDER BY date DESC
        """

        cursor.execute(query, (tanggal,))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results


    @staticmethod
    def get_available_dates():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT DATE(date) AS tanggal
            FROM sentiment_emiten_detail
            ORDER BY tanggal DESC
        """)

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results


    @staticmethod
    def get_sentiment_summary(tanggal):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                sentiment,
                COUNT(*) AS total
            FROM sentiment_emiten_detail
            WHERE DATE(date) = %s
            GROUP BY sentiment
        """, (tanggal,))

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        summary = {
            "positif": 0,
            "netral": 0,
            "negatif": 0
        }

        for row in rows:
            sentiment = (row["sentiment"] or "netral").lower()

            if sentiment in summary:
                summary[sentiment] = row["total"]

        return summary