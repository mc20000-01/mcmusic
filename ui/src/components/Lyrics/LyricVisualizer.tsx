/** Compact, deterministic lyric visualizer for the web lyrics panel.
 *
 * The shape is a pure function of a virtual clock seeded from the player's
 * `position` signal and advanced with requestAnimationFrame only while
 * `isPlaying` is true — pausing leaves the last frame on screen. A change of
 * active lyric gives a short brightness/phase lift. There is no audio
 * analyser, randomness, dependency or network access here.
 */
import { useEffect, useRef } from "preact/hooks";
import { isPlaying, position } from "../../common/player";

export type VisualizerMode = "bars" | "wave" | "glow";

export const VISUALIZER_KEY = "mcmusic:lyricsVisualizer";
export const VISUALIZER_MODES: readonly VisualizerMode[] = ["bars", "wave", "glow"];
export const VISUALIZER_LABELS: Record<VisualizerMode, string> = {
    bars: "Bars",
    wave: "Wave",
    glow: "Glow",
};

export function readVisualizerMode(): VisualizerMode {
    try {
        const v = localStorage.getItem(VISUALIZER_KEY);
        if (v === "bars" || v === "wave" || v === "glow") return v;
    } catch { /* storage may be unavailable; keep the default */ }
    return "bars";
}

export function saveVisualizerMode(mode: VisualizerMode) {
    try { localStorage.setItem(VISUALIZER_KEY, mode); } catch { /* ignore */ }
}

const BANDS = 36;
const GLOWS = 5;
const VIOLET = "160, 107, 255"; // flufi accent #A06BFF
const FLASH_MS = 520;

function clamp(v: number, lo: number, hi: number): number {
    return Math.min(hi, Math.max(lo, v));
}

/** Layered sines give a stable, spectrum-like value for each band and time. */
function band(i: number, t: number): number {
    const beat = 0.5 + 0.5 * Math.sin(t * 2.3 + i * 0.37);
    const ripple = 0.5 + 0.5 * Math.sin(t * 4.1 - i * 0.64);
    const envelope = Math.pow(Math.sin(Math.PI * ((i + 0.5) / BANDS)), 0.55);
    const shimmer = 0.5 + 0.5 * Math.sin(t * 1.7 + i * 1.13);
    return clamp(0.06 + envelope * (0.34 * beat + 0.40 * ripple) + 0.06 * shimmer, 0, 1);
}

function paint(
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    mode: VisualizerMode,
    t: number,
    flash: number,
) {
    ctx.clearRect(0, 0, w, h);
    const mid = h / 2;
    const lift = 1 + flash * 0.35;
    const alpha = (a: number) => String(clamp(a, 0, 1));
    const values = Array.from({ length: BANDS }, (_, i) => band(i, t + flash * 0.7));

    if (mode === "bars") {
        const gap = 2;
        const barW = Math.max(1, (w - gap * (BANDS - 1)) / BANDS);
        for (let i = 0; i < BANDS; i++) {
            const bh = Math.max(2, values[i] * (h - 6) * lift);
            const x = i * (barW + gap);
            const y = h - bh;
            ctx.fillStyle = `rgba(${VIOLET}, ${alpha((0.36 + values[i] * 0.5) * lift)})`;
            ctx.fillRect(x, y, barW, bh);
            ctx.fillStyle = `rgba(184, 136, 255, ${alpha(0.35 + flash * 0.4)})`;
            ctx.fillRect(x, y, barW, 1);
        }
        return;
    }

    if (mode === "wave") {
        const amp = (h / 2 - 3) * lift;
        ctx.beginPath();
        for (let i = 0; i < BANDS; i++) {
            const x = (i / (BANDS - 1)) * w;
            const y = mid - values[i] * amp;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        for (let i = BANDS - 1; i >= 0; i--) {
            ctx.lineTo((i / (BANDS - 1)) * w, mid + values[i] * amp);
        }
        ctx.closePath();
        ctx.fillStyle = `rgba(${VIOLET}, ${alpha(0.12 + flash * 0.12)})`;
        ctx.fill();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = `rgba(${VIOLET}, ${alpha(0.72 + flash * 0.28)})`;
        ctx.stroke();
        return;
    }

    for (let i = 0; i < GLOWS; i++) {
        const v = band((i * 7) % BANDS, t + i * 1.23 + flash * 0.7);
        const x = ((i + 0.5) / GLOWS) * w;
        const y = mid + Math.sin(t * 1.3 + i * 2.1) * h * 0.12;
        const r = Math.max(4, (h * 0.22 + v * h * 0.3) * lift);
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, r);
        gradient.addColorStop(0, `rgba(${VIOLET}, ${alpha((0.42 + v * 0.24) * lift)})`);
        gradient.addColorStop(0.45, `rgba(${VIOLET}, ${alpha(0.16 + flash * 0.14)})`);
        gradient.addColorStop(1, "rgba(8, 6, 13, 0)"); // ink #08060D
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
    }
}

