# Outreach CLI

Draft and send personalized cold emails from your **resume** + an **Excel sheet of HR contacts**, using a **local Ollama model** (offline, private). Sends via Gmail SMTP.

## Setup

```bash
# one-time: create the venv and install deps (from the project root)
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r outreach_cli/requirements.txt

# initialize a working folder
.venv/Scripts/python.exe -m outreach_cli --root ./my-outreach init
```

This writes `outreach.yaml` + `contacts.xlsx` into the folder. Then:

1. Drop your **resume** in the folder (`resume.pdf`, `.docx`, or `.txt`).
2. Edit **`outreach.yaml`** — your name, signature, and a **Gmail App Password**
   (create at https://myaccount.google.com/apppasswords).
3. Fill **`contacts.xlsx`** — columns: `name, email, company, role, notes`.
   The `notes` column is the highest-leverage field: a specific detail about the
   person/company that the model works into the email.

## Commands

```bash
P=".venv/Scripts/python.exe -m outreach_cli --root ./my-outreach"

$P test                  # send ONE test email to yourself — verify Gmail/SMTP works first
$P test --to me@you.com  # ...or to a specific address
$P draft                 # generate drafts into outbox/ (nothing sends) — review these
$P draft --research      # ...and web-search each company for an honest personalized line
$P run                   # draft AND send (full auto, throttled). Asks once before sending.
$P run --research        # ...with per-company research (slower, better replies)
$P run --yes             # skip the one confirmation (true hands-off)
$P run --dry-run --yes   # simulate sending; prints what it would do
$P run --only Acme       # just contacts at a matching company/name
$P run --limit 10        # cap emails this run
```

## Safety rails (on by default)

- **Dedupe** — `sent_log.csv` records who was emailed; they're skipped next run.
- **Throttle** — `throttle_seconds` pause between sends (avoid Gmail spam flags).
- **Daily limit** — stop after `daily_limit` sends in one run.
- **Placeholder guard** — a draft with a leaked `[Name]`/`{company}` is skipped, not sent.
- **Batch confirm** — one `y/N` before a run (bypass with `--yes`).
- **Resume auto-attached** to every email.

## Notes

- Requires Ollama running locally with the configured model (`ollama pull llama3.2:3b`).
  A stronger model (`qwen2.5:7b`) gives better emails but is slower.
- Gmail caps sending (~500/day, far fewer in practice for cold outreach). Keep
  volumes low and personalized to stay deliverable and within terms.
```
