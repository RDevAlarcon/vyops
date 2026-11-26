"""Verificador completo de la ficha funcional de VyOps.

Actividad correspondiente al Bloque 34 de SkillNest.

Valida la estructura, los requerimientos, los criterios
de aceptación, el plan de construcción y la revisión
del alcance de la ficha funcional.
"""

import argparse
import re
from pathlib import Path

from ficha_datos import cargar

from verificar_ficha import (
    RAIZ_PROYECTO,
    RUTA_FICHA,
    extraer_secciones,
    validar_estructura,
    validar_problema,
    validar_requerimientos,
    validar_alcance,
    validar_diagrama,
)


# Cantidad de hitos permitidos en el plan de construcción.
MIN_HITOS = 3
MAX_HITOS = 6
# Nombre del documento de revisión del alcance.
NOMBRE_REVISION = "revision_alcance.md"

def validar_base(
    contenido: str,
    raiz: Path = RAIZ_PROYECTO,
) -> tuple[list[str], list[str]]:
    """Valida las primeras tres secciones de la ficha funcional.

    Reutiliza las funciones implementadas durante el Bloque 33.

    Args:
        contenido: Contenido completo de la ficha funcional.

    Returns:
        Tupla con los errores y avisos detectados.
    """
    secciones = extraer_secciones(contenido)

    errores = validar_estructura(secciones)
    avisos = []

    # Sección 1: problema de negocio.
    if 1 in secciones:
        texto1 = secciones[1]["contenido"]
        avisos.extend(validar_problema(texto1))

    # Sección 2: requerimientos y alcance.
    if 2 in secciones:
        texto2 = secciones[2]["contenido"]
        errores.extend(validar_requerimientos(texto2))
        errores.extend(validar_alcance(texto2))

    # Sección 3: arquitectura de la solución.
    if 3 in secciones:
        texto3 = secciones[3]["contenido"]
        errores.extend(validar_diagrama(texto3, raiz=raiz))

    return errores, avisos

def validar_pendientes(ficha: dict) -> list[str]:
    """Detecta secciones pendientes de completar.

    Comprueba que las secciones de criterios de aceptación
    y plan de construcción tengan contenido definitivo.

    Args:
        ficha: Datos estructurados de la ficha funcional.

    Returns:
        Lista de errores asociados a secciones incompletas.
    """
    errores = []

    secciones = {
        4: ("Criterios de aceptación", ficha["texto4"]),
        5: ("Plan de construcción por hitos", ficha["texto5"]),
    }

    for numero, (titulo, contenido) in secciones.items():
        texto = contenido.strip().upper()

        if (
            not texto
            or "[PENDIENTE" in texto
            or "[COMPLETAR" in texto
        ):
            errores.append(
                f"La seccion {numero} esta pendiente: {titulo}"
            )

    return errores

def validar_criterios(ficha: dict) -> tuple[list[str], list[str]]:
    """Valida los criterios de aceptación de la ficha funcional.

    Comprueba su existencia, formato, unicidad, referencias
    y cobertura de los requerimientos obligatorios.

    Args:
        ficha: Datos estructurados de la ficha funcional.

    Returns:
        Tupla con los errores y avisos detectados.
    """
    errores = []
    avisos = []

    criterios = ficha["criterios"]
    requerimientos = set(ficha["rf"]) | set(ficha["rnf"])

    obligatorios = (
        set(ficha["cajones"]["imprescindible"])
        | set(ficha["rnf"])
    )

    # Comprobar que existen criterios de aceptación.
    if not criterios:
        errores.append("No existen criterios de aceptacion.")

    # Detectar criterios que no respetan el formato establecido.
    lineas_criterios = re.findall(
        r"(?m)^- CA.*$",
        ficha["texto4"],
    )

    if len(lineas_criterios) != len(criterios):
        errores.append(
            "Existen criterios de aceptacion con formato incorrecto."
        )

    identificadores = set()
    cubiertos = set()

    for criterio in criterios:
        identificador = criterio["id"]
        referencias = criterio["cubre"]
        descripcion = criterio["texto"]

        # Detectar identificadores duplicados.
        if identificador in identificadores:
            errores.append(
                f"Criterio duplicado: {identificador}"
            )

        identificadores.add(identificador)

        # Comprobar que el criterio referencia un requerimiento.
        if not referencias:
            errores.append(
                f"{identificador} no referencia ningun requerimiento."
            )

        # Validar que los requerimientos referenciados existen.
        for referencia in referencias:
            if referencia not in requerimientos:
                errores.append(
                    f"{identificador} referencia un "
                    f"requerimiento inexistente: {referencia}"
                )
            else:
                cubiertos.add(referencia)

        # Identificar criterios potencialmente poco verificables.
        if not re.search(r'\d|"', descripcion):
            avisos.append(
                f"{identificador} podria ser poco verificable."
            )

    # Comprobar la cobertura de los requerimientos obligatorios.
    faltantes = sorted(obligatorios - cubiertos)

    for referencia in faltantes:
        errores.append(
            f"Requerimiento obligatorio sin criterio: {referencia}"
        )

    return errores, avisos

