# AI-OS Outreach Agent

A local **CLI cold-email agent**. Drop in your **resume** and an **Excel sheet of
HR contacts**, run one command, and it drafts and sends personalized outreach
emails — using a **local Ollama model** (offline, private) and Gmail for sending.

> This repo was pivoted from a larger AI platform to focus on this one tool.
> Everything lives in [`outreach_cli/`](outreach_cli/).

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com)** running locally with a model:
  ```bash
  ollama pull llama3.2:3b        # fast; qwen2.5:7b is better but slower
  ```
- A **Gmail App Password** for sending (https://myaccount.google.com/apppasswords)

## Setup (one time)

```bash
# from this folder
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r outreach_cli/requirements.txt   # Windows
# (macOS/Linux: .venv/bin/python -m pip install -r outreach_cli/requirements.txt)
```

## Use it

```bash
PY=".venv/Scripts/python.exe -m outreach_cli --root ./my-outreach"

$PY init                 # writes outreach.yaml + contacts.xlsx into ./my-outreach
# → drop your resume there, edit outreach.yaml (sender + Gmail App Password),
#   and fill contacts.xlsx (columns: name, email, company, role, notes)

$PY test                 # send ONE test email to yourself — verify Gmail works first
$PY draft                # generate drafts into outbox/ (nothing sends) — review them
$PY run --dry-run --yes  # simulate sending
$PY run                  # draft + send for real (asks once before sending)
```

See [outreach_cli/README.md](outreach_cli/README.md) for all commands, options,
and the built-in safety rails (dedupe, throttle, daily limit, placeholder guard).

## How it works

```
resume.(pdf|docx|txt) ─┐
                       ├─► profile (LLM, once) ─► per-contact email ─► outbox/ or Gmail SMTP
contacts.xlsx ─────────┘                                   │
                                              sent_log.csv (dedupe + history)
```
