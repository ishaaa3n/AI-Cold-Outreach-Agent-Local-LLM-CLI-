"""Optional company research: web-search a company and return raw snippet text
for the drafter to distill into ONE honest personalization sentence.

Keyless, best-effort, multi-backend (DuckDuckGo HTML → Lite → Bing). Any failure
is swallowed — research is a bonus, never a blocker.
"""
from __future__ import annotations

import re
from html import unescape

import httpx

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-OS-outreach/0.1)"}
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# (name, url, method)
_BACKENDS = [
    ("ddg-html", "https://html.duckduckgo.com/html/", "post"),
    ("ddg-lite", "https://lite.duckduckgo.com/lite/", "post"),
    ("bing", "https://www.bing.com/search", "get"),
]


def _visible_text(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    return _WS_RE.sub(" ", unescape(text)).strip()


def search_company(company: str, timeout: float = 10.0) -> str:
    """Return concatenated visible snippet text from search backends (best-effort)."""
    if not company:
        return ""
    query = f"{company} company what they do products"
    chunks: list[str] = []
    try:
        with httpx.Client(timeout=timeout, headers=_HEADERS, follow_redirects=True) as client:
            for name, url, method in _BACKENDS:
                try:
                    if method == "post":
                        r = client.post(url, data={"q": query})
                    else:
                        r = client.get(url, params={"q": query})
                except Exception:
                    continue
                if r.status_code < 400 and len(r.text) > 500:
                    chunks.append(_visible_text(r.text))
                if sum(len(c) for c in chunks) > 6000:
                    break
    except Exception:
        return ""
    return "\n".join(chunks)[:6000]
