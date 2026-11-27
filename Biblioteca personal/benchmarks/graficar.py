"""
ARCHIVO: benchmarks/graficar.py
PROPÓSITO:
    Lee los CSV resumidos de benchmarks/resultados (mediciones_op7.csv y mediciones_op4.csv) y dibuja UNA gráfica por operación medida con la mediana de las
    repeticiones. Ejes en escala log-log.
    Uso: python benchmarks/graficar.py [--rapido]
"""

import csv
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIR = os.path.join(RAIZ, "benchmarks", "resultados")
SUF = "_rapido" if "--rapido" in sys.argv else ""

TITULOS = {
    "op7_lecturas_recientes": "Operación 7: Mostrar lecturas recientes",
    "op4_cambiar_prioridad": "Operación 4: Cambiar prioridad",
}
UNIDAD_X = {
    "op7_lecturas_recientes": "Libros terminados en la colección",
    "op4_cambiar_prioridad": "Libros pendientes al empezar",
}
ESTILOS = {  # candidato -> (color, marcador)
    "lista_enlazada": ("#1f77b4", "o"), "list_python": ("#d62728", "s"),
    "heap_propio": ("#1f77b4", "o"), "arreglo_bisect": ("#d62728", "s"),
}
LINEA = ["-", "--"]


def cargar(operacion: str) -> dict:
    """Devuelve {(escenario, candidato): [(tamano, mediana_ms), ...]}."""
    ruta = os.path.join(DIR, f"mediciones_{operacion.split('_')[0]}{SUF}.csv")
    series = defaultdict(list)
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            series[(fila["escenario"], fila["candidato"])].append(
                (int(fila["tamano_v"]), float(fila["mediana_ms"])))
    return series


def main() -> None:
    for op, titulo in TITULOS.items():
        series = cargar(op)
        fig, ax = plt.subplots(figsize=(8, 5.2))
        escenarios = sorted({k[0] for k in series})
        for ie, esc in enumerate(escenarios):
            for cand in sorted({k[1] for k in series if k[0] == esc}):
                puntos = sorted(series[(esc, cand)])
                color, marca = ESTILOS[cand]
                ax.plot([p[0] for p in puntos], [p[1] for p in puntos], color=color, marker=marca,
                        linestyle=LINEA[ie % 2], label=f"{cand} — {esc}")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(UNIDAD_X[op])
        ax.set_ylabel("Tiempo por operación (ms)")
        ax.set_title(titulo + "\n(mediana de las repeticiones)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        ruta = os.path.join(DIR, f"{op}{SUF}.png")
        fig.savefig(ruta, dpi=140)
        plt.close(fig)
        print("Gráfica guardada:", ruta)


if __name__ == "__main__":
    main()
