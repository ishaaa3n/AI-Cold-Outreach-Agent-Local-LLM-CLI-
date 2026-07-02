# 05 — Design Decisions & Trade-offs

For each decision: **what we chose**, **why**, and **the trade-off**. This is the
"senior engineer" thinking — interviewers care more about *why* than *what*.

---

## 1. CLI tool, not a web app

**Chose:** a command-line program.
**Why:** it's the simplest thing that solves the problem — no server, database,
frontend, or hosting. Fast to build, easy to run locally.
**Trade-off:** no GUI; non-technical users need the terminal. (We *started* as a
web app but pivoted — a CLI matched the actual need better.)

---

## 2. Local AI (Ollama), not a cloud API

**Chose:** run models locally via Ollama.
**Why:**
- **Privacy** — your resume and contacts never leave your machine.
- **Cost** — free; no per-token billing.
- **Offline** — works without internet (except sending).
**Trade-off:** local models are **weaker and slower** than cloud models like GPT-4
or Groq-hosted Llama-70B. This is the central tension in the project (see #4).

---

## 3. You provide the contacts (Excel), we don't scrape them

**Chose:** the user supplies an Excel sheet of HR emails.
**Why:** getting correct recipient emails is the hardest, least reliable part.
Scraping them is inaccurate and can violate site terms. A user-provided sheet is
accurate and clean.
**Trade-off:** the user has to build the sheet. (We tried automated discovery
earlier; it produced mostly low-confidence guesses — proof this was the right call.)

---

## 4. Model choice: 3b vs 8b (speed vs faithfulness)

**Observed:**
- `llama3.2:3b` — ~25s/email, but **copies jargon** and occasionally **embellishes**.
- `llama3.1:8b` — clean, faithful, follows nuanced instructions — but **~5 min/email**
  on a CPU laptop, impractical for batches.
**Chose:** 3b for speed (user's hardware + need for batches), temperature 0, and
strong grounding — with the **draft→review→send** workflow as the safety net.
**Trade-off:** you accept that a small local model needs human review before
sending. The honest fix for both speed *and* quality is a fast cloud model
(e.g. Groq Llama-70B), which we deliberately did not use to stay local.

---

## 5. Temperature = 0

**Chose:** `temperature=0.0` for all AI calls.
**Why:** temperature controls randomness. 0 makes output **deterministic** and
**minimizes invention/hallucination** — critical when the text goes to real
recruiters under your name.
**Trade-off:** less variety between emails (mitigated by per-company research and
per-contact details).

---

## 6. Anti-fabrication measures

The biggest risk: the model **making up achievements** (it once invented "250%
increase in customer orders" — nowhere in the resume). Mitigations, layered:
1. **Prompt grounding** — "use ONLY facts/numbers/outcomes in the resume; invent
   nothing."
2. **Temperature 0** — less creative drift.
3. **Bigger model when needed** — 8b fabricates far less than 3b.
4. **Human review** — the `draft` command lets you read every email before `run`.
5. **Placeholder guard** — blocks obviously broken output.

Interview gold: *"LLMs hallucinate, so I treated the model as untrusted — grounded
the prompt, set temperature 0, and kept a human-review step for anything sent
under the user's name."*

---

## 7. Separation: profile keeps detail, draft simplifies

**Chose:** `build_profile()` preserves **all** technical detail (RAG, FastAPI,
metrics); `draft()` decides what to simplify per email.
**Why:** different companies value different keywords — stripping them at the
profile stage loses information you might want later. Simplification is an
audience decision, so it belongs at draft time.
**Trade-off:** the draft prompt has to do more work (and small models do it
imperfectly).

---

## 8. Deterministic subject line

**Chose:** build the subject in code from config, not from the model.
**Why:** the model was inconsistent (once used the sender's *name* as the title).
A fixed, generic subject (`AI/ML & Backend Engineering Opportunities`) is reliable.
**Trade-off:** less per-email subject tailoring (fine — consistency matters more
here).

---

## 9. Safety rails (because it sends real email)

| Rail | Purpose |
|---|---|
| **Dedupe** (`sent_log.csv`) | never email the same person twice |
| **Throttle** (`throttle_seconds`) | space out sends to avoid spam flags |
| **Daily limit** | cap volume per run (Gmail suspends bulk senders) |
| **Placeholder guard** | don't send `[Name]`-leaked drafts |
| **Batch confirmation** | one `y/N` before sending (bypass with `--yes`) |
| **`test` / `dry-run`** | validate the pipeline without emailing strangers |

**Why:** cold-emailing from a personal Gmail can get the account **suspended** and
land you in spam. These rails protect the user's account and reputation.

---

## 10. Best-effort, fail-safe external calls

**Chose:** web research and each search backend are wrapped so failures return
empty instead of crashing.
**Why:** the core job (writing + sending) must not fail because a search engine
rate-limited us.
**Trade-off:** personalization is sometimes missing — which is correct, because
inventing company facts would be worse than omitting them.

---

## What you'd improve with more time / resources (say this in interviews)

- **Fast, faithful model** via a cloud API (Groq) behind the same interface.
- **Reliable research** via a paid search API (Tavily/Serper) instead of scraping.
- **Reply tracking** (IMAP) to auto-send follow-ups.
- **A/B testing** subject lines and measuring reply rates.
- **A small web UI** for non-technical users.
- **Tests** (unit tests for the parsers; a mock SMTP for the mailer).
