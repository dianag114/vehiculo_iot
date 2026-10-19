
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSocket"])


class AdministradorWebSocket:
    def __init__(self):
        self.conexiones = {}

    async def conectar(self, id_vehiculo: int, websocket: WebSocket):
        await websocket.accept()
        self.conexiones.setdefault(id_vehiculo, []).append(websocket)

    def desconectar(self, id_vehiculo: int, websocket: WebSocket):
        if id_vehiculo in self.conexiones:
            if websocket in self.conexiones[id_vehiculo]:
                self.conexiones[id_vehiculo].remove(websocket)

            if not self.conexiones[id_vehiculo]:
                del self.conexiones[id_vehiculo]

    async def enviar_a_vehiculo(self, id_vehiculo: int, mensaje: dict):
        conexiones = self.conexiones.get(id_vehiculo, []).copy()

        for conexion in conexiones:
            try:
                await conexion.send_json(mensaje)
            except Exception:
                self.desconectar(id_vehiculo, conexion)


administrador_ws = AdministradorWebSocket()


@router.websocket("/ws/{id_vehiculo}")
async def websocket_vehiculo(websocket: WebSocket, id_vehiculo: int):
    if id_vehiculo <= 0:
        await websocket.close(code=1008)
        return

    await administrador_ws.conectar(id_vehiculo, websocket)

    try:
        await websocket.send_json({
            "tipo": "conexion",
            "id_vehiculo": id_vehiculo,
            "mensaje": "WebSocket conectado correctamente"
        })

        while True:
            mensaje = await websocket.receive_json()

            await administrador_ws.enviar_a_vehiculo(
                id_vehiculo,
                {
                    "tipo": "evento",
                    "id_vehiculo": id_vehiculo,
                    "datos": mensaje
                }
            )

    except WebSocketDisconnect:
        pass

    finally:
        administrador_ws.desconectar(id_vehiculo, websocket)
