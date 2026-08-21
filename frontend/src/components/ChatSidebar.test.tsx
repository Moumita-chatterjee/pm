import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatSidebar } from "@/components/ChatSidebar";
import type { BoardData } from "@/lib/kanban";

const updatedBoard: BoardData = {
  columns: [{ id: "col-backlog", title: "Backlog", cardIds: ["card-new"] }],
  cards: {
    "card-new": { id: "card-new", title: "From AI", details: "Created via chat" },
  },
};

describe("ChatSidebar", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ reply: "Added it!", board: updatedBoard }),
        })
      )
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the message, renders both sides of the exchange, and calls onBoardUpdate", async () => {
    const onBoardUpdate = vi.fn();
    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);

    await userEvent.type(
      screen.getByLabelText("Chat message"),
      "add a card called From AI to Backlog"
    );
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(fetch).toHaveBeenCalledWith(
      "/api/chat",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          message: "add a card called From AI to Backlog",
          history: [],
        }),
      })
    );

    expect(
      await screen.findByText("add a card called From AI to Backlog")
    ).toBeInTheDocument();
    expect(await screen.findByText("Added it!")).toBeInTheDocument();
    expect(onBoardUpdate).toHaveBeenCalledWith(updatedBoard);
  });

  it("does not submit an empty message", async () => {
    const onBoardUpdate = vi.fn();
    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);

    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(fetch).not.toHaveBeenCalled();
    expect(onBoardUpdate).not.toHaveBeenCalled();
  });
});
