"""Central configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
HOME_FILE = FRONTEND_DIR / "home.html"

# Feature flags
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "900"))
