"""Send email via Gmail SMTP (App Password) with the resume attached."""
from __future__ import annotations

import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

from .drafting import Email

# Connection hiccups worth retrying (network drops, timeouts) — but NOT auth errors.
_RETRYABLE = (
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPConnectError,
    OSError,          # covers socket errors / TimeoutError on flaky networks
)


class Mailer:
    def __init__(self, smtp: dict, sender_name: str, sender_email: str):
        self._host = smtp.get("host", "smtp.gmail.com")
        self._port = int(smtp.get("port", 587))
        self._username = smtp["username"]
        self._password = smtp["app_password"].replace(" ", "")
        self._from = f"{sender_name} <{sender_email}>"
        # Higher timeout + retries tolerate slow/flaky networks.
        self._timeout = int(smtp.get("timeout", 60))
        self._retries = int(smtp.get("retries", 3))

    def _build(self, to_email: str, email: Email, attachment: Path | None) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self._from
        msg["To"] = to_email
        msg["Subject"] = email.subject
        msg.set_content(email.body)
        if attachment and attachment.exists():
            data = attachment.read_bytes()
            subtype = attachment.suffix.lstrip(".") or "octet-stream"
            maintype = "application" if subtype != "txt" else "text"
            msg.add_attachment(
                data, maintype=maintype, subtype=subtype, filename=attachment.name
            )
        return msg

    def send(self, to_email: str, email: Email, attachment: Path | None = None) -> None:
        msg = self._build(to_email, email, attachment)
        last_error: Exception | None = None
        for attempt in range(1, self._retries + 1):
            try:
                with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self._username, self._password)
                    server.send_message(msg)
                return  # success
            except _RETRYABLE as exc:
                last_error = exc
                if attempt < self._retries:
                    time.sleep(3 * attempt)  # brief backoff, then reconnect fresh
        raise last_error  # all attempts failed
