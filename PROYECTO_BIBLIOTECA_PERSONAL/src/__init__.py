"""
Paquete principal del Motor de la Biblioteca personal (CMP3002).

Expone los tipos de datos y las tres estructuras implementadas desde cero:
TablaHash (Hashing), HeapLibros (Árboles) y ListaEnlazada (Secuencias).
MotorBiblioteca los integra y MotorBibliotecaLento es la versión de referencia.
"""

from .libro import (
    PRIORIDAD_MIN,
    PRIORIDAD_MAX,
    EstadoLibro,
    Libro,
    EntradaHeap,
    ResultadoOperacion,
    ResultadoBusqueda,
    ResultadoSiguiente,
    ResultadoLista,
    tiene_mayor_prioridad,
    copiar_libro,
    libros_son_iguales,
)
from .tabla_hash import TablaHash
from .lista_enlazada import ListaEnlazada
from .heap_libros import HeapLibros
from .motor_biblioteca import MotorBiblioteca
from .motor_lento import MotorBibliotecaLento

__all__ = [
    "PRIORIDAD_MIN",
    "PRIORIDAD_MAX",
    "EstadoLibro",
    "Libro",
    "EntradaHeap",
    "ResultadoOperacion",
    "ResultadoBusqueda",
    "ResultadoSiguiente",
    "ResultadoLista",
    "tiene_mayor_prioridad",
    "copiar_libro",
    "libros_son_iguales",
    "TablaHash",
    "ListaEnlazada",
    "HeapLibros",
    "MotorBiblioteca",
    "MotorBibliotecaLento",
]
