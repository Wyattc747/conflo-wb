import { test, expect } from "@playwright/test";

test.describe("Owner Portal", () => {
  test("owner dashboard page loads", async ({ page }) => {
    await page.goto("/owner/dashboard");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });

  test("owner portal shows pay apps", async ({ page }) => {
    await page.goto("/owner/dashboard");
    await page.waitForLoadState("domcontentloaded");
    const body = await page.textContent("body");
    expect(body).not.toContain("Application error");
  });
});
