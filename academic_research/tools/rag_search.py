# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""RAG search tool for retrieving relevant information from indexed documents."""

import os
from typing import Any

from google.adk.tools import tool
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel


@tool
def rag_search_tool(query: str, max_results: int = 5) -> str:
    """
    Search through indexed documents using RAG (Retrieval Augmented Generation).

    This tool searches through a collection of documents that have been previously
    indexed and returns the most relevant passages based on the query.

    Args:
        query: The search query or question to find relevant information for.
        max_results: Maximum number of relevant passages to return (default: 5).

    Returns:
        A string containing the most relevant passages found in the documents,
        formatted with source information.
    """
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        if not project_id:
            return "Error: GOOGLE_CLOUD_PROJECT environment variable not set."

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Use Vertex AI Search if configured
        search_datastore_id = os.getenv("RAG_SEARCH_DATASTORE_ID")

        if search_datastore_id:
            return _search_with_vertex_ai_search(
                query, project_id, location, search_datastore_id, max_results
            )
        else:
            # Fallback to vector search with embeddings
            return _search_with_embeddings(query, project_id, location, max_results)

    except Exception as e:
        return f"Error performing RAG search: {str(e)}"


def _search_with_vertex_ai_search(
    query: str,
    project_id: str,
    location: str,
    datastore_id: str,
    max_results: int
) -> str:
    """
    Perform search using Vertex AI Search (formerly Enterprise Search).

    Args:
        query: Search query
        project_id: GCP project ID
        location: GCP location
        datastore_id: Vertex AI Search datastore ID
        max_results: Maximum number of results

    Returns:
        Formatted search results
    """
    from google.cloud import discoveryengine_v1 as discoveryengine

    client = discoveryengine.SearchServiceClient()

    # Configure the search request
    serving_config = (
        f"projects/{project_id}/locations/{location}"
        f"/collections/default_collection/dataStores/{datastore_id}"
        f"/servingConfigs/default_config"
    )

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=max_results,
    )

    # Execute search
    response = client.search(request)

    # Format results
    results = []
    for result in response.results:
        document = result.document

        # Extract relevant fields from the document
        title = document.derived_struct_data.get("title", "Untitled")
        snippet = document.derived_struct_data.get("snippets", [{}])[0].get(
            "snippet", ""
        )
        link = document.derived_struct_data.get("link", "")

        results.append(f"**{title}**\n{snippet}\nSource: {link}\n")

    if not results:
        return "No relevant documents found for the query."

    return "\n---\n".join(results)


def _search_with_embeddings(
    query: str, project_id: str, location: str, max_results: int
) -> str:
    """
    Perform semantic search using text embeddings and vector similarity.

    This is a fallback method when Vertex AI Search is not configured.
    It uses Vertex AI text embeddings to perform semantic search.

    Args:
        query: Search query
        project_id: GCP project ID
        location: GCP location
        max_results: Maximum number of results

    Returns:
        Formatted search results
    """
    # Initialize the text embedding model
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    # Generate embedding for the query
    query_embedding = model.get_embeddings([query])[0].values

    # In a production system, you would:
    # 1. Load document embeddings from a vector database (e.g., Vertex AI Vector Search)
    # 2. Compute similarity scores between query and document embeddings
    # 3. Return top k most similar documents

    # For now, return a message indicating setup is needed
    return (
        "RAG search with embeddings requires additional setup:\n"
        "1. Index your documents in a vector database\n"
        "2. Configure RAG_SEARCH_DATASTORE_ID in your .env file\n"
        "3. Or implement custom vector similarity search here"
    )
