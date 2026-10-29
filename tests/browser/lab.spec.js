import { test, expect } from "@playwright/test";
test("manual thresholds, core switching, capture export and reset", async ({
  page,
}, info) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Where does the alert happen?" }),
  ).toBeVisible();
  await page
    .getByLabel("Signal source", { exact: true })
    .selectOption("manual");
  await page.locator("#manual").fill("4095");
  await page.getByRole("button", { name: "Single sample" }).click();
  await expect(page.locator("#alert")).toHaveText("HIGH ALERT");
  await page.locator("#manual").fill("0");
  await page.getByRole("button", { name: "Single sample" }).click();
  await expect(page.locator("#alert")).toHaveText("LOW ALERT");
  await page.locator("#manual").fill("800");
  await page.getByRole("button", { name: "Single sample" }).click();
  await expect(page.locator("#alert")).toHaveText("SAFE");
  await page.getByLabel("Processor core").selectOption("m4");
  await expect(page.getByLabel("Clock (MHz)")).toHaveValue("168");
  await expect(page.locator("#timing")).toContainText("71.4 ns");
  await expect(page.locator("#sample-count")).toHaveText("3 samples");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export CSV" }).click();
  expect((await download).suggestedFilename()).toBe("signal-bench-capture.csv");
  await page.getByRole("button", { name: "Run simulation" }).click();
  await expect(
    page.getByRole("button", { name: "Pause simulation" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Pause simulation" }).click();
  page.once("dialog", (d) => d.accept());
  await page.getByRole("button", { name: "Reset simulation" }).click();
  await expect(page.locator("#sample-count")).toHaveText("0 samples");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `test-results/signal-bench-${info.project.name}.png`,
    fullPage: true,
  });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(page.viewportSize().width);
  expect(errors).toEqual([]);
});
test("invalid settings fail safely and local preview serves only public assets", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await page.locator("#file").setInputFiles({
    name: "bad.json",
    mimeType: "application/json",
    buffer: Buffer.from('{"version":1,"config":{"core":"__proto__"}}'),
  });
  await expect(page.getByRole("alert")).toContainText("supported Cortex");
  expect(
    (await request.get("/remnant-project/remnant/data/remnant.db")).status(),
  ).toBe(404);
  expect((await request.get("/.git/config")).status()).toBe(404);
  expect((await request.get("/simulator/../../package.json")).status()).toBe(
    404,
  );
});
