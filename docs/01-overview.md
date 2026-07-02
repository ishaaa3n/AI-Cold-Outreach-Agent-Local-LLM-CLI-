# 01 — Overview

## What is this?

A **cold-outreach automation CLI**. You give it two things:

1. Your **resume** (`resume.pdf`).
2. An **Excel sheet** of HR/recruiter contacts (`name, email, company, title, ...`).

It then, for each contact:
- Reads your resume once and builds a short "profile" of you.
- (Optionally) web-searches the contact's company for one real fact.
- Uses a **local AI model** to write a personalized cold email.
- Sends it from your **Gmail**, with your resume attached.
- Logs who was emailed so nobody gets emailed twice.

## The problem it solves

Job-seekers send the same generic email to hundreds of companies, or spend hours
manually tailoring each one. The two hard parts are:
- **Getting recipient addresses** — solved here by *you* providing the Excel sheet
  (far more reliable than scraping the web).
- **Personalizing at scale** — solved by an LLM that rewrites your achievements
  per company.

## Why it's built the way it is (one line each)

- **CLI, not a web app** — simplest thing that works; no server, no database, no UI.
- **Local AI (Ollama)** — free, private (your resume never leaves your machine),
  works offline.
- **You provide contacts** — eliminates the unreliable, borderline-legal step of
  scraping emails.
- **Safety rails everywhere** — because it sends real emails from *your* account,
  which can be suspended or land in spam if abused.

## The pipeline (big picture)

```
 resume.pdf ──► extract text ──► [AI] build "profile of you" (done once)
                                          │
 contacts.xlsx ──► read rows ─────────────┤
                                          ▼
                For each contact:  (optional) [web search] company fact
                                          ▼
                              [AI] write personalized email
                                          ▼
                     safety checks (dedupe, placeholder guard)
                                          ▼
                          send via Gmail SMTP  +  log to sent_log.csv
```

## Tech stack (what each piece is for)

| Piece | Role |
|---|---|
| **Python 3** | The language everything is written in |
| **Ollama** | Runs the AI model locally on your machine |
| **llama3.2:3b / llama3.1:8b** | The actual AI models (3b = fast, 8b = higher quality) |
| **`openai` library** | Talks to Ollama using the OpenAI API format |
| **openpyxl** | Reads the Excel contacts sheet |
| **pypdf / docx2txt** | Extract text from resume files |
| **httpx** | Makes web requests (company research) |
| **smtplib / email** (built-in) | Sends the Gmail email with attachment |
| **PyYAML** | Reads the `outreach.yaml` config file |

## How you actually run it

```bash
python -m outreach_cli --root ./my-outreach init     # create config + template sheet
python -m outreach_cli --root ./my-outreach test     # send a test email to yourself
python -m outreach_cli --root ./my-outreach draft    # write drafts to outbox/ (no send)
python -m outreach_cli --root ./my-outreach run      # draft AND send (throttled)
```

Next: **[02-architecture.md](02-architecture.md)** for how the files fit together.
