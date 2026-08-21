import sqlite3
from contextlib import contextmanager

from app.config import settings
from app.models import BoardOut, CardOut, ColumnOut

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash BLOB NOT NULL,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS boards (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS columns (
    id       TEXT PRIMARY KEY,
    board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    title    TEXT NOT NULL,
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id        TEXT PRIMARY KEY,
    board_id  INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
    column_id TEXT NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
    title     TEXT NOT NULL,
    details   TEXT NOT NULL DEFAULT '',
    position  INTEGER NOT NULL
);
"""

HARDCODED_USERNAME = "user"
HARDCODED_PASSWORD = "password"

FIXED_COLUMNS = [
    ("col-backlog", "Backlog"),
    ("col-discovery", "Discovery"),
    ("col-progress", "In Progress"),
    ("col-review", "Review"),
    ("col-done", "Done"),
]


def init_db() -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        _seed_hardcoded_user(conn)


def _seed_hardcoded_user(conn: sqlite3.Connection) -> None:
    from app.auth import hash_password

    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
        (HARDCODED_USERNAME, hash_password(HARDCODED_PASSWORD)),
    )


@contextmanager
def get_connection():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_or_create_board(user_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM boards WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is not None:
            return row["id"]

        board_id = conn.execute(
            "INSERT INTO boards (user_id) VALUES (?)", (user_id,)
        ).lastrowid
        conn.executemany(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            [
                (column_id, board_id, title, position)
                for position, (column_id, title) in enumerate(FIXED_COLUMNS)
            ],
        )
        return board_id


def load_board(board_id: int) -> BoardOut:
    with get_connection() as conn:
        column_rows = conn.execute(
            "SELECT id, title FROM columns WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()
        card_rows = conn.execute(
            "SELECT id, column_id, title, details FROM cards"
            " WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()

    card_ids_by_column: dict[str, list[str]] = {row["id"]: [] for row in column_rows}
    cards: dict[str, CardOut] = {}
    for row in card_rows:
        card_ids_by_column[row["column_id"]].append(row["id"])
        cards[row["id"]] = CardOut(
            id=row["id"], title=row["title"], details=row["details"]
        )

    columns = [
        ColumnOut(id=row["id"], title=row["title"], card_ids=card_ids_by_column[row["id"]])
        for row in column_rows
    ]
    return BoardOut(columns=columns, cards=cards)


def save_board(board_id: int, board: BoardOut) -> None:
    with get_connection() as conn:
        for column in board.columns:
            conn.execute(
                "UPDATE columns SET title = ? WHERE id = ? AND board_id = ?",
                (column.title, column.id, board_id),
            )

        conn.execute("DELETE FROM cards WHERE board_id = ?", (board_id,))
        for column in board.columns:
            for position, card_id in enumerate(column.card_ids):
                card = board.cards[card_id]
                conn.execute(
                    "INSERT INTO cards (id, board_id, column_id, title, details, position)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (card.id, board_id, column.id, card.title, card.details, position),
                )
