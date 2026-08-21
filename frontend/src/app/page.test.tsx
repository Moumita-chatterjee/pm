import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the login form when unauthenticated", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: false });
    render(<Home />);

    expect(await screen.findByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });

  it("renders the kanban board when authenticated", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ columns: [], cards: {} }),
    });
    render(<Home />);

    expect(await screen.findByRole("heading", { name: /kanban studio/i })).toBeInTheDocument();
  });
});
