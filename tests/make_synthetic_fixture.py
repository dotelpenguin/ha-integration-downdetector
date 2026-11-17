"""Build tests/fixtures/homepage_synthetic.html in the same shape as the live page.

The live homepage embeds data as Next.js RSC chunks:
    <script>self.__next_f.push([1,"<json-escaped text>"])</script>
This mimics that, splitting the payload across several chunks (including mid-array)
so the parser's chunk-joining is exercised.
"""

from __future__ import annotations

import json
from pathlib import Path

SPIKE = [5] * 80 + [123, 49, 30, 14, 17, 3, 124, 658, 1285, 1836, 2266, 2130, 1708, 1613, 1473, 1238]
FLAT = [3, 4, 2, 5, 3] * 19 + [4]
RISING = [10] * 90 + [40, 80, 150, 260, 380, 512]

COMPANIES = [
    ("43140", "Apple Support", "apple-support", "info-tools", "danger", SPIKE),
    ("46293", "Apple Pay", "apple-pay", "payments", "danger", RISING),
    ("10205", "Microsoft Outlook", "outlook", "email", "warning", [20] * 95 + [60]),
    ("20049", "iCloud", "icloud", "cloud", "success", FLAT),
] + [
    (str(1000 + i), f'Service "{i}"', f"service-{i}", "misc", "success", FLAT)
    for i in range(20)
]


def build() -> str:
    top = [
        {
            "__typename": "CompanyType",
            "id": cid,
            "name": name,
            "logo": f"logo/{slug}_tile.webp",
            "slug": slug,
            "category": {"__typename": "CategoryType", "slug": cat},
            "stats": {
                "__typename": "CompanyStatsType",
                "correlationOutage": None,
                "status": status,
                "sparkline": spark,
                "stats24CalculatedAt": "2026-11-17T20:17:46+00:00",
            },
        }
        for cid, name, slug, cat, status, spark in COMPANIES
    ]
    payload = (
        '1:"$Sreact.fragment"\n2:I[68172,[],""]\n'
        + '5:["$","div",null,{"trendingSearches":[{"id":"43140","name":"Apple Support","slug":"apple-support"}]}]\n'
        + '6:["$","$L136",null,{"topCompanies":'
        + json.dumps(top, separators=(",", ":"))
        + "}]\n"
    )
    cut1, cut2 = len(payload) // 3, 2 * len(payload) // 3
    parts = [payload[:cut1], payload[cut1:cut2], payload[cut2:]]
    scripts = "".join(
        f"<script>self.__next_f.push([1,{json.dumps(p)}])</script>" for p in parts
    )
    return (
        "<!DOCTYPE html><html><head><title>Downdetector</title></head><body>"
        '<script>(self.__next_f=self.__next_f||[]).push([0])</script>'
        f"{scripts}</body></html>"
    )


if __name__ == "__main__":
    out = Path(__file__).parent / "fixtures" / "homepage_synthetic.html"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out}")
