
"""Pruebas unitarias del registro de costos por sesión de VyOps.

Este módulo verifica el comportamiento de RegistroCostosSesion,
implementado en src.registro_costos.

El registro permite almacenar costos individuales de operaciones
y consultar el costo total acumulado durante una sesión.

Las pruebas contemplan cinco escenarios:

    1. Inicialización de una sesión sin costos.
    2. Registro y acumulación de costos por operación.
    3. Rechazo de valores negativos, no finitos o inválidos.
    4. Aislamiento de los costos entre sesiones independientes.
    5. Protección del historial frente a modificaciones externas.

Se utiliza unittest para comprobar los resultados esperados
y las excepciones generadas ante entradas inválidas.

Las pruebas trabajan con valores simulados de costos.
No realizan llamadas a Gemini ni calculan tarifas reales
de los proveedores de inteligencia artificial.

El módulo puede ejecutarse directamente mediante
unittest.main().
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework estándar de Python para pruebas unitarias.
import unittest

# Clase responsable de almacenar y consultar
# los costos asociados a las operaciones de una sesión.
from src.registro_costos import RegistroCostosSesion


# ============================================================
# 2. PRUEBAS DEL REGISTRO DE COSTOS POR SESIÓN
# ============================================================

class TestRegistroCostosSesion(unittest.TestCase):
    """Verifica el registro, acumulación y aislamiento de costos.

    Comprueba las operaciones principales de RegistroCostosSesion:

        - Consultar el costo total.
        - Obtener el historial de operaciones.
        - Registrar costos individuales.
        - Rechazar valores inválidos.
        - Mantener registros independientes.
        - Proteger el historial interno.

    Cada prueba crea sus propias instancias para evaluar
    el comportamiento sin depender de otras sesiones.
    """

    # --------------------------------------------------------
    # 2.1. INICIALIZACIÓN DE UNA SESIÓN
    # --------------------------------------------------------

    def test_sesion_inicia_sin_costos(self):
        """Comprueba que una sesión nueva no tenga operaciones.

        Crea una instancia de RegistroCostosSesion
        sin registrar ningún costo.

        Verificaciones:
            - El costo total inicial es 0.0.
            - El historial de operaciones está vacío.

        Esta prueba establece el estado inicial esperado
        antes de comenzar a registrar consumos.
        """

        # Crea un registro de costos para una nueva sesión.
        registro = RegistroCostosSesion()

        # El total inicial debe ser cero.
        self.assertEqual(registro.obtener_total(), 0.0)

        # No deben existir operaciones registradas.
        self.assertEqual(registro.obtener_operaciones(), [])

    # --------------------------------------------------------
    # 2.2. REGISTRO Y ACUMULACIÓN DE COSTOS
    # --------------------------------------------------------

    def test_registra_costo_por_operacion(self):
        """Comprueba que cada operación conserve su costo.

        Registra dos operaciones con costos conocidos
        y verifica tanto el historial como el total acumulado.

        Verificaciones:
            - Se conservan los costos 0.001 y 0.002.
            - Se mantiene el orden de registro.
            - El costo total acumulado es aproximadamente 0.003.

        Se utiliza assertAlmostEqual para comparar el total,
        considerando las particularidades de la representación
        de números de punto flotante.
        """

        # Inicializa un registro independiente.
        registro = RegistroCostosSesion()

        # Registra el costo de la primera operación.
        registro.registrar_operacion(0.001)

        # Registra el costo de la segunda operación.
        registro.registrar_operacion(0.002)

        # Comprueba que el historial conserve ambos valores
        # en el orden en que fueron registrados.
        self.assertEqual(
            registro.obtener_operaciones(),
            [0.001, 0.002],
        )

        # Comprueba el total acumulado de las operaciones.
        self.assertAlmostEqual(registro.obtener_total(), 0.003)

    # --------------------------------------------------------
    # 2.3. VALIDACIÓN DE COSTOS INVÁLIDOS
    # --------------------------------------------------------

    def test_rechaza_costos_invalidos(self):
        """Impide registrar costos negativos o no finitos.

        Evalúa diferentes entradas que no deben aceptarse
        como costos válidos de una operación.

        Valores evaluados:
            - -1: costo negativo.
            - NaN: valor numérico indefinido.
            - Infinito positivo: valor no finito.
            - True: valor booleano.
            - "1": representación textual de un número.

        Verificaciones:
            - Cada valor genera una excepción ValueError.
            - Ninguna entrada inválida se incorpora al historial.

        Se utiliza subTest para identificar individualmente
        cada valor evaluado dentro de la misma prueba.
        """

        # Crea un registro sin operaciones.
        registro = RegistroCostosSesion()

        # Recorre los valores considerados inválidos.
        for costo in (-1, float("nan"), float("inf"), True, "1"):

            # Identifica el valor evaluado en cada subprueba.
            with self.subTest(costo=costo):

                # Cada entrada inválida debe producir ValueError.
                with self.assertRaises(ValueError):
                    registro.registrar_operacion(costo)

        # Ninguno de los valores rechazados
        # debe haberse incorporado al historial.
        self.assertEqual(registro.obtener_operaciones(), [])

    # --------------------------------------------------------
    # 2.4. AISLAMIENTO ENTRE SESIONES
    # --------------------------------------------------------

    def test_sesiones_independientes(self):
        """Comprueba que dos sesiones no compartan operaciones.

        Crea dos instancias independientes del registro
        y agrega un costo diferente a cada una.

        Verificaciones:
            - La sesión A acumula 0.01.
            - La sesión B acumula 0.02.
            - Los costos de una sesión no afectan a la otra.

        Esta prueba verifica el aislamiento del estado
        entre distintas instancias de RegistroCostosSesion.
        """

        # Inicializa dos registros independientes.
        sesion_a = RegistroCostosSesion()
        sesion_b = RegistroCostosSesion()

        # Registra un costo diferente en cada sesión.
        sesion_a.registrar_operacion(0.01)
        sesion_b.registrar_operacion(0.02)

        # Comprueba el total individual de la sesión A.
        self.assertAlmostEqual(sesion_a.obtener_total(), 0.01)

        # Comprueba el total individual de la sesión B.
        self.assertAlmostEqual(sesion_b.obtener_total(), 0.02)

    # --------------------------------------------------------
    # 2.5. PROTECCIÓN DEL HISTORIAL INTERNO
    # --------------------------------------------------------

    def test_historial_no_se_modifica_externamente(self):
        """Comprueba que el historial devuelto sea una copia.

        Registra una operación y obtiene el historial
        mediante obtener_operaciones().

        Después modifica la lista recibida agregando
        un valor que no corresponde a una operación real.

        Verificaciones:
            - La modificación de la lista externa
              no altera el historial interno.
            - El registro conserva únicamente el costo original.

        Esta prueba comprueba que el método de consulta
        no exponga una referencia mutable directa
        a la lista interna de operaciones.
        """

        # Inicializa un registro independiente.
        registro = RegistroCostosSesion()

        # Registra una operación con costo conocido.
        registro.registrar_operacion(0.01)

        # Obtiene el historial de operaciones.
        historial = registro.obtener_operaciones()

        # Modifica la lista obtenida externamente.
        #
        # Esta operación no debe afectar al registro interno.
        historial.append(999)

        # Comprueba que el historial original
        # conserve únicamente la operación registrada.
        self.assertEqual(registro.obtener_operaciones(), [0.01])


# ============================================================
# 3. EJECUCIÓN DIRECTA DE LAS PRUEBAS
# ============================================================

if __name__ == "__main__":

    # Ejecuta las pruebas de este módulo cuando
    # se inicia directamente como programa.
    #
    # No se ejecuta automáticamente al importar
    # este archivo desde otro módulo.
    unittest.main()
