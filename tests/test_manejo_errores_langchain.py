
"""Pruebas del manejo de errores con LangChain.

Bloque 20 de SkillNest.

Este módulo verifica los mecanismos de recuperación
ante errores implementados en src.manejo_errores_langchain.

Las pruebas comprueban tres componentes principales:

    1. Cadenas con fallback:
       Utilizan una respuesta alternativa cuando falla
       la cadena principal.

    2. Ejecución segura:
       Captura errores técnicos, registra información
       de diagnóstico y entrega mensajes controlados.

    3. Enrutamiento seguro:
       Recupera errores producidos durante la clasificación
       o la generación de respuestas, manteniendo
       la estructura esperada por VyOps.

Los escenarios incluyen ejecuciones exitosas,
excepciones simuladas, conservación de mensajes
y verificación de registros de errores.

Se utilizan RunnableLambda y modelos simulados
para evitar llamadas reales a Gemini.

Las pruebas verifican comportamientos específicos
de recuperación y registro. No constituyen una
auditoría completa de seguridad de los logs.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite representar funciones Python como componentes
# ejecutables dentro de cadenas de LangChain.
from langchain_core.runnables import RunnableLambda

# Construye una cadena que utiliza una respuesta alternativa
# cuando falla el procesamiento principal.
from src.manejo_errores_langchain import construir_cadena_con_fallback


# ============================================================
# 2. ACTIVACIÓN DEL FALLBACK EN LA CADENA PRINCIPAL
# ============================================================

def test_fallback_se_activa_si_falla_cadena_principal() -> None:
    """Verifica que se utiliza el fallback ante una excepción.

    Simula una cadena principal que genera RuntimeError.

    Comprueba que el mecanismo de recuperación:

        - Capture el fallo de la cadena principal.
        - Active la respuesta alternativa.
        - Devuelva el mensaje esperado para el usuario.

    El error simulado no requiere utilizar un modelo real.
    """

    def cadena_con_error(datos: dict) -> str:
        """Simula un fallo durante el procesamiento.

        Args:
            datos (dict):
                Datos recibidos por la cadena simulada.

        Raises:
            RuntimeError:
                Representa un fallo del modelo principal.
        """

        # Simula una excepción durante el procesamiento.
        raise RuntimeError("Error simulado del modelo")

    # Convierte la función que falla en una cadena ejecutable.
    modelo_simulado = RunnableLambda(cadena_con_error)

    # Construye la cadena protegida por un fallback.
    cadena = construir_cadena_con_fallback(modelo_simulado)

    # Ejecuta una consulta municipal que provoca
    # el error de la cadena principal.
    resultado = cadena.invoke({
        "mensaje": "¿Cómo puedo solicitar un permiso municipal?"
    })

    # Comprueba que se entregue la respuesta alternativa
    # definida por el mecanismo de fallback.
    assert resultado == (
        "No fue posible procesar tu solicitud en este momento. "
        "Por favor, intenta nuevamente más tarde."
    )


# ============================================================
# 3. EJECUCIÓN EXITOSA SIN ACTIVAR EL FALLBACK
# ============================================================

def test_fallback_no_se_activa_si_cadena_funciona() -> None:
    """Verifica que una ejecución exitosa no active el fallback.

    Simula una cadena principal que devuelve
    una respuesta sin generar excepciones.

    Comprueba que el resultado original se conserve
    y no sea reemplazado por el mensaje alternativo.
    """

    def cadena_exitosa(datos: dict) -> str:
        """Simula una respuesta correcta del modelo.

        Args:
            datos (dict):
                Datos recibidos por la cadena simulada.

        Returns:
            str:
                Mensaje de procesamiento exitoso.
        """

        # Devuelve una respuesta simulada sin errores.
        return "Solicitud procesada correctamente."

    # Construye una cadena ejecutable que responde correctamente.
    modelo_simulado = RunnableLambda(cadena_exitosa)

    # Incorpora el mecanismo de fallback.
    cadena = construir_cadena_con_fallback(modelo_simulado)

    # Ejecuta una consulta municipal.
    resultado = cadena.invoke({
        "mensaje": "¿Cómo puedo obtener una patente comercial?"
    })

    # Comprueba que se mantenga la respuesta principal.
    assert resultado == "Solicitud procesada correctamente."


# ============================================================
# 4. REGISTRO DE ERRORES EN LA EJECUCIÓN SEGURA
# ============================================================

def test_ejecutar_cadena_segura_registra_error(caplog) -> None:
    """Verifica que se registre un error sin exponerlo al usuario.

    Simula un fallo técnico durante la ejecución
    de una cadena LangChain.

    Utiliza la fixture caplog de pytest para capturar
    registros de nivel ERROR.

    Comprueba que:

        - El usuario reciba una respuesta controlada.
        - Se registre un mensaje de error técnico.
        - El detalle de la excepción aparezca en el log.
        - El detalle interno no aparezca en la respuesta.

    Esta prueba distingue la información de diagnóstico
    de aquella que se entrega al usuario.
    """

    # Módulo estándar utilizado para configurar
    # el nivel de captura de los registros.
    import logging

    # Función que ejecuta cadenas LangChain
    # con manejo controlado de excepciones.
    from src.manejo_errores_langchain import ejecutar_cadena_segura

    def cadena_con_error(datos: dict) -> str:
        """Simula un fallo inesperado del modelo.

        Args:
            datos (dict):
                Datos de entrada de la cadena.

        Raises:
            RuntimeError:
                Representa un error técnico interno.
        """

        # Genera la excepción utilizada para comprobar
        # el registro y la respuesta controlada.
        raise RuntimeError("Error interno simulado")

    # Construye una cadena que genera la excepción.
    cadena = RunnableLambda(cadena_con_error)

    # Captura los registros de nivel ERROR
    # producidos durante la ejecución segura.
    with caplog.at_level(logging.ERROR):
        resultado = ejecutar_cadena_segura(
            cadena,
            {"mensaje": "Necesito consultar un permiso municipal."},
        )

    # Comprueba el mensaje controlado recibido por el usuario.
    assert resultado == (
        "No fue posible completar tu solicitud. "
        "Por favor, intenta nuevamente más tarde."
    )

    # Verifica que se registre el contexto técnico del error.
    assert "Ocurrió un error al ejecutar la cadena LangChain." in caplog.text

    # En este escenario, el detalle de la excepción
    # debe estar disponible en el registro de diagnóstico.
    assert "Error interno simulado" in caplog.text

    # El detalle técnico no debe exponerse en la respuesta.
    assert "Error interno simulado" not in resultado


# ============================================================
# 5. EJECUCIÓN SEGURA SIN ERRORES
# ============================================================

def test_ejecutar_cadena_segura_sin_errores(caplog) -> None:
    """Verifica que una ejecución exitosa conserve su respuesta.

    Simula una cadena que finaliza correctamente.

    Comprueba que:

        - Se devuelva la respuesta original.
        - No se generen registros de nivel ERROR
          durante la ejecución evaluada.

    Esta prueba verifica que el manejo seguro
    no altere una ejecución satisfactoria.
    """

    # Permite capturar registros de nivel ERROR.
    import logging

    # Función de ejecución segura que se está evaluando.
    from src.manejo_errores_langchain import ejecutar_cadena_segura

    def cadena_exitosa(datos: dict) -> str:
        """Simula una respuesta correcta del modelo.

        Args:
            datos (dict):
                Datos recibidos por la cadena.

        Returns:
            str:
                Respuesta simulada del procedimiento.
        """

        # Devuelve una respuesta sin generar excepciones.
        return "El procedimiento fue consultado correctamente."

    # Construye la cadena simulada.
    cadena = RunnableLambda(cadena_exitosa)

    # Ejecuta la cadena capturando posibles registros de error.
    with caplog.at_level(logging.ERROR):
        resultado = ejecutar_cadena_segura(
            cadena,
            {"mensaje": "¿Cómo solicito un permiso municipal?"},
        )

    # La ejecución segura debe conservar la respuesta original.
    assert resultado == "El procedimiento fue consultado correctamente."

    # No deben existir registros capturados de nivel ERROR.
    assert caplog.records == []


# ============================================================
# 6. CONSERVACIÓN DEL MENSAJE EN EL FALLBACK
# ============================================================

def test_fallback_enrutamiento_conserva_mensaje() -> None:
    """Verifica que el fallback conserve el mensaje original.

    Construye el fallback utilizado por el enrutamiento
    de consultas municipales.

    Comprueba que el resultado mantenga tres campos:

        mensaje:
            Texto original recibido del usuario.

        categoria:
            Valor "error", que identifica el fallo.

        respuesta:
            Mensaje alternativo definido para el usuario.

    Esta prueba verifica la estructura del resultado
    y la conservación del texto de entrada.
    """

    # Importa el constructor del fallback de enrutamiento.
    from src.manejo_errores_langchain import (
        construir_fallback_enrutamiento,
    )

    # Define el mensaje original de la consulta.
    mensaje = "¿Qué documentos necesito para solicitar un permiso?"

    # Construye el componente de respuesta alternativa.
    fallback = construir_fallback_enrutamiento()

    # Ejecuta el fallback con el mensaje de entrada.
    resultado = fallback.invoke({"mensaje": mensaje})

    # Comprueba la estructura completa del resultado.
    #
    # El mensaje original debe conservarse,
    # la categoría debe indicar error y la respuesta
    # debe corresponder al mensaje alternativo esperado.
    assert resultado == {
        "mensaje": mensaje,
        "categoria": "error",
        "respuesta": (
            "No fue posible procesar tu solicitud en este momento. "
            "Por favor, intenta nuevamente más tarde."
        ),
    }


# ============================================================
# 7. ERROR DURANTE LA CLASIFICACIÓN DE UNA CONSULTA
# ============================================================

def test_enrutamiento_seguro_recupera_error_clasificacion() -> None:
    """Verifica que un fallo de clasificación active el fallback.

    Simula un modelo que genera una excepción
    durante la primera llamada.

    Comprueba que:

        - Se conserve el mensaje original.
        - La categoría devuelta sea "error".
        - Se entregue la respuesta alternativa.
        - El modelo se haya llamado una sola vez.

    Este escenario representa un fallo antes
    de completar la clasificación de la consulta.
    """

    # Permite simular el modelo y contar sus invocaciones.
    from unittest.mock import MagicMock

    # Constructor del enrutamiento con recuperación de errores.
    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    def modelo_con_error(entrada: object) -> str:
        """Simula un error del modelo durante la clasificación.

        Args:
            entrada (object):
                Entrada recibida por el modelo simulado.

        Raises:
            RuntimeError:
                Representa un fallo de clasificación.
        """

        # Provoca un fallo durante la primera invocación.
        raise RuntimeError("Fallo simulado de Gemini")

    # Configura el modelo simulado para ejecutar
    # la función que genera la excepción.
    modelo_simulado = MagicMock(side_effect=modelo_con_error)

    # Construye el enrutamiento seguro con el modelo simulado.
    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_simulado)
    )

    # Consulta municipal utilizada durante la prueba.
    mensaje = "¿Qué documentos necesito para abrir un negocio?"

    # Ejecuta la cadena para comprobar la recuperación.
    resultado = cadena.invoke({"mensaje": mensaje})

    # Comprueba que el resultado conserve el mensaje original.
    assert resultado["mensaje"] == mensaje

    # El fallo debe identificarse mediante la categoría error.
    assert resultado["categoria"] == "error"

    # Verifica que se entregue la respuesta alternativa.
    assert resultado["respuesta"] == (
        "No fue posible procesar tu solicitud en este momento. "
        "Por favor, intenta nuevamente más tarde."
    )

    # El fallo ocurre durante la primera llamada al modelo.
    assert modelo_simulado.call_count == 1


# ============================================================
# 8. ERROR DURANTE LA GENERACIÓN DE LA RESPUESTA
# ============================================================

def test_enrutamiento_seguro_recupera_error_respuesta() -> None:
    """Verifica que un fallo posterior a la clasificación active el fallback.

    Simula un modelo que responde correctamente
    durante la primera llamada de clasificación,
    pero genera una excepción durante la segunda llamada.

    Comprueba que:

        - El mensaje original se conserve.
        - La categoría final sea "error".
        - Se entregue la respuesta alternativa.
        - El modelo haya recibido dos llamadas.

    Este escenario verifica la recuperación de errores
    cuando la clasificación ya se completó,
    pero falla la generación de la respuesta.
    """

    # Permite simular el modelo y contar sus llamadas.
    from unittest.mock import MagicMock

    # Clase utilizada para representar una respuesta
    # generada por el modelo.
    from langchain_core.messages import AIMessage

    # Constructor del enrutamiento seguro.
    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    def modelo_con_fallo_en_respuesta(entrada: object) -> AIMessage:
        """Clasifica correctamente, pero falla al generar la respuesta.

        Args:
            entrada (object):
                Entrada recibida por el modelo simulado.

        Returns:
            AIMessage:
                Mensaje de clasificación durante
                la primera llamada.

        Raises:
            RuntimeError:
                Representa un fallo durante
                la generación de la respuesta.
        """

        # La primera llamada corresponde a la clasificación.
        if modelo_simulado.call_count == 1:
            return AIMessage(content="pregunta")

        # La segunda llamada simula un fallo de generación.
        raise RuntimeError("Fallo simulado al generar respuesta")

    # Configura el modelo con la función que permite
    # clasificar primero y fallar posteriormente.
    modelo_simulado = MagicMock(
        side_effect=modelo_con_fallo_en_respuesta
    )

    # Construye la cadena protegida por el fallback.
    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_simulado)
    )

    # Define la consulta municipal.
    mensaje = "¿Cómo solicito una patente comercial?"

    # Ejecuta el enrutamiento completo.
    resultado = cadena.invoke({"mensaje": mensaje})

    # El mensaje original debe conservarse.
    assert resultado["mensaje"] == mensaje

    # El fallo posterior debe activar la categoría error.
    assert resultado["categoria"] == "error"

    # Comprueba la respuesta alternativa entregada.
    assert resultado["respuesta"] == (
        "No fue posible procesar tu solicitud en este momento. "
        "Por favor, intenta nuevamente más tarde."
    )

    # Una llamada clasifica y la segunda intenta responder.
    assert modelo_simulado.call_count == 2


# ============================================================
# 9. ENRUTAMIENTO EXITOSO
# ============================================================

def test_enrutamiento_seguro_conserva_respuesta_exitosa() -> None:
    """Verifica que una ejecución correcta no active el fallback.

    Simula dos respuestas consecutivas del modelo:

        1. Clasificación de la consulta como "pregunta".
        2. Generación de una respuesta sobre el procedimiento.

    Comprueba que el resultado conserve:

        - El mensaje original.
        - La categoría de clasificación.
        - La respuesta generada.

    También verifica que el modelo haya recibido
    exactamente dos llamadas.
    """

    # Permite simular respuestas consecutivas del modelo.
    from unittest.mock import MagicMock

    # Representa las respuestas simuladas del modelo.
    from langchain_core.messages import AIMessage

    # Constructor del enrutamiento seguro.
    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    # Configura las respuestas para clasificación y generación.
    modelo_simulado = MagicMock(
        side_effect=[
            AIMessage(content="pregunta"),
            AIMessage(content="Estos son los pasos del procedimiento."),
        ]
    )

    # Construye la cadena de enrutamiento seguro.
    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_simulado)
    )

    # Define el mensaje original del usuario.
    mensaje = "¿Cómo puedo realizar un trámite municipal?"

    # Ejecuta la clasificación y generación simuladas.
    resultado = cadena.invoke({"mensaje": mensaje})

    # Comprueba que se conserve la respuesta exitosa
    # con todos los campos esperados.
    assert resultado == {
        "mensaje": mensaje,
        "categoria": "pregunta",
        "respuesta": "Estos son los pasos del procedimiento.",
    }

    # Se espera una llamada para clasificar
    # y otra para generar la respuesta.
    assert modelo_simulado.call_count == 2


# ============================================================
# 10. REGISTRO DE ERRORES DEL ENRUTAMIENTO SEGURO
# ============================================================

def test_enrutamiento_seguro_registra_error(caplog) -> None:
    """Verifica el registro de errores del enrutamiento seguro.

    Simula un fallo técnico cuyo mensaje contiene
    un detalle interno que no debe exponerse.

    Utiliza caplog para capturar registros de nivel ERROR.

    Comprueba que:

        - El mensaje original se conserve.
        - La categoría del resultado sea "error".
        - Se registre el fallo del enrutamiento.
        - Se registre la activación del fallback.
        - El detalle confidencial no aparezca en el log.
        - El detalle confidencial no aparezca
          en la respuesta entregada al usuario.

    A diferencia de la prueba de ejecución segura,
    este escenario exige que el detalle de la excepción
    tampoco aparezca en los registros capturados.
    """

    # Permite capturar registros de nivel ERROR.
    import logging

    # Constructor del enrutamiento protegido.
    from src.manejo_errores_langchain import (
        construir_enrutamiento_seguro,
    )

    def modelo_con_error(entrada: object) -> str:
        """Simula un fallo técnico del modelo.

        Args:
            entrada (object):
                Entrada recibida por el modelo simulado.

        Raises:
            RuntimeError:
                Representa un error técnico interno
                cuyo detalle no debe divulgarse.
        """

        # Genera una excepción con un mensaje
        # que representa información interna.
        raise RuntimeError("Fallo interno confidencial")

    # Construye una cadena de enrutamiento
    # utilizando el modelo que genera la excepción.
    cadena = construir_enrutamiento_seguro(
        RunnableLambda(modelo_con_error)
    )

    # Define la consulta que desencadena el fallo simulado.
    mensaje = "¿Cómo solicito una autorización municipal?"

    # Captura los registros de error durante
    # la ejecución del enrutamiento.
    with caplog.at_level(logging.ERROR):
        resultado = cadena.invoke({"mensaje": mensaje})

    # La respuesta debe mantener el contrato de VyOps.
    #
    # Se conserva el mensaje original y se identifica
    # el resultado mediante la categoría error.
    assert resultado["mensaje"] == mensaje
    assert resultado["categoria"] == "error"

    # El error técnico debe quedar registrado.
    #
    # Los mensajes permiten identificar el fallo
    # y la activación del mecanismo alternativo.
    assert "Falló el enrutamiento de LangChain." in caplog.text
    assert "Se activó la respuesta alternativa." in caplog.text

    # El detalle interno no debe aparecer
    # en los registros capturados.
    assert "Fallo interno confidencial" not in caplog.text

    # El usuario no debe recibir información interna.
    assert "Fallo interno confidencial" not in resultado["respuesta"]
