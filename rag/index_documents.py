#!/usr/bin/env python3
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

"""
Helper script to upload local documents to Cloud Storage for RAG indexing.

This script:
1. Uploads PDF, TXT, or HTML files from a local directory to Cloud Storage
2. Optionally triggers the import into Vertex AI Search
"""

import os
import sys
from pathlib import Path

from absl import app, flags
from dotenv import load_dotenv
from google.cloud import storage

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID")
flags.DEFINE_string("bucket", None, "Cloud Storage bucket name")
flags.DEFINE_string("source_dir", None, "Local directory with documents")
flags.DEFINE_string("destination_path", "rag-documents/", "Path in bucket")
flags.DEFINE_list(
    "extensions",
    ["pdf", "txt", "html", "json"],
    "File extensions to upload",
)


def upload_documents(
    project_id: str,
    bucket_name: str,
    source_dir: str,
    destination_path: str,
    extensions: list[str],
) -> list[str]:
    """
    Upload documents from local directory to Cloud Storage.

    Args:
        project_id: GCP project ID
        bucket_name: Cloud Storage bucket name
        source_dir: Local directory containing documents
        destination_path: Target path in the bucket
        extensions: List of file extensions to include

    Returns:
        List of uploaded file URIs
    """
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)

    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: Directory not found: {source_dir}")
        sys.exit(1)

    uploaded_files = []
    total_files = 0

    print(f"Scanning directory: {source_dir}")
    print(f"Looking for files with extensions: {extensions}")
    print("-" * 80)

    for ext in extensions:
        pattern = f"**/*.{ext}"
        for file_path in source_path.rglob(pattern):
            if file_path.is_file():
                relative_path = file_path.relative_to(source_path)
                blob_name = f"{destination_path}{relative_path}"

                blob = bucket.blob(blob_name)
                blob.upload_from_filename(str(file_path))

                uri = f"gs://{bucket_name}/{blob_name}"
                uploaded_files.append(uri)
                total_files += 1

                print(f"Uploaded: {file_path.name} -> {uri}")

    print("-" * 80)
    print(f"\nTotal files uploaded: {total_files}")

    if total_files > 0:
        gcs_pattern = f"gs://{bucket_name}/{destination_path}*"
        print(f"\nTo import these documents into Vertex AI Search, run:")
        print(f"\npython rag/setup_rag.py \\")
        print(f"  --action=import \\")
        print(f"  --datastore_id=YOUR_DATASTORE_ID \\")
        print(f"  --gcs_uri='{gcs_pattern}'")

    return uploaded_files


def main(argv):
    """Main entry point for document indexing script."""
    del argv

    load_dotenv()

    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    bucket_name = FLAGS.bucket or os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT not set")
        sys.exit(1)

    if not bucket_name:
        print("Error: GOOGLE_CLOUD_STORAGE_BUCKET not set")
        sys.exit(1)

    if not FLAGS.source_dir:
        print("Error: --source_dir is required")
        print("\nExample usage:")
        print("  python rag/index_documents.py --source_dir=/path/to/documents")
        sys.exit(1)

    try:
        upload_documents(
            project_id,
            bucket_name,
            FLAGS.source_dir,
            FLAGS.destination_path,
            FLAGS.extensions,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
