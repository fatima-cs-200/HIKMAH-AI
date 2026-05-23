"""
HIKMAH AI — Backend launcher.
Run from the hikmah-ai directory:  python start_backend.py
"""

import sys
import os
from pathlib import Path

# ── Load .env FIRST so all os.environ reads get the values ──────────────────
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)
# ─────────────────────────────────────────────────────────────────────────────

# ── SSL bypass (must happen before any network library imports) ──────────────
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")
os.environ.setdefault("HF_HUB_DISABLE_SSL_VERIFICATION", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import ssl
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass
# ─────────────────────────────────────────────────────────────────────────────

# Ensure the project root (hikmah-ai/) is on sys.path so all
# absolute imports like `from api.routes import ...` resolve correctly.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn
from utils.config import settings

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  {settings.app_name} v{settings.app_version} — Backend")
    print(f"  API docs : http://localhost:{settings.api_port}/docs")
    print(f"  Health   : http://localhost:{settings.api_port}/api/v1/health")
    print(f"{'='*60}\n")

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        reload_dirs=[str(ROOT)],
        log_level="info",
    )
