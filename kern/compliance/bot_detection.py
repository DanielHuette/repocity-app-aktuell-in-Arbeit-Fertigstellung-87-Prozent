"""Detection of anti-bot measures — and the decision to stop, not evade.

A CAPTCHA, a JS challenge or a WAF interstitial is an unambiguous signal
that the operator does not consent to automated access. This module's job
is to *recognise* those signals so the crawler can abort cleanly.

Nothing here attempts to solve, bypass or fingerprint-spoof around a
protection. That is a deliberate design boundary: circumventing a
technical access control can constitute unauthorised access under
§ 202a StGB (DE) and Art. 6 of the InfoSoc Directive, and it voids the
TDM exception of DSM Art. 4.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_CHALLENGE_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("cloudflare", re.compile(r"cf-browser-verification|cf_chl_|Checking your browser|__cf_bm", re.I)),
    ("recaptcha", re.compile(r"g-recaptcha|recaptcha/api\.js|grecaptcha", re.I)),
    ("hcaptcha", re.compile(r"h-captcha|hcaptcha\.com", re.I)),
    ("turnstile", re.compile(r"cf-turnstile|challenges\.cloudflare\.com/turnstile", re.I)),
    ("datadome", re.compile(r"datadome|dd_cookie_test", re.I)),
    ("perimeterx", re.compile(r"_px[A-Za-z0-9]*|perimeterx", re.I)),
    ("akamai", re.compile(r"_abck|ak_bmsc|akamai bot manager", re.I)),
    ("imperva", re.compile(r"incapsula|_Incap_|visid_incap", re.I)),
    ("generic_captcha", re.compile(r"\bcaptcha\b|Are you a robot|Bist du ein Roboter", re.I)),
    ("login_wall", re.compile(r"Log in to continue|Melde dich an, um fortzufahren", re.I)),
)

_BLOCKING_STATUS = {401, 403, 407, 429, 503}

_BLOCKING_HEADERS = ("cf-mitigated", "x-datadome", "x-iinfo")


@dataclass(frozen=True)
class BotProtectionVerdict:
    detected: bool
    kind: str = ""
    evidence: str = ""

    def __bool__(self) -> bool:
        return self.detected


def detect(
    status_code: int,
    headers: dict[str, str] | None = None,
    body: str = "",
) -> BotProtectionVerdict:
    """Classify a response as bot-protected or clean.

    Only the first ~200 KB of the body is scanned; challenge pages are
    always small, and this bounds the cost on large documents.
    """
    headers = {key.lower(): value for key, value in (headers or {}).items()}

    for header in _BLOCKING_HEADERS:
        if header in headers:
            return BotProtectionVerdict(True, "waf_header", f"header {header!r} present")

    server = headers.get("server", "").lower()
    if status_code in _BLOCKING_STATUS:
        if status_code == 429:
            return BotProtectionVerdict(True, "rate_limited", "HTTP 429 Too Many Requests")
        if "cloudflare" in server:
            return BotProtectionVerdict(
                True, "cloudflare", f"HTTP {status_code} from a Cloudflare edge"
            )
        return BotProtectionVerdict(
            True, "http_block", f"HTTP {status_code} indicates access is refused"
        )

    sample = body[:200_000]
    for kind, pattern in _CHALLENGE_MARKERS:
        match = pattern.search(sample)
        if match:
            return BotProtectionVerdict(True, kind, f"page contains {match.group(0)!r}")

    return BotProtectionVerdict(False)


_NOAI_META = re.compile(
    r"<meta[^>]+name=[\"']?robots[\"']?[^>]*content=[\"'][^\"']*\b(noai|noimageai)\b",
    re.I,
)
_TDM_RESERVATION = re.compile(r"tdm-reservation[\"']?\s*[:=]\s*[\"']?1", re.I)


def has_tdm_optout(body: str, headers: dict[str, str] | None = None) -> tuple[bool, str]:
    """Check for a machine-readable TDM opt-out (EU DSM Art. 4(3)).

    Recognises the ``noai`` robots meta value and the ``tdm-reservation``
    signal from the W3C TDM Reservation Protocol, in the body or in an
    HTTP header.
    """
    headers = {key.lower(): value for key, value in (headers or {}).items()}
    if "tdm-reservation" in headers and headers["tdm-reservation"].strip() == "1":
        return True, "TDM-Reservation HTTP header set to 1"
    sample = body[:200_000]
    if _NOAI_META.search(sample):
        return True, "robots meta tag contains 'noai'"
    if _TDM_RESERVATION.search(sample):
        return True, "TDM reservation policy declared in page"
    return False, ""
