"""Command-line entrypoint: init / draft / run."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from openai import APIConnectionError

from . import config as cfg
from . import contacts as contacts_mod
from . import sent_log
from .drafting import Drafter, Email, has_placeholder
from .mailer import Mailer
from .resume import extract_resume_text

_PLACEHOLDER_SECRETS = {"", "you@gmail.com", "xxxx xxxx xxxx xxxx", "Your Name"}


def _check_smtp_configured(config) -> str | None:
    """Return an error string if SMTP/sender still holds template placeholders."""
    if config.smtp.get("username", "") in _PLACEHOLDER_SECRETS:
        return "smtp.username is not set in outreach.yaml"
    if config.smtp.get("app_password", "").strip() in _PLACEHOLDER_SECRETS:
        return "smtp.app_password is not set (create a Gmail App Password)"
    if config.sender.get("email", "") in _PLACEHOLDER_SECRETS:
        return "sender.email is not set in outreach.yaml"
    return None


def _safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:40] or "contact"


def cmd_init(args) -> int:
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    cfg_path = root / cfg.CONFIG_NAME
    if cfg_path.exists() and not args.force:
        print(f"{cfg_path} already exists (use --force to overwrite).")
    else:
        cfg_path.write_text(cfg.TEMPLATE, encoding="utf-8")
        print(f"Wrote {cfg_path}")
    xlsx = root / "contacts.xlsx"
    if xlsx.exists() and not args.force:
        print(f"{xlsx} already exists.")
    else:
        contacts_mod.write_template(xlsx)
        print(f"Wrote {xlsx} (fill in your HR contacts)")
    (root / "outbox").mkdir(exist_ok=True)
    print("\nNext steps:")
    print(f"  1. Put your resume in {root} (e.g. resume.pdf)")
    print(f"  2. Edit {cfg.CONFIG_NAME} (sender info + Gmail App Password)")
    print("  3. Fill contacts.xlsx")
    print("  4. Preview:  python -m outreach_cli draft")
    print("  5. Send:     python -m outreach_cli run")
    return 0


def _prepare(args):
    """Shared setup for draft/run: config, resume profile, filtered contacts."""
    config = cfg.load_config(Path(args.root))
    resume_text = extract_resume_text(config.resume_path)
    all_contacts = contacts_mod.read_contacts(config.contacts_path)

    if args.only:
        needle = args.only.lower()
        all_contacts = [
            c for c in all_contacts
            if needle in c.company.lower() or needle in c.name.lower()
        ]

    already = sent_log.load_sent_emails(config.sent_log)
    fresh = [c for c in all_contacts if c.email.lower() not in already]
    skipped = len(all_contacts) - len(fresh)

    drafter = Drafter(
        base_url=config.model["base_url"],
        model=config.model["name"],
        sender_name=config.sender["name"],
        signature=config.sender.get("signature", ""),
        tone=config.tone,
        subject_template=config.subject,
        temperature=float(config.model.get("temperature", 0.0)),
        api_key=config.model.get("api_key", "ollama"),
    )
    print(f"Building profile from {config.resume_path.name}…")
    drafter.build_profile(resume_text)
    return config, drafter, fresh, skipped


def _research_enabled(args, config) -> bool:
    return bool(getattr(args, "research", False) or config.sending.get("research", False))


def cmd_draft(args) -> int:
    config, drafter, contacts, skipped = _prepare(args)
    config.outbox.mkdir(exist_ok=True)
    research = _research_enabled(args, config)
    print(f"{len(contacts)} to draft ({skipped} already sent, skipped)."
          f"{' Researching each company…' if research else ''}\n")
    for c in contacts:
        info = drafter.research_company(c.company) if research else ""
        email = drafter.draft(c, company_info=info)
        leak = has_placeholder(email)
        flag = f"  ⚠ placeholder {leak}" if leak else ""
        fname = config.outbox / f"{_safe_name(c.company)}_{_safe_name(c.name)}.txt"
        fname.write_text(
            f"To: {c.name} <{c.email}>\nSubject: {email.subject}\n\n{email.body}\n",
            encoding="utf-8",
        )
        print(f"  ✓ {c.email:35} {email.subject}{flag}")
    print(f"\nDrafts written to {config.outbox}. Review, then run:  python -m outreach_cli run")
    return 0


def cmd_run(args) -> int:
    config, drafter, contacts, skipped = _prepare(args)
    limit = args.limit or int(config.sending.get("daily_limit", 40))
    contacts = contacts[:limit]
    throttle = int(config.sending.get("throttle_seconds", 45))
    attach = config.resume_path if config.sending.get("attach_resume", True) else None

    print(f"\n{len(contacts)} to send ({skipped} already sent, skipped). "
          f"Throttle {throttle}s, model {config.model['name']}.")
    if args.dry_run:
        print("DRY RUN — nothing will actually send.\n")
    elif not args.yes:
        answer = input(f"Send {len(contacts)} emails via {config.smtp['username']}? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return 1

    mailer = None
    if not args.dry_run:
        mailer = Mailer(config.smtp, config.sender["name"], config.sender["email"])

    research = _research_enabled(args, config)
    sent = failed = 0
    for i, c in enumerate(contacts):
        info = drafter.research_company(c.company) if research else ""
        email = drafter.draft(c, company_info=info)
        leak = has_placeholder(email)
        if leak:
            print(f"  ⚠ SKIP {c.email}: leaked placeholder {leak!r}")
            sent_log.append(config.sent_log, email=c.email, name=c.name,
                            company=c.company, subject=email.subject, status="skipped-placeholder")
            failed += 1
            continue
        try:
            if args.dry_run:
                print(f"  [dry] would send → {c.email:35} {email.subject}")
            else:
                mailer.send(c.email, email, attach)
                print(f"  ✓ sent → {c.email:35} {email.subject}")
                sent_log.append(config.sent_log, email=c.email, name=c.name,
                                company=c.company, subject=email.subject, status="sent")
            sent += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ FAILED {c.email}: {exc}")
            sent_log.append(config.sent_log, email=c.email, name=c.name,
                            company=c.company, subject=email.subject, status="failed")
            failed += 1
        if throttle and not args.dry_run and i < len(contacts) - 1:
            time.sleep(throttle)

    print(f"\nDone. {sent} sent, {failed} failed/skipped.")
    return 0


def cmd_test(args) -> int:
    """Send one clearly-marked test email to verify the Gmail SMTP path."""
    config = cfg.load_config(Path(args.root))
    problem = _check_smtp_configured(config)
    if problem:
        print(f"Cannot send test: {problem}.")
        print("Edit outreach.yaml (sender + smtp) then retry.")
        return 2

    to = args.to or config.sender["email"]
    attach = None
    if config.resume_path.exists():
        attach = config.resume_path
        note = f"Your resume ({config.resume_path.name}) is attached to confirm attachments work."
    else:
        note = "No resume file found, so nothing is attached (that's fine for this test)."

    email = Email(
        subject="[Outreach CLI] Test email — send path works ✅",
        body=(
            "This is a test from the AI-OS Outreach CLI.\n\n"
            "If you're reading this in your inbox (not spam), your Gmail App Password, "
            "SMTP settings, and sending all work.\n\n"
            f"{note}\n\n"
            "— sent by `outreach_cli test`"
        ),
    )

    print(f"Sending test email to {to} via {config.smtp['username']}…")
    try:
        mailer = Mailer(config.smtp, config.sender["name"], config.sender["email"])
        mailer.send(to, email, attach)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        print(f"FAILED: {msg}")
        if "535" in msg or "auth" in msg.lower() or "username and password" in msg.lower():
            print("Hint: Gmail rejected the login. Use a 16-char App Password (not your "
                  "normal password), and make sure 2-Step Verification is on.")
        return 1
    print(f"Sent. Check {to} — and peek in Spam; if it's there, warm up before bulk sending.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="outreach_cli", description="Cold-outreach agent")
    p.add_argument("--root", default=".", help="project directory (default: current)")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("init", help="write config + contacts template")
    pi.add_argument("--force", action="store_true")
    pi.set_defaults(func=cmd_init)

    pd = sub.add_parser("draft", help="generate drafts to outbox/ (no sending)")
    pd.add_argument("--only", help="filter to a company/name substring")
    pd.add_argument("--research", action="store_true", help="web-search each company to personalize")
    pd.set_defaults(func=cmd_draft)

    pr = sub.add_parser("run", help="draft AND send (full auto, throttled)")
    pr.add_argument("--only", help="filter to a company/name substring")
    pr.add_argument("--limit", type=int, help="max emails this run")
    pr.add_argument("--dry-run", action="store_true", help="simulate; do not send")
    pr.add_argument("--yes", action="store_true", help="skip the batch confirmation")
    pr.add_argument("--research", action="store_true", help="web-search each company to personalize")
    pr.set_defaults(func=cmd_run)

    pt = sub.add_parser("test", help="send one test email (default: to yourself)")
    pt.add_argument("--to", help="recipient (default: sender.email from config)")
    pt.set_defaults(func=cmd_test)
    return p


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to cp1252 and choke on ✓/⚠; force UTF-8.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except APIConnectionError:
        print(
            "\n"
            "======================================================\n"
            " Can't reach the local AI model (Ollama is not running).\n"
            "======================================================\n"
            " Fix it, then try again:\n"
            "   1. Start Ollama — open the Ollama app from your Start menu\n"
            "      (or run  ollama serve  in a terminal).\n"
            "   2. Make sure a model is installed:  ollama list\n",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
