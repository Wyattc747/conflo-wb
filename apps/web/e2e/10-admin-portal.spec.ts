import { test, expect } from "@playwright/test";

test.describe("Admin Portal", () => {
  test("admin login page renders", async ({ page }) => {
    await page.goto("/admin/login");
    await page.waitForLoadState("domcontentloaded");
    // Should show login form
    const emailInput = page.locator("input[type='email']");
    await expect(emailInput).toBeVisible();
  });

  test("admin login form has required fields", async ({ page }) => {
    await page.goto("/admin/login");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("input[type='email']")).toBeVisible();
    await expect(page.locator("input[type='password']")).toBeVisible();
    await expect(page.locator("button[type='submit']")).toBeVisible();
  });

  test("admin login shows error for invalid credentials", async ({ page }) => {
    await page.goto("/admin/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("bad@example.com");
    await page.locator("input[type='password']").fill("wrongpass");
    await page.locator("button[type='submit']").click();
    // Should show an error (connection error if API not running, or invalid credentials)
    await page.waitForTimeout(1000);
    const errorEl = page.locator("[class*='red'], [class*='error']");
    // Error should appear (either API error or validation)
    await expect(errorEl.first()).toBeVisible();
  });

  test("admin dashboard redirects when not logged in", async ({ page }) => {
    await page.goto("/admin");
    await page.waitForLoadState("domcontentloaded");
    // Should redirect to login
    await page.waitForTimeout(500);
    expect(page.url()).toContain("login");
  });
});
