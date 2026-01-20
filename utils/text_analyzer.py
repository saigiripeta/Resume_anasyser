# app/utils/text_analyzer.py

from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import date

# ---------- Degree detection patterns ----------

DEGREE_PATTERNS: Dict[str, str] = {
    # PhD / Doctorate
    r"\bphd\b": "PhD",
    r"\bph\.?\s*d\.?\b": "PhD",          # "Ph. D", "Ph.D", "Ph D"
    r"doctor of philosophy": "PhD",
    r"doctoral (degree|studies|candidate)": "PhD",

    # Master's level
    r"\bm\.?\s*tech\b": "Master",
    r"\bmaster of technology\b": "Master",
    r"\bm\.?\s*e\b": "Master",
    r"\bmaster of engineering\b": "Master",
    r"\bm\.?\s*sc\b": "Master",
    r"\bmaster of science\b": "Master",
    r"\bm\.?\s*a\b": "Master",          # "M.A", "MA"
    r"\bmaster of arts\b": "Master",
    r"\bmca\b": "Master",
    r"\bmaster of computer applications\b": "Master",
    r"\bmba\b": "Master",
    r"\bmaster of business administration\b": "Master",

    # Bachelor's level
    r"\bb\.?\s*tech\b": "Bachelor",
    r"\bbtech\b": "Bachelor",
    r"\bb\.?\s*e\b": "Bachelor",
    r"\bbachelor of engineering\b": "Bachelor",
    r"\bb\.?\s*sc\b": "Bachelor",
    r"\bbachelor of science\b": "Bachelor",
    r"\bb\.?\s*a\b": "Bachelor",        # "B.A", "BA"
    r"\bbachelor of arts\b": "Bachelor",
    r"\bb\.?\s*com\b": "Bachelor",
    r"\bbachelor of commerce\b": "Bachelor",

    # Diploma / School
    r"\bdiploma\b": "Diploma",
    r"higher secondary": "HighSchool",
    r"high school": "HighSchool",
    r"\bssc\b": "HighSchool",
    r"\bhsc\b": "HighSchool",
}

DEGREE_PRIORITY: Dict[str, int] = {
    "HighSchool": 1,
    "Diploma": 2,
    "Bachelor": 3,
    "Master": 4,
    "PhD": 5,
}

# ---------- Department keywords ----------

DEPARTMENT_KEYWORDS: Dict[str, str] = {
    # English / Humanities
    "english language and literature": "English",
    "department of english language and literature": "English",
    "english literature": "English",
    "department of english": "English",
    "m.a (english)": "English",
    "ma (english)": "English",
    "b.a (english)": "English",
    "b.a (english literature)": "English",
    "ba (english)": "English",
    "english": "English",   # generic

    # Computer Science / IT
    "computer science and engineering": "Computer Science",
    "computer science & engineering": "Computer Science",
    "computer science": "Computer Science",
    "information technology": "Computer Science",
    "information systems": "Computer Science",
    "cse": "Computer Science",
    "it engineering": "Computer Science",
    "data science": "Computer Science",
    "data structures": "Computer Science",
    "algorithms": "Computer Science",
    "machine learning": "Computer Science",
    "artificial intelligence": "Computer Science",
    "operating systems": "Computer Science",
    "database systems": "Computer Science",
    "databases": "Computer Science",

    # Electronics / Electrical
    "electronics and communication": "Electronics",
    "electronics & communication": "Electronics",
    "ece": "Electronics",
    "electronics engineering": "Electronics",
    "vlsi": "Electronics",
    "signal processing": "Electronics",
    "embedded systems": "Electronics",
    "electrical engineering": "Electrical",
    "eee": "Electrical",

    # Mechanical
    "mechanical engineering": "Mechanical",
    "thermal engineering": "Mechanical",
    "thermodynamics": "Mechanical",
    "fluid mechanics": "Mechanical",

    # Civil
    "civil engineering": "Civil",
    "structural engineering": "Civil",

    # Sciences
    "applied physics": "Physics",
    "physics": "Physics",
    "applied mathematics": "Mathematics",
    "mathematics": "Mathematics",
    "chemistry": "Chemistry",
    "biotechnology": "Biotechnology",
}

