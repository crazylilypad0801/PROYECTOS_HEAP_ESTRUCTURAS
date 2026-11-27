"""
ARCHIVO: tests/pruebas.py
PROPÓSITO:
    Suite de pruebas del motor de la Biblioteca personal. Incluye:
      1. Pruebas unitarias de TablaHash, ListaEnlazada y HeapLibros.
      2. Casos borde de las 8 operaciones del motor.
      3. Verificación explícita de los invariantes de cada estructura y del motor.
      4. Prueba diferencial aleatoria de 12 000 operaciones (semilla fija) comparando
         cada respuesta de MotorBiblioteca contra MotorBibliotecaLento, con IDs
         inexistentes y entradas inválidas; invariantes cada 250 pasos.
      5. Prueba de mutantes: se rompe a propósito el motor de 7 maneras y se
         comprueba que la prueba diferencial detecta cada una.
    Ejecución: python tests/pruebas.py
"""

import os
import random
import sys

RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from src import heap_libros as modulo_heap
from src import lista_enlazada as modulo_lista
from src import tabla_hash as modulo_hash
from src.heap_libros import HeapLibros
from src.libro import EstadoLibro, libros_son_iguales
from src.lista_enlazada import ListaEnlazada
from src.motor_biblioteca import MotorBiblioteca
from src.motor_lento import MotorBibliotecaLento
from src.tabla_hash import TablaHash

SEMILLA = 2026


# ---------------------------------------------------------------- 1. Estructuras

def probar_tabla_hash() -> None:
    t = TablaHash()
    assert t.vacia() and t.tamano() == 0 and t.verificar_invariante()
    assert t.insertar_o_actualizar("a", 1) is True       # Clave nueva.
    assert t.insertar_o_actualizar("a", 2) is False      # Sobrescritura: no crece.
    assert t.obtener("a") == 2 and t.tamano() == 1
    assert t.obtener("zzz") is None and not t.contiene("zzz")
    assert t.eliminar("a") is True and t.eliminar("a") is False and t.vacia()

    capacidad_inicial = t.capacidad()
    for i in range(1000):
        t.insertar_o_actualizar(f"id{i}", i)
    assert t.tamano() == 1000 and t.capacidad() > capacidad_inicial   # Hubo rehash.
    assert t.factor_carga() <= 0.75 and t.verificar_invariante()
    assert all(t.obtener(f"id{i}") == i for i in range(1000))
    for i in range(0, 1000, 2):
        assert t.eliminar(f"id{i}")
    assert t.tamano() == 500 and t.verificar_invariante()
    assert all(t.contiene(f"id{i}") == (i % 2 == 1) for i in range(1000))
    assert sorted(t.claves()) == sorted(f"id{i}" for i in range(1, 1000, 2))

    # Claves enteras y rechazo de bool.
    t2 = TablaHash()
    t2.insertar_o_actualizar(7, "siete")
    assert t2.obtener(7) == "siete"
    try:
        t2.insertar_o_actualizar(True, "x")
        assert False, "debía rechazar bool"
    except TypeError:
        pass

    # Colisiones forzadas: capacidad 1 desactivada por rehash, pero muchas claves
    # con el mismo cubo deben seguir encontrándose.
    t3 = TablaHash(capacidad_inicial=2)
    for i in range(50):
        t3.insertar_o_actualizar(f"k{i}", i)
    assert t3.verificar_invariante() and all(t3.obtener(f"k{i}") == i for i in range(50))


def probar_lista_enlazada() -> None:
    l = ListaEnlazada()
    assert l.vacia() and l.primeros_k(5) == [] and l.verificar_invariante()
    for v in ["a", "b", "c", "d"]:
        l.insertar_al_inicio(v)
    assert l.todos() == ["d", "c", "b", "a"] and l.tamano() == 4
    assert l.primeros_k(0) == [] and l.primeros_k(2) == ["d", "c"]
    assert l.primeros_k(99) == ["d", "c", "b", "a"]
    assert l.tamano() == 4 and l.todos() == ["d", "c", "b", "a"]   # No se modifica al leer.
    assert l.verificar_invariante()
    # Eliminar: en el medio, cabeza, cola e inexistente.
    assert l.eliminar("c") and l.todos() == ["d", "b", "a"]
    assert l.eliminar("d") and l.todos() == ["b", "a"]
    assert l.eliminar("a") and l.todos() == ["b"]
    assert not l.eliminar("zz") and l.tamano() == 1 and l.verificar_invariante()
    assert l.eliminar("b") and l.vacia() and l.verificar_invariante()


