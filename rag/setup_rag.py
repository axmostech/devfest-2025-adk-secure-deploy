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
Setup script for RAG (Retrieval Augmented Generation) with Vertex AI Search.

This script helps you:
1. Create a Vertex AI Search datastore
2. Import documents from a Cloud Storage bucket
3. Configure the datastore for use with the academic research agent
"""

import os
import sys
from typing import Optional

from absl import app, flags
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID")
flags.DEFINE_string("location", "global", "GCP location for Discovery Engine")
flags.DEFINE_string("datastore_id", None, "Datastore ID to create")
flags.DEFINE_string("datastore_name", "Academic Research Documents", "Display name")
flags.DEFINE_string("gcs_uri", None, "GCS URI with documents (gs://bucket/path/)")
flags.DEFINE_enum(
    "action",
    None,
    ["create", "import", "list", "delete"],
    "Action to perform",
)


def create_datastore(
    project_id: str,
    location: str,
    datastore_id: str,
    display_name: str,
) -> str:
    """
    Create a new Vertex AI Search datastore.

    Args:
        project_id: GCP project ID
        location: GCP location (default: global)
        datastore_id: Unique ID for the datastore
        display_name: Human-readable name for the datastore

    Returns:
        The full resource name of the created datastore
    """
    client = discoveryengine.DataStoreServiceClient()

    parent = (
        f"projects/{project_id}/locations/{location}/collections/default_collection"
    )

    data_store = discoveryengine.DataStore(
        display_name=display_name,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
    )

    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store=data_store,
        data_store_id=datastore_id,
    )

    operation = client.create_data_store(request=request)
    print(f"Creating datastore: {datastore_id}")
    print("This may take a few minutes...")

    response = operation.result()
    print(f"Datastore created: {response.name}")
    print(f"\nAdd this to your .env file:")
    print(f"RAG_SEARCH_DATASTORE_ID={datastore_id}")

    return response.name


def import_documents(
    project_id: str,
    location: str,
    datastore_id: str,
    gcs_uri: str,
) -> None:
    """
    Import documents from Cloud Storage into the datastore.

    Supported formats:
    - PDF files
    - Text files (.txt)
    - HTML files
    - JSON/JSONL files with metadata

    Args:
        project_id: GCP project ID
        location: GCP location
        datastore_id: Target datastore ID
        gcs_uri: Cloud Storage URI (gs://bucket/path/)
    """
    client = discoveryengine.DocumentServiceClient()

    parent = (
        f"projects/{project_id}/locations/{location}"
        f"/collections/default_collection/dataStores/{datastore_id}/branches/default_branch"
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri] if not gcs_uri.endswith("*") else [],
            data_schema="content",
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    operation = client.import_documents(request=request)
    print(f"Importing documents from: {gcs_uri}")
    print("This may take several minutes depending on the number of documents...")

    response = operation.result()
    print(f"Import completed successfully")
    print(f"Documents imported: {response}")


def list_datastores(project_id: str, location: str) -> None:
    """
    List all datastores in the project.

    Args:
        project_id: GCP project ID
        location: GCP location
    """
    client = discoveryengine.DataStoreServiceClient()

    parent = (
        f"projects/{project_id}/locations/{location}/collections/default_collection"
    )

    request = discoveryengine.ListDataStoresRequest(parent=parent)

    page_result = client.list_data_stores(request=request)

    print(f"\nDatastores in project {project_id}:")
    print("-" * 80)

    for data_store in page_result:
        datastore_id = data_store.name.split("/")[-1]
        print(f"\nID: {datastore_id}")
        print(f"Name: {data_store.display_name}")
        print(f"State: {data_store.name}")
        print(f"Created: {data_store.create_time}")


def delete_datastore(
    project_id: str,
    location: str,
    datastore_id: str,
) -> None:
    """
    Delete a datastore.

    Args:
        project_id: GCP project ID
        location: GCP location
        datastore_id: Datastore ID to delete
    """
    client = discoveryengine.DataStoreServiceClient()

    name = (
        f"projects/{project_id}/locations/{location}"
        f"/collections/default_collection/dataStores/{datastore_id}"
    )

    request = discoveryengine.DeleteDataStoreRequest(name=name)

    operation = client.delete_data_store(request=request)
    print(f"Deleting datastore: {datastore_id}")

    operation.result()
    print(f"Datastore deleted successfully")


def main(argv):
    """Main entry point for the RAG setup script."""
    del argv

    load_dotenv()

    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location

    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT not set")
        sys.exit(1)

    if not FLAGS.action:
        print("Error: --action is required")
        print("Available actions: create, import, list, delete")
        sys.exit(1)

    try:
        if FLAGS.action == "create":
            if not FLAGS.datastore_id:
                print("Error: --datastore_id is required for create action")
                sys.exit(1)
            create_datastore(
                project_id,
                location,
                FLAGS.datastore_id,
                FLAGS.datastore_name,
            )

        elif FLAGS.action == "import":
            if not FLAGS.datastore_id or not FLAGS.gcs_uri:
                print("Error: --datastore_id and --gcs_uri are required for import")
                sys.exit(1)
            import_documents(
                project_id,
                location,
                FLAGS.datastore_id,
                FLAGS.gcs_uri,
            )

        elif FLAGS.action == "list":
            list_datastores(project_id, location)

        elif FLAGS.action == "delete":
            if not FLAGS.datastore_id:
                print("Error: --datastore_id is required for delete action")
                sys.exit(1)
            confirm = input(
                f"Are you sure you want to delete datastore '{FLAGS.datastore_id}'? (yes/no): "
            )
            if confirm.lower() == "yes":
                delete_datastore(project_id, location, FLAGS.datastore_id)
            else:
                print("Delete cancelled")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
