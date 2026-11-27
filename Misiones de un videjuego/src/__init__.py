"""
Paquete principal del Motor de Misiones de un Videojuego.

Expone las clases y tipos de datos principales para registrar, consultar,
priorizar y calcular rutas hacia misiones utilizando estructuras implementadas
desde cero en Python: TablaHash, HeapMisiones y GrafoCiudad.
"""

from .mision import (
    URGENCIA_MIN,
    URGENCIA_MAX,
    TipoMision,
    EstadoMision,
    Mision,
    ResultadoOperacion,
    ResultadoBusqueda,
    ResultadoSiguiente,
    ResultadoTopK,
    ResultadoRuta,
    tiene_mayor_prioridad,
    clave_orden_prioridad,
    copiar_mision,
    misiones_son_iguales,
)
from .tabla_hash import TablaHash
from .heap_misiones import HeapMisiones
from .grafo_ciudad import GrafoCiudad
from .motor_misiones import MotorMisiones
from .motor_lento import MotorMisionesLento

__all__ = [
    "URGENCIA_MIN",
    "URGENCIA_MAX",
    "TipoMision",
    "EstadoMision",
    "Mision",
    "ResultadoOperacion",
    "ResultadoBusqueda",
    "ResultadoSiguiente",
    "ResultadoTopK",
    "ResultadoRuta",
    "tiene_mayor_prioridad",
    "clave_orden_prioridad",
    "copiar_mision",
    "misiones_son_iguales",
    "TablaHash",
    "HeapMisiones",
    "GrafoCiudad",
    "MotorMisiones",
    "MotorMisionesLento",
]
