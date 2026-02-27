import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("landing page loads", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Conflo/);
  });

  test("unauthenticated users are redirected to login", async ({ page }) => {
    await page.goto("/app/dashboard");
    // Should redirect to Clerk login or show login UI
    await expect(page.url()).toContain("/sign-in");
  });

  test("nav links are present", async ({ page }) => {
    await page.goto("/");
    // Check main CTA buttons exist
    const startButton = page.getByRole("link", { name: /get started|sign up/i });
    await expect(startButton).toBeVisible();
  });
});
