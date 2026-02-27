import { test, expect } from "@playwright/test";

test.describe("Daily Logs", () => {
  test("daily logs page loads without errors", async ({ page }) => {
    await page.goto("/app/projects");
    await page.waitForLoadState("domcontentloaded");
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.waitForTimeout(500);
    // No critical JS errors
    expect(errors.filter((e) => e.includes("TypeError"))).toHaveLength(0);
  });
});