def probar_heap() -> None:
    h = HeapLibros()
    assert h.vacio() and h.extraer_maximo() is None and h.verificar_invariante()
    assert h.insertar("a", 5, 1) and h.insertar("b", 9, 2) and h.insertar("c", 5, 3)
    assert h.insertar("d", 9, 4)
    assert not h.insertar("a", 1, 9)                   # ID repetido.
    assert h.tamano() == 4 and h.verificar_invariante()
    # Mayor prioridad primero; empate -> el que llegó antes (orden menor).
    assert [h.extraer_maximo().id for _ in range(4)] == ["b", "d", "a", "c"]
    assert h.vacio()

    h = HeapLibros()
    for i in range(10):
        h.insertar(f"x{i}", 1 + i % 3, i)
    assert h.actualizar_prioridad("x0", 10) and h.verificar_invariante()
    assert not h.actualizar_prioridad("nope", 3)
    assert h.extraer_maximo().id == "x0"
    assert h.eliminar_por_id("x5") and not h.eliminar_por_id("x5")
    assert not h.contiene("x5") and h.verificar_invariante()
    # Subir un elemento del medio y bajar otro (casos de _subir y _bajar).
    h.actualizar_prioridad("x3", 10)
    assert h.extraer_maximo().id == "x3"
    # La entrada devuelta es una copia: modificarla no rompe el heap.
    e = h.obtener_entrada("x1")
    e.prioridad = 99
    assert h.verificar_invariante() and h.obtener_entrada("x1").prioridad != 99

    # Heap aleatorio contra orden de referencia.
    rng = random.Random(SEMILLA)
    h = HeapLibros()
    ref = []
    for i in range(500):
        p = rng.randint(1, 10)
        h.insertar(f"r{i}", p, i)
        ref.append((p, i, f"r{i}"))
    esperado = [x[2] for x in sorted(ref, key=lambda x: (-x[0], x[1]))]
    obtenido = [h.extraer_maximo().id for _ in range(500)]
    assert obtenido == esperado


# ---------------------------------------------------------------- 2. Casos borde

def _motores():
    return [MotorBiblioteca(), MotorBibliotecaLento()]


