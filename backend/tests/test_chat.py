import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login() -> str:
    response = client.post(
        "/api/login", json={"username": "user", "password": "password"}
    )
    return response.cookies["session"]


def test_chat_requires_authentication():
    response = client.post("/api/chat", json={"message": "hi"})
    assert response.status_code == 401


def test_chat_applies_and_persists_a_create_card_operation(monkeypatch):
    token = _login()

    canned = json.dumps(
        {
            "reply": "Added it!",
            "operations": [
                {
                    "op": "create_card",
                    "column_id": "col-backlog",
                    "title": "From AI",
                    "details": "Created via chat",
                }
            ],
        }
    )
    monkeypatch.setattr("app.routers.chat.call_openrouter", lambda *a, **k: canned)

    response = client.post(
        "/api/chat", json={"message": "add a card"}, cookies={"session": token}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Added it!"
    assert "From AI" in [card["title"] for card in body["board"]["cards"].values()]

    get_response = client.get("/api/board", cookies={"session": token})
    titles = [card["title"] for card in get_response.json()["cards"].values()]
    assert "From AI" in titles


def test_chat_with_no_operations_leaves_board_unchanged(monkeypatch):
    token = _login()
    before = client.get("/api/board", cookies={"session": token}).json()

    canned = json.dumps({"reply": "No changes needed.", "operations": []})
    monkeypatch.setattr("app.routers.chat.call_openrouter", lambda *a, **k: canned)

    response = client.post(
        "/api/chat", json={"message": "hello"}, cookies={"session": token}
    )

    assert response.status_code == 200
    assert response.json()["board"] == before


def test_chat_with_invalid_operation_keeps_board_but_still_returns_reply(monkeypatch):
    token = _login()
    before = client.get("/api/board", cookies={"session": token}).json()

    canned = json.dumps(
        {
            "reply": "Done (this operation is actually invalid).",
            "operations": [
                {
                    "op": "move_card",
                    "card_id": "card-does-not-exist",
                    "column_id": "col-backlog",
                }
            ],
        }
    )
    monkeypatch.setattr("app.routers.chat.call_openrouter", lambda *a, **k: canned)

    response = client.post(
        "/api/chat", json={"message": "move it"}, cookies={"session": token}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Done (this operation is actually invalid)."
    assert body["board"] == before
