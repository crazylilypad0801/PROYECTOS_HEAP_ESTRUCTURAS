"""
ARCHIVO: src/motor_biblioteca.py
PROPÓSITO:
    Coordina las estructuras del motor de la Biblioteca personal:
      1. TablaHash (Hashing): fuente maestra de los libros (id -> Libro).
      2. Array (list de Python, Secuencias): la colección, en orden de registro.
      3. HeapLibros (Árboles): solo los libros PENDIENTE, por prioridad.
      4. ListaEnlazada (Secuencias): IDs de los libros TERMINADO, el más
         reciente primero.

    REGLA DE SINCRONIZACIÓN:
      - La tabla hash y el array apuntan al MISMO objeto Libro (no hay copias).
      - El heap guarda solo (id, prioridad, orden); la lista enlazada, solo IDs.
      - Los PENDIENTE son exactamente los libros del heap, y los TERMINADO son
        exactamente los de la lista enlazada.
"""

from typing import List

from .heap_libros import HeapLibros
from .libro import (
    PRIORIDAD_MAX,
    PRIORIDAD_MIN,
    EstadoLibro,
    Libro,
    ResultadoBusqueda,
    ResultadoLista,
    ResultadoOperacion,
    ResultadoSiguiente,
    copiar_libro,
)
from .lista_enlazada import ListaEnlazada
from .tabla_hash import TablaHash


def _texto_valido(valor: object) -> bool:
    """True si 'valor' es un str no vacío."""
    return isinstance(valor, str) and len(valor) > 0


def _prioridad_valida(valor: object) -> bool:
    """True si 'valor' es un int (no bool) dentro de [PRIORIDAD_MIN, PRIORIDAD_MAX]."""
    return (
        isinstance(valor, int)
        and not isinstance(valor, bool)
        and PRIORIDAD_MIN <= valor <= PRIORIDAD_MAX
    )


def _clave_titulo(libro: Libro) -> tuple:
    """Clave de orden de la operación 8: título sin distinguir mayúsculas, luego ID."""
    return (libro.titulo.casefold(), libro.id)