def probar_casos_borde_motor() -> None:
    for m in _motores():
        # Operación 1: registrar.
        assert m.registrar_libro("L1", "Dune", "Herbert").exito
        assert not m.registrar_libro("L1", "Otro", "Otro").exito          # ID repetido.
        assert not m.registrar_libro("", "t", "a").exito
        assert not m.registrar_libro("L2", "", "a").exito
        assert not m.registrar_libro("L2", "t", "").exito
        assert not m.registrar_libro(5, "t", "a").exito                   # No es texto.
        assert m.contar_libros() == 1

        # Operación 2: buscar.
        r = m.buscar_libro("L1")
        assert r.encontrado and r.libro.titulo == "Dune" and r.libro.estado == EstadoLibro.REGISTRADO
        r.libro.titulo = "MODIFICADO"                                     # Es una copia.
        assert m.buscar_libro("L1").libro.titulo == "Dune"
        assert not m.buscar_libro("NO").encontrado and not m.buscar_libro("").encontrado
        assert not m.buscar_libro(None).encontrado

        # Operación 3: añadir a pendientes.
        assert not m.anadir_a_pendientes("L1", 0).exito and not m.anadir_a_pendientes("L1", 11).exito
        assert not m.anadir_a_pendientes("L1", True).exito and not m.anadir_a_pendientes("L1", 2.5).exito
        assert not m.anadir_a_pendientes("NO", 5).exito
        assert m.anadir_a_pendientes("L1", 5).exito
        assert not m.anadir_a_pendientes("L1", 5).exito                   # No duplica.
        assert m.contar_pendientes() == 1

        # Operación 4: cambiar prioridad.
        m.registrar_libro("L2", "alba", "X")
        assert not m.cambiar_prioridad("L2", 3).exito                     # No está pendiente.
        assert not m.cambiar_prioridad("NO", 3).exito
        assert not m.cambiar_prioridad("L1", 99).exito
        assert m.cambiar_prioridad("L1", 9).exito
        assert m.buscar_libro("L1").libro.prioridad == 9

        # Operación 5: elegir siguiente (prioridad, y desempate por llegada).
        m.anadir_a_pendientes("L2", 9)
        m.registrar_libro("L3", "Zorro", "Z")
        m.anadir_a_pendientes("L3", 9)
        assert m.elegir_siguiente_libro().libro.id == "L1"                # Llegó antes.
        m.cambiar_prioridad("L3", 10)
        assert m.elegir_siguiente_libro().libro.id == "L3"
        assert m.elegir_siguiente_libro().libro.id == "L2"
        sig = m.elegir_siguiente_libro()
        assert not sig.disponible and sig.libro is None                   # Sin pendientes.
        assert m.buscar_libro("L1").libro.estado == EstadoLibro.EN_LECTURA

        # Operación 6: marcar terminado.
        assert not m.marcar_como_terminado("NO").exito
        assert m.marcar_como_terminado("L1").exito
        assert not m.marcar_como_terminado("L1").exito                    # No dos veces.
        m.registrar_libro("L4", "Rayuela", "C")
        assert not m.marcar_como_terminado("L4").exito                    # REGISTRADO no.
        m.anadir_a_pendientes("L4", 4)
        assert m.marcar_como_terminado("L4").exito                        # PENDIENTE sí.
        assert m.contar_pendientes() == 0 and not m.elegir_siguiente_libro().disponible
        assert m.marcar_como_terminado("L3").exito and m.marcar_como_terminado("L2").exito

        # Operación 7: lecturas recientes (más reciente primero, sin modificar).
        ids = [l.id for l in m.mostrar_lecturas_recientes(10).libros]
        assert ids == ["L2", "L3", "L4", "L1"]
        assert [l.id for l in m.mostrar_lecturas_recientes(2).libros] == ["L2", "L3"]
        assert m.mostrar_lecturas_recientes(0).exito and m.mostrar_lecturas_recientes(0).libros == []
        assert not m.mostrar_lecturas_recientes(-1).exito
        assert not m.mostrar_lecturas_recientes(True).exito and not m.mostrar_lecturas_recientes("2").exito
        assert [l.id for l in m.mostrar_lecturas_recientes(10).libros] == ids   # No cambió.

        # Operación 8: colección por título (sin distinguir mayúsculas; empate -> ID).
        m.registrar_libro("L0", "dune", "Otro")
        r = m.listar_coleccion_por_titulo()
        assert r.exito and [l.id for l in r.libros] == ["L2", "L0", "L1", "L4", "L3"]
        assert [l.id for l in m.listar_coleccion()] == ["L1", "L2", "L3", "L4", "L0"]  # Orden de registro.

    # Eliminar libro (auxiliar): de cada estado, e ID libre para registrarse de nuevo.
    for m in _motores():
        for i in range(1, 6):
            m.registrar_libro(f"E{i}", f"t{i}", "a")
        m.anadir_a_pendientes("E2", 5)                       # E2 pendiente.
        m.anadir_a_pendientes("E3", 6)
        m.elegir_siguiente_libro()                           # E3 en lectura.
        m.anadir_a_pendientes("E4", 4)
        m.marcar_como_terminado("E4")                        # E4 terminado.
        m.anadir_a_pendientes("E5", 7)
        m.elegir_siguiente_libro()
        m.marcar_como_terminado("E3")                        # E3 terminado (más reciente).
        assert not m.eliminar_libro("NO").exito and not m.eliminar_libro("").exito
        assert not m.eliminar_libro(None).exito
        assert m.eliminar_libro("E2").exito                  # Pendiente.
        assert m.eliminar_libro("E4").exito                  # Terminado.
        assert m.eliminar_libro("E1").exito                  # Registrado.
        assert not m.eliminar_libro("E1").exito              # Ya no existe.
        assert not m.buscar_libro("E2").encontrado and m.contar_libros() == 2
        assert [l.id for l in m.mostrar_lecturas_recientes(10).libros] == ["E3"]
        assert m.contar_pendientes() == 0 and m.contar_terminados() == 1
        assert m.registrar_libro("E2", "nuevo", "b").exito   # ID reutilizable.
        assert m.buscar_libro("E2").libro.estado == EstadoLibro.REGISTRADO
    m = MotorBiblioteca()
    for i in range(20):
        m.registrar_libro(f"V{i}", "t", "a")
        m.anadir_a_pendientes(f"V{i}", 1 + i % 10)
    m.elegir_siguiente_libro()
    m.marcar_como_terminado("V3")
    for i in range(0, 20, 3):
        m.eliminar_libro(f"V{i}")
    assert m.verificar_invariantes()

    # Colección vacía y consultas sin datos.
    for m in _motores():
        assert m.listar_coleccion_por_titulo().libros == []
        assert m.mostrar_lecturas_recientes(5).libros == []
        assert not m.elegir_siguiente_libro().disponible

    # Cambiar prioridad no altera el orden de llegada.
    for m in _motores():
        for i in ("A", "B"):
            m.registrar_libro(i, "t" + i, "a")
            m.anadir_a_pendientes(i, 5)
        m.cambiar_prioridad("A", 7)
        m.cambiar_prioridad("A", 5)
        assert m.elegir_siguiente_libro().libro.id == "A"
        assert m.buscar_libro("A").libro.orden_pendiente == 1


