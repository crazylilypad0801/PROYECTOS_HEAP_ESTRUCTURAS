"""
ARCHIVO: src/motor_lento.py
PROPÓSITO:
    Versión de referencia intencionalmente simple implementada únicamente con
    listas lineales de Python (list). Sus operaciones son lentas asintóticamente
    (O(n) / O(n log n) y Dijkstra O(V^2 + V*E)), pero muy fáciles de revisar
    a mano. Sirve como oráculo en las pruebas diferenciales aleatorias para
    garantizar que MotorMisiones responde exactamente igual en todo escenario.
"""

from typing import List, Tuple

from .mision import (
    URGENCIA_MAX,
    URGENCIA_MIN,
    EstadoMision,
    Mision,
    ResultadoBusqueda,
    ResultadoOperacion,
    ResultadoRuta,
    ResultadoSiguiente,
    ResultadoTopK,
    TipoMision,
    clave_orden_prioridad,
    copiar_mision,
    tiene_mayor_prioridad,
)


class MotorMisionesLento:
    """
    Implementación lineal de referencia del Motor de Misiones.
    """

    def __init__(self) -> None:
        self._misiones: List[Mision] = []
        self._ubicaciones: List[str] = []
        # Lista plana de aristas (idx_origen, idx_destino, peso).
        self._aristas: List[Tuple[int, int, int]] = []
        self._contador_llegada: int = 0

    def _buscar_indice_ubicacion(self, nombre: str) -> int:
        for i, lugar in enumerate(self._ubicaciones):
            if lugar == nombre:
                return i
        return -1

    def _buscar_indice_mision(self, id_mision: str) -> int:
        for i, mision in enumerate(self._misiones):
            if mision.id == id_mision:
                return i
        return -1

    def agregar_ubicacion(self, nombre: str) -> bool:
        if not isinstance(nombre, str) or not nombre or self._buscar_indice_ubicacion(nombre) != -1:
            return False
        self._ubicaciones.append(nombre)
        return True

    def agregar_camino(
        self,
        origen: str,
        destino: str,
        peso: int,
        bidireccional: bool = True,
    ) -> bool:
        if isinstance(peso, bool) or not isinstance(peso, int) or peso < 0:
            return False
        u = self._buscar_indice_ubicacion(origen)
        v = self._buscar_indice_ubicacion(destino)
        if u == -1 or v == -1:
            return False
        self._aristas.append((u, v, peso))
        if bidireccional and u != v:
            self._aristas.append((v, u, peso))
        return True

    def total_misiones(self) -> int:
        return len(self._misiones)

    def total_pendientes(self) -> int:
        return sum(1 for m in self._misiones if m.estado == EstadoMision.PENDIENTE)

    def registrar_mision(
        self,
        id_mision: str,
        nombre: str,
        tipo: TipoMision,
        urgencia: int,
        ubicacion: str,
    ) -> ResultadoOperacion:
        if not id_mision or not nombre or not ubicacion:
            return ResultadoOperacion(False, "El ID, el nombre y la ubicación no pueden estar vacíos.")
        if isinstance(urgencia, bool) or not isinstance(urgencia, int):
            return ResultadoOperacion(False, "La urgencia debe ser un número entero.")
        if urgencia < URGENCIA_MIN or urgencia > URGENCIA_MAX:
            return ResultadoOperacion(False, "La urgencia debe estar entre 1 y 10.")
        if not isinstance(tipo, TipoMision):
            return ResultadoOperacion(False, "El tipo de misión no es válido.")
        if self._buscar_indice_ubicacion(ubicacion) == -1:
            return ResultadoOperacion(False, f"La ubicación '{ubicacion}' no existe en el mapa.")
        if self._buscar_indice_mision(id_mision) != -1:
            return ResultadoOperacion(False, f"Ya existe una misión registrada con el ID '{id_mision}'.")

        self._contador_llegada += 1
        self._misiones.append(
            Mision(
                id=id_mision,
                nombre=nombre,
                tipo=tipo,
                urgencia=urgencia,
                ubicacion=ubicacion,
                estado=EstadoMision.PENDIENTE,
                orden_llegada=self._contador_llegada,
            )
        )
        return ResultadoOperacion(True, f"Misión '{id_mision}' registrada como pendiente.")

    def buscar_mision(self, id_mision: str) -> ResultadoBusqueda:
        if not id_mision:
            return ResultadoBusqueda(False, None, "El ID de búsqueda está vacío.")
        idx = self._buscar_indice_mision(id_mision)
        if idx == -1:
            return ResultadoBusqueda(False, None, f"No existe ninguna misión con el ID '{id_mision}'.")
        return ResultadoBusqueda(True, copiar_mision(self._misiones[idx]), "Misión encontrada.")

    def cambiar_urgencia(self, id_mision: str, nueva_urgencia: int) -> ResultadoOperacion:
        if isinstance(nueva_urgencia, bool) or not isinstance(nueva_urgencia, int):
            return ResultadoOperacion(False, "La nueva urgencia debe ser un número entero.")
        if nueva_urgencia < URGENCIA_MIN or nueva_urgencia > URGENCIA_MAX:
            return ResultadoOperacion(False, "La nueva urgencia debe estar entre 1 y 10.")
        idx = self._buscar_indice_mision(id_mision)
        if idx == -1:
            return ResultadoOperacion(False, f"No existe ninguna misión con el ID '{id_mision}'.")
        if self._misiones[idx].estado != EstadoMision.PENDIENTE:
            return ResultadoOperacion(False, "Solo se puede cambiar la urgencia de misiones pendientes.")

        self._misiones[idx].urgencia = nueva_urgencia
        return ResultadoOperacion(True, "Urgencia actualizada.")

    def cancelar_mision(self, id_mision: str) -> ResultadoOperacion:
        idx = self._buscar_indice_mision(id_mision)
        if idx == -1:
            return ResultadoOperacion(False, f"No existe ninguna misión con el ID '{id_mision}'.")
        if self._misiones[idx].estado != EstadoMision.PENDIENTE:
            return ResultadoOperacion(False, "Solo se pueden cancelar misiones que estén pendientes.")

        self._misiones[idx].estado = EstadoMision.CANCELADA
        return ResultadoOperacion(True, "Misión cancelada.")

    def obtener_siguiente_mision(self) -> ResultadoSiguiente:
        mejor_idx = -1
        for i, mision in enumerate(self._misiones):
            if mision.estado == EstadoMision.PENDIENTE:
                if mejor_idx == -1 or tiene_mayor_prioridad(mision, self._misiones[mejor_idx]):
                    mejor_idx = i

        if mejor_idx == -1:
            return ResultadoSiguiente(False, None, "No hay misiones pendientes disponibles.")

        self._misiones[mejor_idx].estado = EstadoMision.EN_CURSO
        return ResultadoSiguiente(
            True, copiar_mision(self._misiones[mejor_idx]), "Misión asignada."
        )

    def consultar_primeras_k(self, k: int) -> ResultadoTopK:
        if isinstance(k, bool) or not isinstance(k, int):
            return ResultadoTopK(False, [], "El parámetro k debe ser un número entero.")
        if k < 0:
            return ResultadoTopK(False, [], "El parámetro k no puede ser negativo.")

        pendientes = [
            copiar_mision(m) for m in self._misiones if m.estado == EstadoMision.PENDIENTE
        ]
        pendientes.sort(key=clave_orden_prioridad)
        return ResultadoTopK(True, pendientes[:k], "Consulta completada.")

    def calcular_ruta_a_mision(self, ubicacion_jugador: str, id_mision: str) -> ResultadoRuta:
        idx_m = self._buscar_indice_mision(id_mision)
        if idx_m == -1:
            return ResultadoRuta(False, [], 0, "Misión no encontrada.")
        if self._misiones[idx_m].estado == EstadoMision.CANCELADA:
            return ResultadoRuta(False, [], 0, "La misión fue cancelada.")

        origen = self._buscar_indice_ubicacion(ubicacion_jugador)
        destino = self._buscar_indice_ubicacion(self._misiones[idx_m].ubicacion)
        if origen == -1 or destino == -1:
            return ResultadoRuta(False, [], 0, "Ubicación inexistente.")
        if origen == destino:
            return ResultadoRuta(True, [ubicacion_jugador], 0, "Misma ubicación.")

        v = len(self._ubicaciones)
        inf = float("inf")
        dist: List[float] = [inf] * v
        padre: List[int] = [-1] * v
        visitado: List[bool] = [False] * v
        dist[origen] = 0

        # Dijkstra clásico O(V^2 + V*E) buscando el mínimo linealmente en cada paso.
        for _ in range(v):
            u = -1
            for i in range(v):
                if not visitado[i] and dist[i] != inf and (u == -1 or dist[i] < dist[u]):
                    u = i
            if u == -1:
                break
            visitado[u] = True

            for ar_u, ar_v, peso in self._aristas:
                if ar_u == u:
                    nueva_dist = dist[u] + peso
                    if nueva_dist < dist[ar_v]:
                        dist[ar_v] = nueva_dist
                        padre[ar_v] = u

        if dist[destino] == inf:
            return ResultadoRuta(False, [], 0, "No existe camino.")

        camino: List[str] = []
        actual = destino
        while actual != -1:
            camino.append(self._ubicaciones[actual])
            actual = padre[actual]
        camino.reverse()

        return ResultadoRuta(True, camino, int(dist[destino]), "Ruta encontrada.")
