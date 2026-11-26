/** Reflow regressions across the full viewport matrix and every route.
 *
 * Sizes are grouped into one test per width: each test reuses a single signed-in
 * page (fresh per test) for all heights and routes instead of creating hundreds
 * of separate browser contexts.
 */
import {
    ROUTES,
    VIEWPORT_HEIGHTS,
    VIEWPORT_WIDTHS,
    checkLayout,
    openRoute,
    test,
} from "./fixtures";

for (const width of VIEWPORT_WIDTHS) {
    test(`all routes fit at ${width}px (heights ${VIEWPORT_HEIGHTS.join(", ")})`, async ({ signedInPage }) => {
        for (const height of VIEWPORT_HEIGHTS) {
            await signedInPage.setViewportSize({ width, height });
            for (const route of ROUTES) {
                await openRoute(signedInPage, route);
                await checkLayout(signedInPage, `${route} @ ${width}x${height}`);
            }
        }
    });
}

for (const width of VIEWPORT_WIDTHS) {
    test(`all routes fit at ${width}px with 200% text`, async ({ signedInPage }) => {
        await signedInPage.setViewportSize({ width, height: 800 });
        for (const route of ROUTES) {
            await openRoute(signedInPage, route);
            // Re-inject after every navigation: styles do not survive a reload.
            await signedInPage.addStyleTag({ content: ":root{font-size:200%}" });
            await signedInPage.evaluate(() => new Promise<void>(resolve =>
                requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
            await checkLayout(signedInPage, `${route} @ ${width}x800 @ 200% text`);
        }
    });
}
