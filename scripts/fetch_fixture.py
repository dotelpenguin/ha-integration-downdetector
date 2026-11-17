"""Fetch the live downdetector.com homepage, save it as a test fixture and print a summary.

Usage (from the repo root):
    python3 -m venv .venv && .venv/bin/pip install curl_cffi pytest
    .venv/bin/python scripts/fetch_fixture.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
pkg = types.ModuleType("dd_standalone")
pkg.__path__ = [str(ROOT / "custom_components" / "downdetector")]
sys.modules["dd_standalone"] = pkg

from dd_standalone.api import DowndetectorClient, parse_homepage  # noqa: E402


async def main() -> None:
    client = DowndetectorClient()
    html = await client.async_fetch_html()
    out = ROOT / "tests" / "fixtures" / "homepage_live.html"
    out.write_text(html, encoding="utf-8")
    print(f"HTTP {client.last_status}, {len(html):,} bytes -> {out}")

    snap = parse_homepage(html)
    print(f"{snap.total_listed} services, calculated_at={snap.calculated_at}")
    print(f"danger in top 16: {snap.danger_count(16)}\n")
    print(f"{'#':>2}  {'service':<28} {'status':<8} {'now':>6} {'base':>5} {'trend':>7} {'peak':>6}")
    for s in snap.top(16):
        print(f"{s.rank:>2}  {s.name[:28]:<28} {s.status:<8} {s.reports:>6} {s.baseline:>5} {s.trend:>+7} {s.peak_24h:>6}")


if __name__ == "__main__":
    asyncio.run(main())
