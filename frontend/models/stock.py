from db import get_db

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