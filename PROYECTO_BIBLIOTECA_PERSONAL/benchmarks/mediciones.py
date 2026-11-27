"""
ARCHIVO: benchmarks/mediciones.py
PROPÓSITO:
    Mide el tiempo real de DOS operaciones, cada una con sus dos candidatos
    implementados (el candidato que no se eligió usa estructuras del lenguaje):

      Operación 7 (Mostrar lecturas recientes):
          ListaEnlazada propia (elegida)  vs  list de Python con append y lectura al revés.
      Operación 4 (Cambiar prioridad):
          HeapLibros propio con índice id->posición (elegido)
          vs  list de Python ordenada con bisect + diccionario id->clave.

    Unidad: microsegundos (µs) por operación durante la medición; los CSV guardan
    milisegundos (ms). Cada punto se repite varias veces y el CSV guarda una fila por
    escenario, tamaño y candidato con el promedio y la mediana de las repeticiones. Antes de medir, se comprueba que ambos
    candidatos dan las MISMAS respuestas (si no, el script se detiene).

    Uso:
        python benchmarks/mediciones.py            # medición completa
        python benchmarks/mediciones.py --rapido   # versión corta para probar
"""

import bisect
import csv
import gc
import os
import platform
import random
import sys
import time

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from src.heap_libros import HeapLibros
from src.lista_enlazada import ListaEnlazada

SEMILLA = 2026
DIR_RESULTADOS = os.path.join(RAIZ_PROYECTO, "benchmarks", "resultados")

COMPLETO = {"tamanos": [1000, 5000, 20000, 50000], "repeticiones": 7,
            "consultas_op7": 2000, "ops_op4": 3000}
RAPIDO = {"tamanos": [200, 1000, 2000, 4000], "repeticiones": 3,
          "consultas_op7": 300, "ops_op4": 600}



# ------------------------------------------------------------ Operación 7

def medir_op7(cfg: dict) -> list:
    """
    Escenarios (forma de la consulta):
      'k=5'   : el lector mira sus 5 últimas lecturas.
      'k=500' : el lector repasa su historial (500 últimas, o todas si hay menos).
    El tamaño es la cantidad de libros terminados.
    """
    filas = []
    for k_texto, k in (("k=5", 5), ("k=500", 500)):
        for n in cfg["tamanos"]:
            ids = [f"L{i}" for i in range(n)]
            # Verificación previa: mismas respuestas.
            lista = ListaEnlazada()
            arreglo = []
            for i in ids:
                lista.insertar_al_inicio(i)
                arreglo.append(i)
            esperado = arreglo[:-k - 1:-1] if k > 0 else []
            assert lista.primeros_k(k) == esperado, "Las respuestas de op. 7 no coinciden"

            for rep in range(cfg["repeticiones"]):
                q = cfg["consultas_op7"]
                gc.collect()
                gc.disable()
                t0 = time.perf_counter_ns()
                for _ in range(q):
                    lista.primeros_k(k)
                t_lista = time.perf_counter_ns() - t0
                t0 = time.perf_counter_ns()
                for _ in range(q):
                    arreglo[:-k - 1:-1]
                t_arreglo = time.perf_counter_ns() - t0
                gc.enable()
                filas.append(("op7_lecturas_recientes", k_texto, "lista_enlazada", n, rep, t_lista / q / 1000))
                filas.append(("op7_lecturas_recientes", k_texto, "list_python", n, rep, t_arreglo / q / 1000))
    return filas


# ------------------------------------------------------------ Operación 4

class ArregloOrdenado:
    """Candidato NO elegido: list ordenada con bisect + diccionario id -> clave."""

    def __init__(self) -> None:
        self._a = []        # Tuplas (prioridad, -orden, id) en orden ascendente; el mejor va al final.
        self._clave = {}    # id -> (prioridad, -orden)

    def insertar(self, id_libro, prioridad, orden):
        self._clave[id_libro] = (prioridad, -orden)
        bisect.insort(self._a, (prioridad, -orden, id_libro))

    def actualizar_prioridad(self, id_libro, nueva):
        p, no = self._clave[id_libro]
        i = bisect.bisect_left(self._a, (p, no, id_libro))
        del self._a[i]
        self._clave[id_libro] = (nueva, no)
        bisect.insort(self._a, (nueva, no, id_libro))

    def extraer_maximo(self):
        p, no, id_libro = self._a.pop()
        del self._clave[id_libro]
        return id_libro


ESCENARIOS_OP4 = {
    # nombre: (% añadir, % cambiar prioridad, % elegir siguiente)
    "lector_casual": (45, 10, 45),
    "muchos_cambios": (15, 70, 15),
}


def generar_operaciones(n: int, m: int, mezcla: tuple, rng: random.Random):
    """
    Genera (cola inicial, lista de operaciones, ids esperados al elegir) usando el
    candidato de arreglo como modelo. Así las operaciones 'cambiar' siempre apuntan
    a libros pendientes de verdad.
    """
    modelo = ArregloOrdenado()
    inicial = []
    pool, pos = [], {}

    def alta(id_libro):
        pos[id_libro] = len(pool)
        pool.append(id_libro)

    def baja(id_libro):
        i = pos.pop(id_libro)
        ultimo = pool.pop()
        if i < len(pool):
            pool[i] = ultimo
            pos[ultimo] = i

    orden = 0
    for i in range(n):
        orden += 1
        p = rng.randint(1, 10)
        inicial.append((f"I{i}", p, orden))
        modelo.insertar(f"I{i}", p, orden)
        alta(f"I{i}")

    ops, esperados = [], []
    nuevo = 0
    pa, pc, _ = mezcla
    for _ in range(m):
        d = rng.randrange(100)
        if d < pa or not pool:
            nuevo += 1
            orden += 1
            id_libro, p = f"N{nuevo}", rng.randint(1, 10)
            ops.append(("add", id_libro, p, orden))
            modelo.insertar(id_libro, p, orden)
            alta(id_libro)
        elif d < pa + pc:
            id_libro, p = rng.choice(pool), rng.randint(1, 10)
            ops.append(("chg", id_libro, p, 0))
            modelo.actualizar_prioridad(id_libro, p)
        else:
            ops.append(("pop", "", 0, 0))
            elegido = modelo.extraer_maximo()
            esperados.append(elegido)
            baja(elegido)
    return inicial, ops, esperados


