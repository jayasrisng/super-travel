"""A local fake Messages API that replays scripted assistant turns, for testing agent loops without a key."""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Iterator


def tool_use(name: str, input: dict[str, Any], id: str) -> dict[str, Any]:
    return {"content": [{"type": "tool_use", "id": id, "name": name, "input": input}], "stop_reason": "tool_use"}


def text(t: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": t}], "stop_reason": "end_turn"}


@contextmanager
def fake_messages_api(script: list[dict[str, Any]], monkeypatch) -> Iterator[list[dict[str, Any]]]:
    """Serve `script` turns in order. Yields the list of captured request bodies."""
    seen: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:
            pass

        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["content-length"])))
            seen.append({"path": self.path, "beta": self.headers.get("anthropic-beta"), "body": body})
            turn = script[min(len(seen), len(script)) - 1]
            out = json.dumps({
                "id": f"msg_{len(seen)}", "type": "message", "role": "assistant", "model": body["model"],
                "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}, **turn,
            }).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    from super_travel.core import llm

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    llm.client.cache_clear()
    try:
        yield seen
    finally:
        server.shutdown()
        llm.client.cache_clear()