EDU_SECTION_TITLES: List[str] = [
    "education",
    "educational qualification",
    "educational qualifications",
    "academic background",
    "academic qualifications",
    "qualifications",
]

# ---------- Helpers: education section ----------

def extract_education_section(text: str) -> str:
    """
    Find the 'Education' heading and return text from there until the end.
    If not found, return the whole text.
    """
    lines = text.splitlines()
    if not lines:
        return text

    start_idx: Optional[int] = None
    for i, line in enumerate(lines):
        ll = line.strip().lower()
        if any(title in ll for title in EDU_SECTION_TITLES):
            start_idx = i
            break

    if start_idx is None:
        return text

    section = "\n".join(lines[start_idx:]).strip()
    return section or text

# ---------- Degree detail extraction ----------

def detect_degrees_simple(text: str) -> List[str]:
    """
    Simple detection of degree *types* used as fallback.
    """
    text_low = text.lower()
    found: List[str] = []
    for pattern, degree_name in DEGREE_PATTERNS.items():
        if re.search(pattern, text_low):
            if degree_name not in found:
                found.append(degree_name)
    return found


def determine_highest_degree(degrees: List[str]) -> str:
    if not degrees:
        return "Unknown"
    best_degree = "Unknown"
    best_priority = 0
    for d in degrees:
        priority = DEGREE_PRIORITY.get(d, 0)
        if priority > best_priority:
            best_priority = priority
            best_degree = d
    return best_degree


def get_phd_status(text: str) -> Optional[str]:
    """
    Try to infer PhD status from surrounding text; returns one of:
    'Awarded', 'Thesis Submitted', 'Pursuing', or None.
    """
    low = text.lower()
    statuses: List[str] = []

    for m in re.finditer(r"ph\.?\s*d\.?|phd", low):
        window = low[max(0, m.start() - 100): m.end() + 100]
        if "awarded" in window:
            return "Awarded"
        if "thesis submitted" in window or "submitted thesis" in window:
            statuses.append("Thesis Submitted")
        if any(w in window for w in ["pursuing", "ongoing", "currently", "in progress"]):
            statuses.append("Pursuing")

    return statuses[0] if statuses else None


def extract_years_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract start and end/passing year from a piece of text.
    """
    range_pattern = re.compile(
        r"(19|20)\d{2}\s*[-–]\s*(\d{4}|Present|present|Ongoing|ongoing|Pursuing|pursuing|Till Date|till date|Current|current)"
    )
    single_year_pattern = re.compile(r"\b(19|20)\d{2}\b")

    m = range_pattern.search(text)
    if m:
        start_year = int(m.group(0)[0:4])
        end_part = m.group(0).split("-")[-1].strip()
        if end_part.isdigit():
            end_year = int(end_part)
        else:
            end_year = None  # still ongoing
        return start_year, end_year

    # Fallback: any single year (treat as end/passing year)
    m2 = single_year_pattern.findall(text)
    if m2:
        # take the last year in the text
        years = re.findall(r"(19|20)\d{2}", text)
        if years:
            last = years[-1]
            return None, int(last)
    return None, None


def extract_field_and_institution(block_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to extract field of study and institution from a degree block text.
    """
    field = None
    institution = None

    # Field from parentheses
    paren = re.search(r"\(([^)]+)\)", block_text)
    if paren:
        raw = paren.group(1).strip()
        if len(raw) > 2 and not re.search(r"\d{2,4}", raw):
            field = raw

    # Field from "in X"
    if field is None:
        low = block_text.lower()
        if " in " in low:
            idx = low.find(" in ")
            after_orig = block_text[idx + 4:]
            for sep in [",", "|", "-", "–", " at "]:
                if sep in after_orig:
                    after_orig = after_orig.split(sep)[0]
            f = after_orig.strip(" ,.-–")
            if len(f) > 2 and not re.search(r"\d{2,4}", f):
                field = f

    # Institution: look for University / College / Institute / School
    inst_match = re.search(
        r"([A-Z][A-Za-z&. ]+(University|College|Institute|School|Academy))",
        block_text,
    )
    if inst_match:
        institution = inst_match.group(1).strip()

    return field, institution


