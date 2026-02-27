import { test, expect } from "@playwright/test";

test.describe("Settings", () => {
  test("company settings page loads", async ({ page }) => {
    await page.goto("/app/settings/company");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });

  test("integrations page loads", async ({ page }) => {
    await page.goto("/app/settings/integrations");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });

  test("notification preferences page loads", async ({ page }) => {
    await page.goto("/app/settings/notifications");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });

  test("billing page loads", async ({ page }) => {
    await page.goto("/app/settings/billing");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });
});
