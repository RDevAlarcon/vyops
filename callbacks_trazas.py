
"""Demuestra la trazabilidad de operaciones LangChain mediante callbacks.

Este módulo implementa un manejador de eventos que permite observar
el inicio y la finalización de operaciones de recuperación documental
y generación de respuestas.

Incluye:
    - Un logger para emitir eventos estructurados en JSON.
    - Un manejador de callbacks basado en BaseCallbackHandler.
    - Un recuperador fijo para simular consultas documentales.
    - Un modelo de lenguaje simulado mediante FakeListLLM.
    - Una demostración de los eventos generados por LangChain.

Los eventos registran cantidades y longitudes, evitando incluir
el texto completo de las consultas, los documentos recuperados
y las respuestas generadas.

Este módulo utiliza componentes simulados de LangChain.
No necesita consultar Gemini ni acceder a ChromaDB.

La demostración se ejecuta al importar el módulo, porque las
invocaciones de ejemplo se encuentran en el ámbito global.
"""

import json
import logging
import sys

from typing import List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from langchain_core.language_models.fake import FakeListLLM


# Logger dedicado a los eventos de trazabilidad del pipeline.
# Los mensajes se emiten directamente a stdout en formato JSON.
logger = logging.getLogger("trazas_pipeline")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))

# Sustituye los handlers existentes para este logger y evita
# que sus eventos se propaguen a otros loggers superiores.
logger.handlers = [handler]
logger.propagate = False


class HandlerDeTrazas(BaseCallbackHandler):
    """Registra eventos de recuperación y generación de LangChain.

    Implementa métodos de callback que LangChain invoca
    al comenzar y finalizar determinadas operaciones.

    Los eventos registrados son:
        - retriever_start: Inicio de recuperación documental.
        - retriever_end: Finalización de recuperación documental.
        - llm_start: Inicio de generación con un modelo.
        - llm_end: Finalización de generación con un modelo.

    Cada evento se serializa como JSON y se envía
    mediante el logger de trazabilidad.

    Notes:
        Los eventos contienen métricas agregadas, no el
        contenido completo de consultas o respuestas.

        Los identificadores de ejecución recibidos desde
        LangChain no se incorporan a los registros actuales.

        Esta implementación registra los eventos disponibles
        sin modificar el comportamiento de los componentes.
    """

    def on_retriever_start(
        self,
        serialized,
        query,
        *,
        run_id,
        parent_run_id=None,
        tags=None,
        metadata=None,
        **kwargs,
    ):
        """Registra el inicio de una recuperación documental.

        Args:
            serialized: Información serializada del recuperador.
            query: Consulta enviada al recuperador.
            run_id: Identificador de ejecución asignado
                por LangChain.
            parent_run_id: Identificador de la ejecución padre,
                cuando existe.
            tags: Etiquetas opcionales de la ejecución.
            metadata: Metadatos opcionales de la ejecución.
            **kwargs: Argumentos adicionales proporcionados
                por LangChain.

        Returns:
            None: Emite un evento de logging sin devolver datos.

        Notes:
            Solo se registra la longitud de la consulta.
            Su contenido textual no se incluye en el evento.
        """
        logger.info(
            json.dumps({
                "evento": "retriever_start",
                "query_len": len(query),
            })
        )

    def on_retriever_end(
        self,
        documents,
        *,
        run_id,
        parent_run_id=None,
        **kwargs,
    ):
        """Registra la finalización de una recuperación documental.

        Args:
            documents: Documentos devueltos por el recuperador.
            run_id: Identificador de ejecución de LangChain.
            parent_run_id: Identificador de la ejecución padre,
                cuando existe.
            **kwargs: Argumentos adicionales del callback.

        Returns:
            None: Emite un evento con la cantidad de documentos.

        Notes:
            No registra el contenido ni los metadatos
            individuales de los documentos recuperados.
        """
        logger.info(
            json.dumps({
                "evento": "retriever_end",
                "n_documentos": len(documents),
            })
        )

    def on_llm_start(
        self,
        serialized,
        prompts,
        *,
        run_id,
        parent_run_id=None,
        **kwargs,
    ):
        """Registra el inicio de una operación de generación.

        Args:
            serialized: Información serializada del modelo.
            prompts: Colección de prompts recibidos por el modelo.
            run_id: Identificador de ejecución de LangChain.
            parent_run_id: Identificador de la ejecución padre,
                cuando existe.
            **kwargs: Argumentos adicionales del callback.

        Returns:
            None: Emite un evento con la cantidad de prompts.

        Notes:
            El contenido de los prompts no se incorpora
            al registro de trazabilidad.
        """
        logger.info(
            json.dumps({
                "evento": "llm_start",
                "n_prompts": len(prompts),
            })
        )

    def on_llm_end(
        self,
        response,
        *,
        run_id,
        parent_run_id=None,
        **kwargs,
    ):
        """Registra la finalización de una operación de generación.

        Args:
            response: Resultado de generación proporcionado
                por LangChain.
            run_id: Identificador de ejecución de LangChain.
            parent_run_id: Identificador de la ejecución padre,
                cuando existe.
            **kwargs: Argumentos adicionales del callback.

        Returns:
            None: Emite un evento con el número total
            de generaciones producidas.

        Notes:
            El resultado puede contener varios grupos
            de generaciones. Se suman las cantidades
            de todos los grupos disponibles.

            No se registra el texto de las respuestas.
        """
        # Suma las generaciones de todos los grupos devueltos
        # por LangChain, sin registrar sus contenidos.
        logger.info(
            json.dumps({
                "evento": "llm_end",
                "n_generaciones": sum(
                    len(grupo) for grupo in response.generations
                ),
            })
        )


