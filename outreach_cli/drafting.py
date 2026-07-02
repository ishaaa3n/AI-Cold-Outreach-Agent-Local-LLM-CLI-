"""Turn (resume profile + contact) into a personalized email via local Ollama.

Uses the OpenAI-compatible endpoint Ollama exposes, so it's just the `openai`
client pointed at localhost — no cloud calls, fully offline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from openai import OpenAI

from .contacts import Contact
from .research import search_company

_PLACEHOLDER_RE = re.compile(r"[\[{][A-Za-z ._-]{2,30}[\]}]")


@dataclass
class Email:
    subject: str
    body: str


class Drafter:
    def __init__(
        self,
        base_url: str,
        model: str,
        sender_name: str,
        signature: str,
        tone: str,
        subject_template: str = "AI/ML & Backend Engineering Opportunities",
        temperature: float = 0.0,
        api_key: str = "ollama",
    ):
        # api_key is ignored by local Ollama; set it for cloud (e.g. Groq).
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model
        self._sender = sender_name
        self._signature = signature.rstrip()
        self._tone = tone
        self._subject_template = subject_template
        self._temperature = temperature
        self._profile: str | None = None
        self._research_cache: dict[str, str] = {}

    def research_company(self, company: str) -> str:
        """Web-search the company and distill ONE honest fact for personalization.
        Returns "" if nothing concrete is found (never fabricates). Cached per run."""
        if not company:
            return ""
        if company in self._research_cache:
            return self._research_cache[company]
        raw = search_company(company)
        info = ""
        if raw:
            prompt = (
                f"From the web-search text about the company '{company}', write ONE short "
                "factual sentence describing what the company does (its domain/products/"
                "focus) that could personalize a cold email. Use ONLY facts clearly present "
                "in the text — do not guess. If the text has no concrete facts about this "
                "specific company, reply with exactly: NONE\n\n"
                f"SEARCH TEXT:\n{raw}"
            )
            out = self._complete(prompt).strip()
            if out and "NONE" not in out.upper()[:8]:
                info = out
        self._research_cache[company] = info
        return info

    def build_profile(self, resume_text: str) -> str:
        """Summarize the resume once; reused for every contact."""
        prompt = (
            "Summarize this resume for writing job-outreach emails. Extract as plain text, "
            "using ONLY what is in the resume:\n"
            "- NAME\n"
            "- TARGET ROLES: the kinds of jobs the candidate wants (e.g. 'Backend AI Engineer, "
            "AI Engineer, Python Backend Developer')\n"
            "- EDUCATION: current degree/status in a short phrase (e.g. 'pursuing MCA')\n"
            "- EXPERIENCE: notable roles/internships, one short line each "
            "(e.g. 'Frontend Developer intern — React, REST APIs')\n"
            "- PROJECTS: up to 4, each as 'Project name — key technologies used', KEEPING the "
            "real tech stack from the resume (e.g. FastAPI, LangChain, RAG, ChromaDB, Docker, "
            "Playwright, PostgreSQL, JWT)\n"
            "- SKILLS: one short comma-separated list of core skills\n\n"
            "ANTI-FABRICATION (critical): copy technologies and facts from the resume; invent "
            "NOTHING — no projects, companies, or numbers that aren't there.\n\n"
            f"RESUME:\n{resume_text[:8000]}"
        )
        self._profile = self._complete(prompt).strip()
        return self._profile

    def draft(self, contact: Contact, company_info: str = "") -> Email:
        if self._profile is None:
            raise RuntimeError("Call build_profile() before draft().")
        company = contact.company or "their company"
        first_name = contact.name.split()[0] if contact.name else "there"
        # Generic, fixed subject from config (optionally includes {company}).
        try:
            subject = self._subject_template.format(company=company)
        except (KeyError, IndexError):
            subject = self._subject_template
        # Combine any sheet 'notes' with researched company info — both are REAL.
        real_info = " ".join(x for x in (contact.notes, company_info) if x).strip()
        if real_info:
            opening_line = (
                "Opening (2 sentences): \"I came across your profile at "
                f"{company} and wanted to reach out because I'm actively looking for <TARGET "
                "ROLES from profile> opportunities.\" Then ONE honest sentence referencing the "
                f"company using ONLY these real facts: {real_info}"
            )
        else:
            opening_line = (
                "Opening (1 sentence): \"I came across your profile/company and wanted to reach "
                "out because I'm actively looking for <TARGET ROLES from profile> opportunities.\" "
                "Do NOT invent any company-specific claim."
            )
        prompt = (
            f"Write ONLY the body of a {self._tone} cold job-outreach email (NO subject line), "
            f"FROM the sender (job seeker; see CANDIDATE PROFILE) TO {first_name} at {company}. "
            "Use ONLY facts from the profile; invent nothing.\n\n"
            "Follow this EXACT structure:\n"
            f"1) 'Hi {first_name},'\n"
            f"2) {opening_line}\n"
            "3) Background: ONE sentence combining the sender's EDUCATION and a relevant "
            "EXPERIENCE/internship from the profile.\n"
            "4) A line exactly: 'Some projects I've built include:' then UP TO 3 bullets, each "
            "'- <Project name> using <its real tech stack>' taken from the profile's PROJECTS. "
            "KEEP the technologies (FastAPI, LangChain, RAG, Docker, etc.) — do not simplify them.\n"
            "5) Skills: ONE sentence like 'I'm comfortable building APIs, integrating LLMs, "
            "designing RAG pipelines, and working with <core skills from profile>.'\n"
            "6) Closing: 'I've attached my resume.' then 'If my profile aligns with any current "
            "or upcoming <TARGET ROLES> openings, I'd appreciate the opportunity to interview.' "
            "then 'Thank you for your time.'\n\n"
            "HARD RULES:\n"
            "- FIRST PERSON ('I'/'my').\n"
            "- ANTI-FABRICATION: only projects, tech, education, and experience found in the "
            "profile. Invent no projects, companies, numbers, or claims.\n"
            "- No fake familiarity; reference the company only via provided real facts.\n"
            "- BANNED words: seasoned, passionate, thrilled, excited to reach out, honored, guru.\n"
            "- No placeholders like [Name]. Do NOT include a subject line or signature "
            "(both are added automatically).\n\n"
            f"CANDIDATE PROFILE (the SENDER):\n{self._profile}"
        )
        body = _clean_body(self._complete(prompt))
        body = _strip_signoff(body)
        body = f"{body.rstrip()}\n\n{self._signature}"
        return Email(subject=subject, body=body)

    def _complete(self, prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=self._temperature,  # 0 = deterministic, minimizes fabrication
        )
        return resp.choices[0].message.content or ""


_SIGNOFF_RE = re.compile(
    r"\b(best regards|kind regards|warm regards|regards|sincerely|best|thanks|"
    r"thank you|cheers|yours truly)\s*,?\s*$",
    re.IGNORECASE,
)


def _clean_body(text: str) -> str:
    """Drop a stray leading 'Subject:' line the model may add, and normalize
    duplicated bullet markers (e.g. '- - x' or '•- x' -> '- x')."""
    lines = text.strip().splitlines()
    while lines and (not lines[0].strip() or lines[0].lower().startswith("subject:")):
        lines.pop(0)
    norm = []
    for ln in lines:
        if re.match(r"^\s*[-*•]", ln):
            ln = re.sub(r"^\s*(?:[-*•]\s*)+", "- ", ln)
        norm.append(ln)
    return "\n".join(norm).strip()


def _strip_signoff(body: str) -> str:
    """Drop a trailing closing salutation (and any trailing name after it) the
    model added on its own, so we don't double up with the appended signature."""
    lines = body.rstrip().splitlines()
    # Walk up past a short trailing name line, then a salutation line.
    while lines and not lines[-1].strip():
        lines.pop()
    # If one of the last two lines is a bare sign-off, cut from there.
    for cut in range(len(lines) - 1, max(len(lines) - 3, -1), -1):
        if _SIGNOFF_RE.match(lines[cut].strip()):
            lines = lines[:cut]
            break
    return "\n".join(lines).rstrip()


def has_placeholder(email: Email) -> str | None:
    """Return the first leaked placeholder found, or None if clean."""
    for chunk in (email.subject, email.body):
        m = _PLACEHOLDER_RE.search(chunk)
        if m:
            return m.group(0)
    return None
