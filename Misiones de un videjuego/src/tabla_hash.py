"""
ARCHIVO: src/tabla_hash.py
FAMILIA DE ESTRUCTURA: Hashing (estructura propia #1).
PROPÓSITO:
    Implementa una tabla hash genérica desde cero usando encadenamiento
    separado (separate chaining) con cubetas y redimensionamiento dinámico
    (rehash) cuando el factor de carga supera 0.75.

    A diferencia de usar directamente el dict de Python como caja negra, aquí
    programamos explícitamente:
      - La función de dispersión FNV-1a de 64 bits para cadenas (sin usar hash()).
      - Las cubetas enlazadas como listas de pares [clave, valor].
      - El control de factor de carga y la operación de rehash().
      - El método verificar_invariante() para comprobar la integridad interna.
"""

from typing import Generic, List, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


def _hash_propio(clave: object) -> int:
    """
    Calcula un código hash entero no negativo de forma determinista y sin
    depender del hash() interno de Python (que cambia entre ejecuciones).

    - Para cadenas (str): aplica el algoritmo FNV-1a de 64 bits sobre cada byte UTF-8.
    - Para enteros (int): aplica mezcla de bits estilo SplitMix64.
    """
    mascara_64 = 0xFFFFFFFFFFFFFFFF
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
        x = x ^ (x >> 31)
        return x

    raise TypeError(f"Tipo de clave no soportado por TablaHash: {type(clave).__name__}")


class TablaHash(Generic[K, V]):
    """
    Tabla hash con encadenamiento separado y crecimiento dinámico por duplicación.
    """

    CAPACIDAD_INICIAL: int = 16
    FACTOR_CARGA_MAXIMO: float = 0.75

    def __init__(self, capacidad_inicial: int = CAPACIDAD_INICIAL) -> None:
        """
        Inicializa la tabla vacía con al menos CAPACIDAD_INICIAL cubetas.
        Cada cubeta es una lista de entradas [clave, valor].
        """
        cap = capacidad_inicial if capacidad_inicial > 0 else self.CAPACIDAD_INICIAL
        self._capacidad: int = cap
        self._cantidad: int = 0
        self._cubetas: List[List[List[object]]] = [[] for _ in range(cap)]

    def _calcular_indice(self, clave: K, capacidad: int) -> int:
        """Mapea una clave al índice de su cubeta mediante módulo."""
        return _hash_propio(clave) % capacidad

    def _rehash(self, nueva_capacidad: int) -> None:
        """
        Crea un nuevo arreglo de cubetas de tamaño 'nueva_capacidad' y reubica
        todas las entradas existentes recalculando su cubeta destino.
        Costo temporal: O(n) amortizado sobre secuencias de inserciones.
        """
        nuevas_cubetas: List[List[List[object]]] = [[] for _ in range(nueva_capacidad)]
        for cubeta in self._cubetas:
            for entrada in cubeta:
                nuevo_idx = self._calcular_indice(entrada[0], nueva_capacidad)  # type: ignore[arg-type]
                nuevas_cubetas[nuevo_idx].append(entrada)
        self._cubetas = nuevas_cubetas
        self._capacidad = nueva_capacidad

    def insertar_o_actualizar(self, clave: K, valor: V) -> bool:
        """
        Inserta el par (clave, valor) en la tabla. Si la clave ya existía,
        actualiza su valor asociado sin duplicar la entrada.

        Devuelve True si la clave era nueva; False si solo se actualizó.
        Complejidad: O(1) esperado (amortizado por rehash).
        """
        idx = self._calcular_indice(clave, self._capacidad)
        cubeta = self._cubetas[idx]

        # Primero verificamos si la clave ya existe en la cubeta correspondiente.
        for entrada in cubeta:
            if entrada[0] == clave:
                entrada[1] = valor
                return False

        # Si agregar una clave nueva superaría el factor de carga, duplicamos cubetas.
        if (self._cantidad + 1) / self._capacidad > self.FACTOR_CARGA_MAXIMO:
            self._rehash(self._capacidad * 2)
            idx = self._calcular_indice(clave, self._capacidad)
            cubeta = self._cubetas[idx]

        cubeta.append([clave, valor])
        self._cantidad += 1
        return True

    def obtener(self, clave: K) -> Optional[V]:
        """
        Busca la clave en su cubeta correspondiente y devuelve su valor,
        o None si la clave no está registrada.
        Complejidad: O(1) esperado; O(n) en el peor caso teórico.
        """
        idx = self._calcular_indice(clave, self._capacidad)
        for entrada in self._cubetas[idx]:
            if entrada[0] == clave:
                return entrada[1]  # type: ignore[return-value]
        return None

    def contiene(self, clave: K) -> bool:
        """Indica si una clave existe dentro de la tabla hash."""
        idx = self._calcular_indice(clave, self._capacidad)
        for entrada in self._cubetas[idx]:
            if entrada[0] == clave:
                return True
        return False

    def eliminar(self, clave: K) -> bool:
        """
        Elimina la entrada asociada a 'clave' si existe.
        Devuelve True si se encontró y borró; False si no existía.
        Complejidad: O(1) esperado.
        """
        idx = self._calcular_indice(clave, self._capacidad)
        cubeta = self._cubetas[idx]
        for i, entrada in enumerate(cubeta):
            if entrada[0] == clave:
                cubeta.pop(i)
                self._cantidad -= 1
                return True
        return False

    def tamano(self) -> int:
        """Devuelve el número total de claves únicas almacenadas."""
        return self._cantidad

    def capacidad(self) -> int:
        """Devuelve el número actual de cubetas del arreglo interno."""
        return self._capacidad

    def vacia(self) -> bool:
        """Indica si la tabla no contiene elementos."""
        return self._cantidad == 0

    def factor_carga(self) -> float:
        """Calcula la razón elementos / cubetas actual."""
        return self._cantidad / self._capacidad

    def claves(self) -> List[K]:
        """Devuelve una lista con todas las claves almacenadas."""
        resultado: List[K] = []
        for cubeta in self._cubetas:
            for entrada in cubeta:
                resultado.append(entrada[0])  # type: ignore[arg-type]
        return resultado

    def limpiar(self) -> None:
        """Vacía por completo la tabla y restaura su capacidad inicial."""
        self._capacidad = self.CAPACIDAD_INICIAL
        self._cantidad = 0
        self._cubetas = [[] for _ in range(self._capacidad)]

    def verificar_invariante(self) -> bool:
        """
        INVARIANTE DE REPRESENTACIÓN DE LA TABLA HASH:
        Comprueba en todo momento que:
            1. La cantidad de cubetas coincide con _capacidad (> 0).
            2. El factor de carga no excede FACTOR_CARGA_MAXIMO.
            3. La suma de longitudes de todas las cubetas es igual a _cantidad.
            4. Cada clave está guardada exactamente en la cubeta que dicta _calcular_indice().
            5. No existen claves repetidas dentro de una cubeta.
        """
        if self._capacidad <= 0 or len(self._cubetas) != self._capacidad:
            return False
        if self.factor_carga() > self.FACTOR_CARGA_MAXIMO + 1e-9:
            return False

        conteo_real = 0
        for indice_cubeta, cubeta in enumerate(self._cubetas):
            vistas_en_cubeta = set()
            for entrada in cubeta:
                conteo_real += 1
                clave = entrada[0]
                if self._calcular_indice(clave, self._capacidad) != indice_cubeta:
                    return False
                if clave in vistas_en_cubeta:
                    return False
                vistas_en_cubeta.add(clave)

        return conteo_real == self._cantidad
