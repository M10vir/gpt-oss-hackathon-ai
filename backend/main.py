from fastapi import FastAPI
from routes.resume import router as resume_router

app = FastAPI()

app.include_router(resume_router, prefix="/resume")

@app.get("/")
def root():
    return {"message": "Welcome to GPT-OSS Hackathon backend"}
