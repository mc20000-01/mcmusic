/** Cover-derived tonal colour for the web player.
 *
 * Loads the same cover the UI already displays, samples its dominant flat
 * colour on a tiny canvas and seeds a Material 3 tonal scheme through HCT in
 * `theme.ts`. Missing artwork, disabled covers and failed extraction clear the
 * seed so the chosen family palette stays in charge. No external requests are
 * made and no decorative effects are introduced.
 */
import { useEffect } from "preact/hooks";
import { covers } from "./prefs";
import { setCoverSeed } from "./theme";

const cache = new Map<string, string>();
let requestId = 0;

function hex(r: number, g: number, b: number): string {
    return "#" + [r, g, b].map(v => Math.max(0, Math.min(255, Math.round(v)))
        .toString(16).padStart(2, "0")).join("");
}

function loadImage(src: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.decoding = "async";
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error(`cover image failed: ${src}`));
        image.src = src;
    });
}

/** Quantise to 16-level buckets and weight saturated tones over grey ones. */
function dominantColour(image: HTMLImageElement): string | null {
    if (typeof document === "undefined") return null;
    const size = 24;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) return null;
    context.drawImage(image, 0, 0, size, size);
    let data: Uint8ClampedArray;
    try {
        data = context.getImageData(0, 0, size, size).data;
    } catch {
        return null;
    }
    const buckets = new Map<string, { score: number; weight: number; r: number; g: number; b: number }>();
    for (let i = 0; i < data.length; i += 4) {
        const a = data[i + 3];
        if (a < 128) continue;
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        if (max < 24 || max > 248) continue;
        const saturation = max === 0 ? 0 : (max - min) / max;
        const weight = 1 + saturation * 4;
        const key = `${r >> 4}-${g >> 4}-${b >> 4}`;
        const bucket = buckets.get(key) ?? { score: 0, weight: 0, r: 0, g: 0, b: 0 };
        bucket.score += weight;
        bucket.weight += 1;
        bucket.r += r;
        bucket.g += g;
        bucket.b += b;
        buckets.set(key, bucket);
    }
    let best: { score: number; weight: number; r: number; g: number; b: number } | null = null;
    for (const bucket of buckets.values())
        if (!best || bucket.score > best.score) best = bucket;
    if (!best) return null;
    return hex(best.r / best.weight, best.g / best.weight, best.b / best.weight);
}

async function apply(src: string): Promise<void> {
    const id = ++requestId;
    const usable = !!src && !src.startsWith("placeholder:") && covers.value;
    if (!usable) {
        setCoverSeed(null);
        return;
    }
    let seed = cache.get(src) ?? null;
    if (seed == null) {
        try {
            seed = dominantColour(await loadImage(src));
        } catch {
            seed = null;
        }
        if (seed) cache.set(src, seed);
    }
    if (id !== requestId) return;
    setCoverSeed(seed);
}

/** Apply the current track's cover colour, falling back to the family palette. */
export function useCoverColour(src: string | null | undefined): void {
    const value = src ?? "";
    useEffect(() => {
        void apply(value);
        return () => {
            requestId++;
            setCoverSeed(null);
        };
    }, [value, covers.value]);
}
