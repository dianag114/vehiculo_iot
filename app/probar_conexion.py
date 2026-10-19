
from app.db.connection import get_connection


def probar_conexion():
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE(), VERSION()")
            resultado = cursor.fetchone()
            cursor.close()

            print("¡Conexión con Amazon RDS exitosa!")
            print(f"Base de datos: {resultado[0]}")
            print(f"Versión de MySQL: {resultado[1]}")

    except Exception as error:
        print("No se pudo conectar con Amazon RDS.")
        print(f"Tipo de error: {type(error).__name__}")
        print(f"Detalle: {error}")


if __name__ == "__main__":
    probar_conexion()
