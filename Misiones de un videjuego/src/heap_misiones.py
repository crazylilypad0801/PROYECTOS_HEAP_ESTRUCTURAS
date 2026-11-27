"""
ARCHIVO: src/heap_misiones.py
FAMILIA DE ESTRUCTURA: Árboles (estructura propia #2).
PROPÓSITO:
    Implementa un Max-Heap binario indexado para mantener únicamente las
    misiones en estado PENDIENTE ordenadas por prioridad.

    Además del arreglo implícito del árbol binario completo (_datos), mantiene
    un diccionario de posiciones basado en nuestra TablaHash (_posiciones: id -> índice).
    Gracias a ese índice, cambiar la urgencia de una misión o cancelarla por ID
    se ejecuta en O(log n) esperado en lugar de requerir una búsqueda lineal O(n).
"""

from typing import List, Optional

from .mision import Mision, copiar_mision, tiene_mayor_prioridad
from .tabla_hash import TablaHash


class _HeapAuxiliarIndices:
    """
    Pequeño Max-Heap binario de índices implementado manualmente para soportar
    consultar_top_k(k) en O(k log k) SIN modificar el heap principal ni usar heapq.

    Compara índices i, j mirando la prioridad de datos[i] frente a datos[j].
    """

    def __init__(self, ref_datos: List[Mision]) -> None:
        self._ref_datos = ref_datos
        self._indices: List[int] = []

    def vacio(self) -> bool:
        return len(self._indices) == 0

    def insertar(self, idx: int) -> None:
        self._indices.append(idx)
        self._subir(len(self._indices) - 1)

    def extraer_maximo(self) -> int:
        max_idx = self._indices[0]
        ultimo = self._indices.pop()
        if self._indices:
            self._indices[0] = ultimo
            self._bajar(0)
        return max_idx

    def _subir(self, pos: int) -> None:
        while pos > 0:
            padre = (pos - 1) // 2
            idx_pos = self._indices[pos]
            idx_padre = self._indices[padre]
            if tiene_mayor_prioridad(self._ref_datos[idx_pos], self._ref_datos[idx_padre]):
                self._indices[pos], self._indices[padre] = self._indices[padre], self._indices[pos]
                pos = padre
            else:
                break

    def _bajar(self, pos: int) -> None:
        n = len(self._indices)
        while True:
            izq = 2 * pos + 1
            der = 2 * pos + 2
            mejor = pos

            if izq < n and tiene_mayor_prioridad(
                self._ref_datos[self._indices[izq]], self._ref_datos[self._indices[mejor]]
            ):
                mejor = izq
            if der < n and tiene_mayor_prioridad(
                self._ref_datos[self._indices[der]], self._ref_datos[self._indices[mejor]]
            ):
                mejor = der

            if mejor != pos:
                self._indices[pos], self._indices[mejor] = self._indices[mejor], self._indices[pos]
                pos = mejor
            else:
                break


