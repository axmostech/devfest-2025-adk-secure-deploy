# Load environment variables from .env if it exists
-include .env
export

# Derived variables
PROJECT_ID ?= $(GOOGLE_CLOUD_PROJECT)
LOCATION ?= $(GOOGLE_CLOUD_LOCATION)
REGION ?= $(GOOGLE_CLOUD_REGION)
BUCKET ?= $(GOOGLE_CLOUD_STORAGE_BUCKET)
SERVICE_NAME ?= academic-research-agent
DATASTORE_ID ?= academic-docs

.PHONY: help setup install test run web deploy-agent deploy-cloudrun logs clean

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup           - Create .env file from template"
	@echo "  install         - Install dependencies with Poetry"
	@echo "  install-dev     - Install with dev dependencies"
	@echo "  auth            - Authenticate with Google Cloud"
	@echo ""
	@echo "Development:"
	@echo "  run             - Run agent locally with ADK CLI"
	@echo "  web             - Start ADK web interface"
	@echo "  test            - Run tests"
	@echo "  eval            - Run evaluation"
	@echo "  format          - Format code with black"
	@echo ""
	@echo "RAG Setup:"
	@echo "  rag-create      - Create Vertex AI Search datastore"
	@echo "  rag-upload      - Upload documents to Cloud Storage"
	@echo "  rag-import      - Import documents into datastore"
	@echo "  rag-list        - List all datastores"
	@echo "  rag-delete      - Delete datastore"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-agent    - Deploy to Vertex AI Agent Engine"
	@echo "  deploy-cloudrun - Deploy to Cloud Run"
	@echo "  list-agents     - List deployed agents"
	@echo "  delete-agent    - Delete deployed agent"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs            - View deployment logs"
	@echo "  describe        - Describe deployed service"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean           - Clean up temporary files"
	@echo "  clean-all       - Clean everything including dependencies"
	@echo ""
	@echo "Environment Variables:"
	@echo "  PROJECT_ID: $(PROJECT_ID)"
	@echo "  LOCATION: $(LOCATION)"
	@echo "  BUCKET: $(BUCKET)"
	@echo "  SERVICE_NAME: $(SERVICE_NAME)"

# Setup: Create .env from template
setup:
	@echo "Setting up project environment..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "Created .env file"; \
		echo ""; \
		echo "Please edit .env with your values:"; \
		echo "  GOOGLE_CLOUD_PROJECT=your-project-id"; \
		echo "  GOOGLE_CLOUD_LOCATION=us-central1"; \
		echo "  GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name"; \
	else \
		echo ".env file already exists"; \
	fi

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Installation completed"

install-dev:
	@echo "Installing dependencies with dev tools..."
	pip install -r requirements.txt
	pip install pytest black pytest-asyncio pandas tabulate absl-py
	@echo "Installation completed"

# Authenticate with Google Cloud
auth:
	@echo "Authenticating with Google Cloud..."
	gcloud config set project $(PROJECT_ID)
	gcloud auth application-default login
	gcloud auth application-default set-quota-project $(PROJECT_ID)
	@echo "Authentication completed"

# Run agent locally with ADK CLI
run:
	@echo "Starting agent locally..."
	adk run academic_research

# Start ADK web interface
web:
	@echo "Starting ADK web interface..."
	@echo "Open your browser to the URL shown below"
	adk web

# Run tests
test:
	@echo "Running tests..."
	pytest tests/

# Run evaluation
eval:
	@echo "Running evaluation..."
	pytest eval/

# Format code with black
format:
	@echo "Formatting code with black..."
	black academic_research/ rag/ deployment/ tests/ eval/
	@echo "Code formatted"

# RAG: Create Vertex AI Search datastore
rag-create:
	@echo "Creating Vertex AI Search datastore..."
	@if [ -z "$(DATASTORE_ID)" ]; then \
		echo "Error: DATASTORE_ID not set"; \
		exit 1; \
	fi
	python rag/setup_rag.py \
		--action=create \
		--datastore_id=$(DATASTORE_ID) \
		--datastore_name="Academic Research Documents"
	@echo ""
	@echo "Add this to your .env file:"
	@echo "RAG_SEARCH_DATASTORE_ID=$(DATASTORE_ID)"

# RAG: Upload documents to Cloud Storage
rag-upload:
	@echo "Uploading documents to Cloud Storage..."
	@if [ -z "$(DOCS_DIR)" ]; then \
		echo "Error: DOCS_DIR not set"; \
		echo "Usage: make rag-upload DOCS_DIR=/path/to/documents"; \
		exit 1; \
	fi
	python rag/index_documents.py --source_dir=$(DOCS_DIR)

# RAG: Import documents into datastore
rag-import:
	@echo "Importing documents into datastore..."
	@if [ -z "$(DATASTORE_ID)" ]; then \
		echo "Error: DATASTORE_ID not set"; \
		exit 1; \
	fi
	@GCS_URI="gs://$(BUCKET)/rag-documents/*"; \
	echo "Importing from: $$GCS_URI"; \
	python rag/setup_rag.py \
		--action=import \
		--datastore_id=$(DATASTORE_ID) \
		--gcs_uri="$$GCS_URI"

# RAG: List all datastores
rag-list:
	@echo "Listing datastores..."
	python rag/setup_rag.py --action=list

