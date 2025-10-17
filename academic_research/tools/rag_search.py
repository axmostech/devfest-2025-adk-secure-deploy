"""RAG search tool using Vertex AI RAG Engine."""

import os
from google.adk.tools import FunctionTool
from vertexai.preview import rag
import vertexai


def rag_search(query: str) -> str:
    """
    Search through indexed documents using RAG (Retrieval Augmented Generation).

    This tool searches through a collection of documents that have been previously
    indexed in Vertex AI RAG Engine and returns the most relevant passages.

    Args:
        query: The search query or question to find relevant information for.

    Returns:
        A string containing the most relevant passages found in the documents.
    """
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")
        rag_corpus_id = os.getenv("RAG_CORPUS_NAME")

        if not project_id:
            return "Error: GOOGLE_CLOUD_PROJECT environment variable not set."

        if not rag_corpus_id:
            return "Error: RAG_CORPUS_NAME environment variable not set."

        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)

        # Build full corpus resource name
        if not rag_corpus_id.startswith("projects/"):
            corpus_name = (
                f"projects/{project_id}/locations/{location}/ragCorpora/{rag_corpus_id}"
            )
        else:
            corpus_name = rag_corpus_id

        # Perform RAG retrieval query
        response = rag.retrieval_query(
            rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
            text=query,
            similarity_top_k=5,
            vector_distance_threshold=0.5,
        )

        # Format results
        if not response.contexts or not response.contexts.contexts:
            return f"No relevant documents found for query: '{query}'"

        results = []
        for i, context in enumerate(response.contexts.contexts, 1):
            # Extract text and metadata
            text = context.text[:500]  # Limit to 500 chars per context
            distance = context.distance

            # Try to get source info
            source = "Unknown source"
            if hasattr(context, 'source_uri') and context.source_uri:
                source = context.source_uri

            results.append(
                f"**Result {i}** (similarity: {1-distance:.2f})\n"
                f"{text}...\n"
                f"Source: {source}\n"
            )

        return "\n---\n".join(results)

    except Exception as e:
        return f"Error performing RAG search: {str(e)}"


# Wrap the function in a FunctionTool
rag_search = FunctionTool(rag_search)
