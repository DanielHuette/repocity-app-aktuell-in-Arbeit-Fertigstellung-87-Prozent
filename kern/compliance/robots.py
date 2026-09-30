"""robots.txt handling: RFC 9309 matching, per-host caching, crawl-delay.

Why this exists
---------------
``robots.txt`` is the machine-readable expression of a site operator's
will. Under the EU DSM Directive (2019/790) Art. 4(3), a rightsholder may
reserve text-and-data-mining rights "in an appropriate manner, such as
machine-readable means" — robots.txt and ``noai`` meta tags are exactly
that. Ignoring them does not merely breach etiquette; it removes the
Art. 4 TDM exception that would otherwise make the copying lawful.

Why not ``urllib.robotparser``
------------------------------
The standard library matches rule paths with a plain ``startswith`` and
silently ignores the ``*`` and ``$`` wildcards that RFC 9309 §2.2.3
defines. That is not merely pedantic. Hacker News publishes::

    User-agent: *
    Allow: /*.json$
    Disallow: /

The stdlib parser cannot match the ``Allow`` line, falls through to
``Disallow: /`` and refuses an endpoint the operator explicitly opened.
Over-blocking is the safe failure direction, but it is still wrong, so
this module implements the specified matching itself:

* ``*`` matches any sequence of characters, ``$`` anchors the end;
* the **longest matching rule** wins (§2.2.2);
* on equal length, ``Allow`` beats ``Disallow``;
* the most specific matching user-agent group is used, ``*`` as fallback.
"""

from __future__ import annotations

import contextlib
import re
import time
from dataclasses import dataclass, field
from urllib.parse import unquote, urlparse

import requests


@dataclass
class RobotsDecision:
    allowed: bool
    reason: str
    crawl_delay: float = 0.0
    robots_url: str = ""


@dataclass(frozen=True)
class _Rule:
    allow: bool
    path: str
    pattern: re.Pattern[str]

    @property
    def specificity(self) -> int:
        return len(self.path)


def _compile(path: str) -> re.Pattern[str]:
    """Translate an RFC 9309 rule path into a regex."""
    anchored_end = path.endswith("$")
    if anchored_end:
        path = path[:-1]
    parts = [re.escape(segment) for segment in path.split("*")]
    body = ".*".join(parts)
    return re.compile(f"^{body}$" if anchored_end else f"^{body}")


class RobotsGroup:
    """The parsed rules of one robots.txt, for one user-agent."""

    def __init__(self) -> None:
        self.rules: list[_Rule] = []
        self.crawl_delay: float | None = None

    def add(self, allow: bool, path: str) -> None:
        path = path.strip()
        if not path:
            # "Disallow:" with an empty value means "allow everything".
            if not allow:
                return
            path = "/"
        if not path.startswith("/"):
            path = "/" + path
        self.rules.append(_Rule(allow, path, _compile(path)))

    def allows(self, path: str) -> tuple[bool, str]:
        best: _Rule | None = None
        for rule in self.rules:
            if not rule.pattern.match(path):
                continue
            if best is None or rule.specificity > best.specificity:
                best = rule
            elif rule.specificity == best.specificity and rule.allow:
                best = rule  # ties go to Allow (RFC 9309 §2.2.2)
        if best is None:
            return True, "no matching rule in robots.txt"
        verb = "Allow" if best.allow else "Disallow"
        return best.allow, f"{verb}: {best.path} in robots.txt"