def extract_degrees_detail(education_text: str, full_text: str) -> List[Dict[str, Any]]:
    """
    Extract detailed degree info:
    degree_type, field_of_study, institution, start_year, end_year, status.
    """
    lines = [ln.strip() for ln in education_text.splitlines() if ln.strip()]
    if not lines:
        return []

    blocks: List[List[str]] = []
    current: List[str] = []

    # Heuristic: start a new block when a line has a degree keyword
    for line in lines:
        ll = line.lower()
        has_degree_kw = any(re.search(pat, ll) for pat in DEGREE_PATTERNS.keys())
        if has_degree_kw:
            if current:
                blocks.append(current)
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        blocks.append(current)

    phd_status_global = get_phd_status(full_text)

    detailed: List[Dict[str, Any]] = []

    for block in blocks:
        full = " ".join(block)
        full_low = full.lower()

        # Degree type: use simple detector on this block
        degrees_here = detect_degrees_simple(full)
        if not degrees_here:
            continue
        degree_type = determine_highest_degree(degrees_here)

        start_year, end_year = extract_years_from_text(full)
        field, institution = extract_field_and_institution(full)

        # Default status
        status = "Completed"
        if any(w in full_low for w in ["pursuing", "ongoing", "currently", "in progress"]):
            status = "Pursuing"
        if end_year is None and start_year is not None:
            # likely ongoing
            status = "Pursuing"

        phd_thesis_submitted = False
        phd_awarded = False

        if degree_type == "PhD":
            # Override from global PhD status if available
            if phd_status_global == "Awarded":
                status = "Awarded"
                phd_awarded = True
            elif phd_status_global == "Thesis Submitted":
                status = "Thesis Submitted"
                phd_thesis_submitted = True
            elif phd_status_global == "Pursuing":
                status = "Pursuing"

            # If not determined globally, still look locally
            if "thesis submitted" in full_low:
                status = "Thesis Submitted"
                phd_thesis_submitted = True
            if "awarded" in full_low:
                status = "Awarded"
                phd_awarded = True

        detailed.append(
            {
                "degree_type": degree_type,
                "raw_text": full,
                "field_of_study": field,
                "institution": institution,
                "start_year": start_year,
                "end_year": end_year,
                "status": status,
                "phd_thesis_submitted": phd_thesis_submitted if degree_type == "PhD" else None,
                "phd_awarded": phd_awarded if degree_type == "PhD" else None,
            }
        )

    return detailed

# ---------- Department from fields ----------

def infer_department_from_fields(fields_of_study: List[str]) -> str:
    for field in fields_of_study:
        f_low = field.lower()
        for keyword, department in DEPARTMENT_KEYWORDS.items():
            if keyword in f_low:
                return department
    return "Unknown"


def infer_department_from_text(text: str) -> str:
    text_low = text.lower()
    for keyword, department in DEPARTMENT_KEYWORDS.items():
        if keyword in text_low:
            return department
    return "Unknown"

# ---------- Scoring ----------

def score_resume(
    has_phd_flag: bool,
    highest_degree: str,
    department: str,
    target_department: Optional[str] = None,
) -> int:
    score = 0
    if has_phd_flag:
        score += 50
    elif highest_degree == "Master":
        score += 35
    elif highest_degree == "Bachelor":
        score += 25
    elif highest_degree in ("Diploma", "HighSchool"):
        score += 15
    else:
        score += 10

    if target_department:
        if department.lower() == target_department.lower():
            score += 30
        else:
            score += 10
    return score

# ---------- Personal info ----------

def extract_email(text: str) -> Optional[str]:
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text: str) -> Optional[str]:
    lines = text.splitlines()
    top = "\n".join(lines[:15])
    candidates = re.findall(r"(\+?\d[\d\s\-]{8,}\d)", top)
    for cand in candidates:
        digits = re.sub(r"\D", "", cand)
        if 10 <= len(digits) <= 13:
            return cand.strip()
    return None


