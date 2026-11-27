"""
ARCHIVO: src/grafo_ciudad.py
FAMILIA DE ESTRUCTURA: Grafos (estructura propia #3).
PROPÓSITO:
    Representa los lugares y caminos de la ciudad mediante un grafo ponderado
    con listas de adyacencia y pesos no negativos.
    Incluye la implementación propia del algoritmo de Dijkstra apoyada en un
    Min-Heap binario manual (sin usar heapq) para calcular la ruta de menor
    costo desde la ubicación del jugador hasta una misión.
"""

from typing import List, Tuple

from .mision import ResultadoRuta
from .tabla_hash import TablaHash


class _MinHeapDijkstra:
    """
    Min-Heap binario implementado desde cero para la cola de prioridad de
    Dijkstra. Cada elemento almacenado es una tupla (distancia_acumulada, nodo).
    """

    def __init__(self) -> None:
        self._heap: List[Tuple[int, int]] = []

    def vacio(self) -> bool:
        return len(self._heap) == 0

    def insertar(self, distancia: int, nodo: int) -> None:
        self._heap.append((distancia, nodo))
        self._subir(len(self._heap) - 1)

    def extraer_minimo(self) -> Tuple[int, int]:
        minimo = self._heap[0]
        ultimo = self._heap.pop()
        if self._heap:
            self._heap[0] = ultimo
            self._bajar(0)
        return minimo

    def _subir(self, pos: int) -> None:
        while pos > 0:
            padre = (pos - 1) // 2
            if self._heap[pos][0] < self._heap[padre][0]:
                self._heap[pos], self._heap[padre] = self._heap[padre], self._heap[pos]
                pos = padre
            else:
                break

    def _bajar(self, pos: int) -> None:
        n = len(self._heap)
        while True:
            izq = 2 * pos + 1
            der = 2 * pos + 2
            menor = pos

            if izq < n and self._heap[izq][0] < self._heap[menor][0]:
                menor = izq
            if der < n and self._heap[der][0] < self._heap[menor][0]:
                menor = der

            if menor != pos:
                self._heap[pos], self._heap[menor] = self._heap[menor], self._heap[pos]
                pos = menor
            else:
                break


