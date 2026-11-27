"""
ARCHIVO: benchmarks/mediciones.py
PROPÓSITO:
    Ejecuta las mediciones empíricas de rendimiento para dos operaciones clave
    del motor, comparando dos candidatos razonables en dos escenarios y cuatro
    tamaños de entrada cada uno, con 5 repeticiones por configuración.

    Operación medida 1 (Operación 6: consultar_primeras_k + actualizaciones):
      - Candidato 1: Heap binario indexado (HeapMisiones, top-k en O(k log k)).
      - Candidato 2: Árbol AVL ordenado por prioridad (top-k en O(log n + k)).
      - Tamaños: n = 1 000, 5 000, 20 000, 50 000 misiones pendientes.
      - Escenario A: Actualizaciones intensivas + top-k pequeño (k = 10).
      - Escenario B: Consultas intensivas de top-k grande (k = 500) sin cambios.

    Operación medida 2 (Operación 7: calcular_ruta_a_mision / Dijkstra):
      - Candidato 1: Dijkstra con listas de adyacencia + Min-Heap binario.
      - Candidato 2: Dijkstra con matriz de adyacencia + selección lineal O(V^2).
      - Tamaños: V = 100, 250, 500, 1 000 ubicaciones.
      - Escenario A: Grafo disperso de ciudad (E ≈ 3*V aristas no dirigidas).
      - Escenario B: Grafo denso con portales/teletransporte (densidad ≈ 85%).

    Los resultados (promedio y mediana en milisegundos) se guardan en:
      - benchmarks/resultados/medicion_top_k.csv
      - benchmarks/resultados/medicion_rutas.csv
"""

import csv
import os
import random
import statistics
import sys
import time
from typing import Dict, List, Optional, Tuple

# Asegura que el directorio raíz del proyecto esté en sys.path.
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from src.grafo_ciudad import GrafoCiudad
from src.heap_misiones import HeapMisiones
from src.mision import EstadoMision, Mision, TipoMision, clave_orden_prioridad, copiar_mision

REPETICIONES = 5
DIR_RESULTADOS = os.path.join(os.path.dirname(__file__), "resultados")


# ============================================================================
# CANDIDATO ALTERNATIVO PARA OPERACIÓN 6: Árbol AVL ordenado por prioridad
# ============================================================================

class _NodoAVL:
    """Nodo de un árbol AVL ordenado por clave_orden_prioridad(mision)."""

    __slots__ = ("clave", "mision", "izq", "der", "altura")

    def __init__(self, mision: Mision) -> None:
        self.clave = clave_orden_prioridad(mision)
        self.mision = mision
        self.izq: Optional[_NodoAVL] = None
        self.der: Optional[_NodoAVL] = None
        self.altura: int = 1


