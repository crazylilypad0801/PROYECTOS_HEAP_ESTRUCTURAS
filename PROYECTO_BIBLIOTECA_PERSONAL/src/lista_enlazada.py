"""
ARCHIVO: src/lista_enlazada.py
FAMILIA DE ESTRUCTURA: Secuencias (lista enlazada simple propia).
PROPÓSITO:
    Organiza las lecturas recientes. Guarda los IDs de los libros terminados;
    cada libro que se termina se inserta en la cabeza, así el primer nodo es
    siempre la lectura más reciente.

PROPIEDAD QUE SIEMPRE CUMPLE (invariante de representación):
    1. Recorriendo desde la cabeza se visitan exactamente _tamano nodos.
    2. No hay ciclos (el recorrido termina en None).
    3. Si _tamano == 0, la cabeza es None.
"""

from typing import List, Optional


class _Nodo:
    """Nodo de la lista: un ID de libro y el puntero al siguiente (más antiguo)."""

    __slots__ = ("valor", "siguiente")

    def __init__(self, valor: str, siguiente: "Optional[_Nodo]" = None) -> None:
        self.valor = valor
        self.siguiente = siguiente


class ListaEnlazada:
    """Lista enlazada simple con inserción en la cabeza."""

    def __init__(self) -> None:
        self._cabeza: Optional[_Nodo] = None
        self._tamano: int = 0

    def insertar_al_inicio(self, valor: str) -> None:
        """Coloca 'valor' como nueva cabeza. O(1) en el peor caso."""
        self._cabeza = _Nodo(valor, self._cabeza)
        self._tamano += 1

    def primeros_k(self, k: int) -> List[str]:
        """
        Devuelve hasta k valores desde la cabeza (del más reciente al más antiguo)
        SIN modificar la lista. O(k).
        """
        resultado: List[str] = []
        actual = self._cabeza
        while actual is not None and len(resultado) < k:
            resultado.append(actual.valor)
            actual = actual.siguiente
        return resultado

    def eliminar(self, valor: str) -> bool:
        """
        Elimina la primera aparición de 'valor'. Devuelve False si no estaba.
        Al ser lista simple, hay que recorrerla guardando el nodo anterior. O(n).
        """
        anterior: Optional[_Nodo] = None
        actual = self._cabeza
        while actual is not None:
            if actual.valor == valor:
                if anterior is None:
                    self._cabeza = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                self._tamano -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

    def todos(self) -> List[str]:
        """Todos los valores, del más reciente al más antiguo. O(n)."""
        return self.primeros_k(self._tamano)

    def tamano(self) -> int:
        return self._tamano

    def vacia(self) -> bool:
        return self._tamano == 0

    def verificar_invariante(self) -> bool:
        """Recorre la lista con un tope de _tamano + 1 pasos para detectar ciclos."""
        if self._tamano == 0:
            return self._cabeza is None
        visitados = 0
        actual = self._cabeza
        while actual is not None:
            visitados += 1
            if visitados > self._tamano:
                return False  # Más nodos que _tamano (o un ciclo).
            actual = actual.siguiente
        return visitados == self._tamano