def parse_robots(text: str, user_agent: str) -> RobotsGroup:
    """Parse robots.txt and return the group applying to ``user_agent``."""
    token = user_agent.split("/")[0].strip().lower()
    groups: dict[str, RobotsGroup] = {}
    current: list[str] = []
    expecting_agent = True

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field_name, _, value = line.partition(":")
        field_name = field_name.strip().lower()
        value = value.strip()

        if field_name == "user-agent":
            if not expecting_agent:
                current = []
                expecting_agent = True
            agent = value.lower()
            current.append(agent)
            groups.setdefault(agent, RobotsGroup())
            continue

        if not current:
            continue
        expecting_agent = False

        for agent in current:
            group = groups[agent]
            if field_name == "disallow":
                group.add(False, value)
            elif field_name == "allow":
                group.add(True, value)
            elif field_name == "crawl-delay":
                with contextlib.suppress(ValueError):
                    group.crawl_delay = float(value)
            elif field_name == "request-rate":
                # e.g. "1/10s" -> one request per 10 seconds
                match = re.match(r"(\d+)\s*/\s*(\d+)", value)
                if match and int(match.group(1)):
                    group.crawl_delay = int(match.group(2)) / int(match.group(1))

    # Most specific matching agent first, then the '*' fallback.
    for agent in sorted(groups, key=len, reverse=True):
        if agent != "*" and agent in token:
            return groups[agent]
    return groups.get("*", RobotsGroup())


@dataclass
class RobotsCache:
    """Fetches, caches and applies robots.txt rules per host."""

    user_agent: str
    timeout: float = 20.0
    default_delay: float = 2.0
    fail_closed: bool = True
    """If robots.txt is unreachable, refuse rather than assume consent."""

    _groups: dict[str, RobotsGroup | None] = field(default_factory=dict, repr=False)
    _last_request: dict[str, float] = field(default_factory=dict, repr=False)

    # ---- fetching ------------------------------------------------------
    def _robots_url(self, url: str) -> str:
        parts = urlparse(url)
        return f"{parts.scheme}://{parts.netloc}/robots.txt"

    def _group_for(self, url: str) -> RobotsGroup | None:
        host = urlparse(url).netloc
        if host in self._groups:
            return self._groups[host]

        group: RobotsGroup | None = None
        try:
            response = requests.get(
                self._robots_url(url),
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
            )
            if response.status_code == 200:
                group = parse_robots(response.text, self.user_agent)
            elif response.status_code in (401, 403):
                # Explicitly protected: treat as a full disallow.
                group = parse_robots("User-agent: *\nDisallow: /", self.user_agent)
            elif 400 <= response.status_code < 500:
                # 404 and friends: RFC 9309 §2.3.1.3 - no restrictions.
                group = RobotsGroup()
        except requests.RequestException:
            group = None

        self._groups[host] = group
        return group

    # ---- decisions -----------------------------------------------------
    def check(self, url: str) -> RobotsDecision:
        robots_url = self._robots_url(url)
        parts = urlparse(url)
        if parts.scheme not in ("http", "https"):
            return RobotsDecision(
                False, f"unsupported scheme {parts.scheme!r}", robots_url=robots_url
            )

        group = self._group_for(url)
        if group is None:
            if self.fail_closed:
                return RobotsDecision(
                    False,
                    "robots.txt could not be retrieved - refusing (fail-closed)",
                    robots_url=robots_url,
                )
            return RobotsDecision(
                True, "robots.txt unavailable, fail-open configured",
                self.default_delay, robots_url,
            )

        path = unquote(parts.path or "/")
        if parts.query:
            path = f"{path}?{parts.query}"
        allowed, reason = group.allows(path)
        delay = max(float(group.crawl_delay or 0.0), self.default_delay)

        return RobotsDecision(
            allowed=allowed,
            reason=("allowed - " if allowed else "disallowed - ") + reason,
            crawl_delay=delay,
            robots_url=robots_url,
        )

    # ---- politeness ----------------------------------------------------
    def wait(self, url: str, delay: float) -> float:
        """Block until ``delay`` seconds have passed since the last hit."""
        host = urlparse(url).netloc
        now = time.monotonic()
        previous = self._last_request.get(host)
        slept = 0.0
        if previous is not None:
            remaining = delay - (now - previous)
            if remaining > 0:
                time.sleep(remaining)
                slept = remaining
        self._last_request[host] = time.monotonic()
        return slept
