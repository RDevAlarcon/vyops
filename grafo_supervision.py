
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


def proponer(estado: EstadoDespliegue):
    """Presenta la versión candidata para revisión."""
    print(f"Versión propuesta: {estado['huella_nueva']}")
    return {}


def supervisar(estado: EstadoDespliegue):
    """Detiene el flujo hasta recibir aprobación humana."""
    decision = interrupt({
        "motivo": "Aprobar o rechazar nueva versión del prompt",
        "huella_nueva": estado["huella_nueva"],
    })

    if not isinstance(decision, bool):
        raise ValueError("La decisión humana debe ser True o False.")

    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue):
    """Simula la activación únicamente si existe aprobación."""
    if estado["aprobado"] is True:
        print(f"Versión ACTIVADA: {estado['huella_nueva']}")
    else:
        print(f"Versión RECHAZADA: {estado['huella_nueva']}")

    return {}


def construir_grafo():
    grafo = StateGraph(EstadoDespliegue)

    grafo.add_node("proponer", proponer)
    grafo.add_node("supervisar", supervisar)
    grafo.add_node("aplicar", aplicar)

    grafo.add_edge(START, "proponer")
    grafo.add_edge("proponer", "supervisar")
    grafo.add_edge("supervisar", "aplicar")
    grafo.add_edge("aplicar", END)

    return grafo.compile(checkpointer=InMemorySaver())



if __name__ == "__main__":
    app = construir_grafo()

    # 1. Proponer una versión y detener el flujo.
    config = {
        "configurable": {
            "thread_id": "vyops-supervision-demo-1"
        }
    }

    resultado = app.invoke(
        {
            "huella_nueva": "fdff8ebf6d37",
            "aprobado": False,
        },
        config=config,
    )

    print("\n=== SUPERVISIÓN HUMANA ===")
    print("1) tras invocar:", resultado)
    print("Flujo interrumpido:", "__interrupt__" in resultado)

    # 2. Consultar la solicitud de aprobación pendiente.
    estado_pendiente = app.get_state(config)

    print("2) pendiente:", estado_pendiente.interrupts[0].value)
    print("Estado pendiente:", estado_pendiente.next)

    # 3. Aprobar la versión y reanudar el flujo.
    print("\n=== APROBACIÓN HUMANA ===")

    resultado_aprobado = app.invoke(
        Command(resume=True),
        config=config,
    )

    print("3) tras aprobar:", resultado_aprobado)
    print("Decisión registrada:", resultado_aprobado["aprobado"])
    print(
    "Estado final:",
    "FINALIZADO" if not app.get_state(config).next else "PENDIENTE"
    )

    # 4. Iniciar otra ejecución independiente para probar el rechazo.
    print("\n=== RECHAZO HUMANO ===")

    config_rechazo = {
        "configurable": {
            "thread_id": "vyops-supervision-demo-rechazo"
        }
    }

    resultado_pendiente = app.invoke(
        {
            "huella_nueva": "fdff8ebf6d37",
            "aprobado": False,
        },
        config=config_rechazo,
    )

    print(
        "Flujo interrumpido:",
        "__interrupt__" in resultado_pendiente,
    )

    # Rechazar la versión propuesta.
    resultado_rechazado = app.invoke(
        Command(resume=False),
        config=config_rechazo,
    )

    print("4) tras rechazar:", resultado_rechazado)
    print("Decisión registrada:", resultado_rechazado["aprobado"])
    print(
    "Estado final:",
    "FINALIZADO" if not app.get_state(config_rechazo).next else "PENDIENTE"
    )   
