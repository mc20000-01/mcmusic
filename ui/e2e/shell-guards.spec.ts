/** Targeted guards for the shell reflow: no overflow clipping, breakpoint
 *  tiers, a short-viewport player bar, and reference screenshots. */
import { expect } from "@playwright/test";
import { checkLayout, openRoute, test } from "./fixtures";

const CLIPPING_SELECTORS = [
    "html",
    "body",
    "#app",
    "#app > div",
    "#app > div > main",
    'main[class^="content-"]',
] as const;

// Text that is *meant* to truncate; it must not trip the clipping guard.
const ELLIPSIS_EXEMPTIONS = [
    ".clip",
    ".user",
    ".library-title",
    ".device-name",
    ".device-meta",
    ".track .center > .name",
].join(", ");

test("no overflow clipping hides an overflowing shell", async ({ signedInPage }) => {
    for (const width of [320, 800, 1280]) {
        await signedInPage.setViewportSize({ width, height: 800 });
        await openRoute(signedInPage, "/");

        const violations: string[] = await signedInPage.evaluate(({ selectors, exemptions }) => {
            const out: string[] = [];
            const main = document.querySelector('main[class^="content-"]');
            if (!main) return ["missing main[class^=content-]"];

            // Force a real overflow so the guard exercises the condition instead
            // of passing trivially on an empty page.
            const probe = document.createElement("div");
            probe.dataset.e2eProbe = "true";
            probe.style.cssText = "width:3000px;height:1px;flex:none;pointer-events:none;";
            main.appendChild(probe);

            const clips = (value: string) =>
                value.split(/\s+/).some(v => v === "hidden" || v === "clip");
            const name = (el: Element) => {
                const id = el.id ? `#${el.id}` : "";
                const cls = typeof el.className === "string" && el.className
                    ? `.${el.className.trim().split(/\s+/).slice(0, 2).join(".")}`
                    : "";
                return `${el.tagName.toLowerCase()}${id}${cls}`;
            };

            for (const selector of selectors) {
                for (const el of Array.from(document.querySelectorAll(selector))) {
                    if (el instanceof Element &&
                        (el.matches(exemptions) || el.closest(exemptions))) continue;
                    if (el.scrollWidth <= el.clientWidth + 1) continue;
                    const cs = getComputedStyle(el);
                    const bad = clips(cs.overflow) || clips(cs.overflowX) || clips(cs.overflowY);
                    if (bad) {
                        out.push(`${selector} (${name(el)}) scrollWidth ${el.scrollWidth} > clientWidth ${el.clientWidth} but overflow=${cs.overflow} / ${cs.overflowX} / ${cs.overflowY}`);
                    }
                }
            }

            probe.remove();
            return out;
        }, { selectors: CLIPPING_SELECTORS, exemptions: ELLIPSIS_EXEMPTIONS });

        expect(violations, `overflow guard at ${width}px:\n${violations.join("\n")}`).toEqual([]);
    }
});

for (const [width, expected] of [
    [799, "tablet"],
    [800, "compact"],
    [1099, "compact"],
    [1100, "full"],
] as const) {
    test(`shell data-tier is ${expected} at ${width}px`, async ({ signedInPage }) => {
        await signedInPage.setViewportSize({ width, height: 800 });
        await openRoute(signedInPage, "/");
        await expect(signedInPage.locator("#app > div").first()).toHaveAttribute("data-tier", expected);
    });
}

test("player bar stays in view and content scrolls at 1280x600", async ({ signedInPage }) => {
    await signedInPage.setViewportSize({ width: 1280, height: 600 });
    await openRoute(signedInPage, "/");

    const result = await signedInPage.evaluate(() => {
        const player = document.querySelector("#player-bar");
        const main = document.querySelector('main[class^="content-"]');
        if (!player || !main) return { playerVisible: false, scrollable: false, scrolled: false };

        const r = player.getBoundingClientRect();
        const playerVisible = r.left >= -1 && r.top >= -1 &&
            r.right <= window.innerWidth + 1 && r.bottom <= window.innerHeight + 1;

        // Guarantee overflowing content so this checks the scroll container,
        // not whether the stubbed library happens to be tall enough today.
        const probe = document.createElement("div");
        probe.dataset.e2eProbe = "true";
        probe.style.cssText = "width:1px;height:2000px;flex:none;pointer-events:none;";
        main.appendChild(probe);
        const before = main.scrollTop;
        main.scrollTop = 400;
        const after = main.scrollTop;
        const scrollable = main.scrollHeight > main.clientHeight + 1;
        probe.remove();

        return { playerVisible, scrollable, scrolled: after > before };
    });

    expect(result.playerVisible, "player bar must be inside the 1280x600 viewport").toBe(true);
    expect(result.scrollable, "content main must be a vertical scroll container").toBe(true);
    expect(result.scrolled, "content main must actually scroll vertically").toBe(true);
});

for (const width of [800, 1024, 1280]) {
    test(`home screenshot at ${width}px`, async ({ signedInPage }, testInfo) => {
        await signedInPage.setViewportSize({ width, height: 800 });
        await openRoute(signedInPage, "/");
        await signedInPage.screenshot({
            path: testInfo.outputPath(`home-${width}.png`),
            fullPage: true,
        });
        await checkLayout(signedInPage, `home @ ${width}x800 (screenshot)`);
    });
}
