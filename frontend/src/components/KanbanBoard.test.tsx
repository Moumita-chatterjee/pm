import { useState } from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";

const freshBoard: BoardData = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: [] },
    { id: "col-discovery", title: "Discovery", cardIds: [] },
    { id: "col-progress", title: "In Progress", cardIds: [] },
    { id: "col-review", title: "Review", cardIds: [] },
    { id: "col-done", title: "Done", cardIds: [] },
  ],
  cards: {},
};

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

// KanbanBoard is a controlled component (board/setBoard lifted to page.tsx
// in Part 10 so the chat sidebar can share state); this harness stands in
// for that lifted state so the existing render/interaction assertions still
// see the board update after each PUT round-trip.
const KanbanBoardHarness = () => {
  const [board, setBoard] = useState<BoardData>(freshBoard);
  return <KanbanBoard board={board} setBoard={setBoard} />;
};

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) => {
        if (init?.method === "PUT") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(JSON.parse(init.body as string)),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(freshBoard),
        });
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the five columns from the given board", async () => {
    render(<KanbanBoardHarness />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("persists a column rename on blur via PUT /api/board", async () => {
    render(<KanbanBoardHarness />);
    await screen.findAllByTestId(/column-/i);

    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");

    await userEvent.tab();

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/board",
        expect.objectContaining({ method: "PUT" })
      );
    });
  });

  it("adds and removes a card, persisting each change via PUT", async () => {
    render(<KanbanBoardHarness />);
    await screen.findAllByTestId(/column-/i);

    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(within(column).queryByText("New card")).not.toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalledWith(
      "/api/board",
      expect.objectContaining({ method: "PUT" })
    );
  });
});
