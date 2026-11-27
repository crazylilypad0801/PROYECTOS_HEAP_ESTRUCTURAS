"""
ARCHIVO: tests/pruebas.py
PROPÓSITO:
    Suite completa de pruebas del Motor de Misiones de un Videojuego.
    Incluye:
      1. Pruebas unitarias de TablaHash (rehash automático, sobrescritura y borrado).
      2. Pruebas unitarias y casos borde de las 7 operaciones del motor.
      3. Verificación explícita de los invariantes de TablaHash, HeapMisiones y GrafoCiudad.
      4. Prueba diferencial aleatoria de 12 000 operaciones comparando cada resultado
         del MotorMisiones optimizado contra MotorMisionesLento (referencia lineal).
"""

import os
import random
import sys

# Asegura que el directorio raíz del proyecto esté en sys.path al ejecutar este script.
RAIZ_PROYECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from src.mision import EstadoMision, TipoMision, misiones_son_iguales
from src.motor_lento import MotorMisionesLento
from src.motor_misiones import MotorMisiones
from src.tabla_hash import TablaHash


def construir_mapa_base(rapido: MotorMisiones, lento: MotorMisionesLento) -> None:
    """Carga un mapa pequeño y conocido con un componente conexo y una isla aislada."""
    lugares = ["Plaza_Central", "Puerto", "Torre_Norte", "Bosque", "Mina", "Isla_Aislada"]
    for lugar in lugares:
        assert rapido.agregar_ubicacion(lugar)
        assert lento.agregar_ubicacion(lugar)

    caminos = [
        ("Plaza_Central", "Puerto", 4),
        ("Plaza_Central", "Torre_Norte", 2),
        ("Torre_Norte", "Puerto", 1),  # Atajo: Plaza -> Torre_Norte -> Puerto cuesta 3 (< 4).
        ("Puerto", "Bosque", 5),
        ("Torre_Norte", "Mina", 7),
        ("Bosque", "Mina", 2),
    ]
    for u, v, peso in caminos:
        assert rapido.agregar_camino(u, v, peso)
        assert lento.agregar_camino(u, v, peso)


def probar_tabla_hash() -> None:
    """Verifica inserción, múltiples rehash, actualización y eliminación en TablaHash."""
    tabla: TablaHash[str, int] = TablaHash()
    assert tabla.vacia()
    assert tabla.verificar_invariante()

    # Insertar 200 claves para disparar varios rehash (16 -> 32 -> 64 -> 128 -> 256 -> 512).
    for i in range(200):
        clave = f"clave_{i}"
        assert tabla.insertar_o_actualizar(clave, i * 10) is True
        assert tabla.verificar_invariante()

    assert tabla.tamano() == 200
    assert tabla.capacidad() >= 256

    # Actualizar una clave existente no debe duplicarla.
    assert tabla.insertar_o_actualizar("clave_42", 9999) is False
    assert tabla.tamano() == 200
    assert tabla.obtener("clave_42") == 9999

    # Eliminar la mitad de las claves.
    for i in range(0, 200, 2):
        clave = f"clave_{i}"
        assert tabla.eliminar(clave) is True
        assert tabla.eliminar(clave) is False
        assert tabla.verificar_invariante()

    assert tabla.tamano() == 100
    print("[OK] Prueba unitaria de TablaHash (rehash, actualización y eliminaciones)")


