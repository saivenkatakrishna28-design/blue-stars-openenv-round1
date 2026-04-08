from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3


def test_reset_endpoint():
    response = client.post("/reset?task_id=easy_refund_request")
    assert response.status_code == 200
    body = response.json()
    assert body["observation"]["task"]["task_id"] == "easy_refund_request"


def test_step_endpoint():
    client.post("/reset?task_id=easy_refund_request")

    response = client.post(
        "/step",
        json={
            "queue": "billing",
            "response_type": "reply",
            "priority": "medium",
            "tags": ["refund", "duplicate_charge"],
            "redact_pii": False,
            "note": "billing triage",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["reward"]["score"] <= 1.0
