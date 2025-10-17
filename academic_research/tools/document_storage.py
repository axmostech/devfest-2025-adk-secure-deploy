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

"""Simple document storage with embeddings for RAG."""

import hashlib
import json
import os
from typing import List, Tuple

from google.cloud import storage
from vertexai.language_models import TextEmbeddingModel


class DocumentStore:
    """Store and retrieve documents with embeddings."""

    def __init__(self):
        self.bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")
        self.folder = "rag_documents"

        if not self.bucket_name:
            raise ValueError("GOOGLE_CLOUD_STORAGE_BUCKET not set")

        self.storage_client = storage.Client(project=self.project_id)
        self.bucket = self.storage_client.bucket(self.bucket_name)

        model_name = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-004")
        self.embedding_model = TextEmbeddingModel.from_pretrained(model_name)

    def _chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def store_document(self, title: str, content: str) -> str:
        """Store a document with embeddings."""
        doc_id = hashlib.md5(title.encode()).hexdigest()
        chunks = self._chunk_text(content)

        embeddings = []
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_embeddings = self.embedding_model.get_embeddings(batch)
            embeddings.extend([emb.values for emb in batch_embeddings])

        doc_data = {
            "id": doc_id,
            "title": title,
            "chunks": chunks,
            "embeddings": embeddings,
            "chunk_count": len(chunks)
        }

        blob = self.bucket.blob(f"{self.folder}/{doc_id}.json")
        blob.upload_from_string(json.dumps(doc_data), content_type="application/json")

        return doc_id

    def search(self, query: str, max_results: int = 5) -> List[Tuple[str, str, float]]:
        """Search documents using semantic similarity."""
        query_embedding = self.embedding_model.get_embeddings([query])[0].values

        results = []

        blobs = self.bucket.list_blobs(prefix=f"{self.folder}/")
        for blob in blobs:
            if not blob.name.endswith(".json"):
                continue

            doc_data = json.loads(blob.download_as_string())

            for chunk, embedding in zip(doc_data["chunks"], doc_data["embeddings"]):
                similarity = self._cosine_similarity(query_embedding, embedding)
                results.append((doc_data["title"], chunk, similarity))

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:max_results]


_store = None

def get_store() -> DocumentStore:
    """Get or create the document store singleton."""
    global _store
    if _store is None:
        _store = DocumentStore()
    return _store