class GrafoCiudad:
    """
    Grafo ponderado de ubicaciones de la ciudad usando listas de adyacencia.
    Traduce los nombres de lugares (str) a índices enteros [0, V-1] mediante
    una TablaHash para que Dijkstra trabaje de forma compacta con arreglos.
    """

    def __init__(self) -> None:
        self._nombre_a_indice: TablaHash[str, int] = TablaHash()
        self._indice_a_nombre: List[str] = []
        # Cada entrada adyacencia[u] contiene tuplas (indice_destino, peso).
        self._adyacencia: List[List[Tuple[int, int]]] = []

    def agregar_ubicacion(self, nombre: str) -> bool:
        """
        Registra un nuevo lugar (vértice) en el mapa si su nombre no es vacío
        y no existía previamente.
        """
        if not isinstance(nombre, str) or not nombre or self._nombre_a_indice.contiene(nombre):
            return False
        nuevo_idx = len(self._indice_a_nombre)
        self._nombre_a_indice.insertar_o_actualizar(nombre, nuevo_idx)
        self._indice_a_nombre.append(nombre)
        self._adyacencia.append([])
        return True

    def existe_ubicacion(self, nombre: str) -> bool:
        """Indica si una ubicación está registrada en el mapa."""
        if not isinstance(nombre, str) or not nombre:
            return False
        return self._nombre_a_indice.contiene(nombre)

    def agregar_camino(
        self,
        origen: str,
        destino: str,
        peso: int,
        bidireccional: bool = True,
    ) -> bool:
        """
        Agrega un camino con costo 'peso' (>= 0) entre dos ubicaciones existentes.
        Por defecto los caminos de la ciudad son bidireccionales (grafo no dirigido).
        Rechaza pesos negativos porque el algoritmo de Dijkstra requiere pesos >= 0.
        """
        if isinstance(peso, bool) or not isinstance(peso, int) or peso < 0:
            return False
        idx_u = self._nombre_a_indice.obtener(origen)
        idx_v = self._nombre_a_indice.obtener(destino)
        if idx_u is None or idx_v is None:
            return False

        self._adyacencia[idx_u].append((idx_v, peso))
        if bidireccional and idx_u != idx_v:
            self._adyacencia[idx_v].append((idx_u, peso))
        return True

    def calcular_ruta_minima(self, origen: str, destino: str) -> ResultadoRuta:
        """
        Calcula la ruta de menor costo entre 'origen' y 'destino' mediante Dijkstra.
        Complejidad temporal: O((V + E) log V) con listas de adyacencia y heap binario.
        Complejidad espacial: O(V + E) para el grafo + O(V) para dist, padre y cola.
        """
        idx_origen = self._nombre_a_indice.obtener(origen) if isinstance(origen, str) else None
        idx_destino = self._nombre_a_indice.obtener(destino) if isinstance(destino, str) else None

        if idx_origen is None:
            return ResultadoRuta(
                existe=False,
                mensaje=f"La ubicación actual del jugador ('{origen}') no existe en el mapa.",
            )
        if idx_destino is None:
            return ResultadoRuta(
                existe=False,
                mensaje=f"La ubicación de la misión ('{destino}') no existe en el mapa.",
            )

        # Caso trivial: el jugador ya está parado en la ubicación de la misión.
        if idx_origen == idx_destino:
            return ResultadoRuta(
                existe=True,
                camino=[origen],
                costo_total=0,
                mensaje="El jugador ya se encuentra en la ubicación de la misión.",
            )

        n = len(self._indice_a_nombre)
        inf = float("inf")
        dist: List[float] = [inf] * n
        padre: List[int] = [-1] * n

        cola = _MinHeapDijkstra()
        dist[idx_origen] = 0
        cola.insertar(0, idx_origen)

        while not cola.vacio():
            dist_actual, u = cola.extraer_minimo()

            # Ignorar entradas desactualizadas en la cola de prioridad (lazy deletion).
            if dist_actual > dist[u]:
                continue
            # Al extraer el destino de la cima del Min-Heap, su distancia mínima es definitiva.
            if u == idx_destino:
                break

            for v, peso in self._adyacencia[u]:
                nueva_dist = dist_actual + peso
                if nueva_dist < dist[v]:
                    dist[v] = nueva_dist
                    padre[v] = u
                    cola.insertar(nueva_dist, v)

        if dist[idx_destino] == inf:
            return ResultadoRuta(
                existe=False,
                camino=[],
                costo_total=0,
                mensaje=f"No existe un camino entre '{origen}' y '{destino}'.",
            )

        # Reconstruimos el camino desde destino hasta origen siguiendo los punteros padre[].
        camino: List[str] = []
        actual = idx_destino
        while actual != -1:
            camino.append(self._indice_a_nombre[actual])
            actual = padre[actual]
        camino.reverse()

        return ResultadoRuta(
            existe=True,
            camino=camino,
            costo_total=int(dist[idx_destino]),
            mensaje="Ruta óptima encontrada.",
        )

    def validar_camino(
        self,
        origen: str,
        destino: str,
        camino: List[str],
        costo_esperado: int,
    ) -> bool:
        """
        Verifica que una lista de ubicaciones forme un camino real en el grafo
        cuya suma de aristas de mínimo peso entre nodos consecutivos sea igual
        a 'costo_esperado'. Útil en pruebas diferenciales cuando existen empates
        de caminos óptimos distintos con el mismo costo total.
        """
        if not camino or camino[0] != origen or camino[-1] != destino:
            return False

        costo_acumulado = 0
        for i in range(len(camino) - 1):
            idx_u = self._nombre_a_indice.obtener(camino[i])
            idx_v = self._nombre_a_indice.obtener(camino[i + 1])
            if idx_u is None or idx_v is None:
                return False

            mejor_peso = None
            for vecino, peso in self._adyacencia[idx_u]:
                if vecino == idx_v and (mejor_peso is None or peso < mejor_peso):
                    mejor_peso = peso

            if mejor_peso is None:
                return False
            costo_acumulado += mejor_peso

        return costo_acumulado == costo_esperado

    def cantidad_ubicaciones(self) -> int:
        return len(self._indice_a_nombre)

    def cantidad_aristas_dirigidas(self) -> int:
        return sum(len(lista) for lista in self._adyacencia)

    def verificar_invariante(self) -> bool:
        """
        INVARIANTE DE REPRESENTACIÓN DEL GRAFO:
        Comprueba que:
            1. _nombre_a_indice cumple su invariante de TablaHash.
            2. Hay correspondencia exacta 1 a 1 entre _nombre_a_indice e _indice_a_nombre.
            3. Todas las aristas apuntan a índices válidos en [0, V-1] con peso >= 0.
        """
        if not self._nombre_a_indice.verificar_invariante():
            return False

        v = len(self._indice_a_nombre)
        if self._nombre_a_indice.tamano() != v or len(self._adyacencia) != v:
            return False

        for i, nombre in enumerate(self._indice_a_nombre):
            idx = self._nombre_a_indice.obtener(nombre)
            if idx is None or idx != i:
                return False
            for destino, peso in self._adyacencia[i]:
                if destino < 0 or destino >= v or peso < 0:
                    return False

        return True
