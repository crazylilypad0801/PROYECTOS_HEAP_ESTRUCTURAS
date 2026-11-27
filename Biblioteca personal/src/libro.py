"""
ARCHIVO: src/libro.py
PROPÓSITO:
    Define los tipos de datos del dominio de la Biblioteca personal: el estado
    de un libro, la clase Libro, la entrada que guarda el heap de pendientes,
    la regla oficial de prioridad y las respuestas de las operaciones.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# Rango válido de la prioridad que la persona asigna a un libro pendiente.
PRIORIDAD_MIN: int = 1
PRIORIDAD_MAX: int = 10


class EstadoLibro(Enum):
    """
    Ciclo de vida de un libro dentro del motor:
    - REGISTRADO: está en la colección, pero aún no es una próxima lectura.
    - PENDIENTE: está en el heap de próximas lecturas con una prioridad.
    - EN_LECTURA: fue elegido como siguiente libro y la persona lo está leyendo.
    - TERMINADO: ya se leyó; aparece en la lista de lecturas recientes.
    """

    REGISTRADO = "Registrado"
    PENDIENTE = "Pendiente"
    EN_LECTURA = "En lectura"
    TERMINADO = "Terminado"


@dataclass
class Libro:
    """Un libro de la colección personal."""

    id: str                      # Identificador único (clave principal).
    titulo: str
    autor: str
    estado: EstadoLibro
    prioridad: int = 0           # 0 = sin prioridad; si es pendiente, está en [1, 10].
    orden_pendiente: int = 0     # Reloj lógico de cuándo se añadió a pendientes (0 = nunca).


def copiar_libro(libro: Libro) -> Libro:
    """
    Copia independiente de un Libro. Se usa al devolver resultados para que el
    código externo no pueda modificar los objetos guardados dentro del motor.
    """
    return Libro(
        id=libro.id,
        titulo=libro.titulo,
        autor=libro.autor,
        estado=libro.estado,
        prioridad=libro.prioridad,
        orden_pendiente=libro.orden_pendiente,
    )


def libros_son_iguales(a: Libro, b: Libro) -> bool:
    """Compara campo por campo dos libros (pruebas y comparación con el motor lento)."""
    return (
        a.id == b.id
        and a.titulo == b.titulo
        and a.autor == b.autor
        and a.estado == b.estado
        and a.prioridad == b.prioridad
        and a.orden_pendiente == b.orden_pendiente
    )


class EntradaHeap:
    """
    Lo que guarda el heap por cada libro pendiente: solo su ID, su prioridad y
    su orden de llegada a pendientes. No guarda copias del libro completo, así
    el heap no tiene datos duplicados que puedan desincronizarse de la tabla hash.
    """

    __slots__ = ("id", "prioridad", "orden")

    def __init__(self, id_libro: str, prioridad: int, orden: int) -> None:
        self.id = id_libro
        self.prioridad = prioridad
        self.orden = orden


def tiene_mayor_prioridad(a: EntradaHeap, b: EntradaHeap) -> bool:
    """
    Determina si 'a' tiene ESTRICTAMENTE mayor prioridad que 'b'.

    Regla de desempate del sistema:
        1. Gana la entrada con mayor prioridad numérica.
        2. Si empatan, gana la que se añadió antes a pendientes (menor orden).
    """
    if a.prioridad != b.prioridad:
        return a.prioridad > b.prioridad
    return a.orden < b.orden


@dataclass
class ResultadoOperacion:
    """Respuesta estándar para las operaciones que crean o modifican un libro."""

    exito: bool
    mensaje: str


@dataclass
class ResultadoBusqueda:
    """Respuesta de la operación 2 (Buscar libro)."""

    encontrado: bool
    libro: Optional[Libro] = None
    mensaje: str = ""


@dataclass
class ResultadoSiguiente:
    """Respuesta de la operación 5 (Elegir siguiente libro)."""

    disponible: bool
    libro: Optional[Libro] = None
    mensaje: str = ""


@dataclass
class ResultadoLista:
    """
    Respuesta de las operaciones que devuelven varios libros: la operación 7
    (Mostrar lecturas recientes) y la operación 8 (Listar colección por título).
    """

    exito: bool
    libros: List[Libro] = field(default_factory=list)
    mensaje: str = ""
