import { expect, test } from "@playwright/test";

test("chatting with the AI assistant creates a card on the board without a reload", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).toBeVisible();

  await page.route("**/api/chat", async (route) => {
    const boardResponse = await page.request.get("/api/board");
    const current = await boardResponse.json();
    const newCardId = "card-chat-e2e";
    current.cards[newCardId] = {
      id: newCardId,
      title: "From chat",
      details: "Added via the assistant.",
    };
    current.columns[0].cardIds.push(newCardId);

    await route.fulfill({
      status: 200,
      json: { reply: "Added it to Backlog!", board: current },
    });
  });

  await page.getByLabel("Chat message").fill("Add a card called From chat to Backlog");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Add a card called From chat to Backlog")).toBeVisible();
  await expect(page.getByText("Added it to Backlog!")).toBeVisible();
  await expect(page.getByTestId("column-col-backlog").getByText("From chat")).toBeVisible();
});
