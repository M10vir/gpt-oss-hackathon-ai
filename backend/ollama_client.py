import requests

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL = "gpt-oss"

def generate_score(resume_text: str, job_description: str) -> dict:
    prompt = f"""
    You are an HR AI Assistant.

    Job Description: {job_description}

    Resume: {resume_text}

    Score the resume’s relevance to the job from 0 to 100 and provide a 2-line summary.
    Return your response in JSON like:
    {{
        "score": 85,
        "summary": "Highly relevant with 5 years of cloud experience"
    }}
    """

    response = requests.post(OLLAMA_API, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })

    try:
        return eval(response.json()['response'])
    except Exception:
        return {"score": 0, "summary": "Error parsing result"}
