# app/utils/file_extractor.py

from io import BytesIO
from typing import Optional

import fitz  # PyMuPDF
import pdfplumber
from docx import Document


def extract_text_from_bytes(file_bytes: bytes, filename: Optional[str]) -> str:
    """
    Extract text from PDF, DOCX, or TXT file bytes.
    """
    if not filename:
        raise ValueError("Filename is required to detect file type.")

    if "." in filename:
        ext = filename.rsplit(".", 1)[1].lower()
    else:
        ext = ""

    if ext == "pdf":
        return _extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        return _extract_text_from_docx(file_bytes)
    elif ext == "txt":
        return _extract_text_from_txt(file_bytes)
    else:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF using PyMuPDF first, then pdfplumber as a fallback.
    """
    text = ""

    # Try PyMuPDF
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
    except Exception:
        text = ""

    text = text.strip()

    # If PyMuPDF got something, return it
    if text:
        return text

    # Fallback: pdfplumber
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

    return text.strip()


def _extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs).strip()


def _extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        # Fallback if encoding is not UTF-8
        return file_bytes.decode("latin-1", errors="ignore").strip()