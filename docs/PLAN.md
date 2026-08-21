# Project Management MVP — build plan

Source requirements: root `AGENTS.md`. This document breaks the 10-part
outline into checklists with substeps, tests, and success criteria. Checked
items are done; see each part's "Status" line for where the project stands.

**Current pass scope**: Parts 1-9 done and verified. Part 10 (AI chat sidebar
UI) is not started.

## Cross-cutting technical decisions

| Area | Decision | Why |
|---|---|---|
| Frontend build | `output: "export"` in `next.config.ts` | App is 100% client components, one route — static export lets FastAPI serve plain files directly. |
| Auth | `sessions` table + opaque token in an HttpOnly cookie | Static export has no middleware; a session table is trivially revocable and reuses the same SQLite DB. |
| Board persistence | `GET /api/board` + `PUT /api/board`, full-replace on write | MVP scale (5 columns, &lt;20 cards) — full replace is simpler than diffing. |
| AI board edits | Closed set of typed ops (`create_card`, `edit_card`, `move_card`), validated before applying | Matches the requirement exactly; safer than trusting the AI to echo a whole board. |
| Chat history | Client-side only, sent with each request | No requirement to survive reload; avoids a new DB table. |
| DB layer | Stdlib `sqlite3`, hand-written SQL, no ORM/migrations | 5 tables, one schema version — an ORM would be ceremony. |
| Containers | Plain `docker build`/`docker run`, no compose | Requirement says "a Docker container" (singular). |

---

## Part 1: Plan

**Status**: done (this document).

- [x] Enrich this document with substeps, tests, and success criteria per part.
- [x] Create `frontend/AGENTS.md` describing the existing frontend code.
- [x] User checks and approves the plan (approved via plan-mode sign-off; see
      `docs/code_review.md` for the separate code-quality review already done).

## Part 2: Scaffolding

**Status**: done. `docker build` succeeds, `docker run` serves `/api/hello`
and `/`, backend pytest suite passes.

- [ ] `backend/pyproject.toml` (uv-managed): deps `fastapi`, `uvicorn[standard]`,
      `pydantic-settings`; dev deps `pytest`, `httpx`, `ruff`.
- [ ] `backend/app/main.py`: FastAPI app; API routers registered before a
      catch-all `StaticFiles("/")` mount (so `/api/*` never falls through to
      static serving).
- [ ] `backend/app/config.py`: `pydantic-settings` Settings reading env vars
      (`.env` at repo root).
- [ ] `backend/app/db.py`: SQLite connection helper + `init_db()` stub
      (creates DB file if missing; real schema lands in Part 5/6).
- [ ] `backend/app/static/`: gitignored; placeholder `index.html` that calls
      `fetch('/api/hello')` and renders the result — proves the "hello world"
      + "API call" requirement before the real frontend is wired in (Part 3).
- [ ] Route `GET /api/hello` → `{"message": "hello world"}`.
- [ ] Root `Dockerfile` (single-stage): `uv`-maintained Python base image,
      `uv sync --frozen --no-dev`, copy `app/`, `CMD uvicorn app.main:app
      --host 0.0.0.0 --port 8000`.
- [ ] `scripts/start.sh` / `scripts/stop.sh` (bash, Mac/Linux) and
      `scripts/start.ps1` / `scripts/stop.ps1` (PowerShell, Windows): build +
      run / stop + remove the container, `--env-file .env`, volume-mount
      `./data:/app/data` for the future SQLite file.

**Tests**:
- `backend/tests/test_health.py` — `GET /api/hello` and `GET /` return 200
  via FastAPI `TestClient`.

**Success criteria**: `uv run pytest` passes; `docker build` succeeds;
`docker run` + `curl localhost:8000/api/hello` returns the hello JSON;
browser at `http://localhost:8000/` shows the placeholder page fetching and
displaying that JSON.

## Part 3: Add in Frontend

**Status**: done. `http://localhost:8000/` serves the built Kanban UI from
the containerized backend.

- [ ] `next.config.ts`: add `output: "export"`.
- [ ] `npm run build` produces `frontend/out/` (static HTML/JS/CSS).
- [ ] Dockerfile becomes multi-stage: `node:22-slim` stage runs `npm ci &&
      npm run build`; final stage copies `frontend/out` into
      `backend/app/static/`.
- [ ] `backend/.gitignore` entry for `app/static/` (build artifact, never
      committed).

**Tests**:
- Existing `frontend/` Vitest unit/component tests and the original
  `tests/kanban.spec.ts` Playwright suite (against `next dev`) continue to
  pass unchanged — they test client-side behavior independent of serving.
- New backend test: `GET /` serves the real built `index.html` when
  `app/static/index.html` exists; skips cleanly (not a failure) when it's
  absent, so running backend tests without a frontend build doesn't error
  obscurely.

**Success criteria**: `docker build && docker run`, then
`http://localhost:8000/` renders the identical Kanban UI seen under
`npm run dev`.

## Part 4: Add in a fake user sign in experience

**Status**: done. Verified against the containerized app: login/logout/`/api/me`
cookie flow works via curl, and the docker-config Playwright suite
(`tests/docker/auth.spec.ts`, 2 tests) passes against the live container.

