# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Project Management MVP: a single-user (MVP) Kanban board app with an AI chat sidebar that can create/edit/move cards. See `AGENTS.md` for full business requirements and `docs/PLAN.md` for the phased build plan (Plan → Scaffolding → Frontend → Auth → DB modeling → Backend API → Frontend+Backend integration → AI connectivity → AI structured outputs → AI chat sidebar).

**Current state**: only `frontend/` has real code (a standalone frontend-only Kanban demo, not yet wired to a backend). `backend/` and `scripts/` are empty placeholders — nothing has been scaffolded there yet. Check `docs/PLAN.md` for which part is currently in progress before assuming backend/auth/AI/DB pieces exist.

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

There is no backend yet, so there are no backend commands to document until Part 2 of `docs/PLAN.md` is implemented.

## Architecture (frontend)

- `src/lib/kanban.ts` — the board data model and pure logic. `BoardData` is `{ columns: Column[], cards: Record<string, Card> }`, i.e. columns hold ordered arrays of card IDs and cards are stored in a normalized lookup map. `moveCard` contains all drag-and-drop reordering/re-columning logic and is deliberately pure (columns in, columns out) so it's unit-testable without mounting components. `initialData` is the in-memory demo seed data — there is no persistence layer yet.
- `src/components/KanbanBoard.tsx` — top-level client component (`"use client"`) holding board state via `useState`, wiring up `@dnd-kit/core` (`DndContext`, sensors, drag overlay) and delegating actual reorder logic to `moveCard`. All mutation handlers (rename column, add/delete card) live here and flow down as props.
- `src/components/KanbanColumn.tsx`, `KanbanCard.tsx`, `KanbanCardPreview.tsx`, `NewCardForm.tsx` — presentational pieces. Columns are `useDroppable`; cards are part of a `SortableContext` per column (`@dnd-kit/sortable`).
- Styling: Tailwind v4 (via `@tailwindcss/postcss`) plus CSS custom properties for the brand palette (see Color Scheme below) — colors are referenced as `var(--accent-yellow)` etc. rather than Tailwind color utilities.
- Path alias `@/*` maps to `src/*` (configured in both `tsconfig.json` and `vitest.config.ts`).

Because there is no backend yet, all board state is client-side only and resets on reload — do not assume persistence when reasoning about behavior until Part 6/7 of the plan lands.

## Testing setup

- Unit/component tests: Vitest + jsdom + Testing Library, colocated as `*.test.ts(x)` under `src/`, global setup in `src/test/setup.ts`.
- E2E tests: Playwright, in `frontend/tests/`, against a real dev server on `127.0.0.1:3000` (playwright starts it automatically and reuses an existing server if already running).

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
