
"""Banco de prompts estructurados para el proyecto VyOps.

Proyecto académico — Especialización en Desarrollo con IA Generativa.
Unidad 1 — Bloque 10: Ingeniería de prompts y consistencia.

Objetivo:
    Definir un conjunto de prompts reutilizables para evaluar
    tareas empresariales mediante Google Gemini.

Casos incluidos:
    1. Clasificación de solicitudes.
    2. Extracción de información de clientes.
    3. Priorización de solicitudes empresariales.

Estructura:
    Cada elemento de BANCO_DE_PROMPTS contiene:
        - nombre: Identificador del caso de evaluación.
        - system_instruction: Instrucciones para el modelo.
        - ejemplo_usuario: Mensaje utilizado durante la prueba.
        - claves_esperadas: Campos obligatorios de la respuesta.
        - response_schema: Esquema JSON solicitado a Gemini.

Validación:
    Los esquemas definen tipos de datos, campos obligatorios
    y restricciones aplicables a cada tarea.

    La comprobación de las respuestas se realiza desde
    prompts/test_consistencia.py.

Arquitectura:
    Este módulo contiene únicamente la configuración de los
    prompts. No realiza solicitudes HTTP, no utiliza credenciales
    y no ejecuta consultas a Gemini.

Extensibilidad:
    Permite incorporar nuevos casos de evaluación manteniendo
    separadas las instrucciones de la lógica de ejecución.
"""

# ============================================================
# 1. CATÁLOGO DE PROMPTS ESTRUCTURADOS
# ============================================================