class MotorBiblioteca:
    """Motor principal: guarda libros, lleva pendientes y lecturas recientes."""

    def __init__(self) -> None:
        self._libros: TablaHash[str, Libro] = TablaHash()
        self._coleccion: List[Libro] = []
        self._pendientes: HeapLibros = HeapLibros()
        self._recientes: ListaEnlazada = ListaEnlazada()
        self._contador_pendientes: int = 0  # Reloj lógico para el desempate por llegada.

    # ---------------- Operaciones auxiliares simples (no se analizan) ----------------

    def existe_libro(self, id_libro: str) -> bool:
        return _texto_valido(id_libro) and self._libros.contiene(id_libro)

    def contar_libros(self) -> int:
        return len(self._coleccion)

    def contar_pendientes(self) -> int:
        return self._pendientes.tamano()

    def contar_terminados(self) -> int:
        return self._recientes.tamano()

    def listar_coleccion(self) -> List[Libro]:
        """Recorre el array y devuelve copias en orden de registro. O(n)."""
        return [copiar_libro(l) for l in self._coleccion]

    # ---------------- Las 8 operaciones ----------------

    def registrar_libro(self, id_libro: str, titulo: str, autor: str) -> ResultadoOperacion:
        """
        Operación 1: Registrar libro.
        - Entradas: ID, título y autor (str no vacíos).
        - Cambios: inserta el libro (estado REGISTRADO) en la tabla hash y en el array.
        - Casos borde: rechaza campos vacíos o que no sean texto, y un ID repetido.
        """
        if not (_texto_valido(id_libro) and _texto_valido(titulo) and _texto_valido(autor)):
            return ResultadoOperacion(False, "El ID, el título y el autor deben ser texto no vacío.")
        if self._libros.contiene(id_libro):
            return ResultadoOperacion(False, f"Ya existe un libro con el ID '{id_libro}'.")

        libro = Libro(id=id_libro, titulo=titulo, autor=autor, estado=EstadoLibro.REGISTRADO)
        self._libros.insertar_o_actualizar(id_libro, libro)
        self._coleccion.append(libro)
        return ResultadoOperacion(True, f"Libro '{id_libro}' registrado.")

    def buscar_libro(self, id_libro: str) -> ResultadoBusqueda:
        """
        Operación 2: Buscar libro.
        - Cambios: ninguno (solo lectura en la tabla hash).
        - Casos borde: ID vacío, que no sea texto o inexistente -> no encontrado.
        """
        if not _texto_valido(id_libro):
            return ResultadoBusqueda(False, None, "El ID de búsqueda no es válido.")
        libro = self._libros.obtener(id_libro)
        if libro is None:
            return ResultadoBusqueda(False, None, f"No existe un libro con el ID '{id_libro}'.")
        return ResultadoBusqueda(True, copiar_libro(libro), "Libro encontrado.")

    def anadir_a_pendientes(self, id_libro: str, prioridad: int) -> ResultadoOperacion:
        """
        Operación 3: Añadir a pendientes.
        - Cambios: el libro pasa a PENDIENTE y se inserta en el heap.
        - Casos borde: prioridad inválida; ID inexistente; libro que ya estaba
          pendiente (no se duplica) o que está EN_LECTURA o TERMINADO.
        """
        if not _prioridad_valida(prioridad):
            return ResultadoOperacion(False, "La prioridad debe ser un entero entre 1 y 10.")
        libro = self._libros.obtener(id_libro) if _texto_valido(id_libro) else None
        if libro is None:
            return ResultadoOperacion(False, f"No existe un libro con el ID '{id_libro}'.")
        if libro.estado == EstadoLibro.PENDIENTE:
            return ResultadoOperacion(False, "El libro ya está en pendientes.")
        if libro.estado != EstadoLibro.REGISTRADO:
            return ResultadoOperacion(False, "Solo se pueden añadir a pendientes libros registrados.")

        self._contador_pendientes += 1
        libro.estado = EstadoLibro.PENDIENTE
        libro.prioridad = prioridad
        libro.orden_pendiente = self._contador_pendientes
        self._pendientes.insertar(libro.id, prioridad, self._contador_pendientes)
        return ResultadoOperacion(True, f"Libro '{id_libro}' añadido a pendientes.")

    def cambiar_prioridad(self, id_libro: str, nueva_prioridad: int) -> ResultadoOperacion:
        """
        Operación 4: Cambiar prioridad.
        - Cambios: actualiza la prioridad en el libro y reubica la entrada en el heap.
        - Casos borde: prioridad inválida, ID inexistente o libro que no está pendiente.
        """
        if not _prioridad_valida(nueva_prioridad):
            return ResultadoOperacion(False, "La prioridad debe ser un entero entre 1 y 10.")
        libro = self._libros.obtener(id_libro) if _texto_valido(id_libro) else None
        if libro is None:
            return ResultadoOperacion(False, f"No existe un libro con el ID '{id_libro}'.")
        if libro.estado != EstadoLibro.PENDIENTE:
            return ResultadoOperacion(False, "Solo se puede cambiar la prioridad de libros pendientes.")

        libro.prioridad = nueva_prioridad
        self._pendientes.actualizar_prioridad(id_libro, nueva_prioridad)
        return ResultadoOperacion(True, f"Prioridad del libro '{id_libro}' actualizada.")

    def elegir_siguiente_libro(self) -> ResultadoSiguiente:
        """
        Operación 5: Elegir siguiente libro.
        - Cambios: extrae el de mayor prioridad del heap y lo pasa a EN_LECTURA.
        - Casos borde: si no hay pendientes, devuelve disponible=False.
        """
        entrada = self._pendientes.extraer_maximo()
        if entrada is None:
            return ResultadoSiguiente(False, None, "No hay libros pendientes.")
        libro = self._libros.obtener(entrada.id)
        libro.estado = EstadoLibro.EN_LECTURA
        return ResultadoSiguiente(True, copiar_libro(libro), f"Libro '{libro.id}' elegido.")

    def marcar_como_terminado(self, id_libro: str) -> ResultadoOperacion:
        """
        Operación 6: Marcar como terminado.
        - Cambios: estado TERMINADO; si estaba pendiente sale del heap; el ID se
          inserta al inicio de la lista de lecturas recientes.
        - Casos borde: ID inexistente; libro REGISTRADO o ya TERMINADO.
        """
        libro = self._libros.obtener(id_libro) if _texto_valido(id_libro) else None
        if libro is None:
            return ResultadoOperacion(False, f"No existe un libro con el ID '{id_libro}'.")
        if libro.estado not in (EstadoLibro.EN_LECTURA, EstadoLibro.PENDIENTE):
            return ResultadoOperacion(
                False, "Solo se puede terminar un libro que esté en lectura o pendiente."
            )

        if libro.estado == EstadoLibro.PENDIENTE:
            self._pendientes.eliminar_por_id(id_libro)
        libro.estado = EstadoLibro.TERMINADO
        self._recientes.insertar_al_inicio(id_libro)
        return ResultadoOperacion(True, f"Libro '{id_libro}' marcado como terminado.")

    def mostrar_lecturas_recientes(self, k: int) -> ResultadoLista:
        """
        Operación 7: Mostrar lecturas recientes.
        - Cambios: ninguno (recorre desde la cabeza sin modificar la lista).
        - Casos borde: k no entero o negativo se rechaza; k = 0 devuelve vacío;
          k mayor que los terminados devuelve los que haya.
        """
        if isinstance(k, bool) or not isinstance(k, int):
            return ResultadoLista(False, [], "k debe ser un número entero.")
        if k < 0:
            return ResultadoLista(False, [], "k no puede ser negativo.")
        libros = [copiar_libro(self._libros.obtener(i)) for i in self._recientes.primeros_k(k)]
        return ResultadoLista(True, libros, "Consulta de lecturas recientes completada.")

    def listar_coleccion_por_titulo(self) -> ResultadoLista:
        """
        Operación 8: Listar la colección ordenada por título.
        - Cambios: ninguno. Ordena una copia del array (título sin distinguir
          mayúsculas, ID como desempate). O(n log n).
        - Casos borde: colección vacía devuelve lista vacía.
        """
        ordenados = sorted(self._coleccion, key=_clave_titulo)
        return ResultadoLista(True, [copiar_libro(l) for l in ordenados], "Colección ordenada por título.")

    def eliminar_libro(self, id_libro: str) -> ResultadoOperacion:
        """
        Operación auxiliar: Eliminar libro (no entra al análisis de las 8 que cuentan).
        - Cambios: quita el libro de la tabla hash y del array; si estaba PENDIENTE
          sale del heap; si estaba TERMINADO sale de la lista de recientes.
        - Costo: O(n) por el array y, si estaba terminado, por la lista simple.
        - Casos borde: ID inválido o inexistente. El ID queda libre para registrarse de nuevo.
        """
        libro = self._libros.obtener(id_libro) if _texto_valido(id_libro) else None
        if libro is None:
            return ResultadoOperacion(False, f"No existe un libro con el ID '{id_libro}'.")

        if libro.estado == EstadoLibro.PENDIENTE:
            self._pendientes.eliminar_por_id(id_libro)
        elif libro.estado == EstadoLibro.TERMINADO:
            self._recientes.eliminar(id_libro)
        for i in range(len(self._coleccion)):
            if self._coleccion[i] is libro:
                del self._coleccion[i]
                break
        self._libros.eliminar(id_libro)
        return ResultadoOperacion(True, f"Libro '{id_libro}' eliminado.")

    # ---------------- Verificación de invariantes ----------------

    def verificar_invariantes(self) -> bool:
        """
        Verifica los invariantes de cada estructura y el invariante global:
          - El array y la tabla hash contienen los mismos libros (mismo objeto), una vez cada uno.
          - Los PENDIENTE son exactamente los del heap, con la misma prioridad y orden.
          - Los TERMINADO son exactamente los IDs de la lista enlazada, sin repetir.
          - Ningún REGISTRADO ni EN_LECTURA está en el heap ni en la lista.
        """
        if not (
            self._libros.verificar_invariante()
            and self._pendientes.verificar_invariante()
            and self._recientes.verificar_invariante()
        ):
            return False

        if len(self._coleccion) != self._libros.tamano():
            return False
        vistos = set()
        for libro in self._coleccion:
            if libro.id in vistos or self._libros.obtener(libro.id) is not libro:
                return False
            vistos.add(libro.id)

        ids_lista = self._recientes.todos()
        if len(set(ids_lista)) != len(ids_lista):
            return False
        pendientes_en_tabla = 0
        terminados_en_tabla = 0
        for libro in self._coleccion:
            en_heap = self._pendientes.contiene(libro.id)
            en_lista = libro.id in ids_lista
            if libro.estado == EstadoLibro.PENDIENTE:
                pendientes_en_tabla += 1
                entrada = self._pendientes.obtener_entrada(libro.id)
                if (
                    entrada is None
                    or entrada.prioridad != libro.prioridad
                    or entrada.orden != libro.orden_pendiente
                    or en_lista
                ):
                    return False
            elif libro.estado == EstadoLibro.TERMINADO:
                terminados_en_tabla += 1
                if en_heap or not en_lista:
                    return False
            else:
                if en_heap or en_lista:
                    return False
        return (
            pendientes_en_tabla == self._pendientes.tamano()
            and terminados_en_tabla == self._recientes.tamano()
        )