class _ArbolAVLPrioridad:
    """
    Candidato alternativo al Heap para mantener misiones ordenadas por prioridad.
    - Inserción, actualización de urgencia y borrado: O(log n) con rotaciones.
    - Consulta top-k: recorrido en orden ascendente de clave_orden_prioridad
      (izq -> raíz -> der), deteniéndose exactamente al reunir k elementos: O(log n + k).
    """

    def __init__(self) -> None:
        self._raiz: Optional[_NodoAVL] = None
        self._por_id: Dict[str, Mision] = {}

    @staticmethod
    def _altura(nodo: Optional[_NodoAVL]) -> int:
        return nodo.altura if nodo is not None else 0

    @classmethod
    def _actualizar_altura(cls, nodo: _NodoAVL) -> None:
        nodo.altura = 1 + max(cls._altura(nodo.izq), cls._altura(nodo.der))

    @classmethod
    def _balance(cls, nodo: Optional[_NodoAVL]) -> int:
        if nodo is None:
            return 0
        return cls._altura(nodo.izq) - cls._altura(nodo.der)

    @classmethod
    def _rotar_derecha(cls, y: _NodoAVL) -> _NodoAVL:
        x = y.izq
        assert x is not None
        t2 = x.der
        x.der = y
        y.izq = t2
        cls._actualizar_altura(y)
        cls._actualizar_altura(x)
        return x

    @classmethod
    def _rotar_izquierda(cls, x: _NodoAVL) -> _NodoAVL:
        y = x.der
        assert y is not None
        t2 = y.izq
        y.izq = x
        x.der = t2
        cls._actualizar_altura(x)
        cls._actualizar_altura(y)
        return y

    @classmethod
    def _rebalancear(cls, nodo: _NodoAVL) -> _NodoAVL:
        cls._actualizar_altura(nodo)
        fb = cls._balance(nodo)
        if fb > 1:
            if cls._balance(nodo.izq) < 0:
                assert nodo.izq is not None
                nodo.izq = cls._rotar_izquierda(nodo.izq)
            return cls._rotar_derecha(nodo)
        if fb < -1:
            if cls._balance(nodo.der) > 0:
                assert nodo.der is not None
                nodo.der = cls._rotar_derecha(nodo.der)
            return cls._rotar_izquierda(nodo)
        return nodo

    @classmethod
    def _insertar_nodo(cls, nodo: Optional[_NodoAVL], mision: Mision, clave: Tuple[int, int, int]) -> _NodoAVL:
        if nodo is None:
            return _NodoAVL(mision)
        if clave < nodo.clave:
            nodo.izq = cls._insertar_nodo(nodo.izq, mision, clave)
        else:
            nodo.der = cls._insertar_nodo(nodo.der, mision, clave)
        return cls._rebalancear(nodo)

    @classmethod
    def _minimo_nodo(cls, nodo: _NodoAVL) -> _NodoAVL:
        actual = nodo
        while actual.izq is not None:
            actual = actual.izq
        return actual

    @classmethod
    def _eliminar_nodo(cls, nodo: Optional[_NodoAVL], clave: Tuple[int, int, int]) -> Optional[_NodoAVL]:
        if nodo is None:
            return None
        if clave < nodo.clave:
            nodo.izq = cls._eliminar_nodo(nodo.izq, clave)
        elif clave > nodo.clave:
            nodo.der = cls._eliminar_nodo(nodo.der, clave)
        else:
            if nodo.izq is None:
                return nodo.der
            if nodo.der is None:
                return nodo.izq
            sucesor = cls._minimo_nodo(nodo.der)
            nodo.clave = sucesor.clave
            nodo.mision = sucesor.mision
            nodo.der = cls._eliminar_nodo(nodo.der, sucesor.clave)
        return cls._rebalancear(nodo)

    def insertar(self, mision: Mision) -> None:
        copia = copiar_mision(mision)
        self._por_id[copia.id] = copia
        self._raiz = self._insertar_nodo(self._raiz, copia, clave_orden_prioridad(copia))

    def eliminar_por_id(self, id_mision: str) -> None:
        m = self._por_id.pop(id_mision, None)
        if m is None:
            return
        self._raiz = self._eliminar_nodo(self._raiz, clave_orden_prioridad(m))

    def actualizar_urgencia(self, id_mision: str, nueva_urgencia: int) -> None:
        m = self._por_id.get(id_mision)
        if m is None:
            return
        # En un árbol ordenado por prioridad, cambiar la clave exige borrar y reinsertar.
        self._raiz = self._eliminar_nodo(self._raiz, clave_orden_prioridad(m))
        m.urgencia = nueva_urgencia
        self._raiz = self._insertar_nodo(self._raiz, m, clave_orden_prioridad(m))

    def consultar_top_k(self, k: int) -> List[Mision]:
        """Recorrido in-order iterativo (de mayor a menor prioridad) hasta reunir k."""
        if k <= 0 or self._raiz is None:
            return []
        resultado: List[Mision] = []
        pila: List[_NodoAVL] = []
        actual: Optional[_NodoAVL] = self._raiz
        while (pila or actual is not None) and len(resultado) < k:
            while actual is not None:
                pila.append(actual)
                actual = actual.izq
            actual = pila.pop()
            resultado.append(actual.mision)
            actual = actual.der
        return resultado


# ============================================================================
# CANDIDATO ALTERNATIVO PARA OPERACIÓN 7: Dijkstra con matriz + búsqueda lineal
# ============================================================================

