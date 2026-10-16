from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

from app.core.config import settings


@contextmanager
def get_connection():
    connection = None

    try:
        connection = mysql.connector.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connection_timeout=10
        )

        yield connection

    except Error:
        raise

    finally:
        if connection is not None and connection.is_connected():
            connection.close()