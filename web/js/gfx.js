/* ==========================================================================
   mcmusic — per-device graphics quality
   Local storage only. Nothing here is sent to the account settings endpoint.
   The browser UI reads data-gfx from <html>, the same way it reads the theme.
   ========================================================================== */

import { RealGlass } from "./glass.js";

export const GFX_LEVELS = [
  { key: "off", label: "Off", blurb: "Solid tints only. No blur, filters, or motion." },
  { key: "low", label: "Low", blurb: "Light static blur on floating controls only." },
  { key: "medium", label: "Medium", blurb: "Standard glass on floating controls; solid panels." },
  { key: "high", label: "High", blurb: "Full glass on floating controls and panels." },
  { key: "max", label: "Max", blurb: "High plus real glass refraction where supported." },
];

const STORAGE_KEY = "mc_gfx_v1";
const DETECT_KEY = "mc_gfx_detect_v1";
const root = document.documentElement;
const COOLDOWN = 60_000;
const SAMPLE_MS = 2_000;
const RAISE_AFTER = 30_000;

const media = (query) => {
  try {
    return !!(window.matchMedia && window.matchMedia(query).matches);
  } catch {
    return false;
  }
};

const clampInt = (value) => Math.max(0, Math.min(4, Math.round(Number(value) || 0)));

function readJson(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}

function writeJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch { /* private mode */ }
}

function rendererName() {
  try {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    if (!gl) return "";
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    return String(
      (ext && gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) || gl.getParameter(gl.RENDERER) || ""
    );
  } catch {
    return "";
  }
}

function detect() {
  const renderer = rendererName();
  const cores = Number(navigator.hardwareConcurrency) || 8;
  const memory = Number(navigator.deviceMemory) || 8;
  const coarse = media("(pointer: coarse)");
  const dpr = Number(window.devicePixelRatio) || 1;
  const pixels = (Number(screen.width) || innerWidth) * (Number(screen.height) || innerHeight) * dpr * dpr;
  const software = /swiftshader|llvmpipe|software|softpipe/i.test(renderer);

  const cached = readJson(DETECT_KEY);
  if (cached && cached.v === 1 && cached.renderer === renderer &&
      cached.cores === cores && cached.memory === memory && cached.coarse === coarse) {
    return cached;
  }

  // A modern phone can report 4 GB while still being a strong device; only
  // treat low memory as weak on a fine-pointer machine.
  const weak = cores <= 4 || (memory <= 4 && !coarse);
  let start = 2;
  if (software) start = 0;
  else if (weak) start = 1;
  else if (coarse && cores >= 8 && memory >= 4) start = 3;
  else if (!coarse && cores >= 12 && memory >= 8) start = 3;

  let cap = start;
  if (!coarse && pixels > 8_300_000) cap = Math.min(cap, 2);
  if (software) cap = 1;

  const result = {
    v: 1,
    renderer,
    software,
    cores,
    memory,
    coarse,
    dpr,
    pixels,
    start,
    cap,
  };
  writeJson(DETECT_KEY, result);
  return result;
}

const state = {
  level: 2,
  auto: true,
  frameMs: null,
  detected: null,
  battery: null,
  saveData: false,
  paused: false,
  ready: false,
};

let stats = { goodMs: 0, lastChange: 0 };
let sampleEnd = 0;
let sampling = false;
let frameRaf = 0;
let notifier = null;
let listenersBound = false;

const software = () => !!state.detected?.software;
const reducedTransparency = () => media("(prefers-reduced-transparency: reduce)");
const reducedMotion = () => media("(prefers-reduced-motion: reduce)");
const powerLimited = () => state.saveData ||
  !!(state.battery && !state.battery.charging && state.battery.level < 0.2);
const manualMax = () => Math.min(4, software() ? 1 : 4, reducedTransparency() ? 1 : 4);
const detectedCap = () => Math.min(state.detected?.cap ?? 2, manualMax());
const autoCap = () => Math.min(detectedCap(), powerLimited() ? 1 : 4);

function currentMax(isAuto) {
  return isAuto ? autoCap() : manualMax();
}

function apply() {
  const isAuto = state.auto;
  state.level = Math.max(0, Math.min(currentMax(isAuto), clampInt(state.level)));
  root.dataset.gfx = String(state.level);
  root.classList.toggle("gfx-software", software());
  root.classList.toggle("gfx-reduced-motion", reducedMotion());
  root.classList.toggle("gfx-reduced-transparency", reducedTransparency());
  root.classList.toggle("gfx-paused", state.paused);
  RealGlass.setQuality(state.level);

  window.__gfx = {
    level: state.level,
    auto: state.auto,
    renderer: state.detected?.renderer || "",
    frameMs: state.frameMs,
    caps: {
      software: software(),
      detected: state.detected?.start ?? 2,
      cap: autoCap(),
      manualMax: manualMax(),
      cores: state.detected?.cores,
      memory: state.detected?.memory,
      coarse: state.detected?.coarse,
      dpr: state.detected?.dpr,
      reducedMotion: reducedMotion(),
      reducedTransparency: reducedTransparency(),
      saveData: state.saveData,
      powerLimited: powerLimited(),
    },
  };

  window.dispatchEvent(new CustomEvent("mc:gfx", { detail: publicState() }));
}

