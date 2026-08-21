# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Project Management MVP: a single-user (MVP) Kanban board app with an AI chat sidebar that can create/edit/move cards. See `AGENTS.md` for full business requirements and `docs/PLAN.md` for the phased build plan (Plan → Scaffolding → Frontend → Auth → DB modeling → Backend API → Frontend+Backend integration → AI connectivity → AI structured outputs → AI chat sidebar).

**Current state**: Parts 1-8 of `docs/PLAN.md` are done — `backend/` is a real FastAPI app (auth, SQLite-backed board persistence, OpenRouter connectivity via `app/ai/openrouter.py`), `frontend/` is wired to it (login, logout, and the Kanban board all round-trip through the backend, no more in-memory-only state), and `scripts/` has working Docker start/stop scripts. A real `OPENROUTER_API_KEY` is in the root `.env` (gitignored, not committed). AI structured outputs (Part 9) and the chat sidebar UI (Part 10) are not started. Check `docs/PLAN.md` for exact per-part status.

### Target architecture (per AGENTS.md, not all built yet)

- NextJS frontend, Python FastAPI backend (using `uv` as the package manager), everything packaged into one Docker container with the backend serving the static NextJS build at `/`.
- SQLite local database, created on first run if missing.
- AI calls via OpenRouter using `openai/gpt-oss-120b`, with `OPENROUTER_API_KEY` from a root `.env`.
- Hardcoded MVP login (`user` / `password`); DB schema supports multiple users for the future but MVP is single-user, single-board.
- Start/stop scripts for Mac/PC/Linux belong in `scripts/`.

## Commands

All frontend commands run from `frontend/`:

```bash
npm install
npm run dev          # start Next.js dev server
npm run build         # production build
npm run lint          # eslint
npm run test:unit      # vitest run (unit/component tests)
npm run test:unit:watch # vitest watch mode
npm run test:e2e       # playwright tests (auto-starts dev server on 127.0.0.1:3000)
npm run test:all       # unit then e2e
```

Run a single vitest test file: `npx vitest run src/lib/kanban.test.ts`
Run a single playwright test: `npx playwright test tests/kanban.spec.ts`

Backend commands run from `backend/` (uv-managed):

```bash
uv run pytest              # backend test suite (excludes integration tests)
uv run pytest -m integration  # OpenRouter smoke test — needs a real OPENROUTER_API_KEY in root .env
uv run ruff check .         # lint
```

Docker (from repo root): `scripts/start.ps1` / `scripts/start.sh` builds the image and runs the full stack on `http://localhost:8000`; `scripts/stop.ps1` / `scripts/stop.sh` stops and removes it. Board data persists in `./data/app.db` (volume-mounted).

## Architecture (frontend)

