"""
ARCHIVO: src/motor_misiones.py
PROPÓSITO:
    Coordina las tres estructuras propias de tres familias distintas para
    conformar el motor completo de misiones de un videojuego:
      1. TablaHash (Hashing): almacenamiento maestro de misiones por ID (O(1) esperado).
      2. HeapMisiones (Árboles): Max-Heap indexado solo para misiones PENDIENTE (O(log n)).
      3. GrafoCiudad (Grafos): mapa ponderado de la ciudad con Dijkstra (O((V+E) log V)).

    Implementa las 7 operaciones especificadas manteniendo sincronizadas las
    estructuras internas en cada cambio de estado o urgencia.
"""

from .grafo_ciudad import GrafoCiudad
from .heap_misiones import HeapMisiones
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
    copiar_mision,
    misiones_son_iguales,
)
from .tabla_hash import TablaHash


class MotorMisiones:
    """
    Motor principal encargado de almacenar misiones, decidir cuál atender
    primero según prioridad y calcular la ruta óptima en el mapa de la ciudad.
    """

    def __init__(self) -> None:
        self._misiones: TablaHash[str, Mision] = TablaHash()
        self._cola_prioridad: HeapMisiones = HeapMisiones()
        self._mapa: GrafoCiudad = GrafoCiudad()
        self._contador_llegada: int = 0  # Reloj lógico para desempates FIFO.

    # ---------------- Métodos de configuración del mapa y conteos ----------------

    def agregar_ubicacion(self, nombre: str) -> bool:
        """Agrega una nueva ubicación al grafo de la ciudad."""
        return self._mapa.agregar_ubicacion(nombre)

    def agregar_camino(
        self,
        origen: str,
        destino: str,
        peso: int,
        bidireccional: bool = True,
    ) -> bool:
        """Agrega un camino ponderado (>= 0) entre dos ubicaciones del mapa."""
        return self._mapa.agregar_camino(origen, destino, peso, bidireccional)

    def total_misiones(self) -> int:
        """Cantidad total de misiones registradas (pendientes, en curso y canceladas)."""
        return self._misiones.tamano()

    def total_pendientes(self) -> int:
        """Cantidad de misiones actualmente en espera dentro del heap."""
        return self._cola_prioridad.tamano()

    def obtener_mapa(self) -> GrafoCiudad:
        """Devuelve la referencia al grafo del mapa (para validaciones en pruebas)."""
        return self._mapa

    # ---------------- Las 7 operaciones principales del motor ----------------

    def registrar_mision(
        self,
        id_mision: str,
        nombre: str,
        tipo: TipoMision,
        urgencia: int,
        ubicacion: str,
    ) -> ResultadoOperacion:
        """
        Operación 1: Registrar misión.
        - Entradas: id, nombre, tipo (PRINCIPAL/SECUNDARIA), urgencia [1..10], ubicación.
        - Cambios: inserta la misión en estado PENDIENTE tanto en TablaHash como en
          HeapMisiones, asignándole un orden de llegada estrictamente creciente.
        - Casos borde: rechaza campos vacíos, urgencia fuera de [1..10], ubicación
          inexistente en el mapa o identificador ya registrado.
        """
        if not id_mision or not nombre or not ubicacion:
            return ResultadoOperacion(False, "El ID, el nombre y la ubicación no pueden estar vacíos.")
        if isinstance(urgencia, bool) or not isinstance(urgencia, int):
            return ResultadoOperacion(False, "La urgencia debe ser un número entero.")
        if urgencia < URGENCIA_MIN or urgencia > URGENCIA_MAX:
            return ResultadoOperacion(False, "La urgencia debe estar entre 1 y 10.")
        if not isinstance(tipo, TipoMision):
            return ResultadoOperacion(False, "El tipo de misión no es válido.")
        if not self._mapa.existe_ubicacion(ubicacion):
            return ResultadoOperacion(False, f"La ubicación '{ubicacion}' no existe en el mapa.")
        if self._misiones.contiene(id_mision):
            return ResultadoOperacion(False, f"Ya existe una misión registrada con el ID '{id_mision}'.")

        self._contador_llegada += 1
        nueva = Mision(
            id=id_mision,
            nombre=nombre,
            tipo=tipo,
            urgencia=urgencia,
            ubicacion=ubicacion,
            estado=EstadoMision.PENDIENTE,
            orden_llegada=self._contador_llegada,
        )

        self._misiones.insertar_o_actualizar(id_mision, nueva)
        self._cola_prioridad.insertar(nueva)
        return ResultadoOperacion(True, f"Misión '{id_mision}' registrada como pendiente.")

    def buscar_mision(self, id_mision: str) -> ResultadoBusqueda:
        """
        Operación 2: Buscar misión.
        - Entradas: identificador de la misión.
        - Cambios: ninguno (solo lectura en TablaHash).
        - Casos borde: si el motor está vacío, el ID es vacío o no existe, informa
          que no fue encontrada; si existe (pendiente, en curso o cancelada),
          devuelve una copia de sus datos y estado.
        """
        if not id_mision:
            return ResultadoBusqueda(False, None, "El ID de búsqueda está vacío.")
        mision = self._misiones.obtener(id_mision)
        if mision is None:
            return ResultadoBusqueda(False, None, f"No existe ninguna misión con el ID '{id_mision}'.")
        return ResultadoBusqueda(True, copiar_mision(mision), "Misión encontrada.")

    def cambiar_urgencia(self, id_mision: str, nueva_urgencia: int) -> ResultadoOperacion:
        """
        Operación 3: Cambiar urgencia.
        - Entradas: id y nueva urgencia [1..10].
        - Cambios: actualiza la urgencia en TablaHash y reubica la misión dentro
          de HeapMisiones en O(log n) usando el diccionario de posiciones.
        - Casos borde: rechaza urgencia fuera de rango, ID inexistente o misión
          cuyo estado no sea PENDIENTE (en curso o cancelada).
        """
        if isinstance(nueva_urgencia, bool) or not isinstance(nueva_urgencia, int):
            return ResultadoOperacion(False, "La nueva urgencia debe ser un número entero.")
        if nueva_urgencia < URGENCIA_MIN or nueva_urgencia > URGENCIA_MAX:
            return ResultadoOperacion(False, "La nueva urgencia debe estar entre 1 y 10.")

        mision = self._misiones.obtener(id_mision)
        if mision is None:
            return ResultadoOperacion(False, f"No existe ninguna misión con el ID '{id_mision}'.")
        if mision.estado != EstadoMision.PENDIENTE:
            return ResultadoOperacion(False, "Solo se puede cambiar la urgencia de misiones pendientes.")

        mision.urgencia = nueva_urgencia
        self._cola_prioridad.actualizar_urgencia(id_mision, nueva_urgencia)
        return ResultadoOperacion(
            True, f"Urgencia de la misión '{id_mision}' actualizada a {nueva_urgencia}."
        )

    def cancelar_mision(self, id_mision: str) -> ResultadoOperacion:
        """
        Operación 4: Cancelar misión.
        - Entradas: id de la misión.
        - Cambios: cambia su estado a CANCELADA en TablaHash (conservando sus datos)
          y la elimina de HeapMisiones en O(log n).
        - Casos borde: rechaza ID inexistente o misión que no esté PENDIENTE.
        """
        mision = self._misiones.obtener(id_mision)
        if mision is None:
            return ResultadoOperacion(False, f"No existe ninguna misión con el ID '{id_mision}'.")
        if mision.estado != EstadoMision.PENDIENTE:
            return ResultadoOperacion(False, "Solo se pueden cancelar misiones que estén pendientes.")

        mision.estado = EstadoMision.CANCELADA
        self._cola_prioridad.eliminar_por_id(id_mision)
        return ResultadoOperacion(
            True, f"Misión '{id_mision}' cancelada y retirada de la cola de prioridad."
        )

    def obtener_siguiente_mision(self) -> ResultadoSiguiente:
        """
        Operación 5: Obtener siguiente misión.
        - Entradas: ninguna.
        - Cambios: extrae la misión de mayor prioridad de HeapMisiones y actualiza
          su estado a EN_CURSO en TablaHash.
        - Casos borde: si no hay misiones pendientes, devuelve disponible=False.
        """
        elegida = self._cola_prioridad.extraer_maximo()
        if elegida is None:
            return ResultadoSiguiente(False, None, "No hay misiones pendientes disponibles.")

        mision_maestra = self._misiones.obtener(elegida.id)
        if mision_maestra is not None:
            mision_maestra.estado = EstadoMision.EN_CURSO
        elegida.estado = EstadoMision.EN_CURSO

        return ResultadoSiguiente(
            True, elegida, f"Misión '{elegida.id}' asignada y puesta en curso."
        )

    def consultar_primeras_k(self, k: int) -> ResultadoTopK:
        """
        Operación 6: Consultar las primeras k misiones.
        - Entradas: entero k.
        - Cambios: ninguno (consulta no destructiva sobre HeapMisiones).
        - Casos borde: rechaza k < 0; si k == 0 o el heap está vacío devuelve
          lista vacía; si k > total_pendientes(), devuelve solo las existentes.
        """
        if isinstance(k, bool) or not isinstance(k, int):
            return ResultadoTopK(False, [], "El parámetro k debe ser un número entero.")
        if k < 0:
            return ResultadoTopK(False, [], "El parámetro k no puede ser negativo.")

        lista = self._cola_prioridad.consultar_top_k(k)
        if not lista:
            return ResultadoTopK(True, [], "No hay misiones pendientes para mostrar.")
        return ResultadoTopK(True, lista, "Consulta de primeras k misiones completada.")

    def calcular_ruta_a_mision(self, ubicacion_jugador: str, id_mision: str) -> ResultadoRuta:
        """
        Operación 7: Calcular ruta a una misión.
        - Entradas: ubicación actual del jugador e id de la misión destino.
        - Cambios: ninguno (consulta TablaHash para localizar el destino y ejecuta
          Dijkstra sobre GrafoCiudad).
        - Casos borde: rechaza ID inexistente, misión CANCELADA, origen inexistente
          en el mapa o ausencia de camino entre ambos lugares.
        """
        mision = self._misiones.obtener(id_mision)
        if mision is None:
            return ResultadoRuta(False, [], 0, f"No existe ninguna misión con el ID '{id_mision}'.")
        if mision.estado == EstadoMision.CANCELADA:
            return ResultadoRuta(
                False, [], 0, f"La misión '{id_mision}' fue cancelada y no requiere ruta."
            )
        return self._mapa.calcular_ruta_minima(ubicacion_jugador, mision.ubicacion)

    # ---------------- Verificación de invariantes globales ----------------

    def verificar_invariantes(self) -> bool:
        """
        Verifica los invariantes internos de TablaHash, HeapMisiones y GrafoCiudad,
        además del invariante global de sincronización entre estructuras:
          - Toda misión PENDIENTE en TablaHash existe idéntica en HeapMisiones.
          - Ninguna misión EN_CURSO o CANCELADA permanece dentro de HeapMisiones.
          - El conteo de misiones PENDIENTE coincide con el tamaño del heap.
        """
        if (
            not self._misiones.verificar_invariante()
            or not self._cola_prioridad.verificar_invariante()
            or not self._mapa.verificar_invariante()
        ):
            return False

        pendientes_en_hash = 0
        for id_mision in self._misiones.claves():
            m_hash = self._misiones.obtener(id_mision)
            if m_hash is None:
                return False
            if m_hash.estado == EstadoMision.PENDIENTE:
                pendientes_en_hash += 1
                m_heap = self._cola_prioridad.obtener_por_id(id_mision)
                if m_heap is None or not misiones_son_iguales(m_hash, m_heap):
                    return False
            else:
                if self._cola_prioridad.contiene(id_mision):
                    return False

        return pendientes_en_hash == self._cola_prioridad.tamano()