def probar_casos_borde_motor() -> None:
    """Prueba todas las operaciones y cada caso borde definido en el diseño."""
    rapido = MotorMisiones()
    lento = MotorMisionesLento()
    construir_mapa_base(rapido, lento)

    # 1. Comportamiento sobre motor vacío.
    assert not rapido.obtener_siguiente_mision().disponible
    assert not rapido.buscar_mision("M01").encontrada
    assert not rapido.cambiar_urgencia("M01", 5).exito
    assert not rapido.cancelar_mision("M01").exito
    top_vacio = rapido.consultar_primeras_k(3)
    assert top_vacio.exito and top_vacio.misiones == []
    assert not rapido.consultar_primeras_k(-1).exito
    assert not rapido.calcular_ruta_a_mision("Plaza_Central", "M01").existe
    assert rapido.verificar_invariantes()

    # 2. Validaciones de entrada al registrar misiones.
    assert not rapido.registrar_mision("", "Sin ID", TipoMision.PRINCIPAL, 5, "Puerto").exito
    assert not rapido.registrar_mision("M01", "", TipoMision.PRINCIPAL, 5, "Puerto").exito
    assert not rapido.registrar_mision("M01", "Urgencia baja", TipoMision.PRINCIPAL, 0, "Puerto").exito
    assert not rapido.registrar_mision("M01", "Urgencia alta", TipoMision.PRINCIPAL, 11, "Puerto").exito
    assert not rapido.registrar_mision("M01", "Lugar falso", TipoMision.PRINCIPAL, 5, "Luna").exito

    # 3. Registro válido y rechazo de ID repetido.
    assert rapido.registrar_mision("M01", "Rescatar muelle", TipoMision.SECUNDARIA, 6, "Puerto").exito
    assert not rapido.registrar_mision("M01", "Duplicada", TipoMision.PRINCIPAL, 10, "Bosque").exito

    # 4. Regla de desempate en cascada: urgencia -> tipo -> orden de llegada.
    assert rapido.registrar_mision("M02", "Escolta real", TipoMision.PRINCIPAL, 6, "Torre_Norte").exito
    assert rapido.registrar_mision("M03", "Suministros", TipoMision.PRINCIPAL, 6, "Bosque").exito
    assert rapido.registrar_mision("M04", "Defensa final", TipoMision.SECUNDARIA, 9, "Mina").exito

    top10 = rapido.consultar_primeras_k(10)  # k > 4 disponibles -> devuelve 4.
    assert top10.exito and len(top10.misiones) == 4
    assert [m.id for m in top10.misiones] == ["M04", "M02", "M03", "M01"]
    assert rapido.consultar_primeras_k(0).misiones == []

    # 5. Cambio de urgencia (subir hasta el tope y bajar hasta el final).
    assert not rapido.cambiar_urgencia("M01", 0).exito
    assert rapido.cambiar_urgencia("M01", 10).exito
    assert rapido.consultar_primeras_k(1).misiones[0].id == "M01"
    assert rapido.cambiar_urgencia("M01", 2).exito
    assert rapido.consultar_primeras_k(4).misiones[-1].id == "M01"
    assert rapido.verificar_invariantes()

    # 6. Cancelación: desaparece del heap, pero conserva datos consultables en TablaHash.
    assert rapido.cancelar_mision("M02").exito
    assert not rapido.cancelar_mision("M02").exito
    assert not rapido.cambiar_urgencia("M02", 8).exito
    busq_m02 = rapido.buscar_mision("M02")
    assert busq_m02.encontrada
    assert busq_m02.mision is not None
    assert busq_m02.mision.estado == EstadoMision.CANCELADA
    assert busq_m02.mision.nombre == "Escolta real"
    assert not rapido.calcular_ruta_a_mision("Plaza_Central", "M02").existe

    # 7. Obtener siguiente misión: pasa a EN_CURSO y no se puede editar ni cancelar.
    sig = rapido.obtener_siguiente_mision()
    assert sig.disponible and sig.mision is not None
    assert sig.mision.id == "M04"
    assert sig.mision.estado == EstadoMision.EN_CURSO
    assert not rapido.cancelar_mision("M04").exito
    assert not rapido.cambiar_urgencia("M04", 3).exito

    # 8. Rutas con Dijkstra: atajo de menor costo, misma ubicación y componente desconectado.
    ruta_puerto = rapido.calcular_ruta_a_mision("Plaza_Central", "M01")
    assert ruta_puerto.existe and ruta_puerto.costo_total == 3
    assert rapido.obtener_mapa().validar_camino("Plaza_Central", "Puerto", ruta_puerto.camino, 3)

    ruta_misma = rapido.calcular_ruta_a_mision("Puerto", "M01")
    assert ruta_misma.existe and ruta_misma.costo_total == 0 and ruta_misma.camino == ["Puerto"]

    assert rapido.registrar_mision("M05", "Faro lejano", TipoMision.SECUNDARIA, 5, "Isla_Aislada").exito
    assert not rapido.calcular_ruta_a_mision("Plaza_Central", "M05").existe
    assert not rapido.calcular_ruta_a_mision("Lugar_Inexistente", "M01").existe
    assert rapido.verificar_invariantes()

    print("[OK] Pruebas unitarias y casos borde de las 7 operaciones")


