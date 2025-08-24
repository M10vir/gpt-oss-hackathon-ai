# backend/main.py
import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv

# load env
load_dotenv(find_dotenv())

from backend.routes.resume import router as resume_router  # routes
from backend.ollama_client import warmup as ollama_warmup  # <-- warmup(model)

APP_TITLE = "GPT-OSS Hackathon Backend"
APP_VERSION = "0.1.0"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("MODEL", "llama3.2:3b")
MODEL_COMPARE = os.getenv("MODEL_COMPARE", MODEL)
AUTO_WARMUP = os.getenv("AUTO_WARMUP", "1")  # set to "0" to disable

_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ORIGINS = [o.strip() for o in os.getenv("BACKEND_CORS_ORIGINS", "").split(",") if o.strip()] or _default_origins

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router, prefix="/resume")

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL, "ollama_url": OLLAMA_URL}

@app.get("/")
def root():
    return {"message": "Welcome to GPT-OSS Hackathon backend", "model": MODEL, "ollama_url": OLLAMA_URL}

async def _background_warm():
    try:
        logging.info("Warming compare model: %s", MODEL_COMPARE)
        ollama_warmup(MODEL_COMPARE)
        logging.info("Warming main model: %s", MODEL)
        ollama_warmup(MODEL)
        logging.info("Warmup done.")
    except Exception as e:
        logging.warning("Warmup failed: %s", e)

@app.on_event("startup")
async def on_startup():
    logging.basicConfig(level=logging.INFO)
    logging.info("=== Backend started ===")
    logging.info("MODEL=%s", MODEL)
    logging.info("MODEL_COMPARE=%s", MODEL_COMPARE)
    logging.info("OLLAMA_URL=%s", OLLAMA_URL)
    logging.info("CORS_ORIGINS=%s", CORS_ORIGINS)
    if AUTO_WARMUP == "1":
        asyncio.create_task(_background_warm()) 
