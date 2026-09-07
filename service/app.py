#!/usr/bin/env python3
"""POST /mesh microservice wrapping score-sum consensus (not Borda)."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agents import consensus_pick, consensus_pick_borda  # noqa: E402


def mesh(body: dict) -> dict:
    ranks = body.get("ranks") or []
    weights = body.get("agent_weights") or {}
    method = str(body.get("consensus") or "score_sum")
    fn = consensus_pick_borda if method == "borda" else consensus_pick
    result = fn(ranks, weights)
    result["service"] = "mncd"
    result["consensus"] = "borda" if method == "borda" else "score_sum"
    result["note"] = "Eval default is score-sum; Borda is opt-in via consensus=borda."
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path in {"/", "/health", "/mesh"}:
            self._send(200, {"ok": True, "service": "mncd", "consensus_default": "score_sum"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/mesh":
            self._send(404, {"error": "not found"})
            return
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        self._send(200, mesh(body))


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 43133
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"MNCD microservice http://127.0.0.1:{port}/mesh", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
