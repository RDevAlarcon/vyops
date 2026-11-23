
"""Planifica la sincronización vectorial del corpus municipal de VyOps.

Este módulo compara los identificadores del corpus preparado con
los registros almacenados en ChromaDB.

Permite:
- Identificar fragmentos nuevos que deben incorporarse.
- Reconocer fragmentos existentes que deben conservarse.
- Detectar registros obsoletos candidatos a eliminación.
- Validar condiciones de seguridad antes de autorizar una limpieza.

Las operaciones de planificación son de solo lectura:
no generan embeddings ni insertan o eliminan registros.

Las funciones de autorización únicamente evalúan condiciones.
La eliminación efectiva corresponde al módulo de indexación.
"""

from dataclasses import dataclass
from pathlib import Path

import chromadb

from indexar_corpus import preparar_documentos
from recuperacion import obtener_directorio_vectorial
from src.bloqueo_indexacion import bloqueo_indexacion


# Directorio raíz del proyecto.
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta convencional del índice vectorial original.
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

# Nombre de la colección municipal utilizada por VyOps.
NOMBRE_COLECCION = "vyops_municipal_v1"


@dataclass(frozen=True)
class PlanSincronizacion:
    """Representa el resultado inmutable de una comparación vectorial.

    Attributes:
        coleccion: Nombre de la colección evaluada.
        documentos_deseados: Cantidad de fragmentos del corpus actual.
        registros_existentes: Cantidad de registros almacenados.
        insertar: IDs presentes en el corpus, pero no en ChromaDB.
        conservar: IDs presentes tanto en el corpus como en ChromaDB.
        eliminar: IDs almacenados que ya no aparecen en el corpus.

    El uso de frozen=True impide reasignar los atributos del plan.
    Los conjuntos frozenset también impiden modificar sus elementos.
    """

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
    """Calcula las diferencias entre el índice y el corpus actual.

    La función utiliza operaciones de conjuntos y no accede
    directamente a ChromaDB.

    Args:
        ids_existentes: Identificadores almacenados actualmente.
        ids_deseados: Identificadores generados desde el corpus.
        nombre_coleccion: Colección asociada al plan.

    Returns:
        PlanSincronizacion: Clasificación de los identificadores
        que deben insertarse, conservarse o eliminarse.
    """
    # Diferencia: registros nuevos o registros obsoletos.
    # Intersección: registros que ya están sincronizados.
    return PlanSincronizacion(
        coleccion=nombre_coleccion,
        documentos_deseados=len(ids_deseados),
        registros_existentes=len(ids_existentes),
        insertar=frozenset(ids_deseados - ids_existentes),
        conservar=frozenset(ids_deseados & ids_existentes),
        eliminar=frozenset(ids_existentes - ids_deseados),
    )


def obtener_ids_existentes() -> set[str]:
    """Consulta los identificadores almacenados en ChromaDB.

    Comprueba primero que exista un índice persistente y que
    contenga la colección municipal esperada.

    No crea colecciones ni incorpora documentos.

    Returns:
        set[str]: Identificadores existentes en la colección.
        Devuelve un conjunto vacío cuando el índice o la
        colección todavía no existen.
    """
    directorio = obtener_directorio_vectorial()

    # Evita abrir una base de datos inexistente.
    if not directorio.is_dir():
        return set()

    # Verifica que exista el archivo de persistencia antes
    # de inicializar el cliente de ChromaDB.
    if not (directorio / "chroma.sqlite3").is_file():
        return set()

    cliente = chromadb.PersistentClient(path=str(directorio))

    # Comprueba la existencia de la colección sin crearla.
    nombres = {
        coleccion.name
        for coleccion in cliente.list_collections()
    }

    if NOMBRE_COLECCION not in nombres:
        return set()

    coleccion = cliente.get_collection(name=NOMBRE_COLECCION)

    # Recupera únicamente los IDs, sin solicitar embeddings
    # ni contenido documental.
    resultado = coleccion.get(include=[])

    return set(resultado["ids"])


def preparar_plan() -> PlanSincronizacion:
    """Prepara un plan de sincronización bajo bloqueo temporal.

    Obtiene los identificadores del corpus actual, comprueba
    su unicidad y los compara con los registros existentes.

    Returns:
        PlanSincronizacion: Plan de inserción, conservación
        y eliminación, sin ejecutar los cambios.

    Raises:
        ValueError: Si el corpus contiene IDs duplicados.
    """
    # Evita que otra operación que respete el mismo mecanismo
    # de bloqueo intervenga durante la preparación del plan.
    with bloqueo_indexacion():
        _, identificadores = preparar_documentos()

        if len(identificadores) != len(set(identificadores)):
            raise ValueError("Identificadores duplicados")

        return calcular_plan(
            ids_existentes=obtener_ids_existentes(),
            ids_deseados=set(identificadores),
        )


