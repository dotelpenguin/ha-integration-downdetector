"""Downdetector client and homepage parser.

This module has no Home Assistant imports so it can be unit-tested on its own.

The downdetector.com homepage is a Next.js (app router) page. The "Most
reported right now" list is embedded in React Server Component payload chunks:

    <script>self.__next_f.push([1,"...JSON-escaped text..."])</script>

Somewhere in the concatenated payload is ``"topCompanies":[{...}, ...]`` where
each company has ``stats.sparkline``: 96 report counts covering the last 24 h
in 15-minute buckets (last element = most recent).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
import statistics
from typing import Any

from .const import (
    BASE_URL,
    IMPACTED_STATUSES,
    IMPERSONATE,
    REQUEST_TIMEOUT,
    STATUS_DANGER,
    STATUS_URL,
)

_PUSH_RE = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', re.S)


class DowndetectorError(Exception):
    """Base error."""


class DowndetectorBlockedError(DowndetectorError):
    """Request was rejected (Cloudflare / rate limit)."""

    def __init__(self, status: int) -> None:
        super().__init__(f"Downdetector rejected the request (HTTP {status})")
        self.status = status


class DowndetectorParseError(DowndetectorError):
    """Page was fetched but the expected data was not found."""


@dataclass(slots=True)
class ServiceReport:
    """One service from the "most reported" list."""

    rank: int
    name: str
    slug: str
    status: str
    category: str | None
    reports: int
    baseline: int
    trend: int
    peak_24h: int
    url: str

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict for state attributes."""
        return asdict(self)


@dataclass(slots=True)
class Snapshot:
    """Parsed homepage data."""

    services: list[ServiceReport]
    calculated_at: str | None = None
    total_listed: int = 0
    raw_count: int = field(default=0, repr=False)

    def top(self, n: int) -> list[ServiceReport]:
        """Top *n* services in homepage order."""
        return self.services[:n]

    def impacted(self, n: int) -> list[ServiceReport]:
        """Services among the top *n* in danger/warning state, biggest jump first."""
        return sorted(
            (s for s in self.top(n) if s.status in IMPACTED_STATUSES),
            key=lambda s: s.trend,
            reverse=True,
        )

    def danger_count(self, n: int) -> int:
        """Number of services among the top *n* in danger state."""
        return sum(1 for s in self.top(n) if s.status == STATUS_DANGER)


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def extract_rsc_payload(html: str) -> str:
    """Concatenate and unescape all ``self.__next_f.push([1, "..."])`` chunks."""
    chunks = _PUSH_RE.findall(html)
    if not chunks:
        raise DowndetectorParseError("No Next.js data chunks found in page")
    try:
        return "".join(json.loads(f'"{chunk}"') for chunk in chunks)
    except json.JSONDecodeError as err:
        raise DowndetectorParseError(f"Could not unescape page data: {err}") from err


def extract_json_array(text: str, key: str) -> list[Any]:
    """Find ``"key":[ ... ]`` in *text* and return the decoded array."""
    idx = text.find(f'"{key}":')
    if idx < 0:
        raise DowndetectorParseError(f'"{key}" not found in page data')
    start = text.find("[", idx)
    if start < 0:
        raise DowndetectorParseError(f'"{key}" is not followed by an array')

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError as err:
                    raise DowndetectorParseError(
                        f'Could not decode "{key}": {err}'
                    ) from err
    raise DowndetectorParseError(f'Unterminated "{key}" array')


def compute_metrics(sparkline: list[Any]) -> tuple[int, int, int, int]:
    """Return (reports, baseline, trend, peak) from a 24 h sparkline.

    reports  = latest bucket
    baseline = median of the 24 h window (robust against the spike itself)
    trend    = reports - baseline
    """
    values = [int(v) for v in sparkline if isinstance(v, (int, float))]
    if not values:
        return 0, 0, 0, 0
    reports = values[-1]
    baseline = round(statistics.median(values))
    return reports, baseline, reports - baseline, max(values)


def parse_homepage(html: str) -> Snapshot:
    """Parse the downdetector.com homepage HTML into a Snapshot."""
    payload = extract_rsc_payload(html)
    companies = extract_json_array(payload, "topCompanies")
    if not isinstance(companies, list) or not companies:
        raise DowndetectorParseError('"topCompanies" is empty')

    services: list[ServiceReport] = []
    calculated_at: str | None = None
    for company in companies:
        if not isinstance(company, dict) or not company.get("slug"):
            continue
        stats = company.get("stats") or {}
        reports, baseline, trend, peak = compute_metrics(stats.get("sparkline") or [])
        calculated_at = calculated_at or stats.get("stats24CalculatedAt")
        slug = str(company["slug"])
        services.append(
            ServiceReport(
                rank=len(services) + 1,
                name=str(company.get("name") or slug),
                slug=slug,
                status=str(stats.get("status") or "unknown"),
                category=(company.get("category") or {}).get("slug"),
                reports=reports,
                baseline=baseline,
                trend=trend,
                peak_24h=peak,
                url=STATUS_URL.format(slug=slug),
            )
        )

    if not services:
        raise DowndetectorParseError("No usable services in topCompanies")
    return Snapshot(
        services=services,
        calculated_at=calculated_at,
        total_listed=len(services),
        raw_count=len(companies),
    )


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #


class DowndetectorClient:
    """Fetches the homepage using curl_cffi browser impersonation."""

    def __init__(
        self,
        url: str = BASE_URL,
        impersonate: str = IMPERSONATE,
        timeout: int = REQUEST_TIMEOUT,
    ) -> None:
        self._url = url
        self._impersonate = impersonate
        self._timeout = timeout
        self.last_html_size: int | None = None
        self.last_status: int | None = None

    async def async_fetch_html(self) -> str:
        """Download the homepage HTML."""
        # Imported lazily so the parser can be used without curl_cffi installed.
        from curl_cffi.requests import AsyncSession  # noqa: PLC0415
        from curl_cffi.requests.exceptions import RequestException  # noqa: PLC0415

        try:
            async with AsyncSession(impersonate=self._impersonate) as session:
                resp = await session.get(self._url, timeout=self._timeout)
        except RequestException as err:
            raise DowndetectorError(f"Request failed: {err}") from err

        self.last_status = resp.status_code
        if resp.status_code in (403, 429, 503):
            raise DowndetectorBlockedError(resp.status_code)
        if resp.status_code != 200:
            raise DowndetectorError(f"Unexpected HTTP {resp.status_code}")
        self.last_html_size = len(resp.text)
        return resp.text

    async def async_get_snapshot(self) -> Snapshot:
        """Fetch and parse."""
        return parse_homepage(await self.async_fetch_html())
