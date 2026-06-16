import { expect, test } from "@playwright/test";

import { seedAuthSession } from "./helpers/auth";

function dashboardsForRange(range: string) {
  return [
    {
      uid: "ragmind-overview",
      title: "RAGMind Overview",
      category: "application",
      description: "Backend, query pipeline, Celery, Qdrant, and incident health.",
      url: `http://127.0.0.1:3000/d/ragmind-overview?from=now-${range}&to=now`,
      embed_url: null,
    },
    {
      uid: "postgres-exporter-12485",
      title: "PostgreSQL Exporter",
      category: "database",
      description: "Database connections, locks, buffers, and storage.",
      url: `http://127.0.0.1:3000/d/postgres-exporter-12485?from=now-${range}&to=now`,
      embed_url: null,
    },
  ];
}

function summaryForRange(range: string) {
  return {
    range,
    generated_at: "2026-06-13T12:00:00Z",
    grafana: {
      status: "ready",
      public_url: "http://127.0.0.1:3000",
      embedding_enabled: false,
      version: "12.0.0",
      database: "ok",
    },
    prometheus: {
      status: "ready",
      base_url_configured: true,
    },
    targets: [
      {
        job: "ragmind-backend",
        label: "Backend API",
        health: "ready",
        last_scrape: "2026-06-13T11:59:50Z",
      },
      {
        job: "postgres",
        label: "Postgres Exporter",
        health: "ready",
        last_scrape: "2026-06-13T11:59:51Z",
      },
    ],
    metrics: [
      {
        key: "backend_request_rate",
        label: "Backend RPS",
        unit: "requests_per_second",
        value: 2.5,
        status: "ready",
        description: "Current FastAPI request rate over 5 minutes.",
      },
      {
        key: "backend_p95_latency",
        label: "Backend P95",
        unit: "seconds",
        value: 0.23,
        status: "ready",
        description: "95th percentile backend latency over 5 minutes.",
      },
      {
        key: "backend_5xx_rate",
        label: "5xx Rate",
        unit: "requests_per_second",
        value: 0,
        status: "ready",
        description: "Server error rate over 5 minutes.",
      },
      {
        key: "query_failures",
        label: "Query Failures",
        unit: "count",
        value: 1,
        status: "ready",
        description: "Query pipeline failures in the last hour.",
      },
    ],
  };
}

test.describe("admin observability backend bindings", () => {
  test("renders platform observability from authorized backend responses", async ({ page }) => {
    await seedAuthSession(page, {
      token: "platform-token",
      username: "platform-owner",
      role: "platform_owner",
      companyName: "RAGMind Ops",
    });

    const dashboardRanges: string[] = [];
    const summaryRanges: string[] = [];
    const authorizationHeaders: string[] = [];

    await page.route("**/admin/observability/dashboards**", async (route) => {
      const url = new URL(route.request().url());
      const range = url.searchParams.get("range") || "1h";
      dashboardRanges.push(range);
      authorizationHeaders.push(route.request().headers().authorization || "");
      await route.fulfill({ json: dashboardsForRange(range) });
    });

    await page.route("**/admin/observability/summary**", async (route) => {
      const url = new URL(route.request().url());
      const range = url.searchParams.get("range") || "1h";
      summaryRanges.push(range);
      authorizationHeaders.push(route.request().headers().authorization || "");
      await route.fulfill({ json: summaryForRange(range) });
    });

    await page.goto("/admin/observability");

    await expect(page.getByRole("heading", { name: "Observability" })).toBeVisible();
    await expect(page.getByText("Platform-owner Grafana and Prometheus dashboards")).toBeVisible();
    await expect(page.getByText("Backend RPS")).toBeVisible();
    await expect(page.getByText("2.50/s")).toBeVisible();
    await expect(page.getByText("Grafana embedding is disabled")).toBeVisible();
    await expect(page.getByText("Backend API")).toBeVisible();
    await expect(page.getByRole("link", { name: /Open Grafana/i })).toHaveAttribute("href", /now-1h/);

    await page.getByRole("tab", { name: /Database/i }).click();
    await expect(page.getByText("PostgreSQL Exporter").first()).toBeVisible();

    await page.getByRole("button", { name: "24h" }).click();
    await expect.poll(() => dashboardRanges).toContain("24h");
    await expect.poll(() => summaryRanges).toContain("24h");
    await expect(page.getByRole("link", { name: /Open Grafana/i })).toHaveAttribute("href", /now-24h/);

    expect(authorizationHeaders).toEqual(
      expect.arrayContaining(["Bearer platform-token", "Bearer platform-token"]),
    );
  });

  test("blocks company users before observability backend requests run", async ({ page }) => {
    await seedAuthSession(page, {
      token: "company-token",
      username: "company-admin",
      role: "company_admin",
      companyName: "Acme Support",
    });

    let observabilityCalls = 0;
    await page.route("**/admin/observability/**", async (route) => {
      observabilityCalls += 1;
      await route.fulfill({ status: 403, json: { detail: "Forbidden" } });
    });

    await page.goto("/admin/observability");

    await expect(page).toHaveURL(/\/forbidden/);
    expect(observabilityCalls).toBe(0);
  });
});
