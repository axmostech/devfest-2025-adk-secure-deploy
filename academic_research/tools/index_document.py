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

"""Tool to index document content for RAG retrieval."""

from google.adk.tools import FunctionTool
from .document_storage import get_store


def _index_document_impl(title: str, content: str) -> str:
    """
    Index a document for semantic search.

    Call this tool whenever you receive a document (PDF or text) from the user
    to store it in the RAG system for future retrieval.

    Args:
        title: The title or filename of the document
        content: The full text content of the document

    Returns:
        Confirmation message with the document ID
    """
    try:
        store = get_store()
        doc_id = store.store_document(title, content)
        return f"Document '{title}' successfully indexed with ID: {doc_id}"
    except Exception as e:
        return f"Error indexing document: {str(e)}"


index_document_tool = FunctionTool(_index_document_impl)
