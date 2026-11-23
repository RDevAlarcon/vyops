
"""Pruebas unitarias de persistencia y privacidad de registros RAG de VyOps.

Este módulo verifica el comportamiento de guardar_registro_jsonl(),
implementado en persistencia_rag.py.

La persistencia RAG permite almacenar información técnica
sobre las ejecuciones del sistema, incluyendo:

    - Identificadores de trazabilidad.
    - Modelos utilizados para generación y embeddings.
    - Fuentes documentales.
    - Tiempos de procesamiento.
    - Consumo de tokens.
    - Costos estimados.
    - Resultados de validación de citas.

Las pruebas cubren tres escenarios:

    1. Escritura y acumulación de registros JSONL.
    2. Exclusión del contenido completo de las preguntas.
    3. Exclusión de metadatos sensibles de las fuentes
       y de los datos originales de consumo.

Se utilizan directorios temporales para evitar modificar
los archivos de trazabilidad reales del proyecto.

Estas pruebas verifican propiedades concretas del registro
persistido. No constituyen una auditoría completa de
privacidad ni garantizan la eliminación de cualquier
dato sensible que pudiera aparecer en otros campos.

No realizan llamadas a Gemini ni utilizan ChromaDB.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite convertir registros JSONL en objetos Python
# para verificar los valores almacenados.
import json

# Proporciona directorios temporales que se eliminan
# automáticamente al finalizar cada escenario.
import tempfile

# Framework estándar para organizar y ejecutar
# las pruebas unitarias.
import unittest

# Facilita la construcción de rutas de archivos.
from pathlib import Path

# Función encargada de guardar registros RAG
# en archivos con formato JSON Lines.
from persistencia_rag import guardar_registro_jsonl


# ============================================================
# 2. PRUEBAS DE PERSISTENCIA RAG
# ============================================================

class TestPersistenciaRAG(unittest.TestCase):
    """Verifica la escritura, acumulación y privacidad de registros.

    Comprueba que guardar_registro_jsonl() conserve
    información técnica relevante para la trazabilidad
    y aplique las restricciones de persistencia evaluadas.

    Cada prueba utiliza un directorio temporal independiente
    para evitar interferencias entre archivos.
    """

    # --------------------------------------------------------
    # 2.1. ESCRITURA Y ACUMULACIÓN DE REGISTROS
    # --------------------------------------------------------

    def test_guardar_y_acumular_registros(self):
        """Comprueba que los registros se acumulen en un archivo JSONL.

        Prepara un resultado RAG simulado que incluye
        trazabilidad, modelos, tiempos, tokens, costos
        y validación de citas.

        Guarda el mismo resultado dos veces y comprueba:

            - El archivo contiene dos líneas.
            - Cada línea representa un objeto JSON válido.
            - Se conserva el total de tokens.
            - Los valores nulos se recuperan como None.
            - Se conserva el modelo de generación.
            - Se incorpora un campo timestamp.
            - Ambas entradas conservan el trace_id original.

        La prueba verifica la acumulación de registros
        sin sobrescribir la entrada anterior.
        """

        # Construye un resultado RAG simulado.
        #
        # Los valores representan información técnica
        # que puede producir una ejecución del sistema.
        resultado = {
            "trace_id": "traza-prueba-001",
            "modelo_generacion": "gemini-3.5-flash-lite",
            "modelo_embedding": "gemini-embedding-001",
            "pregunta": "¿Cómo consultar una solicitud?",
            "fuentes": ["solicitudes_consulta.md"],
            "tiempos": {
                "recuperacion": 0.5,
                "generacion": 1.2,
                "total_rag": 1.8,
                "total_completo": 2.0,
            },
            "tokens_entrada": 100,
            "tokens_salida": 50,
            "tokens_totales": 150,
            "tokens_razonamiento": None,
            "tokens_cache": 0,
            "tokens_embedding": 8,
            "uso_original": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            },
            "costo_generacion_usd": 0.000155,
            "costo_embedding_usd": 0.0000012,
            "costo_total_usd": 0.0001562,
            "validacion_citas": {
                "citas_encontradas": 1,
                "citas_invalidas": [],
                "numeracion_valida": True,
            },
        }

        # Crea un directorio temporal para almacenar
        # el archivo de prueba sin afectar los registros reales.
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "prueba_rag.jsonl"

            # Guarda dos veces el mismo resultado.
            #
            # Cada llamada debe agregar una entrada
            # independiente al archivo JSONL.
            guardar_registro_jsonl(resultado, ruta)
            guardar_registro_jsonl(resultado, ruta)

            # Lee el contenido del archivo y lo divide
            # en líneas individuales.
            lineas = ruta.read_text(
                encoding="utf-8"
            ).splitlines()

            # Comprueba que se hayan almacenado dos entradas.
            self.assertEqual(len(lineas), 2)

            # Convierte cada línea JSON en un diccionario
            # para verificar los campos persistidos.
            registros = [
                json.loads(linea) for linea in lineas
            ]

            # Comprueba que se conserve el total de tokens.
            self.assertEqual(
                registros[0]["tokens_totales"], 150
            )

            # Verifica que un valor nulo en JSON
            # se recupere como None en Python.
            self.assertIsNone(
                registros[0]["tokens_razonamiento"]
            )

            # Comprueba la conservación del modelo
            # utilizado para la generación.
            self.assertEqual(
                registros[1]["modelo_generacion"],
                "gemini-3.5-flash-lite",
            )

            # Verifica que el registro incorpore
            # información temporal para trazabilidad.
            self.assertIn("timestamp", registros[0])

            # Comprueba que ambas entradas mantengan
            # el mismo identificador de trazabilidad.
            self.assertEqual(
                registros[0]["trace_id"],
                "traza-prueba-001",
            )
            self.assertEqual(
                registros[1]["trace_id"],
                "traza-prueba-001",
            )

    # --------------------------------------------------------
    # 2.2. PRIVACIDAD DEL CONTENIDO DE LAS PREGUNTAS
    # --------------------------------------------------------

    def test_no_guardar_pregunta_completa(self):
        """Comprueba que no se persista el texto completo de una pregunta.

        Prepara una consulta que contiene un identificador
        personal ficticio con formato de RUT.

        Después guarda el resultado RAG y verifica:

            - La pregunta original no aparece en el archivo.
            - No existe una clave llamada "pregunta".
            - Se conserva únicamente la longitud de la pregunta
              mediante el campo "pregunta_longitud".

        Esta prueba verifica una medida concreta
        de minimización de datos en la persistencia.
        """

        # Define una pregunta con un RUT de ejemplo.
        #
        # El texto se utiliza exclusivamente
        # para comprobar que no quede persistido.
        pregunta = "Mi RUT es 12345678-9"

        # Construye un resultado RAG con los campos
        # necesarios para el escenario de privacidad.
        resultado = {
            "modelo_generacion": "modelo-prueba",
            "modelo_embedding": "embedding-prueba",
            "pregunta": pregunta,
            "fuentes": [],
            "tiempos": {
                "total_rag": 0.5,
                "total_completo": 0.6,
            },
            "tokens_entrada": 10,
            "tokens_salida": 5,
            "tokens_totales": 15,
            "tokens_razonamiento": None,
            "tokens_cache": None,
            "tokens_embedding": 3,
            "uso_original": {},
            "costo_generacion_usd": 0.0,
            "costo_embedding_usd": 0.0,
            "costo_total_usd": 0.0,
            "validacion_citas": {},
        }

        # Crea un archivo temporal destinado
        # a comprobar la privacidad de las preguntas.
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "privacidad.jsonl"

            # Persiste el resultado mediante
            # la función que se está evaluando.
            guardar_registro_jsonl(resultado, ruta)

            # Lee el contenido textual completo
            # y convierte el registro a un diccionario.
            contenido = ruta.read_text(encoding="utf-8")
            registro = json.loads(contenido)

            # La pregunta original no debe aparecer
            # en ninguna parte del archivo.
            self.assertNotIn(pregunta, contenido)

            # El registro no debe contener
            # una clave con el texto de la pregunta.
            self.assertNotIn("pregunta", registro)

            # Se permite conservar la cantidad de caracteres
            # como información técnica de la consulta.
            self.assertEqual(
                registro["pregunta_longitud"],
                len(pregunta),
            )

    # --------------------------------------------------------
    # 2.3. PRIVACIDAD DE METADATOS Y DATOS DE CONSUMO
    # --------------------------------------------------------

    def test_no_persistir_metadatos_sensibles(self):
        """Comprueba que se excluyan determinados metadatos sensibles.

        Construye un resultado RAG con un marcador sensible
        ficticio incorporado en dos ubicaciones:

            - El nombre de un archivo documental.
            - Un campo adicional de uso_original.

        Después guarda el registro y comprueba:

            - El marcador sensible no aparece en el archivo.
            - El campo "dato_externo" no se conserva.
            - El campo permitido "input_tokens" permanece.

        La prueba verifica que la persistencia pueda
        conservar métricas técnicas sin almacenar
        los datos sensibles incluidos en este escenario.
        """

        # Define una consulta de ejemplo y un marcador
        # que representa información sensible.
        pregunta = "Consulta municipal de prueba"
        dato_sensible = "RUT-PRIVADO-12345678-9"

        # Construye un resultado que incluye el marcador
        # sensible tanto en las fuentes documentales
        # como en los metadatos originales de consumo.
        resultado = {
            "trace_id": "traza-privacidad-001",
            "modelo_generacion": "gemini-3.5-flash-lite",
            "modelo_embedding": "gemini-embedding-001",
            "pregunta": pregunta,
            "fuentes": [f"documento_{dato_sensible}.md"],
            "tiempos": {
                "total_rag": 0.5,
                "total_completo": 0.6,
            },
            "tokens_entrada": 10,
            "tokens_salida": 5,
            "tokens_totales": 15,
            "tokens_razonamiento": None,
            "tokens_cache": 0,
            "tokens_embedding": 3,
            "uso_original": {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
                "dato_externo": dato_sensible,
            },
            "costo_generacion_usd": 0.0,
            "costo_embedding_usd": 0.0,
            "costo_total_usd": 0.0,
            "validacion_citas": {
                "citas_encontradas": 1,
                "citas_invalidas": [],
                "numeracion_valida": True,
            },
        }

        # Crea un directorio temporal para comprobar
        # el contenido persistido sin modificar otros archivos.
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "privacidad_metadatos.jsonl"

            # Guarda el resultado que contiene
            # los metadatos sensibles simulados.
            guardar_registro_jsonl(resultado, ruta)

            # Recupera el contenido textual y el objeto JSON.
            contenido = ruta.read_text(encoding="utf-8")
            registro = json.loads(contenido)

            # El marcador sensible no debe aparecer
            # en ninguna parte del archivo persistido.
            self.assertNotIn(dato_sensible, contenido)

            # El campo adicional no autorizado
            # debe excluirse de uso_original.
            self.assertNotIn("dato_externo", registro["uso_original"])

            # Los datos técnicos permitidos deben conservarse
            # para mantener la utilidad del registro.
            self.assertEqual(
                registro["uso_original"]["input_tokens"], 10
            )


# ============================================================
# 3. EJECUCIÓN DIRECTA DE LAS PRUEBAS
# ============================================================

if __name__ == "__main__":

    # Ejecuta las pruebas del módulo cuando
    # el archivo se inicia directamente.
    unittest.main()
