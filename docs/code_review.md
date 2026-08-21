# Code Review — pm repo (2026-08-18)

## Scope

Full-repository review, not a diff. `backend/` and `scripts/` contain only a
one-line placeholder `AGENTS.md` each and were confirmed empty of real code —
nothing to review there yet. All findings below are in `frontend/`, the only
part of the repo with implemented code (a standalone, client-only Kanban demo
per `CLAUDE.md`: no backend, no persistence, no auth yet).

Reviewed: `src/lib/kanban.ts` (board model + `moveCard`), all five components
under `src/components/`, `src/app/`, all three test files (Vitest unit,
Vitest/RTL component, Playwright e2e), and the project config
(`package.json`, `tsconfig.json`, `eslint.config.mjs`, `vitest.config.ts`,
`playwright.config.ts`, `.gitignore`).

**Overall assessment**: the code is small, deliberately simple, and its core
logic (`moveCard`) is correctly covered by unit tests for the paths it
exercises. No exploitable security issues or data-corruption bugs were found
— there is no backend, no `dangerouslySetInnerHTML`, no `eval`, and no
persistence layer for anything to corrupt. Findings below are dead code,
missed test coverage on unexercised branches, an accessibility gap, and a
committed build artifact.

## Findings (prioritized)

### 1. Generated Playwright artifact committed to git
**File**: `frontend/test-results/.last-run.json` (tracked); `frontend/.gitignore`
**Priority**: High (repo hygiene / will worsen over time)

`frontend/test-results/.last-run.json` is a Playwright-generated file and is
currently tracked in git. `frontend/.gitignore` has no entry for
`test-results/` or `playwright-report/`. Combined with
`trace: "retain-on-failure"` in `playwright.config.ts`, a failing e2e run
will start generating trace/screenshot files under `test-results/` that are
also untracked-but-visible or, worse, get accidentally `git add`ed since the
directory is already inside the repo's tracked history.

**Action**: add to `frontend/.gitignore`:
```
/test-results/
/playwright-report/
```
then `git rm --cached frontend/test-results/.last-run.json`.

