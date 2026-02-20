import os

class Config:
    SECRET_KEY = "super-secret"

    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
