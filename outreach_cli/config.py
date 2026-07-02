"""Config loading + the template written by `init`."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_NAME = "outreach.yaml"

TEMPLATE = """\
# AI-OS Outreach CLI config. Fill this in, then run:  python -m outreach_cli run
sender:
  name: "Your Name"
  email: "you@gmail.com"
  signature: |
    Best regards,
    Your Name
    +91-00000-00000 | linkedin.com/in/you

smtp:
  host: smtp.gmail.com
  port: 587
  username: "you@gmail.com"
  # Gmail App Password (16 chars) — create at https://myaccount.google.com/apppasswords
  app_password: "xxxx xxxx xxxx xxxx"

# A fixed, generic subject line for all emails (optionally use {company}).
subject: "AI/ML & Backend Engineering Opportunities"

model:
  base_url: "http://localhost:11434/v1"   # local Ollama
  name: "llama3.2:3b"      # fast local model. Use llama3.1:8b for better quality (slower).
  temperature: 0.0         # 0 = deterministic, minimizes made-up details

sending:
  throttle_seconds: 45      # pause between sends (avoid spam flags)
  daily_limit: 40           # stop after this many in one run
  attach_resume: true
  research: false           # web-search each company to personalize (slower; or use --research)

tone: "warm, professional, concise"
resume_path: "resume.pdf"
contacts_path: "contacts.xlsx"
"""


@dataclass
class Config:
    sender: dict
    smtp: dict
    model: dict
    sending: dict
    tone: str
    resume_path: Path
    contacts_path: Path
    subject: str = "AI/ML & Backend Engineering Opportunities"
    root: Path = field(default=Path("."))

    @property
    def outbox(self) -> Path:
        return self.root / "outbox"

    @property
    def sent_log(self) -> Path:
        return self.root / "sent_log.csv"


def load_config(root: Path) -> Config:
    path = root / CONFIG_NAME
    if not path.exists():
        raise FileNotFoundError(
            f"No {CONFIG_NAME} found in {root}. Run:  python -m outreach_cli init"
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Config(
        sender=data["sender"],
        smtp=data["smtp"],
        model=data["model"],
        sending=data.get("sending", {}),
        tone=data.get("tone", "warm, professional, concise"),
        resume_path=root / data.get("resume_path", "resume.pdf"),
        contacts_path=root / data.get("contacts_path", "contacts.xlsx"),
        subject=data.get("subject", "AI/ML & Backend Engineering Opportunities"),
        root=root,
    )
