from app.db import get_connection, init_db


def test_init_db_idempotent():
    init_db()
    init_db()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    assert count == 1


def test_hardcoded_user_seeded_once():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT username FROM users WHERE username = 'user'"
        ).fetchone()
    assert row is not None