- `src/lib/kanban.ts` — the board data model and pure logic. `BoardData` is `{ columns: Column[], cards: Record<string, Card> }`, i.e. columns hold ordered arrays of card IDs and cards are stored in a normalized lookup map. `moveCard` contains all drag-and-drop reordering/re-columning logic and is deliberately pure (columns in, columns out) so it's unit-testable without mounting components. `initialData` is now only used as a fixture in the mocked-backend e2e suite (`tests/kanban.spec.ts`) — the running app always loads real board state from the backend.
- `src/lib/api.ts` — the only place that calls the backend (`me`, `login`, `logout`, `getBoard`, `putBoard`), all `credentials: "include"`. `src/lib/api-base.ts` resolves the base URL: empty string (relative, same-origin) in production/Docker, `http://localhost:8000` under `next dev` (the backend's CORS is scoped to `localhost:3000`/`127.0.0.1:3000` for exactly this).
- `src/components/KanbanBoard.tsx` — top-level client component (`"use client"`). Loads the board from `getBoard()` on mount (`board` is `null` until then, component renders nothing while loading). Every mutation handler (rename column, add/delete card, drag end) computes the next `BoardData` locally (reusing `moveCard`, etc.), applies it to state immediately (optimistic — required so a dropped drag doesn't visibly snap back to its old column while `PUT /api/board` is in flight, since dnd-kit resets its drag transform the instant the drop completes), then calls `putBoard(next)` and reconciles state with the server's response. Wires up `@dnd-kit/core` (`DndContext`, sensors, drag overlay).
- `src/components/KanbanColumn.tsx` — the column-title `<input>` holds its own local state and only calls `onRename` (→ a `PUT /api/board`) on blur, not on every keystroke, since board updates now mean a network round trip.
- `src/components/KanbanCard.tsx`, `KanbanCardPreview.tsx`, `NewCardForm.tsx` — presentational pieces. Columns are `useDroppable`; cards are part of a `SortableContext` per column (`@dnd-kit/sortable`).
- `src/components/LoginForm.tsx`, `src/app/page.tsx` — auth gate. `page.tsx` resolves `me()` on mount and renders `LoginForm` or `KanbanBoard` accordingly (a runtime client check, since static export has no middleware for a build-time route gate).
- Styling: Tailwind v4 (via `@tailwindcss/postcss`) plus CSS custom properties for the brand palette (see Color Scheme below) — colors are referenced as `var(--accent-yellow)` etc. rather than Tailwind color utilities.
- Path alias `@/*` maps to `src/*` (configured in both `tsconfig.json` and `vitest.config.ts`).

## Architecture (backend)

- `app/main.py` — FastAPI app; `init_db()` runs at import time; API routers registered before the catch-all `StaticFiles("/")` mount serving the built frontend.
- `app/db.py` — stdlib `sqlite3`, hand-written SQL, `CREATE TABLE IF NOT EXISTS` schema (no ORM/migrations — see `docs/database.md`). `get_or_create_board`/`load_board`/`save_board` implement full-replace board persistence.
- `app/models.py` — Pydantic `CardOut`/`ColumnOut`/`BoardOut` mirroring the frontend's `BoardData` shape exactly (`ColumnOut.card_ids` aliased to `cardIds` in JSON).
- `app/auth.py` + `app/routers/auth.py` — bcrypt password hash/verify, opaque session token in an HttpOnly cookie, `get_current_user` FastAPI dependency.
- `app/routers/board.py` — `GET`/`PUT /api/board`; `PUT` validates referential integrity (column ids match exactly, every `cardIds` entry has a matching `cards` entry and vice versa) before persisting.
- `app/ai/openrouter.py` — `call_openrouter(messages, response_format=None)`, a thin `httpx` wrapper around OpenRouter's chat completions endpoint, hardcoded to `openai/gpt-oss-120b` (per `AGENTS.md`). Not yet used by any router (Part 9/10 wire it into a chat endpoint).

## Testing setup

- Frontend unit/component tests: Vitest + jsdom + Testing Library, colocated as `*.test.ts(x)` under `src/`, global setup in `src/test/setup.ts`.
- Frontend e2e (`frontend/tests/`, `npm run test:e2e`): Playwright against a real dev server on `127.0.0.1:3000` (auto-started, reused if already running); backend calls are mocked via `page.route` since no real backend runs alongside `next dev`.
- Frontend e2e against the real stack (`frontend/tests/docker/`, `playwright.docker.config.ts`): assumes `scripts/start.ps1`/`start.sh` already started the container on `127.0.0.1:8000`; no mocking.
- Backend tests: `uv run pytest` from `backend/`, using FastAPI `TestClient` against an isolated tmp-path SQLite DB per test (`tests/conftest.py`). `tests/test_openrouter.py` is marked `@pytest.mark.integration` and excluded by default (`addopts` in `pyproject.toml`) — it makes a real network call and needs a real API key; skips cleanly if `OPENROUTER_API_KEY` is unset.

## Color scheme

- Accent Yellow `#ecad0a` — accent lines, highlights
- Blue Primary `#209dd7` — links, key sections
- Purple Secondary `#753991` — submit buttons, important actions
- Dark Navy `#032147` — main headings
- Gray Text `#888888` — supporting text, labels

## Coding standards (from AGENTS.md — apply repo-wide)

1. Use latest versions of libraries and idiomatic approaches as of today.
2. Keep it simple — never over-engineer, no unnecessary defensive programming, no extra features beyond what's asked.
3. Be concise; keep README content minimal; no emojis, ever.
4. When hitting issues, identify root cause before attempting a fix — prove it with evidence rather than guessing.

## Working documentation

All planning/execution docs for this project live in `docs/`. `docs/PLAN.md` is the authoritative phased plan — read it before starting work that spans backend, auth, database, or AI features, since those parts may not exist yet depending on where the project currently stands.