# ---------------------------------------------------------------- 3. Invariantes

def probar_invariantes_motor() -> None:
    m = MotorBiblioteca()
    assert m.verificar_invariantes()
    for i in range(30):
        m.registrar_libro(f"L{i}", f"T{i % 7}", "a")
    for i in range(0, 30, 2):
        m.anadir_a_pendientes(f"L{i}", 1 + i % 10)
    for _ in range(5):
        m.elegir_siguiente_libro()
    for i in (0, 2, 4, 6, 8, 10, 12):
        m.marcar_como_terminado(f"L{i}")
    assert m.verificar_invariantes()

    # Corromper a propósito debe ser detectado.
    libro = m._libros.obtener("L14")           # Pendiente.
    libro.estado = EstadoLibro.REGISTRADO      # Sigue en el heap -> inconsistente.
    assert not m.verificar_invariantes()
    libro.estado = EstadoLibro.PENDIENTE
    assert m.verificar_invariantes()
    m._pendientes._datos[0], m._pendientes._datos[-1] = m._pendientes._datos[-1], m._pendientes._datos[0]
    assert not m.verificar_invariantes()       # Heap roto.


# ---------------------------------------------------------------- 4. Diferencial

def prueba_diferencial(n_operaciones: int, semilla: int, fabrica_rapido=MotorBiblioteca,
                       chequeo_cada: int = 250) -> int:
    """
    Ejecuta n_operaciones aleatorias en ambos motores y compara cada respuesta.
    La mezcla mantiene pendientes casi siempre (más añadir que elegir/terminar).
    Devuelve el número de operaciones ejecutadas. Lanza AssertionError si hay diferencia.
    """
    rng = random.Random(semilla)
    r, l = fabrica_rapido(), MotorBibliotecaLento()
    ids = []
    titulos = ["Dune", "dune", "Ágata", "Zorro", "alba", "Rayuela", "Ficciones", "ficciones"]

    def elegir_id():
        if ids and rng.random() < 0.85:
            return rng.choice(ids)
        return rng.choice(["NO_EXISTE", "", "L-1"])

    def prioridad():
        if rng.random() < 0.08:
            return rng.choice([0, 11, -3, True, 5.5, None])
        return rng.randint(1, 10)

    for paso in range(n_operaciones):
        d = rng.randrange(100)
        if d < 20:
            i = rng.choice(ids) if ids and rng.random() < 0.08 else f"L{len(ids)}"
            t, a = rng.choice(titulos + [""]), rng.choice(["X", "Y", ""])
            x, y = r.registrar_libro(i, t, a), l.registrar_libro(i, t, a)
            assert x.exito == y.exito, (paso, "registrar")
            if x.exito:
                ids.append(i)
        elif d < 32:
            i = elegir_id()
            x, y = r.buscar_libro(i), l.buscar_libro(i)
            assert x.encontrado == y.encontrado, (paso, "buscar")
            assert (not x.encontrado) or libros_son_iguales(x.libro, y.libro), (paso, "buscar")
        elif d < 55:
            i, p = elegir_id(), prioridad()
            assert r.anadir_a_pendientes(i, p).exito == l.anadir_a_pendientes(i, p).exito, (paso, "añadir")
        elif d < 72:
            i, p = elegir_id(), prioridad()
            assert r.cambiar_prioridad(i, p).exito == l.cambiar_prioridad(i, p).exito, (paso, "cambiar")
        elif d < 80:
            x, y = r.elegir_siguiente_libro(), l.elegir_siguiente_libro()
            assert x.disponible == y.disponible, (paso, "elegir")
            assert (not x.disponible) or libros_son_iguales(x.libro, y.libro), (paso, "elegir")
        elif d < 88:
            i = elegir_id()
            assert r.marcar_como_terminado(i).exito == l.marcar_como_terminado(i).exito, (paso, "terminar")
        elif d < 96:
            k = rng.choice([-1, 0, 1, 3, 10, 50, 10_000])
            x, y = r.mostrar_lecturas_recientes(k), l.mostrar_lecturas_recientes(k)
            assert x.exito == y.exito and len(x.libros) == len(y.libros), (paso, "recientes")
            assert all(libros_son_iguales(a, b) for a, b in zip(x.libros, y.libros)), (paso, "recientes")
        elif d < 98:
            i = elegir_id()
            assert r.eliminar_libro(i).exito == l.eliminar_libro(i).exito, (paso, "eliminar")
            if rng.random() < 0.5:                      # A veces se reutiliza el ID eliminado.
                t, a = rng.choice(titulos), "R"
                assert r.registrar_libro(i, t, a).exito == l.registrar_libro(i, t, a).exito, (paso, "reusar")
        else:
            x, y = r.listar_coleccion_por_titulo(), l.listar_coleccion_por_titulo()
            assert len(x.libros) == len(y.libros)
            assert all(libros_son_iguales(a, b) for a, b in zip(x.libros, y.libros)), (paso, "ordenada")

        if paso % chequeo_cada == 0:
            assert r.verificar_invariantes(), (paso, "invariantes")
            assert (r.contar_libros(), r.contar_pendientes(), r.contar_terminados()) == (
                l.contar_libros(), l.contar_pendientes(), l.contar_terminados()), (paso, "conteos")
    assert r.verificar_invariantes()
    todos_r, todos_l = r.listar_coleccion(), l.listar_coleccion()
    assert len(todos_r) == len(todos_l)
    assert all(libros_son_iguales(a, b) for a, b in zip(todos_r, todos_l))
    return n_operaciones


