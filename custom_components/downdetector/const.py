"""Constants for the Downdetector integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "downdetector"

BASE_URL: Final = "https://downdetector.com/"
STATUS_URL: Final = "https://downdetector.com/status/{slug}/"

# Refresh interval (minutes), editable via the options flow slider.
CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 30
MAX_SCAN_INTERVAL: Final = 1440
SCAN_INTERVAL_STEP: Final = 30

# Number of services exposed in the sensor attributes.
TOP_N: Final = 16

# Browser fingerprint used by curl_cffi to get past Cloudflare.
IMPERSONATE: Final = "chrome"
REQUEST_TIMEOUT: Final = 30

STATUS_DANGER: Final = "danger"
STATUS_WARNING: Final = "warning"
IMPACTED_STATUSES: Final = (STATUS_DANGER, STATUS_WARNING)
