# Guía de defensa — Biblioteca personal (CMP3002)

Esta guía es para estudiar. **No va dentro del zip de entrega** (no es parte del paquete). Cada integrante debe poder responder **sola**, sin que las otras completen. Se puede responder con una tabla, una traza o un dibujo. Si algo falta en el paquete, se dice; no se inventa una prueba ni una medición.

Los números salen de las corridas reales (`benchmarks/resultados/mediciones_op7.csv`, `mediciones_op4.csv` y `tests/pruebas.py`). Si vuelven a medir, los números cambian un poco: usen los suyos.

---

## Las 4 preguntas

### 1. Una decisión: qué candidatos compararon, cuál eligieron y en qué escenario gana el otro

**Ejemplo con la cola de pendientes (operaciones 3, 4 y 5).**
- **Candidatos:** heap indexado propio (un árbol guardado en un arreglo, más una tabla hash `id → posición`) contra un arreglo ordenado con `bisect` (operaciones 3 y 4, la 4 medida) y contra un arreglo sin ordenar que recorre todo para encontrar el mejor (operación 5, solo análisis).
- **Elegimos:** el heap.
- **Dónde gana el otro:** con pocos pendientes. Lo medimos en cambiar prioridad: con 1 000 pendientes, el arreglo ordenado tarda 0.98 µs y el heap 6.5 µs. En elegir siguiente, el arreglo ordenado le gana al heap en teoría (sacar el último es O(1)), y el arreglo sin ordenar gana solo con muy pocos pendientes; eso es análisis, no medición.
- **Dónde gana el heap:** cambiar prioridad con colas grandes. Medido: con 50 000 pendientes, heap 7.2 µs contra arreglo 13.2 µs; el cruce está cerca de 20 000.
- **Por qué lo elegimos igual:** garantiza O(log p) en las tres operaciones de la cola. No medimos el costo total de la cola, así que no podemos afirmar con datos que sea la opción más rápida en conjunto.

**Otro ejemplo: lecturas recientes (operaciones 6 y 7).** Lista enlazada (insertar en la cabeza) contra `list` con `append` leída desde el final. La lista gana en el peor caso por operación (nunca copia el arreglo) y contra insertar al inicio de un array (`insert(0, x)`, que es O(n)). Gana el array con `append` en tiempo real medido.

### 2. Por qué el motor es correcto y cuánto cuesta

**Propiedad de una estructura propia (heap).** Ningún nodo tiene mayor prioridad que su padre; además, la posición guardada en la tabla hash para el ID de `_datos[i]` es siempre `i`, y el arreglo y la tabla tienen el mismo tamaño. `verificar_invariante()` lo comprueba.

**Propiedad de la tabla hash.** El factor de carga nunca pasa de 0.75; cada clave está en la cubeta que dicta su hash; no hay claves repetidas; la suma de las cubetas es la cantidad.

**Una prueba difícil.** La prueba diferencial: 12 000 operaciones aleatorias (con IDs inexistentes, entradas inválidas, eliminar y reutilizar IDs) en el motor rápido y en el lento, comparando cada respuesta y los invariantes cada 250 pasos. Y los 7 mutantes: rompimos el motor a propósito y la prueba detectó los 7.

**Tiempo y espacio de una operación (ejemplo: cambiar prioridad).** Buscar el libro en la tabla hash es O(1) esperado; buscar su posición en el heap por la tabla de posiciones es O(1) esperado; subir o bajar la entrada es O(log p) en el peor caso, con p = pendientes. Espacio extra O(1). En total O(log p).

**Traza corta para dibujar (heap de 3 libros).** Pendientes A(5, orden 1), B(9, orden 2), C(5, orden 3). El heap tiene B en la raíz. Cambiar C a prioridad 10: C sube al lado de B, intercambia con su padre y queda en la raíz. `elegir siguiente` devuelve C. Si A y C empatan en prioridad, sale A, porque llegó antes.

### 3. Una medición: qué midieron, en qué unidad y si confirma su análisis

**Operación 7 (lecturas recientes).**
- **Qué:** el tiempo de pedir los k libros terminados más recientes, con la lista enlazada propia y con una `list` de Python.
- **Unidad:** microsegundos por consulta. 7 repeticiones, tamaños de 1 000 a 50 000 terminados, k = 5 y k = 500.
- **Resultado:** las líneas son planas al crecer el tamaño (el costo depende de k, no de n): *confirma* el análisis O(k). Pero la `list` es unas 6 veces más rápida con k = 5 y unas 40 con k = 500: eso *contradice* que la lista enlazada tuviera alguna ventaja práctica. La razón es que recortar una `list` lo hace código en C, y recorrer la lista salta nodo por nodo en Python. Es la diferencia de constantes.

**Operación 4 (cambiar prioridad).**
- **Qué:** el tiempo de cambiar la prioridad, heap contra arreglo con `bisect`, en dos mezclas (45/10/45 y 15/70/15 de añadir, cambiar y elegir), con 1 000 a 50 000 pendientes.
- **Resultado:** *confirma* el análisis: el arreglo crece casi lineal (1 a 13 µs), el heap casi plano (4 a 7 µs), y se cruzan cerca de los 20 000 pendientes.

### 4. Qué no demuestran sus pruebas y sus mediciones

- Las pruebas coinciden con el motor lento en 12 000 operaciones con una semilla; no prueban todos los casos.
- Los dos motores comparten tipos y reglas escritos por el mismo equipo: un malentendido común no se vería.
- Los mutantes son solo 7, los que se nos ocurrieron.
- Pocos pendientes a la vez en la prueba aleatoria (0 a 14) y prioridades solo de 1 a 10.
- Las mediciones son de una sola computadora y Python 3.10.12, con datos sintéticos y hasta 50 000 libros.
- Se midieron las estructuras sueltas, no el motor completo.
- No se midió espacio, ni eliminar libro, ni la operación 8; el AVL no está implementado (solo análisis teórico).

---

## Guion de presentación (unos 10 minutos)

1. **La app (1 min):** biblioteca personal; qué guarda y qué responde; los 4 estados.
2. **El diseño (2 min):** dibujo de las 4 estructuras (tabla hash, array, heap, lista) y la regla de que los datos viven una sola vez en la tabla hash.
3. **Una decisión difícil (2 min):** la cola de pendientes, heap contra arreglo ordenado.
4. **Una medición que nos sorprendió (3 min):** la `list` de Python le gana a nuestra lista enlazada (unas 6 veces con k = 5 y unas 40 con k = 500), aunque ambas cuestan O(k); y el heap solo le gana al arreglo en cambiar prioridad con colas grandes.
5. **Cómo sabemos que funciona (1 min):** correr `python tests/pruebas.py` y mostrar la línea final.
6. **Lo que falta (1 min):** lo de la pregunta 4.

---

## Lo que falta o es débil (decirlo si lo preguntan)

- Las operaciones 3, 4 y 5 comparten la estructura elegida (el heap), y las 6 y 7 comparten el mismo par.
- Contra el arreglo ordenado, la operación 5 la gana el arreglo en teoría; el heap solo le gana al arreglo sin ordenar. La operación 5 no se midió.
- No medimos el costo total de la cola de pendientes (añadir, cambiar y elegir juntos).
- La operación 2 tiene una ventaja de constante para el array ordenado.
- El AVL de la operación 8 es teórico; no está implementado ni medido.
- El equipo es de tres integrantes y los lineamientos hablan de grupos de dos: hay que confirmarlo con el profesor.
