# 06 — Interview Q&A

Practice these out loud. Each has a **short answer** (say this) and **why it's
right**. Tie answers to real files/decisions.

---

### Q1. "Walk me through this project."

**Say:** "It's a local command-line tool that automates personalized cold-email
outreach for job hunting. You give it your resume and an Excel sheet of HR
contacts. It extracts your resume text, uses a local LLM via Ollama to build a
profile of you, then for each contact optionally web-searches their company and
writes a personalized email, and sends it through Gmail SMTP with your resume
attached. It has safety rails — dedupe, rate-limiting, and anti-fabrication —
because it sends real email from your account."

---

### Q2. "How does it actually talk to the AI model?"

**Say:** "Ollama runs the model locally and exposes an OpenAI-compatible HTTP API.
So I use the standard `openai` Python client, just pointed at `localhost:11434`.
I send a prompt as a chat message and get text back. Everything else is prompt
engineering and parsing the response."

**Why right:** shows you understand the abstraction (OpenAI-compatible API) and
that an LLM call is just text-in/text-out.

---

### Q3. "How do you stop the model from making things up?"

**Say:** "That was a real bug — the model once invented achievements that weren't
in the resume. I treated the model as untrusted and layered defenses: I ground the
prompt to use only facts from the resume, set temperature to 0 for determinism,
use a larger model when quality matters, keep a human-review step (`draft` before
`run`), and a placeholder guard that blocks broken output."

**Why right:** demonstrates awareness of hallucination and a *systematic* mitigation.

---

### Q4. "What is temperature?"

**Say:** "A setting from 0 to ~2 that controls randomness in the model's output.
At 0 it's deterministic and picks the most likely tokens — best for factual,
consistent text. Higher values add creativity and variety. I use 0 here to
minimize invented details."

---

### Q5. "Why a local model instead of GPT-4 or a cloud API?"

**Say:** "Privacy — the resume and contacts never leave the machine; cost — it's
free; and it works offline. The trade-off is that local models are weaker and
slower. On a laptop CPU, the 3B model is fast but sloppy, and the 8B is faithful
but ~5 min per email. The honest fix for both speed and quality would be a fast
cloud model behind the same interface, but the requirement was to stay local."

**Why right:** shows you can articulate a trade-off, not just a preference.

---

### Q6. "How do you avoid emailing the same person twice?"

**Say:** "Every successful send is appended to `sent_log.csv`. At the start of each
run I load those addresses into a set and filter them out before drafting. That
makes runs idempotent — re-running doesn't duplicate emails, and it enables
follow-ups later."

**Keyword to drop:** *idempotency*.

---

### Q7. "How do you personalize the emails honestly?"

**Say:** "Two sources of real info: an optional `notes` column in the sheet, and an
optional web search of the company. The search results are distilled by the model
into one factual sentence — and if it can't find real facts, it returns `NONE` and
I skip personalization rather than invent something. No fake 'I've long admired
your company' lines."

---

### Q8. "Web scraping is unreliable — how did you handle that?"

**Say:** "I used a fallback chain — DuckDuckGo HTML, DuckDuckGo Lite, then Bing —
and merge whatever responds, all wrapped in try/except so any failure just returns
empty. Research is best-effort; it never blocks the core job of writing and
sending. A production version would use a paid search API for reliability."

---

### Q9. "What are the risks of automated cold email, and how did you mitigate them?"

**Say:** "Two big ones. First, account safety — bulk sending from a personal Gmail
can get it suspended and land in spam, so I added throttling, a daily limit, and a
`test`/`dry-run` mode, and I recommend small batches. Second, reputation — a bad or
fabricated email under your name is unrecoverable, so I added a review step and
anti-fabrication controls."

**Why right:** shows judgment and responsibility, not just coding.

---

### Q10. "How would you scale this to thousands of emails a day?"

**Say:** "You wouldn't do it from one personal Gmail — you'd use a dedicated
sending domain with proper SPF/DKIM/DMARC and a transactional email provider,
warm up the domain, and respect provider limits. On the code side, batch and
queue the work, add reply tracking via IMAP for follow-ups, and swap the local
model for a fast hosted one. But high volume also lowers reply rates — better to
send fewer, more-targeted emails."

---

### Q11. "Tell me about a bug you found and fixed."

**Pick one (all real):**
- **Misattribution:** the model credited the sender's achievements to the
  recipient ("your experience building…"). Fixed by making sender/recipient roles
  explicit in the prompt and enforcing first person.
- **Fabrication:** invented metrics. Fixed with grounding + temperature 0 + a
  bigger model + review.
- **Ragged rows:** the Excel reader crashed on rows shorter than the header. Fixed
  with a bounds check before indexing.
- **Windows console crash:** printing ✓/⚠ crashed cp1252 terminals; fixed by
  forcing UTF-8 stdout.

**Why right:** concrete debugging stories are the most convincing interview material.

---

### Q12. "What does the code do to be robust / production-minded?"

**Say:** "Defensive parsing of messy spreadsheets, best-effort external calls that
fail safe, guard clauses that refuse to run with placeholder credentials or send
broken emails, deterministic output where reliability matters (the subject), and
config-driven behavior so nothing sensitive is hardcoded."

---

### Q13. "What would you improve?"

**Say:** "Add automated tests (parsers + a mock SMTP), a fast faithful model via a
cloud API behind the same interface, a reliable search API, reply tracking for
follow-ups, and reply-rate analytics to A/B test subject lines."

---

## Rapid-fire (one-liners)

- **What's an LLM?** A next-token predictor trained on huge text; you prompt it and
  it continues the text.
- **What's a token?** ~¾ of a word; the unit models read/write.
- **What's Ollama?** A tool to run open LLMs locally with an OpenAI-compatible API.
- **What's SMTP?** The protocol for sending email.
- **Why an App Password?** Gmail blocks normal passwords for scripts; app passwords
  (with 2FA) are the supported way.
- **What's idempotency?** Running an operation again doesn't change the result /
  duplicate work — here, via the sent-log dedupe.
- **What's separation of concerns?** Each module has one responsibility, so changes
  stay local.
