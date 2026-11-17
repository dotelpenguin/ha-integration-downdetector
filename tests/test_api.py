"""Parser tests (no network, no Home Assistant)."""

from __future__ import annotations

from pathlib import Path

import pytest

from dd_standalone.api import (  # type: ignore[import-not-found]
    DowndetectorParseError,
    compute_metrics,
    extract_json_array,
    parse_homepage,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_compute_metrics_spike() -> None:
    reports, baseline, trend, peak = compute_metrics([5] * 90 + [100, 500, 1200, 2000, 1500, 1238])
    assert reports == 1238
    assert baseline == 5
    assert trend == 1233
    assert peak == 2000


def test_compute_metrics_empty() -> None:
    assert compute_metrics([]) == (0, 0, 0, 0)


def test_extract_json_array_handles_brackets_in_strings() -> None:
    text = 'x"topCompanies":[{"name":"a]b[c\\"}"}, {"n":[1,2]}]tail'
    assert extract_json_array(text, "topCompanies") == [{"name": 'a]b[c"}'}, {"n": [1, 2]}]


def test_parse_synthetic_fixture() -> None:
    html = (FIXTURES / "homepage_synthetic.html").read_text(encoding="utf-8")
    snap = parse_homepage(html)

    assert snap.total_listed == 24
    first = snap.services[0]
    assert (first.rank, first.name, first.slug, first.status) == (1, "Apple Support", "apple-support", "danger")
    assert first.reports == 1238
    assert first.baseline == 5
    assert first.trend == 1233
    assert first.peak_24h == 2266
    assert first.url == "https://downdetector.com/status/apple-support/"
    assert snap.calculated_at == "2026-11-17T20:17:46+00:00"

    # Names with quotes survive the double unescape.
    assert snap.services[4].name == 'Service "0"'

    assert len(snap.top(16)) == 16
    assert snap.danger_count(16) == 2
    impacted = snap.impacted(16)
    assert [s.slug for s in impacted] == ["apple-support", "apple-pay", "outlook"]


def test_parse_rejects_non_nextjs_page() -> None:
    with pytest.raises(DowndetectorParseError):
        parse_homepage("<html><body>Just a moment...</body></html>")


@pytest.mark.skipif(
    not (FIXTURES / "homepage_live.html").exists(),
    reason="run scripts/fetch_fixture.py to capture a live page",
)
def test_parse_live_fixture() -> None:
    snap = parse_homepage((FIXTURES / "homepage_live.html").read_text(encoding="utf-8"))
    assert snap.total_listed >= 16
    for svc in snap.top(16):
        assert svc.name and svc.slug
        assert svc.status in {"danger", "warning", "success"}
        assert svc.reports >= 0 and svc.peak_24h >= svc.reports