### 2. Unreachable defensive fallback in `moveCard`
**File**: `frontend/src/lib/kanban.ts:149`
**Priority**: Medium (dead code, violates project's own coding standard)

```ts
const overIndex = overColumn.cardIds.indexOf(overId);
const insertIndex = overIndex === -1 ? nextOverCardIds.length : overIndex;
```

This branch only runs when `isOverColumn` is `false`, which means
`overColumnId` was derived via `findColumnId`'s "search columns for one whose
`cardIds` contains `overId`" path (`kanban.ts:81`) — i.e. `overColumn` was
*chosen because* it contains `overId`. `overIndex` can therefore never be
`-1` here; the `-1` branch is unreachable and untested (no test exercises
it). `CLAUDE.md`'s coding standards state: *"Keep it simple — never
over-engineer, no unnecessary defensive programming"*. This guard is exactly
that.

**Action**: simplify to `const insertIndex = overColumn.cardIds.indexOf(overId);`
and drop the ternary, or add a comment + test if the authors believe the
branch is reachable via some path not yet considered.

### 3. No-op `useMemo` in `KanbanBoard`
**File**: `frontend/src/components/KanbanBoard.tsx:28`
**Priority**: Low (simplification)

```ts
const cardsById = useMemo(() => board.cards, [board.cards]);
```

This memoizes an identity passthrough — it returns the exact same reference
it was given, on every dependency change. It provides no memoization benefit
and adds an unnecessary hook + import.

**Action**: replace with `const cardsById = board.cards;`.

### 4. `KanbanCard` and `KanbanCardPreview` duplicate markup and have already drifted
**File**: `frontend/src/components/KanbanCard.tsx:33-41`, `frontend/src/components/KanbanCardPreview.tsx:9-18`
**Priority**: Medium (reuse / maintainability)

Both components render the identical title+details block
(`<h4 className="font-display text-base font-semibold ...">{title}</h4>` +
`<p className="mt-2 text-sm leading-6 ...">{details}</p>`), copy-pasted. The
surrounding shadow styling has already diverged:
`KanbanCard` uses `shadow-[0_12px_24px_rgba(3,33,71,0.08)]` at rest, while
`KanbanCardPreview` (the drag overlay) hardcodes
`shadow-[0_18px_32px_rgba(3,33,71,0.16)]` — coincidentally the same value
`KanbanCard` uses only in its `isDragging` state. A future content/style
change to one is easy to forget applying to the other.

**Action**: extract the shared read-only body into one presentational
component (e.g. `CardContent`) used by both `KanbanCard` and
`KanbanCardPreview`.

### 5. No memoization — every keystroke/mutation re-renders the whole board
**File**: `frontend/src/components/KanbanBoard.tsx` (state shape), `KanbanColumn.tsx`, `KanbanCard.tsx`
**Priority**: Low (efficiency; currently harmless at n=8 cards, doesn't scale)

`board` is one flat object recreated on every mutation (`handleRenameColumn`,
`handleAddCard`, `handleDeleteCard`, `handleDragEnd` all call `setBoard` with
a new top-level object). No component in the tree is wrapped in
`React.memo`, so typing a single character into a column's rename `<input>`
(`KanbanColumn.tsx:44`, fires `onRename` on every `onChange`) triggers a full
re-render of all 5 columns and all cards on the board, not just the column
being renamed.

**Action**: wrap `KanbanColumn` and `KanbanCard` in `React.memo`, and/or
switch column-title editing to local component state committed on blur
instead of propagating to board state on every keystroke.

### 6. No keyboard sensor — drag-and-drop is pointer-only
**File**: `frontend/src/components/KanbanBoard.tsx:22-26`
**Priority**: Medium (accessibility / functional gap against stated requirement)

```ts
const sensors = useSensors(
  useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
);
```

Only `PointerSensor` is registered. `@dnd-kit/core` sensors are independent —
without a `KeyboardSensor` also registered in `useSensors`, keyboard-only
users cannot pick up or move a card at all (there's no other UI for
reordering/moving cards between columns). `AGENTS.md`'s business requirement
states cards "can be moved with drag and drop" with no keyboard alternative
provided.

**Action**: add `useSensor(KeyboardSensor, { coordinateGetter:
sortableKeyboardCoordinates })` from `@dnd-kit/sortable` to the sensors list.

### 7. Duplicate `aria-label` across all column rename inputs
**File**: `frontend/src/components/KanbanColumn.tsx:46`
**Priority**: Low (accessibility)

Every column's rename `<input>` has the identical
`aria-label="Column title"`. With 5 columns on the board, a screen-reader
user gets 5 indistinguishable controls all announced as "Column title" and
cannot tell which one they're focused on without also reading surrounding
context.

**Action**: `aria-label={`Rename ${column.title} column`}` (or similar,
derived from the column being rendered).

### 8. Missed test coverage on `moveCard`'s guard/no-op branches
**File**: `frontend/src/lib/kanban.test.ts`
**Priority**: Low (test coverage)

The existing 3 tests only cover the reorder-within-column, move-to-column,
and drop-at-end happy paths. Not covered:
- unknown `activeId`/`overId` (the `if (!activeColumnId || !overColumnId) return columns;` guard at `kanban.ts:92`),
- a no-op same-column drop where `oldIndex === newIndex` (`kanban.ts:121`),
- dropping onto an empty column.

These are exactly the branches most likely to silently regress, since
they're also not exercised by the component test or the Playwright e2e
suite.

**Action**: add unit tests for the three cases above.

### 9. Redundant `test` / `test:unit` npm scripts
**File**: `frontend/package.json:10-11`
**Priority**: Low (cleanup)

```json
"test": "vitest run",
"test:unit": "vitest run",
```

Byte-identical scripts. Keep one (docs/commands elsewhere in the repo
reference `test:unit`, so drop `test`).

## Summary table

| # | Priority | File | Category |
|---|----------|------|----------|
| 1 | High | frontend/test-results/.last-run.json, .gitignore | Repo hygiene |
| 2 | Medium | src/lib/kanban.ts:149 | Dead code / convention |
| 3 | Low | src/components/KanbanBoard.tsx:28 | Simplification |
| 4 | Medium | KanbanCard.tsx / KanbanCardPreview.tsx | Reuse / duplication |
| 5 | Low | KanbanBoard.tsx, KanbanColumn.tsx, KanbanCard.tsx | Efficiency |
| 6 | Medium | KanbanBoard.tsx:22-26 | Accessibility |
| 7 | Low | KanbanColumn.tsx:46 | Accessibility |
| 8 | Low | src/lib/kanban.test.ts | Test coverage |
| 9 | Low | package.json:10-11 | Cleanup |

No findings were made for `backend/` or `scripts/` — both are empty
placeholders per `CLAUDE.md`'s own description of current repo state.