# ---------------------------------------------------------------- 5. Mutantes

class _MotorMutante(MotorBiblioteca):
    """Base para mutantes: se sobreescribe una sola operación a la vez."""


class _M2_CambiarPrioridadNoReubica(_MotorMutante):
    def cambiar_prioridad(self, id_libro, nueva_prioridad):
        from src.libro import ResultadoOperacion
        libro = self._libros.obtener(id_libro) if isinstance(id_libro, str) and id_libro else None
        if isinstance(nueva_prioridad, bool) or not isinstance(nueva_prioridad, int) \
                or not 1 <= nueva_prioridad <= 10:
            return ResultadoOperacion(False, "prioridad")
        if libro is None or libro.estado != EstadoLibro.PENDIENTE:
            return ResultadoOperacion(False, "estado")
        libro.prioridad = nueva_prioridad
        # BUG: cambia el número en el heap pero no sube ni baja la entrada.
        self._pendientes._datos[self._pendientes._posiciones.obtener(id_libro)].prioridad = nueva_prioridad
        return ResultadoOperacion(True, "mutante")


class _M3_RecientesDevuelveUnoMenos(_MotorMutante):
    def mostrar_lecturas_recientes(self, k):
        res = super().mostrar_lecturas_recientes(k)
        if res.exito and res.libros:
            res.libros = res.libros[:-1]
        return res


class _M4_OrdenTituloDistingueMayusculas(_MotorMutante):
    def listar_coleccion_por_titulo(self):
        from src.libro import ResultadoLista, copiar_libro
        orden = sorted(self._coleccion, key=lambda x: (x.titulo, x.id))
        return ResultadoLista(True, [copiar_libro(x) for x in orden], "mutante")


class _M5_AnadirPermiteDuplicar(_MotorMutante):
    def anadir_a_pendientes(self, id_libro, prioridad):
        libro = self._libros.obtener(id_libro) if isinstance(id_libro, str) and id_libro else None
        if libro is not None and libro.estado == EstadoLibro.PENDIENTE and 1 <= prioridad <= 10 \
                and not isinstance(prioridad, bool):
            self._contador_pendientes += 1
            self._pendientes.insertar(id_libro, prioridad, self._contador_pendientes)  # Falla en silencio.
            from src.libro import ResultadoOperacion
            return ResultadoOperacion(True, "mutante")
        return super().anadir_a_pendientes(id_libro, prioridad)


