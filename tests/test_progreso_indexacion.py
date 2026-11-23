
"""Pruebas del progreso de indexación incremental de VyOps.

Este módulo verifica los mensajes de progreso y el comportamiento
de sincronizar(), implementado en src.indexacion_incremental.

Las pruebas comprueban cuatro escenarios:

    1. Finalización correcta de la indexación por lotes.
    2. Distinción entre fragmentos conservados y pendientes.
    3. Ausencia de operaciones cuando no existen cambios.
    4. Manejo de fallos durante la persistencia de un lote.

Se utiliza una base vectorial simulada mediante MagicMock
para evitar operaciones reales sobre ChromaDB.

También se sustituyen la preparación de documentos,
el bloqueo de indexación y las pausas entre lotes.

La salida estándar se captura mediante redirect_stdout
para comprobar los mensajes informativos generados
durante el proceso.

Las pruebas no consumen Gemini ni modifican
el índice vectorial real de VyOps.

El objetivo principal es comprobar que el progreso
informado sea coherente con las operaciones realizadas,
especialmente cuando ocurre un error de persistencia.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite crear un búfer de texto en memoria
# para capturar los mensajes impresos por sincronizar().
import io

# Permite modificar temporalmente variables de entorno
# utilizadas por la configuración de indexación.
import os

# Framework estándar de pruebas unitarias.
import unittest

# Redirige temporalmente la salida estándar
# hacia un objeto de escritura en memoria.
from contextlib import redirect_stdout

# Facilita la representación de rutas de directorios.
from pathlib import Path

# Crea directorios temporales para las pruebas.
from tempfile import TemporaryDirectory

# MagicMock simula la base vectorial y otras dependencias.
# patch sustituye temporalmente componentes del módulo.
from unittest.mock import MagicMock, patch

# Representa los documentos procesados por LangChain.
from langchain_core.documents import Document

# Función responsable de la sincronización
# incremental de documentos en el índice vectorial.
from src.indexacion_incremental import sincronizar


# ============================================================
# 2. PRUEBAS DEL PROGRESO DE INDEXACIÓN
# ============================================================

class TestProgresoIndexacion(unittest.TestCase):
    """Valida los mensajes y evita reportar inserciones fallidas.

    Comprueba la información presentada durante
    la sincronización incremental de documentos.

    Los escenarios utilizan dependencias simuladas
    para controlar los documentos disponibles,
    los identificadores existentes y los errores
    de persistencia.

    También se verifica que el sistema no ejecute
    inserciones ni pausas cuando no sean necesarias.
    """

    # --------------------------------------------------------
    # 2.1. PREPARACIÓN DE UN ESCENARIO SIMULADO
    # --------------------------------------------------------

    def ejecutar(self, cantidad=30, existentes=(), fallar=False):
        """Ejecuta la sincronización con dependencias simuladas.

        Construye documentos y sus identificadores,
        configura una base vectorial simulada y captura
        los mensajes generados por sincronizar().

        Args:
            cantidad (int):
                Número de documentos y fragmentos simulados.
                Su valor predeterminado es 30.

            existentes (iterable):
                Identificadores que se consideran previamente
                almacenados en el índice vectorial.

            fallar (bool):
                Indica si la operación de inserción simulada
                debe generar un RuntimeError.

        Returns:
            tuple:
                Contiene cinco elementos:

                - salida: texto capturado desde stdout.
                - resultado: valor devuelto por sincronizar(),
                  o None si se captura un RuntimeError.
                - error: excepción RuntimeError capturada,
                  o None si no se produce.
                - db: objeto MagicMock de la base vectorial.
                - dormir: mock de time.sleep.

        El método permite reutilizar la misma preparación
        en los diferentes escenarios de prueba.

        No realiza inserciones reales en ChromaDB
        ni llamadas a servicios de embeddings.
        """

        # Construye la cantidad solicitada de documentos.
        #
        # El identificador de metadatos utiliza módulo 30,
        # conservando el comportamiento original de la prueba.
        documentos = [
            Document(
                page_content=f"Contenido {i}",
                metadata={"id": f"doc-{i % 30}"},
            )
            for i in range(cantidad)
        ]

        # Genera un identificador de fragmento
        # para cada documento simulado.
        identificadores = [
            f"fragmento-{i}" for i in range(cantidad)
        ]

        # Crea una base vectorial simulada.
        db = MagicMock()

        # Simula los identificadores previamente almacenados.
        db.get.return_value = {"ids": list(existentes)}

        # Configura el resultado simulado
        # de la consulta de cantidad de elementos.
        db._collection.count.return_value = cantidad

        # Cuando se solicita un fallo, la inserción
        # de documentos genera una excepción controlada.
        if fallar:
            db.add_documents.side_effect = RuntimeError(
                "Fallo simulado de persistencia"
            )

        # Prepara un búfer para capturar los mensajes
        # impresos durante la sincronización.
        salida = io.StringIO()

        # Inicializa los resultados que devolverá
        # este método auxiliar.
        error = None
        resultado = None

        # Crea un directorio temporal para representar
        # la ubicación del índice durante la prueba.
        with TemporaryDirectory() as temporal:

            # Sustituye las dependencias externas:
            #
            # - Preparación de documentos.
            # - Cliente de ChromaDB.
            # - Bloqueo de indexación.
            # - Pausas entre lotes.
            # - Variable de entorno de pausa.
            #
            # También captura la salida estándar.
            with (
                patch(
                    "src.indexacion_incremental.preparar_documentos",
                    return_value=(documentos, identificadores),
                ),
                patch(
                    "src.indexacion_incremental.Chroma",
                    return_value=db,
                ),
                patch("src.indexacion_incremental.bloqueo_indexacion"),
                patch("src.indexacion_incremental.time.sleep") as dormir,
                patch.dict(
                    os.environ,
                    {"VYOPS_EMBEDDING_PAUSA_SEGUNDOS": "10"},
                ),
                redirect_stdout(salida),
            ):
                try:
                    # Ejecuta la sincronización incremental
                    # utilizando las dependencias simuladas.
                    resultado = sincronizar(
                        Path(temporal),
                        MagicMock(),
                    )

                except RuntimeError as excepcion:
                    # Conserva el error de persistencia
                    # para que la prueba pueda evaluarlo.
                    error = excepcion

        # Devuelve la salida, el resultado, el error
        # y los mocks necesarios para las verificaciones.
        return salida.getvalue(), resultado, error, db, dormir

    # --------------------------------------------------------
    # 2.2. PROGRESO COMPLETO DE INDEXACIÓN
    # --------------------------------------------------------

    def test_progreso_llega_a_cien_por_ciento(self):
        """Comprueba que una indexación completa alcance el 100 %.

        Simula la inserción de 30 fragmentos nuevos.

        Verificaciones:
            - No ocurre un error de sincronización.
            - Se informa el primer lote de tres.
            - Se informa el último lote de tres.
            - Se reportan 30 fragmentos persistidos.
            - El progreso alcanza el 100 %.
            - Se registran 30 inserciones.
            - La inserción se invoca tres veces.

        Este escenario comprueba la presentación
        del progreso cuando todos los lotes
        finalizan correctamente.
        """

        # Ejecuta una sincronización con 30 fragmentos nuevos.
        salida, resultado, error, db, _ = self.ejecutar(30)

        # La ejecución no debe producir errores.
        self.assertIsNone(error)

        # Comprueba los mensajes del primer y último lote.
        self.assertIn("[INDEXACION] Lote 1/3", salida)
        self.assertIn("[INDEXACION] Lote 3/3", salida)

        # Comprueba el total de fragmentos persistidos.
        self.assertIn("30/30 nuevos fragmentos persistidos", salida)

        # El progreso informado debe alcanzar el 100 %.
        self.assertIn("100.0%", salida)

        # Comprueba la cantidad total de inserciones reportadas.
        self.assertEqual(resultado["insertados"], 30)

        # La base simulada debe recibir tres llamadas
        # de inserción de documentos.
        self.assertEqual(db.add_documents.call_count, 3)

    # --------------------------------------------------------
    # 2.3. FRAGMENTOS CONSERVADOS Y PENDIENTES
    # --------------------------------------------------------

    def test_distingue_conservados_y_pendientes(self):
        """Comprueba la distinción entre fragmentos existentes y nuevos.

        Simula 30 fragmentos, de los cuales 10
        ya se encuentran registrados en el índice.

        Verificaciones:
            - No se produce un error.
            - Se informan 10 fragmentos conservados.
            - Se informan 20 fragmentos pendientes.
            - Se reporta la persistencia de los 20 nuevos.
            - El progreso alcanza el 100 %.
            - Se realizan dos llamadas de inserción.

        Esta prueba comprueba que la sincronización
        no contabilice los fragmentos existentes
        como nuevas inserciones.
        """

        # Genera diez identificadores previamente existentes.
        existentes = [f"fragmento-{i}" for i in range(10)]

        # Ejecuta la sincronización de 30 fragmentos,
        # considerando diez ya almacenados.
        salida, resultado, error, db, _ = self.ejecutar(
            30,
            existentes=existentes,
        )

        # La ejecución debe finalizar sin errores.
        self.assertIsNone(error)

        # Comprueba los totales informados.
        self.assertIn("Conservados: 10 | Pendientes: 20", salida)

        # Solo deben reportarse como nuevos
        # los veinte fragmentos pendientes.
        self.assertIn("20/20 nuevos fragmentos persistidos", salida)

        # Comprueba la finalización del progreso.
        self.assertIn("100.0%", salida)

        # Verifica los totales devueltos por la sincronización.
        self.assertEqual(resultado["conservados"], 10)
        self.assertEqual(resultado["insertados"], 20)

        # Los veinte fragmentos nuevos deben procesarse
        # mediante dos llamadas de inserción.
        self.assertEqual(db.add_documents.call_count, 2)

    # --------------------------------------------------------
    # 2.4. SINCRONIZACIÓN SIN CAMBIOS
    # --------------------------------------------------------

    def test_sin_cambios_no_indexa_ni_espera(self):
        """Comprueba que no se indexe cuando todo está actualizado.

        Simula una colección que ya contiene
        los 30 fragmentos preparados.

        Verificaciones:
            - No se produce un error.
            - Se informa que no existen pendientes.
            - Se muestra el mensaje de ausencia de cambios.
            - No se registran nuevas inserciones.
            - No se invoca add_documents().
            - No se ejecutan pausas mediante time.sleep().

        Este escenario verifica que la sincronización
        evite trabajo innecesario cuando el índice
        ya contiene todos los fragmentos.
        """

        # Simula que los treinta fragmentos
        # ya existen en el índice vectorial.
        existentes = [f"fragmento-{i}" for i in range(30)]

        # Ejecuta la sincronización sin fragmentos nuevos.
        salida, resultado, error, db, dormir = self.ejecutar(
            30,
            existentes=existentes,
        )

        # No debe producirse ningún error.
        self.assertIsNone(error)

        # El sistema debe informar cero pendientes.
        self.assertIn("Pendientes: 0", salida)

        # Comprueba el mensaje de ausencia de cambios.
        self.assertIn(
            "[PASS] No hay fragmentos nuevos para indexar.",
            salida,
        )

        # No deben registrarse nuevas inserciones.
        self.assertEqual(resultado["insertados"], 0)

        # No debe ejecutarse la inserción de documentos.
        db.add_documents.assert_not_called()

        # Tampoco deben ejecutarse pausas entre lotes.
        dormir.assert_not_called()

    # --------------------------------------------------------
    # 2.5. FALLO DE PERSISTENCIA DURANTE UN LOTE
    # --------------------------------------------------------

    def test_lote_fallido_no_se_anuncia_persistido(self):
        """Comprueba que un lote fallido no se reporte como persistido.

        Simula 30 fragmentos nuevos y configura
        la inserción para que genere un RuntimeError.

        Verificaciones:
            - No se obtiene un resultado exitoso.
            - Se captura una excepción RuntimeError.
            - Se informa el inicio del primer lote.
            - No se muestra un mensaje de progreso exitoso.
            - No se muestra un mensaje de finalización.
            - Solo se intenta insertar el primer lote.
            - No se ejecuta una pausa después del fallo.

        Esta prueba comprueba que los mensajes
        no anuncien persistencia exitosa cuando
        la operación de inserción ha fallado.
        """

        # Ejecuta la sincronización configurando
        # un fallo en la inserción de documentos.
        salida, resultado, error, db, dormir = self.ejecutar(
            30,
            fallar=True,
        )

        # No debe existir un resultado de sincronización exitosa.
        self.assertIsNone(resultado)

        # El error capturado debe ser RuntimeError.
        self.assertIsInstance(error, RuntimeError)

        # Debe haberse informado el inicio del primer lote.
        self.assertIn("[INDEXACION] Lote 1/3", salida)

        # No debe anunciarse progreso de persistencia
        # después de producirse el error.
        self.assertNotIn("[PROGRESO]", salida)

        # Tampoco debe anunciarse la finalización del proceso.
        self.assertNotIn("[FINALIZADO]", salida)

        # La inserción debe haberse intentado una sola vez.
        self.assertEqual(db.add_documents.call_count, 1)

        # No debe ejecutarse una pausa después del fallo.
        dormir.assert_not_called()


# ============================================================
# 3. EJECUCIÓN DIRECTA DE LAS PRUEBAS
# ============================================================

if __name__ == "__main__":

    # Ejecuta las pruebas definidas en este módulo
    # cuando el archivo se inicia directamente.
    #
    # Este bloque no se ejecuta al importar el módulo
    # desde otro archivo.
    unittest.main()
