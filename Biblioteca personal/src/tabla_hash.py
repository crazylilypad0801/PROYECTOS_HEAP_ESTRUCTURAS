"""
ARCHIVO: src/tabla_hash.py
FAMILIA DE ESTRUCTURA: Hashing (estructura propia #1).
PROPÓSITO:
    Tabla hash genérica con encadenamiento separado y crecimiento dinámico
    (rehash) cuando el factor de carga superaría 0.75. Se usa para:
      - guardar cada libro por su ID (id -> Libro), y
      - llevar las posiciones dentro del heap (id -> índice).

    No usa dict de Python: se programan explícitamente la función hash FNV-1a
    de 64 bits para cadenas, las cubetas, el rehash y verificar_invariante().

PROPIEDAD QUE SIEMPRE CUMPLE (invariante de representación):
    1. len(_cubetas) == _capacidad > 0.
    2. factor de carga <= 0.75.
    3. la suma de longitudes de las cubetas == _cantidad.
    4. cada clave está en la cubeta que dicta su hash.
    5. no hay claves repetidas.
"""

from typing import Generic, List, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


def _hash_propio(clave: object) -> int:
    """
    Código hash entero no negativo, determinista y sin usar hash() de Python.
    - str: FNV-1a de 64 bits sobre los bytes UTF-8.
    - int: mezcla de bits estilo SplitMix64.
    - bool y otros tipos: TypeError (True y 1 no deben confundirse como claves).
    """
    mascara_64 = 0xFFFFFFFFFFFFFFFF
    if isinstance(clave, bool):
        raise TypeError("TablaHash no admite claves bool")
    if isinstance(clave, str):
        valor_hash = 14695981039346656037  # Base FNV-1a de 64 bits.
        primo_fnv = 1099511628211          # Primo FNV de 64 bits.
        for byte in clave.encode("utf-8"):
            valor_hash ^= byte
            valor_hash = (valor_hash * primo_fnv) & mascara_64
        return valor_hash
    if isinstance(clave, int):
        x = clave & mascara_64
        x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & mascara_64
        x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & mascara_64
        return x ^ (x >> 31)
    raise TypeError(f"Tipo de clave no soportado por TablaHash: {type(clave).__name__}")


class TablaHash(Generic[K, V]):
    """Tabla hash con encadenamiento separado y duplicación de cubetas."""

    CAPACIDAD_INICIAL: int = 16
    FACTOR_CARGA_MAXIMO: float = 0.75

    def __init__(self, capacidad_inicial: int = CAPACIDAD_INICIAL) -> None:
        cap = capacidad_inicial if capacidad_inicial > 0 else self.CAPACIDAD_INICIAL
        self._capacidad: int = cap
        self._cantidad: int = 0
        # Cada cubeta es una lista de entradas [clave, valor].
        self._cubetas: List[List[List[object]]] = [[] for _ in range(cap)]

    def _calcular_indice(self, clave: K, capacidad: int) -> int:
        return _hash_propio(clave) % capacidad

    def _rehash(self, nueva_capacidad: int) -> None:
        """Reubica todas las entradas en 'nueva_capacidad' cubetas. Costo O(n)."""
        nuevas: List[List[List[object]]] = [[] for _ in range(nueva_capacidad)]
        for cubeta in self._cubetas:
            for entrada in cubeta:
                nuevas[self._calcular_indice(entrada[0], nueva_capacidad)].append(entrada)  # type: ignore[arg-type]
        self._cubetas = nuevas
        self._capacidad = nueva_capacidad

    def insertar_o_actualizar(self, clave: K, valor: V) -> bool:
        """
        Inserta (clave, valor); si la clave existía, solo actualiza su valor.
        Devuelve True si la clave era nueva. O(1) esperado, amortizado por el rehash.
        """
        idx = self._calcular_indice(clave, self._capacidad)
        cubeta = self._cubetas[idx]
        for entrada in cubeta:
            if entrada[0] == clave:
                entrada[1] = valor
                return False

        if (self._cantidad + 1) / self._capacidad > self.FACTOR_CARGA_MAXIMO:
            self._rehash(self._capacidad * 2)
            idx = self._calcular_indice(clave, self._capacidad)
            cubeta = self._cubetas[idx]

        cubeta.append([clave, valor])
        self._cantidad += 1
        return True

    def obtener(self, clave: K) -> Optional[V]:
        """Valor asociado a la clave, o None. O(1) esperado, O(n) en el peor caso."""
        idx = self._calcular_indice(clave, self._capacidad)
        for entrada in self._cubetas[idx]:
            if entrada[0] == clave:
                return entrada[1]  # type: ignore[return-value]
        return None

    def contiene(self, clave: K) -> bool:
        """Indica si la clave existe. O(1) esperado."""
        idx = self._calcular_indice(clave, self._capacidad)
        for entrada in self._cubetas[idx]:
            if entrada[0] == clave:
                return True
        return False

    def eliminar(self, clave: K) -> bool:
        """Elimina la clave si existe. Devuelve True si la borró. O(1) esperado."""
        idx = self._calcular_indice(clave, self._capacidad)
        cubeta = self._cubetas[idx]
        for i, entrada in enumerate(cubeta):
            if entrada[0] == clave:
                cubeta.pop(i)
                self._cantidad -= 1
                return True
        return False

    def tamano(self) -> int:
        return self._cantidad

    def capacidad(self) -> int:
        return self._capacidad

    def vacia(self) -> bool:
        return self._cantidad == 0

    def factor_carga(self) -> float:
        return self._cantidad / self._capacidad

    def claves(self) -> List[K]:
        """Lista con todas las claves almacenadas. O(capacidad + n)."""
        resultado: List[K] = []
        for cubeta in self._cubetas:
            for entrada in cubeta:
                resultado.append(entrada[0])  # type: ignore[arg-type]
        return resultado

    def verificar_invariante(self) -> bool:
        """Comprueba las 5 propiedades descritas en el docstring del módulo."""
        if self._capacidad <= 0 or len(self._cubetas) != self._capacidad:
            return False
        if self.factor_carga() > self.FACTOR_CARGA_MAXIMO + 1e-9:
            return False

        conteo_real = 0
        for indice_cubeta, cubeta in enumerate(self._cubetas):
            vistas = []
            for entrada in cubeta:
                conteo_real += 1
                clave = entrada[0]
                if self._calcular_indice(clave, self._capacidad) != indice_cubeta:
                    return False
                if clave in vistas:
                    return False
                vistas.append(clave)

        return conteo_real == self._cantidad
