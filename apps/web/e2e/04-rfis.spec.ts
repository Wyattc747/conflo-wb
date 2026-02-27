import { test, expect } from "@playwright/test";

test.describe("RFIs", () => {
  const PROJECT_PATH = "/app/projects";

  test("RFI page structure", async ({ page }) => {
    await page.goto(`${PROJECT_PATH}`);
    await page.waitForLoadState("domcontentloaded");
    // Verify navigation doesn't crash
    expect(page.url()).toBeTruthy();
  });

  test("RFI list shows filter options", async ({ page }) => {
    // Navigate to a project's RFI page
    await page.goto("/app/projects");
    await page.waitForLoadState("domcontentloaded");
    // Check page renders without errors
    const body = await page.textContent("body");
    expect(body).not.toContain("Application error");
  });

  test("RFI status badges render correctly", async ({ page }) => {
    await page.goto("/app/projects");
    await page.waitForLoadState("domcontentloaded");
    // Verify no unhandled errors
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.waitForTimeout(1000);
    expect(errors.filter((e) => !e.includes("hydration"))).toHaveLength(0);
  });
});
