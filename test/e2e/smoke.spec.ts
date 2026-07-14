import { test, expect } from "@playwright/test";

const base = process.env.BASE_URL || "http://localhost:8000";

test.describe("FinAlly smoke", () => {
  test("health endpoint", async ({ request }) => {
    const res = await request.get(`${base}/api/health`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
  });

  test("watchlist seeded", async ({ request }) => {
    const res = await request.get(`${base}/api/watchlist`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.length).toBeGreaterThanOrEqual(10);
  });

  test("trade and portfolio", async ({ request }) => {
    const buy = await request.post(`${base}/api/portfolio/trade`, {
      data: { ticker: "AAPL", quantity: 1, side: "buy" },
    });
    expect(buy.ok()).toBeTruthy();
    const port = await (await request.get(`${base}/api/portfolio`)).json();
    expect(port.cash_balance).toBeLessThan(10000);
  });
});
