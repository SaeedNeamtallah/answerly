import { expect, test } from "@playwright/test";

import { seedAuthSession } from "./helpers/auth";

test.describe("company dashboard backend bindings", () => {
  test("renders dashboard blocks from authenticated backend API responses", async ({ page }) => {
    await seedAuthSession(page, {
      token: "company-token",
      username: "company-admin",
      role: "company_admin",
      companyName: "Acme Support",
    });

    const authorizationByEndpoint = new Map<string, string | undefined>();

    await page.route("**/projects/", async (route) => {
      authorizationByEndpoint.set("projects", route.request().headers().authorization);
      await route.fulfill({
        json: {
          items: [
            {
              id: 101,
              name: "Acme Knowledge",
              description: "Public support answers",
              created_at: "2026-06-13T10:00:00Z",
            },
          ],
        },
      });
    });

    await page.route("**/bot-integrations/", async (route) => {
      authorizationByEndpoint.set("bots", route.request().headers().authorization);
      await route.fulfill({
        json: [
          {
            id: 201,
            owner_id: 1,
            project_id: 101,
            name: "Support Bot",
            telegram_bot_id: "support-bot-id",
            telegram_username: "@support_bot",
            status: "ready",
            last_error: null,
          },
          {
            id: 202,
            owner_id: 1,
            project_id: 101,
            name: "Escalation Bot",
            telegram_bot_id: "escalation-bot-id",
            telegram_username: "@escalation_bot",
            status: "degraded",
            last_error: "Webhook not reachable",
          },
        ],
      });
    });

    await page.route("**/conversations/", async (route) => {
      authorizationByEndpoint.set("conversations", route.request().headers().authorization);
      await route.fulfill({
        json: [
          {
            id: 301,
            owner_id: 1,
            bot_integration_id: 201,
            bot_name: "Support Bot",
            telegram_customer_id: 401,
            customer_label: "Ada Customer",
            project_id: 101,
            status: "open",
            needs_human: true,
            last_message_at: "2026-06-13T12:00:00Z",
          },
          {
            id: 302,
            owner_id: 1,
            bot_integration_id: 201,
            bot_name: "Support Bot",
            telegram_customer_id: 402,
            customer_label: "Resolved Customer",
            project_id: 101,
            status: "resolved",
            needs_human: false,
            last_message_at: "2026-06-13T11:00:00Z",
          },
        ],
      });
    });

    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByText("Overview of your bots, conversations, and knowledge assets.")).toBeVisible();
    await expect(page.getByText("Setup checklist")).toBeVisible();
    await expect(page.getByText("4 / 4 complete")).toBeVisible();
    await expect(page.getByText("Bot health")).toBeVisible();
    await expect(page.getByText("Support Bot")).toBeVisible();
    await expect(page.getByText("@support_bot")).toBeVisible();
    await expect(page.getByText("Knowledge base readiness")).toBeVisible();
    await expect(page.getByText("Acme Knowledge")).toBeVisible();
    await expect(page.getByText("Recent conversations")).toBeVisible();
    await expect(page.getByRole("link", { name: "Ada Customer" })).toBeVisible();

    expect(authorizationByEndpoint.get("projects")).toBe("Bearer company-token");
    expect(authorizationByEndpoint.get("bots")).toBe("Bearer company-token");
    expect(authorizationByEndpoint.get("conversations")).toBe("Bearer company-token");
  });
});
