# Load environment variables from .env file if it exists
ifneq (,$(wildcard .env))
include .env
export $(shell sed 's/=.*//' .env)
endif

# Variables
PROJECT_ID ?= $(or $(GCP_PROJECT_ID),default-project-id)
SERVICE_NAME ?= byo-unstructured-api
REGION ?= $(or $(GCP_REGION),us-central1)
LOCAL_IMAGE_NAME=$(SERVICE_NAME)-local
CLOUD_IMAGE=gcr.io/$(PROJECT_ID)/$(SERVICE_NAME)
PORT ?= 8080
BYO_UNSTRUCTURED_API_KEY ?= default-dev-key

#######################
# Local Development   #
#######################

# Build the Docker image for local development
local-build:
	docker build -t $(LOCAL_IMAGE_NAME) .

# Run the container locally
local-run:
	docker run -p $(PORT):8080 -e BYO_UNSTRUCTURED_API_KEY=$(BYO_UNSTRUCTURED_API_KEY) $(LOCAL_IMAGE_NAME)

# Run container in detached mode
local-run-detached:
	docker run -d -p $(PORT):8080 -e BYO_UNSTRUCTURED_API_KEY=$(BYO_UNSTRUCTURED_API_KEY) $(LOCAL_IMAGE_NAME)

# Stop the running container
local-stop:
	docker ps -q --filter ancestor=$(LOCAL_IMAGE_NAME) | xargs -r docker stop

# Remove the local container and image
local-clean:
	docker ps -aq --filter ancestor=$(LOCAL_IMAGE_NAME) | xargs -r docker rm
	docker images -q $(LOCAL_IMAGE_NAME) | xargs -r docker rmi

# Rebuild and restart the local container
local-rebuild: local-clean local-build local-run

# Test by sending a request to the local server with API key
local-test:
	curl -X 'POST' \
	  'http://localhost:$(PORT)/unstructured' \
	  -H 'accept: application/json' \
	  -H 'x-api-key: $(BYO_UNSTRUCTURED_API_KEY)' \
	  -H 'Content-Type: multipart/form-data' \
	  -F 'file=@test.pdf'

#######################
# Setup Docker BuildX for multi-platform builds
setup-buildx:
	docker buildx create --name mybuilder --use || true
	docker buildx inspect --bootstrap

# Google Cloud Run    #
#######################

# Authenticate Google Cloud CLI
gcp-auth:
	gcloud auth login
	gcloud config set project $(PROJECT_ID)
	gcloud auth configure-docker

# Enable required Google Cloud services
gcp-enable-services:
	gcloud services enable run.googleapis.com containerregistry.googleapis.com

# Build Docker image for Google Cloud (with platform specification for AMD64)
gcp-build:
	docker buildx build --platform linux/amd64 -t $(CLOUD_IMAGE) --push .

# Deploy to Google Cloud Run with API key from .env
gcp-deploy:
	@if [ "$(BYO_UNSTRUCTURED_API_KEY)" = "default-dev-key" ]; then \
		echo "⚠️ WARNING: Deploying with default development API key."; \
		echo "This is not recommended for production."; \
		echo "Please set a secure BYO_UNSTRUCTURED_API_KEY in your .env file."; \
		read -p "Continue anyway? (y/N): " confirm && [ $$confirm = "y" ] || exit 1; \
	else \
		echo "✅ Deploying with API key from .env file"; \
	fi
	gcloud run deploy $(SERVICE_NAME) \
	  --image $(CLOUD_IMAGE) \
	  --platform managed \
	  --region $(REGION) \
	  --allow-unauthenticated \
	  --set-env-vars "BYO_UNSTRUCTURED_API_KEY=$(BYO_UNSTRUCTURED_API_KEY)"

# Open deployed service URL in browser
gcp-open:
	gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format 'value(status.url)' | xargs open

# Full pipeline: Build, Push, Deploy (push is included in build)
gcp-release: setup-buildx gcp-build gcp-deploy gcp-open

# Clean up Google Cloud Docker images
gcp-clean:
	docker images -q $(CLOUD_IMAGE) | xargs -r docker rmi

# Show deployed service URL
gcp-url:
	gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format 'value(status.url)'

# Test API after deployment
gcp-test:
	curl -X 'POST' \
	  "$(shell gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format 'value(status.url)')/unstructured" \
	  -H 'accept: application/json' \
	  -H 'x-api-key: $(BYO_UNSTRUCTURED_API_KEY)' \
	  -H 'Content-Type: multipart/form-data' \
	  -F 'file=@test.pdf'

#######################
# General Commands    #
#######################

# Show all running containers
ps:
	docker ps

# Setup environment file from template if it doesn't exist
setup-env:
	@if [ ! -f .env ]; then \
		if [ -f .env.sample ]; then \
			cp .env.sample .env; \
			echo ".env file created from template. Please edit it with your actual values."; \
		else \
			echo "# Google Cloud Platform configuration\nGCP_PROJECT_ID=your-project-id\nGCP_REGION=us-central1\nPORT=8080\nBYO_UNSTRUCTURED_API_KEY=your-secure-api-key" > .env; \
			echo ".env file created. Please edit it with your actual values."; \
		fi; \
	else \
		echo ".env file already exists."; \
	fi

# Print current environment settings
env-info:
	@echo "Current environment settings:"
	@echo "  PROJECT_ID: $(PROJECT_ID)"
	@echo "  REGION: $(REGION)"
	@echo "  SERVICE_NAME: $(SERVICE_NAME)"
	@echo "  PORT: $(PORT)"
	@if [ "$(BYO_UNSTRUCTURED_API_KEY)" = "default-dev-key" ]; then \
		echo "  BYO_UNSTRUCTURED_API_KEY: default-dev-key (OK for local development only)"; \
	else \
		echo "  BYO_UNSTRUCTURED_API_KEY: ******** (secure key set)"; \
	fi

# Help command to list available targets
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup-env           - Create .env file from template if it doesn't exist"
	@echo "  env-info            - Display current environment settings"
	@echo ""
	@echo "Local Development:"
	@echo "  local-build         - Build Docker image for local testing"
	@echo "  local-run           - Run container locally"
	@echo "  local-run-detached  - Run container locally in background"
	@echo "  local-stop          - Stop local container"
	@echo "  local-clean         - Remove local container and image"
	@echo "  local-rebuild       - Rebuild and restart local container"
	@echo "  local-test          - Test local deployment with a sample PDF"
	@echo ""
	@echo "Google Cloud Run:"
	@echo "  gcp-auth            - Authenticate with Google Cloud"
	@echo "  gcp-enable-services - Enable required GCP services"
	@echo "  setup-buildx        - Set up Docker BuildX for multi-platform builds"
	@echo "  gcp-build           - Build and push Docker image for GCP (AMD64 architecture)"
	@echo "  gcp-deploy          - Deploy to Google Cloud Run with API key from .env"
	@echo "  gcp-release         - Full pipeline: build, push, deploy"
	@echo "  gcp-clean           - Clean up GCP Docker images"
	@echo "  gcp-url             - Show deployed service URL"
	@echo "  gcp-test            - Test GCP deployment with a sample PDF"
	@echo ""
	@echo "General:"
	@echo "  ps                  - Show running containers"
	@echo "  help                - Show this help message"