# RAG: Delete datastore
rag-delete:
	@echo "Deleting datastore..."
	@if [ -z "$(DATASTORE_ID)" ]; then \
		echo "Error: DATASTORE_ID not set"; \
		exit 1; \
	fi
	python rag/setup_rag.py \
		--action=delete \
		--datastore_id=$(DATASTORE_ID)

# Deploy to Vertex AI Agent Engine
deploy-agent:
	@echo "Deploying to Vertex AI Agent Engine..."
	@if [ -z "$(PROJECT_ID)" ] || [ -z "$(LOCATION)" ] || [ -z "$(BUCKET)" ]; then \
		echo "Error: Missing required environment variables"; \
		echo "Please check your .env file"; \
		exit 1; \
	fi
	python deployment/deploy.py --create
	@echo ""
	@echo "Deployment completed"
	@echo "To test: make test-agent AGENT_ID=your-agent-id"

# List deployed agents
list-agents:
	@echo "Listing deployed agents..."
	python deployment/deploy.py --list

# Delete deployed agent
delete-agent:
	@echo "Deleting agent..."
	@if [ -z "$(AGENT_ID)" ]; then \
		echo "Error: AGENT_ID not set"; \
		echo "Usage: make delete-agent AGENT_ID=123456789"; \
		exit 1; \
	fi
	python deployment/deploy.py --delete --resource_id=$(AGENT_ID)

# Test deployed agent
test-agent:
	@echo "Testing deployed agent..."
	@if [ -z "$(AGENT_ID)" ]; then \
		echo "Error: AGENT_ID not set"; \
		echo "Usage: make test-agent AGENT_ID=123456789"; \
		exit 1; \
	fi
	@USER_ID=$${USER_ID:-test-user-$$RANDOM}; \
	echo "Using USER_ID: $$USER_ID"; \
	python deployment/test_deployment.py \
		--resource_id=$(AGENT_ID) \
		--user_id=$$USER_ID

# Build and push Docker image
IMAGE_NAME ?= $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(SERVICE_NAME)/$(SERVICE_NAME)
TAG ?= latest

build:
	@echo "Building Docker image..."
	@if [ -z "$(PROJECT_ID)" ] || [ -z "$(REGION)" ]; then \
		echo "Error: PROJECT_ID and REGION must be set"; \
		exit 1; \
	fi
	docker build --platform linux/amd64 -t $(IMAGE_NAME):$(TAG) .
	@echo "Image built: $(IMAGE_NAME):$(TAG)"

push: build
	@echo "Pushing image to Artifact Registry..."
	docker push $(IMAGE_NAME):$(TAG)
	@echo "Image pushed successfully"

# Deploy to Cloud Run
deploy-cloudrun: push
	@echo "Deploying to Cloud Run..."
	@if [ -z "$(PROJECT_ID)" ] || [ -z "$(REGION)" ]; then \
		echo "Error: Missing required environment variables"; \
		exit 1; \
	fi
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE_NAME):$(TAG) \
		--platform managed \
		--region $(REGION) \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=$(PROJECT_ID),GOOGLE_CLOUD_LOCATION=$(LOCATION),GOOGLE_GENAI_USE_VERTEXAI=true" \
		--allow-unauthenticated \
		--memory=4Gi \
		--cpu=2 \
		--timeout=900 \
		--max-instances=5
	@echo "Deployment completed"
	@echo "Service URL:"
	@gcloud run services describe $(SERVICE_NAME) --region=$(REGION) --format="value(status.url)"

# View logs from Vertex AI
logs:
	@echo "Viewing logs..."
	@if [ -z "$(AGENT_ID)" ]; then \
		echo "Showing recent Cloud Run logs..."; \
		gcloud logs read "resource.type=cloud_run_revision" \
			--limit=50 \
			--format="table(timestamp,severity,textPayload)"; \
	else \
		echo "Showing logs for agent: $(AGENT_ID)"; \
		gcloud logs read "resource.type=aiplatform.googleapis.com/ReasoningEngine" \
			--limit=50 \
			--format="table(timestamp,severity,textPayload)"; \
	fi

# Describe deployed service
describe:
	@if [ -z "$(AGENT_ID)" ]; then \
		echo "Error: AGENT_ID not set"; \
		echo "Usage: make describe AGENT_ID=123456789"; \
		exit 1; \
	fi
	@echo "Agent details:"
	gcloud ai reasoning-engines describe $(AGENT_ID) \
		--project=$(PROJECT_ID) \
		--location=$(LOCATION)

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "Cleanup completed"

# Clean everything including dependencies
clean-all: clean
	@echo "Removing Python cache and virtual environments..."
	rm -rf venv/ .venv/ env/
	@echo "Complete cleanup finished"

# Complete setup flow for new projects
setup-all: setup install-dev auth
	@echo ""
	@echo "Setup completed successfully"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env with your project values"
	@echo "2. Test locally: make run"
	@echo "3. Setup RAG (optional):"
	@echo "   - make rag-create"
	@echo "   - make rag-upload DOCS_DIR=/path/to/docs"
	@echo "   - make rag-import"
	@echo "4. Deploy: make deploy-agent"

# Quick start for development
dev: install-dev
	@echo "Starting development environment..."
	make web

# Full deployment pipeline
deploy-all: install-dev test deploy-agent
	@echo ""
	@echo "Deployment pipeline completed"
	@echo "Run 'make list-agents' to see your deployed agent"
