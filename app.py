"""Flask API and tightly scoped static frontend for UPI Sentinel."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory

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
    # In local development, Flask serves the frontend. Vercel can serve /index.html
    # from its CDN, but the public directory is also explicitly bundled in the
    # function (vercel.json) so this route works on both platforms.
    if (PUBLIC / "index.html").is_file():
        return send_from_directory(PUBLIC, "index.html")
    if os.getenv("VERCEL"):
        return redirect("/index.html", code=307)
    return jsonify(error="Frontend index.html missing; check public/ directory."), 500


@app.get("/<asset>")
def static_asset(asset: str):
    if asset not in {"index.html", "script.js", "style.css", "config.js", "favicon.svg"}:
        return jsonify(error="Not found."), 404
    return send_from_directory(PUBLIC, asset)


@app.get("/api/ping")
def ping():
    """Cheap deployment probe even if the ML native libraries cannot be imported."""
    return jsonify(status="ok", service="upi-sentinel-api", runtime="flask",
                   release="2026-11-20-route-model-fix",
                   model_artifact_present=(ROOT / "model_artifacts" / "ensemble.joblib").is_file(),
                   frontend_present=(PUBLIC / "index.html").is_file()), 200


@app.get("/api/health")
def health():
    """Only load the already-built model in production; no HTTP-time training."""
    try:
        from model import get_model
        get_model()
    except Exception as exc:
        app.logger.exception("ML model load failed (health)")
        return jsonify(status="not_ready", model_type="three_model_ensemble",
                       training_data="synthetic_only", reason="model_load_failed",
                       error_type=type(exc).__name__,
                       message="Model load failed. See Vercel runtime logs."), 503
    return jsonify(status="ready", model_type="three_model_ensemble",
                   training_data="synthetic_only", message=""), 200


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
        from model import parse_transaction, predict_transaction, get_model
        # Validate before loading the pre-trained models.
        parse_transaction(data.get("amount"), data.get("timestamp"))
        result = predict_transaction(data["amount"], data["timestamp"], get_model())
        return jsonify(result)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:
        app.logger.exception("Inference failure")
        return jsonify(error="ML inference unavailable; see Vercel runtime logs.",
                       reason="model_load_failed", error_type=type(exc).__name__), 503


if __name__ == "__main__":
    from model import get_model
    get_model()  # Local development initializes the writable cache.
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5001")), debug=False)
