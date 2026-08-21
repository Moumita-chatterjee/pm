import pytest
from fastapi.testclient import TestClient

from app.config import STATIC_DIR
from app.main import app

client = TestClient(app)


def test_hello():
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}


def test_root_serves_static_page():
    if not (STATIC_DIR / "index.html").exists():
        pytest.skip("frontend has not been built into app/static yet")

    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
