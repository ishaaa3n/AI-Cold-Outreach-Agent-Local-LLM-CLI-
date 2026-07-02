# 04 — Concepts to Learn (0 → 100)

Everything the project uses, grouped by area. For each: **what it is**, **where it
appears here**, and **what to study**. Tick these off and you can explain the
whole project.

---

## A. Python language

| Concept | What it is | Where here |
|---|---|---|
| **Variables & types, f-strings** | `f"Hello {name}"` string formatting | everywhere |
| **Functions** | reusable blocks with args/return | every file |
| **Type hints** | `def f(x: str) -> int:` — documents types | every signature |
| **`@dataclass`** | auto-generates data-holding classes | `Config`, `Contact`, `Email` |
| **Classes / OOP** | `Drafter` bundles state (client, model) + methods | `drafting.py`, `mailer.py` |
| **`pathlib.Path`** | object-oriented file paths (`root / "x"`) | `config.py`, `resume.py` |
| **List comprehensions** | `[f(x) for x in xs if cond]` | `contacts.py`, `cli.py` |
| **Generators / iterators** | lazy sequences (`ws.iter_rows()`) | `contacts.py` |
| **Context managers (`with`)** | auto-cleanup (files, HTTP, SMTP) | `research.py`, `mailer.py` |
| **Exceptions (`try/except`)** | handle errors without crashing | research, mailer, cli |
| **Modules & packages** | `__init__.py`, `python -m outreach_cli` | whole package |
| **`argparse`** | build command-line interfaces | `cli.py` |
| **Regular expressions (`re`)** | pattern matching on text | placeholder guard, HTML strip |
| **Sets & dicts** | fast lookups (dedupe, header map) | `sent_log.py`, `contacts.py` |

**Study:** the official Python tutorial (docs.python.org/3/tutorial), then
"dataclasses", "argparse", and "pathlib" module docs. Practice: rewrite one file
from memory.

---

## B. Large Language Models (LLMs)

| Concept | What it is | Where here |
|---|---|---|
| **LLM** | a model that predicts the next token; can write text | the whole email generation |
| **Token** | a chunk of text (~¾ of a word) the model reads/writes | `max_tokens=600` |
| **Prompt** | the text instructions you send the model | `build_profile`, `draft` |
| **Prompt engineering** | crafting instructions to get good output | the big prompt strings |
| **Temperature** | randomness knob; 0 = deterministic, higher = creative | `temperature=0.0` |
| **Context window** | max tokens the model can consider at once | why resume is capped at 8000 chars |
| **System vs user messages** | roles in a chat API | `messages=[{"role":"user",...}]` |
| **Hallucination** | model inventing false facts | the fabrication bug we fixed |
| **Grounding** | forcing the model to use only given facts | anti-fabrication rules |
| **Quantization** | shrinking a model (e.g. 4-bit) to run on small hardware | why 3b/8b fit in RAM |

**Study:** Anthropic's / OpenAI's prompt-engineering guides; the concept of
temperature and tokens; "why LLMs hallucinate." You don't need the math — you need
the intuitions.

**The one-paragraph explanation you should be able to give:**
*"An LLM is a next-token predictor trained on huge text. You give it a prompt and
it continues it. Temperature controls randomness — I set it to 0 for consistent,
factual output. Because it can 'hallucinate' (make things up), I ground it by
telling it to use only facts from the resume and I post-process/guard the output."*

---

## C. Ollama & running models locally

| Concept | What it is |
|---|---|
| **Ollama** | a tool that downloads and runs open LLMs locally, exposing an API |
| **Model tags** | `llama3.2:3b`, `llama3.1:8b` — family:size |
| **Parameters (3b/8b)** | model size; more = smarter but slower/heavier |
| **GGUF / quantization** | compressed model format so it runs on CPU/small GPU |
| **OpenAI-compatible API** | Ollama mimics OpenAI's API so standard clients work |
| **VRAM vs RAM** | GPU memory vs system memory; small VRAM ⇒ runs mostly on CPU/RAM |

**Study:** ollama.com docs; run `ollama list`, `ollama run llama3.2:3b`. Understand
that bigger models are more faithful but slower — the core trade-off in this project.

---

## D. Email & deliverability

| Concept | What it is | Where here |
|---|---|---|
| **SMTP** | the protocol for *sending* email | `mailer.py` |
| **TLS / STARTTLS** | encryption for the SMTP connection | `server.starttls()` |
| **App Password** | app-specific Gmail password (needs 2FA) | `smtp.app_password` |
| **MIME / attachments** | email format that allows files | `add_attachment()` |
| **Deliverability** | whether email lands in inbox vs spam | throttle, small batches |
| **Rate limits** | Gmail caps daily sends; abuse ⇒ suspension | `daily_limit`, `throttle_seconds` |

**Study:** "how SMTP works", "Gmail App Passwords", "why emails go to spam"
(SPF/DKIM/DMARC at a high level, sender reputation, volume/warm-up).

---

## E. Data formats

| Concept | What it is | Where |
|---|---|---|
| **Excel / openpyxl** | reading `.xlsx` spreadsheets | `contacts.py` |
| **CSV** | comma-separated values (the sent log) | `sent_log.py` |
| **PDF/DOCX text extraction** | pulling text out of documents | `resume.py` |
| **YAML** | human-friendly config format | `config.py` |

**Study:** the `csv` and `openpyxl` quickstarts; what YAML is.

---

## F. Web / HTTP

| Concept | What it is | Where |
|---|---|---|
| **HTTP GET/POST** | request methods to a server | `research.py` |
| **httpx** | modern Python HTTP client | `research.py` |
| **Web scraping** | extracting data from HTML pages | company research |
| **Rate limiting / blocking** | servers refusing too many requests | why research is flaky |

**Study:** "HTTP basics", "GET vs POST", and why scraping search engines is
unreliable.

---

## G. Software-design ideas (great for interviews)

| Idea | Meaning | Where |
|---|---|---|
| **Separation of concerns** | each module does one job | whole project |
| **DRY** (Don't Repeat Yourself) | shared setup in `_prepare()` | `cli.py` |
| **Idempotency** | running again doesn't duplicate work | `sent_log` dedupe |
| **Fail-safe / best-effort** | optional steps never crash the main flow | research |
| **Config-driven** | behavior set by a file, not hardcoded | `outreach.yaml` |
| **Defensive programming** | assume inputs are messy | ragged-row handling |
| **Guard clauses** | early checks that stop bad actions | placeholder/SMTP guards |

**Study:** just be able to define each and point to where you used it.

---

## Suggested learning path (2–3 weeks, part-time)

1. **Week 1 — Python:** tutorial + dataclasses/argparse/pathlib. Re-read
   `contacts.py` and `cli.py` until every line is obvious.
2. **Week 2 — LLMs & Ollama:** tokens, temperature, prompting, hallucination.
   Re-read `drafting.py`; experiment by changing the prompt and temperature.
3. **Week 3 — Email + web + design:** SMTP/deliverability, HTTP, and the
   design-ideas table. Practice the interview answers in
   [06-interview-qa.md](06-interview-qa.md).
