# Use Python base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app

# Set default API key for development (should be overridden in production)
ENV BYO_UNSTRUCTURED_API_KEY="default-dev-key"

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]