def ejecutar(estructura, inicial, ops, medir: bool):
    """Aplica las operaciones. Si medir, devuelve ns acumulados por tipo y ops por tipo."""
    for id_libro, p, orden in inicial:
        estructura.insertar(id_libro, p, orden)
    elegidos = []
    tiempo = {"add": 0, "chg": 0, "pop": 0}
    cuenta = {"add": 0, "chg": 0, "pop": 0}
    reloj = time.perf_counter_ns
    for tipo, id_libro, p, orden in ops:
        t0 = reloj()
        if tipo == "add":
            estructura.insertar(id_libro, p, orden)
        elif tipo == "chg":
            estructura.actualizar_prioridad(id_libro, p)
        else:
            r = estructura.extraer_maximo()
            elegidos.append(r if isinstance(r, str) else r.id)
        tiempo[tipo] += reloj() - t0
        cuenta[tipo] += 1
    return tiempo, cuenta, elegidos


def medir_op4(cfg: dict) -> list:
    """
    Escenarios (mezcla de operaciones), medido SOLO el tiempo de 'cambiar prioridad':
      lector_casual  : 45% añadir, 10% cambiar prioridad, 45% elegir.
      muchos_cambios : 15% añadir, 70% cambiar prioridad, 15% elegir.
    El tamaño es la cantidad de libros pendientes al empezar.
    """
    filas = []
    for nombre, mezcla in ESCENARIOS_OP4.items():
        for n in cfg["tamanos"]:
            rng = random.Random(f"{SEMILLA}-{nombre}-{n}")
            inicial, ops, esperados = generar_operaciones(n, cfg["ops_op4"], mezcla, rng)
            candidatos = {"heap_propio": HeapLibros, "arreglo_bisect": ArregloOrdenado}
            for nombre_cand, fabrica in candidatos.items():       # Verificación previa.
                _, _, elegidos = ejecutar(fabrica(), inicial, ops, False)
                assert elegidos == esperados, f"Respuestas distintas en {nombre_cand}/{nombre}/{n}"
            for rep in range(cfg["repeticiones"]):
                for nombre_cand, fabrica in candidatos.items():
                    gc.collect()
                    gc.disable()
                    tiempo, cuenta, _ = ejecutar(fabrica(), inicial, ops, True)
                    gc.enable()
                    for tipo, op in (("chg", "op4_cambiar_prioridad"),):
                        if cuenta[tipo]:
                            filas.append((op, nombre, nombre_cand, n, rep,
                                          tiempo[tipo] / cuenta[tipo] / 1000))
    return filas


def escribir_resumen(ruta: str, filas: list, op_principal: str) -> None:
    """
    Guarda UNA fila por escenario, tamaño y candidato, solo para la operación medida
    (op_principal). Columnas: escenario, tamano_v, candidato, repeticiones,
    promedio_ms, mediana_ms. Los tiempos se guardan en milisegundos por operación.
    """
    import statistics
    grupos = {}
    orden = []
    for op, esc, cand, n, rep, valor_us in filas:
        if op != op_principal:
            continue
        clave = (esc, n, cand)
        if clave not in grupos:
            grupos[clave] = []
            orden.append(clave)
        grupos[clave].append(valor_us / 1000.0)           # µs -> ms
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["escenario", "tamano_v", "candidato", "repeticiones", "promedio_ms", "mediana_ms"])
        for (esc, n, cand) in orden:
            v = grupos[(esc, n, cand)]
            w.writerow([esc, n, cand, len(v), f"{statistics.mean(v):.7f}", f"{statistics.median(v):.7f}"])


def guardar_todo(filas7: list, filas4: list, sufijo: str) -> None:
    escribir_resumen(os.path.join(DIR_RESULTADOS, f"mediciones_op7{sufijo}.csv"), filas7, "op7_lecturas_recientes")
    escribir_resumen(os.path.join(DIR_RESULTADOS, f"mediciones_op4{sufijo}.csv"), filas4, "op4_cambiar_prioridad")


def main() -> None:
    cfg = RAPIDO if "--rapido" in sys.argv else COMPLETO
    os.makedirs(DIR_RESULTADOS, exist_ok=True)
    sufijo = "_rapido" if "--rapido" in sys.argv else ""
    print("Configuración:", cfg)
    filas7 = medir_op7(cfg)
    print("Operación 7 medida.")
    filas4 = medir_op4(cfg)
    print("Operación 4 medida.")
    guardar_todo(filas7, filas4, sufijo)
    with open(os.path.join(DIR_RESULTADOS, f"entorno{sufijo}.txt"), "w", encoding="utf-8") as f:
        f.write(f"Python {platform.python_version()} en {platform.platform()}\n")
        f.write(f"Semilla: {SEMILLA}\nConfiguración: {cfg}\n")
        f.write("CSV: escenario, tamano_v, candidato, repeticiones, promedio_ms, mediana_ms.\n")
    print("Resultados guardados en", DIR_RESULTADOS)


if __name__ == "__main__":
    main()
