# VyOps — Agente de IA para Gestión Operativa

**Proyecto académico | Especialización en Desarrollo con IA Generativa — Accenture / SkillNest**

## 1. Descripción del proyecto

VyOps es un proyecto de agente de inteligencia artificial orientado a apoyar la gestión operativa de organizaciones y pequeñas y medianas empresas.

Su objetivo es permitir que los usuarios consulten información, obtengan respuestas contextualizadas y, progresivamente, puedan ejecutar tareas mediante herramientas e integraciones con APIs.

La arquitectura prevista es modular y multiempresa (*multi-tenant*), con separación de información por organización.

El proyecto se desarrolla de manera incremental durante el programa SkillNest.

## 2. Objetivo

Construir una solución capaz de:

- Interpretar solicitudes mediante lenguaje natural.
- Consumir modelos de inteligencia artificial mediante APIs.
- Procesar respuestas estructuradas.
- Validar datos y manejar errores.
- Evaluar modelos y prompts.
- Integrar fuentes documentales mediante RAG en etapas posteriores.
- Incorporar herramientas, controles de acceso y observabilidad progresivamente.

Las funcionalidades futuras se implementarán durante las siguientes unidades.

## 3. Estado actual — Unidad 1 / Gate 1

La primera unidad incluye:

- Entorno virtual Python y dependencias reproducibles.
- Configuración segura de credenciales.
- Consumo funcional de Google Gemini mediante API REST.
- Procesamiento de respuestas y métricas de tokens.
- Manejo de errores HTTP y reintentos ante fallos transitorios.
- Evaluación comparativa de modelos.
- Banco de tres prompts con instrucciones de sistema.
- Validación de respuestas JSON estructuradas.
- Evaluación de consistencia con nueve ejecuciones.
- Documentación técnica y control de versiones.

**Modelo seleccionado para las pruebas actuales:** `gemini-3.5-flash-lite`.

## 4. Tecnologías

| Tecnología | Propósito |
|---|---|
| Python 3.13 | Lenguaje principal |
| Google Gemini API | Proveedor de inteligencia artificial |
| requests | Cliente HTTP |
| python-dotenv | Variables de entorno |
| google-genai | SDK de Gemini disponible en el entorno |
| tzdata | Soporte de zonas horarias |
| Git y GitHub | Control de versiones |
| Postman | Pruebas de API |
| venv | Aislamiento de dependencias |

## 5. Estructura del repositorio

