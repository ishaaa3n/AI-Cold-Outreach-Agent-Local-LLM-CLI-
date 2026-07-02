# 07 — Glossary

Quick definitions of every term used in this project and its docs.

## AI / LLM

- **LLM (Large Language Model)** — an AI trained on huge amounts of text that
  predicts the next token; you give it a prompt, it produces text.
- **Token** — the unit an LLM reads/writes; roughly ¾ of an English word.
- **Prompt** — the instruction text you send the model.
- **Prompt engineering** — the craft of writing prompts to get reliable output.
- **Temperature** — randomness control (0 = deterministic/factual, higher =
  creative/varied).
- **Context window** — the maximum number of tokens the model can consider at once.
- **Hallucination** — when a model confidently states something false/invented.
- **Grounding** — constraining the model to use only provided facts.
- **Inference** — running the model to get an output (as opposed to training it).
- **Parameters (3B/8B)** — the count of learned weights; more = more capable but
  heavier/slower.
- **Quantization** — compressing a model (e.g. to 4-bit) so it runs on modest
  hardware.
- **System / user / assistant messages** — roles in a chat-style LLM API.

## Ollama / running models

- **Ollama** — software that downloads and runs open LLMs locally and serves an API.
- **OpenAI-compatible API** — an API that speaks the same format as OpenAI's, so
  standard clients (like the `openai` library) work against it.
- **GGUF** — a file format for quantized local models.
- **VRAM** — GPU memory; **RAM** — system memory. Small VRAM means the model runs
  mostly on CPU/RAM (slower).

## Email

- **SMTP (Simple Mail Transfer Protocol)** — the protocol for *sending* email.
- **IMAP** — protocol for *reading* email (not used yet; needed for reply tracking).
- **TLS / STARTTLS** — encryption; STARTTLS upgrades a plain connection to
  encrypted.
- **App Password** — a 16-character Gmail password for apps/scripts; requires
  2-Step Verification.
- **MIME** — the standard that lets emails include attachments and rich content.
- **Deliverability** — whether your email reaches the inbox vs spam.
- **SPF / DKIM / DMARC** — email-authentication standards that affect deliverability
  and sender reputation.
- **Warm-up** — gradually increasing send volume so a new sender isn't flagged.

## Python / software

- **Dataclass** — a Python class (via `@dataclass`) that auto-generates boilerplate
  for holding data.
- **Type hint** — annotation like `x: str` that documents expected types.
- **Context manager** — the `with` statement; guarantees cleanup (closing files,
  connections).
- **Generator / iterator** — produces items lazily, one at a time (memory-efficient).
- **List comprehension** — concise `[f(x) for x in xs]` syntax to build lists.
- **Regular expression (regex)** — a pattern language for matching/searching text.
- **argparse** — Python's standard library for building command-line interfaces.
- **Decorator** — a function that wraps another to add behavior (e.g. `@dataclass`,
  `@property`, `@staticmethod`).
- **Package / module** — a folder with `__init__.py` / a `.py` file; run with
  `python -m package`.

## Data formats

- **YAML** — a human-readable config format (used for `outreach.yaml`).
- **CSV** — comma-separated values text table (used for `sent_log.csv`).
- **XLSX** — the Excel spreadsheet format (read with openpyxl).

## Web

- **HTTP** — the request/response protocol of the web.
- **GET / POST** — HTTP methods (fetch data / submit data).
- **httpx** — a modern Python HTTP client library.
- **Web scraping** — extracting information from HTML web pages.
- **Rate limiting** — a server restricting how many requests you can make.

## Design ideas

- **Separation of concerns** — each component has one responsibility.
- **DRY (Don't Repeat Yourself)** — factor shared logic into one place.
- **Idempotency** — repeating an operation doesn't change the result / duplicate
  work.
- **Best-effort / fail-safe** — optional steps that never crash the main flow.
- **Guard clause** — an early check that stops a bad or unsafe action.
- **Defensive programming** — writing code assuming inputs will be messy or wrong.
- **Config-driven** — behavior controlled by a config file rather than hardcoded
  values.
