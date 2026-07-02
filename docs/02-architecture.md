# 02 — Architecture

## Design principle: separation of concerns

Each file does **one job** and knows as little as possible about the others. This
is why the code is easy to change (e.g. swapping the AI model or the mail sender
touches only one file). Interviewers love this phrase — "separation of concerns."

## The modules and their single responsibility

| File | Single responsibility | Key public thing |
|---|---|---|
| `cli.py` | Parse commands, orchestrate the flow | `main()`, `cmd_init/draft/run/test` |
| `config.py` | Load settings from `outreach.yaml` | `load_config()`, `Config` |
| `contacts.py` | Read the Excel sheet into objects | `read_contacts()`, `Contact` |
| `resume.py` | Turn a resume file into plain text | `extract_resume_text()` |
| `research.py` | Web-search a company (best-effort) | `search_company()` |
| `drafting.py` | Use the AI to write the email | `Drafter`, `draft()` |
| `mailer.py` | Send an email via Gmail SMTP | `Mailer.send()` |
| `sent_log.py` | Track/prevent duplicate sends | `load_sent_emails()`, `append()` |

## How data flows through the system

Everything is orchestrated by **`cli.py`**. The other modules are "dumb" helpers
it calls. Here is the `run` command end-to-end:

```
cli.main()
  └─ cmd_run(args)
       ├─ _prepare(args)                         # shared setup
       │    ├─ config.load_config()              # read outreach.yaml
       │    ├─ resume.extract_resume_text()      # resume.pdf -> text
       │    ├─ contacts.read_contacts()          # contacts.xlsx -> [Contact]
       │    ├─ sent_log.load_sent_emails()       # who to skip
       │    └─ Drafter(...).build_profile(text)  # AI: summarize resume ONCE
       │
       └─ for each Contact (up to daily_limit):
            ├─ drafter.research_company(company) # optional web search + AI distill
            ├─ drafter.draft(contact, info)      # AI: write the email
            ├─ has_placeholder(email)?           # safety: skip if "[Name]" leaked
            ├─ mailer.send(email + resume)       # Gmail SMTP
            ├─ sent_log.append(...)              # record it
            └─ time.sleep(throttle_seconds)      # pace the sends
```

## The three data objects (the "nouns")

The whole program moves three simple objects around:

1. **`Config`** (from `config.py`) — your settings (sender info, SMTP creds,
   model name, throttle, etc.). Built once at startup.
2. **`Contact`** (from `contacts.py`) — one row of the Excel sheet:
   `name, email, company, title, role, notes`.
3. **`Email`** (from `drafting.py`) — a `subject` + `body` produced by the AI.

## Where files live at runtime

You run the tool against a **working folder** (via `--root ./my-outreach`). That
folder contains everything for one "campaign":

```
my-outreach/
├── outreach.yaml     # your config (settings + Gmail app password)
├── resume.pdf        # your resume
├── contacts.xlsx     # your HR contacts
├── outbox/           # drafts written by the `draft` command
└── sent_log.csv      # created after the first send; the dedupe record
```

The `--root` flag means you can keep multiple campaigns in separate folders and
the code stays generic.

## Why this shape is "good engineering"

- **Testable** — each helper can be run in isolation (we did exactly this while
  building it).
- **Swappable** — change the AI model in `config.py`; change the mail provider in
  `mailer.py`. Nothing else cares.
- **Self-contained** — no database, no server, no cloud account required.
- **Fails safe** — research and web calls are "best-effort"; if they fail, the
  email still gets written.

Next: **[03-code-walkthrough.md](03-code-walkthrough.md)** for the line-level detail.
