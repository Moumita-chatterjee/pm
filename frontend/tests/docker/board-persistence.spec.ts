import { expect, test } from "@playwright/test";

test("a card added to the board survives a page reload", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).toBeVisible();

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Persisted card");
  await firstColumn.getByPlaceholder("Details").fill("Should survive a reload.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();

  await expect(firstColumn.getByText("Persisted card")).toBeVisible();

  await page.reload();

  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).toBeVisible();
  await expect(firstColumn.getByText("Persisted card")).toBeVisible();
});
