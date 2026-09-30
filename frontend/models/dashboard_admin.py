from db import get_db

class DashboardAdm:

        @staticmethod
        def get_rule_count():
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM rule")
            count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return count