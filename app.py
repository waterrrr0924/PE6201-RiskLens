"""Local HTTP UI and controlled serving. No uploads, arbitrary paths or tool execution.

Only loopback binding. Browser origin/Host checks protect the private API config.
No paragraph text is logged or saved unless the user exports results in the UI.
"""
import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from risklens import ROOT, analyze, config, split_paragraphs

LOCK = threading.Lock()
LAST_CALL = 0
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def allowed(self):
        hosts = {"127.0.0.1:%s" % PORT, "localhost:%s" % PORT}
        return self.headers.get("Host") in hosts and self.headers.get("Origin") in {None, *["http://" + h for h in hosts]}

    def do_GET(self):
        if not self.allowed():
            return self.send_json({"error": "Local origin required"}, 403)
        assets = {"/": (ROOT / "index.html", "text/html; charset=utf-8"),
                  "/record": (ROOT.parent / "recording.html", "text/html; charset=utf-8"),
                  "/video_script.json": (ROOT.parent / "video_script.json", "application/json")}
        for i in range(1,7):
            assets["/video/scene%d.png"%i] = (ROOT.parent / "video_assets" / ("scene%d.png"%i),"image/png")
        if self.path in assets:
            path,mime = assets[self.path]
            if not path.exists():
                return self.send_json({"error":"Recording assets are optional and not bundled in the code-only package"},404)
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            c = config()
            self.send_json({"llm_ready": bool(c.get("api_key")), "model": c["model"], "metrics": json.loads((ROOT / "evals/results/metrics.json").read_text()) if (ROOT / "evals/results/metrics.json").exists() else {}})
        elif self.path == "/api/samples":
            self.send_json(json.loads((ROOT / "data/demo.json").read_text(encoding="utf-8")))
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        global LAST_CALL
        if self.path != "/api/analyze" or not self.allowed():
            return self.send_json({"error": "Local origin and analyze route required"}, 403)
        if self.headers.get_content_type() != "application/json":
            return self.send_json({"error": "JSON required"}, 415)
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 100000:
                raise ValueError("Request too large or empty")
            request = json.loads(self.rfile.read(size))
            paragraphs = split_paragraphs(request.get("text", ""))
            engine = request.get("engine", "llm")
            if not LOCK.acquire(blocking=False):
                return self.send_json({"error": "Another request is running"}, 429)
            try:
                if time.monotonic()-LAST_CALL < 2:
                    return self.send_json({"error": "Please wait two seconds between requests"}, 429)
                LAST_CALL = time.monotonic()
                results = [{"input": p, **analyze(p, engine)} for p in paragraphs]
                self.send_json({"results": results})
            finally:
                LOCK.release()
        except (ValueError, RuntimeError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except Exception:
            self.send_json({"error": "Unexpected error; inspect local configuration"}, 500)


if __name__ == "__main__":
    print("RiskLens running at http://127.0.0.1:8765 - Ctrl+C to stop")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
