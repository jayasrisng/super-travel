import { test, expect } from "@playwright/test";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
const evidence = (name: string) =>
  path.resolve("../../docs/screenshots/" + name + ".png");

test("Tokyo consumer journey, swipe controls, persistence, briefing, and Magic", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Where shall we go?" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "+ New trip", exact: true }).click();
  await page.getByLabel("A name for these pages").fill("Tokyo with family");
  await page.getByRole("button", { name: "Next page →" }).click();
  await page.getByLabel("Relevant child ages").fill("8");
  await page.getByLabel("Dietary preferences").fill("Vegetarian");
  await page
    .getByLabel("Accessibility or special requirements")
    .fill("Easy walks");
  await page.getByRole("button", { name: "Next page →" }).click();
  await page.getByLabel("Approximate budget").fill("120000");
  await page.getByRole("button", { name: "Create my notebook →" }).click();
  await expect(
    page.getByRole("heading", { name: "Tokyo with family", exact: true }),
  ).toBeVisible();
  const tripURL = page.url();
  const firstTask = page.locator(".task-title").first();
  await firstTask.click();
  await page
    .getByLabel("Task title", { exact: true })
    .fill("Find a vegetarian birthday dinner");
  await page
    .getByLabel("What Wonder should do")
    .fill("Research three vegetarian options with easy access. Do not book.");
  await page.getByRole("button", { name: "Save changes", exact: true }).click();
  await page.getByRole("button", { name: "Ask Wonder →" }).click();
  await expect(
    page.getByRole("button", { name: "Accept draft" }),
  ).toBeVisible();
  await expect(page.locator(".agent-result")).toContainText("Sample proposal");
  await page.getByRole("button", { name: "Accept draft" }).click();
  await page.screenshot({ path: evidence("trip-light"), fullPage: true });
  await page.getByRole("button", { name: "Wardrobe & outfits" }).click();
  await expect(page.locator(".garment")).toHaveCount(34);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: evidence("wardrobe-light"), fullPage: true });
  await page.getByRole("button", { name: "Find my outfits" }).click();
  await page
    .getByRole("button", { name: "Generate outfits", exact: true })
    .click();
  await expect(
    page.getByRole("group", { name: "Outfit swipe card" }),
  ).toBeVisible();
  await page.screenshot({ path: evidence("outfits-light"), fullPage: true });
  await page.getByRole("button", { name: "Like outfit", exact: true }).click();
  await page
    .getByRole("button", { name: "Dislike outfit", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Undo last swipe", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Back a page");
  await expect(
    page.getByRole("button", { name: "Like outfit", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("group", { name: "Outfit swipe card" })
    .press("ArrowRight");
  await expect(page.locator(".liked-counter")).toContainText("2");
  const card = page.getByRole("group", { name: "Outfit swipe card" });
  const box = await card.boundingBox();
  if (!box) throw new Error("Missing swipe card");
  await page.mouse.move(box.x + box.width / 2, box.y + 80);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 150, box.y + 80, { steps: 8 });
  await page.mouse.up();
  await expect(page.locator(".liked-counter")).toContainText("3");
  await page.getByRole("button", { name: "Review & pack liked looks" }).click();
  await page.getByRole("button", { name: "Build from liked outfits" }).click();
  await expect(page.getByRole("checkbox").first()).toBeVisible();
  const checks = page.getByRole("checkbox");
  const count = await checks.count();
  expect(count).toBeGreaterThan(0);
  expect(count).toBeLessThanOrEqual(12);
  for (let i = 0; i < count; i++) {
    await checks.nth(i).click();
    await expect(checks.nth(i)).toHaveAttribute("aria-checked", "true");
  }
  await page.reload();
  await expect(page.getByRole("checkbox").first()).toHaveAttribute(
    "aria-checked",
    "true",
  );
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: evidence("packing-light"), fullPage: true });
  const tripId = new URL(tripURL).searchParams.get("trip");
  await page.goto("/briefing?trip=" + tripId);
  await expect(
    page.getByRole("heading", { name: /Good morning|morning|day/i }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: /Use sample calendar/ }).click();
  await expect(page.locator(".briefing-note")).toContainText("museum");
  await page.screenshot({ path: evidence("briefing-light"), fullPage: true });
  await page.goto("/magic?trip=" + tripId);
  await page.getByRole("button", { name: "Find a little Magic ✧" }).click();
  await expect(page.locator(".discovery").first()).toBeVisible();
  await page.getByRole("button", { name: "Save moment" }).first().click();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Moments to remember" }),
  ).toBeVisible();
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: /Tokyo with family/ }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: evidence("home-light"), fullPage: true });
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: evidence("home-dark"), fullPage: true });
  await page.goto("/outfits?trip=" + tripId);
  await page
    .getByRole("button", { name: "Generate outfits", exact: true })
    .click();
  await expect(card).toBeVisible();
  await page.screenshot({ path: evidence("outfits-dark"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Where shall we go?" }),
  ).toBeVisible();
  await page.screenshot({ path: evidence("mobile-dark"), fullPage: true });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Switch to light theme" }).click();
  await page.screenshot({ path: evidence("mobile-light"), fullPage: true });
  await page.goto("/outfits?trip=" + tripId);
  await page
    .getByRole("button", { name: "Generate outfits", exact: true })
    .click();
  await expect(card).toBeVisible();
  await page.screenshot({ path: evidence("mobile-outfits"), fullPage: true });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  expect(errors).toEqual([]);
});

