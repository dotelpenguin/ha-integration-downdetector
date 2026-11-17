# Downdetector for Home Assistant

A "pulse" of what's broken on the internet right now, from the **Most reported right now** list on [downdetector.com](https://downdetector.com/) (US).

One sensor, one button:

| Entity | What it is |
|---|---|
| `sensor.downdetector_pulse` | **State:** how many of the top 16 services Downdetector currently flags as an outage (`danger`). **Attributes:** the top 16 with report counts and trend, plus an `impacted` list. |
| `button.downdetector_refresh_now` | Fetches immediately. |

Refresh interval: 30 min by default, adjustable from 30 min to 24 h with a slider (**Settings → Devices & services → Downdetector → Configure**).

## How the numbers work

Downdetector's homepage includes a 24-hour sparkline (96 × 15-minute buckets) for each service. For each one:

- **reports**: latest 15-minute bucket
- **baseline**: median of the last 24 h (what "normal" looks like)
- **trend**: `reports - baseline`, the rough "+/-" jump
- **peak_24h**: highest bucket in the last 24 h
- **status**: Downdetector's own flag: `danger`, `warning` or `success`

These are rough indicators, not exact counts.

### Attributes

```yaml
top_service: Apple Support      # biggest jump among impacted services
top_reports: 1238
top_trend: 1233
impacted_count: 3
calculated_at: "2026-11-17T20:17:46+00:00"
impacted:                        # danger/warning only, biggest trend first
  - rank: 1
    name: Apple Support
    slug: apple-support
    status: danger
    category: info-tools
    reports: 1238
    baseline: 5
    trend: 1233
    peak_24h: 2266
    url: https://downdetector.com/status/apple-support/
services: [...]                  # all top 16, same shape, homepage order
```

`impacted` and `services` aren't written to the recorder database, to keep it small.

## Install (HACS custom repository)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/dotelpenguin/ha-integration-downdetector`, type **Integration**.
2. Install **Downdetector**, restart Home Assistant.
3. **Settings → Devices & services → Add integration → Downdetector**.

Requires Home Assistant 2025.2 or newer on 64-bit hardware (x86_64 or aarch64). It uses [`curl_cffi`](https://github.com/lexiforest/curl_cffi) to fetch the page with a browser-like connection, because Downdetector's Cloudflare protection rejects plain HTTP clients.

## Dashboard: top 5 impacted

```yaml
type: markdown
title: Internet pulse
content: >
  {% set items = state_attr('sensor.downdetector_pulse', 'impacted') or [] %}
  {% if items %}
  {% for s in items[:5] %}
  - [{{ s.name }}]({{ s.url }}): **{{ s.reports }}** reports ({{ '%+d' % s.trend }} vs normal)
  {% endfor %}
  {% else %}
  All quiet.
  {% endif %}
```

## Automation: sudden jump

```yaml
alias: Downdetector spike
triggers:
  - trigger: numeric_state
    entity_id: sensor.downdetector_pulse
    attribute: top_trend
    above: 1000
actions:
  - action: notify.notify
    data:
      title: "Possible outage: {{ state_attr('sensor.downdetector_pulse', 'top_service') }}"
      message: >
        {{ state_attr('sensor.downdetector_pulse', 'top_reports') }} reports
        ({{ '%+d' % state_attr('sensor.downdetector_pulse', 'top_trend') }} vs normal)
```

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install curl_cffi pytest
.venv/bin/python scripts/fetch_fixture.py   # saves a live page + prints the parsed top 16
.venv/bin/python -m pytest tests
```

If the integration starts failing, download diagnostics from the integration page. They include the last HTTP status and the parsed data.

## Disclaimer

Not affiliated with Downdetector or Ookla. This reads a public web page that can change without notice. Keep the refresh interval reasonable.
# ha-integration-downdetector
# ha-integration-downdetector
# ha-integration-downdetector
