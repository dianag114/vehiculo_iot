from typing import Optional

import mysql.connector
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.connection import get_connection


router = APIRouter(prefix="/api", tags=["Vehículo IoT"])


# =========================================================
# FUNCION GENERAL PARA EJECUTAR PROCEDIMIENTOS ALMACENADOS
# =========================================================

def ejecutar_sp(nombre: str, parametros: tuple = ()) -> list:
    conexion = None
    cursor = None

    try:
        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True)

        cursor.callproc(nombre, parametros)

        filas = []

        for resultado in cursor.stored_results():
            filas.extend(resultado.fetchall())
            resultado.close()

        conexion.commit()
        return filas

    except mysql.connector.Error as error:
        if conexion is not None:
            conexion.rollback()

        # Errores de claves duplicadas o relaciones entre tablas
        if error.errno in (1062, 1451, 1452):
            raise HTTPException(
                status_code=409,
                detail="La operación entra en conflicto con los datos "
                       "o las relaciones de la base de datos."
            ) from error

        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar {nombre}: {error}"
        ) from error

    except Exception as error:
        if conexion is not None:
            conexion.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error interno al ejecutar {nombre}."
        ) from error

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None:
            conexion.close()


def obtener_uno(nombre: str, parametros: tuple = ()):
    filas = ejecutar_sp(nombre, parametros)

    if not filas:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el registro solicitado."
        )

    return filas[0]


def respuesta_operacion(mensaje: str, filas: list = None):
    respuesta = {"mensaje": mensaje}

    if filas:
        respuesta["resultado"] = filas[0]

    return respuesta


# =========================================================
# MODELOS DE DATOS
# =========================================================

class VehiculoCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    modelo: Optional[str] = Field(default=None, max_length=80)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    microcontrolador: Optional[str] = Field(default=None, max_length=50)


