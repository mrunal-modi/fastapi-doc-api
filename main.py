from fastapi import FastAPI, File, UploadFile
import pdfplumber
import pypdf

app = FastAPI()

@app.post("/extract-text/")
async def extract_text(file: UploadFile = File(...)):
    if file.filename.endswith(".pdf"):
        pdf_reader = pypdf.PdfReader(file.file)
        text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        return {"filename": file.filename, "text": text}
    
    return {"error": "Only PDFs are supported"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)