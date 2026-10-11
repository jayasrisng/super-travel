"""Explicit local-demo sessions. Not production authentication."""

import hashlib
import hmac
import time
from uuid import UUID, uuid4

from super_travel.control.store import ControlError


def local_request(request):
    host = request.url.hostname
    origin = request.headers.get("origin", "")
    if (
        host not in ("127.0.0.1", "localhost", "testserver")
        or origin
        and origin
        not in (
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        )
    ):
        raise ControlError(
            403,
            "local_only",
            "Demo sessions are available only on local trusted origins",
        )


def issue(secret):
    payload = f"{uuid4()}.{int(time.time()) + 604800}"
    return (
        payload
        + "."
        + hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    )


def verify(request, secret):
    local_request(request)
    cookie = request.cookies.get("wonder_demo", "")
    try:
        identity, expiry, signature = cookie.split(".")
        payload = identity + "." + expiry
        expected = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected) or int(expiry) < int(
            time.time()
        ):
            raise ValueError("Invalid session")
        return UUID(identity)
    except (ValueError, TypeError) as exc:
        raise ControlError(
            401, "unauthorized", "Open a local demo notebook to continue"
        ) from exc