- [ ] `backend/app/auth.py`: bcrypt password hash/verify, `create_session`,
      `destroy_session`, `get_current_user` FastAPI dependency (reads the
      session cookie, 401 if missing/expired).
- [ ] `backend/app/routers/auth.py`: `POST /api/login`, `POST /api/logout`,
      `GET /api/me`.
- [ ] Hardcoded user (`user` / `password`, bcrypt-hashed) seeded idempotently
      in `db.py`'s init routine.
- [ ] `CORSMiddleware` enabled for `localhost:3000` / `127.0.0.1:3000` so
      `npm run dev` can hit the live backend on `:8000` during iteration.
- [ ] `frontend/src/components/LoginForm.tsx`: username/password inputs,
      POSTs to `/api/login`, shows inline error on 401.
- [ ] `frontend/src/app/page.tsx`: client component that resolves `/api/me`
      on mount and renders `LoginForm` vs `KanbanBoard` accordingly (a
      runtime client check, since static export has no middleware for a
      build-time route gate).
- [ ] Logout control that calls `POST /api/logout` and returns to the login
      form.
- [ ] `frontend/playwright.docker.config.ts`: baseURL `127.0.0.1:8000`, no
      auto-started `webServer` (assumes `scripts/start.sh` already ran) — for
      specs that need the real backend.

**Tests**:
- Backend `test_auth.py`: login success sets cookie; login failure → 401;
  `/api/me` unauthenticated → 401; `/api/me` with valid cookie → 200; logout
  invalidates the session (subsequent `/api/me` → 401).
- Frontend unit: `LoginForm.test.tsx` (renders, submits, shows error on
  mocked 401, calls `onSuccess` on mocked 200), `page.test.tsx` (mocked
  `/api/me` 200 → board, 401 → login form).
- E2E `tests/auth.spec.ts` (docker config): login → board visible → logout →
  login form reappears → reload while logged out stays on login form.

**Success criteria**: cannot see the Kanban board without logging in with
`user`/`password`; logging out returns to the login form; reloading while
logged out does not leak the board.

## Part 5: Database modeling

**Status**: done — approved by user.

- [x] Propose SQLite schema (`users`, `sessions`, `boards`, `columns`,
      `cards`) mapping onto the frontend's `BoardData` shape, supporting
      multiple users with 1 board each.
- [x] Save the schema as `docs/db_schema.json`.
- [x] Document the approach in `docs/database.md`.
- [x] Get user sign-off before any Part 6 code is written against it.

**Tests**: N/A (design/doc part).

**Success criteria**: user has reviewed and approved `docs/db_schema.json`
and `docs/database.md`.

## Part 6: Backend

**Status**: done and verified (backend pytest, ruff, and a rebuilt Docker
container smoke-tested via curl — including PUT validation and persistence
across a container restart — all pass).

- [ ] `backend/app/models.py`: Pydantic `CardOut`, `ColumnOut`, `BoardOut`
      mirroring the frontend types exactly.
- [ ] `backend/app/routers/board.py`: `GET /api/board` (creates the user's
      board on first access if missing), `PUT /api/board` (full-replace with
      referential-integrity validation: every `cardIds` entry has a matching
      `cards` entry and vice versa; unknown `column_id` → 400).
- [ ] `db.py`: `get_or_create_board(user_id)`, `load_board(board_id)`,
      `save_board(board_id, BoardOut)` (single transaction: update column
      titles, delete+reinsert cards with position = index in `cardIds`).

**Tests**:
- `test_db.py`: `init_db()` idempotent; hardcoded user seeded exactly once.
- `test_board.py`: fresh user gets the 5 fixed empty columns; `PUT` then
  `GET` round-trips a full board; invalid `column_id`/orphaned `cardIds` →
  400; unauthenticated → 401.

**Success criteria**: backend can read/write a user's board end-to-end via
HTTP, validated by tests; DB file is created automatically if missing.

## Part 7: Frontend + Backend

**Status**: done and verified (frontend lint/unit/e2e, backend pytest, and
the docker-config e2e suite — including a new board-persistence test — all
pass against a rebuilt container).

- [x] `frontend/src/lib/api.ts`: fetch wrapper (`getBoard`, `putBoard`,
      `login`, `logout`, `me`), all `credentials: "include"`.
- [x] `KanbanBoard.tsx`'s four handlers (`handleRenameColumn`,
      `handleAddCard`, `handleDeleteCard`, `handleDragEnd`) compute the next
      `BoardData` locally (reusing `moveCard`, etc.), apply it to state
      immediately (optimistic), then `putBoard(...)` and reconcile state with
      the server's response.
      **Revised from the original non-optimistic design**: applying state
      only after the `PUT` resolved caused a visible bug during drag —
      dnd-kit resets its drag transform as soon as the drop completes, so
      with `board` still unchanged the card visibly snapped back to its
      original column for the round-trip duration, then jumped to its real
      position once the response landed. Confirmed against the live app,
      not just inferred. Setting state immediately removes the flash; the
      later `.then(setBoard)` still makes the server response authoritative.

