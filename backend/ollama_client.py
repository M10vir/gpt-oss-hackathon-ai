import os
import json
import re
import requests
import threading

# ------------ Config ------------
OLLAMA_API = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/generate"
MODEL = os.getenv("MODEL", "llama3.2:3b")  # safe default for 16-GB M1 Pro

# serialize generations to avoid daemon contention oddities
_gen_lock = threading.Lock()

SYSTEM = (
    "You are an HR resume evaluator. "
    "Return ONLY strict JSON; no markdown, no extra text, no code fences."
)

# ------------ HTTP helper ------------
def _post(prompt: str, *, model: str, timeout: int, num_ctx: int, num_predict: int):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "1h",
        "format": "json",  # ask Ollama to emit valid JSON
        "options": {
            "temperature": 0,
            "num_ctx": num_ctx,
            "num_predict": num_predict,
            "repeat_penalty": 1.05,
            "top_k": 30,
        },
    }
    with _gen_lock:
        r = requests.post(OLLAMA_API, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()  # {"response": <dict or str>, ...}

# ------------ Utilities ------------
def warmup(model: str) -> str:
    """Spin up model quickly to avoid first-token latency."""
    data = _post("Say GO!", model=model, timeout=120, num_ctx=512, num_predict=12)
    resp = data.get("response")
    if isinstance(resp, dict):
        return "GO!"
    return (resp or "GO!").strip().replace("```", "")[:10] or "GO!"

def _strip_fences(s: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", (s or "").strip(), flags=re.IGNORECASE)

def _parse_json(raw):
    """Robustly parse model output into dict; rescue largest {...} if needed."""
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8", errors="ignore")
        except Exception:
            raw = str(raw)
    elif not isinstance(raw, str):
        try:
            return json.loads(json.dumps(raw))
        except Exception:
            raw = str(raw)

    raw = _strip_fences(raw)

    try:
        return json.loads(raw)
    except Exception:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e > s:
            try:
                return json.loads(raw[s : e + 1])
            except Exception:
                pass

    # fallback; caller will coerce fields safely
    return {"score": 0, "summary": "Unable to parse model output", "evidence": [], "risks": []}

# ------------ Public API ------------
def generate_explained_score(
    *,
    resume_text: str,
    job_description: str,
    model: str,
    timeout: int,
    num_ctx: int,
) -> dict:
    """
    Returns:
      { "score": int, "summary": str,
        "evidence": [ { "requirement": str, "match": str } ],
        "risks": [ str ] }
    """
    prompt = (
        f"{SYSTEM}\n"
        "Task: Score how well the RESUME matches the JOB DESCRIPTION.\n"
        "Rules: score is integer 0-100; summary <= 160 chars; evidence <= 3 items; risks <= 2 items. "
        "Use short phrases for evidence.match and risks. Return EXACTLY these keys.\n\n"
        f"JOB DESCRIPTION:\n{job_description}\n\n"
        f"RESUME:\n{resume_text}\n\n"
        'Output example: {"score": 85, "summary": "…", '
        '"evidence": [{"requirement":"Kubernetes","match":"2y AKS ops"}], '
        '"risks": ["No Terraform"]}'
    )
    data = _post(prompt, model=model, timeout=180, num_ctx=1024, num_predict=280)
    return _parse_json(data.get("response", ""))

def generate_explained_score_quick(
    *,
    resume_text: str,
    job_description: str,
    model: str,
    timeout: int = 120,
    num_ctx: int = 900,
) -> dict:
    """
    Lighter-weight variant for bias compare. Same JSON as generate_explained_score.
    """
    prompt = (
        f"{SYSTEM}\n"
        "Task: Score RESUME vs JOB DESCRIPTION.\n"
        "Return compact JSON: score(int 0-100), summary(<=120 chars), evidence(max 2), risks(max 1).\n\n"
        f"JOB DESCRIPTION:\n{job_description}\n\n"
        f"RESUME:\n{resume_text}\n\n"
        'Expected: {"score": 82, "summary": "…", "evidence":[{"requirement":"Kubernetes","match":"AKS"}], "risks":["No Terraform"]}'
    )
    data = _post(prompt, model=model, timeout=timeout, num_ctx=num_ctx, num_predict=200)
    return _parse_json(data.get("response", ""))

def generate_compare_scores_single_call(
    *,
    job_description: str,
    original_text: str,
    anonymized_text: str,
    model: str,
    timeout: int = 140,
    num_ctx: int = 1200,
) -> dict:
    """
    Strong comparative prompt (single call). Used as a fallback when two-call
    compare yields identical/empty scores.
    Returns ONLY:
      {
        "original": {"score": int, "summary": str},
        "anonymized": {"score": int, "summary": str},
        "delta": int
      }
    """
    prompt = (
        f"{SYSTEM}\n"
        "You will compare two versions of the same resume against a single job description.\n"
        "Version A is ORIGINAL (with identity & specific details). "
        "Version B is ANONYMIZED (identity removed; some specifics may be masked).\n"
        "Score each version 0–100 for relevance to the job; give a one-sentence summary "
        "for each; compute delta = A - B.\n"
        "Respond ONLY with valid JSON (no extra text):\n"
        '{"original":{"score":85,"summary":"..."},'
        '"anonymized":{"score":78,"summary":"..."},'
        '"delta":7}\n\n"'
        f"JOB DESCRIPTION:\n{job_description}\n\n"
        f"ORIGINAL (A):\n{original_text}\n\n"
        f"ANONYMIZED (B):\n{anonymized_text}\n"
    )
    data = _post(prompt, model=model, timeout=timeout, num_ctx=num_ctx, num_predict=240)
    return _parse_json(data.get("response", "")) 
