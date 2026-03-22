"""Shared test configuration and fixtures.

Heavy external dependencies (claude_agent_sdk, gitpython, redis, aiomysql) may
not be present in a CI / lightweight test environment.  We register lightweight
stubs in sys.modules *before* any app module is imported so that the real
packages are never required just to run unit tests.
"""

import os
import sys
from unittest.mock import MagicMock

# ── Environment defaults ──────────────────────────────────────────────────────
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PASSWORD", "")
os.environ.setdefault("REDIS_BASE_URL", "localhost")
os.environ.setdefault("REDIS_SECRETE_KEY", "")

# ── Stub missing optional packages ───────────────────────────────────────────
for _mod in (
    "claude_agent_sdk",
    "git",           # gitpython exposes the 'git' namespace
    "aiomysql",
    "fitz",          # pymupdf
    "docx",          # python-docx
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
