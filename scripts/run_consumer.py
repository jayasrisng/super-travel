"""Loopback-only consumer fixture server; never print or put a shared token in JS."""

import os
import secrets
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    local = root / ".wonder.local.env"
    if not local.exists():
        descriptor = os.open(local, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(secrets.token_urlsafe(48))
    os.environ["WONDER_API_TOKEN"] = local.read_text().strip()
    os.environ["WONDER_DEMO_AUTH"] = "true"
    os.environ["APP_ENV"] = "local"
    os.environ.setdefault("WONDER_AGENT_MODE", "fixture")
    os.environ.setdefault("WONDER_DB_PATH", str(root / "wonder-consumer.sqlite3"))
    uvicorn.run(
        "super_travel.control.app:app",
        host="127.0.0.1",
        port=int(os.environ.get("WONDER_API_PORT", "8000")),
        access_log=False,
    )
