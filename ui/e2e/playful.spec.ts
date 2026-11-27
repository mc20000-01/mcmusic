/** Phase 1 guards for the playful web language: generated blob placeholders,
 *  the play/pause morph, the wavy progress line and the Lyrics | Up next
 *  segmented pill. Screenshots of the open sheet are uploaded as artifacts.
 */
import { expect } from "@playwright/test";
import { checkLayout, openRoute, test } from "./fixtures";

/** Make the media element report a real play event without decoding audio. */
async function fakePlayback(page: import("@playwright/test").Page) {
    await page.addInitScript(() => {
        HTMLMediaElement.prototype.play = function () {
            this.dispatchEvent(new Event("play"));
            return Promise.resolve();
        };
        HTMLMediaElement.prototype.pause = function () {
            this.dispatchEvent(new Event("pause"));
            return Promise.resolve();
        };
    });
}

test("placeholders use the generated canonical blob paths", async ({ signedInPage }) => {
    await openRoute(signedInPage, "/");
    const shapes = signedInPage.locator("#player-bar .cover-placeholder[data-blob]");
    await expect(shapes.first()).toBeVisible();

    const paths = await signedInPage.locator("#player-bar .cover-blob path").evaluateAll(
        nodes => nodes.map(node => node.getAttribute("d") ?? ""));
    expect(paths.length).toBeGreaterThan(0);
    for (const path of paths) {
        expect(path.startsWith("M ")).toBe(true);
        expect(path.endsWith(" Z")).toBe(true);
        expect(path.length).toBeGreaterThan(40);
    }
});

test("play morphs the button into a blob and starts the progress wave", async ({ signedInPage }) => {
    await fakePlayback(signedInPage);
    await openRoute(signedInPage, "/");

    const play = signedInPage.locator("#player-bar .play-pause");
    const pausedRadius = await play.evaluate(el => getComputedStyle(el).borderRadius);
    await play.click();
    await expect(play).toHaveClass(/playing/);

    const playingRadius = await play.evaluate(el => getComputedStyle(el).borderRadius);
    expect(playingRadius).not.toBe(pausedRadius);
    expect(playingRadius).toContain("%");

    // The pause bars must stay vertical (||), not rotate into an equals sign.
    const glyphTransform = await play.locator("svg").evaluate(el => getComputedStyle(el).transform);
    expect(glyphTransform).toBe("none");
    await expect(signedInPage.locator("#player-bar .seek-wave path")).toBeVisible();

    // The wave is decorative: turning playful motion off removes it.
    await signedInPage.evaluate(() => {
        document.documentElement.dataset.playful = "false";
    });
    await expect(signedInPage.locator("#player-bar .seek-wave")).toBeHidden();
});

/** Compact tiers fold the lyrics action into the More popover. */
async function openLyrics(page: import("@playwright/test").Page) {
    const more = page.locator("#player-bar .control-more");
    if (await more.isVisible()) {
        await more.click();
        await page.locator('.player-more-menu .button[title="Lyrics"]').click();
    } else {
        await page.locator("#player-bar .control-lyrics").click();
    }
}

test("Lyrics and Up next are peer tabs in one pill", async ({ signedInPage }) => {
    await signedInPage.setViewportSize({ width: 1280, height: 800 });
    await openRoute(signedInPage, "/");
    await openLyrics(signedInPage);

    const lyricsTabs = signedInPage.locator(".lyrics-panel .sheet-tabs");
    await expect(lyricsTabs).toBeVisible();
    await expect(lyricsTabs.locator('.sheet-tab[aria-pressed="true"]')).toContainText("Lyrics");
    await expect(signedInPage.locator(".lyrics-panel .sheet-actions")).toBeVisible();

    await lyricsTabs.locator(".sheet-tab", { hasText: "Up next" }).click();
    await expect(signedInPage.locator(".queue-drawer")).toBeVisible();
    await expect(
        signedInPage.locator('.queue-drawer .sheet-tab[aria-pressed="true"]'),
    ).toContainText("Up next");

    await signedInPage.locator(".queue-drawer .sheet-tab", { hasText: "Lyrics" }).click();
    await expect(signedInPage.locator(".lyrics-panel")).toBeVisible();
    await expect(signedInPage.locator(".queue-drawer")).toHaveCount(0);
});

for (const width of [800, 1024, 1280]) {
    test(`sheet screenshot at ${width}px`, async ({ signedInPage }, testInfo) => {
        await signedInPage.setViewportSize({ width, height: 800 });
        await openRoute(signedInPage, "/");
        await openLyrics(signedInPage);
        await expect(signedInPage.locator(".lyrics-panel .sheet-tabs")).toBeVisible();
        await signedInPage.screenshot({
            path: testInfo.outputPath(`playful-sheet-${width}.png`),
            fullPage: true,
        });
        await checkLayout(signedInPage, `playful sheet @ ${width}x800`);
    });
}
