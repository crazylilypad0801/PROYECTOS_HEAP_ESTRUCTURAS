# Motor de la Biblioteca personal (CMP3002 — Estructuras de Datos)

Motor en **Python 3** de una biblioteca personal: registra libros, los busca por ID, lleva una lista de pendientes con prioridad, elige qué leer a continuación, guarda las lecturas recientes y lista la colección por título. No hay pantallas: lo que se construye es el motor (guarda datos y responde operaciones).

Usa estructuras de tres familias distintas:

- **Hashing:** `TablaHash` propia, con encadenamiento separado, hash FNV-1a de 64 bits para texto y rehash cuando el factor de carga pasa de 0.75 (`src/tabla_hash.py`). Guarda cada libro por su ID.
- **Árboles:** `HeapLibros` propio, un heap máximo binario indexado con una `TablaHash` de posiciones (`src/heap_libros.py`). Guarda los libros pendientes.
- **Secuencias:** `ListaEnlazada` simple propia (`src/lista_enlazada.py`) para las lecturas recientes, y una `list` de Python como array con la colección en orden de registro.

## Estructura del proyecto

- `src/`: tipos del dominio (`libro.py`), las tres estructuras propias, `MotorBiblioteca` (`motor_biblioteca.py`) y `MotorBibliotecaLento` (`motor_lento.py`, versión de referencia con listas simples).
- `tests/pruebas.py`: pruebas unitarias, casos borde, invariantes, comparación diferencial de 12 000 operaciones al azar contra el motor lento y prueba de 7 mutantes.
- `benchmarks/mediciones.py`: mediciones de la operación 7 (lecturas recientes) y la operación 4 (cambiar prioridad).
- `benchmarks/graficar.py`: dibuja una gráfica por operación medida.
- `benchmarks/resultados/`: `mediciones_op7.csv` y `mediciones_op4.csv` (una fila por escenario, tamaño y candidato, con las columnas `escenario, tamano_v, candidato, repeticiones, promedio_ms, mediana_ms`; tiempos en milisegundos), `entorno.txt` y las gráficas `.png`.
- `informe.md`: informe técnico (pasos 1 a 6, lo que las pruebas y mediciones no demuestran, y herramientas usadas).
- `FLUJO_DEL_CODIGO.md`: explicación del flujo interno del código y de las operaciones.
- `DECISIONES.md`: registro de decisiones del equipo.

## Requisitos

- Python 3.10 o superior (probado con Python 3.10.12).
- `matplotlib` solo para dibujar las gráficas con `benchmarks/graficar.py` (probado con 3.10.9). Las pruebas y las mediciones usan solo la biblioteca estándar.

## Comandos

Ejecutar desde la raíz del proyecto:

1. **Correr las pruebas** (unitarias, casos borde, invariantes, 12 000 operaciones aleatorias contra el motor lento y los mutantes):
   ```bash
   python tests/pruebas.py
   ```
   Debe terminar con la línea `TODAS LAS PRUEBAS PASARON`.

2. **Repetir las mediciones** (reescribe los dos `mediciones_op*.csv`; tarda cerca de 20 segundos):
   ```bash
   python benchmarks/mediciones.py
   ```
   Para una prueba corta: `python benchmarks/mediciones.py --rapido`.

3. **Volver a dibujar las gráficas** a partir del `.csv`:
   ```bash
   python benchmarks/graficar.py
   ```

> **Windows:** si el alias `python` no apunta a su instalación real, indiquen la ruta completa del intérprete, por ejemplo `& "C:\Ruta\a\python.exe" tests/pruebas.py`.

## Notas

- Los tiempos medidos dependen del computador; los de `resultados/` se midieron en una sola máquina (ver `entorno.txt`). Al repetirlos saldrán valores distintos, pero la forma de las curvas debe parecerse.
- La carpeta `__pycache__` la crea Python al ejecutar; no forma parte del código.