def extract_name(text: str) -> Optional[str]:
    for line in text.splitlines():
        name = line.strip()
        if not name:
            continue
        low = name.lower()
        prefixes = ["mr ", "ms ", "mrs ", "dr ", "prof. ", "prof "]
        for p in prefixes:
            if low.startswith(p):
                name = name[len(p):].strip()
                break
        if "@" not in name and not re.search(r"\d", name):
            return name
        else:
            return name
    return None


def extract_location(text: str) -> Optional[str]:
    lines = text.splitlines()
    for line in lines[:15]:
        if "india" in line.lower():
            if "|" in line:
                part = line.split("|")[-1].strip()
                return part
            m = re.search(r"([A-Za-z ]+,\s*India\b)", line, re.IGNORECASE)
            if m:
                return m.group(1).strip()
    return None


def extract_current_organization(text: str) -> Optional[str]:
    lines = text.splitlines()
    work_start = None
    for i, line in enumerate(lines):
        if "work experience" in line.lower():
            work_start = i
            break
    start_idx = work_start if work_start is not None else 0

    # Try "currently working" / "present"
    for i in range(start_idx, len(lines)):
        ll = lines[i].lower()
        if "currently working" in ll or "present" in ll:
            for j in range(i + 1, min(i + 5, len(lines))):
                candidate = lines[j].strip()
                if candidate:
                    return candidate

    # Fallback: first organization-like line after WORK EXPERIENCE
    org_keywords = ["university", "college", "institute", "school", "company", "pvt", "ltd", "inc"]
    for i in range(start_idx, min(start_idx + 20, len(lines))):
        ll = lines[i].lower()
        if any(k in ll for k in org_keywords):
            cand = lines[i].strip()
            if cand:
                return cand
    return None

# ---------- Experience breakdown ----------

def calculate_experience_breakdown(text: str) -> Dict[str, Optional[float]]:
    """
    Parse date ranges and approximate teaching vs industry vs total experience in years.
    """
    month_pattern = (
        r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)"
    )
    range_pattern = (
        rf"(?P<from_month>{month_pattern})\s+(?P<from_year>\d{{4}})\s*[-–]\s*"
        rf"(?:(?P<to_month>{month_pattern})\s+(?P<to_year>\d{{4}})|"
        r"(?P<to_label>Present|Currently Working|Current|Till Date|Now))"
    )

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    teaching_keywords = [
        "professor", "assistant professor", "associate professor",
        "lecturer", "teacher", "faculty", "school", "college", "university",
        "institute", "academy"
    ]
    industry_keywords = [
        "developer", "software", "engineer", "company", "pvt", "ltd",
        "solutions", "consultant", "analyst", "manager", "industry",
        "it services", "technologies", "firm", "corporation"
    ]

    teaching_months = 0
    industry_months = 0
    other_months = 0

    today = date.today()

    for m in re.finditer(range_pattern, text, re.IGNORECASE):
        fm_str = m.group("from_month")[:3].lower()
        from_month = month_map.get(fm_str)
        from_year = int(m.group("from_year"))
        if from_month is None:
            continue

        if m.group("to_month"):
            tm_str = m.group("to_month")[:3].lower()
            to_month = month_map.get(tm_str, today.month)
            to_year = int(m.group("to_year"))
        else:
            to_year = today.year
            to_month = today.month

        months = (to_year - from_year) * 12 + (to_month - from_month)
        if months <= 0:
            continue

        # Classify this period by context around the match
        ctx = text[max(0, m.start() - 120): m.end() + 120].lower()
        if any(kw in ctx for kw in teaching_keywords):
            teaching_months += months
        elif any(kw in ctx for kw in industry_keywords):
            industry_months += months
        else:
            other_months += months

    def months_to_years(m: int) -> Optional[float]:
        if m <= 0:
            return None
        return round(m / 12.0, 1)

    total_months = teaching_months + industry_months + other_months

    return {
        "teaching_years": months_to_years(teaching_months),
        "industry_years": months_to_years(industry_months),
        "other_years": months_to_years(other_months),
        "total_years": months_to_years(total_months),
    }

