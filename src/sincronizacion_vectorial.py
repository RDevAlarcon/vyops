
"""Planificacion segura de sincronizacion vectorial para VyOps.

Modo exclusivo de lectura:
- No crea colecciones.
- No genera embeddings.
- No inserta ni elimina registros.
"""

from dataclasses import dataclass
from pathlib import Path

import chromadb

from indexar_corpus import preparar_documentos
from recuperacion import obtener_directorio_vectorial
from src.bloqueo_indexacion import bloqueo_indexacion

BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
NOMBRE_COLECCION = "vyops_municipal_v1"


@dataclass(frozen=True)
class PlanSincronizacion:
    coleccion: str
    documentos_deseados: int
    registros_existentes: int
    insertar: frozenset[str]
    conservar: frozenset[str]
    eliminar: frozenset[str]


def calcular_plan(
    ids_existentes: set[str],
    ids_deseados: set[str],
    nombre_coleccion: str = NOMBRE_COLECCION,
) -> PlanSincronizacion:
    """Calcula diferencias sin modificar el almacenamiento."""

    return PlanSincronizacion(
        coleccion=nombre_coleccion,
        documentos_deseados=len(ids_deseados),
        registros_existentes=len(ids_existentes),
        insertar=frozenset(ids_deseados - ids_existentes),
        conservar=frozenset(ids_deseados & ids_existentes),
        eliminar=frozenset(ids_existentes - ids_deseados),
    )


def obtener_ids_existentes() -> set[str]:
    """Consulta los IDs existentes sin crear colecciones."""

    directorio = obtener_directorio_vectorial()

    if not directorio.is_dir():
        return set()

    # Evita inicializar ChromaDB en un directorio vacío.
    if not (directorio / "chroma.sqlite3").is_file():
        return set()

    cliente = chromadb.PersistentClient(path=str(directorio))

    nombres = {
        coleccion.name
        for coleccion in cliente.list_collections()
    }

    if NOMBRE_COLECCION not in nombres:
        return set()

    coleccion = cliente.get_collection(name=NOMBRE_COLECCION)

    resultado = coleccion.get(include=[])

    return set(resultado["ids"])


def preparar_plan() -> PlanSincronizacion:
    """Prepara el plan bajo bloqueo exclusivo temporal."""
    with bloqueo_indexacion():
        _, identificadores = preparar_documentos()

        if len(identificadores) != len(set(identificadores)):
            raise ValueError("Identificadores duplicados")

        return calcular_plan(
            ids_existentes=obtener_ids_existentes(),
            ids_deseados=set(identificadores),
        )

def main() -> None:
    plan = preparar_plan()

    print("Coleccion:", plan.coleccion)
    print("Fragmentos deseados:", plan.documentos_deseados)
    print("Registros existentes:", plan.registros_existentes)
    print("Insertar:", len(plan.insertar))
    print("Conservar:", len(plan.conservar))
    print("Eliminar:", len(plan.eliminar))

    assert (
        len(plan.insertar) + len(plan.conservar)
        == plan.documentos_deseados
    )

    assert (
        len(plan.eliminar) + len(plan.conservar)
        == plan.registros_existentes
    )

    print("\nPASS: Plan de sincronizacion preparado.")
    print("Modo: solo lectura.")
    print("Gemini: sin llamadas.")


if __name__ == "__main__":
    main()


def validar_limpieza(
    documentos_cargados: int,
    registros_existentes: int,
    registros_a_eliminar: int,
    minimo_documentos: int = 30,
    maximo_porcentaje: float = 20.0,
) -> tuple[bool, str]:
    """Evalua limites de seguridad antes de una limpieza."""

    if documentos_cargados < minimo_documentos:
        return False, "Corpus incompleto"

    if registros_existentes < 0 or registros_a_eliminar < 0:
        return False, "Cantidades invalidas"

    if registros_a_eliminar > registros_existentes:
        return False, "Cantidad de eliminaciones invalida"

    if registros_existentes == 0:
        return True, "Sin registros anteriores"

    porcentaje = (
        registros_a_eliminar / registros_existentes
    ) * 100

    if porcentaje > maximo_porcentaje:
        return False, "Eliminacion masiva detectada"

    return True, "Limpieza dentro de los limites"


def autorizar_limpieza(
    ids_almacenados: set[str],
    ids_deseados: set[str],
    documentos_cargados: int,
) -> tuple[bool, str]:
    """Exige incorporacion completa y limites de limpieza seguros."""

    faltantes = ids_deseados - ids_almacenados

    if faltantes:
        return False, "Incorporacion incompleta"

    obsoletos = ids_almacenados - ids_deseados

    return validar_limpieza(
        documentos_cargados=documentos_cargados,
        registros_existentes=len(ids_almacenados),
        registros_a_eliminar=len(obsoletos),
    )