/** One breakpoint source of truth for JS chrome decisions.
 *
 * The CSS tiers live in app.css container queries; the numeric boundaries are
 * generated from design/tokens.json so the flufi `innerWidth < 800` signal can
 * no longer disagree with the stylesheet at exactly 800px.
 */
import { computed, signal } from "@preact/signals";
import { COMPACT_BREAKPOINT, isMobileChrome, tierForWidth, type ResponsiveTier } from "./breakpoints.generated";

const initialWidth = typeof window === "undefined" ? COMPACT_BREAKPOINT : window.innerWidth;

export const tier = signal<ResponsiveTier>(tierForWidth(initialWidth));
export const mobileChrome = computed(() => isMobileChrome(tier.value));

function update() {
    tier.value = tierForWidth(window.innerWidth);
}

if (typeof window !== "undefined") {
    update();
    window.addEventListener("resize", update, { passive: true });
}
