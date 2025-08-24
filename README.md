# GPT-OSS Resume Scorer 📝⚡

![Hackathon](https://img.shields.io/badge/Hackathon-GPT--OSS%20Hackathon-blueviolet?style=for-the-badge&logo=github)
![Project Status](https://img.shields.io/badge/Status-Ready%20to%20Submit-success?style=for-the-badge&logo=rocket)
![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen?style=for-the-badge&logo=github)

![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=for-the-badge&logo=llama)
![Platform](https://img.shields.io/badge/Platform-macOS%20M1-lightgrey?style=for-the-badge&logo=apple)
![GitHub](https://img.shields.io/badge/GitHub-Repo-black?style=for-the-badge&logo=github)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=for-the-badge&logo=pytest)
![Lint](https://img.shields.io/badge/Lint-Flake8-blue?style=for-the-badge&logo=python)

---

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

# Frontend (React)
cd frontend
npm install
npm run dev
