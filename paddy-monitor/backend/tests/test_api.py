import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from quality import classify, build_alerts

client = TestClient(app)
H = {"X-API-Key": "change-me"}


def test_classify():
    assert classify(10) == "dry"
    assert classify(13) == "optimal"
    assert classify(16) == "excess"


def test_alerts():
    assert build_alerts(13, 30, 60) == []
    assert build_alerts(17, 30, 60)[0][0] == "critical"


def test_flow():
    client.post("/devices", json={"name": "t-dev", "location": "x"}, headers=H)
    r = client.post("/readings", json={"device": "t-dev", "moisture": 16.5, "temperature": 30, "humidity": 80}, headers=H)
    assert r.status_code == 201 and r.json()["status"] == "excess"
    assert any("Moisture" in a["message"] for a in client.get("/alerts").json())


def test_auth_and_validation():
    assert client.post("/readings", json={}).status_code == 401
    bad = client.post("/readings", json={"device": "t-dev", "moisture": 500, "temperature": 30, "humidity": 50}, headers=H)
    assert bad.status_code == 422
    unknown = client.post("/readings", json={"device": "nope", "moisture": 13, "temperature": 30, "humidity": 50}, headers=H)
    assert unknown.status_code == 404
