/** Server-owned paths must trigger a document request, never a SPA route.
 *
 * The shell used to intercept every same-origin anchor except `/api/...`, so
 * OAuth authorize URLs, downloads, health checks, static assets and icons
 * were swallowed and rendered as a client-side 404. These tests assert both
 * the scope predicate and the real navigation request in the browser.
 */
import { expect } from "@playwright/test";
import { openRoute, test } from "./fixtures";
import { SPA_SCOPE } from "../src/common/routeScope";

const SERVER_HREFS = [
    "/api",
    "/api/auth/rotur/authorize?next=%2Fsettings",
    "/health",
    "/apps/test.apk",
    "/get",
    "/downloads",
    "/embed",
    "/embeds",
    "/video-cache/abc.mp4",
    "/u/e2e-user",
    "/static/ui/app.css",
    "/manifest.webmanifest",
    "/sw.js",
    "/favicon.ico",
    "/icon-192.png",
    "/icon-maskable-512.png",
    "/apple-touch-icon.png",
];

const SPA_HREFS = [
    "/",
    "/search",
    "/settings",
    "/auth",
    "/forgot",
    "/reset?token=abc",
    "/not-allowed",
    "/artist/artist%3A%3AE2E%20Artist",
    "/downloads-local",
];

test("SPA scope excludes server routes and keeps client pages", async () => {
    for (const href of SERVER_HREFS)
        expect(SPA_SCOPE.test(href), `server route ${href}`).toBe(false);
    for (const href of SPA_HREFS)
        expect(SPA_SCOPE.test(href), `client page ${href}`).toBe(true);
});

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

    const navigated = signedInPage.waitForEvent("framenavigated", frame =>
        frame === signedInPage.mainFrame() &&
        new URL(frame.url()).pathname === "/api/auth/rotur/authorize");

    await link.click();
    await navigated;

    await expect(signedInPage).toHaveURL(/\/api\/auth\/rotur\/authorize\?next=%2Fsettings$/);
    await expect(signedInPage.getByRole("heading", { name: "oauth stub" })).toBeVisible();
    await expect(signedInPage.locator("body")).not.toContainText("page not found :(");
});

// Chromium reserves /favicon.ico for the browser's own icon request and does
// not perform a top-level navigation when that exact URL is clicked, so its
// exclusion from the SPA scope is asserted by the predicate test above.
const DOCUMENT_HREFS = SERVER_HREFS.filter(
    p => !p.startsWith("/api") && p !== "/favicon.ico",
);

for (const pathname of DOCUMENT_HREFS) {
    test(`${pathname} is loaded as a document`, async ({ signedInPage }) => {
        await signedInPage.setViewportSize({ width: 1280, height: 800 });
        await signedInPage.route(url => url.pathname === pathname, route =>
            route.fulfill({
                status: 200,
                contentType: "text/html; charset=utf-8",
                body: "<!doctype html><html><body><h1>server stub</h1></body></html>",
            }));

        await openRoute(signedInPage, "/settings");
        await signedInPage.evaluate((href) => {
            const a = document.createElement("a");
            a.id = "server-link";
            a.href = href;
            a.textContent = "server link";
            // The app owns the viewport; lift the probe above its chrome.
            a.style.position = "fixed";
            a.style.top = "0";
            a.style.left = "0";
            a.style.zIndex = "2147483647";
            a.style.background = "white";
            document.body.appendChild(a);
        }, pathname);

        const navigations: string[] = [];
        const onRequest = (req: { isNavigationRequest: () => boolean; url: () => string }) => {
            if (req.isNavigationRequest()) navigations.push(new URL(req.url()).pathname);
        };
        signedInPage.on("request", onRequest);
        const navigated = signedInPage.waitForEvent("framenavigated", frame =>
            frame === signedInPage.mainFrame() && new URL(frame.url()).pathname === pathname);

        await signedInPage.locator("#server-link").click();
        await navigated;
        await expect.poll(() => navigations).toContain(pathname);
        signedInPage.off("request", onRequest);

        await expect(signedInPage).toHaveURL(url => url.pathname === pathname);
        await expect(signedInPage.getByRole("heading", { name: "server stub" })).toBeVisible();
        await expect(signedInPage.locator("body")).not.toContainText("page not found :(");
    });
}

test("unconfigured Discord link is a disabled button, not href=\"#\"", async ({ signedInPage }) => {
    await openRoute(signedInPage, "/settings");
    // The status endpoint is stubbed without `configured`, so linking is off.
    await expect(signedInPage.getByRole("button", { name: /Link Discord/i })).toBeDisabled();
    await expect(signedInPage.locator('a[href="#"]')).toHaveCount(0);
    await expect(signedInPage.getByText(/Discord linking needs/i)).toBeVisible();
});
