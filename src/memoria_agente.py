
"""Memoria conversacional temporal de VyOps con LangGraph.

Este módulo implementa un mecanismo de memoria conversacional
organizado por sesiones para el agente municipal VyOps.

Utiliza LangGraph y su sistema de checkpoints en memoria
para conservar los mensajes intercambiados durante
una conversación.

Responsabilidades principales:

    1. Definir el estado de los mensajes conversacionales.
    2. Crear un grafo encargado de conservar el historial.
    3. Administrar historiales independientes por sesión.
    4. Recuperar mensajes de conversaciones anteriores.
    5. Registrar mensajes del usuario y del asistente.
    6. Proporcionar el historial al agente municipal.
    7. Eliminar historiales y checkpoints de una sesión.

Componentes principales:

    EstadoMemoria:
        Define la estructura de mensajes persistidos
        mediante checkpoints de LangGraph.

    HistorialSesion:
        Proporciona una interfaz para consultar
        y actualizar los mensajes de una sesión.

    EstadoAgente:
        Define las entradas y salidas utilizadas
        por el grafo que ejecuta el agente municipal.

    InMemorySaver:
        Almacena temporalmente los checkpoints
        de las conversaciones.

    grafo_memoria:
        Grafo encargado de conservar el estado
        de los mensajes por identificador de sesión.

    construir_agente_con_memoria():
        Integra un agente Runnable con el historial
        correspondiente a cada sesión.

Flujo general:

    Mensaje del usuario
        |
        v
    Identificación de la sesión
        |
        v
    Recuperación del historial
        |
        v
    Ejecución del agente con contexto anterior
        |
        v
    Registro del mensaje y la respuesta
        |
        v
    Resultado del agente

IMPORTANTE:
    La persistencia implementada es temporal.

    InMemorySaver conserva los checkpoints
    dentro de la memoria del proceso.

    Este módulo no implementa almacenamiento
    persistente en archivos ni bases de datos.

    Los identificadores de sesión permiten
    separar lógicamente los historiales,
    pero no constituyen por sí mismos
    un mecanismo de autenticación o autorización.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Annotated permite asociar el reductor add_messages
# al campo de mensajes del estado.
#
# TypedDict define las estructuras utilizadas
# por los grafos de LangGraph.
from typing import Annotated, TypedDict

# Tipos de mensajes utilizados en las conversaciones.
#
# BaseMessage representa mensajes de distintos roles.
# HumanMessage representa mensajes del usuario.
# AIMessage representa respuestas del asistente.
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

# Runnable representa componentes ejecutables.
#
# RunnableConfig permite recibir la configuración
# de ejecución, incluidos los datos de sesión.
from langchain_core.runnables import Runnable, RunnableConfig

# Implementación de checkpoints almacenados en memoria.
from langgraph.checkpoint.memory import InMemorySaver

# Componentes para construir grafos de estados.
#
# START representa el inicio del flujo.
# END representa su finalización.
# StateGraph permite definir nodos y transiciones.
from langgraph.graph import END, START, StateGraph

# Reductor que permite incorporar mensajes al estado
# conservando los mensajes anteriores.
from langgraph.graph.message import add_messages


# ============================================================
# 2. ESTADO DE MEMORIA CONVERSACIONAL
# ============================================================

class EstadoMemoria(TypedDict):
    """Define el estado de mensajes de una conversación.

    Attributes:
        messages:
            Lista de mensajes almacenados
            en el historial de una sesión.

    La anotación add_messages indica a LangGraph
    cómo combinar los mensajes nuevos con los
    mensajes existentes en el estado.

    Los mensajes se representan mediante BaseMessage,
    lo que permite almacenar distintos tipos
    de mensajes compatibles con LangChain.

    La persistencia del estado depende
    del checkpointer asociado al grafo.
    """

    # Lista de mensajes con el reductor add_messages.
    #
    # El reductor permite actualizar el historial
    # sin reemplazar necesariamente toda la colección.
    messages: Annotated[list[BaseMessage], add_messages]


# ============================================================
# 3. INTERFAZ DE HISTORIAL POR SESIÓN
# ============================================================

class HistorialSesion:
    """Interfaz de consulta y actualización del historial.

    Representa el acceso al historial conversacional
    asociado a un identificador de sesión específico.

    Attributes:
        session_id:
            Identificador utilizado para localizar
            los checkpoints de la conversación.

        _grafo:
            Grafo Runnable encargado de administrar
            el estado conversacional.

    La clase no almacena directamente los mensajes.

    Las operaciones de lectura y escritura se realizan
    mediante el grafo y su sistema de checkpoints.

    Cada instancia queda asociada al identificador
    recibido durante su construcción.
    """

    # --------------------------------------------------------
    # 3.1. INICIALIZACIÓN DEL HISTORIAL
    # --------------------------------------------------------

    def __init__(self, session_id: str, grafo: Runnable):
        """Inicializa la interfaz de historial de una sesión.

        Args:
            session_id:
                Identificador de la sesión conversacional.

            grafo:
                Grafo utilizado para consultar
                y actualizar los mensajes.

        La construcción de esta instancia
        no agrega mensajes al historial.
        """

        # Identificador asociado a la conversación.
        self.session_id = session_id

        # Referencia al grafo de memoria compartido.
        self._grafo = grafo

    # --------------------------------------------------------
    # 3.2. CONSULTA DE MENSAJES ALMACENADOS
    # --------------------------------------------------------

    @property
    def messages(self) -> list[BaseMessage]:
        """Obtiene los mensajes almacenados.

        Returns:
            list[BaseMessage]:
                Lista de mensajes recuperados
                desde el estado del grafo.

                Si el estado no contiene mensajes,
                devuelve una lista vacía.

        La consulta utiliza thread_id para identificar
        los checkpoints correspondientes a la sesión.

        Se devuelve una nueva lista construida
        a partir de los mensajes recuperados.

        Esta operación no agrega mensajes
        ni modifica el historial.
        """

        # Recupera el estado asociado al identificador
        # de sesión configurado como thread_id.
        estado = self._grafo.get_state(
            {"configurable": {"thread_id": self.session_id}}
        )

        # Devuelve una lista con los mensajes existentes.
        #
        # Si no hay mensajes registrados,
        # utiliza una lista vacía.
        return list(estado.values.get("messages", []))

    # --------------------------------------------------------
    # 3.3. REGISTRO DE MENSAJES DEL USUARIO
    # --------------------------------------------------------

    def add_user_message(self, contenido: str) -> None:
        """Agrega un mensaje del usuario.

        Args:
            contenido:
                Texto que se incorporará
                al historial conversacional.

        Convierte el contenido en un HumanMessage
        y delega su almacenamiento
        al método agregar_mensajes().

        No genera respuestas del agente.
        """

        # Construye un mensaje del usuario
        # y lo envía al mecanismo de almacenamiento.
        self.agregar_mensajes([HumanMessage(content=contenido)])

    # --------------------------------------------------------
    # 3.4. ACTUALIZACIÓN DEL HISTORIAL
    # --------------------------------------------------------

    def agregar_mensajes(self, mensajes: list[BaseMessage]) -> None:
        """Guarda mensajes en el checkpoint de la sesión.

        Args:
            mensajes:
                Lista de mensajes compatibles
                con BaseMessage que se desea incorporar.

        Ejecuta el grafo de memoria utilizando
        el identificador de sesión como thread_id.

        El reductor add_messages administra
        la incorporación de los mensajes al estado.

        Esta operación actualiza los checkpoints
        mantenidos por InMemorySaver.
        """

        # Ejecuta el grafo de memoria con los mensajes
        # y la configuración de la sesión correspondiente.
        self._grafo.invoke(
            {"messages": mensajes},
            config={"configurable": {"thread_id": self.session_id}},
        )


# ============================================================
# 4. ESTADO DEL AGENTE MUNICIPAL
# ============================================================

class EstadoAgente(TypedDict, total=False):
    """Define las entradas y resultados del agente municipal.

    Attributes:
        entrada:
            Mensaje actual proporcionado por el usuario.

        output:
            Respuesta generada por el agente.

        intermediate_steps:
            Información de pasos intermedios
            devuelta por el agente cuando está disponible.

    total=False permite que los campos
    no sean obligatorios en todos los estados.

    Durante la ejecución del nodo del agente,
    el código espera recibir el campo entrada.

    El estado permite transportar los resultados
    entre los componentes del grafo.
    """

    entrada: str
    output: str
    intermediate_steps: list


# ============================================================
# 5. ALMACENAMIENTO TEMPORAL COMPARTIDO
# ============================================================

# Checkpointer que conserva los estados de conversación
# dentro de la memoria del proceso.
#
# Es compartido por las sesiones que utilizan
# el grafo de memoria definido en este módulo.
checkpointer = InMemorySaver()

# Diccionario que relaciona identificadores de sesión
# con sus respectivas interfaces HistorialSesion.
#
# Los mensajes se almacenan en los checkpoints;
# este diccionario conserva las interfaces de acceso.
historiales: dict[str, HistorialSesion] = {}


# ============================================================
# 6. CONSTRUCCIÓN DEL GRAFO DE MEMORIA
# ============================================================

def _crear_grafo_memoria():
    """Construye el grafo de persistencia conversacional.

    Returns:
        Grafo compilado de LangGraph que utiliza
        el checkpointer compartido del módulo.

    El grafo contiene un único nodo denominado conservar.

    Su estructura es:

        START
          |
          v
       conservar
          |
          v
         END

    El nodo no devuelve modificaciones adicionales
    al estado recibido.

    La incorporación de mensajes se realiza
    mediante el estado de entrada y su reductor
    add_messages.

    El grafo se compila con InMemorySaver
    para mantener checkpoints por thread_id.
    """

    # --------------------------------------------------------
    # 6.1. NODO DE CONSERVACIÓN
    # --------------------------------------------------------

    def conservar(estado: EstadoMemoria) -> dict:
        """Mantiene el estado sin agregar actualizaciones.

        Args:
            estado:
                Estado conversacional recibido
                por el nodo de LangGraph.

        Returns:
            dict:
                Diccionario vacío que indica
                que el nodo no aporta cambios adicionales.

        Los mensajes recibidos forman parte
        del estado administrado por LangGraph.
        """

        # No agrega modificaciones al estado.
        return {}

    # --------------------------------------------------------
    # 6.2. CREACIÓN DEL GRAFO
    # --------------------------------------------------------

    # Inicializa el constructor utilizando
    # la estructura EstadoMemoria.
    builder = StateGraph(EstadoMemoria)

    # --------------------------------------------------------
    # 6.3. REGISTRO DEL NODO
    # --------------------------------------------------------

    # Incorpora el nodo encargado de conservar el estado.
    builder.add_node("conservar", conservar)

    # --------------------------------------------------------
    # 6.4. DEFINICIÓN DE TRANSICIONES
    # --------------------------------------------------------

    # Conecta el inicio con el nodo de conservación.
    builder.add_edge(START, "conservar")

    # Finaliza la ejecución después del nodo.
    builder.add_edge("conservar", END)

    # --------------------------------------------------------
    # 6.5. COMPILACIÓN CON CHECKPOINTER
    # --------------------------------------------------------

    # Compila el grafo y asocia el almacenamiento
    # temporal compartido.
    return builder.compile(checkpointer=checkpointer)


# ============================================================
# 7. INSTANCIA COMPARTIDA DEL GRAFO DE MEMORIA
# ============================================================

# Construye el grafo de memoria una vez
# durante la carga del módulo.
#
# Las sesiones posteriores utilizan esta instancia
# para acceder a sus respectivos checkpoints.
grafo_memoria = _crear_grafo_memoria()


# ============================================================
# 8. OBTENCIÓN DE HISTORIALES POR SESIÓN
# ============================================================

def obtener_historial(session_id: str) -> HistorialSesion:
    """Obtiene o crea el historial de una sesión.

    Args:
        session_id:
            Identificador de la sesión conversacional.

            Debe ser una cadena de texto
            que no esté vacía ni contenga
            únicamente espacios en blanco.

    Returns:
        HistorialSesion:
            Interfaz de acceso al historial
            asociado al identificador recibido.

    Raises:
        ValueError:
            Si session_id no es una cadena válida
            o contiene únicamente espacios.

    Si el identificador ya existe en historiales,
    devuelve la instancia registrada.

    En caso contrario, crea una nueva instancia
    asociada al grafo de memoria compartido.

    La función no agrega mensajes al historial.
    """

    # --------------------------------------------------------
    # 8.1. VALIDACIÓN DEL IDENTIFICADOR
    # --------------------------------------------------------

    # Rechaza valores que no sean cadenas de texto
    # o que estén vacíos después de eliminar espacios.
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("El identificador de sesión no puede estar vacío.")

    # --------------------------------------------------------
    # 8.2. CREACIÓN DE UNA NUEVA INTERFAZ
    # --------------------------------------------------------

    # Si todavía no existe una interfaz para la sesión,
    # crea una nueva y la incorpora al diccionario.
    if session_id not in historiales:
        historiales[session_id] = HistorialSesion(
            session_id, grafo_memoria
        )

    # --------------------------------------------------------
    # 8.3. DEVOLUCIÓN DEL HISTORIAL
    # --------------------------------------------------------

    # Devuelve la interfaz existente o recién creada.
    return historiales[session_id]


# ============================================================
# 9. ELIMINACIÓN DE HISTORIALES
# ============================================================

def eliminar_historial(session_id: str) -> None:
    """Elimina el historial y los checkpoints de una sesión.

    Args:
        session_id:
            Identificador de la sesión que se desea eliminar.

    El procedimiento realiza dos operaciones:

        1. Elimina la interfaz de la sesión
           del diccionario historiales.

        2. Solicita al checkpointer eliminar
           los checkpoints asociados al thread_id.

    La eliminación del diccionario utiliza pop()
    con un valor predeterminado para evitar
    un KeyError si la sesión no está registrada.

    Esta función no elimina los historiales
    correspondientes a otras sesiones.
    """

    # --------------------------------------------------------
    # 9.1. ELIMINACIÓN DE LA INTERFAZ
    # --------------------------------------------------------

    # Retira la sesión del diccionario de historiales.
    #
    # Si no existe, devuelve None sin generar KeyError.
    historiales.pop(session_id, None)

    # --------------------------------------------------------
    # 9.2. ELIMINACIÓN DE CHECKPOINTS
    # --------------------------------------------------------

    # Solicita al almacenamiento temporal eliminar
    # los checkpoints asociados a la sesión.
    checkpointer.delete_thread(session_id)


# ============================================================
# 10. INTEGRACIÓN DEL AGENTE CON MEMORIA
# ============================================================

def construir_agente_con_memoria(agente: Runnable):
    """Integra el agente municipal con memoria por sesión.

    Args:
        agente:
            Componente Runnable que procesa mensajes
            y genera respuestas del agente municipal.

    Returns:
        Grafo compilado de LangGraph que ejecuta
        el agente utilizando el historial conversacional
        asociado a cada sesión.

    Flujo general:

        1. Obtener session_id desde RunnableConfig.
        2. Recuperar el historial de la sesión.
        3. Obtener los mensajes anteriores.
        4. Ejecutar el agente con entrada y chat_history.
        5. Registrar el mensaje del usuario.
        6. Registrar la respuesta del agente.
        7. Devolver output e intermediate_steps.

    El grafo contiene un nodo denominado agente.

    Su estructura es:

        START
          |
          v
        agente
          |
          v
         END

    El historial conversacional se administra
    mediante el grafo de memoria compartido.

    Este grafo del agente se compila sin asociar
    directamente un checkpointer adicional.

    La persistencia de mensajes se realiza
    mediante HistorialSesion.
    """

    # --------------------------------------------------------
    # 10.1. NODO DE EJECUCIÓN DEL AGENTE
    # --------------------------------------------------------

    def ejecutar(estado: EstadoAgente, config: RunnableConfig):
        """Ejecuta el agente con el historial de su sesión.

        Args:
            estado:
                Estado de entrada que contiene
                el mensaje actual del usuario.

            config:
                Configuración de ejecución de LangChain.

                Se espera que incluya session_id
                dentro del diccionario configurable.

        Returns:
            dict:
                Resultado que contiene:

                - output:
                  Respuesta generada por el agente.

                - intermediate_steps:
                  Pasos intermedios devueltos
                  por el agente cuando están disponibles.

        Raises:
            ValueError:
                Si no se proporciona un identificador
                de sesión válido.

        La función recupera los mensajes anteriores
        antes de ejecutar el agente.

        Una vez obtenida la respuesta,
        registra el mensaje del usuario
        y la respuesta del asistente.

        Si la ejecución del agente produce una excepción
        antes del registro, esta función no incorpora
        el nuevo intercambio al historial.
        """

        # ----------------------------------------------------
        # 10.2. IDENTIFICACIÓN DE LA SESIÓN
        # ----------------------------------------------------

        # Recupera el identificador de sesión
        # desde la configuración de ejecución.
        session_id = config.get("configurable", {}).get("session_id")

        # Obtiene o crea la interfaz del historial.
        #
        # obtener_historial() valida que el identificador
        # corresponda a una cadena no vacía.
        historial = obtener_historial(session_id)

        # ----------------------------------------------------
        # 10.3. RECUPERACIÓN DEL CONTEXTO
        # ----------------------------------------------------

        # Obtiene los mensajes previamente almacenados
        # para la sesión actual.
        anteriores = historial.messages

        # ----------------------------------------------------
        # 10.4. EJECUCIÓN DEL AGENTE
        # ----------------------------------------------------

        # Entrega al agente el mensaje actual
        # y el historial conversacional anterior.
        #
        # La clave chat_history permite proporcionar
        # contexto de conversaciones previas.
        resultado = agente.invoke(
            {
                "entrada": estado["entrada"],
                "chat_history": anteriores,
            }
        )

        # ----------------------------------------------------
        # 10.5. ACTUALIZACIÓN DE LA MEMORIA
        # ----------------------------------------------------

        # Incorpora el mensaje actual del usuario
        # y la respuesta generada por el agente.
        #
        # Ambos mensajes se registran en el historial
        # correspondiente a la sesión.
        historial.agregar_mensajes(
            [
                HumanMessage(content=estado["entrada"]),
                AIMessage(content=resultado["output"]),
            ]
        )

        # ----------------------------------------------------
        # 10.6. DEVOLUCIÓN DEL RESULTADO
        # ----------------------------------------------------

        # Devuelve la respuesta del agente
        # y sus pasos intermedios cuando existan.
        #
        # Si intermediate_steps no está presente,
        # utiliza una lista vacía.
        return {
            "output": resultado["output"],
            "intermediate_steps": resultado.get(
                "intermediate_steps", []
            ),
        }

    # --------------------------------------------------------
    # 10.7. CONSTRUCCIÓN DEL GRAFO DEL AGENTE
    # --------------------------------------------------------

    # Inicializa el grafo utilizando EstadoAgente.
    builder = StateGraph(EstadoAgente)

    # Registra el nodo que ejecuta el agente con memoria.
    builder.add_node("agente", ejecutar)

    # --------------------------------------------------------
    # 10.8. DEFINICIÓN DE TRANSICIONES
    # --------------------------------------------------------

    # Conecta el inicio con el nodo del agente.
    builder.add_edge(START, "agente")

    # Finaliza el flujo después de ejecutar el agente.
    builder.add_edge("agente", END)

    # --------------------------------------------------------
    # 10.9. COMPILACIÓN DEL GRAFO
    # --------------------------------------------------------

    # Devuelve el grafo compilado.
    #
    # El historial se administra mediante
    # el grafo_memoria y su checkpointer compartido.
    return builder.compile()
