import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    from app import config, db

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config.settings, "database_path", db_path)
    db.init_db()
    yield
