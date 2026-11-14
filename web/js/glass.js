/* ==========================================================================
   mcmusic — optional real glass
   One root class, one SVG filter, one feature gate. The base glass styling is
   never touched unless html.glass-real is present.
   ========================================================================== */

const root = document.documentElement;
const FILTER_ID = "glass-refract";
const SVG_NS = "http://www.w3.org/2000/svg";
const TARGETS = ["#deck", "#rail", ".menu", ".toast"];
const SESSION_KEY = "mc_glass_dropped";

const supports = (prop, value) => {
  try {
    return typeof CSS !== "undefined" && !!CSS.supports && CSS.supports(prop, value);
  } catch {
    return false;
  }
};

const media = (query) => {
  try {
    return !!(window.matchMedia && window.matchMedia(query).matches);
  } catch {
    return false;
  }
};

const caps = {
  svgBackdrop: false,
  squircle: supports("corner-shape", "squircle"),
  colorMix: supports("color", "color-mix(in srgb, red, blue)"),
  lightDark: supports("color", "light-dark(white, black)"),
  linearEasing: supports("transition-timing-function", "linear(0, 0.5 40%, 1)"),
  viewTransitions: typeof document.startViewTransition === "function",
};

let svg = null;
let filter = null;
let mapNode = null;
let observer = null;
let markTimer = 0;
let resizeTimer = 0;
let sampleTimer = 0;
let schema = "auto";
let quality = 4;
let active = false;
let detected = false;
let logged = false;
let dropped = false;

try {
  dropped = sessionStorage.getItem(SESSION_KEY) === "1";
} catch { /* private mode */ }

const lowPower = () => {
  const cores = Number(navigator.hardwareConcurrency || 8);
  const memory = Number(navigator.deviceMemory || 8);
  const saveData = !!navigator.connection?.saveData;
  return cores <= 2 || memory <= 2 || saveData;
};

/* A rounded-rect edge-normal map: neutral in the middle, bending at the rim. */
function generateMap(size) {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) return "";
  const image = ctx.createImageData(size, size);
  const data = image.data;
  const margin = size * 0.18;
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const ex = Math.max(0, 1 - Math.min(x, size - 1 - x) / margin);
      const ey = Math.max(0, 1 - Math.min(y, size - 1 - y) / margin);
      const nx = (x < size / 2 ? -1 : 1) * ex;
      const ny = (y < size / 2 ? -1 : 1) * ey;
      const i = (y * size + x) * 4;
      data[i] = Math.round(128 + nx * 92);
      data[i + 1] = Math.round(128 + ny * 92);
      data[i + 2] = 128;
      data[i + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
  return canvas.toDataURL("image/png");
}

function ensureFilter() {
  if (filter && document.documentElement.contains(svg)) return;
  svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  svg.setAttribute("width", "0");
  svg.setAttribute("height", "0");
  svg.style.cssText = "position:fixed;width:0;height:0;overflow:hidden;pointer-events:none";

  filter = document.createElementNS(SVG_NS, "filter");
  filter.setAttribute("id", FILTER_ID);
  filter.setAttribute("x", "-12%");
  filter.setAttribute("y", "-12%");
  filter.setAttribute("width", "124%");
  filter.setAttribute("height", "124%");
  filter.setAttribute("color-interpolation-filters", "sRGB");

  mapNode = document.createElementNS(SVG_NS, "feImage");
  mapNode.setAttribute("result", "edge-map");
  mapNode.setAttribute("preserveAspectRatio", "none");
  mapNode.setAttribute("x", "0");
  mapNode.setAttribute("y", "0");
  mapNode.setAttribute("width", "100%");
  mapNode.setAttribute("height", "100%");

  const displacement = document.createElementNS(SVG_NS, "feDisplacementMap");
  displacement.setAttribute("in", "SourceGraphic");
  displacement.setAttribute("in2", "edge-map");
  displacement.setAttribute("scale", "18");
  displacement.setAttribute("xChannelSelector", "R");
  displacement.setAttribute("yChannelSelector", "G");

  filter.appendChild(mapNode);
  filter.appendChild(displacement);
  svg.appendChild(filter);
  document.body.appendChild(svg);
  regenerateFilter();
}

function regenerateFilter() {
  if (!mapNode) return;
  const size = Math.round(Math.min(320, Math.max(180, Math.min(window.innerWidth, window.innerHeight) * 0.8)));
  const map = generateMap(size);
  if (map) {
    mapNode.setAttribute("href", map);
    mapNode.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", map);
  }
}