**Tests**:
- Frontend unit: mocked-fetch tests asserting each handler calls
  `PUT /api/board` with the expected payload and updates state from the
  mocked response.
- E2E `tests/board-persistence.spec.ts` (docker config): add a card, reload
  the page, card is still there.

**Success criteria**: the Kanban board is now genuinely persistent across
reloads and server restarts (SQLite file), not just in-memory.

## Part 8: AI connectivity

**Status**: done and verified — a real `OPENROUTER_API_KEY` was added to
root `.env` and the integration smoke test passes against the live
OpenRouter API with `openai/gpt-oss-120b`.

- [x] `backend/app/ai/openrouter.py`: `call_openrouter(messages,
      response_format=None)` via `httpx`, POSTing to OpenRouter's chat
      completions endpoint with model `openai/gpt-oss-120b`.
- [x] `config.py`: `openrouter_api_key` setting, read from root `.env`
      (already in place from Part 2 scaffolding).
- [x] Integration smoke test (network-gated, excluded from default test run
      via `addopts = "-m 'not integration'"` in `pyproject.toml`): asks
      "What is 2+2?", asserts "4" appears in the reply.

**Tests**: `pytest -m integration` (not part of default `pytest` run) —
requires a real key present.

**Success criteria**: a real OpenRouter call succeeds and returns a sane
answer to a trivial arithmetic question.

## Part 9: Structured Outputs + board context

**Status**: done and verified — backend pytest (28 passed) and ruff pass,
plus a live smoke test against the real OpenRouter API (create/move/edit via
chat, each persisted and confirmed with a follow-up `GET /api/board`).

- [x] `backend/app/ai/schema.py`: Pydantic `CreateCardOp` / `EditCardOp` /
      `MoveCardOp` (discriminated union) + `ChatAIResponse {reply,
      operations}`. Hand-written strict JSON schema for the outbound request
      (Pydantic's auto-generated schema doesn't satisfy strict-mode
      constraints out of the box); `ChatAIResponse.model_validate_json(...)`
      validates the actual response afterward regardless.
- [x] `backend/app/ai/apply.py`: `apply_operations(board, ops)` — validates
      every op against the current board first; all-or-nothing (if any op is
      invalid, none apply, but the chat reply is still returned).
- [x] `backend/app/routers/chat.py`: `POST /api/chat` — loads the current
      board server-side (not client-trusted), sends board JSON + history +
      message to OpenRouter with the strict schema, applies valid operations,
      persists via the Part 6 `save_board`, returns `{reply, board}`.
- [x] **Found and fixed during live verification**: `build_chat_response_format`
      (originally a static `CHAT_RESPONSE_FORMAT` constant) now takes the
      current board's column ids and card ids and puts them in the outbound
      JSON schema as an `enum` per operation field, built fresh per request.
      Live testing against real OpenRouter (`openai/gpt-oss-120b`) showed the
      model would sometimes emit a plausible but wrong id (e.g.
      `"backlog"` instead of `"col-backlog"`) with a free-form string schema;
      `apply_operations` correctly rejected it as a no-op, but the model's
      own `reply` text still claimed success, so the user saw a false
      "done!" with no actual board change. Column ids are a fixed set of 5
      (`FIXED_COLUMNS` in `db.py`) so they're always enumerable; card ids
      come from the board loaded for that request. `edit_card`/`move_card`
      branches are omitted from the schema entirely when the board has no
      cards yet (an empty enum would make them unsatisfiable). Confirmed
      fixed by re-running the same live prompt that reproduced the bug.

**Tests**:
- `test_apply_operations.py`: per-op-type unit tests (create/edit/move);
  invalid `card_id`/`column_id` → no-op, board unchanged.
- `test_chat.py`: mocked `call_openrouter` returning canned structured JSON;
  assert operations applied + persisted; separate test for `operations: []`.

**Success criteria**: chatting "add a card called X to Discovery" results in
a real new card in the persisted board, returned in the same response.
Verified live, not just via mocked tests.

## Part 10: AI chat sidebar UI

**Status**: not started.

- [ ] `frontend/src/components/ChatSidebar.tsx`: message list + input,
      POSTs `/api/chat` with `{message, history}`, appends the reply, calls
      `onBoardUpdate(board)` with the response's board (unconditional
      `setBoard` — no diffing needed since the backend always returns the
      current board).
- [ ] Lift `board`/`setBoard` from `KanbanBoard` up to `page.tsx` so both the
      board and the sidebar share state.
- [ ] Sidebar styled with the existing brand palette, mounted alongside the
      board (e.g. `grid-cols-[1fr_360px]`).

**Tests**:
- Frontend unit: `ChatSidebar.test.tsx` (mocked fetch; submit renders both
  messages, calls `onBoardUpdate`).
- E2E `tests/chat.spec.ts` (docker config): intercept `/api/chat`, return a
  fixed response with a new card; assert it appears in the board without a
  full page reload, and the transcript shows both messages.

**Success criteria**: chatting in the sidebar can create/edit/move cards on
the live board, and the board visibly updates without a manual refresh.
