/* Embed widget suite.
 *
 * web/embed/widgets.js is a plain browser IIFE: custom elements, shadow DOM and
 * fetch, none of which Node has. So the file is evaluated in a vm context with
 * the handful of browser globals it touches stubbed out, which is enough to
 * check what actually broke in production — every tag registering (a single
 * class may back only one tag name, or the rest silently go missing) and each
 * widget rendering the public payload without leaking `undefined` into the DOM.
 *
 * tests/test_widgets.py invokes this file, which keeps
 * `python -m unittest discover -s tests` a single command for the whole repo.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SOURCE = path.join(path.dirname(HERE), "web", "embed", "widgets.js");

let fails = 0;
function ok(name, cond, extra = "") {
  if (cond) {
    console.log(`ok   ${name}`);
  } else {
    fails += 1;
    console.log(`FAIL ${name} ${extra}`);
  }
}
function done() {
  console.log(fails === 0 ? "WIDGETS-TEST-PASS" : `WIDGETS-TEST-FAIL (${fails})`);
  process.exit(fails === 0 ? 0 : 1);
}

const PAYLOAD = {
  ok: true,
  user: { username: "sandisk" },
  listening: true,
  position: 84.7,
  updated: 1794889177,
  track: { id: 489, title: "Test Track", artist: "Test Artist", album: "Test Album", duration: 215.5 },
  profile_url: "https://embed.test/u/sandisk",
  cover_url: "https://embed.test/u/sandisk/cover.png?v=489-1794889177",
  base_url: "https://embed.test",
};

const TAGS = [
  "mcmusic-now", "mcmusic-turntable", "mcmusic-card",
  "mcmusic-bar", "mcmusic-marquee", "mcmusic-badge",
  "mcmusic-now-playing", "mcmusic-profile", "mcmusic-ticker",
];
/* The ticker is text only — no artwork slot at all, so it has no cover to render. */
const NO_COVER = new Set(["mcmusic-marquee", "mcmusic-ticker"]);
const ALIASES = [
  ["mcmusic-now-playing", "mcmusic-now"],
  ["mcmusic-profile", "mcmusic-card"],
  ["mcmusic-ticker", "mcmusic-marquee"],
];

/* The smallest element the widgets touch: attributes, a style declaration
   block, a class list and a shadow root holding whatever HTML was written. */
function makeElement() {
  class ClassList {
    constructor() { this.names = new Set(); }
    add(...names) { names.forEach((n) => this.names.add(n)); }
    remove(...names) { names.forEach((n) => this.names.delete(n)); }
    contains(name) { return this.names.has(name); }
  }

  return class HTMLElement {
    constructor() {
      this.classList = new ClassList();
      this.shadowRoot = null;
      this.attrs = new Map();
      this.vars = new Map();
      this.style = {
        setProperty: (key, value) => this.vars.set(key, String(value)),
        removeProperty: (key) => this.vars.delete(key),
        getPropertyValue: (key) => this.vars.get(key) || "",
      };
    }
    attachShadow() {
      this.shadowRoot = { innerHTML: "" };
      return this.shadowRoot;
    }
    getAttribute(name) { return this.attrs.has(name) ? this.attrs.get(name) : null; }
    setAttribute(name, value) { this.attrs.set(name, String(value)); }
    hasAttribute(name) { return this.attrs.has(name); }
  };
}

/* A registry that enforces the browser rule the live site tripped over: one
   constructor may only ever back a single tag name. */
function makeRegistry() {
  const byName = new Map();
  const byClass = new Map();
  return {
    byName,
    define(name, cls) {
      if (byName.has(name)) {
        throw Object.assign(new Error(`"${name}" has already been defined`), { name: "NotSupportedError" });
      }
      if (byClass.has(cls)) {
        throw Object.assign(
          new Error(`"${name}" reuses the constructor already registered as "${byClass.get(cls)}"`),
          { name: "NotSupportedError" },
        );
      }
      byClass.set(cls, name);
      byName.set(name, cls);
    },
    get(name) { return byName.get(name); },
  };
}

function loadWidgets(payload = PAYLOAD) {
  const HTMLElement = makeElement();
  const customElements = makeRegistry();
  const context = {
    HTMLElement,
    customElements,
    document: { currentScript: null, scripts: [] },
    location: { origin: "https://embed.test" },
    matchMedia: () => ({ matches: false }),
    getComputedStyle: () => ({ getPropertyValue: () => "" }),
    fetch: async () => ({ ok: true, json: async () => payload }),
    setInterval,
    clearInterval,
    queueMicrotask,
    console,
  };
  context.window = context;
  vm.createContext(context);

  let error = null;
  try {
    vm.runInContext(readFileSync(SOURCE, "utf8"), context, { filename: "widgets.js" });
  } catch (err) {
    error = err;
  }
  return { context, customElements, error };
}

/* Mount one tag the way a page would and let the stubbed fetch settle. */
async function render(tag, customElements) {
  const Ctor = customElements.get(tag);
  const el = new Ctor();
  el.setAttribute("user", "sandisk");
  el.connectedCallback();
  await new Promise((resolve) => setTimeout(resolve, 0));
  el.disconnectedCallback();
  return el;
}

