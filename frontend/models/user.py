from flask_login import UserMixin
from db import get_db


class User(UserMixin):

    def __init__(self, id, username, role):
        self.id = str(id)   # Flask-Login butuh string
        self.username = username
        self.role = role

    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return User(user["user_id"], user["username"], user["role"])
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    @staticmethod
    def create(username, password_hash):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user (username, password, role) VALUES (%s, %s, %s)",
            (username, password_hash, "user")
        )
        conn.commit()
        cursor.close()
        conn.close()
