from db import get_db
import pandas as pd

class StockModel:

    # 🔹 GET ALL DATA
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM stock_lq45
            ORDER BY id_stock ASC
        """)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return data


    # 🔹 GET BY ID
    @staticmethod
    def get_by_id(id_stock):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM stock_lq45
            WHERE id_stock = %s
        """, (id_stock,))

        data = cursor.fetchone()

        cursor.close()
        conn.close()

        return data


    # 🔹 CREATE (INSERT DATA)
    @staticmethod
    def create(data):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO stock_lq45 
            (ticker, nama_perusahaan, sektor, industri)
            VALUES (%s, %s, %s, %s)
        """, (
            data['ticker'],
            data['nama_perusahaan'],
            data['sektor'],
            data['industri']
        ))

        conn.commit()

        cursor.close()
        conn.close()


    # 🔹 UPDATE DATA
    @staticmethod
    def update(id_stock, data):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE stock_lq45
            SET ticker = %s,
                nama_perusahaan = %s,
                sektor = %s,
                industri = %s
            WHERE id_stock = %s
        """, (
            data['ticker'],
            data['nama_perusahaan'],
            data['sektor'],
            data['industri'],
            id_stock
        ))

        conn.commit()

        cursor.close()
        conn.close()


    # 🔹 DELETE DATA
    @staticmethod
    def delete(id_stock):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM stock_lq45
            WHERE id_stock = %s
        """, (id_stock,))

        conn.commit()

        cursor.close()
        conn.close()

    @staticmethod
    def get_stock_performance(id_stock):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                date,
                close_price
            FROM stock_data
            WHERE id_stock=%s
            ORDER BY date DESC
        """, (id_stock,))

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if not rows:
            return {}

        df = pd.DataFrame(rows)

        df["date"] = pd.to_datetime(df["date"])

        latest_price = df.iloc[0]["close_price"]
        latest_date = df.iloc[0]["date"]

        def calc_by_offset(offset):
            if len(df) <= offset:
                return None

            old_price = df.iloc[offset]["close_price"]

            return round(
                ((latest_price - old_price) / old_price) * 100,
                2
            )

        performance = {
            "week": calc_by_offset(5),
            "month": calc_by_offset(21),
            "quarter": calc_by_offset(63),
            "half": calc_by_offset(126),
            "ytd": None,
            "three_year": None
        }

        # ===========================
        # YTD
        # ===========================
        current_year = latest_date.year

        ytd = df[df["date"].dt.year == current_year]

        if len(ytd):

            first_price = ytd.iloc[-1]["close_price"]

            performance["ytd"] = round(
                ((latest_price - first_price) / first_price) * 100,
                2
            )

        # ===========================
        # 3 Tahun
        # ===========================
        target_date = latest_date - pd.DateOffset(years=3)

        old = df[df["date"] <= target_date]

        if len(old):

            price = old.iloc[0]["close_price"]

            performance["three_year"] = round(
                ((latest_price - price) / price) * 100,
                2
            )

        return performance