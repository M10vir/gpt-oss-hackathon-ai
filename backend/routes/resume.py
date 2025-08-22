from fastapi import APIRouter, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from backend.ollama_client import generate_score  # absolute import
import fitz  # PyMuPDF

router = APIRouter(tags=["resume"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/upload")
async def upload_resume(
    file: UploadFile,
    job_title: str = Form(...),
    job_description: str = Form(...),
):
    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse PDF: {e}")

    try:
        result = generate_score(text, job_description)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY,
                            content={"error": f"Model inference failed: {str(e)}"})

    try:
        score = int(result.get("score", 0))
    except Exception:
        score = 0
    summary = str(result.get("summary", ""))[:600]

    return {
        "filename": file.filename,
        "job_title": job_title,
        "relevance_score": score,
        "summary": summary,
    }

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    finally:
        if doc is not None:
            doc.close() 