async function main() {
  const { context, customElements, error } = loadWidgets();
  ok("the script evaluates", !error, error ? `${error.name}: ${error.message}` : "");
  if (error) return done();

  for (const tag of TAGS) {
    ok(`defines <${tag}>`, typeof customElements.get(tag) === "function");
  }
  ok("exposes the rescan hook pages call", typeof context.window.__mcWidgetsScan === "function");

  const html = {};
  for (const tag of TAGS) {
    const cls = customElements.get(tag);
    if (!cls) continue;
    const el = await render(tag, customElements);
    html[tag] = el.shadowRoot.innerHTML;

    ok(`<${tag}> renders the stubbed track`, html[tag].includes("Test Track"), html[tag].slice(0, 120));
    ok(`<${tag}> renders the artist`, html[tag].includes("Test Artist"));
    ok(`<${tag}> ${NO_COVER.has(tag) ? "stays text-only" : "renders the cover"}`,
      NO_COVER.has(tag) ? !html[tag].includes("<img") : html[tag].includes(PAYLOAD.cover_url));
    ok(`<${tag}> leaves no undefined or NaN in the markup`,
      !/undefined|NaN/.test(html[tag]), (html[tag].match(/.{0,40}(undefined|NaN).{0,40}/) || [""])[0]);
    ok(`<${tag}> themes itself when the page sets no colours`, el.vars.size > 0);
  }

  for (const [alias, base] of ALIASES) {
    ok(`<${alias}> is the same component as <${base}>`, html[alias] === html[base]);
  }

  /* `maxlen` turns over-long lines into a ticker instead of an ellipsis. */
  const Limit = customElements.get("mcmusic-now");
  const head = (text) => {
    const names = new Set();
    return {
      textContent: text,
      innerHTML: "",
      classList: { add: (name) => names.add(name), contains: (name) => names.has(name) },
    };
  };
  const root = (...els) => ({ querySelectorAll: () => els });

  const long = head("A track title that is far too long to fit");
  const short = head("Short");
  const limited = new Limit();
  limited.setAttribute("maxlen", "10");
  limited.applyScrollLimit(root(long, short));
  ok("long text scrolls past maxlen", limited && long.classList.contains("slide"), long.innerHTML);
  ok("scrolling text is doubled so the loop has no gap",
    (long.innerHTML.match(/far too long/g) || []).length === 2);
  ok("text inside maxlen is left alone", !short.classList.contains("slide") && short.innerHTML === "");

  const unlimited = new Limit();
  const untouched = head("A track title that is far too long to fit");
  unlimited.applyScrollLimit(root(untouched));
  ok("without maxlen nothing scrolls", !untouched.classList.contains("slide"));
  ok("maxlen is an observed attribute", Limit.observedAttributes.includes("maxlen"));
  ok("a pass takes 18s unless speed says otherwise", long.innerHTML.includes("animation-duration:18s"), long.innerHTML);

  /* `speed` sets how long one scroll pass takes. */
  const fast = new Limit();
  fast.setAttribute("maxlen", "10");
  fast.setAttribute("speed", "5");
  const fastLine = head("A track title that is far too long to fit");
  fast.applyScrollLimit(root(fastLine));
  ok("speed sets the pass length", fastLine.innerHTML.includes("animation-duration:5s"), fastLine.innerHTML);
  ok("speed is an observed attribute", Limit.observedAttributes.includes("speed"));

  /* `demo` renders sample data with no username and no network, so a gallery or
     a draft page shows the widgets before anyone is playing. */
  const offline = loadWidgets();
  offline.context.fetch = async () => { throw new Error("demo must not hit the network"); };
  const DemoNow = offline.customElements.get("mcmusic-now");
  const demo = new DemoNow();
  demo.setAttribute("demo", "");
  demo.connectedCallback();
  await new Promise((resolve) => setTimeout(resolve, 0));
  demo.disconnectedCallback();
  const demoHtml = demo.shadowRoot.innerHTML;
  ok("demo renders sample data without a username", demoHtml.includes("The Paper Tigers"), demoHtml.slice(0, 120));
  ok("demo stays offline", !/offline|unavailable|missing user/.test(demoHtml), demoHtml.slice(0, 160));
  ok("demo is an observed attribute", DemoNow.observedAttributes.includes("demo"));

  /* A real user still wins over demo. */
  const mixed = new (customElements.get("mcmusic-now"))();
  mixed.setAttribute("user", "sandisk");
  mixed.setAttribute("demo", "");
  mixed.connectedCallback();
  await new Promise((resolve) => setTimeout(resolve, 0));
  mixed.disconnectedCallback();
  ok("a username beats demo", mixed.shadowRoot.innerHTML.includes("Test Track"));

  /* A paused payload, the other branch every widget has to survive. */
  const paused = loadWidgets({ ...PAYLOAD, listening: false, track: null });
  ok("a quiet payload still evaluates", !paused.error, paused.error ? `${paused.error.message}` : "");
  for (const tag of TAGS) {
    const cls = paused.customElements.get(tag);
    if (!cls) continue;
    const el = await render(tag, paused.customElements);
    const markup = el.shadowRoot.innerHTML;
    ok(`<${tag}> renders without a track`,
      markup.length > 0 && !/undefined|NaN/.test(markup), markup.slice(0, 120));
  }

  done();
}

main();
