"""
ARCHIVO: src/motor_lento.py
PROPÓSITO:
    Versión de referencia, intencionalmente simple: solo listas de Python y
    búsquedas lineales. Sirve de oráculo en las pruebas diferenciales.

    Es INDEPENDIENTE del motor rápido: reimplementa por su cuenta las
    validaciones, la regla de prioridad y el orden por título. Solo comparte
    con el motor rápido los tipos de datos (Libro, EstadoLibro, resultados)
    de libro.py, y NO usa TablaHash, HeapLibros, ListaEnlazada, EntradaHeap
    ni tiene_mayor_prioridad.
"""

from typing import List

from .libro import (
    EstadoLibro,
    Libro,
    ResultadoBusqueda,
    ResultadoLista,
    ResultadoOperacion,
    ResultadoSiguiente,
    copiar_libro,
)


class MotorBibliotecaLento:
    """Implementación lineal de referencia del motor de la biblioteca."""

    def __init__(self) -> None:
        self._libros: List[Libro] = []          # En orden de registro.
        self._terminados: List[str] = []        # IDs, el más reciente en la posición 0.
        self._contador: int = 0

    # ---------------- Utilidades internas ----------------

    def _indice(self, id_libro: object) -> int:
        """Búsqueda lineal. -1 si no existe o si el ID no es un texto no vacío."""
        if not isinstance(id_libro, str) or id_libro == "":
            return -1
        for i in range(len(self._libros)):
            if self._libros[i].id == id_libro:
                return i
        return -1

    @staticmethod
    def _prioridad_ok(p: object) -> bool:
        if isinstance(p, bool) or not isinstance(p, int):
            return False
        return p >= 1 and p <= 10

    @staticmethod
    def _texto_ok(t: object) -> bool:
        return isinstance(t, str) and t != ""

    # ---------------- Auxiliares ----------------

    def existe_libro(self, id_libro: str) -> bool:
        return self._indice(id_libro) != -1

    def contar_libros(self) -> int:
        return len(self._libros)

    def contar_pendientes(self) -> int:
        return sum(1 for l in self._libros if l.estado == EstadoLibro.PENDIENTE)

    def contar_terminados(self) -> int:
        return len(self._terminados)

    def listar_coleccion(self) -> List[Libro]:
        return [copiar_libro(l) for l in self._libros]

    # ---------------- Las 8 operaciones ----------------

    def registrar_libro(self, id_libro: str, titulo: str, autor: str) -> ResultadoOperacion:
        if not (self._texto_ok(id_libro) and self._texto_ok(titulo) and self._texto_ok(autor)):
            return ResultadoOperacion(False, "Datos inválidos.")
        if self._indice(id_libro) != -1:
            return ResultadoOperacion(False, "ID repetido.")
        self._libros.append(Libro(id_libro, titulo, autor, EstadoLibro.REGISTRADO))
        return ResultadoOperacion(True, "Registrado.")

    def buscar_libro(self, id_libro: str) -> ResultadoBusqueda:
        i = self._indice(id_libro)
        if i == -1:
            return ResultadoBusqueda(False, None, "No existe.")
        return ResultadoBusqueda(True, copiar_libro(self._libros[i]), "Encontrado.")

    def anadir_a_pendientes(self, id_libro: str, prioridad: int) -> ResultadoOperacion:
        if not self._prioridad_ok(prioridad):
            return ResultadoOperacion(False, "Prioridad inválida.")
        i = self._indice(id_libro)
        if i == -1:
            return ResultadoOperacion(False, "No existe.")
        if self._libros[i].estado != EstadoLibro.REGISTRADO:
            return ResultadoOperacion(False, "Estado no permitido.")
        self._contador += 1
        self._libros[i].estado = EstadoLibro.PENDIENTE
        self._libros[i].prioridad = prioridad
        self._libros[i].orden_pendiente = self._contador
        return ResultadoOperacion(True, "Añadido.")

    def cambiar_prioridad(self, id_libro: str, nueva_prioridad: int) -> ResultadoOperacion:
        if not self._prioridad_ok(nueva_prioridad):
            return ResultadoOperacion(False, "Prioridad inválida.")
        i = self._indice(id_libro)
        if i == -1:
            return ResultadoOperacion(False, "No existe.")
        if self._libros[i].estado != EstadoLibro.PENDIENTE:
            return ResultadoOperacion(False, "No está pendiente.")
        self._libros[i].prioridad = nueva_prioridad
        return ResultadoOperacion(True, "Actualizada.")

    def elegir_siguiente_libro(self) -> ResultadoSiguiente:
        mejor = -1
        for i in range(len(self._libros)):
            l = self._libros[i]
            if l.estado != EstadoLibro.PENDIENTE:
                continue
            if mejor == -1:
                mejor = i
                continue
            m = self._libros[mejor]
            # Regla propia: mayor prioridad; si empatan, el que llegó antes.
            if l.prioridad > m.prioridad or (
                l.prioridad == m.prioridad and l.orden_pendiente < m.orden_pendiente
            ):
                mejor = i
        if mejor == -1:
            return ResultadoSiguiente(False, None, "No hay pendientes.")
        self._libros[mejor].estado = EstadoLibro.EN_LECTURA
        return ResultadoSiguiente(True, copiar_libro(self._libros[mejor]), "Elegido.")

    def marcar_como_terminado(self, id_libro: str) -> ResultadoOperacion:
        i = self._indice(id_libro)
        if i == -1:
            return ResultadoOperacion(False, "No existe.")
        e = self._libros[i].estado
        if e != EstadoLibro.EN_LECTURA and e != EstadoLibro.PENDIENTE:
            return ResultadoOperacion(False, "Estado no permitido.")
        self._libros[i].estado = EstadoLibro.TERMINADO
        self._terminados.insert(0, id_libro)
        return ResultadoOperacion(True, "Terminado.")

    def mostrar_lecturas_recientes(self, k: int) -> ResultadoLista:
        if isinstance(k, bool) or not isinstance(k, int):
            return ResultadoLista(False, [], "k inválido.")
        if k < 0:
            return ResultadoLista(False, [], "k negativo.")
        salida: List[Libro] = []
        for pos in range(len(self._terminados)):
            if len(salida) >= k:
                break
            salida.append(copiar_libro(self._libros[self._indice(self._terminados[pos])]))
        return ResultadoLista(True, salida, "Listo.")

    def listar_coleccion_por_titulo(self) -> ResultadoLista:
        # Ordenamiento por inserción escrito a mano (clave: título sin mayúsculas, luego ID).
        copia = [copiar_libro(l) for l in self._libros]
        for i in range(1, len(copia)):
            actual = copia[i]
            j = i - 1
            while j >= 0 and self._va_despues(copia[j], actual):
                copia[j + 1] = copia[j]
                j -= 1
            copia[j + 1] = actual
        return ResultadoLista(True, copia, "Listo.")

    def eliminar_libro(self, id_libro: str) -> ResultadoOperacion:
        i = self._indice(id_libro)
        if i == -1:
            return ResultadoOperacion(False, "No existe.")
        if self._libros[i].estado == EstadoLibro.TERMINADO:
            for pos in range(len(self._terminados)):
                if self._terminados[pos] == id_libro:
                    del self._terminados[pos]
                    break
        del self._libros[i]
        return ResultadoOperacion(True, "Eliminado.")

    @staticmethod
    def _va_despues(a: Libro, b: Libro) -> bool:
        """True si 'a' debe ir DESPUÉS de 'b' en el orden por título."""
        ta = a.titulo.casefold()
        tb = b.titulo.casefold()
        if ta != tb:
            return ta > tb
        return a.id > b.id
