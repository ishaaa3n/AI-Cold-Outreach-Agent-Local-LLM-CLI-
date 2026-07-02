# 03 — Code Walkthrough (low-level)

This goes file by file. For each, we cover **what it does**, the **key code**, and
the **Python/CS concepts** it uses (so you can explain them). Concepts are also
collected in [04-concepts-to-learn.md](04-concepts-to-learn.md).

---

## `config.py` — settings

**Job:** read `outreach.yaml` into a typed object; provide the template that
`init` writes.

Key ideas:
- **`@dataclass`** — a Python decorator that auto-generates a class for holding
  data (like a struct). `Config` holds sender, smtp, model, sending, etc.
- **`@property`** — `outbox` and `sent_log` are computed on access
  (`self.root / "outbox"`) instead of stored.
- **PyYAML** — `yaml.safe_load()` turns the YAML text into a Python dict.
- **`Path`** (`pathlib`) — a modern way to handle file paths (`root / "resume.pdf"`).

```python
@dataclass
class Config:
    sender: dict
    smtp: dict
    model: dict
    ...
    @property
    def outbox(self) -> Path:
        return self.root / "outbox"

def load_config(root: Path) -> Config:
    data = yaml.safe_load((root / CONFIG_NAME).read_text())
    return Config(sender=data["sender"], smtp=data["smtp"], ...)
```

Interview point: *"Config is centralized and typed, so the rest of the code never
parses YAML or guesses defaults."*

---

## `contacts.py` — reading the Excel sheet

**Job:** turn `contacts.xlsx` rows into a list of `Contact` objects.

Key ideas:
- **openpyxl** — library to read `.xlsx`. `load_workbook(..., read_only=True,
  data_only=True)` streams rows efficiently and returns computed values (not
  formulas).
- **Header mapping** — we read the first row, lowercase it, and find the column
  index of each field we care about. This means the sheet's columns can be in
  any order and extra columns are ignored.
- **Defensive parsing** — real spreadsheets are messy:
  - Rows can be **shorter than the header** ("ragged"), so we bounds-check
    `idx[col] >= len(row)` before indexing (this was a real bug we hit and fixed).
  - Rows with no/invalid email are skipped.

```python
def read_contacts(path) -> list[Contact]:
    ...
    header = [str(c).strip().lower() if c else "" for c in next(rows)]
    idx = {col: header.index(col) for col in COLUMNS if col in header}
    for row in rows:
        def get(col, _row=row):
            if col not in idx or idx[col] >= len(_row) or _row[idx[col]] is None:
                return ""
            return str(_row[idx[col]]).strip()
        email = get("email")
        if not email or "@" not in email:
            continue
        out.append(Contact(name=get("name"), email=email, ...))
```

Interview point: *"Never trust input data — spreadsheets have blank rows, ragged
rows, and missing columns. The reader is defensive so one bad row can't crash a
batch of 1,800."*

---

## `resume.py` — extracting resume text

**Job:** given `resume.pdf/.docx/.txt`, return plain text.

Key ideas:
- **Polymorphism by extension** — checks the file suffix and uses the right
  library: `pypdf` for PDF, `docx2txt` for Word, plain read for text.
- PDFs store text per page; we join every page's `extract_text()`.

```python
def extract_resume_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
    if path.suffix.lower() == ".docx":
        return docx2txt.process(str(path)).strip()
    return path.read_text(encoding="utf-8", errors="ignore").strip()
```

Gotcha to mention: PDF text extraction is imperfect (layout, scanned images).
If a résumé is a scanned image, you'd need OCR (not implemented).

---

## `research.py` — optional company web search

**Job:** given a company name, return raw text from web searches so the AI can
distill one factual sentence for personalization.

Key ideas:
- **Multiple backends with fallback** — tries DuckDuckGo HTML, DuckDuckGo Lite,
  then Bing, and **merges** whatever responds. If one is rate-limited, the others
  still contribute. (This mirrors a "provider fallback" pattern.)
- **Best-effort / fail-safe** — every network call is wrapped in `try/except`; any
  failure returns `""` rather than crashing. Research is a bonus, never a blocker.
- **HTML → text** — a regex strips tags (`<[^>]+>`) and collapses whitespace.
- **`httpx.Client`** — a modern HTTP library; used as a **context manager**
  (`with ... as client:`) so the connection is always closed.

```python
def search_company(company: str) -> str:
    query = f"{company} company what they do products"
    chunks = []
    with httpx.Client(timeout=10, headers=_HEADERS) as client:
        for name, url, method in _BACKENDS:
            try:
                r = client.post(url, data={"q": query}) if method == "post" \
                    else client.get(url, params={"q": query})
            except Exception:
                continue
            if r.status_code < 400 and len(r.text) > 500:
                chunks.append(_visible_text(r.text))
    return "\n".join(chunks)[:6000]
```

Honest limitation to mention: keyless web scraping is **unreliable** — search
engines rate-limit and block. That's why it's optional and best-effort. A
production version would use a paid search API (Tavily/Serper).

---

## `drafting.py` — the AI core (most important file)

**Job:** turn (resume profile + one contact) into an `Email(subject, body)`.

### How it talks to the AI