class HeapMisiones:
    """
    Cola de prioridad implementada como Max-Heap binario indexado por ID.
    La raíz (índice 0) siempre corresponde a la misión pendiente que debe
    atenderse primero según tiene_mayor_prioridad().
    """

    def __init__(self) -> None:
        self._datos: List[Mision] = []
        self._posiciones: TablaHash[str, int] = TablaHash()

    def _intercambiar(self, i: int, j: int) -> None:
        """
        Intercambia los elementos en las posiciones i y j del arreglo del heap
        y actualiza de inmediato ambas entradas en la TablaHash de posiciones.
        """
        if i == j:
            return
        self._datos[i], self._datos[j] = self._datos[j], self._datos[i]
        self._posiciones.insertar_o_actualizar(self._datos[i].id, i)
        self._posiciones.insertar_o_actualizar(self._datos[j].id, j)

    def _subir(self, idx: int) -> None:
        """
        Restaura la propiedad de Max-Heap hacia arriba (sift-up) mientras el nodo
        en idx tenga mayor prioridad que su padre (idx - 1) // 2.
        Complejidad: O(log n).
        """
        while idx > 0:
            padre = (idx - 1) // 2
            if tiene_mayor_prioridad(self._datos[idx], self._datos[padre]):
                self._intercambiar(idx, padre)
                idx = padre
            else:
                break

    def _bajar(self, idx: int) -> None:
        """
        Restaura la propiedad de Max-Heap hacia abajo (sift-down) intercambiando
        el nodo en idx con su hijo de mayor prioridad hasta estabilizar el subárbol.
        Complejidad: O(log n).
        """
        n = len(self._datos)
        while True:
            izq = 2 * idx + 1
            der = 2 * idx + 2
            mejor = idx

            if izq < n and tiene_mayor_prioridad(self._datos[izq], self._datos[mejor]):
                mejor = izq
            if der < n and tiene_mayor_prioridad(self._datos[der], self._datos[mejor]):
                mejor = der

            if mejor != idx:
                self._intercambiar(idx, mejor)
                idx = mejor
            else:
                break

    def insertar(self, mision: Mision) -> bool:
        """
        Agrega una misión pendiente al final del heap y la flota hasta su posición.
        Complejidad: O(log n) en tiempo esperado.
        """
        if self._posiciones.contiene(mision.id):
            return False
        idx = len(self._datos)
        self._datos.append(copiar_mision(mision))
        self._posiciones.insertar_o_actualizar(mision.id, idx)
        self._subir(idx)
        return True

    def actualizar_urgencia(self, id_mision: str, nueva_urgencia: int) -> bool:
        """
        Modifica la urgencia de una misión ya presente en el heap y ajusta su
        posición en O(log n) esperado usando _posiciones para encontrarla en O(1).
        """
        idx = self._posiciones.obtener(id_mision)
        if idx is None:
            return False

        urgencia_anterior = self._datos[idx].urgencia
        self._datos[idx].urgencia = nueva_urgencia

        if nueva_urgencia > urgencia_anterior:
            self._subir(idx)
        elif nueva_urgencia < urgencia_anterior:
            self._bajar(idx)
        return True

    def eliminar_por_id(self, id_mision: str) -> bool:
        """
        Retira una misión arbitraria del heap (por ejemplo, al cancelarla).
        Mueve el último elemento al hueco liberado, borra el ID del índice
        y restaura la propiedad de Max-Heap en O(log n) esperado.
        """
        idx = self._posiciones.obtener(id_mision)
        if idx is None:
            return False

        ultimo = len(self._datos) - 1
        if idx == ultimo:
            self._posiciones.eliminar(id_mision)
            self._datos.pop()
            return True

        self._intercambiar(idx, ultimo)
        self._posiciones.eliminar(id_mision)
        self._datos.pop()

        # El elemento traído desde el final puede necesitar subir o bajar.
        self._subir(idx)
        self._bajar(idx)
        return True

    def extraer_maximo(self) -> Optional[Mision]:
        """
        Retira y devuelve la misión de mayor prioridad (la raíz del heap).
        Devuelve None si el heap está vacío.
        Complejidad: O(log n) en tiempo esperado.
        """
        if not self._datos:
            return None

        maxima = copiar_mision(self._datos[0])
        ultimo = len(self._datos) - 1

        if ultimo == 0:
            self._posiciones.eliminar(maxima.id)
            self._datos.pop()
            return maxima

        self._intercambiar(0, ultimo)
        self._posiciones.eliminar(maxima.id)
        self._datos.pop()
        self._bajar(0)
        return maxima

    def consultar_top_k(self, k: int) -> List[Mision]:
        """
        Devuelve hasta k misiones pendientes en orden descendente de prioridad
        SIN modificar el heap principal.

        Funcionamiento:
            Usa un heap auxiliar con índices del arreglo _datos. Inicia en la
            raíz (índice 0). Cada vez que extrae el índice más prioritario, solo
            sus dos hijos (2*idx + 1 y 2*idx + 2) pueden convertirse en los
            siguientes candidatos inmediatos.
        Complejidad: O(k log k), muy eficiente cuando k es pequeño frente a n.
        """
        if k <= 0 or not self._datos:
            return []

        limite = min(k, len(self._datos))
        resultado: List[Mision] = []
        aux = _HeapAuxiliarIndices(self._datos)
        aux.insertar(0)

        while not aux.vacio() and len(resultado) < limite:
            idx = aux.extraer_maximo()
            resultado.append(copiar_mision(self._datos[idx]))

            izq = 2 * idx + 1
            der = 2 * idx + 2
            if izq < len(self._datos):
                aux.insertar(izq)
            if der < len(self._datos):
                aux.insertar(der)

        return resultado

    def contiene(self, id_mision: str) -> bool:
        """Indica si una misión se encuentra actualmente en el heap."""
        return self._posiciones.contiene(id_mision)

    def obtener_por_id(self, id_mision: str) -> Optional[Mision]:
        """Devuelve una copia de la misión guardada en el heap, o None si no está."""
        idx = self._posiciones.obtener(id_mision)
        if idx is None:
            return None
        return copiar_mision(self._datos[idx])

    def tamano(self) -> int:
        """Cantidad de misiones pendientes en el heap."""
        return len(self._datos)

    def vacio(self) -> bool:
        """Indica si no hay misiones pendientes."""
        return len(self._datos) == 0

    def verificar_invariante(self) -> bool:
        """
        INVARIANTE DE REPRESENTACIÓN DEL HEAP INDEXADO:
        Verifica que:
            1. La TablaHash _posiciones cumple su propio invariante.
            2. len(_datos) coincide exactamente con _posiciones.tamano().
            3. Para todo índice i, _posiciones.obtener(_datos[i].id) == i.
            4. Propiedad de Max-Heap: ningún nodo i > 0 tiene mayor prioridad
               que su padre (i - 1) // 2.
        """
        if not self._posiciones.verificar_invariante():
            return False
        if self._posiciones.tamano() != len(self._datos):
            return False

        for i, mision in enumerate(self._datos):
            pos_guardada = self._posiciones.obtener(mision.id)
            if pos_guardada is None or pos_guardada != i:
                return False
            if i > 0:
                padre = (i - 1) // 2
                if tiene_mayor_prioridad(self._datos[i], self._datos[padre]):
                    return False

        return True
