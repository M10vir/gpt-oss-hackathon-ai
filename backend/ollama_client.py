import os, json, requests

OLLAMA_API = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/generate"
MODEL = os.getenv("MODEL", "gpt-oss:latest")

SYSTEM = (
    "You are an HR AI Assistant. "
    "Always return a single compact JSON object with keys: score (0-100 integer) and summary (string). "
    "No extra text, no code fences."
)

def _build_prompt(resume_text: str, job_description: str) -> str:
    return (
        f"{SYSTEM}\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Resume:\n{resume_text}\n\n"
        'Return exactly: {"score": 85, "summary": "2-line concise summary"}'
    )

def generate_score(resume_text: str, job_description: str) -> dict:
    prompt = _build_prompt(resume_text, job_description)
    r = requests.post(
        OLLAMA_API,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": { "temperature": 0, "num_ctx": 2048 }
        },
        timeout=600,  # allow long first-load on big models
    )
    r.raise_for_status()
    raw = r.json().get("response", "").strip()
    # strict parse, then fallback to extracting first {...}
    try:
        return json.loads(raw)
    except Exception:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(raw[s:e+1])
            except Exception:
                pass
    return {"score": 0, "summary": "Unable to parse model output"}