class RetrieverFijo(BaseRetriever):
    """Recuperador simulado que devuelve documentos predefinidos.

    Permite demostrar el funcionamiento de los callbacks
    de recuperación sin consultar una base de datos vectorial.

    Attributes:
        documentos (List[Document]): Documentos que serán
            devueltos por cada consulta.

    Notes:
        El recuperador no realiza búsquedas semánticas.

        Devuelve la colección configurada independientemente
        del contenido de la consulta recibida.
    """

    documentos: List[Document] = []

    def _get_relevant_documents(
        self,
        query,
        *,
        run_manager=None,
    ):
        """Devuelve los documentos configurados en el recuperador.

        Args:
            query: Consulta recibida desde LangChain.
                No se utiliza para filtrar los documentos.
            run_manager: Administrador de ejecución opcional
                proporcionado por LangChain.

        Returns:
            List[Document]: Colección de documentos configurados.

        Notes:
            No aplica ranking, filtros ni búsquedas vectoriales.
            Devuelve directamente la colección almacenada.
        """
        return self.documentos


# ============================================================
# DEMOSTRACIÓN DE CALLBACKS
# ============================================================

# Documento ficticio utilizado para demostrar una recuperación.
docs = [
    Document(
        page_content="Política de devoluciones: 30 días.",
        metadata={"fuente": "manual.pdf"},
    )
]

# Recuperador de ejemplo y manejador de trazabilidad.
retriever = RetrieverFijo(documentos=docs)
handler_trazas = HandlerDeTrazas()

# Ejecuta la recuperación y registra sus eventos de inicio
# y finalización mediante el manejador configurado.
resultado = retriever.invoke(
    "cual es la politica de devoluciones",
    config={"callbacks": [handler_trazas]},
)

# Modelo simulado que devuelve una respuesta predefinida.
# FakeListLLM evita realizar solicitudes a un proveedor externo.
llm = FakeListLLM(
    responses=["La política permite devoluciones dentro de 30 días."]
)

# Ejecuta la generación simulada y registra los callbacks
# correspondientes al inicio y finalización del modelo.
respuesta = llm.invoke(
    "Resume la política de devoluciones.",
    config={"callbacks": [handler_trazas]},
)
