/* Pure web checks for the 4.0.1 Lucide icon style helpers.
 *
 * Run directly with Node's TypeScript stripping, or through
 * `python -m unittest tests.test_icon_prefs`. No DOM is required: theme.ts
 * guards its document access, so the math can be tested in isolation.
 */
import assert from "node:assert/strict";
import test from "node:test";
import {
    DEFAULT_ICON_FILLED, DEFAULT_ICON_STROKE,
    iconStrokeWidth, lucideStrokeWidth, normalizeIconStroke,
} from "../ui/src/common/theme.ts";

test("icon stroke snaps to the three allowed widths", () => {
    assert.equal(DEFAULT_ICON_STROKE, 1);
    assert.equal(DEFAULT_ICON_FILLED, false);
    assert.equal(normalizeIconStroke(undefined), 1);
    assert.equal(normalizeIconStroke("wide"), 1);
    assert.equal(normalizeIconStroke("1.7"), 1.5);
    assert.equal(normalizeIconStroke(2), 2);
    assert.equal(normalizeIconStroke(1.25), 1);
});

test("1x is Lucide's default stroke and 2x respects the ceiling", () => {
    assert.equal(iconStrokeWidth(1, 20), 20 / 12);
    assert.equal(iconStrokeWidth(1.5, 20), 20 / 8);
    assert.equal(iconStrokeWidth(2, 32), 32 / 6);
    assert.equal(iconStrokeWidth(2, 52), 52 / 6);
    assert.equal(iconStrokeWidth(1, 48), 4);
    assert.equal(iconStrokeWidth(1.5, 48), 6);
    assert.equal(iconStrokeWidth(2, 16), 16 / 6);
});

test("lucideStrokeWidth converts rendered pixels into viewBox units", () => {
    assert.equal(lucideStrokeWidth(1, 24), 2);
    assert.equal(lucideStrokeWidth(1, 16), 2);
    assert.equal(lucideStrokeWidth(1.5, 48), 3);
    assert.equal(lucideStrokeWidth(2, 52), 4);
    // Bad sizes fall back to 24px rather than producing NaN or Infinity.
    assert.equal(lucideStrokeWidth(1, 0), 2);
});
