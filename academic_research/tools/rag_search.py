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

from google.adk.tools.base_tool import BaseTool


class RagSearchTool(BaseTool):
    """Tool for searching through indexed documents using Vertex AI RAG Engine."""

    def __init__(self):
        """Initialize the RAG search tool."""
        super().__init__(
            name="rag_search_tool",
            description=(
                "Search through indexed documents using RAG (Retrieval Augmented Generation). "
                "This tool searches through a collection of documents that have been previously "
                "indexed and returns the most relevant passages based on the query."
            )
        )

    def get_parameters_schema(self) -> dict[str, Any]:
        """Return the JSON schema for the tool's parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query or question to find relevant information for.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of relevant passages to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def run(self, query: str, max_results: int = 5) -> str:
        """
        Execute the RAG search.

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

            return self._search_with_rag_engine(query, project_id, location, max_results)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"Error performing RAG search: {str(e)}\n\nDetails:\n{error_details}"

    def _search_with_rag_engine(
        self, query: str, project_id: str, location: str, max_results: int
    ) -> str:
        """
        Perform semantic search using Vertex AI RAG Engine.

        Args:
            query: Search query
            project_id: GCP project ID
            location: GCP location
            max_results: Maximum number of results

        Returns:
            Formatted search results
        """
        try:
            from vertexai import rag
            import vertexai

            vertexai.init(project=project_id, location=location)

            rag_corpus_name = os.getenv("RAG_CORPUS_NAME")
            if not rag_corpus_name:
                return (
                    "RAG corpus not configured. Please set RAG_CORPUS_NAME in .env\n"
                    "Format: projects/PROJECT_ID/locations/LOCATION/ragCorpora/CORPUS_ID"
                )

            # Build full corpus resource name if only corpus ID is provided
            if not rag_corpus_name.startswith("projects/"):
                rag_corpus_name = (
                    f"projects/{project_id}/locations/{location}/ragCorpora/{rag_corpus_name}"
                )

            rag_retrieval_config = rag.RagRetrievalConfig(
                top_k=max_results,
                filter=rag.Filter(vector_distance_threshold=0.3),
            )

            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=rag_corpus_name,
                    )
                ],
                text=query,
                rag_retrieval_config=rag_retrieval_config,
            )

            if not response or not hasattr(response, 'contexts'):
                return "No relevant documents found for the query."

            formatted_results = []
            for idx, context in enumerate(response.contexts.contexts[:max_results], 1):
                formatted_results.append(
                    f"**Result {idx}**\n{context.text}\n"
                    f"Source: {context.source_uri if hasattr(context, 'source_uri') else 'N/A'}"
                )

            return "\n---\n".join(formatted_results)

        except ImportError:
            return "Vertex AI SDK not available. Install with: pip install google-cloud-aiplatform"
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"Error searching RAG corpus: {str(e)}\n\nDetails:\n{error_details}"


# Create a singleton instance for use in agents
rag_search_tool = RagSearchTool()
