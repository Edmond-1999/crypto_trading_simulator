import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


class Config:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        db_user = os.getenv("DB_USER", "postgres")
        db_password = quote_plus(os.getenv("DB_PASSWORD", "postgres"))
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "crypto_trading")
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-key-change-in-production-2026",
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=3)
