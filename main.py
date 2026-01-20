# app/main.py

from typing import Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.utils.file_extractor import extract_text_from_bytes
from app.utils.text_analyzer import analyze_resume_text

# from utils.file_extractor import extract_text_from_bytes
# from utils.text_analyzer import analyze_resume_text

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Resume Analyzer",
    description="Analyze resumes for degrees, PhD, department, experience, and publications.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def read_root():
    return {
        "message": "Resume Analyzer API is running.",
        "ui": "Open /ui in your browser to use the web interface.",
        "docs": "/docs",
    }


@app.get("/ui")
async def serve_ui():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="UI file not found.")
    return FileResponse(index_path)


@app.post("/analyze-resume")
async def analyze_resume(
    file: UploadFile = File(...),
    target_department: Optional[str] = None,
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_bytes(file_bytes, file.filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=500, detail="Error while extracting text.")

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract any text from the file. "
                   "It might be a scanned/image PDF.",
        )

    result = analyze_resume_text(text, target_department)
    result["text_preview"] = text[:8000]  # include extracted text
    return result