export function LyricVisualizer(props: {
    mode: VisualizerMode;
    activeIndex: number;
}) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const modeRef = useRef(props.mode);
    const flashAtRef = useRef(0);
    const scheduleRef = useRef<(() => void) | null>(null);
    const prevIndexRef = useRef(props.activeIndex);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let width = 0;
        let height = 0;
        let raf = 0;
        let playing = isPlaying.value;
        let base = position.value;
        let baseAt = performance.now();

        function time(): number {
            // Smoothly interpolate between the ~4 Hz position updates while
            // playing; the signal remains the clock source for the shape.
            return base + (playing ? clamp((performance.now() - baseAt) / 1000, 0, 0.5) : 0);
        }

        function flashValue(now: number): number {
            return flashAtRef.current ? clamp(1 - (now - flashAtRef.current) / FLASH_MS, 0, 1) : 0;
        }

        function render(flash: number) {
            paint(ctx!, width, height, modeRef.current, time(), flash);
        }

        function frame() {
            raf = 0;
            const flash = flashValue(performance.now());
            if (flash <= 0) flashAtRef.current = 0;
            render(flash);
            if (playing) schedule();
        }

        function schedule() {
            if (!raf) raf = requestAnimationFrame(frame);
        }

        function resize() {
            const rect = canvas!.getBoundingClientRect();
            const dpr = clamp(window.devicePixelRatio || 1, 1, 2);
            width = Math.max(1, rect.width);
            height = Math.max(1, rect.height);
            const pw = Math.max(1, Math.round(width * dpr));
            const ph = Math.max(1, Math.round(height * dpr));
            if (canvas!.width !== pw || canvas!.height !== ph) {
                canvas!.width = pw;
                canvas!.height = ph;
            }
            ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
            render(flashValue(performance.now()));
        }

        const unsubPosition = position.subscribe((p) => {
            base = p;
            baseAt = performance.now();
            if (!playing) schedule(); // seek while paused still redraws the frame
        });

        const unsubPlaying = isPlaying.subscribe((v) => {
            if (v !== playing) {
                if (!v) base = time(); // hold the exact frame when paused
                playing = v;
                baseAt = performance.now();
                if (!playing && raf) {
                    cancelAnimationFrame(raf);
                    raf = 0;
                }
            }
            schedule();
        });

        const observer = typeof ResizeObserver === "undefined"
            ? null
            : new ResizeObserver(resize);
        observer?.observe(canvas);
        window.addEventListener("resize", resize);
        scheduleRef.current = schedule;
        resize();

        return () => {
            unsubPosition();
            unsubPlaying();
            if (raf) cancelAnimationFrame(raf);
            observer?.disconnect();
            window.removeEventListener("resize", resize);
            scheduleRef.current = null;
        };
    }, []);

    useEffect(() => {
        modeRef.current = props.mode;
        scheduleRef.current?.();
    }, [props.mode]);

    useEffect(() => {
        if (prevIndexRef.current === props.activeIndex) return;
        prevIndexRef.current = props.activeIndex;
        // A paused visualizer gets one static lift, never a looping animation.
        flashAtRef.current = performance.now() - (isPlaying.value ? 0 : FLASH_MS * 0.65);
        scheduleRef.current?.();
    }, [props.activeIndex]);

    const label = VISUALIZER_LABELS[props.mode];
    return (
        <canvas
            ref={canvasRef}
            class="lyrics-visualizer"
            role="img"
            title={`${label} lyric visualizer`}
            aria-label={`${label} lyric visualizer`}
        />
    );
}
