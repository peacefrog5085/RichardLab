#!/usr/bin/env python3

import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/")
def root():
    return jsonify({
        "service": "RichardLab Cloud",
        "status": "ONLINE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/health")
def health():
    return jsonify({
        "service": "RichardLab Cloud",
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.post("/lab/status")
def lab_status():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({
            "accepted": False,
            "error": "Expected a JSON object",
        }), 400

    return jsonify({
        "accepted": True,
        "service": "RichardLab Cloud",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "lab_status": payload,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
