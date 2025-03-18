# PDF Text Extraction API

A simple, efficient API service built with FastAPI for extracting text from PDF documents. This project provides a lightweight alternative to commercial document processing services.

## Features

- **PDF Text Extraction**: Extract all text content from PDF files
- **REST API**: Simple HTTP endpoint for processing documents
- **Docker Support**: Run locally or deploy to cloud environments
- **Google Cloud Run Ready**: Easy deployment to serverless infrastructure

## Getting Started

### Prerequisites

- Docker (with BuildX support for multi-architecture builds)
- Make
- For cloud deployment: Google Cloud Platform account
- For local testing: A sample PDF file

### System Requirements

- For local development: Any operating system with Docker support
- For cloud deployment: 
  - If using Apple Silicon Mac (M1/M2/M3), you'll need multi-architecture build support
  - Google Cloud account with billing enabled

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pdf-extraction-api.git
   cd pdf-extraction-api
   ```

2. Set up your environment variables:
   ```bash
   make setup-env
   ```
   
3. Edit the `.env` file with your specific configuration:
   ```bash
   nano .env
   ```

4. Verify your environment settings:
   ```bash
   make env-info
   ```

### Local Development

1. Build the Docker image:
   ```bash
   make local-build
   ```

2. Run the service locally:
   ```bash
   make local-run
   ```

3. Test the API with a sample PDF:
   ```bash
   make local-test
   ```
   Note: Place a file named `test.pdf` in your project directory for testing.

4. To stop the service:
   ```bash
   make local-stop
   ```

### Google Cloud Run Deployment

1. Authenticate with Google Cloud:
   ```bash
   make gcp-auth
   ```

2. Enable required Google Cloud services:
   ```bash
   make gcp-enable-services
   ```

3. Set up Docker BuildX for multi-architecture builds (required for Apple Silicon Macs):
   ```bash
   make setup-buildx
   ```

4. Deploy to Google Cloud Run:
   ```bash
   make gcp-release
   ```

   > **Note**: If you're using an Apple Silicon Mac (M1/M2/M3), the deployment process has been configured to build AMD64 compatible images required by Google Cloud Run.

5. Alternative Deployment Using Google Cloud Build (recommended for Apple Silicon Macs):
   ```bash
   make gcp-cloud-release
   ```
   This method uses Google's servers to build the container image, which avoids architecture compatibility issues.

4. Get the deployed service URL:
   ```bash
   make gcp-url
   ```

5. Test the deployed API:
   ```bash
   make gcp-test
   ```

## API Documentation

### Extract Text from PDF

**Endpoint**: `/extract-text/`

**Method**: POST

**Content-Type**: multipart/form-data

**Request Parameters**:
- `file`: The PDF file to process

**Response**:
```json
{
  "filename": "example.pdf",
  "text": "Extracted text content from the PDF..."
}
```

## Project Structure

```
.
├── Dockerfile            # Container definition
├── main.py               # FastAPI application code
├── Makefile              # Build and deployment scripts
├── .env.template         # Template for environment variables
├── .env                  # Local environment variables (not committed to Git)
├── .gitignore            # Git ignore rules
└── README.md             # This documentation
```

## Architecture

This application is designed as a lightweight microservice with:

1. **FastAPI Backend**: Handles PDF processing requests
2. **Docker Containerization**: Ensures consistent deployment across environments
3. **Cloud Run Deployment**: Serverless infrastructure that scales automatically

### Deployment Architecture

```
[Client] → [Cloud Run API Endpoint] → [FastAPI Container] → [PDF Processing Logic]
```

The service accepts PDF files via a POST request, processes them using PyPDF and PDFPlumber libraries, and returns the extracted text in a JSON response.

## Technologies Used

- [FastAPI](https://fastapi.tiangolo.com/) - Fast, modern Python web framework
- [PyPDF](https://pypdf.readthedocs.io/) - PDF processing library
- [PDFPlumber](https://github.com/jsvine/pdfplumber) - Enhanced PDF text extraction
- [Docker](https://www.docker.com/) - Containerization platform
- [Docker BuildX](https://docs.docker.com/buildx/working-with-buildx/) - Multi-architecture build support
- [Google Cloud Run](https://cloud.google.com/run) - Serverless container platform
- [Google Container Registry](https://cloud.google.com/container-registry) - Container image storage

## Performance Considerations

- **Timeout Limits**: Cloud Run has a maximum request timeout of 60 minutes, which should be sufficient for most PDF processing tasks.
- **Memory Allocation**: For large PDFs, you may need to increase the memory allocation in the Cloud Run deployment settings.
- **Cold Starts**: As a serverless platform, Cloud Run may experience cold starts. For production use with high traffic, consider setting a minimum number of instances.
- **Concurrent Requests**: The service can handle multiple concurrent requests, limited by the resources allocated to the Cloud Run instance.

## Extending the API

To add more functionality:

1. Edit `main.py` to add new endpoints
2. Update the Dockerfile if new dependencies are needed
3. Rebuild with `make local-build`

### Environment Variables

This project uses environment variables for configuration. These are stored in a `.env` file (not committed to version control for security reasons). A template is provided in `.env.template`.

Key environment variables:
- `GCP_PROJECT_ID`: Your Google Cloud Platform project ID
- `GCP_REGION`: The GCP region for deployment (default: us-central1)
- `PORT`: The port to expose (default: 8080)

You can check your current environment settings with:
```bash
make env-info
```

Example of adding a metadata extraction endpoint:

```python
@app.post("/extract-metadata/")
async def extract_metadata(file: UploadFile = File(...)):
    if file.filename.endswith(".pdf"):
        pdf_reader = pypdf.PdfReader(file.file)
        metadata = pdf_reader.metadata
        return {
            "filename": file.filename,
            "metadata": {
                "title": metadata.get('/Title', ''),
                "author": metadata.get('/Author', ''),
                "creator": metadata.get('/Creator', ''),
                "producer": metadata.get('/Producer', '')
            }
        }
    
    return {"error": "Only PDFs are supported"}
```

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

### Common Issues

#### Docker BuildX Not Found
If you encounter errors about BuildX not being available:
```bash
make setup-buildx
```

#### Permission Denied on GCP Services
Make sure you have the correct IAM permissions:
- Service Usage Admin
- Cloud Run Admin
- Storage Admin

#### Push to Container Registry Fails
Configure Docker to use GCP credentials:
```bash
gcloud auth configure-docker
```

#### Deployment Architecture Issues
When deploying from Apple Silicon Macs, you have two options:

1. Use the multi-architecture build (can be problematic on some systems):
```bash
make setup-buildx
make gcp-build
```

2. **Recommended:** Use Google Cloud Build to handle the build process:
```bash
make gcp-cloud-release
```
This second approach is more reliable because it builds the container on Google's infrastructure, avoiding architecture compatibility issues completely.

## Security Notes

- This API doesn't implement authentication in its current form. For production use, consider enabling Cloud Run authentication.
- PDF files can potentially contain malicious content. Consider implementing additional validation and sanitization for production use.
- Environment variables containing sensitive information should never be committed to version control.
