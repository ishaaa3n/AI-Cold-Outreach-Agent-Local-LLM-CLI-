"""Extract text from a resume file (PDF / DOCX / TXT)."""
from __future__ import annotations

from pathlib import Path


def extract_resume_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
    if suffix == ".docx":
        import docx2txt

        return (docx2txt.process(str(path)) or "").strip()
    return path.read_text(encoding="utf-8", errors="ignore").strip()
