"""Load the integration's api.py without importing Home Assistant.

custom_components/downdetector/__init__.py imports homeassistant, so we register
a bare package pointing at the same directory and import api/const through it.
"""

from __future__ import annotations

from pathlib import Path
import sys
import types

PKG_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "downdetector"

if "dd_standalone" not in sys.modules:
    pkg = types.ModuleType("dd_standalone")
    pkg.__path__ = [str(PKG_DIR)]
    sys.modules["dd_standalone"] = pkg
