"""The compliance gate every outbound request must pass.

Layered checks, cheapest and most decisive first:

1. **Scheme / host sanity** - no ``file://``, no private network ranges.
2. **Denylist** - hosts whose terms of service forbid automated access.
   Encoded as data, not as scattered ``if`` statements, so the policy is
   auditable in one place.
3. **Allowlist** - if configured, nothing outside it is fetched.
4. **robots.txt** - handled by :mod:`isi.compliance.robots`.
5. **Response-time checks** - bot protection and TDM opt-out, evaluated
   after the response arrives, in :mod:`isi.compliance.bot_detection`.

Every refusal returns a *reason*, which is logged and surfaced in the
CLI. A silent block would be worse than useless.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from .robots import RobotsCache

#: Hosts whose ToS prohibit scraping or which are gated behind an
#: authenticated API. Fetching these is refused before any network call.
DEFAULT_DENYLIST: dict[str, str] = {
    "x.com": "ToS prohibit automated collection; robots.txt disallows crawlers; no free API",
    "twitter.com": "see x.com - ToS prohibit scraping",
    "www.instagram.com": "ToS prohibit automated collection; login wall",
    "instagram.com": "ToS prohibit automated collection; login wall",
    "www.facebook.com": "ToS prohibit automated collection; login wall",
    "facebook.com": "ToS prohibit automated collection; login wall",
    "www.linkedin.com": "ToS prohibit scraping; hiQ v. LinkedIn notwithstanding, EU ToS apply",
    "linkedin.com": "ToS prohibit scraping",
    "www.tiktok.com": "ToS prohibit automated collection",
    "tiktok.com": "ToS prohibit automated collection",
}

#: Openly licensed sources used as the project's demo corpus.
REFERENCE_SOURCES: dict[str, str] = {
    "de.wikipedia.org": "CC BY-SA 4.0",
    "en.wikipedia.org": "CC BY-SA 4.0",
    "eur-lex.europa.eu": "EU reuse policy, Decision 2011/833/EU",
    "arxiv.org": "per-paper licence, metadata CC0",
    "data.europa.eu": "open data portal",
    "www.gutenberg.org": "public domain",
}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    stage: str
    crawl_delay: float = 0.0

    def __bool__(self) -> bool:
        return self.allowed


def _is_private_host(host: str) -> bool:
    """Block SSRF-style targets: localhost, RFC1918, link-local."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return True
    return False


class CompliancePolicy:
    """Decides whether a URL may be fetched, and why not if it may not."""

    def __init__(
        self,
        user_agent: str,
        respect_robots: bool = True,
        default_delay: float = 2.0,
        denylist: list[str] | None = None,
        allowlist: list[str] | None = None,
        timeout: float = 20.0,
        block_private_hosts: bool = True,
    ) -> None:
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.block_private_hosts = block_private_hosts
        self.denylist = {**DEFAULT_DENYLIST}
        for host in denylist or []:
            self.denylist.setdefault(host.lower(), "configured denylist entry")
        self.allowlist = {host.lower() for host in (allowlist or [])}
        self.robots = RobotsCache(
            user_agent=user_agent, timeout=timeout, default_delay=default_delay
        )

    def check(self, url: str) -> PolicyDecision:
        parts = urlparse(url)
        host = (parts.netloc or "").lower().split(":")[0]

        if parts.scheme not in ("http", "https"):
            return PolicyDecision(False, f"scheme {parts.scheme!r} is not permitted", "scheme")
        if not host:
            return PolicyDecision(False, "URL has no host", "scheme")

        if self.block_private_hosts and _is_private_host(host):
            return PolicyDecision(
                False, "host resolves to a private or loopback address", "network"
            )

        for denied, reason in self.denylist.items():
            if host == denied or host.endswith(f".{denied}"):
                return PolicyDecision(False, reason, "denylist")

        if self.allowlist and not any(
            host == allowed or host.endswith(f".{allowed}") for allowed in self.allowlist
        ):
            return PolicyDecision(False, "host is not on the configured allowlist", "allowlist")

        if not self.respect_robots:
            # Available for sites you own. Loud on purpose.
            return PolicyDecision(True, "robots.txt checking disabled in config", "robots")

        decision = self.robots.check(url)
        return PolicyDecision(
            allowed=decision.allowed,
            reason=decision.reason,
            stage="robots",
            crawl_delay=decision.crawl_delay,
        )

    def wait(self, url: str, delay: float) -> float:
        return self.robots.wait(url, delay)
