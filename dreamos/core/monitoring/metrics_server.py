"""Simple Flask server exposing log metrics as JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify

app = Flask(__name__)
METRICS_FILE = Path("logs/metrics.json")


def _load_metrics() -> Dict[str, Any]:
    if METRICS_FILE.exists():
        try:
            with METRICS_FILE.open() as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


@app.route("/metrics")
def metrics() -> Any:
    """Return collected log metrics."""
    return jsonify(_load_metrics())


def start(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the metrics server."""
    app.run(host=host, port=port)


if __name__ == "__main__":
    start()
