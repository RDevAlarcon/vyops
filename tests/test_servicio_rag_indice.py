
"""Pruebas de verificación del índice vectorial del servicio RAG de VyOps.

Este módulo comprueba el comportamiento de verificar_indice(),
implementado en servicio_vyops_rag.py.

El objetivo es validar las condiciones mínimas que debe
cumplir el índice documental antes de utilizarlo
en el servicio de recuperación aumentada (RAG).

Las pruebas contemplan tres escenarios:

    1. Directorio existente con identificadores persistidos.
    2. Directorio del índice inexistente.
    3. Directorio existente con una colección vacía.

Se utilizan directorios temporales y mocks para
simular la configuración y el estado del índice.

Las funciones obtener_directorio_vectorial()
y obtener_ids_existentes() se sustituyen temporalmente
durante las pruebas.

Esto permite comprobar la lógica de validación
sin consultar Gemini ni modificar ChromaDB.

El módulo utiliza unittest como framework de pruebas
y puede ejecutarse directamente mediante unittest.main().
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite crear directorios temporales que se eliminan
# automáticamente al finalizar su contexto.
import tempfile

# Framework estándar para implementar pruebas unitarias.
import unittest

# Facilita la construcción y comprobación de rutas.
from pathlib import Path

# Permite sustituir funciones del módulo evaluado
# por respuestas controladas durante las pruebas.
from unittest.mock import patch

# Módulo que contiene la función verificar_indice()
# y las dependencias utilizadas para validar el índice.
import servicio_vyops_rag


# ============================================================
# 2. PRUEBAS DE VALIDACIÓN DEL ÍNDICE VECTORIAL
# ============================================================

class TestServicioRAGIndice(unittest.TestCase):
    """Valida el índice sin consultar Gemini ni modificar ChromaDB.

    Comprueba el comportamiento de verificar_indice()
    frente a diferentes estados del directorio vectorial.

    Los escenarios utilizan directorios temporales
    y sustituciones controladas de las funciones
    que obtienen la ubicación y los identificadores
    de los documentos persistidos.

    No se utiliza el índice real de VyOps.
    """

    # --------------------------------------------------------
    # 2.1. DIRECTORIO EXISTENTE CON IDENTIFICADORES
    # --------------------------------------------------------

    def test_reconoce_directorio_configurado(self):
        """Comprueba la aceptación de un índice con identificadores.

        Crea un directorio temporal existente y simula
        una colección con dos identificadores documentales.

        Verificaciones:
            - La validación reconoce dos fragmentos persistidos.
            - El resultado indica que los identificadores
              son únicos.

        El contenido del índice se simula mediante mocks;
        no se consulta una colección real de ChromaDB.
        """

        # Crea un directorio temporal para representar
        # la ubicación configurada del índice vectorial.
        with tempfile.TemporaryDirectory() as temporal:
            directorio = Path(temporal)

            # Sustituye la ruta real del índice
            # y la consulta de identificadores persistidos.
            with (
                patch.object(
                    servicio_vyops_rag,
                    "obtener_directorio_vectorial",
                    return_value=directorio,
                ),
                patch.object(
                    servicio_vyops_rag,
                    "obtener_ids_existentes",
                    return_value={"doc-1", "doc-2"},
                ),
            ):
                # Ejecuta la validación con los datos simulados.
                resultado = servicio_vyops_rag.verificar_indice()

            # Comprueba que se reconozcan los dos identificadores.
            self.assertEqual(resultado["fragmentos_persistidos"], 2)

            # Comprueba el indicador de unicidad devuelto.
            self.assertTrue(resultado["ids_unicos"])

    # --------------------------------------------------------
    # 2.2. DIRECTORIO DEL ÍNDICE INEXISTENTE
    # --------------------------------------------------------

    def test_rechaza_directorio_inexistente(self):
        """Comprueba el rechazo de una ruta que no existe.

        Construye una ruta dentro de un directorio temporal
        sin crear el subdirectorio correspondiente al índice.

        Verificaciones:
            - verificar_indice() lanza RuntimeError.
            - La validación no crea el directorio inexistente.
            - No se intenta consultar identificadores.

        Este escenario verifica que el servicio no acepte
        silenciosamente una ubicación sin índice.
        """

        # Crea un directorio temporal principal.
        with tempfile.TemporaryDirectory() as temporal:

            # Construye una ruta hija que todavía no existe.
            directorio = Path(temporal) / "indice_inexistente"

            # Simula la configuración de la ruta inexistente
            # y observa si se intenta consultar identificadores.
            with (
                patch.object(
                    servicio_vyops_rag,
                    "obtener_directorio_vectorial",
                    return_value=directorio,
                ),
                patch.object(
                    servicio_vyops_rag,
                    "obtener_ids_existentes",
                ) as consultar_ids,
            ):
                # La validación debe rechazar la ruta.
                with self.assertRaises(RuntimeError):
                    servicio_vyops_rag.verificar_indice()

            # Comprueba que la validación no haya creado
            # automáticamente el directorio del índice.
            self.assertFalse(directorio.exists())

            # La consulta de identificadores no debe ejecutarse
            # cuando el directorio no existe.
            consultar_ids.assert_not_called()

    # --------------------------------------------------------
    # 2.3. COLECCIÓN VECTORIAL VACÍA
    # --------------------------------------------------------

    def test_rechaza_coleccion_vacia(self):
        """Comprueba el rechazo de un índice sin identificadores.

        Utiliza un directorio existente y simula
        una colección que no contiene documentos.

        Verificaciones:
            - La validación lanza RuntimeError.
            - El mensaje de error contiene la secuencia "vac".

        Esta prueba distingue entre la existencia física
        del directorio y la disponibilidad de documentos
        dentro de la colección vectorial.
        """

        # Crea un directorio temporal existente.
        with tempfile.TemporaryDirectory() as temporal:
            directorio = Path(temporal)

            # Simula una ubicación válida del índice,
            # pero sin identificadores documentales.
            with (
                patch.object(
                    servicio_vyops_rag,
                    "obtener_directorio_vectorial",
                    return_value=directorio,
                ),
                patch.object(
                    servicio_vyops_rag,
                    "obtener_ids_existentes",
                    return_value=set(),
                ),
            ):
                # La validación debe rechazar la colección vacía.
                #
                # Se comprueba que el mensaje incluya "vac",
                # correspondiente al error esperado.
                with self.assertRaisesRegex(RuntimeError, "vac"):
                    servicio_vyops_rag.verificar_indice()


# ============================================================
# 3. EJECUCIÓN DIRECTA DE LAS PRUEBAS
# ============================================================

if __name__ == "__main__":

    # Ejecuta las pruebas de este módulo cuando
    # se inicia directamente como programa.
    #
    # Este bloque no se ejecuta al importar el módulo
    # desde otro archivo.
    unittest.main()
