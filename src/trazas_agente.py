
"""Registro de trazas de ejecución del agente VyOps.

Este módulo proporciona mecanismos de trazabilidad
para registrar y analizar las operaciones realizadas
por el agente municipal VyOps.

Su objetivo es conservar evidencia de las herramientas
utilizadas durante cada ejecución y detectar patrones
de llamadas consecutivas que puedan requerir revisión.

Responsabilidades principales:

    1. Registrar la fecha y hora de una ejecución.
    2. Asociar cada traza a una sesión.
    3. Conservar la entrada enviada al agente.
    4. Registrar herramientas, argumentos y observaciones.
    5. Almacenar la respuesta final generada.
    6. Guardar las trazas en formato JSON Lines.
    7. Detectar repeticiones consecutivas de herramientas.
    8. Devolver alertas para su análisis posterior.

Formato de almacenamiento:

    JSONL (JSON Lines)

    Cada línea del archivo representa una ejecución
    del agente serializada como un objeto JSON.

Estructura de una traza:

    timestamp:
        Fecha y hora de registro en UTC.

    session_id:
        Identificador de la sesión.

    entrada:
        Mensaje recibido por el agente.

    acciones:
        Lista de herramientas utilizadas,
        sus argumentos y observaciones.

    respuesta_final:
        Resultado textual final del agente.

Detección de repeticiones:

    El módulo permite identificar secuencias
    consecutivas de llamadas a una misma herramienta
    dentro de una ejecución registrada.

    El umbral predeterminado es de tres llamadas.

    Las alertas permiten localizar posibles
    comportamientos repetitivos del agente.

IMPORTANTE:
    El registro contiene entradas, argumentos
    y observaciones de las herramientas.

    Estos datos pueden incluir información sensible
    dependiendo del contenido procesado.

    Este módulo no implementa anonimización,
    cifrado, rotación de archivos ni control
    de acceso al almacenamiento.

    La detección de repeticiones es una herramienta
    de diagnóstico y no demuestra por sí misma
    que exista un error o un comportamiento malicioso.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# json permite serializar las trazas
# y recuperar posteriormente los registros JSONL.
import json

# datetime obtiene la fecha y hora de registro.
#
# timezone.utc permite utilizar una referencia
# temporal explícita en UTC.
from datetime import datetime, timezone

# Path proporciona una interfaz para trabajar
# con rutas, directorios y archivos.
from pathlib import Path

# Any permite representar valores de distintos tipos
# dentro de los resultados del agente.
from typing import Any


# ============================================================
# 2. REGISTRO DE TRAZAS DE EJECUCIÓN
# ============================================================

def registrar_traza(
    session_id: str,
    entrada: str,
    resultado: dict[str, Any],
    ruta_archivo: str | Path = "trazas_agente.jsonl",
) -> None:
    """Registra las herramientas utilizadas y la respuesta del agente.

    Args:
        session_id:
            Identificador de la sesión correspondiente
            a la ejecución del agente.

        entrada:
            Mensaje de entrada que recibió el agente.

        resultado:
            Diccionario con los resultados de ejecución.

            Puede contener:

                intermediate_steps:
                    Secuencia de pares formados
                    por una acción y su observación.

                output:
                    Respuesta final generada por el agente.

        ruta_archivo:
            Ruta del archivo donde se almacenará
            la traza en formato JSONL.

            Su valor predeterminado es
            trazas_agente.jsonl.

    Returns:
        None:
            La función escribe el registro
            y no devuelve ningún valor.

    Flujo:
        1. Recuperar los pasos intermedios del agente.
        2. Extraer herramientas, argumentos y observaciones.
        3. Construir la estructura de la traza.
        4. Generar la marca temporal en UTC.
        5. Crear el directorio de destino si es necesario.
        6. Abrir el archivo en modo de anexado.
        7. Escribir una línea JSON.

    El archivo se abre en modo "a", por lo que
    las trazas anteriores se conservan.

    La serialización utiliza ensure_ascii=False
    para conservar caracteres Unicode legibles.

    default=str permite representar como texto
    ciertos objetos que JSON no serializa directamente.

    La función no elimina ni modifica
    los registros previamente almacenados.
    """

    # --------------------------------------------------------
    # 2.1. PREPARACIÓN DEL REGISTRO DE ACCIONES
    # --------------------------------------------------------

    # Lista que almacenará las herramientas utilizadas
    # durante la ejecución del agente.
    acciones = []

    # --------------------------------------------------------
    # 2.2. RECORRIDO DE LOS PASOS INTERMEDIOS
    # --------------------------------------------------------

    # Recupera los pasos intermedios.
    #
    # Si no existe la clave intermediate_steps,
    # utiliza una lista vacía.
    #
    # Cada elemento esperado contiene:
    #
    # - accion: información de la herramienta ejecutada.
    # - observacion: resultado de esa ejecución.
    for accion, observacion in resultado.get("intermediate_steps", []):

        # Registra el nombre de la herramienta,
        # sus argumentos y la observación recibida.
        acciones.append(
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
        )

    # --------------------------------------------------------
    # 2.3. CONSTRUCCIÓN DE LA TRAZA
    # --------------------------------------------------------

    # Organiza la información de ejecución
    # en una estructura serializable.
    traza = {
        # Fecha y hora actual en UTC,
        # representada mediante ISO 8601.
        "timestamp": datetime.now(timezone.utc).isoformat(),

        # Identificador de la sesión.
        "session_id": session_id,

        # Entrada original recibida por el agente.
        "entrada": entrada,

        # Herramientas ejecutadas y sus resultados.
        "acciones": acciones,

        # Respuesta final del agente.
        #
        # Si output no existe, utiliza una cadena vacía.
        "respuesta_final": resultado.get("output", ""),
    }

    # --------------------------------------------------------
    # 2.4. PREPARACIÓN DE LA RUTA
    # --------------------------------------------------------

    # Convierte la ruta recibida en un objeto Path.
    ruta = Path(ruta_archivo)

    # Crea los directorios necesarios.
    #
    # parents=True permite crear directorios intermedios.
    # exist_ok=True evita errores cuando ya existen.
    ruta.parent.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # 2.5. ESCRITURA DEL REGISTRO JSONL
    # --------------------------------------------------------

    # Abre el archivo en modo de anexado.
    #
    # encoding="utf-8" permite conservar
    # caracteres especiales correctamente.
    with ruta.open("a", encoding="utf-8") as archivo:

        # Serializa la traza como JSON y agrega
        # un salto de línea al final.
        #
        # Cada llamada produce una nueva línea
        # dentro del archivo de trazabilidad.
        archivo.write(
            json.dumps(traza, ensure_ascii=False, default=str) + "\n"
        )


# ============================================================
# 3. DETECCIÓN DE REPETICIONES SOSPECHOSAS
# ============================================================

def marcar_repeticiones_sospechosas(
    ruta_archivo: str | Path = "trazas_agente.jsonl",
    umbral: int = 3,
) -> list[dict[str, Any]]:
    """Detecta llamadas consecutivas repetidas a una herramienta.

    Args:
        ruta_archivo:
            Ruta del archivo JSONL que contiene
            las trazas de ejecución del agente.

            Su valor predeterminado es
            trazas_agente.jsonl.

        umbral:
            Número mínimo de llamadas consecutivas
            que activa una alerta.

            Su valor predeterminado es 3.

            Debe ser mayor o igual a 2.

    Returns:
        list[dict[str, Any]]:
            Lista de alertas identificadas.

            Cada alerta contiene:

                linea:
                    Número de línea del archivo JSONL.

                session_id:
                    Identificador de la sesión registrada.

                herramienta:
                    Nombre de la herramienta repetida.

                repeticiones:
                    Cantidad de repeticiones alcanzadas
                    al generar la alerta.

            Si el archivo no existe o no se detectan
            secuencias que alcancen el umbral,
            devuelve una lista vacía.

    Raises:
        ValueError:
            Cuando el umbral es menor que 2.

    Flujo:
        1. Validar el umbral.
        2. Comprobar la existencia del archivo.
        3. Leer las trazas línea por línea.
        4. Ignorar las líneas vacías.
        5. Recuperar las acciones de cada traza.
        6. Comparar herramientas consecutivas.
        7. Registrar alertas al alcanzar el umbral.
        8. Devolver las alertas encontradas.

    La detección se realiza de forma independiente
    para cada línea del archivo.

    Por lo tanto, las repeticiones no se acumulan
    entre ejecuciones distintas del agente.

    Se genera una alerta cuando la cantidad
    de repeticiones es exactamente igual al umbral.

    Una secuencia más larga no genera alertas
    adicionales por cada repetición posterior.

    La función no modifica el archivo analizado.
    """

    # --------------------------------------------------------
    # 3.1. VALIDACIÓN DEL UMBRAL
    # --------------------------------------------------------

    # Impide configurar un umbral inferior a dos.
    #
    # La detección requiere al menos dos
    # llamadas consecutivas a una herramienta.
    if umbral < 2:
        raise ValueError("El umbral debe ser al menos 2.")

    # --------------------------------------------------------
    # 3.2. PREPARACIÓN DE LA RUTA
    # --------------------------------------------------------

    # Convierte la ruta del archivo en un objeto Path.
    ruta = Path(ruta_archivo)

    # --------------------------------------------------------
    # 3.3. VERIFICACIÓN DE EXISTENCIA
    # --------------------------------------------------------

    # Si el archivo todavía no existe,
    # no hay registros que analizar.
    if not ruta.exists():
        return []

    # --------------------------------------------------------
    # 3.4. INICIALIZACIÓN DE ALERTAS
    # --------------------------------------------------------

    # Lista que almacenará las secuencias repetitivas
    # identificadas durante el análisis.
    alertas: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # 3.5. LECTURA DEL ARCHIVO JSONL
    # --------------------------------------------------------

    # Abre el archivo en modo de lectura.
    with ruta.open("r", encoding="utf-8") as archivo:

        # Recorre las líneas conservando su número real.
        #
        # start=1 permite utilizar una numeración
        # compatible con la visualización habitual
        # de archivos de texto.
        for numero_linea, linea in enumerate(archivo, start=1):

            # ------------------------------------------------
            # 3.6. OMISIÓN DE LÍNEAS VACÍAS
            # ------------------------------------------------

            # Ignora líneas que no contienen información.
            if not linea.strip():
                continue

            # ------------------------------------------------
            # 3.7. RECUPERACIÓN DE LA TRAZA
            # ------------------------------------------------

            # Convierte la línea JSON
            # en una estructura de Python.
            traza = json.loads(linea)

            # Recupera las acciones registradas.
            #
            # Si no existe la clave acciones,
            # utiliza una lista vacía.
            acciones = traza.get("acciones", [])

            # ------------------------------------------------
            # 3.8. INICIALIZACIÓN DEL CONTADOR
            # ------------------------------------------------

            # Conserva el nombre de la herramienta anterior
            # para comparar llamadas consecutivas.
            herramienta_anterior: str | None = None

            # Cantidad de llamadas consecutivas
            # de la herramienta actual.
            repeticiones = 0

            # ------------------------------------------------
            # 3.9. ANÁLISIS DE LAS ACCIONES
            # ------------------------------------------------

            # Recorre las herramientas ejecutadas
            # dentro de la traza actual.
            for accion in acciones:

                # Obtiene el nombre de la herramienta.
                herramienta = accion.get("herramienta")

                # --------------------------------------------
                # 3.10. COMPARACIÓN CON LA ACCIÓN ANTERIOR
                # --------------------------------------------

                # Si la herramienta coincide con la anterior,
                # incrementa el contador consecutivo.
                if herramienta == herramienta_anterior:
                    repeticiones += 1

                else:
                    # Cuando cambia la herramienta,
                    # comienza una nueva secuencia.
                    herramienta_anterior = herramienta
                    repeticiones = 1

                # --------------------------------------------
                # 3.11. GENERACIÓN DE ALERTAS
                # --------------------------------------------

                # Registra una alerta cuando la secuencia
                # alcanza exactamente el umbral configurado.
                if repeticiones == umbral:
                    alertas.append(
                        {
                            # Línea del archivo donde
                            # se encontró la secuencia.
                            "linea": numero_linea,

                            # Sesión asociada a la traza.
                            "session_id": traza.get("session_id"),

                            # Herramienta que se repitió.
                            "herramienta": herramienta,

                            # Cantidad de repeticiones
                            # que activó la alerta.
                            "repeticiones": repeticiones,
                        }
                    )

    # --------------------------------------------------------
    # 3.12. DEVOLUCIÓN DE RESULTADOS
    # --------------------------------------------------------

    # Devuelve todas las alertas encontradas
    # durante el análisis del archivo.
    return alertas
