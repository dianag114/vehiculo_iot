from fastapi import FastAPI, HTTPException
from mysql.connector import Error

from app.db.connection import get_connection

app = FastAPI(
    title="API de Vehículos IoT",
    description=(
        "API REST local conectada a Amazon RDS "
        "con procedimientos almacenados y WebSocket."
    ),
    version="1.0.0"
)


@app.get("/", tags=["Sistema"])
def inicio():
    return {
        "mensaje": "API de Vehículos IoT funcionando",
        "entorno": "local",
        "documentacion": "/docs"
    }


@app.get("/health", tags=["Sistema"])
def health():
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            finally:
                cursor.close()

        return {
            "api": "disponible",
            "rds": "conectado",
            "base_datos": "vehiculo_iot"
        }

    except Error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible conectar con la base de datos"
        )