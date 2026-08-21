import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Cookie, HTTPException

from app.db import get_connection

SESSION_COOKIE = "session"
SESSION_TTL = timedelta(days=7)


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed)


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + SESSION_TTL
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at.isoformat()),
        )
    return token


def destroy_session(token: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def get_current_user(session: str | None = Cookie(default=None)) -> dict:
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT users.id, users.username, sessions.expires_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (session,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at < datetime.now(UTC):
        destroy_session(session)
        raise HTTPException(status_code=401, detail="Session expired")

    return {"id": row["id"], "username": row["username"]}
