
"""Pruebas unitarias de los registros JSON de VyOps.

Este módulo verifica el comportamiento de JsonFormatter,
implementado en logs_json.py, y su integración con
el contexto de trazabilidad definido en traza_contexto.py.

Los registros estructurados permiten conservar información
técnica de las operaciones del sistema RAG, facilitando
su seguimiento y diagnóstico.

Las pruebas cubren seis escenarios:

    1. Incorporación automática del trace_id desde contextvars.
    2. Independencia de identificadores entre consultas.
    3. Exclusión de datos sensibles en campos adicionales.
    4. Sustitución de mensajes de log no autorizados.
    5. Validación de valores permitidos para el modelo.
    6. Exclusión de valores numéricos no finitos.

Se utiliza logging.LogRecord para construir eventos
simulados sin configurar archivos ni servicios
externos de almacenamiento de logs.

Las pruebas verifican propiedades concretas
del contenido generado por JsonFormatter.

No constituyen una auditoría completa de privacidad,
seguridad o aislamiento entre organizaciones.

No realizan llamadas a Gemini ni utilizan ChromaDB.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite convertir los registros JSON generados
# en diccionarios de Python para inspeccionar sus campos.
import json

# Proporciona la clase LogRecord utilizada para construir
# eventos de registro simulados.
import logging

# Framework estándar para organizar pruebas unitarias.
import unittest

# Formateador responsable de generar registros JSON
# con los campos autorizados por VyOps.
from logs_json import JsonFormatter

# Variable de contexto utilizada para asociar
# un identificador de trazabilidad a cada ejecución.
from traza_contexto import trace_id_var


# ============================================================
# 2. PRUEBAS DEL FORMATO JSON Y TRAZABILIDAD
# ============================================================

class TestLogsJson(unittest.TestCase):
    """Verifica la trazabilidad y privacidad de los registros JSON.

    Comprueba que JsonFormatter:

        - Incorpore el identificador de traza activo.
        - Mantenga independientes las trazas simuladas.
        - Excluya determinados campos sensibles.
        - Sustituya mensajes no autorizados.
        - Conserve metadatos técnicos permitidos.
        - Descarte valores numéricos no finitos.

    Los registros se crean directamente mediante LogRecord
    y se procesan sin escribir archivos de log reales.
    """

    # --------------------------------------------------------
    # 2.1. IDENTIFICADOR AUTOMÁTICO DE TRAZABILIDAD
    # --------------------------------------------------------

    def test_trace_id_automatico_desde_contextvars(self):
        """Comprueba la incorporación automática del trace_id.

        Establece un identificador de traza en la variable
        de contexto trace_id_var.

        Construye un evento de registro y lo convierte
        a JSON mediante JsonFormatter.

        Verificaciones:
            - El campo trace_id contiene el valor activo.
            - El campo msg conserva el evento autorizado.
            - El campo level indica el nivel INFO.

        El bloque finally restaura el contexto anterior
        mediante el token devuelto por contextvars.
        """

        # Establece el identificador de traza
        # correspondiente a la consulta simulada.
        token = trace_id_var.set("trace-prueba-001")

        try:
            # Construye un evento de registro de nivel INFO.
            registro = logging.LogRecord(
                name="rag_pipeline",
                level=logging.INFO,
                pathname=__file__,
                lineno=1,
                msg="consulta_iniciada",
                args=(),
                exc_info=None,
            )

            # Convierte el registro al formato JSON
            # y recupera sus campos como diccionario.
            resultado = JsonFormatter().format(registro)
            datos = json.loads(resultado)

            # Comprueba que se haya incorporado
            # el identificador de traza activo.
            self.assertEqual(
                datos["trace_id"],
                "trace-prueba-001",
            )

            # Verifica la conservación del nombre del evento.
            self.assertEqual(
                datos["msg"],
                "consulta_iniciada",
            )

            # Comprueba que el nivel del registro sea INFO.
            self.assertEqual(
                datos["level"],
                "INFO",
            )

        finally:
            # Restaura el valor anterior de la variable
            # de contexto para evitar interferencias.
            trace_id_var.reset(token)

    # --------------------------------------------------------
    # 2.2. INDEPENDENCIA DE TRAZAS ENTRE CONSULTAS
    # --------------------------------------------------------

    def test_consultas_independientes_tienen_trazas_distintas(self):
        """Comprueba que distintas consultas utilicen trazas diferentes.

        Simula dos contextos de ejecución consecutivos,
        cada uno con su propio identificador de traza.

        Para cada contexto:
            - Establece un trace_id diferente.
            - Construye un registro.
            - Obtiene el identificador incluido en el JSON.
            - Restaura el contexto anterior.

        Verificaciones:
            - Los identificadores conservan el orden esperado.
            - Cada registro utiliza su propia traza.
            - El contexto queda sin identificador activo
              al finalizar la prueba.

        Este escenario comprueba el manejo secuencial
        de contextos, no la concurrencia entre solicitudes.
        """

        # Reutiliza el mismo formateador para ambos registros.
        formatter = JsonFormatter()

        # Almacena los identificadores obtenidos
        # desde los registros generados.
        identificadores = []

        # Simula dos consultas consecutivas.
        for indice in range(2):

            # Establece un identificador diferente
            # para la consulta actual.
            token = trace_id_var.set(f"trace-consulta-{indice}")

            try:
                # Construye un evento de inicio de consulta.
                registro = logging.LogRecord(
                    name="rag_pipeline",
                    level=logging.INFO,
                    pathname=__file__,
                    lineno=1,
                    msg="consulta_iniciada",
                    args=(),
                    exc_info=None,
                )

                # Formatea el registro y almacena
                # el identificador de traza obtenido.
                datos = json.loads(formatter.format(registro))
                identificadores.append(datos["trace_id"])

            finally:
                # Restaura el contexto anterior
                # después de cada consulta simulada.
                trace_id_var.reset(token)

        # Comprueba que cada consulta haya conservado
        # su identificador de traza correspondiente.
        self.assertEqual(
            identificadores,
            ["trace-consulta-0", "trace-consulta-1"],
        )

        # Verifica que no permanezca un identificador
        # activo después de finalizar ambos contextos.
        self.assertIsNone(trace_id_var.get())

    # --------------------------------------------------------
    # 2.3. EXCLUSIÓN DE CAMPOS SENSIBLES
    # --------------------------------------------------------

    def test_no_expone_datos_sensibles(self):
        """Comprueba la exclusión de datos sensibles en extra_data.

        Construye un registro con campos adicionales
        que contienen información privada simulada.

        Campos sensibles:
            - pregunta: contiene un RUT de ejemplo.
            - respuesta: contiene información privada.

        Campos técnicos permitidos:
            - pregunta_len: longitud de la consulta.
            - k: cantidad de resultados solicitados.

        Verificaciones:
            - Los campos pregunta y respuesta no aparecen.
            - Los valores privados no aparecen en el JSON.
            - Los campos técnicos permitidos se conservan.

        Esta prueba comprueba la minimización de datos
        para los campos incluidos en el escenario.
        """

        # Construye un evento de registro autorizado.
        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="consulta_iniciada",
            args=(),
            exc_info=None,
        )

        # Incorpora metadatos adicionales.
        #
        # Algunos contienen información privada simulada,
        # mientras que otros representan métricas técnicas.
        registro.extra_data = {
            "pregunta": "Mi RUT es 12345678-9",
            "respuesta": "Información privada",
            "pregunta_len": 20,
            "k": 3,
        }

        # Genera el registro JSON y recupera sus campos.
        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        # Los campos que contienen el texto completo
        # de la consulta y respuesta deben excluirse.
        self.assertNotIn("pregunta", datos)
        self.assertNotIn("respuesta", datos)

        # Los valores sensibles tampoco deben aparecer
        # en ninguna parte del contenido generado.
        self.assertNotIn("12345678-9", resultado)
        self.assertNotIn("Información privada", resultado)

        # Las métricas técnicas permitidas deben conservarse.
        self.assertEqual(datos["pregunta_len"], 20)
        self.assertEqual(datos["k"], 3)

    # --------------------------------------------------------
    # 2.4. SUSTITUCIÓN DE MENSAJES NO AUTORIZADOS
    # --------------------------------------------------------

    def test_no_expone_mensaje_sensible(self):
        """Comprueba que un mensaje sensible sea sustituido.

        Construye un evento cuyo campo msg contiene
        una consulta completa con un RUT de ejemplo.

        Verificaciones:
            - El RUT no aparece en el registro generado.
            - El texto original de la consulta no aparece.
            - El mensaje se sustituye por evento_no_autorizado.

        Este comportamiento evita conservar directamente
        el contenido de un mensaje no autorizado.
        """

        # Construye un registro cuyo mensaje contiene
        # información privada simulada.
        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Consulta del usuario: Mi RUT es 12345678-9",
            args=(),
            exc_info=None,
        )

        # Formatea el registro y recupera sus campos.
        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        # Comprueba que el identificador privado
        # no aparezca en el contenido generado.
        self.assertNotIn("12345678-9", resultado)

        # El texto original de la consulta
        # tampoco debe permanecer en el registro.
        self.assertNotIn("Consulta del usuario", resultado)

        # El formateador debe utilizar el nombre
        # del evento alternativo autorizado.
        self.assertEqual(
            datos["msg"],
            "evento_no_autorizado",
        )

    # --------------------------------------------------------
    # 2.5. VALIDACIÓN DE METADATOS DEL MODELO
    # --------------------------------------------------------

    def test_modelo_autorizado_y_modelo_sensible(self):
        """Comprueba la validación del campo modelo.

        Evalúa dos escenarios sobre un mismo registro:

        Primer escenario:
            - El campo modelo contiene el nombre configurado
              para el modelo de generación de VyOps.
            - El campo n_documentos contiene una métrica técnica.

        Segundo escenario:
            - El campo modelo contiene información privada
              simulada en lugar de un nombre autorizado.
            - El campo n_documentos conserva su valor.

        Verificaciones:
            - El modelo autorizado se conserva.
            - La cantidad de documentos se conserva.
            - El modelo no autorizado se excluye.
            - El dato sensible no aparece en el JSON.

        Esta prueba comprueba la validación del valor
        del campo modelo para los dos casos definidos.
        """

        # Importa el identificador del modelo
        # de generación configurado en VyOps.
        from configuracion_modelos import MODELO_GENERACION

        # Construye un evento relacionado
        # con el inicio de la generación.
        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="generacion_iniciada",
            args=(),
            exc_info=None,
        )

        # Primer escenario:
        # utiliza el modelo configurado y una métrica permitida.
        registro.extra_data = {
            "modelo": MODELO_GENERACION,
            "n_documentos": 3,
        }

        # Formatea el registro con valores autorizados.
        datos = json.loads(JsonFormatter().format(registro))

        # Comprueba que ambos campos se conserven.
        self.assertEqual(datos["modelo"], MODELO_GENERACION)
        self.assertEqual(datos["n_documentos"], 3)

        # Segundo escenario:
        # sustituye el nombre del modelo por un valor
        # que contiene información privada simulada.
        registro.extra_data = {
            "modelo": "Mi RUT es 12345678-9",
            "n_documentos": 3,
        }

        # Genera nuevamente el registro JSON.
        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        # El campo modelo debe excluirse
        # cuando contiene el valor no autorizado.
        self.assertNotIn("modelo", datos)

        # El identificador privado no debe aparecer
        # en el contenido del registro.
        self.assertNotIn("12345678-9", resultado)

        # La métrica técnica debe permanecer disponible.
        self.assertEqual(datos["n_documentos"], 3)

    # --------------------------------------------------------
    # 2.6. EXCLUSIÓN DE VALORES NUMÉRICOS NO FINITOS
    # --------------------------------------------------------

    def test_descarta_numeros_no_finitos(self):
        """Comprueba la exclusión de un valor NaN.

        Construye un registro que contiene:

            - n_documentos: valor entero válido.
            - latencia_ms: valor numérico NaN.

        NaN representa un valor numérico no definido.

        Verificaciones:
            - El número de documentos se conserva.
            - El campo latencia_ms se excluye.
            - El texto NaN no aparece en el JSON generado.

        Esta prueba comprueba específicamente el caso NaN.
        No verifica por separado los valores infinitos.
        """

        # Construye un evento de recuperación documental.
        registro = logging.LogRecord(
            name="rag_pipeline",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="documentos_recuperados",
            args=(),
            exc_info=None,
        )

        # Incorpora una métrica válida y una latencia NaN.
        #
        # El valor NaN representa un resultado numérico
        # que no debe persistirse en este escenario.
        registro.extra_data = {
            "n_documentos": 3,
            "latencia_ms": float("nan"),
        }

        # Genera el registro JSON y recupera sus campos.
        resultado = JsonFormatter().format(registro)
        datos = json.loads(resultado)

        # El número de documentos debe conservarse.
        self.assertEqual(datos["n_documentos"], 3)

        # El campo con valor NaN debe descartarse.
        self.assertNotIn("latencia_ms", datos)

        # El contenido JSON no debe incluir el texto NaN.
        self.assertNotIn("NaN", resultado)
