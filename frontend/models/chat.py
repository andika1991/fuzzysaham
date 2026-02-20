from db import get_db
from datetime import datetime

class Conversation:

    @staticmethod
    def create(user_id):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO conversation (user_id, started_at, last_update) VALUES (%s, %s, %s)",
            (user_id, datetime.now(), datetime.now())
        )

        conn.commit()
        conversation_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return conversation_id


    @staticmethod
    def get_latest(user_id):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM conversation
            WHERE user_id = %s
            ORDER BY conversation_id DESC
            LIMIT 1
        """, (user_id,))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return result

    @staticmethod
    def get_all_by_user(user_id):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT conversation_id, started_at, last_update
        FROM conversation
        WHERE user_id = %s
        ORDER BY conversation_id DESC
        """, (user_id,))

        result = cursor.fetchall()
        cursor.close()
        conn.close()

        return result
    
    @staticmethod
    def delete(conversation_id, user_id):
        conn = get_db()
        cursor = conn.cursor()

        # pastikan conversation milik user
        cursor.execute("""
            SELECT conversation_id 
            FROM conversation 
            WHERE conversation_id=%s AND user_id=%s
        """, (conversation_id, user_id))

        convo = cursor.fetchone()

        if convo:
            # hapus chat dulu
            cursor.execute("""
                DELETE FROM chat_messages
                WHERE conversation_id=%s
            """, (conversation_id,))

            # hapus conversation
            cursor.execute("""
                DELETE FROM conversation
                WHERE conversation_id=%s
            """, (conversation_id,))

            conn.commit()

        cursor.close()
        conn.close()



class ChatMessage:

    @staticmethod
    def save(conversation_id, sender, message):
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO chat_messages (conversation_id, sender, message_text, created_at)
            VALUES (%s, %s, %s, %s)
        """, (conversation_id, sender, message, datetime.now()))

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_by_conversation(conversation_id):
         conn = get_db()
         cursor = conn.cursor(dictionary=True)

         cursor.execute("""
        SELECT sender, message_text, created_at
        FROM chat_messages
        WHERE conversation_id = %s
        ORDER BY id_chatmessages ASC
         """, (conversation_id,))

         result = cursor.fetchall()
         cursor.close()
         conn.close()

         return result

    
    