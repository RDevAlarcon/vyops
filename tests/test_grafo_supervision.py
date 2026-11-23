
"""Pruebas unitarias del grafo de supervisión humana de VyOps.

Este módulo verifica el flujo de aprobación y rechazo
implementado mediante LangGraph en grafo_supervision.py.

El grafo representa un proceso supervisado en el que
una nueva versión debe esperar una decisión humana
antes de continuar con su aplicación simulada.

Las pruebas comprueban tres escenarios:

    1. Interrupción del grafo antes de aplicar una versión.
    2. Reanudación del grafo con aprobación explícita.
    3. Reanudación del grafo con rechazo explícito.

Se utiliza Command(resume=...) para proporcionar
la decisión que permite continuar la ejecución
después de una interrupción.

Cada prueba utiliza un thread_id diferente para
identificar su ejecución dentro del estado del grafo.

La fixture capsys de pytest permite inspeccionar
los mensajes escritos en la salida estándar.

Las pruebas verifican el comportamiento del flujo
de supervisión y sus mensajes de simulación.

No realizan activaciones ni modificaciones reales
de versiones documentales o índices de VyOps.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite reanudar la ejecución de un grafo LangGraph
# después de una interrupción, proporcionando una decisión.
from langgraph.types import Command

# Constructor del grafo de supervisión humana
# utilizado para simular la aprobación de versiones.
from grafo_supervision import construir_grafo


# ============================================================
# 2. DATOS COMPARTIDOS POR LAS PRUEBAS
# ============================================================

# Identificador de la versión simulada.
#
# Se utiliza como huella de referencia para comprobar
# los mensajes generados durante la supervisión.
HUELLA = "fdff8ebf6d37"


# ============================================================
# 3. FUNCIÓN AUXILIAR DE INICIO DE SUPERVISIÓN
# ============================================================

def iniciar_supervision(app, thread_id):
    """Inicia una ejecución del grafo hasta su interrupción.

    Construye la configuración de ejecución utilizando
    el identificador de hilo recibido.

    Invoca el grafo con una nueva huella y un estado
    inicial de aprobación negativa.

    Args:
        app:
            Grafo LangGraph compilado que se desea ejecutar.

        thread_id:
            Identificador utilizado para asociar
            la ejecución con su estado persistido
            por el mecanismo de checkpoint del grafo.

    Returns:
        tuple:
            Contiene dos elementos:

            config:
                Configuración utilizada para identificar
                la ejecución del grafo.

            resultado:
                Resultado devuelto por la invocación inicial,
                que las pruebas utilizan para comprobar
                la interrupción de supervisión.

    Esta función permite reutilizar la preparación
    del flujo en los tres escenarios de prueba.
    """

    # Construye la configuración que identifica
    # la ejecución del grafo mediante thread_id.
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # Inicia el flujo con la huella de la nueva versión
    # y el estado inicial de aprobación en False.
    resultado = app.invoke(
        {
            "huella_nueva": HUELLA,
            "aprobado": False,
        },
        config=config,
    )

    # Devuelve la configuración y el resultado
    # para que la prueba pueda inspeccionar
    # o reanudar la ejecución.
    return config, resultado


# ============================================================
# 4. INTERRUPCIÓN ANTES DE APLICAR UNA VERSIÓN
# ============================================================

def test_grafo_se_interrumpe_antes_de_aplicar(capsys):
    """Verifica que el grafo se interrumpa antes de aplicar.

    Construye el grafo de supervisión e inicia
    una ejecución identificada por test-interrupcion.

    Verificaciones:
        - El resultado contiene una interrupción.
        - El siguiente nodo pendiente es supervisar.
        - No se imprime un mensaje de versión activada.

    Esta prueba comprueba que el flujo quede detenido
    en el punto de supervisión antes de continuar.

    Args:
        capsys:
            Fixture de pytest utilizada para capturar
            la salida estándar de la ejecución.
    """

    # Construye una nueva instancia del grafo.
    app = construir_grafo()

    # Inicia la ejecución hasta el punto
    # en que se requiere supervisión.
    config, resultado = iniciar_supervision(
        app, "test-interrupcion"
    )

    # Comprueba que LangGraph haya devuelto
    # información de interrupción.
    assert "__interrupt__" in resultado

    # Verifica que el nodo pendiente de ejecución
    # sea el correspondiente a la supervisión.
    assert app.get_state(config).next == ("supervisar",)

    # Recupera la salida estándar generada
    # durante la ejecución del grafo.
    salida = capsys.readouterr().out

    # Antes de recibir aprobación no debe aparecer
    # un mensaje que indique activación de la versión.
    assert "Versión ACTIVADA" not in salida


# ============================================================
# 5. REANUDACIÓN CON APROBACIÓN HUMANA
# ============================================================

def test_aprobacion_activa_version(capsys):
    """Verifica la continuación del grafo tras una aprobación.

    Construye el grafo y ejecuta el flujo hasta
    la interrupción de supervisión.

    Posteriormente utiliza Command(resume=True)
    para simular una aprobación humana.

    Verificaciones:
        - El grafo se interrumpe inicialmente.
        - El resultado final indica aprobado=True.
        - No quedan nodos pendientes de ejecución.
        - La salida informa la aprobación simulada
          de la versión identificada por HUELLA.

    Args:
        capsys:
            Fixture de pytest utilizada para capturar
            los mensajes escritos en la salida estándar.
    """

    # Construye una instancia del grafo de supervisión.
    app = construir_grafo()

    # Inicia el flujo hasta la interrupción.
    config, pendiente = iniciar_supervision(
        app, "test-aprobacion"
    )

    # Comprueba que la ejecución inicial
    # haya quedado interrumpida.
    assert "__interrupt__" in pendiente

    # Reanuda el grafo proporcionando
    # una decisión afirmativa.
    resultado = app.invoke(
        Command(resume=True),
        config=config,
    )

    # Verifica que el estado final
    # registre la aprobación.
    assert resultado["aprobado"] is True

    # Una ejecución completada no debe
    # conservar nodos pendientes.
    assert app.get_state(config).next == ()

    # Recupera la salida estándar del flujo.
    salida = capsys.readouterr().out

    # Comprueba que se informe la aprobación simulada
    # de la versión correspondiente a la huella.
    assert f"Versión APROBADA (simulación): {HUELLA}" in salida


# ============================================================
# 6. REANUDACIÓN CON RECHAZO HUMANO
# ============================================================

def test_rechazo_no_activa_version(capsys):
    """Verifica que un rechazo no active la versión simulada.

    Construye el grafo y ejecuta el flujo
    hasta la interrupción de supervisión.

    Posteriormente utiliza Command(resume=False)
    para simular una decisión humana negativa.

    Verificaciones:
        - El grafo se interrumpe inicialmente.
        - El resultado final conserva aprobado=False.
        - No quedan nodos pendientes de ejecución.
        - La salida informa el rechazo de la versión.
        - No aparece un mensaje de aprobación simulada.

    Esta prueba comprueba que el flujo pueda finalizar
    después de un rechazo sin considerar aprobada
    la versión evaluada.

    Args:
        capsys:
            Fixture de pytest utilizada para capturar
            los mensajes escritos en la salida estándar.
    """

    # Construye una instancia independiente del grafo.
    app = construir_grafo()

    # Inicia la ejecución hasta el punto
    # que requiere una decisión humana.
    config, pendiente = iniciar_supervision(
        app, "test-rechazo"
    )

    # Verifica que la ejecución inicial
    # haya quedado interrumpida.
    assert "__interrupt__" in pendiente

    # Reanuda el grafo proporcionando
    # una decisión negativa.
    resultado = app.invoke(
        Command(resume=False),
        config=config,
    )

    # Comprueba que el resultado final
    # no indique una aprobación.
    assert resultado["aprobado"] is False

    # Verifica que el flujo haya terminado
    # sin nodos pendientes de ejecución.
    assert app.get_state(config).next == ()

    # Recupera la salida estándar generada.
    salida = capsys.readouterr().out

    # La ejecución debe informar
    # el rechazo simulado de la versión.
    assert f"Versión RECHAZADA (simulación): {HUELLA}" in salida

    # No debe aparecer un mensaje
    # que indique aprobación de la versión.
    assert "Versión APROBADA (simulación)" not in salida
