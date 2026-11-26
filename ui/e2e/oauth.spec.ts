/** Regression for the Settings → Rotur anchor: /api/... links are server
 *  routes and must be left to the browser, not swallowed by preact-iso. */
import { expect } from "@playwright/test";
import { openRoute, test } from "./fixtures";

test("Settings Rotur link navigates to the authorize endpoint", async ({ signedInPage }) => {
    await signedInPage.setViewportSize({ width: 1280, height: 800 });

    // A local, 302-free HTML response keeps the test offline while proving the
    // browser really followed the anchor instead of the SPA router.
    await signedInPage.route("**/api/auth/rotur/authorize**", route =>
        route.fulfill({
            status: 200,
            contentType: "text/html; charset=utf-8",
            body: "<!doctype html><html><body><h1>oauth stub</h1></body></html>",
        }));

    await openRoute(signedInPage, "/settings");
    const link = signedInPage.getByRole("link", { name: /Sign in with Rotur/i });
    await expect(link).toHaveAttribute("href", "/api/auth/rotur/authorize?next=%2Fsettings");

    await link.click();

    await expect(signedInPage).toHaveURL(/\/api\/auth\/rotur\/authorize\?next=%2Fsettings$/);
    await expect(signedInPage.getByRole("heading", { name: "oauth stub" })).toBeVisible();
    await expect(signedInPage.locator("body")).not.toContainText("page not found :(");
});
