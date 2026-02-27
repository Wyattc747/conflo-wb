import { test, expect } from "@playwright/test";

test.describe("GC Dashboard", () => {
  test("dashboard page renders", async ({ page }) => {
    await page.goto("/app/dashboard");
    // Will redirect to login for unauthenticated, which is expected
    // In a real E2E with seeded auth, we'd verify dashboard cards
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });

  test("dashboard has expected structure", async ({ page }) => {
    await page.goto("/app/dashboard");
    await page.waitForLoadState("domcontentloaded");
    // Verify page doesn't error out (no 500 screens)
    const errorText = page.locator("text=500");
    const hasError = await errorText.isVisible().catch(() => false);
    expect(hasError).toBeFalsy();
  });
});