def validar_presupuesto(ficha: dict) -> list[str]:
    """Valida el presupuesto temporal del plan de construcción.

    Comprueba la disponibilidad de horas, el margen de
    imprevistos y el total de horas planificadas.

    Args:
        ficha: Datos estructurados de la ficha funcional.

    Returns:
        Lista de errores presupuestarios detectados.
    """
    errores = []

    disponibles = ficha["disponibles"]
    margen = ficha["margen"]
    hitos = ficha["hitos"]

    # Comprobar que el presupuesto está definido.
    if disponibles is None:
        errores.append("No se definieron las horas disponibles.")

    if margen is None:
        errores.append("No se definio el margen de imprevistos.")

    # No realizar cálculos si faltan datos obligatorios.
    if errores:
        return errores

    # Validar los valores presupuestarios.
    if disponibles <= 0:
        errores.append(
            "Las horas disponibles deben ser mayores que 0."
        )

    if margen < 0 or margen >= disponibles:
        errores.append(
            "El margen de imprevistos debe ser mayor o igual "
            "a 0 y menor que las horas disponibles."
        )

    if errores:
        return errores

    # Calcular el presupuesto máximo de planificación.
    limite = round(disponibles - margen, 2)

    horas_planificadas = round(
        sum(hito["horas"] for hito in hitos),
        2,
    )

    # Detectar excesos presupuestarios.
    if horas_planificadas > limite:
        exceso = round(horas_planificadas - limite, 2)

        errores.append(
            f"Presupuesto excedido: "
            f"{horas_planificadas:g}/{limite:g} h. "
            f"Exceso: {exceso:g} h."
        )

    return errores