class _GrafoMatrizLineal:
    """
    Grafo ponderado representado con matriz de adyacencia V x V.
    Implementa Dijkstra buscando el mínimo por barrido lineal en O(V^2) sin heap.
    """

    def __init__(self, n: int) -> None:
        self._n = n
        self._inf = 10**12
        self._matriz: List[List[int]] = [[self._inf] * n for _ in range(n)]
        for i in range(n):
            self._matriz[i][i] = 0

    def agregar_camino(self, u: int, v: int, peso: int) -> None:
        if peso < self._matriz[u][v]:
            self._matriz[u][v] = peso
            self._matriz[v][u] = peso

    def dijkstra_costo(self, origen: int, destino: int) -> int:
        n = self._n
        inf = self._inf
        dist = [inf] * n
        visitado = [False] * n
        dist[origen] = 0

        for _ in range(n):
            u = -1
            mejor = inf
            for i in range(n):
                if not visitado[i] and dist[i] < mejor:
                    mejor = dist[i]
                    u = i
            if u == -1 or u == destino:
                break
            visitado[u] = True

            fila = self._matriz[u]
            du = dist[u]
            for v in range(n):
                peso = fila[v]
                if peso < inf:
                    nueva = du + peso
                    if nueva < dist[v]:
                        dist[v] = nueva

        return dist[destino]


# ============================================================================
# FUNCIONES DE MEDICIÓN Y EXPORTACIÓN A CSV
# ============================================================================

def generar_misiones_base(n: int, rng: random.Random) -> List[Mision]:
    misiones: List[Mision] = []
    for i in range(n):
        tipo = TipoMision.PRINCIPAL if (i % 4 == 0) else TipoMision.SECUNDARIA
        misiones.append(
            Mision(
                id=f"M_{i}",
                nombre=f"Mision {i}",
                tipo=tipo,
                urgencia=rng.randint(1, 10),
                ubicacion="Plaza",
                estado=EstadoMision.PENDIENTE,
                orden_llegada=i + 1,
            )
        )
    return misiones


def medir_operacion_top_k() -> List[Dict[str, object]]:
    """Mide Heap binario indexado vs Árbol AVL en dos escenarios y cuatro tamaños."""
    tamanos = [1000, 5000, 20000, 50000]
    filas: List[Dict[str, object]] = []

    print("\n--- Midiendo Operación 6: Heap binario indexado vs Árbol AVL ---")

    for n in tamanos:
        rng = random.Random(1000 + n)
        base = generar_misiones_base(n, rng)

        # Escenario A: 2 000 operaciones mixtas (80% cambiar urgencia, 10% alta/baja, 10% top-10).
        num_ops_a = 2000
        ops_a = []
        sig_id = n
        for step in range(num_ops_a):
            dado = rng.randrange(100)
            if dado < 80:
                ops_a.append(("upd", f"M_{rng.randrange(n)}", rng.randint(1, 10)))
            elif dado < 90:
                idx_reemplazo = rng.randrange(n)
                nuevo_id = f"M_NUEVA_{sig_id}"
                sig_id += 1
                nueva_m = Mision(
                    id=nuevo_id,
                    nombre="Extra",
                    tipo=TipoMision.PRINCIPAL,
                    urgencia=rng.randint(1, 10),
                    ubicacion="Plaza",
                    estado=EstadoMision.PENDIENTE,
                    orden_llegada=sig_id,
                )
                ops_a.append(("rep", f"M_{idx_reemplazo}", nueva_m))
            else:
                ops_a.append(("top", 10, None))

        tiempos_heap_a: List[float] = []
        tiempos_avl_a: List[float] = []

        for _ in range(REPETICIONES):
            # Preparar Heap fuera del cronómetro.
            heap = HeapMisiones()
            for m in base:
                heap.insertar(m)

            t0 = time.perf_counter()
            for tipo_op, arg1, arg2 in ops_a:
                if tipo_op == "upd":
                    heap.actualizar_urgencia(arg1, arg2)  # type: ignore[arg-type]
                elif tipo_op == "rep":
                    heap.eliminar_por_id(arg1)  # type: ignore[arg-type]
                    heap.insertar(arg2)  # type: ignore[arg-type]
                else:
                    heap.consultar_top_k(arg1)  # type: ignore[arg-type]
            tiempos_heap_a.append((time.perf_counter() - t0) * 1000.0)

            # Preparar AVL fuera del cronómetro.
            avl = _ArbolAVLPrioridad()
            for m in base:
                avl.insertar(m)

            t0 = time.perf_counter()
            for tipo_op, arg1, arg2 in ops_a:
                if tipo_op == "upd":
                    avl.actualizar_urgencia(arg1, arg2)  # type: ignore[arg-type]
                elif tipo_op == "rep":
                    avl.eliminar_por_id(arg1)  # type: ignore[arg-type]
                    avl.insertar(arg2)  # type: ignore[arg-type]
                else:
                    avl.consultar_top_k(arg1)  # type: ignore[arg-type]
            tiempos_avl_a.append((time.perf_counter() - t0) * 1000.0)

        for nombre_cand, tiempos in [
            ("Heap binario indexado", tiempos_heap_a),
            ("Arbol AVL ordenado", tiempos_avl_a),
        ]:
            filas.append(
                {
                    "escenario": "Actualizaciones_intensivas_k_pequeno",
                    "tamano_n": n,
                    "candidato": nombre_cand,
                    "repeticiones": REPETICIONES,
                    "promedio_ms": round(statistics.mean(tiempos), 3),
                    "mediana_ms": round(statistics.median(tiempos), 3),
                }
            )
        print(
            f"  Escenario A (n={n}): Heap={statistics.median(tiempos_heap_a):.2f} ms | "
            f"AVL={statistics.median(tiempos_avl_a):.2f} ms"
        )

        # Escenario B: 80 consultas seguidas de top-k grande (k = 500) sin actualizaciones.
        heap_b = HeapMisiones()
        avl_b = _ArbolAVLPrioridad()
        for m in base:
            heap_b.insertar(m)
            avl_b.insertar(m)

        tiempos_heap_b: List[float] = []
        tiempos_avl_b: List[float] = []
        num_consultas_b = 80
        k_grande = 500

        for _ in range(REPETICIONES):
            t0 = time.perf_counter()
            for _ in range(num_consultas_b):
                heap_b.consultar_top_k(k_grande)
            tiempos_heap_b.append((time.perf_counter() - t0) * 1000.0)

            t0 = time.perf_counter()
            for _ in range(num_consultas_b):
                avl_b.consultar_top_k(k_grande)
            tiempos_avl_b.append((time.perf_counter() - t0) * 1000.0)

        for nombre_cand, tiempos in [
            ("Heap binario indexado", tiempos_heap_b),
            ("Arbol AVL ordenado", tiempos_avl_b),
        ]:
            filas.append(
                {
                    "escenario": "Consultas_top_k_intensivas_k_grande",
                    "tamano_n": n,
                    "candidato": nombre_cand,
                    "repeticiones": REPETICIONES,
                    "promedio_ms": round(statistics.mean(tiempos), 3),
                    "mediana_ms": round(statistics.median(tiempos), 3),
                }
            )
        print(
            f"  Escenario B (n={n}): Heap={statistics.median(tiempos_heap_b):.2f} ms | "
            f"AVL={statistics.median(tiempos_avl_b):.2f} ms"
        )

    return filas


