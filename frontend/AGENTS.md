# Frontend

Next.js 16 (App Router) + React 19 + TypeScript, Tailwind v4. Wired to the
real FastAPI backend for auth and board persistence (Parts 4/7 of
`docs/PLAN.md`) — no client-only in-memory mode anymore. See root `AGENTS.md`
and `docs/PLAN.md` for the full product plan; this file only describes the
code that exists today.

## Backend access (`src/lib/api.ts`, `src/lib/api-base.ts`)

`api.ts` is the only module that calls the backend: `me()`, `login(username,
password)`, `logout()`, `getBoard()`, `putBoard(board)` — all
`credentials: "include"`. `api-base.ts` resolves the base URL: `""`
(relative/same-origin) in production, `http://localhost:8000` under
`next dev` (the backend's CORS allows `localhost:3000`/`127.0.0.1:3000` for
exactly this).

## Data model (`src/lib/kanban.ts`)

Cards are stored normalized by id; columns hold ordered arrays of card ids —
this is exactly the shape `GET`/`PUT /api/board` speak:

```ts
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };
type BoardData = { columns: Column[]; cards: Record<string, Card> };
```

- `initialData` — demo seed data (5 fixed columns, 8 cards). No longer used
  by the running app (board state always comes from the backend); still used
  as the fixture for the mocked-backend e2e suite (`tests/kanban.spec.ts`).
- `moveCard(columns, activeId, overId): Column[]` — pure function handling
  all drag-and-drop reordering/re-columning. Deliberately takes/returns just
  `columns` (not the whole board) so it's unit-testable without cards or
  components. Handles: reorder within a column, drop onto another card,
  drop onto an empty column body.
- `createId(prefix)` — client-side id generator (`prefix-<random><time>`,
  base36), used for new cards before the server round-trip.

## Components (`src/components/`)

- `KanbanBoard.tsx` — `"use client"` top-level component. `board` starts
  `null` and loads via `getBoard()` on mount (renders nothing until it
  resolves). All mutation handlers (`handleRenameColumn`, `handleAddCard`,
  `handleDeleteCard`, `handleDragEnd`) compute the next `BoardData` locally,
  apply it to state immediately (optimistic), then call `putBoard(next)` and
  reconcile state with the server's response. The optimistic update is
  required for drag specifically: dnd-kit resets its drag transform the
  instant a drop completes, so without an immediate state update the card
  visibly snaps back to its old column for the `PUT` round-trip duration.
  Wires up `@dnd-kit/core`: `DndContext`, `PointerSensor` (6px activation
  distance), `closestCorners` collision detection, `DragOverlay` showing a
  `KanbanCardPreview` while dragging.
- `KanbanColumn.tsx` — one column; `useDroppable`, wraps its cards in a
  `SortableContext` (`@dnd-kit/sortable`). The rename `<input>` holds its
  own local state (synced from `column.title` via `useEffect`) and only
  calls `onRename` on blur — not on every keystroke, since each rename is
  now a real `PUT /api/board`.
- `KanbanCard.tsx` — one card; `useSortable`, delete button.
- `KanbanCardPreview.tsx` — the read-only card body shown in the drag
  overlay (currently duplicates markup from `KanbanCard.tsx` — see
  `docs/code_review.md` finding #4).
- `NewCardForm.tsx` — inline add-card form, local `isOpen`/`formState`.

Data flow is one-directional: `KanbanBoard` owns state, passes data +
callbacks down; no other component touches `board` directly.

## Routing

`src/app/page.tsx` resolves `me()` on mount and renders `LoginForm` or
`KanbanBoard` accordingly — a runtime client check, since static export has
no middleware for a build-time route gate. `src/app/layout.tsx` is a plain
root layout loading two Google fonts (`Space_Grotesk` as `--font-display`,
`Manrope` as `--font-body`).

## Styling

Brand palette as CSS custom properties in `src/app/globals.css`
(`--accent-yellow`, `--primary-blue`, `--secondary-purple`, `--navy-dark`,
`--gray-text`, plus `--surface`/`--surface-strong`/`--stroke`/`--shadow`).
Components reference these via `var(--...)` in Tailwind arbitrary-value
classes rather than Tailwind's own color palette — match this convention for
any new UI.

## Path alias

`@/*` → `src/*`, configured in both `tsconfig.json` and `vitest.config.ts`.

## Tests

- Vitest + jsdom + Testing Library, colocated `*.test.ts(x)` files, global
  setup in `src/test/setup.ts`. Run: `npm run test:unit` /
  `npm run test:unit:watch`. Component tests that render `KanbanBoard` or
  `LoginForm` stub `global.fetch` (`vi.stubGlobal`) — there is no real
  backend in this environment.
- Playwright e2e in `tests/kanban.spec.ts`, against a real dev server
  (`playwright.config.ts` auto-starts `next dev` on `127.0.0.1:3000`,
  `reuseExistingServer: true`). No backend runs alongside `next dev`, so
  `/api/me` and `/api/board` are stubbed via `page.route` (the board fixture
  is `initialData`, reset per test). Run: `npm run test:e2e`.
- Playwright e2e in `tests/docker/`, against the real containerized stack
  (`playwright.docker.config.ts`, baseURL `127.0.0.1:8000`) — no mocking.
  Requires `scripts/start.ps1`/`start.sh` to already be running. Run:
  `npx playwright test --config=playwright.docker.config.ts`.
- `npm run test:all` runs unit + the mocked-backend e2e suite (not the
  docker suite, which needs the container running separately).

## Commands

```bash
npm install
npm run dev       # next dev
npm run build      # next build
npm run lint       # eslint
npm run test:unit
npm run test:e2e
npm run test:all
```
