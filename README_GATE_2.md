# VyOps — Gate 2: Instalación y ejecución

**Proyecto:** Especialización en Desarrollo con IA Generativa — SkillNest
**Repositorio:** [https://github.com/RDevAlarcon/vyops](https://github.com/RDevAlarcon/vyops)
**Entorno:** Windows PowerShell — Python 3.13

## 1. Descripción

VyOps implementa un sistema RAG (*Retrieval-Augmented Generation*) que permite realizar consultas sobre documentación municipal ficticia mediante Google Gemini y ChromaDB.

Esta guía explica cómo instalar el proyecto desde cero y ejecutar la demostración correspondiente a Gate 2.

## 2. Requisitos

- Python 3.13 y Git.
- Conexión a internet.
- Clave API de Gemini, disponible en [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## 3. Instalación

Desde Windows PowerShell:

```powershell
git clone https://github.com/RDevAlarcon/vyops.git
cd vyops

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python -m pip check
```

## 4. Configuración

Crear el archivo `.env`:

```powershell
Copy-Item .env.example .env
```

Editar `.env` con los siguientes valores:

```dotenv
GEMINI_API_KEY=tu_clave_real
VYOPS_VECTORSTORE_DIR=vectorstore_profesor
VYOPS_EMBEDDING_PAUSA_SEGUNDOS=10
```

**Importante:** no compartir la clave API ni subir `.env` a GitHub.

## 5. Preparación e indexación documental

El proyecto contiene 30 documentos municipales ficticios.

**Paso 1 — Preparar el corpus:**

```powershell
python indexar_corpus.py
```

Resultado esperado:

- 30 documentos originales.
- 387 fragmentos preparados.
- 387 identificadores únicos.
- 0 duplicados.

Este paso no utiliza la API de Gemini.

**Paso 2 — Construir el índice ChromaDB:**

```powershell
python -m src.indexacion_incremental --directorio vectorstore_profesor
```

La indexación utiliza `models/gemini-embedding-001` y procesa hasta 10 fragmentos por lote, con pausas de 10 segundos entre lotes.

Para 387 fragmentos se realizan 39 lotes y 38 pausas, equivalentes a 380 segundos de espera, más el procesamiento de Gemini.

**Duración referencial:** aproximadamente 10 minutos para una indexación completa.

La operación consume cuota de API. Se permiten hasta tres intentos ante determinados errores transitorios y se conservan los fragmentos ya indexados.

No utilizar `vectorstore/` como destino, ya que corresponde al índice original de desarrollo.

## 6. Ejecutar pruebas automatizadas

```powershell
python -m pytest -q
```

Alternativamente:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Las pruebas con dependencias simuladas no requieren consumir la API de Gemini.

## 7. Ejecutar Gate 2

Con el entorno virtual activo, la clave configurada y el índice generado:

```powershell
python servicio_vyops_rag.py
```

El servicio verifica:

1. Índice vectorial persistido.
2. Recuperación documental y dos consultas reales a Gemini.
3. Generación de respuestas con citas y abstención segura.
4. Trazabilidad independiente y protección frente a prompt injection.
5. Supervisión humana simulada.

**Resultado esperado:**

```text
RESULTADO FINAL: SERVICIO RAG GATE 2 - PASS
```

La ejecución realiza consultas reales a Gemini y puede consumir cuota de API.

## 8. Validación realizada

**Fecha:** 20 de noviembre de 2026.

| Componente                          | Resultado |
| ----------------------------------- | --------- |
| Índice ChromaDB (387 fragmentos)    | PASS      |
| Recuperación y generación con citas | PASS      |
| Abstención segura                   | PASS      |
| Trazabilidad independiente          | PASS      |
| Bloqueo de contexto sospechoso      | PASS      |
| Supervisión humana simulada         | PASS      |

**Consumo observado:** 2.407 tokens y costo estimado de USD 0,00081855.

**Resultado final:** `SERVICIO RAG GATE 2 - PASS`.

## 9. Documentación adicional

Para revisar la arquitectura, las actividades desarrolladas durante el Módulo 2 y las evidencias técnicas, consultar el archivo principal [README.md](README.md).

La demostración corresponde al alcance académico de Gate 2 y no representa un despliegue en producción.