def medir_operacion_rutas() -> List[Dict[str, object]]:
    """Mide Dijkstra con listas+heap vs matriz+lineal en grafos dispersos y densos."""
    tamanos_v = [100, 250, 500, 1000]
    filas: List[Dict[str, object]] = []

    print("\n--- Midiendo Operación 7: Dijkstra Listas+Heap vs Matriz+Lineal ---")

    for v in tamanos_v:
        rng = random.Random(5000 + v)
        nombres = [f"N_{i}" for i in range(v)]

        # -------- Escenario A: Grafo disperso (E ≈ 3 * V aristas no dirigidas) --------
        grafo_lista_disp = GrafoCiudad()
        grafo_mat_disp = _GrafoMatrizLineal(v)
        for nom in nombres:
            grafo_lista_disp.agregar_ubicacion(nom)

        for i in range(v - 1):
            p = rng.randint(1, 50)
            grafo_lista_disp.agregar_camino(nombres[i], nombres[i + 1], p, True)
            grafo_mat_disp.agregar_camino(i, i + 1, p)
        for _ in range(2 * v):
            a = rng.randrange(v)
            b = rng.randrange(v)
            if a != b:
                p = rng.randint(1, 100)
                grafo_lista_disp.agregar_camino(nombres[a], nombres[b], p, True)
                grafo_mat_disp.agregar_camino(a, b, p)

        pares_disp = [(rng.randrange(v), rng.randrange(v)) for _ in range(10)]
        tiempos_lista_disp: List[float] = []
        tiempos_mat_disp: List[float] = []

        for _ in range(REPETICIONES):
            t0 = time.perf_counter()
            for u, dest in pares_disp:
                grafo_lista_disp.calcular_ruta_minima(nombres[u], nombres[dest])
            tiempos_lista_disp.append((time.perf_counter() - t0) * 1000.0)

            t0 = time.perf_counter()
            for u, dest in pares_disp:
                grafo_mat_disp.dijkstra_costo(u, dest)
            tiempos_mat_disp.append((time.perf_counter() - t0) * 1000.0)

        for nombre_cand, tiempos in [
            ("Dijkstra listas + heap", tiempos_lista_disp),
            ("Dijkstra matriz + lineal", tiempos_mat_disp),
        ]:
            filas.append(
                {
                    "escenario": "Grafo_disperso_ciudad",
                    "tamano_v": v,
                    "candidato": nombre_cand,
                    "repeticiones": REPETICIONES,
                    "promedio_ms": round(statistics.mean(tiempos), 3),
                    "mediana_ms": round(statistics.median(tiempos), 3),
                }
            )
        print(
            f"  Escenario A disperso (V={v}): Listas+Heap={statistics.median(tiempos_lista_disp):.2f} ms | "
            f"Matriz+Lineal={statistics.median(tiempos_mat_disp):.2f} ms"
        )

        # -------- Escenario B: Grafo denso (~85% de todos los pares conectados) --------
        grafo_lista_dens = GrafoCiudad()
        grafo_mat_dens = _GrafoMatrizLineal(v)
        for nom in nombres:
            grafo_lista_dens.agregar_ubicacion(nom)

        for i in range(v):
            for j in range(i + 1, v):
                if j == i + 1 or rng.random() < 0.85:
                    p = rng.randint(1, 100)
                    grafo_lista_dens.agregar_camino(nombres[i], nombres[j], p, True)
                    grafo_mat_dens.agregar_camino(i, j, p)

        pares_dens = [(rng.randrange(v), rng.randrange(v)) for _ in range(5)]
        tiempos_lista_dens: List[float] = []
        tiempos_mat_dens: List[float] = []

        for _ in range(REPETICIONES):
            t0 = time.perf_counter()
            for u, dest in pares_dens:
                grafo_lista_dens.calcular_ruta_minima(nombres[u], nombres[dest])
            tiempos_lista_dens.append((time.perf_counter() - t0) * 1000.0)

            t0 = time.perf_counter()
            for u, dest in pares_dens:
                grafo_mat_dens.dijkstra_costo(u, dest)
            tiempos_mat_dens.append((time.perf_counter() - t0) * 1000.0)

        for nombre_cand, tiempos in [
            ("Dijkstra listas + heap", tiempos_lista_dens),
            ("Dijkstra matriz + lineal", tiempos_mat_dens),
        ]:
            filas.append(
                {
                    "escenario": "Grafo_denso_teletransporte",
                    "tamano_v": v,
                    "candidato": nombre_cand,
                    "repeticiones": REPETICIONES,
                    "promedio_ms": round(statistics.mean(tiempos), 3),
                    "mediana_ms": round(statistics.median(tiempos), 3),
                }
            )
        print(
            f"  Escenario B denso    (V={v}): Listas+Heap={statistics.median(tiempos_lista_dens):.2f} ms | "
            f"Matriz+Lineal={statistics.median(tiempos_mat_dens):.2f} ms"
        )

    return filas


def guardar_csv(ruta: str, columnas: List[str], filas: List[Dict[str, object]]) -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def main() -> None:
    print("=== Iniciando mediciones empíricas del Motor de Misiones ===")
    filas_top_k = medir_operacion_top_k()
    filas_rutas = medir_operacion_rutas()

    ruta_top_k = os.path.join(DIR_RESULTADOS, "medicion_top_k.csv")
    ruta_rutas = os.path.join(DIR_RESULTADOS, "medicion_rutas.csv")

    guardar_csv(
        ruta_top_k,
        ["escenario", "tamano_n", "candidato", "repeticiones", "promedio_ms", "mediana_ms"],
        filas_top_k,
    )
    guardar_csv(
        ruta_rutas,
        ["escenario", "tamano_v", "candidato", "repeticiones", "promedio_ms", "mediana_ms"],
        filas_rutas,
    )

    print(f"\n[OK] Resultados guardados en:\n  - {ruta_top_k}\n  - {ruta_rutas}")


if __name__ == "__main__":
    main()
