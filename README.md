# Resume Analyzer (Open Source, No Paid APIs)

This project analyzes resumes to:

- Detect degrees and highest qualification
- Check if the candidate has a PhD
- Infer department (e.g., Computer Science, Mechanical)
- Compute a simple score

## Tech Stack

- Python
- FastAPI
- pdfplumber (for PDFs)
- python-docx (for DOCX)
- No external paid APIs

## Setup

```bash
# 1. Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application 
uvicorn app.main:app --reload
UI: http://127.0.0.1:8000/ui
API docs (Swagger): http://127.0.0.1:8000/docs
