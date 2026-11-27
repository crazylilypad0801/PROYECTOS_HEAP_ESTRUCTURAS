# Motor de Misiones de un Videojuego (CMP3002 — Estructuras de Datos)

Implementación en **Python 3** del motor de gestión de misiones de un videojuego. Administra el registro de misiones, decide cuál atender primero según prioridad (`urgencia` $\rightarrow$ `tipo` $\rightarrow$ `orden de llegada`) y calcula rutas de menor costo sobre el mapa de la ciudad utilizando tres estructuras implementadas desde cero de tres familias distintas:

- **Hashing**: `TablaHash` con encadenamiento separado, función hash FNV-1a de 64 bits y *rehash* dinámico (`src/tabla_hash.py`).
- **Árboles**: `HeapMisiones` como Max-Heap binario indexado con diccionario de posiciones (`src/heap_misiones.py`).
- **Grafos**: `GrafoCiudad` con listas de adyacencia y Dijkstra con Min-Heap binario propio (`src/grafo_ciudad.py`).

## Estructura del proyecto

- `src/`: módulos del dominio, estructuras propias, `MotorMisiones` y `MotorMisionesLento`.
- `tests/pruebas.py`: pruebas unitarias, casos borde, verificación de invariantes y comparación diferencial de 12 000 operaciones al azar contra el motor lento.
- `benchmarks/mediciones.py`: mediciones empíricas de rendimiento para las operaciones 6 y 7.
- `benchmarks/graficar.py`: generación de gráficos comparativos en PNG a partir de los CSV.
- `benchmarks/resultados/`: archivos `.csv` y gráficos `.png` generados.
- `FLUJO_DEL_CODIGO.md`: explicación detallada del flujo interno del código y las 7 operaciones.
- `informe.tex`: informe técnico completo en LaTeX simple.

## Requisitos

- Python 3.10 o superior (probado en Python 3.15.0).
- `matplotlib` (únicamente para regenerar los gráficos desde `benchmarks/graficar.py`).

## Comandos para ejecutar pruebas y mediciones

Ejecutar desde la raíz del repositorio:

1. **Correr toda la suite de pruebas (unitarias, casos borde, invariantes y 12 000 operaciones aleatorias):**
   ```bash
   python tests/pruebas.py
   ```

2. **Repetir las mediciones empíricas (genera los archivos `.csv` en `benchmarks/resultados/`):**
   ```bash
   python benchmarks/mediciones.py
   ```

3. **Regenerar los gráficos comparativos `.png` a partir de los `.csv`:**
   ```bash
   python benchmarks/graficar.py
   ```

> **Nota en Windows:** si el alias `python` de `Microsoft\WindowsApps` no apunta a tu instalación real de Python, ejecuta los comandos anteriores indicando la ruta de tu intérprete (por ejemplo: `& "C:\Users\ASUS\AppData\Local\Python\bin\python.exe" tests/pruebas.py`).
