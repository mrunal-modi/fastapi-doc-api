# Google Cloud Run Deployment Guide with API Key Authentication

This guide details how to deploy your FastAPI document processing service to Google Cloud Run with proper API key authentication.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and configured
- Docker installed (for local testing)
- Your project files (main.py, Dockerfile, requirements.txt)

## 1. Update Your Code

Make sure your `main.py` has been updated with the API key authentication code, and your Dockerfile includes the default API_KEY environment variable.

## 2. Test Locally First

Before deploying to Cloud Run, test the authentication locally:

```bash
# Build your Docker image
make local-build

# Run the container locally
make local-run

# Test with the auth-test script
python auth_test.py http://localhost:8080 default-dev-key test.pdf

# Test without an API key (should fail)
python auth_test.py http://localhost:8080 "" test.pdf
```

## 3. Deploy to Google Cloud Run

Use your existing Makefile command to deploy, but we'll need to add the API_KEY environment variable:

### Option 1: Deploy with Cloud Build

```bash
# First, ensure your .env file has the correct values
# GCP_PROJECT_ID=your-project-id
# GCP_REGION=your-preferred-region

# Deploy using Cloud Build (recommended for M1/M2 Macs)
gcloud builds submit --tag gcr.io/$(GCP_PROJECT_ID)/fastapi-doc-api .

# Deploy to Cloud Run with custom API key
gcloud run deploy fastapi-doc-api \
  --image gcr.io/$(GCP_PROJECT_ID)/fastapi-doc-api \
  --platform managed \
  --region $(GCP_REGION) \
  --allow-unauthenticated \
  --set-env-vars "API_KEY=your-secure-api-key-here"
```

### Option 2: Use the Makefile with Environment Variables

Add the API_KEY to your deployment by updating your Makefile command:

```bash
# Add this to your Makefile
gcp-secure-deploy:
	gcloud run deploy $(SERVICE_NAME) \
	  --image $(CLOUD_IMAGE) \
	  --platform managed \
	  --region $(REGION) \
	  --allow-unauthenticated \
	  --set-env-vars "API_KEY=$(API_KEY)"

# Then run it with:
API_KEY=your-secure-api-key-here make gcp-secure-deploy
```

### Option 3: Update Existing Deployment

If you've already deployed without setting an API key, you can update the existing service:

1. Go to Google Cloud Console > Cloud Run > Your Service
2. Click "Edit & Deploy New Revision"
3. Expand "Container, Variables & Secrets, Connections" 
4. Add environment variable:
   - Name: `API_KEY`
   - Value: Your secure API key
5. Click "Deploy"

## 4. Verify Deployment

After deployment, verify that the authentication is working:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe fastapi-doc-api --region $(GCP_REGION) --format 'value(status.url)')

# Test with valid API key
python auth_test.py $SERVICE_URL your-secure-api-key-here test.pdf

# Test with invalid API key (should fail)
python auth_test.py $SERVICE_URL wrong-key test.pdf
```

## 5. Update Your RAG Implementation

Now update your RAG implementation to use the deployed service and API key:

```
# In your environment variables
UNSTRUCTURED_API_URL="https://your-cloud-run-service-url/unstructured"
UNSTRUCTURED_API_KEY="your-secure-api-key-here"
```

## 6. API Key Security Best Practices

- Use a strong, randomly generated API key for production
- Store the API key securely (don't commit it to version control)
- Consider using Google Secret Manager for managing API keys
- Rotate the API key periodically
- Use a different key for development and production
- Monitor for suspicious API usage patterns

## 7. Troubleshooting

If you encounter issues:

- Check the Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fastapi-doc-api"`
- Verify the API_KEY environment variable is set correctly in Cloud Run
- Test the endpoint directly with curl:
  ```
  curl -X POST \
    -H "x-api-key: your-secure-api-key-here" \
    -F "file=@test.pdf" \
    https://your-cloud-run-service-url/unstructured
  ```
