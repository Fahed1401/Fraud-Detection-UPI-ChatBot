"""Flask API and tightly scoped static frontend for UPI Sentinel."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from model import get_model, model_ready, predict_transaction

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4096
ALLOWED_ORIGINS = {origin.strip().rstrip("/") for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()}


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
    origin = request.headers.get("Origin", "").rstrip("/")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Vary"] = "Origin"
    return response


@app.errorhandler(413)
def oversized_request(_error):
    return jsonify(error="Request payload is too large."), 413


@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/<asset>")
def static_asset(asset: str):
    if asset not in {"script.js", "style.css", "config.js", "favicon.svg"}:
        return jsonify(error="Not found."), 404
    return send_from_directory(PUBLIC, asset)


@app.get("/api/health")
def health():
    return jsonify(status="ready" if model_ready() else "not_ready",
                   model_type="three_model_ensemble", training_data="synthetic_only",
                   message="Run python train.py to initialize the inference artifact." if not model_ready() else ""), (200 if model_ready() else 503)


@app.route("/api/check_fraud", methods=["POST", "OPTIONS"])
def check_fraud():
    if request.method == "OPTIONS":
        return ("", 204)
    if not request.is_json:
        return jsonify(error="Send a JSON request with Content-Type: application/json."), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="JSON body must be an object."), 400
    try:
        # Reject invalid input before loading potentially expensive models.
        from model import parse_transaction
        parse_transaction(data.get("amount"), data.get("timestamp"))
        result = predict_transaction(data["amount"], data["timestamp"], get_model())
        return jsonify(result)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except Exception:
        app.logger.exception("Inference error")
        return jsonify(error="The inference engine could not complete this request."), 503


if __name__ == "__main__":
    get_model()  # Ensure the dev server health endpoint is ready before browser load.
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5001")), debug=False)