function publicState() {
  return {
    level: state.level,
    auto: state.auto,
    frameMs: state.frameMs,
    rendered: state.detected?.renderer || "",
    software: software(),
    detected: state.detected?.start ?? 2,
    cap: autoCap(),
    manualMax: manualMax(),
    saveData: state.saveData,
    powerLimited: powerLimited(),
    reducedTransparency: reducedTransparency(),
    reducedMotion: reducedMotion(),
    paused: state.paused,
    levels: GFX_LEVELS,
  };
}

function save() {
  writeJson(STORAGE_KEY, { level: state.level, auto: state.auto });
}

function note(text) {
  try { notifier?.(text); } catch { /* ignore */ }
}

function maybeLower(delta) {
  if (!state.auto || delta <= 24 || state.level <= 0) return false;
  const now = performance.now();
  if (now - stats.lastChange < COOLDOWN) return false;
  stats.lastChange = now;
  state.level = Math.max(0, state.level - 1);
  stats.goodMs = 0;
  save();
  apply();
  note("Lowered graphics to keep things smooth");
  return true;
}

function maybeRaise(delta) {
  if (!state.auto || delta >= 10) {
    stats.goodMs = Math.max(0, stats.goodMs - SAMPLE_MS);
    return false;
  }
  stats.goodMs += SAMPLE_MS;
  if (stats.goodMs < RAISE_AFTER || state.level >= autoCap()) return false;
  const now = performance.now();
  if (now - stats.lastChange < COOLDOWN) return false;
  stats.lastChange = now;
  state.level = Math.min(autoCap(), state.level + 1);
  stats.goodMs = 0;
  save();
  apply();
  return true;
}

function stopSample() {
  sampling = false;
  sampleEnd = 0;
  cancelAnimationFrame(frameRaf);
  frameRaf = 0;
}

function runSample() {
  if (sampling) return;
  if (document.hidden || state.paused) return;
  sampling = true;
  sampleEnd = performance.now() + SAMPLE_MS;
  let last = 0;
  let total = 0;
  let frames = 0;

  const frame = (now) => {
    if (document.hidden || state.paused) {
      stopSample();
      return;
    }
    if (last) {
      const delta = now - last;
      if (delta > 0 && delta < 200) {
        total += delta;
        frames += 1;
      }
    }
    last = now;
    if (now < sampleEnd) {
      frameRaf = requestAnimationFrame(frame);
      return;
    }
    sampling = false;
    frameRaf = 0;
    if (!frames) return;
    const avg = total / frames;
    state.frameMs = Math.round(avg * 10) / 10;
    apply();
    if (state.auto) {
      if (!maybeLower(avg)) maybeRaise(avg);
    }
  };
  frameRaf = requestAnimationFrame(frame);
}

export const Gfx = {
  init() {
    if (state.ready) return;
    state.ready = true;
    state.detected = detect();
    const stored = readJson(STORAGE_KEY);
    state.auto = stored ? stored.auto !== false : true;
    state.level = stored && Number.isFinite(Number(stored.level))
      ? clampInt(stored.level)
      : state.detected.start;
    if (software()) state.level = 0;
    state.saveData = !!navigator.connection?.saveData;
    apply();

    if (!listenersBound) {
      listenersBound = true;
      const refreshPower = () => {
        state.saveData = !!navigator.connection?.saveData;
        if (state.auto) {
          state.level = Math.min(state.level, autoCap());
          save();
        }
        apply();
      };
      navigator.connection?.addEventListener?.("change", refreshPower);
      window.addEventListener("focus", () => { state.paused = false; apply(); });
      window.addEventListener("blur", () => { state.paused = true; stopSample(); apply(); });
      document.addEventListener("visibilitychange", () => {
        state.paused = document.hidden;
        if (state.paused) stopSample();
        apply();
      });
      window.matchMedia?.("(prefers-reduced-transparency: reduce)")
        ?.addEventListener?.("change", () => { state.level = Math.min(state.level, manualMax()); save(); apply(); });
      window.matchMedia?.("(prefers-reduced-motion: reduce)")
        ?.addEventListener?.("change", () => apply());
      window.addEventListener("resize", () => Gfx.activity(), { passive: true });
      window.addEventListener("scroll", () => Gfx.activity(), { passive: true });

      if (navigator.getBattery) {
        navigator.getBattery().then((battery) => {
          state.battery = battery;
          const onPower = () => { refreshPower(); };
          battery.addEventListener?.("chargingchange", onPower);
          battery.addEventListener?.("levelchange", onPower);
          refreshPower();
        }).catch(() => {});
      } else {
        refreshPower();
      }
      setTimeout(() => Gfx.activity(), 700);
    }
  },

  get state() {
    return publicState();
  },

  levels: GFX_LEVELS,

  setNotifier(fn) {
    notifier = fn;
  },

  setLevel(value) {
    state.auto = false;
    state.level = Math.max(0, Math.min(manualMax(), clampInt(value)));
    stats.goodMs = 0;
    save();
    apply();
    Gfx.activity();
  },

  setAuto(on) {
    state.auto = !!on;
    if (state.auto) {
      state.level = Math.min(state.detected?.start ?? 2, autoCap());
      stats.goodMs = 0;
    } else {
      state.level = Math.min(state.level, manualMax());
    }
    save();
    apply();
    Gfx.activity();
  },

  activity() {
    if (!state.ready) return;
    if (document.hidden || state.paused) return;
    if (sampling) {
      sampleEnd = performance.now() + SAMPLE_MS;
      return;
    }
    runSample();
  },

  transition(fn) {
    if (state.level < 3 || reducedMotion() || !document.startViewTransition) return fn();
    try {
      return document.startViewTransition(fn);
    } catch {
      return fn();
    }
  },
};
