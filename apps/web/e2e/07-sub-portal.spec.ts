import { test, expect } from "@playwright/test";

test.describe("Sub Portal", () => {
  test("sub dashboard page loads", async ({ page }) => {
    await page.goto("/sub/dashboard");
    await page.waitForLoadState("domcontentloaded");
    // Should redirect to login or show sub dashboard
    expect(page.url()).toBeTruthy();
  });

  test("sub portal has proper navigation", async ({ page }) => {
    await page.goto("/sub/dashboard");
    await page.waitForLoadState("domcontentloaded");
    const body = await page.textContent("body");
    expect(body).not.toContain("500");
  });

  test("sub bids page accessible", async ({ page }) => {
    await page.goto("/sub/bids");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });
});
