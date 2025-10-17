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
from typing import Any, TYPE_CHECKING

from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from typing_extensions import override
from google.adk.utils.model_name_utils import is_gemini_2_model

if TYPE_CHECKING:
    from google.adk.models import LlmRequest


class ConditionalRagRetrieval(VertexAiRagRetrieval):
    """
    A RAG retrieval tool that conditionally disables itself when multimodal content is present.

    Gemini's RAG grounding doesn't support multimodal inputs (PDFs, images), so we skip
    RAG when files are attached and only use it for text-only queries.
    """

    @override
    async def process_llm_request(
        self,
        *,
        tool_context: ToolContext,
        llm_request: 'LlmRequest',
    ) -> None:
        # Check if there are any non-text parts in the contents
        has_multimodal_content = False

        if llm_request.contents:
            for content in llm_request.contents:
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        # If part is not just text, it's multimodal
                        if not isinstance(part, types.Part) or not hasattr(part, 'text'):
                            # Check if it has file_data, inline_data, or other non-text attributes
                            if hasattr(part, 'file_data') or hasattr(part, 'inline_data'):
                                has_multimodal_content = True
                                break
                            # For types.Part, check if it's actually text
                            if isinstance(part, types.Part):
                                # If it doesn't have text attribute or text is None, it's likely multimodal
                                if not hasattr(part, 'text') or (hasattr(part, 'text') and part.text is None):
                                    has_multimodal_content = True
                                    break
                if has_multimodal_content:
                    break

        # Only add RAG if there's no multimodal content
        if not has_multimodal_content:
            # Use the parent class logic to add RAG grounding
            await super().process_llm_request(
                tool_context=tool_context,
                llm_request=llm_request
            )
        # If has_multimodal_content, we skip adding RAG grounding entirely


def get_rag_search_tool():
    """
    Create and return a Vertex AI RAG retrieval tool configured from environment variables.

    Returns:
        ConditionalRagRetrieval: Configured RAG retrieval tool
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    rag_corpus_id = os.getenv("RAG_CORPUS_NAME")

    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")

    if not rag_corpus_id:
        raise ValueError("RAG_CORPUS_NAME environment variable not set")

    # Build full corpus resource name if only corpus ID is provided
    if not rag_corpus_id.startswith("projects/"):
        rag_corpus_name = (
            f"projects/{project_id}/locations/{location}/ragCorpora/{rag_corpus_id}"
        )
    else:
        rag_corpus_name = rag_corpus_id

    return ConditionalRagRetrieval(
        name="rag_search",
        description=(
            "Search through indexed documents using RAG (Retrieval Augmented Generation). "
            "This tool searches through a collection of documents that have been previously "
            "indexed and returns the most relevant passages based on the query."
        ),
        rag_corpora=[rag_corpus_name],
        similarity_top_k=5,
        vector_distance_threshold=0.3,
    )


# Create the tool instance
rag_search_tool = get_rag_search_tool()

# Also export as rag_search for backwards compatibility
rag_search = rag_search_tool
