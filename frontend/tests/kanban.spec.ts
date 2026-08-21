import { expect, test } from "@playwright/test";
import { initialData } from "@/lib/kanban";

// This suite exercises pure client-side board behavior against `next dev`
// with no backend running, so the API calls KanbanBoard makes are stubbed
// out here (auth check + board load/save, backed by an in-memory fixture
// that resets every test).
test.beforeEach(async ({ page }) => {
  await page.route("**/api/me", (route) =>
    route.fulfill({ status: 200, json: { username: "user" } })
  );

  let board = structuredClone(initialData);
  await page.route("**/api/board", (route) => {
    if (route.request().method() === "PUT") {
      board = route.request().postDataJSON();
    }
    return route.fulfill({ status: 200, json: board });
  });
});

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});
