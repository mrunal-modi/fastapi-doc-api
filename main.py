from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends
from typing import List, Dict, Any, Optional
import pypdf
import pdfplumber
import re
import uuid
import datetime
import os
from io import BytesIO

app = FastAPI(
    title="Document Processing API",
    description="A replacement for unstructured.io with document chunking capabilities",
    version="1.0.0"
)

# Helper function to extract text with more formatting preserved using pdfplumber
def extract_text_with_pdfplumber(pdf_bytes):
    with BytesIO(pdf_bytes) as pdf_file:
        with pdfplumber.open(pdf_file) as pdf:
            text_pages = []
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    text_pages.append(text)
            return text_pages

# Chunk text into paragraphs
def chunk_text_into_paragraphs(text: str) -> List[str]:
    # Split on double newlines which typically indicate paragraph breaks
    paragraphs = re.split(r'\n\s*\n', text)
    # Filter out empty paragraphs and strip whitespace
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs

# Chunk by section headers
def chunk_by_headers(text: str) -> List[str]:
    # Pattern for common section headers (e.g., "1. Introduction", "Section 1:", "A. Background", etc.)
    header_patterns = [
        r'^(?:[IVX]+|[A-Z]|\d+(?:\.\d+)*)[\.\s]+\w+',  # Roman numerals, letters, or numbers followed by text
        r'^(?:Section|Chapter|Part)\s+(?:[IVX]+|[A-Z]|\d+(?:\.\d+)*)',  # "Section X" style
        r'^[A-Z][A-Z\s]+(?:\.|\:|\s*$)',  # ALL CAPS section headers
    ]
    combined_pattern = '|'.join(f'({p})' for p in header_patterns)
    
    # Find potential section boundaries
    matches = list(re.finditer(combined_pattern, text, re.MULTILINE))
    
    chunks = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i < len(matches) - 1 else len(text)
        chunks.append(text[start:end].strip())
    
    # If no headers found, fall back to paragraph chunking
    if not chunks:
        return chunk_text_into_paragraphs(text)
    
    return chunks

# Function to chunk text with multiple strategies
def smart_chunking(text: str, min_chunk_size: int = 200, max_chunk_size: int = 1000) -> List[str]:
    # First try chunking by headers
    chunks = chunk_by_headers(text)
    
    # If chunks are too big, break them down further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Further break down by paragraphs
            paragraphs = chunk_text_into_paragraphs(chunk)
            
            # If paragraphs are still too big, use sentence splitting as fallback
            if any(len(p) > max_chunk_size for p in paragraphs):
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= max_chunk_size:
                        current_chunk += " " + sentence if current_chunk else sentence
                    else:
                        if current_chunk:
                            final_chunks.append(current_chunk.strip())
                        current_chunk = sentence
                
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
            else:
                final_chunks.extend(paragraphs)
    
    # Filter out chunks that are too small
    final_chunks = [c for c in final_chunks if len(c) >= min_chunk_size]
    
    # Ensure we don't lose content if all chunks are smaller than min_chunk_size
    if not final_chunks and text.strip():
        final_chunks = [text.strip()]
    
    return final_chunks

# Create document elements in unstructured.io compatible format
def create_document_elements(filename: str, chunks: List[str], page_numbers: Optional[List[int]] = None) -> List[Dict[Any, Any]]:
    elements = []
    
    # If no page numbers are provided, assume all chunks are from page 1
    if not page_numbers:
        page_numbers = [1] * len(chunks)
    
    # Make sure we have enough page numbers
    while len(page_numbers) < len(chunks):
        page_numbers.append(page_numbers[-1])
    
    for i, chunk in enumerate(chunks):
        # Create a unique element_id
        element_id = str(uuid.uuid4())
        
        # Determine the element type based on heuristics
        if i == 0 and len(chunk) < 200:
            element_type = "Title"
        elif re.match(r'^(?:Section|Chapter|Part|\d+\.|\([a-z]\))', chunk.strip()):
            element_type = "NarrativeText"  # Section header or list item
        elif chunk.strip().isupper():
            element_type = "Title"  # All uppercase could be a title
        elif len(chunk.strip()) < 100 and ":" in chunk:
            element_type = "ListItem"  # Short lines with colons often are list items
        else:
            element_type = "NarrativeText"  # Default type
        
        element = {
            "element_id": element_id,
            "text": chunk,
            "type": element_type,
            "metadata": {
                "filename": filename,
                "page_number": page_numbers[i],
                "filetype": "application/pdf",
                "category": "pdf_document",
                "processed_time": datetime.datetime.now().isoformat(),
            }
        }
        
        elements.append(element)
    
    return elements

# Function to verify API key
async def verify_api_key(api_key: Optional[str] = Header(None, alias="x-api-key")):
    expected_api_key = os.environ.get("BYO_UNSTRUCTURED_API_KEY", "default-dev-key")
    if not api_key or api_key != expected_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Please provide a valid API key in the x-api-key header."
        )
    return api_key

@app.post("/unstructured")
async def process_document(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Process a document with chunking to replace unstructured.io API.
    Returns document chunks in the same format as unstructured.io.
    Requires API key authentication via x-api-key header.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are supported")
    
    content = await file.read()
    
    # Get more detailed text with pdfplumber
    text_pages = extract_text_with_pdfplumber(content)
    
    # Store page numbers for each chunk
    all_chunks = []
    page_numbers = []
    
    # Process each page and keep track of page numbers
    for page_num, page_text in enumerate(text_pages, 1):
        if not page_text.strip():
            continue
            
        page_chunks = smart_chunking(page_text)
        all_chunks.extend(page_chunks)
        page_numbers.extend([page_num] * len(page_chunks))
    
    # If no chunks were extracted, fall back to basic extraction
    if not all_chunks:
        pdf_reader = pypdf.PdfReader(BytesIO(content))
        full_text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        all_chunks = smart_chunking(full_text)
        page_numbers = [1] * len(all_chunks)  # Assume all from page 1 in fallback
    
    # Create document elements in unstructured.io compatible format
    elements = create_document_elements(file.filename, all_chunks, page_numbers)
    
    return elements

# Add a route for API documentation about the auth requirement
@app.get("/auth-info")
async def auth_info():
    """
    Returns information about the API authentication requirements.
    """
    return {
        "auth_required": True,
        "auth_type": "API Key",
        "header_name": "x-api-key",
        "environment_variable": "BYO_UNSTRUCTURED_API_KEY",
        "default_key": "default-dev-key (for development only)",
        "instructions": "Set a secure API key via the BYO_UNSTRUCTURED_API_KEY environment variable in production"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)