# GPT-OSS Hackathon Project: Resume Matching AI

This project uses OpenAI's `gpt-oss` (via Ollama) to score resumes against job descriptions.

## Setup

### 1. Install Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
