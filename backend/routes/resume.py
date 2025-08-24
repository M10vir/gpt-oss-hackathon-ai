from fastapi import APIRouter, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from backend.ollama_client import (
    generate_explained_score,
    generate_explained_score_quick,
    generate_compare_scores_single_call,
    warmup,
)
import os
import re
import fitz  # PyMuPDF

router = APIRouter(tags=["resume"])

# Budgets tuned for speed/stability on 16-GB Macs
MAX_CHARS = 40_000
MAX_CHARS_COMPARE = 1_600

MODEL = os.getenv("MODEL", "llama3.2:3b")
MODEL_COMPARE = os.getenv("MODEL_COMPARE", MODEL)

# ---------- Health & Warmup ----------
@router.get("/health")
def health():
    return {"status": "ok", "model": MODEL, "model_compare": MODEL_COMPARE}

@router.post("/warmup")
def warmup_route():
    try:
        cmp_resp = warmup(MODEL_COMPARE)
        main_resp = warmup(MODEL)
        return {
            "status": "ok",
            "compare_response": cmp_resp,
            "response": main_resp,
            "model": MODEL,
            "model_compare": MODEL_COMPARE,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": f"Warmup failed: {e}", "model": MODEL, "model_compare": MODEL_COMPARE},
        )

# ---------- Helpers ----------
def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    finally:
        if doc:
            doc.close()

def _prioritize_sections(text: str, limit: int) -> str:
    lower = text.lower()

    def grab(*names):
        for n in names:
            i = lower.find(n)
            if i != -1:
                return text[i : i + 1600]
        return ""

    chunks = [
        grab("summary", "professional summary", "profile"),
        grab("skills", "technical skills"),
        grab("experience", "work experience", "employment"),
        text,
    ]
    combined = "\n\n".join([c for c in chunks if c]).strip()
    return combined[:limit] + ("\n...[truncated]" if len(combined) > limit else "")

# Heavier anonymization (PII, simple names, locations, social links).
_LOCATION_WORDS = r"(qatar|india|germany|usa|u\.s\.a|uk|u\.k|england|canada|uae|dubai|saudi|australia|singapore|france|italy|spain)"

def _anon(t: str) -> str:
    s = t
    # Emails / phones / years
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", s)
    s = re.sub(r"\+?\d[\d\s().-]{7,}\d", "[PHONE]", s)
    s = re.sub(r"\b(19|20)\d{2}\b", "[YEAR]", s)
    # Social links & usernames
    s = re.sub(r"https?://(www\.)?(linkedin|github|gitlab|twitter|x)\.[^\s]+", "[PROFILE]", s, flags=re.I)
    # Locations / nationalities (coarse)
    s = re.sub(rf"\b{_LOCATION_WORDS}\b", "[LOCATION]", s, flags=re.I)
    # Replace full-name patterns and first-line name
    lines = s.splitlines()
    if lines:
        lines[0] = "Candidate"
    s = re.sub(r"\b[A-Z][a-z]{2,15}\s[A-Z][a-z]{2,15}\b", "Candidate", s)
    return s

def _to_int(v):
    try:
        return int(v)
    except Exception:
        try:
            return int(str(v).strip().split()[0].replace(".", ""))
        except Exception:
            return 0

# ---------- Endpoints ----------
@router.post("/upload")
async def upload_resume(
    file: UploadFile,
    job_title: str = Form(...),
    job_description: str = Form(...),
    anonymize: bool = Form(False),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if file.content_type not in ("application/pdf", "application/octet-stream", "text/plain"):
        raise HTTPException(status_code=400, detail="Upload a PDF (or .txt for testing).")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = (
            content.decode("utf-8", errors="ignore")
            if file.content_type == "text/plain"
            else _extract_text_from_pdf(content)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    text = _prioritize_sections(text, MAX_CHARS)
    text_for_scoring = _anon(text) if anonymize else text

    try:
        result = generate_explained_score(
            resume_text=text_for_scoring,
            job_description=job_description,
            model=MODEL,
            timeout=180,
            num_ctx=1024,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": f"Model inference failed: {e}", "model": MODEL},
        )

    score = _to_int(result.get("score", 0))
    summary = str(result.get("summary", ""))[:600]
    evidence = result.get("evidence") or []
    risks = result.get("risks") or []
    note = "ok" if score != 0 or "Unable to parse" not in summary else "parser_fallback"

    return {
        "filename": file.filename,
        "job_title": job_title,
        "relevance_score": score,
        "summary": summary,
        "evidence": evidence[:3],
        "risks": risks[:2],
        "model": MODEL,
        "anonymized": bool(anonymize),
        "note": note,
    }

@router.post("/compare")
async def compare_resume(
    file: UploadFile,
    job_title: str = Form(...),
    job_description: str = Form(...),
):
    """
    Bias check: (1) score ORIGINAL and ANONYMIZED separately (quick scorer),
    then (2) if both scores look identical/empty, run a single-call comparative
    fallback that often teases out subtle differences.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if file.content_type not in ("application/pdf", "application/octet-stream", "text/plain"):
        raise HTTPException(status_code=400, detail="Upload a PDF (or .txt).")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = (
            content.decode("utf-8", errors="ignore")
            if file.content_type == "text/plain"
            else _extract_text_from_pdf(content)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    # Compact slice for speed
    text_small = _prioritize_sections(text, MAX_CHARS_COMPARE)
    text_anon = _anon(text_small)

    # --- Path A: two-call quick scores
    try:
        r_orig = generate_explained_score_quick(
            resume_text=text_small,
            job_description=job_description,
            model=MODEL_COMPARE,
            timeout=120,
            num_ctx=900,
        )
        r_anon = generate_explained_score_quick(
            resume_text=text_anon,
            job_description=job_description,
            model=MODEL_COMPARE,
            timeout=120,
            num_ctx=900,
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": f"Model inference failed: {e}", "model": MODEL_COMPARE},
        )

    s1 = _to_int(r_orig.get("score", 0))
    s2 = _to_int(r_anon.get("score", 0))
    delta = s1 - s2

    used_fallback = False

    # If identical/empty, try a single-call, stronger comparative prompt
    if (s1 == 0 and s2 == 0) or (s1 == s2):
        try:
            comp = generate_compare_scores_single_call(
                job_description=job_description,
                original_text=text_small,
                anonymized_text=text_anon,
                model=MODEL_COMPARE,
                timeout=140,
                num_ctx=1200,
            )
            o = comp.get("original") or {}
            a = comp.get("anonymized") or {}
            s1b = _to_int(o.get("score", s1))
            s2b = _to_int(a.get("score", s2))
            # Only adopt fallback if it looks sane
            if (s1b != 0 or s2b != 0) and (s1b != s2b or s1 == s2):
                s1, s2 = s1b, s2b
                delta = s1 - s2
                r_orig = {"summary": str(o.get("summary", ""))[:300], "score": s1}
                r_anon = {"summary": str(a.get("summary", ""))[:300], "score": s2}
                used_fallback = True
        except Exception:
            pass  # keep two-call result

    return {
        "filename": file.filename,
        "job_title": job_title,
        "original": {"score": s1, "summary": str(r_orig.get("summary", ""))[:300]},
        "anonymized": {"score": s2, "summary": str(r_anon.get("summary", ""))[:300]},
        "delta": delta,
        "model": MODEL,
        "model_compare": MODEL_COMPARE,
        "note": "fallback_compare_used" if used_fallback else "two_call_compare",
    } 