def main() -> None:
    """Presenta el plan y comprueba sus relaciones de integridad.

    Las cantidades deben satisfacer dos condiciones:
    - Insertar + conservar = fragmentos deseados.
    - Eliminar + conservar = registros existentes.

    La ejecución no genera embeddings ni modifica registros.
    """
    plan = preparar_plan()

    # Presenta las cantidades calculadas para facilitar
    # la revisión y auditoría de la sincronización.
    print("Coleccion:", plan.coleccion)
    print("Fragmentos deseados:", plan.documentos_deseados)
    print("Registros existentes:", plan.registros_existentes)
    print("Insertar:", len(plan.insertar))
    print("Conservar:", len(plan.conservar))
    print("Eliminar:", len(plan.eliminar))

    # Verifica que la clasificación cubra todos los fragmentos
    # deseados y todos los registros existentes.
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
    # La planificación se ejecuta automáticamente solo cuando
    # este archivo se invoca directamente desde la consola.
    main()


def validar_limpieza(
    documentos_cargados: int,
    registros_existentes: int,
    registros_a_eliminar: int,
    minimo_documentos: int = 30,
    maximo_porcentaje: float = 20.0,
) -> tuple[bool, str]:
    """Evalúa los límites de seguridad de una limpieza vectorial.

    La limpieza se rechaza cuando el corpus está incompleto,
    existen cantidades inválidas o el porcentaje de eliminación
    supera el umbral permitido.

    Args:
        documentos_cargados: Documentos originales disponibles.
        registros_existentes: Cantidad actual de registros.
        registros_a_eliminar: Cantidad propuesta para eliminación.
        minimo_documentos: Mínimo exigido para considerar completo
            el corpus. Por defecto, 30 documentos.
        maximo_porcentaje: Porcentaje máximo permitido de
            eliminación. Por defecto, 20 %.

    Returns:
        tuple[bool, str]: Decisión de autorización y motivo.
    """
    # No permite limpiar un índice si el corpus de referencia
    # contiene menos documentos que el mínimo establecido.
    if documentos_cargados < minimo_documentos:
        return False, "Corpus incompleto"

    # Las cantidades negativas representan un estado inválido.
    if registros_existentes < 0 or registros_a_eliminar < 0:
        return False, "Cantidades invalidas"

    # No es posible eliminar más registros de los existentes.
    if registros_a_eliminar > registros_existentes:
        return False, "Cantidad de eliminaciones invalida"

    # Si no existen registros anteriores, no hay nada que eliminar.
    if registros_existentes == 0:
        return True, "Sin registros anteriores"

    porcentaje = (
        registros_a_eliminar / registros_existentes
    ) * 100

    # Bloquea eliminaciones que exceden el porcentaje permitido.
    if porcentaje > maximo_porcentaje:
        return False, "Eliminacion masiva detectada"

    return True, "Limpieza dentro de los limites"


def autorizar_limpieza(
    ids_almacenados: set[str],
    ids_deseados: set[str],
    documentos_cargados: int,
) -> tuple[bool, str]:
    """Autoriza una limpieza solo después de incorporar el corpus.

    Primero comprueba que todos los fragmentos deseados estén
    almacenados. Después evalúa el volumen de registros obsoletos
    mediante validar_limpieza().

    Args:
        ids_almacenados: Identificadores presentes en ChromaDB.
        ids_deseados: Identificadores del corpus preparado.
        documentos_cargados: Número de documentos originales.

    Returns:
        tuple[bool, str]: Indica si la limpieza está autorizada
        y entrega el motivo correspondiente.

    Esta función no elimina registros; únicamente determina
    si se cumplen las condiciones para hacerlo.
    """
    # Impide eliminar registros antes de completar la incorporación
    # de todos los fragmentos deseados.
    faltantes = ids_deseados - ids_almacenados

    if faltantes:
        return False, "Incorporacion incompleta"

    # Solo los IDs que ya no pertenecen al corpus son candidatos
    # a eliminación.
    obsoletos = ids_almacenados - ids_deseados

    return validar_limpieza(
        documentos_cargados=documentos_cargados,
        registros_existentes=len(ids_almacenados),
        registros_a_eliminar=len(obsoletos),
    )
