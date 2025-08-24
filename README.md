# GPT-OSS Resume Scorer 📝⚡

**AI-powered Resume Scoring & Bias-Aware Comparison**  
Built with **FastAPI + React + Ollama (llama3.2:3b)**

---

## 🚀 Overview
Hiring processes often rely on automated resume screeners — but they can be biased, opaque, or slow.  
Our **GPT-OSS Resume Scorer** solves this by providing:

- **Fast local inference** (via [Ollama](https://ollama.ai/))  
- **Explainable scoring** of resumes vs job descriptions  
- **Bias-aware anonymization** & side-by-side comparison  
- **Fair, transparent outputs** with evidence and missing skills

This project was built for the **Hackathon** to demonstrate how OSS AI can empower **ethical recruitment**.

---

## ✨ Features
- **Upload & Score**: Upload a PDF resume and compare it with a job description.
- **Explainability**: See not just a score, but also:
  - ✅ **Evidence** (skills & experiences found)  
  - ⚠️ **Risks / Missing** (gaps relative to the job description)  
- **Bias Compare**:
  - Compare **original** vs **anonymized** resumes (removing names, emails, phone, etc.)
  - Detect potential bias if anonymized scores differ.
- **Warmup Button**: Preloads the model so judges won’t wait for cold start.

---

## 🖼️ Screenshots

### Upload & Score
![Screenshot 1 – Upload & Score UI](screenshots/upload_score.png)

### Bias Compare
![Screenshot 2 – Bias Compare Result](screenshots/bias_compare.png)

---

## 🛠️ Tech Stack
- **Frontend**: React + Vite  
- **Backend**: FastAPI (Python)  
- **AI Inference**: Ollama (llama3.2:3b, local model)  
- **PDF Parsing**: PyMuPDF (`fitz`)  
- **Environment Config**: dotenv  

---

## ⚡ Quickstart

### 1. Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run backend
uvicorn backend.main:app --reload --reload-dir backend