class _M6_ElegirIgnoraDesempate(_MotorMutante):
    def elegir_siguiente_libro(self):
        # Sin reglas de desempate: cambia el orden de llegada al azar entre empates.
        from src.libro import ResultadoSiguiente, copiar_libro
        if self._pendientes.vacio():
            return ResultadoSiguiente(False, None, "mutante")
        maxp = max(e.prioridad for e in self._pendientes._datos)
        candidatos = sorted((e for e in self._pendientes._datos if e.prioridad == maxp),
                            key=lambda e: -e.orden)          # Elige el MÁS NUEVO.
        e = candidatos[0]
        self._pendientes.eliminar_por_id(e.id)
        libro = self._libros.obtener(e.id)
        libro.estado = EstadoLibro.EN_LECTURA
        return ResultadoSiguiente(True, copiar_libro(libro), "mutante")


def _mutante_1_simple():
    """Mutante 1 reescrito sin trucos: terminar un pendiente no lo saca del heap."""
    class M(MotorBiblioteca):
        def marcar_como_terminado(self, id_libro):
            libro = self._libros.obtener(id_libro) if isinstance(id_libro, str) and id_libro else None
            from src.libro import ResultadoOperacion
            if libro is None:
                return ResultadoOperacion(False, "no existe")
            if libro.estado not in (EstadoLibro.EN_LECTURA, EstadoLibro.PENDIENTE):
                return ResultadoOperacion(False, "estado")
            libro.estado = EstadoLibro.TERMINADO       # BUG: no llama a eliminar_por_id.
            self._recientes.insertar_al_inicio(id_libro)
            return ResultadoOperacion(True, "mutante")
    return M


class _M7_EliminarNoSacaDeRecientes(_MotorMutante):
    def eliminar_libro(self, id_libro):
        libro = self._libros.obtener(id_libro) if isinstance(id_libro, str) and id_libro else None
        if libro is not None and libro.estado == EstadoLibro.TERMINADO:
            self._coleccion.remove(libro)
            self._libros.eliminar(id_libro)             # BUG: el ID queda en la lista de recientes.
            from src.libro import ResultadoOperacion
            return ResultadoOperacion(True, "mutante")
        return super().eliminar_libro(id_libro)


def probar_mutantes() -> None:
    mutantes = {
        "M1 terminar un pendiente no lo saca del heap": _mutante_1_simple(),
        "M2 cambiar prioridad sin reubicar en el heap": _M2_CambiarPrioridadNoReubica,
        "M3 lecturas recientes devuelve un libro de menos": _M3_RecientesDevuelveUnoMenos,
        "M4 orden por título distingue mayúsculas": _M4_OrdenTituloDistingueMayusculas,
        "M5 añadir a pendientes permite duplicar": _M5_AnadirPermiteDuplicar,
        "M6 desempate elige el libro más nuevo": _M6_ElegirIgnoraDesempate,
        "M7 eliminar un terminado no lo saca de recientes": _M7_EliminarNoSacaDeRecientes,
    }
    for nombre, clase in mutantes.items():
        try:
            prueba_diferencial(4000, SEMILLA, fabrica_rapido=clase, chequeo_cada=50)
        except AssertionError:
            print(f"   mutante detectado: {nombre}")
        else:
            raise AssertionError(f"MUTANTE NO DETECTADO: {nombre}")
    # Sanidad: sin mutar, la misma prueba pasa.
    prueba_diferencial(4000, SEMILLA, chequeo_cada=50)


# ---------------------------------------------------------------- Ejecución

def main() -> None:
    pasos = [
        ("TablaHash", probar_tabla_hash),
        ("ListaEnlazada", probar_lista_enlazada),
        ("HeapLibros", probar_heap),
        ("Casos borde de las 8 operaciones (ambos motores)", probar_casos_borde_motor),
        ("Invariantes del motor (y detección de corrupción)", probar_invariantes_motor),
    ]
    for nombre, f in pasos:
        f()
        print(f"OK  {nombre}")
    n = prueba_diferencial(12000, SEMILLA)
    print(f"OK  Prueba diferencial: {n} operaciones aleatorias, motor rápido == motor lento")
    print("Prueba de mutantes:")
    probar_mutantes()
    print("OK  Los 7 mutantes fueron detectados")
    print("TODAS LAS PRUEBAS PASARON")


if __name__ == "__main__":
    main()
