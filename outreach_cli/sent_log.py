"""CSV log of who was emailed — powers dedupe and (later) follow-ups."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

_FIELDS = ["email", "name", "company", "subject", "status", "timestamp"]


def load_sent_emails(path: Path) -> set[str]:
    """Emails already sent successfully (lowercased) — used to skip duplicates."""
    if not path.exists():
        return set()
    sent: set[str] = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("status") == "sent" and row.get("email"):
                sent.add(row["email"].lower())
    return sent


def append(path: Path, *, email: str, name: str, company: str, subject: str, status: str) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "email": email,
                "name": name,
                "company": company,
                "subject": subject,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )
