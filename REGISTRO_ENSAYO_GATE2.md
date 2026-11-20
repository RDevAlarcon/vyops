# Registro del ensayo funcional - Gate 2

Proyecto: VyOps
Fecha: 2026-11-19
Seccion: Verificacion funcional en vivo y validacion final

## Hallazgos
- El ejemplo del curso utiliza d.contenido, pero LangChain Document utiliza page_content.
- Se requiere filtrar el contexto recuperado antes de invocar al LLM.
- Cada consulta necesita un trace_id independiente.

## Adaptaciones realizadas
- Se reutilizo filtrar_documentos_langchain() de inyeccion_prompt.py.
- Se integro ChromaDB con DeterministicFakeEmbedding(size=768) para el ensayo.
- Se incorporo una respuesta segura cuando todos los documentos son descartados.
- Se verifico que el LLM no sea invocado sin contexto confiable.
- Se incorporaron eventos JSON y consumo simulado de tokens.
- Se utilizo try/finally para restablecer el trace_id.

## Resultados del ensayo
- Indexacion y recuperacion: PASS
- Filtrado de documentos: PASS
- Generacion simulada y citas: PASS
- Registro de eventos: PASS
- Contexto comprometido: PASS
- Aislamiento de trazas: PASS
- Pipeline original de VyOps en ensayo: PASS

Resultado: ENSAYO GATE 2 COMPLETO - PASS

## Corpus municipal real
- Documentos originales: 30
- Fragmentos preparados: 387
- Coleccion ChromaDB: vyops_municipal_v1
- Fragmentos persistidos: 387
- IDs unicos persistidos: 387
- Duplicados detectados: 0
- Modelo de embeddings configurado: gemini-embedding-001
- Verificacion de persistencia: PASS

## Evaluacion de recuperacion
Cinco casos evaluados sobre el corpus municipal.

| k | Precision media | Recall medio | F1 medio |
|---|---|---|---|
| 1 | 0.600 | 0.600 | 0.600 |
| 3 | 0.600 | 0.800 | 0.660 |
| 5 | 0.520 | 1.000 | 0.645 |

## Supervision humana y matriz de riesgos
Comando:
python -m pytest tests/test_grafo_supervision.py tests/test_matriz_riesgos.py -v

Resultado: 17 passed in 0.43s

## Pruebas automatizadas completas
Comando:
python -m pytest -q

Resultado: 234 passed, 11 subtests passed in 3.53s
Advertencias reportadas: 0

## Limitaciones
- La generacion y el consumo del ensayo integrado son simulados.
- La validacion automatica de citas comprueba numeracion y estructura, no respaldo semantico completo.
- La comprobacion de persistencia verifica cantidad y unicidad de IDs; no demuestra por si sola la correspondencia exacta de cada fragmento con el corpus.
- La corrida real con Gemini y sus metricas se documentan por separado.
