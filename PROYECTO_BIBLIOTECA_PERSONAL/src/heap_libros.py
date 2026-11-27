"""
ARCHIVO: src/heap_libros.py
FAMILIA DE ESTRUCTURA: Árboles (heap máximo binario indexado propio).
PROPÓSITO:
    Mantiene los libros PENDIENTES ordenados por la prioridad que asigna la
    persona. Además del arreglo implícito del árbol binario completo (_datos),
    guarda una TablaHash de posiciones (_posiciones: id -> índice). Así cambiar
    la prioridad o retirar un libro por ID cuesta O(log n) y no O(n).

PROPIEDAD QUE SIEMPRE CUMPLE (invariante de representación):
    1. La tabla _posiciones cumple su propio invariante.
    2. len(_datos) == _posiciones.tamano().
    3. Para todo índice i: _posiciones.obtener(_datos[i].id) == i.
    4. Propiedad de heap: ningún nodo i > 0 tiene mayor prioridad que su padre
       (i - 1) // 2, según tiene_mayor_prioridad().
"""

from typing import List, Optional

from .libro import EntradaHeap, tiene_mayor_prioridad
from .tabla_hash import TablaHash


def _copiar_entrada(e: EntradaHeap) -> EntradaHeap:
    return EntradaHeap(e.id, e.prioridad, e.orden)


class HeapLibros:
    """Cola de prioridad (max-heap) indexada por ID del libro."""

    def __init__(self) -> None:
        self._datos: List[EntradaHeap] = []
        self._posiciones: TablaHash[str, int] = TablaHash()

    def _intercambiar(self, i: int, j: int) -> None:
        """Intercambia dos posiciones y actualiza AL MISMO TIEMPO la tabla de posiciones."""
        if i == j:
            return
        self._datos[i], self._datos[j] = self._datos[j], self._datos[i]
        self._posiciones.insertar_o_actualizar(self._datos[i].id, i)
        self._posiciones.insertar_o_actualizar(self._datos[j].id, j)

    def _subir(self, idx: int) -> None:
        """Sift-up: sube mientras el nodo tenga mayor prioridad que su padre. O(log n)."""
        while idx > 0:
            padre = (idx - 1) // 2
            if tiene_mayor_prioridad(self._datos[idx], self._datos[padre]):
                self._intercambiar(idx, padre)
                idx = padre
            else:
                break

    def _bajar(self, idx: int) -> None:
        """Sift-down: baja intercambiando con el hijo de mayor prioridad. O(log n)."""
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

    def insertar(self, id_libro: str, prioridad: int, orden: int) -> bool:
        """Agrega un pendiente al final y lo sube. False si ya estaba. O(log n) esperado."""
        if self._posiciones.contiene(id_libro):
            return False
        idx = len(self._datos)
        self._datos.append(EntradaHeap(id_libro, prioridad, orden))
        self._posiciones.insertar_o_actualizar(id_libro, idx)
        self._subir(idx)
        return True

    def actualizar_prioridad(self, id_libro: str, nueva_prioridad: int) -> bool:
        """
        Cambia la prioridad y reubica la entrada. Su orden de llegada a pendientes
        NO cambia. Localiza en O(1) esperado y reubica en O(log n).
        """
        idx = self._posiciones.obtener(id_libro)
        if idx is None:
            return False
        anterior = self._datos[idx].prioridad
        self._datos[idx].prioridad = nueva_prioridad
        if nueva_prioridad > anterior:
            self._subir(idx)
        elif nueva_prioridad < anterior:
            self._bajar(idx)
        return True

    def eliminar_por_id(self, id_libro: str) -> bool:
        """
        Retira una entrada arbitraria (por ejemplo, al terminar un libro que
        seguía pendiente). El último elemento llena el hueco y puede necesitar
        subir o bajar. O(log n) esperado.
        """
        idx = self._posiciones.obtener(id_libro)
        if idx is None:
            return False
        ultimo = len(self._datos) - 1
        if idx == ultimo:
            self._posiciones.eliminar(id_libro)
            self._datos.pop()
            return True
        self._intercambiar(idx, ultimo)
        self._posiciones.eliminar(id_libro)
        self._datos.pop()
        self._subir(idx)
        self._bajar(idx)
        return True

    def extraer_maximo(self) -> Optional[EntradaHeap]:
        """Retira y devuelve (copia de) la entrada de mayor prioridad, o None. O(log n)."""
        if not self._datos:
            return None
        maxima = _copiar_entrada(self._datos[0])
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

    def contiene(self, id_libro: str) -> bool:
        return self._posiciones.contiene(id_libro)

    def obtener_entrada(self, id_libro: str) -> Optional[EntradaHeap]:
        """Copia de la entrada de ese libro, o None si no está pendiente."""
        idx = self._posiciones.obtener(id_libro)
        if idx is None:
            return None
        return _copiar_entrada(self._datos[idx])

    def ids(self) -> List[str]:
        """IDs de todos los pendientes (orden interno del arreglo, no por prioridad)."""
        return [e.id for e in self._datos]

    def tamano(self) -> int:
        return len(self._datos)

    def vacio(self) -> bool:
        return len(self._datos) == 0

    def verificar_invariante(self) -> bool:
        """Comprueba las 4 propiedades descritas en el docstring del módulo."""
        if not self._posiciones.verificar_invariante():
            return False
        if self._posiciones.tamano() != len(self._datos):
            return False
        for i, entrada in enumerate(self._datos):
            pos = self._posiciones.obtener(entrada.id)
            if pos is None or pos != i:
                return False
            if i > 0 and tiene_mayor_prioridad(entrada, self._datos[(i - 1) // 2]):
                return False
        return True
