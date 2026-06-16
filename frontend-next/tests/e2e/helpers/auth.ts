import type { Page } from "@playwright/test";

const STORAGE_KEY = "ragmind-next-auth";

export async function seedAuthSession(
  page: Page,
  options: {
    token?: string;
    username?: string;
    role?: "company_admin" | "platform_owner";
    companyName?: string;
  } = {},
) {
  const session = {
    accessToken: options.token || "e2e-token",
    currentUser: {
      id: 1,
      username: options.username || "e2e-user",
      role: options.role || "company_admin",
      company_name: options.companyName || "E2E Company",
    },
  };

  await page.addInitScript(
    ({ key, value }) => {
      window.localStorage.setItem(key, JSON.stringify(value));
    },
    { key: STORAGE_KEY, value: session },
  );
}