Ollama exposes an **OpenAI-compatible API** at `http://localhost:11434/v1`. So we
use the standard `openai` Python client, just pointed at localhost:

```python
self._client = OpenAI(base_url=base_url, api_key=api_key)  # api_key ignored locally

def _complete(self, prompt: str) -> str:
    resp = self._client.chat.completions.create(
        model=self._model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=self._temperature,   # 0 = deterministic
    )
    return resp.choices[0].message.content or ""
```

This is the single most important thing to understand: **we send a text prompt,
the model returns text.** Everything else is prompt engineering + parsing.

### `build_profile(resume_text)` — done once per run

Sends the resume to the model with instructions to extract NAME, HEADLINE,
TARGET ROLES, SKILLS, and ACHIEVEMENTS — **preserving full technical detail** and
**inventing nothing**. Cached in `self._profile` and reused for every contact
(so we don't re-summarize 1,800 times).

### `research_company(company)` — optional, cached

Calls `research.search_company()` to get raw web text, then asks the model to
write **one factual sentence** — or reply `NONE` if the text has no real facts
(so it never fabricates). Cached per company in a dict.

### `draft(contact, company_info)` — the email

Builds a big **prompt** that specifies the exact structure:
- Deterministic **subject** from config (not model-generated, so it's consistent).
- Greeting → opening → up to 2 impact bullets → resume-attached + 15-min CTA.
- **Hard rules**: first person, anti-fabrication (no invented numbers/outcomes),
  no jargon, banned buzzwords, word limit.

Then post-processes the model's output:
- `_clean_body()` — strips a stray `Subject:` line and normalizes double bullet
  markers (`- - x` → `- x`).
- `_strip_signoff()` — removes a closing salutation the model added, so we don't
  double up with the appended signature.
- Appends your signature from config.

```python
def draft(self, contact, company_info="") -> Email:
    subject = self._subject_template.format(company=company)  # deterministic
    prompt = ( ... big structured instructions + self._profile ... )
    body = _clean_body(self._complete(prompt))
    body = _strip_signoff(body)
    body = f"{body.rstrip()}\n\n{self._signature}"
    return Email(subject=subject, body=body)
```

### `has_placeholder(email)` — a safety net

A regex checks for leftover `[Name]` / `{company}` placeholders. If found, the
email is **not sent** (skipped and logged). Prevents embarrassing template leaks.

Interview point: *"The LLM is unreliable, so I don't trust it blindly — the
subject is deterministic, the output is post-processed, and a guard blocks
obviously broken emails."*

---

## `mailer.py` — sending via Gmail

**Job:** send one `Email` to one address, with the resume attached.

Key ideas:
- **`smtplib`** (built-in) — speaks SMTP, the email-sending protocol.
- **STARTTLS** — upgrades the connection to encrypted before logging in.
- **Gmail App Password** — a 16-char password for apps (needed because Gmail
  blocks your normal password for scripts; requires 2-Step Verification).
- **`EmailMessage`** + `add_attachment()` — builds a MIME message with the resume.

```python
def send(self, to_email, email, attachment=None):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = self._from, to_email, email.subject
    msg.set_content(email.body)
    if attachment:
        msg.add_attachment(attachment.read_bytes(), maintype="application",
                           subtype=attachment.suffix.lstrip("."), filename=attachment.name)
    with smtplib.SMTP(self._host, self._port) as server:
        server.starttls()
        server.login(self._username, self._password)
        server.send_message(msg)
```

---

## `sent_log.py` — dedupe

**Job:** remember who was emailed so nobody is emailed twice (idempotency).

Key ideas:
- Appends a row to `sent_log.csv` after each send (`email, name, company,
  subject, status, timestamp`).
- `load_sent_emails()` reads the CSV and returns a **set** of already-sent
  addresses; `_prepare()` filters those out before drafting.
- Uses a **set** for O(1) membership checks.

---

## `cli.py` — the orchestrator

**Job:** parse the command line and run the right flow.

Key ideas:
- **argparse** — Python's built-in command-line parser. Subcommands
  (`init/draft/run/test`) each map to a `cmd_*` function via `set_defaults(func=...)`.
- **`_prepare()`** — shared setup used by both `draft` and `run` (load config,
  extract resume, read contacts, filter already-sent, build profile). DRY.
- **Guards** — `_check_smtp_configured()` refuses to send if the config still has
  placeholder credentials; `run` asks for one confirmation (unless `--yes`).
- **Throttling** — `time.sleep(throttle_seconds)` between sends.
- **UTF-8 fix** — `sys.stdout.reconfigure(encoding="utf-8")` so emoji/✓ don't
  crash the Windows console (another real bug we fixed).

```python
def build_parser():
    p = argparse.ArgumentParser(prog="outreach_cli")
    sub = p.add_subparsers(dest="command", required=True)
    pr = sub.add_parser("run")
    pr.add_argument("--limit", type=int)
    pr.add_argument("--dry-run", action="store_true")
    pr.add_argument("--research", action="store_true")
    pr.set_defaults(func=cmd_run)
    ...
```

Next: **[04-concepts-to-learn.md](04-concepts-to-learn.md)** — the concepts behind all this.