class VehiculoActualizar(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    modelo: Optional[str] = Field(default=None, max_length=80)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    microcontrolador: Optional[str] = Field(default=None, max_length=50)
    activo: bool = True


class ComandoCrear(BaseModel):
    id_vehiculo: int = Field(gt=0)
    nombre: str = Field(min_length=1, max_length=60)
    codigo: int = Field(ge=0)
    descripcion: Optional[str] = Field(default=None, max_length=255)


class ComandoActualizar(BaseModel):
    nombre: str = Field(min_length=1, max_length=60)
    codigo: int = Field(ge=0)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    activo: bool = True


class EstadoActualizar(BaseModel):
    id_comando: Optional[int] = Field(default=None, gt=0)
    conectado: bool


class HistorialCrear(BaseModel):
    id_vehiculo: int = Field(gt=0)
    id_comando: Optional[int] = Field(default=None, gt=0)
    origen: str = Field(default="MANUAL", min_length=1, max_length=30)


class DemoCrear(BaseModel):
    id_vehiculo: int = Field(gt=0)
    nombre: str = Field(min_length=1, max_length=80)
    descripcion: Optional[str] = Field(default=None, max_length=255)


class DemoActualizar(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    activo: bool = True


class MovimientoDemoCrear(BaseModel):
    id_comando: int = Field(gt=0)
    orden: int = Field(gt=0)
    duracion_ms: int = Field(ge=0)
    pausa_ms: int = Field(default=0, ge=0)


class MovimientoDemoActualizar(BaseModel):
    id_comando: int = Field(gt=0)
    orden: int = Field(gt=0)
    duracion_ms: int = Field(ge=0)
    pausa_ms: int = Field(default=0, ge=0)


# =========================================================
# VEHICULOS
# =========================================================

@router.get("/vehiculos")
def listar_vehiculos():
    return ejecutar_sp("sp_obtener_vehiculos")


@router.get("/vehiculos/{id_vehiculo}")
def consultar_vehiculo(id_vehiculo: int):
    return obtener_uno("sp_obtener_vehiculo", (id_vehiculo,))


@router.post("/vehiculos", status_code=201)
def crear_vehiculo(datos: VehiculoCrear):
    filas = ejecutar_sp(
        "sp_crear_vehiculo",
        (
            datos.nombre,
            datos.modelo,
            datos.descripcion,
            datos.microcontrolador,
        ),
    )

    return respuesta_operacion("Vehículo registrado.", filas)


@router.put("/vehiculos/{id_vehiculo}")
def actualizar_vehiculo(id_vehiculo: int, datos: VehiculoActualizar):
    ejecutar_sp(
        "sp_actualizar_vehiculo",
        (
            id_vehiculo,
            datos.nombre,
            datos.modelo,
            datos.descripcion,
            datos.microcontrolador,
            datos.activo,
        ),
    )

    return {"mensaje": "Procedimiento de actualización ejecutado."}


@router.delete("/vehiculos/{id_vehiculo}")
def eliminar_vehiculo(id_vehiculo: int):
    ejecutar_sp("sp_eliminar_vehiculo", (id_vehiculo,))

    return {"mensaje": "Procedimiento de eliminación ejecutado."}


# =========================================================
# COMANDOS
# =========================================================

@router.get("/vehiculos/{id_vehiculo}/comandos")
def listar_comandos(id_vehiculo: int):
    return ejecutar_sp("sp_obtener_comandos_vehiculo", (id_vehiculo,))


@router.post("/comandos", status_code=201)
def crear_comando(datos: ComandoCrear):
    filas = ejecutar_sp(
        "sp_crear_comando",
        (
            datos.id_vehiculo,
            datos.nombre,
            datos.codigo,
            datos.descripcion,
        ),
    )

    return respuesta_operacion("Comando registrado.", filas)


@router.put("/comandos/{id_comando}")
def actualizar_comando(id_comando: int, datos: ComandoActualizar):
    ejecutar_sp(
        "sp_actualizar_comando",
        (
            id_comando,
            datos.nombre,
            datos.codigo,
            datos.descripcion,
            datos.activo,
        ),
    )

    return {"mensaje": "Procedimiento de actualización ejecutado."}


@router.delete("/comandos/{id_comando}")
def eliminar_comando(id_comando: int):
    ejecutar_sp("sp_eliminar_comando", (id_comando,))

    return {"mensaje": "Procedimiento de eliminación ejecutado."}


# =========================================================
# ESTADO DEL VEHICULO
# =========================================================

@router.get("/vehiculos/{id_vehiculo}/estado")
def consultar_estado(id_vehiculo: int):
    return obtener_uno("sp_obtener_estado", (id_vehiculo,))


@router.put("/vehiculos/{id_vehiculo}/estado")
def actualizar_estado(id_vehiculo: int, datos: EstadoActualizar):
    ejecutar_sp(
        "sp_actualizar_estado",
        (
            id_vehiculo,
            datos.id_comando,
            datos.conectado,
        ),
    )

    return {"mensaje": "Estado del vehículo actualizado."}


# =========================================================
# HISTORIAL DE COMANDOS
# =========================================================

@router.get("/vehiculos/{id_vehiculo}/historial")
def consultar_historial(
    id_vehiculo: int,
    limite: int = Query(default=10, ge=1, le=10),
):
    filas = ejecutar_sp("sp_obtener_historial", (id_vehiculo,))

    # El procedimiento ya ordena el historial del más reciente
    # al más antiguo. La API devuelve como máximo diez registros.
    return filas[:limite]


@router.post("/historial", status_code=201)
def registrar_historial(datos: HistorialCrear):
    ejecutar_sp(
        "sp_registrar_historial",
        (
            datos.id_vehiculo,
            datos.id_comando,
            datos.origen,
        ),
    )

    return {"mensaje": "Movimiento registrado en el historial."}


# =========================================================
# DEMOSTRACIONES
# =========================================================

@router.get("/vehiculos/{id_vehiculo}/demos")
def listar_demos(id_vehiculo: int):
    return ejecutar_sp("sp_obtener_demos", (id_vehiculo,))


@router.post("/demos", status_code=201)
def crear_demo(datos: DemoCrear):
    filas = ejecutar_sp(
        "sp_crear_demo",
        (
            datos.id_vehiculo,
            datos.nombre,
            datos.descripcion,
        ),
    )

    return respuesta_operacion("Demostración creada.", filas)


@router.put("/demos/{id_demo}")
def actualizar_demo(id_demo: int, datos: DemoActualizar):
    ejecutar_sp(
        "sp_actualizar_demo",
        (
            id_demo,
            datos.nombre,
            datos.descripcion,
            datos.activo,
        ),
    )

    return {"mensaje": "Procedimiento de actualización ejecutado."}


@router.delete("/demos/{id_demo}")
def eliminar_demo(id_demo: int):
    ejecutar_sp("sp_eliminar_demo", (id_demo,))

    return {"mensaje": "Procedimiento de eliminación ejecutado."}


# =========================================================
# MOVIMIENTOS DE UNA DEMOSTRACION
# =========================================================

@router.get("/demos/{id_demo}/movimientos")
def listar_movimientos_demo(id_demo: int):
    return ejecutar_sp("sp_obtener_movimientos_demo", (id_demo,))


@router.post("/demos/{id_demo}/movimientos", status_code=201)
def agregar_movimiento_demo(
    id_demo: int,
    datos: MovimientoDemoCrear,
):
    ejecutar_sp(
        "sp_agregar_movimiento_demo",
        (
            id_demo,
            datos.id_comando,
            datos.orden,
            datos.duracion_ms,
            datos.pausa_ms,
        ),
    )

    return {"mensaje": "Movimiento agregado a la demostración."}


@router.put("/movimientos-demo/{id_demo_movimiento}")
def actualizar_movimiento_demo(
    id_demo_movimiento: int,
    datos: MovimientoDemoActualizar,
):
    ejecutar_sp(
        "sp_actualizar_movimiento_demo",
        (
            id_demo_movimiento,
            datos.id_comando,
            datos.orden,
            datos.duracion_ms,
            datos.pausa_ms,
        ),
    )

    return {"mensaje": "Movimiento de demostración actualizado."}


@router.delete("/movimientos-demo/{id_demo_movimiento}")
def eliminar_movimiento_demo(id_demo_movimiento: int):
    ejecutar_sp(
        "sp_eliminar_movimiento_demo",
        (id_demo_movimiento,),
    )

    return {"mensaje": "Movimiento de demostración eliminado."}
