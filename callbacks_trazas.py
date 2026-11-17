import json
import logging
import sys

from typing import List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from langchain_core.language_models.fake import FakeListLLM

logger = logging.getLogger("trazas_pipeline")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))

logger.handlers = [handler]
logger.propagate = False


class HandlerDeTrazas(BaseCallbackHandler):

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
        logger.info(
            json.dumps({
                "evento": "llm_end",
                "n_generaciones": sum(
                    len(grupo) for grupo in response.generations
                ),
            })
        )

class RetrieverFijo(BaseRetriever):
    documentos: List[Document] = []

    def _get_relevant_documents(
        self,
        query,
        *,
        run_manager=None,
    ):
        return self.documentos


docs = [
    Document(
        page_content="Política de devoluciones: 30 días.",
        metadata={"fuente": "manual.pdf"},
    )
]

retriever = RetrieverFijo(documentos=docs)
handler_trazas = HandlerDeTrazas()

resultado = retriever.invoke(
    "cual es la politica de devoluciones",
    config={"callbacks": [handler_trazas]},
)

llm = FakeListLLM(
    responses=["La política permite devoluciones dentro de 30 días."]
)

respuesta = llm.invoke(
    "Resume la política de devoluciones.",
    config={"callbacks": [handler_trazas]},
)