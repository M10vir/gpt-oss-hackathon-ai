# backend/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env no matter where uvicorn is launched from
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Absolute import (run from repo root: `python -m uvicorn backend.main:app ...`)
from backend.routes.resume import router as resume_router

APP_TITLE = "GPT-OSS Hackathon Backend"
APP_VERSION = "0.1.0"

# Read config from env (with sensible defaults)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("MODEL", "gpt-oss:latest")

# CORS: comma-separated list allowed via env; fall back to local dev defaults
_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ORIGINS = [
    o.strip() for o in os.getenv("BACKEND_CORS_ORIGINS", "").split(",")
    if o.strip()
] or _default_origins

# App
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(resume_router, prefix="/resume")

# Health (root-level)
@app.get("/health")
def health():
    return {"status": "ok"}

# Root
@app.get("/")
def root():
    return {
        "message": "Welcome to GPT-OSS Hackathon backend",
        "model": MODEL,
        "ollama_url": OLLAMA_URL,
    }

# Log effective config at startup (useful in dev & during judging)
@app.on_event("startup")
async def on_startup():
    logging.basicConfig(level=logging.INFO)
    logging.info("=== Backend started ===")
    logging.info("MODEL=%s", MODEL)
    logging.info("OLLAMA_URL=%s", OLLAMA_URL)
    logging.info("CORS_ORIGINS=%s", CORS_ORIGINS)
