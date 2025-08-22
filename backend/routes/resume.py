from fastapi import APIRouter, UploadFile, Form
from ollama_client import generate_score
import fitz  # PyMuPDF
from pathlib import Path

router = APIRouter()

@router.post("/upload")
async def upload_resume(file: UploadFile, job_title: str = Form(...), job_description: str = Form(...)):
    content = await file.read()
    text = extract_text_from_pdf(content)
    result = generate_score(text, job_description)
    return {
        "filename": file.filename,
        "job_title": job_title,
        "relevance_score": result.get("score", 0),
        "summary": result.get("summary", "")
    }

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join([page.get_text() for page in doc])
