# Investigación Académica con ADK

> Basado en el sample de [google/adk-samples](https://github.com/google/adk-samples) con mejoras de RAG semántico y procesamiento multimodal.

## Descripción General

Agente impulsado por IA diseñado para facilitar la exploración del panorama académico relacionado con trabajos de investigación seminales. Reconociendo el desafío que enfrentan los investigadores al navegar por el creciente cuerpo de literatura influenciado por estudios fundamentales, este agente ofrece un enfoque simplificado.

El agente acepta un artículo seminal como entrada y:

1. Analiza las contribuciones principales del trabajo especificado
2. Utiliza herramientas especializadas para identificar y recuperar vía Google Search publicaciones académicas recientes que citan este artículo seminal
3. Sintetiza el análisis del artículo original con los hallazgos de literatura reciente y propone posibles direcciones de investigación futuras

Esta capacidad tiene como objetivo proporcionar a los investigadores información valiosa sobre el impacto continuo de investigaciones seminales y destacar vías prometedoras para investigación novedosa, acelerando así el proceso de descubrimiento.

## Características del Agente

| Característica | Descripción |
| --- | --- |
| **Tipo de Interacción** | Conversacional |
| **Complejidad**  | Fácil |
| **Tipo de Agente**  | Multi Agente |
| **Componentes**  | Herramientas: Google Search + RAG |
| **Vertical**  | Educación |

### Arquitectura del Agente

Este diagrama muestra la arquitectura detallada de los agentes y herramientas utilizadas para implementar este flujo de trabajo.

<img src="academic-research.svg" alt="academic researcher" width="800"/>

## Configuración e Instalación

### Prerrequisitos

- Python 3.11+
- pip (gestor de paquetes de Python)
- Proyecto en Google Cloud Platform
- Google Cloud CLI ([instrucciones de instalación](https://cloud.google.com/sdk/docs/install))
- Docker (para deployment en Cloud Run)

### Instalación Rápida

```bash
# Configurar proyecto
make setup

# Instalar dependencias
make install-dev

# Autenticar con Google Cloud
make auth
```

O manualmente:

```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env` y edita con tus valores:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
GOOGLE_CLOUD_REGION=us-east4
GOOGLE_CLOUD_LOCATION=us-east4
GOOGLE_CLOUD_STORAGE_BUCKET=tu-bucket

# Vertex AI Configuration
VERTEX_AI_MODEL=gemini-2.5-flash-lite
VERTEX_AI_LOCATION=us-east4

# RAG Configuration
RAG_EMBEDDING_MODEL=text-embedding-004
```

2. Habilita las APIs necesarias:

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

## Uso Local

### Ejecutar el Agente

```bash
# CLI interactivo
make run

# Interfaz web
make web
```

### Ejemplo de Interacción

```
Usuario: ¿Quién eres?

Agente: Soy un Asistente de Investigación con IA.

Mi propósito es ayudarte a explorar el panorama académico relacionado con un artículo
seminal de tu interés. Puedo:

- Analizar un artículo seminal que proporciones (Título/Autores, DOI o URL)
- Encontrar artículos académicos recientes que citen el trabajo seminal
- Sugerir posibles direcciones de investigación futuras

¿Cómo puedo ayudarte hoy?
```

## Sistema RAG con Embeddings

El agente incluye un sistema de RAG (Retrieval Augmented Generation) que indexa automáticamente documentos PDF con embeddings para búsqueda semántica.

### Características del RAG

- **Indexación automática**: Los PDFs subidos se indexan automáticamente con embeddings
- **Procesamiento multimodal**: Extrae texto, imágenes y tablas de los PDFs usando Gemini
- **Búsqueda semántica**: Encuentra información relevante usando similitud coseno
- **Almacenamiento en GCS**: Los embeddings se guardan en `gs://{BUCKET}/rag_documents/`

### Configuración

El sistema RAG se configura automáticamente. Solo necesitas:

1. Configurar el bucket en `.env`:
```bash
GOOGLE_CLOUD_STORAGE_BUCKET=tu-bucket
RAG_EMBEDDING_MODEL=text-embedding-004
```

2. Los documentos se indexan automáticamente cuando el agente los recibe

## Deployment a Cloud Run

### Build y Deploy

```bash
# Build de imagen Docker
make build

# Push a Artifact Registry
make push

# Deploy a Cloud Run
make deploy-cloudrun
```

### Comandos Disponibles

```bash
make help                    # Ver todos los comandos disponibles
make setup-all              # Configuración completa
make dev                    # Iniciar desarrollo rápido
make test                   # Ejecutar tests
make clean                  # Limpiar archivos temporales
```

## Estructura del Proyecto

```
.
├── academic_research/          # Código del agente principal
│   ├── agent.py               # Configuración del agente coordinador
│   ├── prompt.py              # Prompts del sistema
│   ├── tools/                 # Herramientas personalizadas
│   │   ├── document_storage.py  # Sistema de embeddings y storage
│   │   ├── index_document.py    # Tool para indexar documentos
│   │   └── rag_search.py        # Búsqueda semántica
│   └── sub_agents/            # Sub-agentes especializados
│       ├── academic_newresearch/  # Sugerir nuevas direcciones
│       └── academic_websearch/    # Búsqueda de papers citantes
├── .scripts/                  # Scripts de utilidad
│   ├── deployment/           # Scripts de deployment
│   ├── eval/                 # Evaluaciones del agente
│   ├── rag/                  # Configuración RAG avanzada
│   └── tests/                # Tests unitarios
├── .adkignore                # Archivos ignorados por ADK
├── Dockerfile                # Para deployment en Cloud Run
├── Makefile                  # Automatización de tareas
├── requirements.txt          # Dependencias del proyecto
└── README.md                 # Este archivo
```

## Desarrollo

### Ejecutar Tests

```bash
make test
```

### Formatear Código

```bash
make format
```

### Evaluaciones

```bash
make eval
```

## Personalización

El agente puede ser personalizado para adaptarse mejor a tus necesidades:

1. **Integrar Herramientas de Búsqueda Especializadas**: Aumenta las capacidades de descubrimiento del agente incorporando funcionalidades adicionales de búsqueda académica, como una herramienta específica de ArXiv.

2. **Implementar Visualización de Resultados**: Mejora la presentación de hallazgos de investigación agregando módulos para visualizar la red de artículos citados o representar gráficamente temas de investigación sugeridos.

3. **Personalizar Instrucciones del Agente**: Modifica los prompts que guían a los sub-agentes academic_websearch y academic_newresearch en [academic_research/prompt.py](academic_research/prompt.py).

4. **Descargar Artículos vía DOI o URL**: Aumenta las capacidades del agente habilitando descarga directa de artículos seminales dado un DOI o URL.

## Comandos del Makefile

### Setup & Instalación
- `make setup` - Crear archivo .env desde template
- `make install` - Instalar dependencias
- `make install-dev` - Instalar con dependencias de desarrollo
- `make auth` - Autenticar con Google Cloud

### Desarrollo
- `make run` - Ejecutar agente localmente
- `make web` - Iniciar interfaz web de ADK
- `make test` - Ejecutar tests
- `make eval` - Ejecutar evaluaciones
- `make format` - Formatear código

### RAG Setup
- `make rag-create` - Crear datastore de Vertex AI Search
- `make rag-upload DOCS_DIR=/path` - Subir documentos
- `make rag-import` - Importar documentos al datastore
- `make rag-list` - Listar datastores
- `make rag-delete` - Eliminar datastore

### Deployment
- `make build` - Construir imagen Docker
- `make push` - Push a Artifact Registry
- `make deploy-cloudrun` - Deploy a Cloud Run
- `make deploy-agent` - Deploy a Vertex AI Agent Engine
- `make logs` - Ver logs del servicio
- `make clean` - Limpiar archivos temporales

### Flujos Completos
- `make setup-all` - Setup completo
- `make dev` - Desarrollo rápido
- `make deploy-all` - Pipeline completo de deployment

## Solución de Problemas

### Error de autenticación

```bash
make auth
```

### Error de dependencias

```bash
make clean-all
make install-dev
```

### Logs del servicio

```bash
make logs
```

## Licencia

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0

## Recursos

- [Google ADK Documentation](https://ai.google.dev/adk)
- [Google ADK Samples](https://github.com/google/adk-samples)
- [Vertex AI](https://cloud.google.com/vertex-ai)
- [Cloud Run](https://cloud.google.com/run)
- [Text Embeddings](https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings)

## Notas para DevFest

Este proyecto es una demostración para estudiantes. El código está disponible para que lo repliquen en sus propios proyectos GCP. El deployment mostrado en el evento es solo con fines demostrativos.

Para usar este proyecto:
1. Clona el repositorio
2. Configura tu propio proyecto GCP
3. Sigue las instrucciones de instalación
4. Personaliza según tus necesidades
