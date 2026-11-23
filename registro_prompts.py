
"""Gestiona el versionamiento y la trazabilidad de prompts de VyOps.

Este módulo permite recuperar, identificar y comparar versiones
históricas de los prompts utilizados por el asistente RAG municipal.

Sus responsabilidades principales son:
    - Mantener un catálogo de versiones conocidas.
    - Recuperar el código histórico desde commits de Git.
    - Localizar el prompt mediante el árbol sintáctico de Python.
    - Calcular huellas SHA-256 del texto recuperado.
    - Construir registros de versiones con metadatos.
    - Evitar versiones duplicadas en un registro local.
    - Comparar cambios entre prompts mediante difflib.

El versionamiento permite documentar la evolución de las
instrucciones del asistente y facilitar auditorías sobre
los cambios realizados en el comportamiento esperado.

Las versiones históricas se consultan directamente desde
el repositorio Git local.

Este módulo no realiza llamadas a Gemini, no modifica
ChromaDB y no altera los commits históricos.
"""

import ast
import hashlib
import subprocess
from datetime import datetime, timezone
import difflib


# ============================================================
# 1. CATÁLOGO DE VERSIONES HISTÓRICAS
# ============================================================

# Relaciona cada versión lógica del prompt con el commit
# de Git que contiene su implementación histórica.
#
# Las notas describen el cambio principal introducido
# en cada versión, sin modificar el contenido almacenado
# en los commits originales.
VERSIONES = {
    "v1": {
        "commit": "7c3c204",
        "nota": "Prompt municipal original con citas.",
    },
    "v2": {
        "commit": "04706ff",
        "nota": "Incorpora protección contra inyección de prompt.",
    },
}


# ============================================================
# 2. RECUPERACIÓN DE PROMPTS HISTÓRICOS
# ============================================================

def obtener_prompt_historico(commit):
    """Recupera la expresión del prompt desde un commit de Git.

    Consulta el contenido histórico de recuperacion.py
    utilizando git show y analiza su estructura sintáctica
    mediante el módulo ast de Python.

    Busca la función construir_prompt y devuelve el segmento
    de código correspondiente a la primera expresión
    de tipo JoinedStr encontrada dentro de ella.

    Args:
        commit (str): Identificador del commit de Git
            desde el cual se recuperará el archivo.

    Returns:
        str: Segmento de código fuente correspondiente
            a la expresión de cadena interpolada encontrada.

    Raises:
        subprocess.CalledProcessError:
            Si Git no puede recuperar el archivo solicitado.
        SyntaxError:
            Si el contenido recuperado no puede analizarse
            como código Python válido.
        ValueError:
            Si no se encuentra una expresión JoinedStr
            dentro de la función construir_prompt.

    Notes:
        La recuperación requiere acceso al repositorio
        Git que contiene los commits especificados.

        El método no ejecuta el código histórico:
        únicamente lo recupera y analiza sintácticamente.

        Se devuelve el código fuente de la expresión
        interpolada, no el resultado de evaluarla.
    """

    # Recupera el contenido exacto del archivo histórico
    # desde el commit indicado, sin modificar el repositorio.
    contenido = subprocess.check_output(
        ["git", "show", f"{commit}:recuperacion.py"]
    ).decode("utf-8")

    # Construye el árbol sintáctico del código recuperado.
    arbol = ast.parse(contenido)

    # Busca la función que construye el prompt municipal.
    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "construir_prompt":

            # Recorre sus nodos internos para localizar
            # una expresión de cadena interpolada.
            for instruccion in ast.walk(nodo):
                if isinstance(instruccion, ast.JoinedStr):
                    return ast.get_source_segment(contenido, instruccion)

    # Señala que no se encontró el formato de prompt esperado.
    raise ValueError("No se encontró el prompt histórico.")


# ============================================================
# 3. IDENTIFICACIÓN CRIPTOGRÁFICA
# ============================================================

def calcular_huella(texto):
    """Calcula la huella SHA-256 de un texto.

    Convierte el texto a UTF-8 y genera un resumen
    criptográfico utilizando el algoritmo SHA-256.

    Args:
        texto (str): Contenido cuya huella se calculará.

    Returns:
        str: Representación hexadecimal de 64 caracteres
            correspondiente al resumen SHA-256.

    Notes:
        El mismo texto produce siempre la misma huella.

        Cualquier modificación en los bytes del texto
        puede producir una huella diferente.

        La función no almacena ni modifica el contenido.
    """

    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ============================================================
# 4. CONSTRUCCIÓN DE REGISTROS DE VERSIONES
# ============================================================

