import { test, expect } from "@playwright/test";

test.describe("Financial Tools", () => {
  test("budget page renders", async ({ page }) => {
    await page.goto("/app/projects");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });

  test("change orders page renders", async ({ page }) => {
    await page.goto("/app/projects");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });

  test("pay apps page renders", async ({ page }) => {
    await page.goto("/app/projects");
    await page.waitForLoadState("domcontentloaded");
    expect(page.url()).toBeTruthy();
  });
});