/* Runtime check: some engines echo the declaration but drop the SVG filter. */
function runtimeSvgBackdrop() {
  ensureFilter();
  if (!document.body) return false;
  const probe = document.createElement("div");
  probe.style.cssText = [
    "position:fixed",
    "left:-9999px",
    "top:0",
    "width:10px",
    "height:10px",
    `backdrop-filter:url(#${FILTER_ID}) blur(1px)`,
  ].join(";");
  document.body.appendChild(probe);
  const value = getComputedStyle(probe).backdropFilter
    || getComputedStyle(probe).webkitBackdropFilter
    || "";
  probe.remove();
  return /url\(/i.test(value);
}

function detect() {
  if (detected) return;
  detected = true;
  caps.svgBackdrop = runtimeSvgBackdrop();
  root.classList.toggle("has-svg-backdrop", caps.svgBackdrop);
  root.classList.toggle("has-squircle", caps.squircle);
  root.classList.toggle("has-color-mix", caps.colorMix);
  root.classList.toggle("has-light-dark", caps.lightDark);
  root.classList.toggle("has-linear-easing", caps.linearEasing);
  root.classList.toggle("has-view-transitions", caps.viewTransitions);
}

function targets() {
  const found = [];
  TARGETS.forEach((selector) => {
    document.querySelectorAll(selector).forEach((el) => {
      if (!found.includes(el)) found.push(el);
    });
  });
  return found;
}

function unmark() {
  document.querySelectorAll(".is-glass-real, .is-glass-soft").forEach((el) => {
    el.classList.remove("is-glass-real", "is-glass-soft");
  });
}

function mark() {
  unmark();
  if (!active) return;
  // One refracting layer at a time keeps text legible and frame cost low.
  // The rest get the enhanced tint/rim plus the normal blur.
  targets().slice(0, 6).forEach((el) => {
    const refract = el.id === "deck";
    el.classList.add(refract ? "is-glass-real" : "is-glass-soft");
  });
}

function queueMark() {
  clearTimeout(markTimer);
  markTimer = window.setTimeout(mark, 80);
}

function watch() {
  if (observer || !document.body) return;
  observer = new MutationObserver(queueMark);
  observer.observe(document.body, { childList: true, subtree: true });
}

function sampleFrames() {
  clearTimeout(sampleTimer);
  if (!active) return;
  sampleTimer = window.setTimeout(() => {
    if (!active) return;
    let start = 0;
    let last = 0;
    let frames = 0;
    let total = 0;
    const frame = (now) => {
      if (!active) return;
      if (!start) start = now;
      if (last) {
        const delta = now - last;
        if (delta > 0 && delta < 200) {
          total += delta;
          frames += 1;
        }
      }
      last = now;
      if (now - start < 2000) {
        requestAnimationFrame(frame);
        return;
      }
      if (frames > 12 && total / frames > 24) {
        dropped = true;
        active = false;
        root.classList.remove("glass-real");
        unmark();
        try { sessionStorage.setItem(SESSION_KEY, "1"); } catch { /* ignore */ }
        console.info("[mcmusic] real glass dropped: average frame time", (total / frames).toFixed(1), "ms");
        log(true);
      }
    };
    requestAnimationFrame(frame);
  }, 650);
}

function sync() {
  detect();
  const reducedTransparency = media("(prefers-reduced-transparency: reduce)");
  const unsupported = !caps.svgBackdrop || !caps.colorMix;
  active = schema !== "off" && quality >= 4 && !unsupported && !reducedTransparency && !lowPower() && !dropped;
  root.classList.toggle("glass-real", active);
  root.classList.toggle("glass-reduced-transparency", reducedTransparency);
  root.dataset.glassMode = schema;
  if (active) {
    ensureFilter();
    mark();
    watch();
    sampleFrames();
  } else {
    unmark();
    clearTimeout(sampleTimer);
  }
  log();
}

function log(force = false) {
  if (logged && !force) return;
  logged = true;
  console.info("[mcmusic] real glass", {
    mode: schema,
    quality,
    active,
    reason: active ? "enhanced" : schema === "off" ? "off" : dropped ? "poor-frame-time" : media("(prefers-reduced-transparency: reduce)") ? "reduced-transparency" : lowPower() ? "low-power" : "unsupported",
    ...caps,
  });
}

function setMode(value) {
  schema = value === "on" || value === "off" ? value : "auto";
  root.dataset.glassMode = schema;
  sync();
}

export const RealGlass = {
  caps,
  get status() {
    return {
      mode: schema,
      active,
      supported: caps.svgBackdrop && caps.colorMix,
      dropped,
    };
  },
  get supported() {
    return caps.svgBackdrop && caps.colorMix;
  },
  init(mode) {
    setMode(mode);
    // A resize changes the displacement map density; debounce it.
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(() => {
        if (!active) return;
        regenerateFilter();
        queueMark();
      }, 260);
    }, { passive: true });
  },
  setMode,
  setQuality(level) {
    quality = Math.max(0, Math.min(4, Math.round(Number(level) || 0)));
    sync();
  },
  get canTransition() {
    return active && caps.viewTransitions && !media("(prefers-reduced-motion: reduce)");
  },
  transition(fn) {
    if (!this.canTransition) return fn();
    try {
      return document.startViewTransition(fn);
    } catch {
      return fn();
    }
  },
};
