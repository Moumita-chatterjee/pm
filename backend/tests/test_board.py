from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login() -> str:
    response = client.post(
        "/api/login", json={"username": "user", "password": "password"}
    )
    return response.cookies["session"]


def test_get_board_requires_authentication():
    response = client.get("/api/board")
    assert response.status_code == 401


def test_put_board_requires_authentication():
    response = client.put("/api/board", json={"columns": [], "cards": {}})
    assert response.status_code == 401


def test_fresh_user_gets_five_empty_columns():
    token = _login()
    response = client.get("/api/board", cookies={"session": token})
    assert response.status_code == 200

    body = response.json()
    assert len(body["columns"]) == 5
    assert body["cards"] == {}
    assert all(column["cardIds"] == [] for column in body["columns"])


def test_put_then_get_round_trips_board():
    token = _login()
    board = client.get("/api/board", cookies={"session": token}).json()

    board["columns"][0]["cardIds"] = ["card-1"]
    board["cards"]["card-1"] = {
        "id": "card-1",
        "title": "Test card",
        "details": "Some details",
    }

    put_response = client.put("/api/board", json=board, cookies={"session": token})
    assert put_response.status_code == 200

    get_response = client.get("/api/board", cookies={"session": token})
    assert get_response.json() == put_response.json()
    assert get_response.json()["columns"][0]["cardIds"] == ["card-1"]


def test_put_rejects_unknown_column_id():
    token = _login()
    board = client.get("/api/board", cookies={"session": token}).json()
    board["columns"][0]["id"] = "col-not-real"

    response = client.put("/api/board", json=board, cookies={"session": token})
    assert response.status_code == 400


def test_put_rejects_dangling_card_reference():
    token = _login()
    board = client.get("/api/board", cookies={"session": token}).json()
    board["columns"][0]["cardIds"] = ["card-missing"]

    response = client.put("/api/board", json=board, cookies={"session": token})
    assert response.status_code == 400


def test_put_rejects_orphaned_card():
    token = _login()
    board = client.get("/api/board", cookies={"session": token}).json()
    board["cards"]["card-orphan"] = {
        "id": "card-orphan",
        "title": "Not referenced by any column",
        "details": "",
    }

    response = client.put("/api/board", json=board, cookies={"session": token})
    assert response.status_code == 400
