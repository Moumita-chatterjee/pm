# Frontend

Next.js 16 (App Router) + React 19 + TypeScript, Tailwind v4. Currently a
standalone, client-only Kanban demo — no backend calls, no persistence, no
auth. See root `AGENTS.md` and `docs/PLAN.md` for the full product plan; this
file only describes the code that exists today.

## Data model (`src/lib/kanban.ts`)

Cards are stored normalized by id; columns hold ordered arrays of card ids:

```ts
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };
type BoardData = { columns: Column[]; cards: Record<string, Card> };
```

- `initialData` — the in-memory seed data (5 fixed columns, 8 cards).
- `moveCard(columns, activeId, overId): Column[]` — pure function handling
  all drag-and-drop reordering/re-columning. Deliberately takes/returns just
  `columns` (not the whole board) so it's unit-testable without cards or
  components. Handles: reorder within a column, drop onto another card,
  drop onto an empty column body.
- `createId(prefix)` — client-side id generator (`prefix-<random><time>`,
  base36).

## Components (`src/components/`)

- `KanbanBoard.tsx` — `"use client"` top-level component. Owns `board` via
  `useState(initialData)` and all mutation handlers
  (`handleRenameColumn`, `handleAddCard`, `handleDeleteCard`,
  `handleDragEnd`). Wires up `@dnd-kit/core`: `DndContext`, `PointerSensor`
  (6px activation distance), `closestCorners` collision detection,
  `DragOverlay` showing a `KanbanCardPreview` while dragging.
- `KanbanColumn.tsx` — one column; `useDroppable`, wraps its cards in a
  `SortableContext` (`@dnd-kit/sortable`), renders the rename `<input>` and
  `NewCardForm`.
- `KanbanCard.tsx` — one card; `useSortable`, delete button.
- `KanbanCardPreview.tsx` — the read-only card body shown in the drag
  overlay (currently duplicates markup from `KanbanCard.tsx` — see
  `docs/code_review.md` finding #4).
- `NewCardForm.tsx` — inline add-card form, local `isOpen`/`formState`.

Data flow is one-directional: `KanbanBoard` owns state, passes data +
callbacks down; no other component touches `board` directly.

## Routing

`src/app/page.tsx` renders `<KanbanBoard />` unconditionally — no routes,
no auth gate yet (Part 4 of `docs/PLAN.md` adds one). `src/app/layout.tsx` is
a plain root layout loading two Google fonts (`Space_Grotesk` as
`--font-display`, `Manrope` as `--font-body`).

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
  `npm run test:unit:watch`.
- Playwright e2e in `tests/kanban.spec.ts`, against a real dev server
  (`playwright.config.ts` auto-starts `next dev` on `127.0.0.1:3000`,
  `reuseExistingServer: true`). Run: `npm run test:e2e`.
- `npm run test:all` runs both.

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
