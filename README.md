# VyOps — Agente de IA para Gestión Operativa

**Proyecto académico | Especialización en Desarrollo con IA Generativa — Accenture / SkillNest**

## 1. Descripción del proyecto

VyOps es un proyecto de agente de inteligencia artificial orientado a apoyar la gestión operativa de pequeñas y medianas empresas.

Su objetivo es permitir que los usuarios consulten información empresarial, obtengan respuestas contextualizadas y, progresivamente, puedan ejecutar tareas mediante herramientas e integraciones con APIs.

El proyecto se desarrollará de manera incremental durante el programa, aplicando conceptos de integración de modelos de lenguaje, desarrollo backend, recuperación de información (RAG), orquestación y despliegue reproducible.

## 2. Objetivo

Construir una solución capaz de:

- Interpretar solicitudes de usuarios mediante lenguaje natural.
- Consumir modelos de inteligencia artificial mediante APIs.
- Integrar información de diferentes fuentes empresariales.
- Recuperar información relevante mediante técnicas RAG.
- Utilizar herramientas externas para resolver solicitudes operativas.
- Incorporar mecanismos de validación, manejo de errores y observabilidad.

Estas capacidades representan el alcance previsto del proyecto y se implementarán progresivamente durante el curso.

## 3. Tecnologías

| Tecnología | Propósito |
|---|---|
| Python 3.13 | Lenguaje principal |
| Google Gemini API | Proveedor de modelos de IA |
| google-genai | SDK oficial de Gemini |
| requests | Cliente HTTP |
| python-dotenv | Gestión de variables de entorno |
| Git y GitHub | Control de versiones |
| Postman | Pruebas de APIs |
| venv | Aislamiento de dependencias |

Otras tecnologías se incorporarán conforme a los requerimientos de las siguientes unidades.

## 4. Estructura del repositorio

```text
vyops/
├── src/                  # Código fuente
├── docs/                 # Documentación y evidencias
│   └── evidencia_peticion_autenticada.png
├── tests/                # Pruebas automatizadas
├── .env.example          # Plantilla de configuración
├── .gitignore            # Archivos excluidos de Git
├── README.md             # Documentación del proyecto
└── requirements.txt      # Dependencias Python
```

El entorno virtual `.venv/` y el archivo privado `.env` se mantienen exclusivamente en el entorno local.

## 5. Configuración del entorno

### Crear y activar el entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Instalar las dependencias

```powershell
python -m pip install -r requirements.txt
```

### Configurar las variables de entorno

Crear un archivo `.env` a partir de `.env.example` y configurar:

```dotenv
GEMINI_API_KEY=tu_clave_aqui
```

La credencial debe obtenerse desde Google AI Studio y nunca debe incluirse en archivos versionados.

## 6. Avance del proyecto

### Unidad U1.2 — Configuración técnica inicial

**Estado: Completada**

Actividades realizadas:

- Inicialización del repositorio Git.
- Configuración de la rama principal `main`.
- Creación y activación del entorno virtual Python.
- Instalación y registro de dependencias.
- Configuración de variables de entorno.
- Protección de credenciales mediante `.gitignore`.
- Creación del repositorio remoto en GitHub.
- Configuración de una colección de Postman.
- Primera petición HTTP autenticada a Google Gemini.
- Registro de evidencia de respuesta exitosa.

### Primera petición autenticada

| Campo | Resultado |
|---|---|
| Fecha | 09-10-2026 |
| Método | POST |
| Proveedor | Google Gemini |
| Modelo | gemini-2.5-flash |
| Endpoint | `/v1beta/models/gemini-2.5-flash:generateContent` |
| Estado HTTP | 200 OK |
| Resultado | Respuesta generada correctamente |

**Evidencia:** [Primera petición autenticada](docs/evidencia_peticion_autenticada.png)

Esta validación se realizó mediante Postman. El consumo programático desde Python se implementará en la siguiente unidad.

## 7. Próximas etapas

- **Unidad U1.3:** desarrollar el primer módulo Python para consumir Gemini, procesar respuestas y manejar errores.
- **Gate 1:** construir una miniaplicación funcional de consumo de modelos mediante API.
- **Gate 2:** incorporar integración de herramientas, recuperación de información y orquestación.
- **Gate 3 / Capstone:** consolidar la aplicación, las pruebas, la documentación y el despliegue reproducible.

El alcance definitivo de cada etapa se ajustará a las instrucciones y criterios de evaluación del programa.

## 8. Seguridad y buenas prácticas

Durante todo el desarrollo se mantendrán las siguientes reglas:

- No publicar claves API, contraseñas ni tokens.
- Mantener las credenciales reales fuera del control de versiones.
- Utilizar entornos virtuales independientes por proyecto.
- Registrar las dependencias necesarias para reproducir el entorno.
- Documentar los avances mediante commits descriptivos.
- Mantener el trabajo evaluable en GitHub.
- Incorporar pruebas y controles de seguridad conforme avance el proyecto.

## 9. Contexto académico

VyOps se desarrolla como proyecto práctico de la **Especialización en Desarrollo con IA Generativa — Accenture / SkillNest**.

El repositorio evolucionará durante el programa, reutilizando y ampliando los componentes implementados en cada unidad y Gate.