```text
vyops/
├── src/
│   ├── consumir_gemini.py
│   └── comparar_modelos.py
├── prompts/
│   ├── banco.py
│   ├── test_consistencia.py
│   ├── registro_resultados.json
│   ├── registro_resultados_anterior.json
│   └── registro_resultados_con_errores.json
├── resultados/
├── docs/
│   ├── evaluacion_modelos.md
│   ├── evaluacion_prompts.md
│   └── decision-arquitectura.md
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

Los archivos `.env` y `.venv/` son locales y no se incluyen en Git.

## 6. Instalación desde cero — Windows PowerShell

### 6.1. Requisitos previos

- Python 3.13 instalado.
- Git instalado.
- Conexión a internet.
- Clave API de Gemini obtenida desde Google AI Studio.

### 6.2. Clonar el repositorio

```powershell
git clone https://github.com/RDevAlarcon/vyops.git
cd vyops
```

### 6.3. Crear el entorno virtual

```powershell
python -m venv .venv
```

### 6.4. Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6.5. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

Verificar dependencias:

```powershell
python -m pip check
```

### 6.6. Configurar credenciales

Copiar la plantilla:

```powershell
Copy-Item .env.example .env
```

Abrir `.env` y reemplazar el valor de ejemplo por la clave API real:

```dotenv
GEMINI_API_KEY=tu_clave_real
```

Nunca publicar la clave ni incluir `.env` en Git.

## 7. Ejecución de la aplicación

Desde la raíz del proyecto, con el entorno virtual activado y `.env` configurado:

```powershell
python src/main.py
```

También es posible ejecutar directamente el módulo de consumo de Gemini:

```powershell
python src/consumir_gemini.py
```

### 7.1. Pruebas funcionales

El archivo `src/main.py` ejecuta tres pruebas.

**Prueba 1 — Consulta a Gemini**

Realiza una petición al modelo y muestra:

- Respuesta generada.
- Tokens utilizados.
- Tiempo de respuesta.
- Costo estimado de la consulta.

**Prueba 2 — Instrucción de sistema**

Envía una consulta utilizando `system_instruction` para configurar el comportamiento de Gemini como asistente de orientación municipal.

**Prueba 3 — Validación de entrada**

Envía una entrada inválida y comprueba que el sistema la rechace mediante una excepción `ValueError` controlada.

### 7.2. Resultado de verificación

El 22 de octubre de 2026 se ejecutó `src/main.py` correctamente.

| Prueba | Resultado |
|---|---|
| Consulta a Gemini | Correcta |
| Instrucción de sistema | Correcta |
| Validación de entrada | Correcta |

Las dos primeras pruebas requieren conexión a internet y disponibilidad de la API de Gemini. Consumen cuota del proveedor y pueden generar costos.

### 7.3. Otros componentes

Los módulos de evaluación comparativa de modelos y consistencia de prompts se mantienen independientes del punto de entrada principal.

Sus procedimientos de ejecución se describen en las siguientes secciones.

## 8. Evaluación de modelos

Se implementó una comparación de modelos de Gemini considerando:

- Respuestas correctas.
- Tiempo de respuesta.
- Consumo de tokens.
- Costo estimado.
- Errores de API.

Script:

```powershell
python src/comparar_modelos.py
```

Documentación:

- `docs/evaluacion_modelos.md`
- `docs/decision-arquitectura.md`

Los resultados históricos se conservan en `resultados/`.

## 9. Banco de prompts y validación JSON

El banco contiene tres prompts:

1. `clasificar_solicitud`
2. `extraer_datos_cliente`
3. `priorizar_solicitud`

Cada prompt define instrucciones de sistema, entrada de ejemplo, esquema JSON y claves obligatorias.

La evaluación se ejecuta mediante:

```powershell
python prompts/test_consistencia.py
```

Este comando realiza nueve consultas reales a Gemini y actualiza `prompts/registro_resultados.json`. Por lo tanto, consume cuota de API y puede generar costos.

**Resultado registrado el 20 de octubre de 2026:** 9 de 9 pruebas exitosas, con un 100 % de cumplimiento estructural para los ejemplos evaluados.

La evidencia histórica y el análisis se encuentran en:

- `prompts/registro_resultados.json`
- `prompts/registro_resultados_anterior.json`
- `prompts/registro_resultados_con_errores.json`
- `docs/evaluacion_prompts.md`

## 10. Seguridad y buenas prácticas

- Las credenciales se cargan desde `.env`.
- `.env` está excluido mediante `.gitignore`.
- `.env.example` contiene únicamente valores de ejemplo.
- Las dependencias se registran en `requirements.txt`.
- Las peticiones HTTP incorporan manejo de errores.
- Los errores transitorios pueden activar reintentos controlados.
- Las respuestas JSON se validan antes de procesarlas.
- El historial de cambios se mantiene en GitHub.

## 11. Evidencia técnica de la Unidad 1

### Primera petición autenticada

El 9 de octubre de 2026 se realizó una petición HTTP autenticada a Gemini mediante Postman.

- Modelo utilizado inicialmente: `gemini-2.5-flash`.
- Resultado HTTP: `200 OK`.
- Evidencia: [Primera petición autenticada](docs/evidencia_petición_autenticada.png).

Posteriormente se implementó el cliente Python y se evaluaron otros modelos para seleccionar una alternativa apropiada para VyOps.

### Arquitectura

El diseño técnico y su evolución se documentan en `docs/`, incluyendo el diagrama de arquitectura y las decisiones de selección del modelo.
El diagrama de arquitectura de la Unidad 1 está disponible en:
[Diagrama de arquitectura de VyOps](docs/Diagrama_arquitectura.png).

### Prueba funcional del cliente Python

El 20 de octubre de 2026 se comprobó la ejecución de `src/consumir_gemini.py`:

- Respuesta generada correctamente.
- 45 tokens totales.
- Tiempo de respuesta: 10,606 segundos.
- Costo estimado: USD 0,00008390.

## 12. Próximas etapas

Tras completar la evaluación del Gate 1, el proyecto continuará incorporando nuevas capacidades según los requisitos del programa.

Entre las funcionalidades previstas se encuentran la recuperación documental mediante RAG, la integración de herramientas y el desarrollo de componentes de backend.

Estas funcionalidades no forman parte de la implementación actual de la Unidad 1.

## 13. Contexto académico

VyOps se desarrolla como proyecto práctico de la **Especialización en Desarrollo con IA Generativa — Accenture / SkillNest**.

El repositorio evoluciona progresivamente, reutilizando los componentes implementados en cada unidad y Gate.