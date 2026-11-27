"""
ARCHIVO: benchmarks/graficar.py
PROPÓSITO:
    Lee los archivos CSV generados por benchmarks/mediciones.py y produce
    un gráfico comparativo PNG por cada operación medida (con dos paneles,
    uno por escenario) utilizando matplotlib.
"""

import csv
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

DIR_RESULTADOS = os.path.join(os.path.dirname(__file__), "resultados")


def cargar_datos(
    ruta_csv: str, columna_tamano: str
) -> Dict[str, Dict[str, List[Tuple[int, float]]]]:
    """Agrupa pares (tamaño, mediana_ms) por escenario y por candidato."""
    datos: Dict[str, Dict[str, List[Tuple[int, float]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    with open(ruta_csv, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            esc = fila["escenario"]
            cand = fila["candidato"]
            tam = int(fila[columna_tamano])
            mediana = float(fila["mediana_ms"])
            datos[esc][cand].append((tam, mediana))

    for esc in datos:
        for cand in datos[esc]:
            datos[esc][cand].sort(key=lambda par: par[0])
    return datos


def graficar_operacion(
    ruta_csv: str,
    ruta_salida: str,
    columna_tamano: str,
    etiqueta_x: str,
    titulo_general: str,
    escenarios: List[Tuple[str, str]],
) -> None:
    """Genera una figura con dos subgráficos lado a lado y la guarda en PNG."""
    datos = cargar_datos(ruta_csv, columna_tamano)
    fig, ejes = plt.subplots(1, 2, figsize=(12.5, 5.2), dpi=150)

    colores = ["#1f77b4", "#d62728"]
    marcadores = ["o", "s"]

    for idx_panel, (clave_esc, titulo_panel) in enumerate(escenarios):
        ax = ejes[idx_panel]
        series = datos[clave_esc]

        for idx_cand, (nombre_cand, puntos) in enumerate(series.items()):
            xs = [p[0] for p in puntos]
            ys = [p[1] for p in puntos]
            ax.plot(
                xs,
                ys,
                marker=marcadores[idx_cand % len(marcadores)],
                linewidth=2.2,
                markersize=6.5,
                color=colores[idx_cand % len(colores)],
                label=nombre_cand,
            )
            # Anotar valores sobre los puntos (alternando arriba/abajo para evitar solapamiento).
            desplazamiento_y = 8 if idx_cand == 0 else -14
            for x_val, y_val in zip(xs, ys):
                ax.annotate(
                    f"{y_val:.1f}",
                    (x_val, y_val),
                    textcoords="offset points",
                    xytext=(0, desplazamiento_y),
                    ha="center",
                    fontsize=8,
                    color=colores[idx_cand % len(colores)],
                )

        ax.set_title(titulo_panel, fontsize=11, fontweight="bold")
        ax.set_xlabel(etiqueta_x, fontsize=10)
        ax.set_ylabel("Tiempo mediano (ms)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.45)
        ax.legend(loc="best", fontsize=9)

    fig.suptitle(titulo_general, fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(ruta_salida)
    plt.close(fig)
    print(f"[OK] Gráfico generado: {ruta_salida}")


def main() -> None:
    os.makedirs(DIR_RESULTADOS, exist_ok=True)

    graficar_operacion(
        ruta_csv=os.path.join(DIR_RESULTADOS, "medicion_top_k.csv"),
        ruta_salida=os.path.join(DIR_RESULTADOS, "grafico_top_k.png"),
        columna_tamano="tamano_n",
        etiqueta_x="Cantidad de misiones pendientes (n)",
        titulo_general="Operación 6 (Top-k y actualizaciones): Heap binario indexado vs Árbol AVL",
        escenarios=[
            (
                "Actualizaciones_intensivas_k_pequeno",
                "Escenario A: 2000 ops mixtas (80% urgencia, 10% top-10)",
            ),
            (
                "Consultas_top_k_intensivas_k_grande",
                "Escenario B: 80 consultas top-500 (sin cambios)",
            ),
        ],
    )

    graficar_operacion(
        ruta_csv=os.path.join(DIR_RESULTADOS, "medicion_rutas.csv"),
        ruta_salida=os.path.join(DIR_RESULTADOS, "grafico_rutas.png"),
        columna_tamano="tamano_v",
        etiqueta_x="Cantidad de ubicaciones en el grafo (V)",
        titulo_general="Operación 7 (Dijkstra): Listas + Heap vs Matriz + Selección lineal",
        escenarios=[
            (
                "Grafo_disperso_ciudad",
                "Escenario A: Grafo disperso (E ≈ 3V, 10 consultas)",
            ),
            (
                "Grafo_denso_teletransporte",
                "Escenario B: Grafo denso (85% aristas, 5 consultas)",
            ),
        ],
    )


if __name__ == "__main__":
    main()
