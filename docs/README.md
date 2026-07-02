# Outreach CLI — Complete Documentation (0 → 100)

This directory explains **everything** about the project: what it is, how every
line works, the concepts behind it, why each decision was made, and how to talk
about it in an interview. Written for someone who directed the product but wants
to fully understand and defend the implementation.

## Read in this order

1. **[01-overview.md](01-overview.md)** — What the tool does and the big picture. Start here.
2. **[02-architecture.md](02-architecture.md)** — The files, how they fit together, the data flow.
3. **[03-code-walkthrough.md](03-code-walkthrough.md)** — Low-level, file-by-file, function-by-function.
4. **[04-concepts-to-learn.md](04-concepts-to-learn.md)** — Every technology & CS concept used, with what to study.
5. **[05-design-decisions.md](05-design-decisions.md)** — The *why* behind each choice and its trade-offs.
6. **[06-interview-qa.md](06-interview-qa.md)** — Likely interview questions with strong answers.
7. **[07-glossary.md](07-glossary.md)** — Quick definitions of every term.

## The 30-second summary

A **command-line tool** that reads your **resume** and an **Excel sheet of HR
contacts**, then uses a **local AI model (Ollama)** to write a **personalized
cold email** for each contact and send it via **Gmail** — with safety rails
(no duplicates, rate-limiting, no fabricated claims). Fully offline except the
optional company web-search and the Gmail send.

## The code being documented

```
outreach_cli/
├── cli.py         # command-line entry: init / draft / run / test
├── config.py      # loads outreach.yaml (settings)
├── contacts.py    # reads the Excel sheet of HR contacts
├── resume.py      # extracts text from your resume (PDF/DOCX/TXT)
├── research.py    # optional: web-searches a company for personalization
├── drafting.py    # the AI part: turns resume + contact into an email
├── mailer.py      # sends email via Gmail SMTP
└── sent_log.py    # records who was emailed (prevents duplicates)
```

Every file above is dissected in [03-code-walkthrough.md](03-code-walkthrough.md).