def registrar_version(version, autor="Ricardo Alarcón"):
    """Construye un registro descriptivo de una versión del prompt.

    Obtiene la información del catálogo VERSIONES,
    recupera el prompt desde Git y calcula su huella SHA-256.

    Args:
        version (str): Identificador de versión registrado
            en el catálogo VERSIONES.
        autor (str): Nombre asociado al registro.
            Por defecto, Ricardo Alarcón.

    Returns:
        dict: Registro con los siguientes campos:
            - version: Identificador lógico.
            - commit: Referencia al commit histórico.
            - autor: Responsable indicado.
            - fecha_registro: Fecha UTC de creación.
            - nota_cambio: Descripción de la versión.
            - sha256: Huella del prompt recuperado.
            - prompt: Código fuente del prompt.
            - modelo: Identificador del modelo registrado.
            - parametros: Temperatura y máximo de tokens.

    Raises:
        KeyError:
            Si la versión solicitada no existe en VERSIONES.

        También pueden propagarse errores producidos
        durante la recuperación del prompt histórico.

    Notes:
        La fecha corresponde al momento en que se
        construye el registro, no a la fecha del commit.

        Los parámetros con valor None representan
        valores no especificados en este registro.

        La función devuelve un diccionario en memoria.
        No escribe archivos ni modifica Git.
    """

    # Obtiene la referencia histórica y su descripción.
    datos = VERSIONES[version]

    # Recupera el código del prompt correspondiente
    # a la versión solicitada.
    prompt = obtener_prompt_historico(datos["commit"])

    # Construye el registro con información de procedencia,
    # integridad, modelo y parámetros declarados.
    return {
        "version": version,
        "commit": datos["commit"],
        "autor": autor,
        "fecha_registro": datetime.now(timezone.utc).isoformat(),
        "nota_cambio": datos["nota"],
        "sha256": calcular_huella(prompt),
        "prompt": prompt,
        "modelo": "gemini-3.5-flash-lite",
        "parametros": {
            "temperatura": None,
            "max_tokens": None,
        },
    }


# ============================================================
# 5. ADMINISTRACIÓN DE VERSIONES EN MEMORIA
# ============================================================

class RegistroDePrompts:
    """Administra una colección de versiones registradas.

    Permite incorporar registros de prompts, impedir
    identificadores de versión duplicados y consultar
    el último registro agregado.

    Attributes:
        versiones (list): Colección de registros almacenados
            durante la vida de la instancia.

    Notes:
        Los registros se mantienen exclusivamente en memoria.

        La clase no consulta Git directamente y no realiza
        persistencia en archivos o bases de datos.

        El orden de los registros corresponde al orden
        en que fueron agregados.
    """

    def __init__(self):
        """Inicializa una colección vacía de versiones."""

        self.versiones = []

    def agregar(self, registro):
        """Agrega una versión si su identificador no está registrado.

        Args:
            registro (dict): Diccionario que contiene,
                entre otros campos, la clave version.

        Returns:
            None: Incorpora el registro a la colección.

        Raises:
            ValueError:
                Si ya existe un registro con el mismo
                identificador de versión.

        Notes:
            La comprobación de duplicados utiliza
            exclusivamente el campo version.

            No compara las huellas SHA-256 ni los commits
            para determinar si dos registros son duplicados.
        """

        # Comprueba que el identificador lógico no exista
        # entre los registros previamente incorporados.
        if any(
            version["version"] == registro["version"]
            for version in self.versiones
        ):
            raise ValueError("La versión ya está registrada.")

        self.versiones.append(registro)

    def ultima(self):
        """Obtiene la última versión agregada al registro.

        Returns:
            dict: Último registro incorporado a la colección.

        Raises:
            ValueError:
                Si todavía no existen versiones registradas.

        Notes:
            La última versión corresponde al orden
            de inserción, no necesariamente a la fecha
            del commit o a la fecha del registro.
        """

        if not self.versiones:
            raise ValueError("No existen versiones registradas.")

        return self.versiones[-1]


# ============================================================
# 6. DEMOSTRACIÓN LOCAL
# ============================================================

if __name__ == "__main__":
    # Recupera las versiones históricas definidas en VERSIONES
    # y muestra sus metadatos principales en consola.
    #
    # La demostración necesita que Git pueda acceder
    # a los commits históricos configurados.

    for version in VERSIONES:
        registro = registrar_version(version)

        print(f"\nVersión: {registro['version']}")
        print(f"Commit: {registro['commit']}")
        print(f"Autor: {registro['autor']}")
        print(f"SHA-256: {registro['sha256']}")
        print(f"Cambio: {registro['nota_cambio']}")
        print(f"Modelo: {registro['modelo']}")
        print(f"Parámetros: {registro['parametros']}")

    # ========================================================
    # COMPARACIÓN DE CAMBIOS ENTRE VERSIONES
    # ========================================================

    print("\n=== DIFERENCIAS ENTRE V1 Y V2 ===")

    # Recupera nuevamente el contenido de ambas versiones
    # para construir una comparación línea por línea.
    prompt_v1 = obtener_prompt_historico("7c3c204")
    prompt_v2 = obtener_prompt_historico("04706ff")

    # Genera un diff unificado que identifica las líneas
    # eliminadas, agregadas y conservadas entre versiones.
    diferencias = difflib.unified_diff(
        prompt_v1.splitlines(),
        prompt_v2.splitlines(),
        fromfile="v1_prompt_original",
        tofile="v2_prompt_protegido",
        lineterm="",
    )

    # Presenta las diferencias sin modificar los prompts.
    for linea in diferencias:
        print(linea)

    # ========================================================
    # REGISTRO Y CONSULTA DE VERSIONES
    # ========================================================

    # Crea un registro local de versiones y agrega
    # las dos versiones históricas configuradas.
    registro_prompts = RegistroDePrompts()
    registro_prompts.agregar(registrar_version("v1"))
    registro_prompts.agregar(registrar_version("v2"))

    # Obtiene el último registro incorporado.
    ultima_version = registro_prompts.ultima()

    # Muestra sus datos principales.
    print("\n=== ÚLTIMA VERSIÓN REGISTRADA ===")
    print("Versión:", ultima_version["version"])
    print("SHA-256:", ultima_version["sha256"][:12])
    print("Cambio:", ultima_version["nota_cambio"])
