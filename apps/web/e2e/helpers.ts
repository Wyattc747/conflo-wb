import { Page, expect } from "@playwright/test";

const API_BASE = "http://localhost:8000";

// Demo user credentials (matching seed data clerk_user_ids)
export const DEMO_USERS = {
  admin: { clerkId: "clerk_demo_admin", email: "admin@demo.conflo.app" },
  precon: { clerkId: "clerk_demo_precon", email: "precon@demo.conflo.app" },
  mgmt: { clerkId: "clerk_demo_mgmt", email: "mgmt@demo.conflo.app" },
  field: { clerkId: "clerk_demo_field", email: "field@demo.conflo.app" },
  sub: { clerkId: "clerk_demo_sub", email: "sub@demo.conflo.app" },
  owner: { clerkId: "clerk_demo_owner", email: "owner@demo.conflo.app" },
};

/**
 * In E2E tests, we bypass Clerk login by setting a mock JWT cookie/header.
 * This requires the backend auth middleware's fallback JWT decode to be active.
 */
export async function loginAs(page: Page, role: keyof typeof DEMO_USERS) {
  const user = DEMO_USERS[role];
  // Create a minimal JWT-like token that the backend fallback decoder accepts
  const header = btoa(JSON.stringify({ alg: "none", typ: "JWT" }));
  const payload = btoa(JSON.stringify({ sub: user.clerkId, email: user.email }));
  const token = `${header}.${payload}.test`;

  // Store in localStorage for the frontend to use
  await page.evaluate((t) => {
    localStorage.setItem("__clerk_db_jwt", t);
    localStorage.setItem("e2e_token", t);
  }, token);
}

export async function expectPageTitle(page: Page, title: string) {
  await expect(page.locator("h1, [data-testid='page-title']").first()).toContainText(title);
}

export async function waitForApi(page: Page) {
  await page.waitForLoadState("networkidle");
}

export function formatRoute(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}