# ---------- Publications breakdown ----------

def count_publications_breakdown(text: str) -> Dict[str, int]:
    """
    Parse the 'DETAILS OF RESEARCH PUBLICATIONS/BOOKS/ARTICLE/PRESENTATIONS' section,
    and approximate counts for total, articles, books, conference papers.
    """
    lines = text.splitlines()
    start = None
    end = len(lines)

    for i, line in enumerate(lines):
        if "details of research publications" in line.lower():
            start = i
            break
    if start is None:
        return {
            "total": 0,
            "articles": 0,
            "books": 0,
            "conferences": 0,
        }

    for j in range(start + 1, len(lines)):
        if "refresher courses" in lines[j].lower():
            end = j
            break

    total = 0
    articles = 0
    books = 0
    conferences = 0

    for line in lines[start:end]:
        if not re.match(r"^\s*\d+\s", line):
            continue
        total += 1
        low = line.lower()
        if "book" in low or "isbn" in low or "chapter" in low:
            books += 1
        elif any(k in low for k in ["journal", "volume", "issue", "issn", "paper published"]):
            articles += 1
        elif "presented" in low and any(k in low for k in ["conference", "seminar"]):
            conferences += 1
        else:
            # if nothing matched, treat as article by default
            articles += 1

    return {
        "total": total,
        "articles": articles,
        "books": books,
        "conferences": conferences,
    }

# ---------- MAIN PUBLIC FUNCTION ----------

def analyze_resume_text(
    text: str, target_department: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze resume text and return structured result.
    """
    education_text = extract_education_section(text)

    # Degree details
    degrees_info = extract_degrees_detail(education_text, text)
    degree_types = [d["degree_type"] for d in degrees_info]
    degrees_detected = sorted(set(degree_types), key=lambda d: DEGREE_PRIORITY.get(d, 0), reverse=True)
    highest_deg = determine_highest_degree(degrees_detected)
    has_phd_flag = "PhD" in degrees_detected

    # PhD years from degrees_info
    phd_start_year = None
    phd_end_year = None
    for d in degrees_info:
        if d["degree_type"] == "PhD":
            phd_start_year = d.get("start_year")
            phd_end_year = d.get("end_year")
            break

    # Fields of study from degree info
    fields_of_study: List[str] = []
    seen_fields = set()
    for d in degrees_info:
        f = d.get("field_of_study")
        if f and f.lower() not in seen_fields:
            seen_fields.add(f.lower())
            fields_of_study.append(f)

    department = infer_department_from_fields(fields_of_study)
    if department == "Unknown":
        department = infer_department_from_text(text)

    # Score
    score = score_resume(has_phd_flag, highest_deg, department, target_department)

    # Personal details
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    location = extract_location(text)
    current_org = extract_current_organization(text)

    # Experience
    exp_breakdown = calculate_experience_breakdown(text)

    # Publications
    pubs = count_publications_breakdown(text)

    result: Dict[str, Any] = {
        "name": name,
        "email": email,
        "phone": phone,
        "current_location": location,
        "current_organization": current_org,

        "teaching_experience_years": exp_breakdown["teaching_years"],
        "industry_experience_years": exp_breakdown["industry_years"],
        "other_experience_years": exp_breakdown["other_years"],
        "total_experience_years": exp_breakdown["total_years"],

        "publications_total_count": pubs["total"],
        "research_articles_count": pubs["articles"],
        "books_count": pubs["books"],
        "conference_papers_count": pubs["conferences"],

        "has_phd": has_phd_flag,
        "highest_degree": highest_deg,
        "phd_start_year": phd_start_year,
        "phd_end_year": phd_end_year,

        "department": department,
        "degrees_detected": degrees_detected,
        "degrees_info": degrees_info,
        "fields_of_study": fields_of_study,
        "score": score,
    }
    return result