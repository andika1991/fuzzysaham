from db import get_db

class RuleModel:

    # 🔹 GET ALL
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM rule
            ORDER BY id_rule ASC
        """)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return data


    # 🔹 GET BY ID
    @staticmethod
    def get_by_id(id_rule):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM rule
            WHERE id_rule = %s
        """, (id_rule,))

        data = cursor.fetchone()

        cursor.close()
        conn.close()

        return data


    # 🔹 CREATE
    @staticmethod
    def create(data):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rule
            (eps, per, roe, der, fcf, ma50, ma200, gradien, volume, rsi, sentimen, output, horizon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('eps'),
            data.get('per'),
            data.get('roe'),
            data.get('der'),
            data.get('fcf'),
            data.get('ma50'),
            data.get('ma200'),
            data.get('gradien'),
            data.get('volume'),
            data.get('rsi'),
            data.get('sentimen'),
            data.get('output'),
            data.get('horizon')
        ))

        conn.commit()
        cursor.close()
        conn.close()


    # 🔹 UPDATE
    @staticmethod
    def update(id_rule, data):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rule
            SET eps=%s, per=%s, roe=%s, der=%s, fcf=%s,
                ma50=%s, ma200=%s, gradien=%s, volume=%s, rsi=%s,
                sentimen=%s, output=%s, horizon=%s
            WHERE id_rule=%s
        """, (
            data.get('eps'),
            data.get('per'),
            data.get('roe'),
            data.get('der'),
            data.get('fcf'),
            data.get('ma50'),
            data.get('ma200'),
            data.get('gradien'),
            data.get('volume'),
            data.get('rsi'),
            data.get('sentimen'),
            data.get('output'),
            data.get('horizon'),
            id_rule
        ))

        conn.commit()
        cursor.close()
        conn.close()


    # 🔹 DELETE
    @staticmethod
    def delete(id_rule):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM rule
            WHERE id_rule = %s
        """, (id_rule,))

        conn.commit()
        cursor.close()
        conn.close()