# Catálogo de casos de prueba utilizados para evaluar la consistencia
# de las respuestas estructuradas de Gemini.
# Cada caso incluye instrucciones, entrada de ejemplo y esquema JSON.
#
# El banco utiliza una lista de diccionarios.
#
# Cada diccionario representa un caso independiente
# que puede ser recorrido por el módulo de evaluación.
#
# La separación entre configuración y ejecución permite
# reutilizar los prompts sin duplicar la lógica
# de construcción de solicitudes y validación.
BANCO_DE_PROMPTS = [

    # ========================================================
    # 2. CASO 1: CLASIFICACIÓN DE SOLICITUDES
    # ========================================================

    {
        # Identificador utilizado para reconocer
        # este caso en los resultados de evaluación.
        "nombre": "clasificar_solicitud",

        # ----------------------------------------------------
        # 2.1. INSTRUCCIONES DEL MODELO
        # ----------------------------------------------------

        # Define el rol de Gemini como clasificador.
        #
        # Establece cuatro categorías permitidas:
        # - reservas
        # - ventas
        # - soporte
        # - otros
        #
        # Exige una respuesta JSON con dos campos.
        #
        # La confianza debe expresarse mediante
        # un entero entre 0 y 100, sin símbolo %.
        #
        # Se prohíben explicaciones y campos adicionales.
        "system_instruction": (
            "Eres un asistente de clasificación de solicitudes para VyOps. "
            "Clasifica el mensaje del usuario en una de estas categorías: "
            "reservas, ventas, soporte u otros. "
            "Devuelve exclusivamente un objeto JSON con las claves "
            "'categoria' y 'confianza'. "
            "La confianza debe ser un número entero entre 0 y 100, "
            "que represente tu estimación de confianza en la clasificación. "
            "No utilices valores decimales entre 0 y 1. "
            "No incluyas el símbolo % en el valor. "
            "No agregues explicaciones ni campos adicionales."
        ),

        # ----------------------------------------------------
        # 2.2. MENSAJE DE PRUEBA
        # ----------------------------------------------------

        # Solicitud ficticia relacionada con
        # la modificación de una reserva.
        #
        # Permite evaluar si el modelo reconoce
        # correctamente la categoría correspondiente.
        "ejemplo_usuario": (
            "Necesito cambiar la hora de mi reserva para mañana."
        ),

        # ----------------------------------------------------
        # 2.3. CLAVES OBLIGATORIAS
        # ----------------------------------------------------

        # Campos que deben estar presentes
        # en la respuesta JSON interpretada.
        "claves_esperadas": ["categoria", "confianza"],

        # ----------------------------------------------------
        # 2.4. ESQUEMA DE RESPUESTA
        # ----------------------------------------------------

        # Define la estructura solicitada a Gemini.
        "response_schema": {

            # La respuesta debe ser un objeto JSON.
            "type": "OBJECT",

            # Propiedades que componen la respuesta.
            "properties": {

                # Categoría asignada al mensaje.
                "categoria": {

                    # La categoría debe ser una cadena.
                    "type": "STRING",

                    # Solo se admiten estas cuatro opciones.
                    "enum": ["reservas", "ventas", "soporte", "otros"],
                },

                # Estimación de confianza del modelo.
                "confianza": {

                    # Se exige un número entero.
                    "type": "INTEGER",

                    # Límite inferior permitido.
                    "minimum": 0,

                    # Límite superior permitido.
                    "maximum": 100,
                },
            },

            # Ambos campos son obligatorios.
            "required": ["categoria", "confianza"],
        },
    },

    # ========================================================
    # 3. CASO 2: EXTRACCIÓN DE INFORMACIÓN
    # ========================================================

    {
        # Identificador del caso de extracción.
        "nombre": "extraer_datos_cliente",

        # ----------------------------------------------------
        # 3.1. INSTRUCCIONES DEL MODELO
        # ----------------------------------------------------

        # Define el rol de Gemini como extractor
        # de información desde mensajes de usuarios.
        #
        # Solicita identificar:
        # - Nombre del cliente.
        # - Servicio solicitado.
        # - Fecha mencionada.
        #
        # La fecha debe conservarse tal como aparece.
        #
        # Los datos ausentes deben representarse
        # mediante cadenas vacías.
        #
        # La instrucción prohíbe inventar información.
        "system_instruction": (
            "Eres un asistente de extracción de información para VyOps. "
            "Identifica el nombre del cliente, el servicio solicitado "
            "y la fecha mencionada en el mensaje. "
            "Devuelve exclusivamente un objeto JSON con las claves "
            "'nombre', 'servicio' y 'fecha'. "
            "Conserva la fecha tal como aparece en el mensaje. "
            "Si falta algún dato, utiliza una cadena vacía. "
            "No inventes información ni agregues campos adicionales."
        ),

        # ----------------------------------------------------
        # 3.2. MENSAJE DE PRUEBA
        # ----------------------------------------------------

        # Mensaje ficticio que contiene
        # los tres elementos solicitados:
        #
        # - Nombre: Camila.
        # - Servicio: evaluación de kinesiología.
        # - Fecha mencionada: viernes.
        #
        # La fecha no incluye un día calendario concreto.
        "ejemplo_usuario": (
            "Soy Camila, necesito una evaluación de kinesiología "
            "para el viernes."
        ),

        # ----------------------------------------------------
        # 3.3. CLAVES OBLIGATORIAS
        # ----------------------------------------------------

        # La respuesta debe incluir los tres campos,
        # incluso cuando alguno no pueda extraerse.
        "claves_esperadas": ["nombre", "servicio", "fecha"],

        # ----------------------------------------------------
        # 3.4. ESQUEMA DE RESPUESTA
        # ----------------------------------------------------

        "response_schema": {

            # La respuesta debe ser un objeto JSON.
            "type": "OBJECT",

            # Define los campos y sus tipos.
            "properties": {

                # Nombre identificado en el mensaje.
                "nombre": {"type": "STRING"},

                # Servicio solicitado por el usuario.
                "servicio": {"type": "STRING"},

                # Expresión temporal presente en el mensaje.
                "fecha": {"type": "STRING"},
            },

            # Los tres campos deben estar presentes.
            "required": ["nombre", "servicio", "fecha"],
        },
    },

    # ========================================================
    # 4. CASO 3: PRIORIZACIÓN DE SOLICITUDES
    # ========================================================

    {
        # Identificador del caso de priorización.
        "nombre": "priorizar_solicitud",

        # ----------------------------------------------------
        # 4.1. INSTRUCCIONES DEL MODELO
        # ----------------------------------------------------

        # Define el rol de Gemini como evaluador
        # de urgencia de solicitudes empresariales.
        #
        # Establece tres niveles:
        #
        # alta:
        #     Incidentes que impiden operar.
        #
        # media:
        #     Problemas que permiten seguir trabajando.
        #
        # baja:
        #     Consultas sin urgencia.
        #
        # También solicita una justificación breve
        # basada en el mensaje original.
        "system_instruction": (
            "Eres un asistente de priorización de solicitudes para VyOps. "
            "Analiza la urgencia del mensaje y asigna una prioridad: "
            "alta, media o baja. "
            "Utiliza prioridad alta para incidentes que impiden operar, "
            "media para problemas que permiten seguir trabajando "
            "y baja para consultas sin urgencia. "
            "Devuelve exclusivamente un objeto JSON con las claves "
            "'prioridad' y 'motivo'. "
            "El motivo debe ser breve y estar basado en el mensaje. "
            "No agregues campos adicionales."
        ),

        # ----------------------------------------------------
        # 4.2. MENSAJE DE PRUEBA
        # ----------------------------------------------------

        # Describe una interrupción del sistema de ventas
        # que impide atender clientes.
        #
        # Según las reglas del prompt,
        # corresponde a un incidente de prioridad alta.
        "ejemplo_usuario": (
            "El sistema de ventas dejó de funcionar "
            "y no podemos atender clientes."
        ),

        # ----------------------------------------------------
        # 4.3. CLAVES OBLIGATORIAS
        # ----------------------------------------------------

        # La respuesta debe indicar la prioridad
        # y proporcionar una justificación.
        "claves_esperadas": ["prioridad", "motivo"],

        # ----------------------------------------------------
        # 4.4. ESQUEMA DE RESPUESTA
        # ----------------------------------------------------

        "response_schema": {

            # La respuesta debe ser un objeto JSON.
            "type": "OBJECT",

            # Define las propiedades esperadas.
            "properties": {

                # Nivel de urgencia asignado.
                "prioridad": {

                    # La prioridad debe ser una cadena.
                    "type": "STRING",

                    # Valores permitidos.
                    "enum": ["alta", "media", "baja"],
                },

                # Justificación textual de la prioridad.
                "motivo": {

                    # El motivo debe ser una cadena.
                    "type": "STRING",
                },
            },

            # Ambos campos son obligatorios.
            "required": ["prioridad", "motivo"],
        },
    },
]