def validar_hitos(ficha: dict) -> list[str]:
    """Valida los hitos del plan de construcción.

    Comprueba la cantidad, formato, duración, unicidad,
    referencias y cobertura de los requerimientos y
    criterios de aceptación.

    Args:
        ficha: Datos estructurados de la ficha funcional.

    Returns:
        Lista de errores detectados en el plan.
    """
    errores = []

    hitos = ficha["hitos"]
    requerimientos = set(ficha["rf"]) | set(ficha["rnf"])

    obligatorios = set(ficha["cajones"]["imprescindible"])

    criterios = {
        criterio["id"]: set(criterio["cubre"])
        for criterio in ficha["criterios"]
    }

    # Comprobar la cantidad de hitos.
    if not MIN_HITOS <= len(hitos) <= MAX_HITOS:
        errores.append(
            f"El plan debe contener entre {MIN_HITOS} "
            f"y {MAX_HITOS} hitos."
        )

    # Detectar hitos con formato incorrecto.
    lineas_hitos = re.findall(
        r"(?m)^- H\d.*$",
        ficha["texto5"],
    )

    if len(lineas_hitos) != len(hitos):
        errores.append(
            "Existen hitos con formato incorrecto."
        )

    identificadores = set()
    requerimientos_cubiertos = set()
    criterios_planificados = set()

    for hito in hitos:
        identificador = hito["id"]
        horas = hito["horas"]
        referencias = hito["cubre"]
        comprobaciones = hito["criterios"]

        # Comprobar identificadores únicos.
        if identificador in identificadores:
            errores.append(
                f"Hito duplicado: {identificador}"
            )

        identificadores.add(identificador)

        # Validar la duración individual.
        if horas <= 0:
            errores.append(
                f"{identificador} debe tener una duracion "
                "mayor que 0 horas."
            )

        # Comprobar que el hito cubre requerimientos.
        if not referencias:
            errores.append(
                f"{identificador} no referencia requerimientos."
            )

        for referencia in referencias:
            if referencia not in requerimientos:
                errores.append(
                    f"{identificador} referencia un "
                    f"requerimiento inexistente: {referencia}"
                )
            else:
                requerimientos_cubiertos.add(referencia)

        # Comprobar que el hito tiene criterios asociados.
        if not comprobaciones:
            errores.append(
                f"{identificador} no tiene criterios de aceptacion."
            )

        for criterio in comprobaciones:
            if criterio not in criterios:
                errores.append(
                    f"{identificador} referencia un "
                    f"criterio inexistente: {criterio}"
                )
            else:
                criterios_planificados.add(criterio)

                # Comprobar coherencia entre criterio y hito.
                if not criterios[criterio].issubset(
                    set(referencias)
                ):
                    errores.append(
                        f"{identificador} contiene un criterio "
                        f"incompatible con sus requerimientos: "
                        f"{criterio}"
                    )

    # Detectar RF imprescindibles sin hitos asociados.
    faltantes = sorted(
        obligatorios - requerimientos_cubiertos
    )

    for referencia in faltantes:
        errores.append(
            f"Requerimiento imprescindible sin hito: {referencia}"
        )

    # Detectar criterios que no aparecen en ningún hito.
    huerfanos = sorted(
        set(criterios) - criterios_planificados
    )

    for criterio in huerfanos:
        errores.append(
            f"Criterio sin hito asociado: {criterio}"
        )

    return errores

def validar_contenido_revision(contenido: str) -> list[str]:
    """Valida el contenido del documento de revisión del alcance.

    Comprueba la existencia de hallazgos, sus identificadores
    y las decisiones asociadas a cada uno.

    Args:
        contenido: Contenido Markdown del documento de revisión.

    Returns:
        Lista de errores detectados.
    """
    errores = []

    patron_hallazgo = re.compile(
        r"^- Hallazgo (\d+)(?: [^:\n]*)?:[ \t]+(.+)$",
        flags=re.MULTILINE,
    )

    patron_decision = re.compile(
        r"^  Decisión: (aceptado|rechazado|aplazado)\b.*$",
        flags=re.MULTILINE,
    )

    hallazgos = list(patron_hallazgo.finditer(contenido))
    decisiones = list(patron_decision.finditer(contenido))

    # Comprobar la cantidad mínima de hallazgos.
    if len(hallazgos) < 2:
        errores.append(
            "La revision debe contener al menos 2 hallazgos."
        )

    # Comprobar que existe una decisión por cada hallazgo.
    if len(hallazgos) != len(decisiones):
        errores.append(
            "La cantidad de hallazgos y decisiones no coincide."
        )

    identificadores = set()

    for indice, hallazgo in enumerate(hallazgos):
        identificador = hallazgo.group(1)

        # Detectar identificadores duplicados.
        if identificador in identificadores:
            errores.append(
                f"Hallazgo duplicado: {identificador}"
            )

        identificadores.add(identificador)

        # Delimitar el contenido de cada hallazgo.
        inicio = hallazgo.end()

        if indice + 1 < len(hallazgos):
            fin = hallazgos[indice + 1].start()
        else:
            fin = len(contenido)

        bloque = contenido[inicio:fin]

        # Comprobar que cada hallazgo tiene su propia decisión.
        decisiones_hallazgo = patron_decision.findall(bloque)

        if len(decisiones_hallazgo) != 1:
            errores.append(
                f"El hallazgo {identificador} debe tener "
                "exactamente una decision valida."
            )

    return errores