def probar_comparacion_diferencial_12000() -> None:
    """
    Ejecuta 12 000 operaciones aleatorias en ambos motores (optimizado y lento)
    y verifica igualdad estricta en cada respuesta e invariantes cada 250 pasos.
    """
    rapido = MotorMisiones()
    lento = MotorMisionesLento()
    rng = random.Random(20261126)

    num_nodos = 30
    lugares = [f"Zona_{i}" for i in range(num_nodos)]
    for lugar in lugares:
        rapido.agregar_ubicacion(lugar)
        lento.agregar_ubicacion(lugar)

    def conectar(u: int, v: int, peso: int) -> None:
        rapido.agregar_camino(lugares[u], lugares[v], peso, True)
        lento.agregar_camino(lugares[u], lugares[v], peso, True)

    # Componente principal conexo: Zona_0 .. Zona_25.
    for i in range(25):
        conectar(i, i + 1, rng.randint(1, 20))
    # Componente desconectado: Zona_26 .. Zona_29.
    for i in range(26, 29):
        conectar(i, i + 1, rng.randint(1, 15))
    # Atajos aleatorios en el componente principal.
    for _ in range(45):
        conectar(rng.randrange(26), rng.randrange(26), rng.randint(1, 25))

    ids_registrados = []
    consecutivo_id = 1
    total_ops = 12000

    def elegir_id_prueba() -> str:
        if ids_registrados and rng.random() < 0.75:
            return rng.choice(ids_registrados)
        return f"M_NO_EXISTE_{rng.randrange(500)}"

    for paso in range(1, total_ops + 1):
        dado = rng.randrange(100)

        if dado < 28:
            # Op 1: Registrar misión (incluye IDs repetidos, urgencias y lugares inválidos).
            if ids_registrados and rng.random() < 0.10:
                id_m = rng.choice(ids_registrados)
            else:
                id_m = f"M_{consecutivo_id}"
                consecutivo_id += 1
            nombre = f"Mision_{id_m}"
            tipo = TipoMision.PRINCIPAL if rng.randrange(3) == 0 else TipoMision.SECUNDARIA
            urgencia = rng.choice([0, 12]) if rng.random() < 0.08 else rng.randint(1, 10)
            ubicacion = "Zona_Fantasma" if rng.random() < 0.05 else rng.choice(lugares)

            r1 = rapido.registrar_mision(id_m, nombre, tipo, urgencia, ubicacion)
            r2 = lento.registrar_mision(id_m, nombre, tipo, urgencia, ubicacion)
            assert r1.exito == r2.exito
            if r1.exito:
                ids_registrados.append(id_m)

        elif dado < 44:
            # Op 2: Buscar misión.
            id_m = elegir_id_prueba()
            r1 = rapido.buscar_mision(id_m)
            r2 = lento.buscar_mision(id_m)
            assert r1.encontrada == r2.encontrada
            if r1.encontrada:
                assert r1.mision is not None and r2.mision is not None
                assert misiones_son_iguales(r1.mision, r2.mision)

        elif dado < 60:
            # Op 3: Cambiar urgencia.
            id_m = elegir_id_prueba()
            nueva_urg = 15 if rng.random() < 0.08 else rng.randint(1, 10)
            r1 = rapido.cambiar_urgencia(id_m, nueva_urg)
            r2 = lento.cambiar_urgencia(id_m, nueva_urg)
            assert r1.exito == r2.exito

        elif dado < 72:
            # Op 4: Cancelar misión.
            id_m = elegir_id_prueba()
            r1 = rapido.cancelar_mision(id_m)
            r2 = lento.cancelar_mision(id_m)
            assert r1.exito == r2.exito

        elif dado < 82:
            # Op 5: Obtener siguiente misión.
            r1 = rapido.obtener_siguiente_mision()
            r2 = lento.obtener_siguiente_mision()
            assert r1.disponible == r2.disponible
            if r1.disponible:
                assert r1.mision is not None and r2.mision is not None
                assert misiones_son_iguales(r1.mision, r2.mision)

        elif dado < 91:
            # Op 6: Consultar primeras k misiones.
            k = -1 if rng.random() < 0.05 else rng.randrange(15)
            r1 = rapido.consultar_primeras_k(k)
            r2 = lento.consultar_primeras_k(k)
            assert r1.exito == r2.exito
            assert len(r1.misiones) == len(r2.misiones)
            for m1, m2 in zip(r1.misiones, r2.misiones):
                assert misiones_son_iguales(m1, m2)

        else:
            # Op 7: Calcular ruta a una misión.
            id_m = elegir_id_prueba()
            origen = "Origen_Falso" if rng.random() < 0.05 else rng.choice(lugares)
            r1 = rapido.calcular_ruta_a_mision(origen, id_m)
            r2 = lento.calcular_ruta_a_mision(origen, id_m)
            assert r1.existe == r2.existe
            if r1.existe:
                assert r1.costo_total == r2.costo_total
                busq = rapido.buscar_mision(id_m)
                assert busq.mision is not None
                assert rapido.obtener_mapa().validar_camino(
                    origen, busq.mision.ubicacion, r1.camino, r1.costo_total
                )

        if paso % 250 == 0 or paso == total_ops:
            assert rapido.verificar_invariantes()
            assert rapido.total_misiones() == lento.total_misiones()
            assert rapido.total_pendientes() == lento.total_pendientes()

    print(
        f"[OK] Comparación diferencial aleatoria de {total_ops} operaciones "
        "(0 discrepancias, invariantes verificados)"
    )


def main() -> None:
    print("=== Iniciando suite de pruebas del Motor de Misiones ===")
    probar_tabla_hash()
    probar_casos_borde_motor()
    probar_comparacion_diferencial_12000()
    print("=== TODAS LAS PRUEBAS PASARON EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
