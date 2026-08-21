import { expect, test } from "@playwright/test";

test("dragging a card updates the board immediately, not after the network round-trip", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).toBeVisible();

  const sourceColumn = page.locator('[data-testid^="column-"]').nth(0);
  const targetColumn = page.locator('[data-testid^="column-"]').nth(1);

  await sourceColumn.getByRole("button", { name: /add a card/i }).click();
  await sourceColumn.getByPlaceholder("Card title").fill("Drag test card");
  await sourceColumn.getByRole("button", { name: /add card/i }).click();
  const card = sourceColumn.getByText("Drag test card");
  await expect(card).toBeVisible();

  // Artificially slow down the PUT that persists the move. If the UI only
  // updated once this resolved (the pre-fix behavior), the card would stay
  // in the source column — visibly snapping back after the drop — for the
  // full delay. Everything else (GET, login) is untouched.
  await page.route("**/api/board", async (route) => {
    if (route.request().method() === "PUT") {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    await route.continue();
  });

  const cardBox = await card.boundingBox();
  const targetBox = await targetColumn.boundingBox();
  if (!cardBox || !targetBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    targetBox.x + targetBox.width / 2,
    targetBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();

  // The PUT above is deliberately delayed 1s; this only passes within
  // 200ms if the move was applied optimistically, before that delay
  // elapsed.
  await expect(targetColumn.getByText("Drag test card")).toBeVisible({
    timeout: 200,
  });
});
