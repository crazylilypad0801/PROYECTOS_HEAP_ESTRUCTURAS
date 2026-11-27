"""
ARCHIVO: src/mision.py
PROPÓSITO:
    Define los tipos de datos fundamentales del dominio de misiones de un
    videojuego: enumeraciones de tipo y estado, la clase Mision, la regla
    oficial de prioridad y las estructuras de respuesta de las 7 operaciones.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

# Rango válido permitido para el nivel de urgencia de cualquier misión.
URGENCIA_MIN: int = 1
URGENCIA_MAX: int = 10


class TipoMision(Enum):
    """
    Clasificación narrativa de la misión dentro del videojuego.
    En caso de empate en urgencia, PRINCIPAL (valor 1) vence a SECUNDARIA (valor 0).
    """

    SECUNDARIA = 0
    PRINCIPAL = 1


class EstadoMision(Enum):
    """
    Ciclo de vida de una misión dentro del motor:
    - PENDIENTE: registrada y esperando atención (vive tanto en TablaHash como en HeapMisiones).
    - EN_CURSO: retirada del heap al ser entregada al jugador; permanece consultable en TablaHash.
    - CANCELADA: retirada del heap por cancelación; sus datos históricos permanecen en TablaHash.
    """

    PENDIENTE = "Pendiente"
    EN_CURSO = "En curso"
    CANCELADA = "Cancelada"


@dataclass
class Mision:
    """
    Representa una misión individual administrada por el motor.
    """

    id: str                  # Identificador único de la misión (clave principal).
    nombre: str              # Título descriptivo visible para el jugador.
    tipo: TipoMision         # PRINCIPAL o SECUNDARIA.
    urgencia: int            # Entero en el rango [URGENCIA_MIN, URGENCIA_MAX].
    ubicacion: str           # Nombre del vértice en el grafo donde ocurre la misión.
    estado: EstadoMision     # Estado actual del ciclo de vida.
    orden_llegada: int       # Número entero secuencial (menor = se registró antes).


def copiar_mision(mision: Mision) -> Mision:
    """
    Crea una copia independiente de una instancia de Mision.
    Se usa al devolver resultados para evitar que el código externo modifique
    por accidente los objetos almacenados dentro de las estructuras internas.
    """
    return Mision(
        id=mision.id,
        nombre=mision.nombre,
        tipo=mision.tipo,
        urgencia=mision.urgencia,
        ubicacion=mision.ubicacion,
        estado=mision.estado,
        orden_llegada=mision.orden_llegada,
    )


def tiene_mayor_prioridad(a: Mision, b: Mision) -> bool:
    """
    Determina si la misión 'a' tiene ESTRICTAMENTE mayor prioridad que 'b'.

    Regla de desempate en cascada del sistema:
        1. Gana la misión con mayor urgencia numérica.
        2. Si empatan en urgencia, gana la misión PRINCIPAL sobre la SECUNDARIA.
        3. Si el empate continúa, gana la misión que llegó antes (menor orden_llegada).
    """
    if a.urgencia != b.urgencia:
        return a.urgencia > b.urgencia
    if a.tipo != b.tipo:
        return a.tipo.value > b.tipo.value
    return a.orden_llegada < b.orden_llegada


def clave_orden_prioridad(mision: Mision) -> Tuple[int, int, int]:
    """
    Devuelve una tupla comparable en orden ascendente donde las misiones de
    mayor prioridad producen tuplas MÁS PEQUEÑAS (útil para ordenar con sort()
    o en árboles balanceados que ordenan de menor a mayor).
    """
    return (-mision.urgencia, -mision.tipo.value, mision.orden_llegada)


def misiones_son_iguales(a: Mision, b: Mision) -> bool:
    """
    Compara campo por campo dos misiones. Se usa en la verificación de
    invariantes globales y en la comparación diferencial frente al motor lento.
    """
    return (
        a.id == b.id
        and a.nombre == b.nombre
        and a.tipo == b.tipo
        and a.urgencia == b.urgencia
        and a.ubicacion == b.ubicacion
        and a.estado == b.estado
        and a.orden_llegada == b.orden_llegada
    )


@dataclass
class ResultadoOperacion:
    """Respuesta estándar para operaciones que crean o modifican una misión."""

    exito: bool
    mensaje: str


@dataclass
class ResultadoBusqueda:
    """Respuesta de la operación 2 (Buscar misión por identificador)."""

    encontrada: bool
    mision: Optional[Mision] = None
    mensaje: str = ""


@dataclass
class ResultadoSiguiente:
    """Respuesta de la operación 5 (Obtener siguiente misión de mayor prioridad)."""

    disponible: bool
    mision: Optional[Mision] = None
    mensaje: str = ""


@dataclass
class ResultadoTopK:
    """Respuesta de la operación 6 (Consultar las primeras k misiones pendientes)."""

    exito: bool
    misiones: List[Mision] = field(default_factory=list)
    mensaje: str = ""


@dataclass
class ResultadoRuta:
    """Respuesta de la operación 7 (Calcular ruta óptima hacia una misión)."""

    existe: bool
    camino: List[str] = field(default_factory=list)
    costo_total: int = 0
    mensaje: str = ""
