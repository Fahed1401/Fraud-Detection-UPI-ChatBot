import pytest

flask = pytest.importorskip("flask")
import app as webapp


@pytest.fixture()
def client(monkeypatch):
    webapp.app.config["TESTING"] = True
    monkeypatch.setattr(webapp, "model_ready", lambda: True)
    with webapp.app.test_client() as client:
        yield client


def test_frontend_static_routes(client):
    assert client.get("/").status_code == 200
    assert b"UPI Sentinel" in client.get("/").data
    assert client.get("/script.js").status_code == 200
    assert client.get("/style.css").status_code == 200
    assert client.get("/model.py").status_code == 404
    assert client.get("/transactions.csv").status_code == 404


def test_health(client):
    payload = client.get("/api/health").get_json()
    assert payload["status"] == "ready"
    assert payload["training_data"] == "synthetic_only"


def test_malformed_json_and_wrong_content_type(client):
    bad = client.post("/api/check_fraud", data="{", content_type="application/json")
    assert bad.status_code == 400
    wrong = client.post("/api/check_fraud", data="hello", content_type="text/plain")
    assert wrong.status_code == 415
    missing = client.post("/api/check_fraud", json={"amount": 300})
    assert missing.status_code == 400


def test_api_vote_result(client, monkeypatch):
    monkeypatch.setattr(webapp, "get_model", lambda: {"test": True})
    monkeypatch.setattr(webapp, "predict_transaction", lambda amount, timestamp, bundle: {
        "fraud_detected": False, "fraud_votes": 0,
        "isolation_forest": "Normal", "svm": "Normal", "xgboost": "Normal"
    })
    response = client.post("/api/check_fraud", json={"amount": 2500, "timestamp": "2026-11-18 14:25"})
    assert response.status_code == 200
    assert response.get_json()["fraud_votes"] == 0


def test_security_headers(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "object-src 'none'" in response.headers["Content-Security-Policy"]


def test_cors_only_allows_configured_origin(client, monkeypatch):
    monkeypatch.setattr(webapp, "ALLOWED_ORIGINS", {"https://example.vercel.app"})
    ok = client.get("/api/health", headers={"Origin": "https://example.vercel.app"})
    assert ok.headers["Access-Control-Allow-Origin"] == "https://example.vercel.app"
    bad = client.get("/api/health", headers={"Origin": "https://untrusted.example"})
    assert "Access-Control-Allow-Origin" not in bad.headers