test("empty, loading, error/retry and local-session isolation", async ({
  page,
  browser,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "An unwritten adventure" }),
  ).toBeVisible();
  await page.route("**/v1/consumer/wardrobe", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 400));
    await route.fulfill({
      status: 503,
      json: { error: { message: "Wardrobe temporarily unavailable" } },
    });
  });
  await page.getByRole("button", { name: "My wardrobe ↗" }).click();
  await expect(page.getByRole("status")).toContainText("Turning the page");
  await expect(page.getByRole("alert")).toContainText(
    "Wardrobe temporarily unavailable",
  );
  await page.unroute("**/v1/consumer/wardrobe");
  await page.reload();
  await expect(page.locator(".garment")).toHaveCount(34);
  const second = await browser.newContext();
  const another = await second.newPage();
  await another.goto("http://127.0.0.1:5173");
  await expect(
    another.getByRole("heading", { name: "An unwritten adventure" }),
  ).toBeVisible();
  await second.close();
});

test("touch swipes and keyboard alternatives are usable on a phone", async ({
  browser,
}) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
  });
  const page = await context.newPage();
  await page.goto("/wardrobe");
  await expect(page.locator(".garment")).toHaveCount(34);
  await page.getByRole("button", { name: "Find my outfits" }).click();
  await page
    .getByRole("button", { name: "Generate outfits", exact: true })
    .click();
  const card = page.getByRole("group", { name: "Outfit swipe card" });
  await expect(card).toBeVisible();
  await card.scrollIntoViewIfNeeded();
  const session = await context.newCDPSession(page);
  let box = await card.boundingBox();
  if (!box) throw new Error("Missing card");
  let x = box.x + box.width / 2,
    y = box.y + 80;
  await session.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{ x, y }],
  });
  for (let i = 1; i <= 6; i++)
    await session.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [{ x: x + i * 22, y }],
    });
  await session.send("Input.dispatchTouchEvent", {
    type: "touchEnd",
    touchPoints: [],
  });
  await expect(page.locator(".liked-counter")).toContainText("1");
  await page
    .getByRole("button", { name: "Undo last swipe", exact: true })
    .click();
  await expect(page.locator(".liked-counter")).toContainText("0");
  box = await card.boundingBox();
  if (!box) throw new Error("Missing card");
  x = box.x + box.width / 2;
  y = box.y + 80;
  await session.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{ x, y }],
  });
  for (let i = 1; i <= 6; i++)
    await session.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [{ x: x - i * 22, y }],
    });
  await session.send("Input.dispatchTouchEvent", {
    type: "touchEnd",
    touchPoints: [],
  });
  await expect(page.getByRole("status")).toContainText("Passed");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await context.close();
});
