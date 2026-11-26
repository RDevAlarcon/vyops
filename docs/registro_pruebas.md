# Registro de pruebas de la API

Fecha: 2026-11-26

Servicio probado: http://127.0.0.1:8000

Cliente HTTP: httpx2

Modo declarado: SIMULADO

Alcance: contrato HTTP con lógica documental controlada.

Resultado: 14 de 14 casos cumplidos.

| Caso | Descripción | Petición | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- | --- | --- |
| V-01 | Consulta documental válida (CA-01 y CA-02) | POST /consultas {"pregunta": "¿Cuál es el horario de ate... | 200 | 200 | PASA |
| V-02 | Abstención segura sin evidencia (CA-03) | POST /consultas {"pregunta": "¿Cuál es el presupuesto mu... | 200 | 200 | PASA |
| V-03 | Disponibilidad del servicio | GET /salud | 200 | 200 | PASA |
| V-04 | Consulta válida con espacios exteriores | POST /consultas {"pregunta": "   ¿Cuál es el horario de ... | 200 | 200 | PASA |
| I-01 | Campo obligatorio ausente | POST /consultas {} | 422 | 422 | PASA |
| I-02 | Pregunta vacía | POST /consultas {"pregunta": ""} | 422 | 422 | PASA |
| I-03 | Pregunta con solo espacios | POST /consultas {"pregunta": "     "} | 422 | 422 | PASA |
| I-04 | Pregunta inferior a la longitud mínima | POST /consultas {"pregunta": "ab"} | 422 | 422 | PASA |
| I-05 | Pregunta superior a la longitud máxima | POST /consultas {"pregunta": "aaaaaaaaaaaaaaaaaaaaaaaaaa... | 422 | 422 | PASA |
| I-06 | Pregunta de tipo numérico | POST /consultas {"pregunta": 123} | 422 | 422 | PASA |
| I-07 | Cuerpo JSON malformado | POST /consultas {"pregunta": | 422 | 422 | PASA |
| I-08 | Ruta inexistente | GET /inexistente | 404 | 404 | PASA |
| I-09 | Método HTTP incorrecto | GET /consultas | 405 | 405 | PASA |
| I-10 | Pregunta con valor nulo | POST /consultas {"pregunta": null} | 422 | 422 | PASA |

## Resultado final

PASS

El registro no certifica la precisión ni el rendimiento del RAG real.
