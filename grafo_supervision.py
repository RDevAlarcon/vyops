
"""Implementa una demostración de supervisión humana con LangGraph.

Este módulo define un flujo de aprobación para versiones
candidatas de prompts del asistente municipal VyOps.

El flujo está compuesto por tres etapas:

    1. Proponer:
       Presenta la huella de la versión candidata.

    2. Supervisar:
       Interrumpe la ejecución hasta recibir una
       decisión humana explícita.

    3. Aplicar:
       Muestra el resultado de aprobación o rechazo
       sin realizar un despliegue real.

Utiliza StateGraph para organizar las etapas,
interrupt() para solicitar intervención humana
y Command(resume=...) para reanudar la ejecución.

InMemorySaver permite conservar temporalmente el estado
del grafo durante la demostración.

Este módulo no modifica prompts reales, no realiza
despliegues y no invoca servicios externos.
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


# ============================================================
# 1. DEFINICIÓN DEL ESTADO
# ============================================================

class EstadoDespliegue(TypedDict):
    """Define la estructura del estado compartido por el grafo.

    Attributes:
        huella_nueva (str): Identificador o huella de
            la versión candidata del prompt.

        aprobado (bool): Decisión de aprobación asociada
            a la versión propuesta.

    Notes:
        El estado se comparte entre los nodos del grafo.

        Cada nodo puede devolver un diccionario con
        los campos que necesita actualizar.

        La estructura TypedDict proporciona información
        de tipos, pero no implementa por sí misma
        una validación de ejecución.
    """

    huella_nueva: str
    aprobado: bool


# ============================================================
# 2. NODO DE PROPUESTA
# ============================================================

def proponer(estado: EstadoDespliegue):
    """Presenta la versión candidata para revisión humana.

    Args:
        estado (EstadoDespliegue): Estado actual del grafo,
            que contiene la huella de la versión propuesta.

    Returns:
        dict: Diccionario vacío porque este nodo
            no modifica el estado compartido.

    Notes:
        La función únicamente muestra la versión
        propuesta mediante una impresión en consola.

        No modifica archivos, prompts ni configuraciones.
    """

    # Presenta la huella de la versión candidata
    # antes de solicitar la decisión humana.
    print(f"Versión propuesta: {estado['huella_nueva']}")

    return {}


# ============================================================
# 3. NODO DE SUPERVISIÓN HUMANA
# ============================================================

def supervisar(estado: EstadoDespliegue):
    """Interrumpe el flujo hasta recibir una decisión humana.

    Solicita una aprobación o rechazo explícito mediante
    el mecanismo interrupt() de LangGraph.

    Args:
        estado (EstadoDespliegue): Estado actual que contiene
            la huella de la versión candidata.

    Returns:
        dict: Actualización del estado con el campo
            aprobado establecido en True o False.

    Raises:
        ValueError:
            Si la decisión recibida no es de tipo bool.

    Notes:
        interrupt() suspende el flujo y permite
        reanudarlo posteriormente mediante Command.

        La reanudación debe utilizar el contexto
        correspondiente a la ejecución interrumpida.

        El valor recibido se valida explícitamente
        antes de actualizar el estado del grafo.

        La función no realiza la activación del prompt.
    """

    # Solicita una decisión humana y suspende el flujo.
    #
    # El contenido de la interrupción identifica
    # la acción pendiente y la versión candidata.
    decision = interrupt({
        "motivo": "Aprobar o rechazar nueva versión del prompt",
        "huella_nueva": estado["huella_nueva"],
    })

    # Solo se aceptan decisiones booleanas explícitas.
    # Se rechazan otros tipos, incluidos valores
    # textuales o numéricos.
    if not isinstance(decision, bool):
        raise ValueError("La decisión humana debe ser True o False.")

    # Registra la decisión en el estado compartido.
    return {"aprobado": decision}


# ============================================================
# 4. NODO DE APLICACIÓN SIMULADA
# ============================================================

def aplicar(estado: EstadoDespliegue):
    """Simula el resultado de la decisión humana.

    Consulta el campo aprobado y presenta un mensaje
    que indica si la versión fue aprobada o rechazada.

    Args:
        estado (EstadoDespliegue): Estado del grafo
            con la huella y la decisión registrada.

    Returns:
        dict: Diccionario vacío porque este nodo
            no modifica el estado.

    Notes:
        La función no despliega ni activa una versión real.

        La aprobación se representa únicamente
        mediante un mensaje de consola.

        El nodo se ejecuta tanto para decisiones
        de aprobación como de rechazo.
    """

    # Comprueba la decisión registrada por el supervisor.
    if estado["aprobado"] is True:
        print(f"Versión APROBADA (simulación): {estado['huella_nueva']}")
    else:
        print(f"Versión RECHAZADA (simulación): {estado['huella_nueva']}")

    return {}


# ============================================================
# 5. CONSTRUCCIÓN DEL GRAFO
# ============================================================

def construir_grafo():
    """Construye y compila el flujo de supervisión humana.

    Define los nodos del proceso y sus conexiones
    utilizando StateGraph de LangGraph.

    Flujo:
        START
          |
          v
        proponer
          |
          v
        supervisar
          |
          v
        aplicar
          |
          v
        END

    Returns:
        Grafo compilado de LangGraph con un
        checkpointer InMemorySaver configurado.

    Notes:
        El grafo utiliza el estado EstadoDespliegue.

        InMemorySaver conserva el estado temporalmente
        en memoria para permitir interrupciones
        y reanudaciones durante la demostración.

        El flujo no incorpora bifurcaciones:
        ambas decisiones continúan hacia aplicar(),
        que determina el mensaje correspondiente.
    """

    # Inicializa el constructor utilizando
    # la estructura de estado definida.
    grafo = StateGraph(EstadoDespliegue)

    # Registra los tres nodos del proceso.
    grafo.add_node("proponer", proponer)
    grafo.add_node("supervisar", supervisar)
    grafo.add_node("aplicar", aplicar)

    # Define el recorrido secuencial del grafo.
    grafo.add_edge(START, "proponer")
    grafo.add_edge("proponer", "supervisar")
    grafo.add_edge("supervisar", "aplicar")
    grafo.add_edge("aplicar", END)

    # Compila el grafo con persistencia temporal
    # de estado mediante un checkpointer en memoria.
    return grafo.compile(checkpointer=InMemorySaver())


# ============================================================
# 6. DEMOSTRACIÓN LOCAL
# ============================================================

if __name__ == "__main__":
    # Construye una instancia ejecutable del grafo.
    app = construir_grafo()

    # --------------------------------------------------------
    # ESCENARIO 1: PROPUESTA E INTERRUPCIÓN
    # --------------------------------------------------------

    # Identifica la ejecución mediante un thread_id.
    #
    # Este identificador permite recuperar y reanudar
    # el estado asociado a la solicitud de aprobación.
    config = {
        "configurable": {
            "thread_id": "vyops-supervision-demo-1"
        }
    }

    # Inicia el flujo con una versión candidata.
    #
    # La ejecución llega al nodo supervisar(),
    # donde interrupt() solicita una decisión.
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

    # --------------------------------------------------------
    # ESCENARIO 2: CONSULTA DEL ESTADO PENDIENTE
    # --------------------------------------------------------

    # Recupera el estado asociado a la ejecución.
    estado_pendiente = app.get_state(config)

    # Muestra la información de la solicitud pendiente
    # y los nodos que todavía deben ejecutarse.
    print("2) pendiente:", estado_pendiente.interrupts[0].value)
    print("Estado pendiente:", estado_pendiente.next)

    # --------------------------------------------------------
    # ESCENARIO 3: APROBACIÓN HUMANA
    # --------------------------------------------------------

    print("\n=== APROBACIÓN HUMANA ===")

    # Reanuda la ejecución original con una decisión positiva.
    #
    # Command(resume=True) entrega el valor booleano
    # que recibirá la llamada pendiente a interrupt().
    resultado_aprobado = app.invoke(
        Command(resume=True),
        config=config,
    )

    # Comprueba la decisión registrada y si el grafo
    # alcanzó su estado final.
    print("3) tras aprobar:", resultado_aprobado)
    print("Decisión registrada:", resultado_aprobado["aprobado"])
    print(
        "Estado final:",
        "FINALIZADO" if not app.get_state(config).next else "PENDIENTE"
    )

    # --------------------------------------------------------
    # ESCENARIO 4: RECHAZO HUMANO
    # --------------------------------------------------------

    # Inicia otra ejecución independiente para comprobar
    # el comportamiento del flujo ante un rechazo.
    print("\n=== RECHAZO HUMANO ===")

    # Utiliza un thread_id distinto para separar
    # el estado de esta ejecución del escenario anterior.
    config_rechazo = {
        "configurable": {
            "thread_id": "vyops-supervision-demo-rechazo"
        }
    }

    # Presenta nuevamente una versión candidata
    # y detiene el flujo en el nodo de supervisión.
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

    # Reanuda el flujo con una decisión negativa.
    #
    # El nodo aplicar() mostrará el rechazo
    # sin modificar ninguna versión real.
    resultado_rechazado = app.invoke(
        Command(resume=False),
        config=config_rechazo,
    )

    # Presenta la decisión registrada y comprueba
    # que la ejecución haya finalizado.
    print("4) tras rechazar:", resultado_rechazado)
    print("Decisión registrada:", resultado_rechazado["aprobado"])
    print(
        "Estado final:",
        "FINALIZADO" if not app.get_state(config_rechazo).next else "PENDIENTE"
    )