def validar_revision(ruta_ficha: Path = RUTA_FICHA) -> list[str]:
    """Valida el archivo de revisión del alcance.

    Localiza el documento de revisión en el mismo directorio
    de la ficha funcional y comprueba su contenido.

    Args:
        ruta_ficha: Ruta de la ficha de diseño funcional.

    Returns:
        Lista de errores detectados en la revisión.
    """
    ruta_revision = Path(ruta_ficha).parent / NOMBRE_REVISION

    # Comprobar que el documento existe.
    if not ruta_revision.is_file():
        return [
            "No se encontro el archivo de revision del alcance."
        ]

    # Leer el documento utilizando una codificación explícita.
    try:
        contenido = ruta_revision.read_text(encoding="utf-8")

    except UnicodeDecodeError:
        return [
            "El archivo de revision no tiene codificacion UTF-8 valida."
        ]

    except OSError:
        return [
            "No fue posible leer el archivo de revision del alcance."
        ]

    # Delegar la validación del contenido.
    return validar_contenido_revision(contenido)

def verificar(
    ruta_ficha: Path = RUTA_FICHA,
) -> tuple[list[str], list[str]]:
    """Ejecuta la validación completa de la ficha funcional.

    Organiza las validaciones por etapas y detiene el flujo
    cuando encuentra errores que impiden continuar.

    Args:
        ruta_ficha: Ruta de la ficha de diseño funcional.

    Returns:
        Tupla con los errores y avisos detectados.
    """
    errores = []
    avisos = []

    ruta_ficha = Path(ruta_ficha)

    # Etapa 1: comprobar la existencia del archivo.
    if not ruta_ficha.is_file():
        errores.append(
            "No se encontro la ficha de diseno funcional."
        )
        return errores, avisos

    # Leer la ficha utilizando codificación UTF-8.
    try:
        contenido = ruta_ficha.read_text(encoding="utf-8")

    except UnicodeDecodeError:
        errores.append(
            "La ficha funcional no tiene codificacion UTF-8 valida."
        )
        return errores, avisos

    except OSError:
        errores.append(
            "No fue posible leer la ficha funcional."
        )
        return errores, avisos

    # Determinar la raiz del proyecto a partir de la ficha.
    raiz = ruta_ficha.resolve().parent.parent

    # Etapa 2: validar las secciones 1 a 3.
    errores_base, avisos_base = validar_base(
        contenido,
        raiz=raiz,
    )

    errores.extend(errores_base)
    avisos.extend(avisos_base)

    if errores:
        return errores, avisos

    # Obtener los datos estructurados de la ficha.
    try:
        ficha = cargar(ruta_ficha)

    except (OSError, UnicodeDecodeError):
        errores.append(
            "No fue posible cargar los datos de la ficha funcional."
        )
        return errores, avisos

    # Etapa 3: comprobar las secciones pendientes.
    errores.extend(validar_pendientes(ficha))

    if errores:
        return errores, avisos

    # Etapa 4: validar criterios, presupuesto e hitos.
    errores_ca, avisos_ca = validar_criterios(ficha)

    errores.extend(errores_ca)
    avisos.extend(avisos_ca)

    errores.extend(validar_presupuesto(ficha))
    errores.extend(validar_hitos(ficha))

    if errores:
        return errores, avisos

    # Etapa 5: validar la revisión del alcance.
    errores.extend(validar_revision(ruta_ficha))

    return errores, avisos

def main() -> int:
    """Ejecuta el verificador completo desde la terminal.

    Permite utilizar la ficha funcional predeterminada
    o proporcionar una ruta alternativa.

    Returns:
        0 si la ficha supera las validaciones.
        1 si existen errores de validación.
    """
    parser = argparse.ArgumentParser(
        description="Verificador completo de la ficha funcional."
    )

    parser.add_argument(
        "ruta",
        nargs="?",
        type=Path,
        default=RUTA_FICHA,
        help="Ruta alternativa de la ficha funcional.",
    )

    argumentos = parser.parse_args()

    errores, avisos = verificar(argumentos.ruta)

    print("=== VERIFICACION COMPLETA DE FICHA FUNCIONAL ===")
    print()

    # Mostrar los errores detectados.
    for error in errores:
        print(f"ERROR: {error}")

    # Mostrar las observaciones no bloqueantes.
    for aviso in avisos:
        print(f"AVISO: {aviso}")

    print()
    print(f"Errores: {len(errores)}")
    print(f"Avisos: {len(avisos)}")
    print()

    # Determinar el resultado final.
    if errores:
        print("RESULTADO: FAIL")
        return 1

    print("Ficha verificada: las cinco secciones son coherentes.")
    print("RESULTADO: PASS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())