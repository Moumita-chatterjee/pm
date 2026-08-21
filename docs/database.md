# Database design — Part 5

Proposed schema for `boards`, `columns`, `cards`, extending the `users` /
`sessions` tables already implemented in Part 4. Full column-level detail is
in `docs/db_schema.json`; this document explains the reasoning. Needs sign-off
before Part 6 (`backend/app/routers/board.py`, `db.py` read/write functions)
is implemented against it.

## Mapping to the frontend model

`frontend/src/lib/kanban.ts` defines:

```ts
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };
type BoardData = { columns: Column[]; cards: Record<string, Card> };
```

The DB mirrors this directly:

- `boards` — one row per user (`user_id UNIQUE`), enforcing the MVP's
  "1 board per signed-in user" rule at the DB level, not just in application
  code.
- `columns` — one row per column. `id` reuses the frontend's fixed ids
  (`col-backlog`, `col-discovery`, `col-progress`, `col-review`, `col-done`)
  instead of an autoincrement int, so no id-translation layer is needed
  between the DB and `ColumnOut`/`BoardOut` Pydantic models. `position`
  fixes display order (SQLite doesn't guarantee row order without `ORDER BY`).
- `cards` — one row per card, keyed by the frontend's generated id
  (`createId("card")`, e.g. `card-<random><timestamp>`), for the same reason.
  `column_id` replaces the frontend's `Column.cardIds` array membership;
  `position` replaces that array's ordering.

Reconstructing `BoardData` from rows: group `cards` by `column_id`, order by
`position` within each group to rebuild each column's `cardIds`.

## Why fixed-id text primary keys, not autoincrement ints

The frontend already generates ids client-side (`createId`) and the AI
operations planned for Part 9 (`create_card`, `edit_card`, `move_card`) will
reference cards by these same ids. Reusing them as the DB primary key avoids
a mapping table or a round-trip to learn a server-assigned id before the
frontend/AI can refer to a just-created card. Collision risk is negligible at
MVP scale (single board, single user) and not defended against, per the
project's "no unnecessary defensive programming" standard.

## Why columns are seeded, not user-managed

The business requirement is "fixed columns that can be renamed" — no
add/remove/reorder column operation exists in the frontend or is planned for
the AI ops. So `columns` rows are inserted once, when a board is first
created (`get_or_create_board`), and only ever `UPDATE`d for `title`. `PUT
/api/board` (Part 6) will validate that the incoming payload's column ids
are exactly the 5 existing ones — a mismatch is a 400, not a schema change.

## Why `board_id` is denormalized onto `cards`

`column_id` alone is enough to join back to a board, but every read in this
app is "give me this user's whole board" — denormalizing `board_id` onto
`cards` turns that into one indexed lookup instead of a join, at the cost of
one extra column. Given the scale (single board, single user, MVP), this is
a minor simplification rather than a real optimization, but it keeps
`load_board(board_id)` in `db.py` to two flat queries (`columns` and `cards`
each filtered by `board_id`) instead of a join.

## Write strategy: full replace

Per the cross-cutting decision already recorded in `docs/PLAN.md` (full
replace on write, no diffing), `PUT /api/board` will, in one transaction:

1. `UPDATE columns SET title = ? WHERE id = ?` for each of the 5 columns.
2. `DELETE FROM cards WHERE board_id = ?`, then re-`INSERT` every card from
   the payload with `position` set to its index in the column's `cardIds`.

This is simple and correct at MVP scale (fewer than 20 cards); it is not
designed to survive concurrent writers, which doesn't exist in a
single-user MVP.

## Migrations

None. Per the existing cross-cutting decision (stdlib `sqlite3`, no ORM), all
four application tables are created with `CREATE TABLE IF NOT EXISTS` in
`db.py`'s `init_db()`, same pattern as the existing `users`/`sessions`
tables. There is one schema version; adding a real migration tool is out of
scope for an MVP with no deployed data to migrate.

## Open decision for sign-off

Everything above. In particular, please confirm or object to:

1. Text (frontend-generated) ids as primary keys for `columns`/`cards`,
   rather than autoincrement ints with a separate `client_id` column.
2. Columns seeded once and only rename-able (no add/remove/reorder), matching
   "fixed columns" in `AGENTS.md`.
3. Full delete+reinsert of `cards` on every `PUT /api/board`, rather than a
   diff-based update.
