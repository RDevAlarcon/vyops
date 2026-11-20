
from langgraph.types import Command

from grafo_supervision import construir_grafo


HUELLA = "fdff8ebf6d37"


def iniciar_supervision(app, thread_id):
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    resultado = app.invoke(
        {
            "huella_nueva": HUELLA,
            "aprobado": False,
        },
        config=config,
    )

    return config, resultado


def test_grafo_se_interrumpe_antes_de_aplicar(capsys):
    app = construir_grafo()

    config, resultado = iniciar_supervision(
        app, "test-interrupcion"
    )

    assert "__interrupt__" in resultado
    assert app.get_state(config).next == ("supervisar",)

    salida = capsys.readouterr().out
    assert "Versión ACTIVADA" not in salida


def test_aprobacion_activa_version(capsys):
    app = construir_grafo()

    config, pendiente = iniciar_supervision(
        app, "test-aprobacion"
    )

    assert "__interrupt__" in pendiente

    resultado = app.invoke(
        Command(resume=True),
        config=config,
    )

    assert resultado["aprobado"] is True
    assert app.get_state(config).next == ()

    salida = capsys.readouterr().out
    assert f"Versión APROBADA (simulación): {HUELLA}" in salida


def test_rechazo_no_activa_version(capsys):
    app = construir_grafo()

    config, pendiente = iniciar_supervision(
        app, "test-rechazo"
    )

    assert "__interrupt__" in pendiente

    resultado = app.invoke(
        Command(resume=False),
        config=config,
    )

    assert resultado["aprobado"] is False
    assert app.get_state(config).next == ()

    salida = capsys.readouterr().out

    assert f"Versión RECHAZADA (simulación): {HUELLA}" in salida
    assert "Versión APROBADA (simulación)" not in salida
