# RAG Setup Guide

This guide explains how to configure RAG (Retrieval Augmented Generation) for the Academic Research Agent to search through your custom documents.

## Prerequisites

- Google Cloud Project with billing enabled
- Vertex AI API enabled
- Discovery Engine API enabled
- Cloud Storage bucket created

## Setup Steps

### 1. Enable Required APIs

```bash
gcloud services enable discoveryengine.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 2. Prepare Your Documents

Place your documents (PDF, TXT, HTML, or JSON files) in a local directory:

```bash
mkdir -p documents/
# Add your PDF, TXT, or HTML files to this directory
```

### 3. Upload Documents to Cloud Storage

```bash
python rag/index_documents.py --source_dir=./documents
```

This uploads your documents to the Cloud Storage bucket specified in your `.env` file.

### 4. Create Vertex AI Search Datastore

```bash
python rag/setup_rag.py \
  --action=create \
  --datastore_id=academic-docs \
  --datastore_name="Academic Research Documents"
```

Copy the datastore ID to your `.env` file:

```bash
RAG_SEARCH_DATASTORE_ID=academic-docs
```

### 5. Import Documents into the Datastore

```bash
python rag/setup_rag.py \
  --action=import \
  --datastore_id=academic-docs \
  --gcs_uri="gs://YOUR_BUCKET/rag-documents/*"
```

Replace `YOUR_BUCKET` with your actual bucket name from `.env`.

### 6. Test RAG Search

Start the agent and test the RAG functionality:

```bash
adk run academic_research
```

Example queries:
- "Search for information about transformers"
- "Find documents related to machine learning"

## Managing Datastores

### List all datastores

```bash
python rag/setup_rag.py --action=list
```

### Delete a datastore

```bash
python rag/setup_rag.py \
  --action=delete \
  --datastore_id=academic-docs
```

## Document Format Guidelines

### Supported Formats

- PDF: Research papers, articles
- TXT: Plain text documents
- HTML: Web pages, documentation
- JSON/JSONL: Structured data with metadata

### JSON Document Format

For better search results, structure your JSON documents as:

```json
{
  "id": "doc-001",
  "title": "Document Title",
  "content": "Full text content here...",
  "metadata": {
    "author": "Author Name",
    "date": "2024-01-01",
    "category": "research"
  }
}
```

## Troubleshooting

### Documents not appearing in search results

- Wait 5-10 minutes after import for indexing to complete
- Verify documents were uploaded to Cloud Storage
- Check datastore status in Cloud Console

### Permission errors

Ensure your service account has these roles:
- Discovery Engine Admin
- Storage Object Viewer

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/discoveryengine.admin"
```

### Empty search results

- Verify RAG_SEARCH_DATASTORE_ID is set correctly in `.env`
- Check that documents contain searchable text
- Try broader search queries

## Cost Considerations

Vertex AI Search pricing:
- Document storage: Based on document count
- Search queries: Per query pricing
- See: https://cloud.google.com/generative-ai-app-builder/pricing

## Advanced Configuration

### Custom Embedding Models

To use custom embeddings instead of Vertex AI Search, implement vector similarity search in `academic_research/tools/rag_search.py`.

### Chunking Strategy

For large documents, consider pre-processing:
- Split documents into smaller chunks (500-1000 tokens)
- Create separate JSON documents for each chunk
- Include source document reference in metadata
